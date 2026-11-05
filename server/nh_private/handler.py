"""Private NH flow endpoint. Only use behind a verified API Gateway JWT authorizer."""
from __future__ import annotations

import json
import os
import re
import threading
import hmac

from session_store import Sessions, cookie, read_cookie, LIFETIME

PATH = "/api/private/nh/flow"
SESSION_PATH = "/api/private/nh/session"
API_PATH = "/krfuture/quote/v1/tradingStatus"
FIELDS = ("bsop_hour", "timez12", "prsn_val", "frgn_val", "orgn_val")
# NH issuance is coordinated through the initialized shared state. An absent,
# ISSUING or UNCERTAIN record remains fail-closed, even with this launch flag.
TOKEN_CACHE_READY = True
FLOW_SERVICE = None
_service_lock = threading.Lock()
SESSION_LOGIN = SESSION_PATH + "/login"
SESSION_STATE = SESSION_PATH + "/state"
SESSION_LOGOUT = SESSION_PATH + "/logout"
SESSION_FLOW = SESSION_PATH + "/flow"
SESSION_STORE = None


def _configuration():
    required = ("GOOGLE_CLIENT_ID", "OWNER_GOOGLE_SUB", "OWNER_EMAIL", "SSM_PARAMETER_NAME", "ALLOWED_ORIGIN")
    config = {key: os.environ.get(key, "").strip() for key in required}
    if not all(config.values()) or not re.fullmatch(r"[0-9]{1,64}", config["OWNER_GOOGLE_SUB"]):
        raise ValueError("invalid configuration")
    if not config["GOOGLE_CLIENT_ID"].endswith(".apps.googleusercontent.com"):
        raise ValueError("invalid configuration")
    if config["ALLOWED_ORIGIN"] != "https://www.hpmplab.com":
        raise ValueError("invalid configuration")
    return config


def _response(status, value, origin=""):
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "private, no-store, max-age=0",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
        "Vary": "Origin, Cookie",
    }
    if origin == "https://www.hpmplab.com":
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return {"statusCode": status, "headers": headers, "body": json.dumps(value, ensure_ascii=False)}


def _authorized(event, config):
    """Claims are trustworthy only if API Gateway verified the JWT before invocation."""
    context = event.get("requestContext") or {}
    claims = (((context.get("authorizer") or {}).get("jwt") or {}).get("claims") or {})
    if not isinstance(claims, dict):
        return False
    audience = claims.get("aud")
    if isinstance(audience, list):
        valid_audience = config["GOOGLE_CLIENT_ID"] in audience
    else:
        valid_audience = audience == config["GOOGLE_CLIENT_ID"]
    verified = claims.get("email_verified") is True or claims.get("email_verified") == "true"
    return (valid_audience
            and claims.get("iss") in ("https://accounts.google.com", "accounts.google.com")
            and claims.get("sub") == config["OWNER_GOOGLE_SUB"]
            and isinstance(claims.get("email"), str)
            and claims["email"].lower() == config["OWNER_EMAIL"].lower()
            and verified)


def _safe_rows(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("Output_0"), list):
        raise ValueError("invalid response")
    result = []
    for row in payload["Output_0"]:
        if not isinstance(row, dict):
            continue
        item = {key: row.get(key) for key in FIELDS}
        if any(not (isinstance(item[key], int) and not isinstance(item[key], bool)
                        or isinstance(item[key], str) and re.fullmatch(r"[+-]?\d{1,18}", item[key].strip()))
               for key in ("prsn_val", "frgn_val", "orgn_val")):
            continue
        if any(not isinstance(item[key], (str, int)) or isinstance(item[key], bool) or len(str(item[key])) > 24
               for key in ("bsop_hour", "timez12")):
            continue
        result.append(item)
    return result


def _new_runtime_service(config):
    # Imported only on an authorized, explicitly enabled request. boto3 is
    # available in Lambda; initialization is intentionally inert until then.
    import boto3
    from runtime_service import build_service
    runtime_config = dict(config)
    runtime_config["TOKEN_TABLE_NAME"] = os.environ.get("TOKEN_TABLE_NAME", "").strip()
    clients = {name: boto3.client(name) for name in ("ssm", "dynamodb")}
    return build_service(runtime_config, clients, _safe_rows)


