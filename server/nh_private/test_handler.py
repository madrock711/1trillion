import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("nh_handler", Path(__file__).with_name("handler.py"))
handler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler)

CONFIG = {"GOOGLE_CLIENT_ID": "test.apps.googleusercontent.com", "OWNER_GOOGLE_SUB": "12345678",
          "OWNER_EMAIL": "owner@gmail.com", "SSM_PARAMETER_NAME": "/yeonma/nh",
          "ALLOWED_ORIGIN": "https://www.hpmplab.com"}


def event():
    return {"version": "2.0", "rawPath": handler.PATH, "headers": {"origin": CONFIG["ALLOWED_ORIGIN"]},
            "requestContext": {"http": {"method": "GET"}, "authorizer": {"jwt": {"claims": {
                "sub": CONFIG["OWNER_GOOGLE_SUB"], "email": CONFIG["OWNER_EMAIL"], "email_verified": "true",
                "iss": "https://accounts.google.com", "aud": CONFIG["GOOGLE_CLIENT_ID"]}}}}}


class HandlerTest(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, CONFIG, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_authorization_denies_missing_or_incorrect_claims(self):
        cases = [("sub", "other"), ("email", "other@gmail.com"), ("email_verified", "false"),
                 ("iss", "https://attacker.example"), ("aud", "other.apps.googleusercontent.com")]
        with mock.patch.object(handler, "_flow") as flow:
            for key, value in cases:
                request = event()
                request["requestContext"]["authorizer"]["jwt"]["claims"][key] = value
                self.assertEqual(handler.lambda_handler(request, None)["statusCode"], 403, key)
            request = event()
            del request["requestContext"]["authorizer"]
            self.assertEqual(handler.lambda_handler(request, None)["statusCode"], 403)
            flow.assert_not_called()

    def test_happy_path_and_no_store_cors(self):
        with mock.patch.object(handler, "_flow", return_value={"source": "NH PLUG"}):
            response = handler.lambda_handler(event(), None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("no-store", response["headers"]["Cache-Control"])
        self.assertEqual(response["headers"]["Access-Control-Allow-Origin"], CONFIG["ALLOWED_ORIGIN"])

    def test_owner_session_has_no_nh_access_or_identity_details(self):
        request = event()
        request["rawPath"] = handler.SESSION_PATH
        service = mock.Mock()
        with mock.patch.object(handler, "TOKEN_CACHE_READY", True), mock.patch.object(handler, "FLOW_SERVICE", service), \
                mock.patch.object(handler, "_flow") as flow, mock.patch.object(handler, "_new_runtime_service") as initialize:
            response = handler.lambda_handler(request, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), {"authenticated": True})
        self.assertIn("no-store", response["headers"]["Cache-Control"])
        self.assertEqual(response["headers"]["Access-Control-Allow-Origin"], CONFIG["ALLOWED_ORIGIN"])
        self.assertNotIn(CONFIG["OWNER_EMAIL"], str(response))
        self.assertNotIn(CONFIG["OWNER_GOOGLE_SUB"], str(response))
        flow.assert_not_called()
        initialize.assert_not_called()
        service.get.assert_not_called()

    def test_session_rejects_other_accounts_and_missing_claims_before_nh_access(self):
        cases = [("sub", "other"), ("email", "other@gmail.com"), ("email_verified", "false"),
                 ("iss", "https://attacker.example"), ("aud", "other.apps.googleusercontent.com")]
        with mock.patch.object(handler, "_flow") as flow, mock.patch.object(handler, "_new_runtime_service") as initialize:
            for key, value in cases:
                request = event()
                request["rawPath"] = handler.SESSION_PATH
                request["requestContext"]["authorizer"]["jwt"]["claims"][key] = value
                self.assertEqual(handler.lambda_handler(request, None)["statusCode"], 403, key)
            request = event()
            request["rawPath"] = handler.SESSION_PATH
            del request["requestContext"]["authorizer"]
            # Direct Lambda invocation returns 403; API Gateway must reject a
            # missing/invalid JWT with 401 before invoking Lambda in production.
            self.assertEqual(handler.lambda_handler(request, None)["statusCode"], 403)
            flow.assert_not_called()
            initialize.assert_not_called()

    def test_session_rejects_bad_origin_and_method_and_options_has_no_data(self):
        request = event()
        request["rawPath"] = handler.SESSION_PATH
        request["headers"]["origin"] = "https://attacker.example"
        response = handler.lambda_handler(request, None)
        self.assertEqual(response["statusCode"], 403)
        self.assertNotIn("Access-Control-Allow-Origin", response["headers"])
        request = event()
        request["rawPath"] = handler.SESSION_PATH
        request["requestContext"]["http"]["method"] = "POST"
        self.assertEqual(handler.lambda_handler(request, None)["statusCode"], 405)
        request["requestContext"] = {"http": {"method": "OPTIONS"}}
        response = handler.lambda_handler(request, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), {})

    def test_session_route_uses_same_google_authorizer_and_specific_lambda_permission(self):
        template = (Path(__file__).parents[1] / "nh_infra" / "template.yaml").read_text(encoding="utf-8")
        route = template.split("  ReadSession:\n", 1)[1].split("\n  GatewayPermission:", 1)[0]
        self.assertIn("RouteKey: GET /api/private/nh/session", route)
        self.assertIn("AuthorizationType: JWT", route)
        self.assertIn("AuthorizerId: !Ref GoogleAuthorizer", route)
        permission = template.split("  SessionGatewayPermission:\n", 1)[1].split("\n  LiveStage:", 1)[0]
        self.assertIn("Principal: apigateway.amazonaws.com", permission)
        self.assertIn("/GET/api/private/nh/session'", permission)

    def test_malformed_request_wrong_origin_path_method(self):
        request = event()
        request["headers"]["origin"] = "https://evil.example"
        response = handler.lambda_handler(request, None)
        self.assertEqual(response["statusCode"], 403)
        self.assertNotIn("Access-Control-Allow-Origin", response["headers"])
        request = event()
        request["rawPath"] = "/other"
        self.assertEqual(handler.lambda_handler(request, None)["statusCode"], 404)
        request = event()
        request["requestContext"]["http"]["method"] = "POST"
        self.assertEqual(handler.lambda_handler(request, None)["statusCode"], 405)
        self.assertEqual(handler.lambda_handler({}, None)["statusCode"], 400)

    def test_options_is_public_and_empty(self):
        request = event()
        request["requestContext"] = {"http": {"method": "OPTIONS"}}
        response = handler.lambda_handler(request, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), {})

    def test_errors_are_generic_and_do_not_reveal_secrets(self):
        with mock.patch.object(handler, "_flow", side_effect=RuntimeError("secret-token-and-data")):
            response = handler.lambda_handler(event(), None)
        self.assertEqual(response["statusCode"], 503)
        self.assertNotIn("secret-token-and-data", str(response))
        self.assertIn("no-store", response["headers"]["Cache-Control"])

    def test_sanitize_only_expected_fields(self):
        row = {"bsop_hour": "111500", "timez12": "111500", "prsn_val": "314",
               "frgn_val": -3014, "orgn_val": 1816, "extra": "not forwarded"}
        self.assertNotIn("extra", handler._safe_rows({"Output_0": [row]})[0])

    def test_real_flow_is_fail_closed_until_shared_token_cache_is_implemented(self):
        service = mock.Mock()
        with mock.patch.dict(os.environ, {"TOKEN_CACHE_READY": "true", "NH_TOKEN_CACHE_READY": "1"}), mock.patch.object(handler, "FLOW_SERVICE", service), mock.patch.object(handler, "_new_runtime_service") as initialize:
            response = handler.lambda_handler(event(), None)
        self.assertEqual(response["statusCode"], 503)
        service.get.assert_not_called()
        initialize.assert_not_called()

    def test_lazy_initialization_only_after_authorization_and_reused(self):
        request = event()
        request["requestContext"]["authorizer"]["jwt"]["claims"]["sub"] = "not-owner"
        service = mock.Mock()
        service.get.return_value = {"source": "NH PLUG"}
        with mock.patch.object(handler, "TOKEN_CACHE_READY", True), mock.patch.object(handler, "FLOW_SERVICE", None), mock.patch.object(handler, "_new_runtime_service", return_value=service) as initialize:
            self.assertEqual(handler.lambda_handler(request, None)["statusCode"], 403)
            initialize.assert_not_called()
            self.assertEqual(handler.lambda_handler(event(), None)["statusCode"], 200)
            self.assertEqual(handler.lambda_handler(event(), None)["statusCode"], 200)
            initialize.assert_called_once()
            self.assertEqual(service.get.call_count, 2)

    def test_deployment_preflight_is_closed(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name("deployment_guard.py"))],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
