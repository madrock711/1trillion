"""In-process integration only. Every network/storage dependency is fake."""
import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import urlsplit

import test_handler
import test_nh_transport
import test_token_store

spec = importlib.util.spec_from_file_location("flow_service", Path(__file__).with_name("flow_service.py"))
flow_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow_service)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, test_handler.CONFIG, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.ddb = test_token_store.FakeDdb()
        self.opener = mock.Mock()
        self.nh = test_nh_transport.transport.NHTransport("test-key", "test-secret", opener=self.opener)
        self.store = test_token_store.module.DynamoTokenStore(self.ddb, "test", "one")
        self.tokens = test_token_store.module.SharedTokenManager(self.store, self.nh.issue_once, clock=lambda: 1000)
        self.service = flow_service.FlowService(self.tokens, self.nh, test_handler.handler._safe_rows)
        self.row = {"bsop_hour": "111500", "timez12": "111500", "prsn_val": "314", "frgn_val": -3014,
                    "orgn_val": 1816, "ignored": "not forwarded"}

    def call(self):
        # Test-only injection; real source constant remains False and service None.
        with mock.patch.object(test_handler.handler, "TOKEN_CACHE_READY", True), mock.patch.object(test_handler.handler, "FLOW_SERVICE", self.service):
            return test_handler.handler.lambda_handler(test_handler.event(), None)

    def test_authorized_handler_flow_issues_once_and_caches(self):
        self.opener.open.side_effect = [test_nh_transport.Response({"access_token": "fake-token", "expires_in": 86400}),
                                      test_nh_transport.Response({"Output_0": [self.row]}),
                                      test_nh_transport.Response({"Output_0": [self.row]})]
        response = self.call()
        self.assertEqual(response["statusCode"], 200)
        data = json.loads(response["body"])
        self.assertEqual(data["quantity"][0]["prsn_val"], "314")
        self.assertNotIn("ignored", data["amount"][0])
        self.assertEqual(self.call()["statusCode"], 200)
        self.assertEqual(self.opener.open.call_count, 3)
        self.assertEqual(self.store.read()["state"], "VALID")

    def test_unauthorized_handler_never_contacts_service(self):
        request = test_handler.event()
        request["requestContext"]["authorizer"]["jwt"]["claims"]["sub"] = "not-owner"
        with mock.patch.object(test_handler.handler, "TOKEN_CACHE_READY", True), mock.patch.object(test_handler.handler, "FLOW_SERVICE", self.service):
            result = test_handler.handler.lambda_handler(request, None)
        self.assertEqual(result["statusCode"], 403)
        self.opener.open.assert_not_called()

    def test_quote_401_does_not_reissue_token(self):
        self.opener.open.side_effect = [test_nh_transport.Response({"access_token": "fake-token", "expires_in": 86400}),
                                      HTTPError(test_nh_transport.transport.FLOW_URL, 401, "", {}, io.BytesIO()),
                                      HTTPError(test_nh_transport.transport.FLOW_URL, 401, "", {}, io.BytesIO())]
        self.assertEqual(self.call()["statusCode"], 503)
        self.assertEqual(self.call()["statusCode"], 503)
        paths = [urlsplit(call.args[0].full_url).path for call in self.opener.open.call_args_list]
        self.assertEqual(paths.count("/oauth2/token"), 1)
        self.assertEqual(self.store.read()["state"], "VALID")


if __name__ == "__main__":
    unittest.main()
