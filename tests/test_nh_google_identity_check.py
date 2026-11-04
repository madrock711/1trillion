import base64
import io
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nh_google_identity_check as identity


def b64(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def int64(value):
    return b64(value.to_bytes((value.bit_length() + 7) // 8, "big"))


class IdentityCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = cls.key.public_key().public_numbers()
        cls.keys = {"keys": [{"kty": "RSA", "kid": "test-key", "alg": "RS256", "use": "sig",
                              "n": int64(public.n), "e": int64(public.e)}]}

    def setUp(self):
        self.now = int(time.time())
        self.claims = {"iss": "https://accounts.google.com", "aud": identity.CLIENT_ID,
                       "exp": self.now + 3600, "iat": self.now - 1, "email_verified": True,
                       "email": identity.OWNER_EMAIL, "nonce": "one-time-nonce", "sub": "123456789"}

    def token(self, **updates):
        claims = dict(self.claims, **updates)
        header = b64(json.dumps({"alg": "RS256", "kid": "test-key"}).encode())
        body = b64(json.dumps(claims).encode())
        message = (header + "." + body).encode("ascii")
        return header + "." + body + "." + b64(self.key.sign(message, padding.PKCS1v15(), hashes.SHA256()))

    def test_valid_signature_returns_only_subject(self):
        self.assertEqual(identity.verify_token(self.token(), "one-time-nonce", keys=self.keys, now=self.now), "123456789")

    def test_rejects_wrong_account_or_claims(self):
        cases = [dict(email="other@gmail.com"), dict(email_verified=False), dict(aud="other.apps.googleusercontent.com"),
                 dict(iss="https://evil.example"), dict(exp=self.now), dict(iat=self.now + 61),
                 dict(nonce="another-nonce"), dict(sub="other"), dict(azp="other.apps.googleusercontent.com")]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ValueError):
                identity.verify_token(self.token(**change), "one-time-nonce", keys=self.keys, now=self.now)

    def test_rejects_bad_signature_and_key(self):
        token = self.token()
        signed, sig = token.rsplit(".", 1)
        corrupt = b64(bytes([_decode_sig_first(sig) ^ 1]) + base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4))[1:])
        with self.assertRaises(Exception):
            identity.verify_token(signed + "." + corrupt, "one-time-nonce", keys=self.keys, now=self.now)
        with self.assertRaises(ValueError):
            identity.verify_token(token, "one-time-nonce", keys={"keys": []}, now=self.now)

    def test_wrong_origin_cookie_or_csrf_rejected(self):
        headers = {"Host": "localhost:52710", "Origin": identity.ORIGIN, "Sec-Fetch-Site": "same-origin",
                   "Cookie": "yeonma_identity=secret-session"}
        self.assertTrue(identity.valid_request(headers, "secret-session", "csrf-token", "csrf-token"))
        for change in ({"Host": "attacker.example"}, {"Origin": "https://attacker.example"},
                       {"Sec-Fetch-Site": "cross-site"}, {"Cookie": "yeonma_identity=wrong"}):
            self.assertFalse(identity.valid_request(dict(headers, **change), "secret-session", "csrf-token", "csrf-token"))
        self.assertFalse(identity.valid_request(headers, "secret-session", "csrf-token", "wrong"))

    def test_handler_rejects_cross_origin_before_verification_and_never_returns_credential(self):
        handler_cls = identity.make_handler("entry", "session", "csrf", "nonce")
        instance = object.__new__(handler_cls)
        instance.server = SimpleNamespace(entry_used=False, verified=False)
        instance.path = "/verify"
        payload = json.dumps({"csrf": "csrf", "credential": "sensitive-token-value"}).encode()
        instance.rfile = io.BytesIO(payload)
        instance.headers = {"Host": "localhost:52710", "Origin": "https://attacker.example",
                            "Sec-Fetch-Site": "cross-site", "Cookie": "yeonma_identity=session",
                            "Content-Type": "application/json", "Content-Length": str(len(payload))}
        responses = []
        instance._send = lambda status, body=b"", **kwargs: responses.append((status, body, kwargs))
        with patch.object(identity, "verify_token") as verify, patch.object(identity, "save_subject") as save:
            instance.do_POST()
            verify.assert_not_called()
            save.assert_not_called()
        self.assertEqual(responses[0][0], 403)
        self.assertNotIn(b"sensitive-token-value", responses[0][1])

    def test_valid_post_only_saves_verified_subject(self):
        handler_cls = identity.make_handler("entry", "session", "csrf", "nonce")
        instance = object.__new__(handler_cls)
        instance.server = SimpleNamespace(entry_used=False, verified=False)
        instance.path = "/verify"
        payload = json.dumps({"csrf": "csrf", "credential": "sensitive-token-value"}).encode()
        instance.rfile = io.BytesIO(payload)
        instance.headers = {"Host": "localhost:52710", "Origin": identity.ORIGIN,
                            "Sec-Fetch-Site": "same-origin", "Cookie": "yeonma_identity=session",
                            "Content-Type": "application/json", "Content-Length": str(len(payload))}
        responses = []
        instance._send = lambda status, body=b"", **kwargs: responses.append((status, body, kwargs))
        with patch.object(identity, "verify_token", return_value="1234") as verify, patch.object(identity, "save_subject") as save:
            instance.do_POST()
            verify.assert_called_once_with("sensitive-token-value", "nonce")
            save.assert_called_once_with("1234")
        self.assertTrue(instance.server.verified)
        self.assertEqual(responses[0][:2], (200, b"OK"))

    def test_one_time_entry_redirects_to_clean_url(self):
        handler_cls = identity.make_handler("entry", "session", "csrf", "nonce")
        instance = object.__new__(handler_cls)
        instance.server = SimpleNamespace(entry_used=False, verified=False)
        instance.path = "/private-entry/entry"
        instance.headers = {"Host": "localhost:52710"}
        responses = []
        instance._send = lambda status, body=b"", **kwargs: responses.append((status, body, kwargs))
        instance.do_GET()
        self.assertEqual(responses[0][0], 303)
        self.assertTrue(responses[0][2]["redirect"])
        instance.do_GET()
        self.assertEqual(responses[1][0], 404)

    def test_subject_storage_is_encrypted_and_refuses_replacement(self):
        class FakeFile:
            data = None
            parent = SimpleNamespace(mkdir=lambda **_kwargs: None)
            def exists(self):
                return self.data is not None
            def read_bytes(self):
                return self.data
            def open(self, mode):
                assert mode == "xb" and self.data is None
                target = self
                class Writer(io.BytesIO):
                    def __exit__(self, *_args):
                        target.data = self.getvalue()
                        self.close()
                return Writer()
        file = FakeFile()
        def fake_dpapi(value, decrypt=False):
            return value.removeprefix(b"encrypted:") if decrypt else b"encrypted:" + value
        with patch.object(identity, "SUB_FILE", file), patch.object(identity, "dpapi_transform", fake_dpapi):
            identity.save_subject("1234")
            self.assertEqual(file.read_bytes(), b"encrypted:1234")
            identity.save_subject("1234")
            with self.assertRaises(ValueError):
                identity.save_subject("4321")
            self.assertEqual(file.read_bytes(), b"encrypted:1234")

    def test_remote_session_uses_fixed_https_url_and_authorization_only(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *_args): return None
            def read(self, _limit): return b'{"authenticated": true}'
        class Opener:
            request = None
            def open(self, request, timeout):
                self.request = request
                self.timeout = timeout
                return Response()
        opener = Opener()
        self.assertTrue(identity.verify_remote_session("fake-sensitive-token", opener=opener))
        self.assertEqual(opener.request.full_url, identity.REMOTE_SESSION_URL)
        self.assertEqual(opener.request.get_method(), "GET")
        self.assertEqual(opener.request.get_header("Authorization"), "Bearer fake-sensitive-token")
        self.assertNotIn("fake-sensitive-token", opener.request.full_url)
        self.assertIsNone(opener.request.data)
        self.assertEqual(opener.timeout, 10)

    def test_remote_session_disables_proxy_and_redirects(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *_args): return None
            def read(self, _limit): return b'{"authenticated": true}'
        opener = SimpleNamespace(open=lambda *_args, **_kwargs: Response())
        with patch.object(identity.urllib.request, "build_opener", return_value=opener) as build:
            self.assertTrue(identity.verify_remote_session("fake-token"))
        proxy, redirect = build.call_args.args
        self.assertEqual(proxy.proxies, {})
        self.assertIsInstance(redirect, identity.NoRedirect)
        self.assertIsNone(redirect.redirect_request(None, None, 302, "", {}, "https://attacker.example"))

    def test_remote_session_fails_closed_on_response_errors(self):
        class Response:
            def __init__(self, status, body): self.status, self.body = status, body
            def __enter__(self): return self
            def __exit__(self, *_args): return None
            def read(self, _limit): return self.body
        cases = [(302, b'{"authenticated":true}'), (403, b'{"authenticated":true}'),
                 (200, b'{"authenticated":false}'), (200, b'{"authenticated":1}'),
                 (200, b'{"authenticated":true,"extra":"data"}'),
                 (200, b'not-json'), (200, b'x' * 4097)]
        for status, body in cases:
            with self.subTest(status=status, body=body[:32]):
                opener = SimpleNamespace(open=lambda *_args, **_kwargs: Response(status, body))
                self.assertFalse(identity.verify_remote_session("fake-token", opener=opener))
        def fail(*_args, **_kwargs):
            raise RuntimeError("sensitive-token-value must not escape")
        self.assertFalse(identity.verify_remote_session("fake-token", opener=SimpleNamespace(open=fail)))

    def test_remote_requires_prior_verified_same_token_and_user_post(self):
        handler_cls = identity.make_handler("entry", "session", "csrf", "nonce")
        instance = object.__new__(handler_cls)
        instance.server = SimpleNamespace(entry_used=False, verified=False, remote_verified=False,
                                          verified_token_hash=None)
        responses = []
        instance._send = lambda status, body=b"", **kwargs: responses.append((status, body, kwargs))
        def request(path, credential, origin=identity.ORIGIN):
            payload = json.dumps({"csrf": "csrf", "credential": credential}).encode()
            instance.path, instance.rfile = path, io.BytesIO(payload)
            instance.headers = {"Host": "localhost:52710", "Origin": origin,
                                "Sec-Fetch-Site": "same-origin", "Cookie": "yeonma_identity=session",
                                "Content-Type": "application/json", "Content-Length": str(len(payload))}
            instance.do_POST()
        with patch.object(identity, "verify_token", return_value="1234") as verify, \
                patch.object(identity, "save_subject") as save, \
                patch.object(identity, "verify_remote_session", return_value=True) as remote:
            request("/server-verify", "fake-token")
            self.assertEqual(responses[-1][0], 403)
            remote.assert_not_called()
            request("/verify", "fake-token")
            self.assertEqual(responses[-1][0], 200)
            verify.assert_called_once_with("fake-token", "nonce")
            save.assert_called_once_with("1234")
            self.assertEqual(instance.server.verified_token_hash, hashlib.sha256(b"fake-token").digest())
            remote.assert_not_called()  # Explicit second POST is mandatory.
            request("/server-verify", "different-token")
            self.assertEqual(responses[-1][0], 403)
            remote.assert_not_called()
            request("/server-verify", "fake-token", "https://attacker.example")
            self.assertEqual(responses[-1][0], 403)
            remote.assert_not_called()
            request("/server-verify", "fake-token")
            self.assertEqual(responses[-1][:2], (200, b"OK"))
            remote.assert_called_once_with("fake-token")
            self.assertIsNone(instance.server.verified_token_hash)
            request("/server-verify", "fake-token")
            self.assertEqual(responses[-1][0], 403)
        self.assertNotIn("fake-token", repr(responses))

    def test_page_requires_separate_server_check_button(self):
        page = identity._page("fake-csrf", "fake-nonce").decode("utf-8")
        self.assertIn('id="server-check" type="button" hidden', page)
        self.assertIn("serverCheck.addEventListener('click'", page)
        self.assertIn("fetch('/server-verify'", page)


def _decode_sig_first(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))[0]


if __name__ == "__main__":
    unittest.main()