def _flow(config):
    global FLOW_SERVICE
    if not TOKEN_CACHE_READY:
        raise RuntimeError("shared token cache is not live-validated")
    if FLOW_SERVICE is None:
        with _service_lock:
            if FLOW_SERVICE is None:
                FLOW_SERVICE = _new_runtime_service(config)
    return FLOW_SERVICE.get()


def _sessions(config):
    global SESSION_STORE
    if SESSION_STORE is None:
        import boto3
        SESSION_STORE = Sessions(boto3.client("dynamodb"), os.environ["TOKEN_TABLE_NAME"],
                                 config["OWNER_GOOGLE_SUB"] + ":" + config["OWNER_EMAIL"].lower())
    return SESSION_STORE


def _session_response(event, config, path, method, origin):
    expected = {SESSION_LOGIN: "POST", SESSION_LOGOUT: "POST", SESSION_STATE: "GET", SESSION_FLOW: "GET"}
    if method != expected[path]:
        return _response(405, {"error": "method not allowed"}, origin)
    if method == "POST" and origin != config["ALLOWED_ORIGIN"]:
        return _response(403, {"error": "forbidden"}, origin)
    if path == SESSION_LOGIN and not _authorized(event, config):
        return _response(403, {"error": "forbidden"}, origin)
    store = _sessions(config)
    token = read_cookie(event)
    if path == SESSION_LOGIN:
        # Rotate any prior browser session; never retain the Google credential.
        if store.read(token):
            store.revoke(token)
        token, payload = store.create()
        response = _response(200, payload, origin)
        response["cookies"] = [cookie(token, LIFETIME)]
        return response
    session = store.read(token)
    if not session:
        response = _response(401, {"authenticated": False}, origin)
        response["cookies"] = [cookie()]
        return response
    if path == SESSION_LOGOUT:
        csrf = event.get("headers", {}).get("x-yeonma-csrf", "")
        if not isinstance(csrf, str) or not hmac.compare_digest(csrf, session["csrfToken"]):
            return _response(403, {"error": "forbidden"}, origin)
        store.revoke(token)
        response = _response(200, {"authenticated": False}, origin)
        response["cookies"] = [cookie()]
        return response
    if path == SESSION_STATE:
        return _response(200, session, origin)
    return _response(200, _flow(config), origin)


def lambda_handler(event, _context):
    origin = ""
    try:
        if not isinstance(event, dict) or event.get("version") != "2.0":
            return _response(400, {"error": "invalid request"})
        config = _configuration()
        headers = event.get("headers") or {}
        if not isinstance(headers, dict):
            return _response(400, {"error": "invalid request"})
        origin = headers.get("origin", "")
        if origin and origin != config["ALLOWED_ORIGIN"]:
            return _response(403, {"error": "forbidden"})
        context = event.get("requestContext") or {}
        method = (context.get("http") or {}).get("method", "")
        path = event.get("rawPath")
        session_paths = (SESSION_LOGIN, SESSION_STATE, SESSION_LOGOUT, SESSION_FLOW)
        if path not in (PATH, SESSION_PATH) + session_paths:
            return _response(404, {"error": "not found"}, origin)
        if method == "OPTIONS":
            return _response(200, {}, origin)
        if path in session_paths:
            return _session_response(event, config, path, method, origin)
        if method != "GET":
            return _response(405, {"error": "method not allowed"}, origin)
        if not _authorized(event, config):
            return _response(403, {"error": "forbidden"}, origin)
        if path == SESSION_PATH:
            # Authentication check only: never initialize the NH runtime, fetch
            # credentials, contact NH, or expose account identifiers here.
            return _response(200, {"authenticated": True}, origin)
        return _response(200, _flow(config), origin)
    except Exception:
        # Never expose or log provider errors, tokens, user claims or credentials.
        return _response(503, {"error": "service unavailable"}, origin)
