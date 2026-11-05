"""Opaque, revocable browser sessions. Never stores Google or NH tokens."""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time

COOKIE = "__Host-yeonma_session"
LIFETIME = 7 * 24 * 60 * 60


def cookie(value="", max_age=0):
    return f"{COOKIE}={value}; Path=/; Max-Age={max_age}; HttpOnly; Secure; SameSite=Lax"


def read_cookie(event):
    values = []
    raw = event.get("cookies") or [event.get("headers", {}).get("cookie", "")]
    if not isinstance(raw, list):
        return ""
    for header in raw:
        if not isinstance(header, str) or len(header) > 16384:
            return ""
        for pair in header.split(";"):
            name, sep, value = pair.strip().partition("=")
            if sep and name == COOKIE:
                values.append(value)
    return values[0] if len(values) == 1 and re.fullmatch(r"[A-Za-z0-9_-]{43}", values[0]) else ""


class Sessions:
    def __init__(self, ddb, table, owner, clock=time.time):
        self.ddb, self.table, self.clock = ddb, table, clock
        self.owner = hashlib.sha256(owner.encode()).hexdigest()

    def key(self, token):
        return {"id": {"S": "session#" + hashlib.sha256(token.encode()).hexdigest()}}

    def create(self):
        token, csrf = secrets.token_urlsafe(32), secrets.token_hex(32)
        expires = int(self.clock()) + LIFETIME
        self.ddb.update_item(
            TableName=self.table, Key=self.key(token),
            UpdateExpression="SET expires_at = :exp, csrf = :csrf, owner_hash = :owner, revoked = :no",
            ConditionExpression="attribute_not_exists(id)",
            ExpressionAttributeValues={":exp": {"N": str(expires)}, ":csrf": {"S": csrf},
                                       ":owner": {"S": self.owner}, ":no": {"BOOL": False}})
        return token, {"authenticated": True, "expiresAt": expires, "csrfToken": csrf}

    def read(self, token):
        if not token:
            return None
        item = self.ddb.get_item(TableName=self.table, Key=self.key(token), ConsistentRead=True).get("Item")
        if not item:
            return None
        try:
            expires = int(item["expires_at"]["N"])
            csrf = item["csrf"]["S"]
            if (expires <= int(self.clock()) or item["revoked"]["BOOL"] is not False
                    or not hmac.compare_digest(item["owner_hash"]["S"], self.owner)
                    or not re.fullmatch(r"[a-f0-9]{64}", csrf)):
                return None
            return {"authenticated": True, "expiresAt": expires, "csrfToken": csrf}
        except (KeyError, ValueError, TypeError):
            return None

    def revoke(self, token):
        if token:
            self.ddb.update_item(TableName=self.table, Key=self.key(token),
                                 UpdateExpression="SET revoked = :yes",
                                 ExpressionAttributeValues={":yes": {"BOOL": True}})
