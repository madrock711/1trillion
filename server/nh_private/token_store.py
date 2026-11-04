"""Experimental shared NH token coordination; deployment remains blocked.

Tokens are stored as plaintext table attributes. DynamoDB encrypts storage at
rest by default and clients use TLS in transit, but any principal with access
to read the item can see the bearer token. Strict IAM remains essential.
Only a truly single-attempt, non-retrying issuer can satisfy this contract.
"""
from __future__ import annotations

import secrets
import time


class TokenUnavailable(RuntimeError):
    pass


class DynamoTokenStore:
    """Low-level DynamoDB client; conditional writes serialize all issue attempts."""

    def __init__(self, ddb, table, key):
        self.ddb, self.table, self.key = ddb, table, key

    def read(self):
        item = self.ddb.get_item(TableName=self.table, Key={"id": {"S": self.key}}, ConsistentRead=True).get("Item")
        if not item:
            raise TokenUnavailable("token migration is not initialized")
        try:
            state = item["state"]["S"]
            version = int(item["version"]["N"])
            not_before = int(item["not_before"]["N"])
            record = {"state": state, "version": version, "not_before": not_before}
            if state == "VALID":
                record["usable_until"] = int(item["usable_until"]["N"])
                record["token"] = bytes(item["token"]["B"])
            if state not in ("READY", "ISSUING", "VALID", "UNCERTAIN") or version < 0:
                raise ValueError("invalid state")
            return record
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise TokenUnavailable("invalid token state") from exc

    def claim(self, record, attempt, now):
        self.ddb.update_item(
            TableName=self.table, Key={"id": {"S": self.key}},
            UpdateExpression="SET #state = :issuing, #version = :next, attempt = :attempt",
            ConditionExpression="#state = :expected AND #version = :version AND not_before <= :now",
            ExpressionAttributeNames={"#state": "state", "#version": "version"},
            ExpressionAttributeValues={":issuing": {"S": "ISSUING"}, ":next": {"N": str(record["version"] + 1)},
                                       ":attempt": {"S": attempt}, ":expected": {"S": record["state"]},
                                       ":version": {"N": str(record["version"])}, ":now": {"N": str(now)}})

    def commit(self, attempt, token, usable_until, not_before):
        self.ddb.update_item(
            TableName=self.table, Key={"id": {"S": self.key}},
            UpdateExpression="SET #state = :valid, #version = #version + :one, #token = :token, usable_until = :usable, not_before = :not_before REMOVE attempt",
            ConditionExpression="#state = :issuing AND attempt = :attempt",
            ExpressionAttributeNames={"#state": "state", "#version": "version", "#token": "token"},
            ExpressionAttributeValues={":valid": {"S": "VALID"}, ":one": {"N": "1"},
                                       ":token": {"B": token}, ":usable": {"N": str(usable_until)},
                                       ":not_before": {"N": str(not_before)}, ":issuing": {"S": "ISSUING"},
                                       ":attempt": {"S": attempt}})

    def uncertain(self, attempt):
        self.ddb.update_item(
            TableName=self.table, Key={"id": {"S": self.key}},
            UpdateExpression="SET #state = :uncertain, #version = #version + :one REMOVE attempt",
            ConditionExpression="#state = :issuing AND attempt = :attempt",
            ExpressionAttributeNames={"#state": "state", "#version": "version"},
            ExpressionAttributeValues={":uncertain": {"S": "UNCERTAIN"}, ":one": {"N": "1"},
                                       ":issuing": {"S": "ISSUING"}, ":attempt": {"S": attempt}})


class SharedTokenManager:
    def __init__(self, store, issue_once, clock=time.time, margin=120):
        if not callable(issue_once) or margin < 60:
            raise ValueError("token issuer is not configured")
        self.store, self.issue_once = store, issue_once
        self.clock, self.margin = clock, margin

    def get_token(self):
        try:
            return self._get_token()
        except TokenUnavailable:
            raise
        except Exception:
            # Internal provider and AWS messages may contain secrets; suppress them.
            raise TokenUnavailable("token unavailable") from None

    def _get_token(self):
        record = self.store.read()
        now = int(self.clock())
        if record["state"] == "VALID" and now < record["usable_until"]:
            value = record["token"]
            if not isinstance(value, bytes) or not value:
                raise TokenUnavailable("token unavailable")
            return value.decode("utf-8")
        if record["state"] not in ("READY", "VALID") or now < record["not_before"]:
            raise TokenUnavailable("token unavailable")

        attempt = secrets.token_hex(16)
        # A failed or ambiguous conditional claim does NOT permit an issue request.
        self.store.claim(record, attempt, now)
        started = int(self.clock())
        try:
            result = self.issue_once()  # exactly one local invocation; no implicit retries here
            finished = int(self.clock())
            if not isinstance(result, dict):
                raise ValueError("invalid token result")
            token, lifetime = result.get("access_token"), result.get("expires_in")
            if not isinstance(token, str) or not token or not isinstance(lifetime, int) or isinstance(lifetime, bool) or not (self.margin * 2 < lifetime <= 86400):
                raise ValueError("invalid token result")
            if finished < started:
                raise ValueError("clock moved backwards")
            # Use only before earliest plausible expiry; issue again only after latest.
            usable_until = started + lifetime - self.margin
            not_before = finished + lifetime + self.margin
            self.store.commit(attempt, token.encode("utf-8"), usable_until, not_before)
            if int(self.clock()) >= usable_until:
                raise TokenUnavailable("token unavailable")
            return token
        except Exception:
            # A timed-out write might have succeeded. Conditional marking cannot
            # overwrite VALID; if it cannot be marked, ISSUING remains fail-closed.
            try:
                self.store.uncertain(attempt)
            except Exception:
                pass
            raise TokenUnavailable("token unavailable") from None
