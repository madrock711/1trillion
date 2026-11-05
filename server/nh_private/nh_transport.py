"""Experimental read-only NH HTTP transport; not wired to the live handler.

The caller must coordinate all token issuance via SharedTokenManager. This
module never retries, follows redirects, or issues a token on quote errors.
"""
from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

BASE = "https://api.nhplug.com:8443"
TOKEN_URL = BASE + "/oauth2/token"
FLOW_URL = BASE + "/krfuture/quote/v1/tradingStatus"
MAX_BODY = 2_000_000


class NHTransportError(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_credential(value):
    if not isinstance(value, str) or not (1 <= len(value) <= 4096) or any(ord(c) < 33 or ord(c) > 126 for c in value):
        raise NHTransportError("invalid NH credentials")


class NHTransport:
    def __init__(self, app_key, app_secret, opener=None, timeout=6):
        _validate_credential(app_key)
        _validate_credential(app_secret)
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= 30:
            raise ValueError("invalid timeout")
        self._app_key, self._app_secret = app_key, app_secret
        # Avoid proxy environment variables silently forwarding secrets.
        self._opener = opener if opener is not None else build_opener(ProxyHandler({}), _NoRedirect())
        self._timeout = timeout

    def _post(self, request):
        try:
            with self._opener.open(request, timeout=self._timeout) as response:
                if response.status != 200:
                    raise NHTransportError("NH request failed")
                data = response.read(MAX_BODY + 1)
            if len(data) > MAX_BODY:
                raise NHTransportError("NH response too large")
            result = json.loads(data.decode("utf-8"))
            if not isinstance(result, dict):
                raise NHTransportError("invalid NH response")
            return result
        except Exception:
            # HTTP errors can carry request URLs, credentials or provider payloads.
            raise NHTransportError("NH request failed") from None

    def issue_once(self):
        """One request only. A timeout must leave token state UNCERTAIN."""
        # NH's published OpenAPI marks all four as required query parameters;
        # its SDK uses the same wire format. Never log the URL or exceptions.
        query = urlencode({"appkey": self._app_key, "appsecretkey": self._app_secret,
                           "grant_type": "client_credentials", "scope": "oob"})
        request = Request(TOKEN_URL + "?" + query, data=b"", method="POST",
                          headers={"Content-Type": "application/x-www-form-urlencoded"})
        result = self._post(request)
        token, lifetime = result.get("access_token"), result.get("expires_in")
        _validate_credential(token)
        if not isinstance(lifetime, int) or isinstance(lifetime, bool) or not 0 < lifetime <= 86400:
            raise NHTransportError("invalid NH token response")
        return {"access_token": token, "expires_in": lifetime}

    def read_flow(self, token, mode):
        """Read one fixed quote route; 401 and all other failures are not retried."""
        _validate_credential(token)
        if mode not in ("amount", "quantity"):
            raise NHTransportError("invalid NH flow mode")
        body = json.dumps({"Input_0": {"market_cd": "UNT", "mrkt_cls_code": "1", "cycle_cls_code": "4",
                                       "opt_cls_code": "1" if mode == "amount" else "2", "cnt": "999"}}).encode("utf-8")
        request = Request(FLOW_URL, data=body, method="POST", headers={
            "Content-Type": "application/json; charset=UTF-8", "x-client-id": self._app_key,
            "x-client-secret": self._app_secret, "authorization": f"Bearer {token}"})
        result = self._post(request)
        if not isinstance(result.get("Output_0"), list):
            raise NHTransportError("invalid NH flow response")
        return result
