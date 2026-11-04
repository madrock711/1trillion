"""Experimental composition of shared token manager and read-only NH transport.

Not initialized by the production handler. All dependencies must be injected.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone


class FlowService:
    def __init__(self, token_manager, transport, sanitize_rows, monotonic=time.monotonic, utcnow=None):
        self.token_manager, self.transport, self.sanitize_rows = token_manager, transport, sanitize_rows
        self.monotonic = monotonic
        self.utcnow = utcnow or (lambda: datetime.now(timezone.utc))
        self.lock = threading.Lock()
        self.cached, self.cached_at = None, 0.0

    def get(self):
        with self.lock:
            if self.cached is not None and self.monotonic() - self.cached_at < 30:
                return self.cached
            token = self.token_manager.get_token()
            series = {}
            for name in ("amount", "quantity"):
                payload = self.transport.read_flow(token, name)
                series[name] = self.sanitize_rows(payload)
            self.cached = {"source": "NH PLUG", "market": "UNT", "fetchedAt": self.utcnow().isoformat(),
                           "tradeDate": None, "unitsVerified": False, **series}
            self.cached_at = self.monotonic()
            return self.cached
