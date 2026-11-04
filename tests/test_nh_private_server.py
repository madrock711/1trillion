import http.client
import importlib.util
import json
import os
from pathlib import Path
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nh_private_server", ROOT / "scripts" / "nh_private_server.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class PrivateServerTests(unittest.TestCase):
    def test_windows_dpapi_roundtrip(self):
        if os.name != "nt":
            self.skipTest("Windows DPAPI only")
        plain = b"unit-test-not-a-credential"
        protected = app.dpapi_transform(plain)
        self.assertNotEqual(plain, protected)
        self.assertEqual(plain, app.dpapi_transform(protected, decrypt=True))

    def test_flow_cache_and_raw_fields(self):
        calls = []
        def call(path, payload):
            calls.append((path, payload))
            return {"Output_0": [{"bsop_hour": "11000000", "timez12": "202611041100", "prsn_val": 10, "frgn_val": -3, "orgn_val": -7, "ignored": "x"}]}
        reader = app.FlowReader(call)
        result = reader.get()
        self.assertIs(reader.get(), result)
        self.assertEqual(len(calls), 2)
        self.assertEqual({c[1]["opt_cls_code"] for c in calls}, {"1", "2"})
        self.assertTrue(all(c[1]["market_cd"] == "UNT" for c in calls))
        self.assertIsNone(result["tradeDate"])
        self.assertFalse(result["unitsVerified"])
        self.assertNotIn("ignored", result["amount"][0])
        self.assertEqual(app.safe_rows({"Output_0": [{"prsn_val": True}]}), [])

    def test_http_session_origin_and_static_allowlist(self):
        class Reader:
            def get(self):
                return {"amount": [], "quantity": [], "unitsVerified": False, "tradeDate": None}
        server = app.PrivateServer(("127.0.0.1", 0), http.client.HTTPConnection, bind_and_activate=False)
        server.server_bind()
        port = server.server_address[1]
        server.RequestHandlerClass = app.make_handler(Reader(), "session-token", port)
        server.server_activate()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def request(path, headers=None, method="GET"):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            conn.request(method, path, headers=headers or {})
            response = conn.getresponse()
            body = response.read()
            result = response.status, dict(response.getheaders()), body
            conn.close()
            return result
        try:
            self.assertEqual(request("/api/private/nh/flow")[0], 403)
            status, headers, _ = request("/private-entry/session-token")
            self.assertEqual(status, 303)
            cookie = headers["Set-Cookie"].split(";", 1)[0]
            status, _, body = request("/api/private/nh/flow", {"Cookie": cookie, "Sec-Fetch-Site": "same-origin"})
            self.assertEqual(status, 200)
            self.assertIsNone(json.loads(body)["tradeDate"])
            self.assertEqual(request("/api/private/nh/flow", {"Cookie": cookie, "Origin": "https://evil.example"})[0], 403)
            self.assertEqual(request("/api/private/nh/flow", {"Cookie": cookie, "Sec-Fetch-Site": "cross-site"})[0], 403)
            self.assertEqual(request("/api/private/nh/flow", {"Host": "evil.example", "Cookie": cookie})[0], 403)
            for path in ("/.git/config", "/scripts/nh_private_server.py", "/docs/", "/assets/", "/reports/2026-11-04.md"):
                self.assertEqual(request(path)[0], 404, path)
            self.assertEqual(request("/index.html")[0], 200)
            self.assertEqual(request("/.git/config", method="HEAD")[0], 405)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
