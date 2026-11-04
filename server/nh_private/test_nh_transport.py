import importlib.util
import io
import json
import traceback
from pathlib import Path
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

spec = importlib.util.spec_from_file_location("nh_transport", Path(__file__).with_name("nh_transport.py"))
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class Response:
    def __init__(self, payload, status=200):
        self.status = status
        self.payload = payload if isinstance(payload, bytes) else json.dumps(payload).encode()

    def read(self, size):
        return self.payload[:size]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.opener = mock.Mock()
        self.api = transport.NHTransport("test-key", "test-secret", opener=self.opener)

    def test_one_issue_sends_documented_query_to_fixed_https_host(self):
        self.opener.open.return_value = Response({"access_token": "test-token", "expires_in": 86400})
        self.assertEqual(self.api.issue_once()["expires_in"], 86400)
        self.opener.open.assert_called_once()
        request = self.opener.open.call_args.args[0]
        url = urlsplit(request.full_url)
        self.assertEqual((url.scheme, url.netloc, url.path), ("https", "api.nhplug.com:8443", "/oauth2/token"))
        self.assertEqual(parse_qs(url.query), {"appkey": ["test-key"], "appsecretkey": ["test-secret"],
                                              "grant_type": ["client_credentials"], "scope": ["oob"]})
        self.assertEqual(request.data, b"")
        self.assertEqual(request.get_method(), "POST")

    def test_issuer_timeout_never_retries_and_does_not_leak(self):
        self.opener.open.side_effect = TimeoutError("https://api.nhplug.com:8443/oauth2/token?appsecretkey=test-secret")
        with self.assertRaises(transport.NHTransportError) as error:
            self.api.issue_once()
        self.assertNotIn("test-secret", str(error.exception))
        self.assertIsNone(error.exception.__cause__)
        self.opener.open.assert_called_once()

    def test_quote_401_never_reissues_or_retries(self):
        self.opener.open.side_effect = HTTPError(transport.FLOW_URL, 401, "test-token", {}, io.BytesIO())
        with self.assertRaises(transport.NHTransportError) as error:
            self.api.read_flow("test-token", "amount")
        self.assertNotIn("test-token", str(error.exception))
        self.opener.open.assert_called_once()
        request = self.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, transport.FLOW_URL)
        self.assertEqual(json.loads(request.data)["Input_0"]["opt_cls_code"], "1")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")

    def test_quantity_fixed_route_and_response(self):
        self.opener.open.return_value = Response({"Output_0": [{"prsn_val": 314}]})
        self.assertEqual(self.api.read_flow("test-token", "quantity")["Output_0"][0]["prsn_val"], 314)
        request = self.opener.open.call_args.args[0]
        self.assertEqual(json.loads(request.data)["Input_0"]["opt_cls_code"], "2")
        self.assertEqual(json.loads(request.data)["Input_0"]["market_cd"], "UNT")

    def test_invalid_inputs_fail_before_network(self):
        for token in ("bad\nheader", "", None):
            with self.assertRaises(transport.NHTransportError):
                self.api.read_flow(token, "amount")
        with self.assertRaises(transport.NHTransportError):
            self.api.read_flow("test-token", "orders")
        self.opener.open.assert_not_called()

    def test_bad_or_oversized_response_never_retries(self):
        for response in (Response(b"not json"), Response(b"x" * (transport.MAX_BODY + 1)), Response({"error": "x"})):
            self.opener.open.reset_mock()
            self.opener.open.return_value = response
            with self.assertRaises(transport.NHTransportError):
                self.api.read_flow("test-token", "amount")
            self.opener.open.assert_called_once()

    def test_no_redirect_handler_does_not_reuse_credentials(self):
        handler = transport._NoRedirect()
        self.assertIsNone(handler.redirect_request(mock.Mock(), None, 302, "", {}, "https://attacker.example"))

    def test_issuer_http_error_redacts_secret_even_from_formatted_traceback(self):
        url = transport.TOKEN_URL + "?appsecretkey=test-secret"
        self.opener.open.side_effect = HTTPError(url, 302, "redirect", {"Location": "https://attacker.example"}, io.BytesIO())
        with self.assertRaises(transport.NHTransportError) as error:
            self.api.issue_once()
        formatted = "".join(traceback.format_exception(type(error.exception), error.exception, error.exception.__traceback__))
        self.assertNotIn("test-secret", formatted)
        self.assertNotIn(url, formatted)
        self.opener.open.assert_called_once()

    def test_401_does_not_call_issuer_even_with_manager_style_caller(self):
        manager = mock.Mock()
        manager.get_token.return_value = "test-token"
        self.opener.open.side_effect = HTTPError(transport.FLOW_URL, 401, "", {}, io.BytesIO())
        with self.assertRaises(transport.NHTransportError):
            self.api.read_flow(manager.get_token(), "quantity")
        manager.get_token.assert_called_once_with()
        self.opener.open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
