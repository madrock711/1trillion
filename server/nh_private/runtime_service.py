"""Build the private flow service; not activated by the deployment guard.

The caller must supply already-configured AWS clients. Construction makes one
SSM read but does not issue an NH token or query NH. The caller must never log
exceptions from SSM, since provider exceptions may contain sensitive data.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re

from flow_service import FlowService
from nh_transport import NHTransport
from token_store import DynamoTokenStore, SharedTokenManager


class RuntimeConfigurationError(RuntimeError):
    """An intentionally non-sensitive runtime initialization failure."""


def _credential_id(key: str, secret: str) -> str:
    # An HMAC avoids storing keys, secrets or their reversible representation.
    # Changing either credential selects a new, uninitialized token record.
    return hmac.new(secret.encode("utf-8"), key.encode("utf-8"), hashlib.sha256).hexdigest()


def build_service(config, clients, sanitize_rows, transport_factory=NHTransport):
    """Construct a service with injected AWS clients, without an NH request.

    DynamoDB token records must be provisioned separately after the existing
    local issuer has stopped and the current token is known to be expired. A
    missing record is intentionally fail-closed, not initialized on demand.
    """
    try:
        if not isinstance(config, dict) or not isinstance(clients, dict) or not callable(sanitize_rows):
            raise ValueError("invalid runtime input")
        parameter = config.get("SSM_PARAMETER_NAME", "")
        table = config.get("TOKEN_TABLE_NAME", "")
        if (not isinstance(parameter, str) or not re.fullmatch(r"/yeonma/private/[A-Za-z0-9_.-]+", parameter)
                or not isinstance(table, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{3,255}", table)):
            raise ValueError("invalid runtime configuration")
        if any(name not in clients for name in ("ssm", "dynamodb")):
            raise ValueError("missing runtime client")
        raw = clients["ssm"].get_parameter(Name=parameter, WithDecryption=True)["Parameter"]["Value"]
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("invalid credential format")
        key, secret = data.get("key"), data.get("secret")
        if not all(isinstance(value, str) and 1 <= len(value) <= 4096
                   and all(33 <= ord(char) <= 126 for char in value) for value in (key, secret)):
            raise ValueError("invalid credential format")
        identity = _credential_id(key, secret)
        transport = transport_factory(key, secret)
        store = DynamoTokenStore(clients["dynamodb"], table, "nh-" + identity)
        manager = SharedTokenManager(store, transport.issue_once)
        return FlowService(manager, transport, sanitize_rows)
    except Exception:
        # No provider error, raw parameter, key or secret should escape.
        raise RuntimeConfigurationError("private service initialization failed") from None
