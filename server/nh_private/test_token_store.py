import importlib.util
from pathlib import Path
import threading
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("token_store", Path(__file__).with_name("token_store.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeDdb:
    def __init__(self, state="READY", not_before=0):
        self.lock = threading.Lock()
        self.item = None if state is None else {"id": {"S": "one"}, "state": {"S": state},
                    "version": {"N": "0"}, "not_before": {"N": str(not_before)}}
        self.fail_claim = False
        self.fail_commit_before = False
        self.fail_commit_after = False
        self.fail_uncertain = False

    def get_item(self, **kwargs):
        assert kwargs["ConsistentRead"] is True
        with self.lock:
            return {"Item": dict(self.item)} if self.item else {}

    def update_item(self, **kwargs):
        values = kwargs["ExpressionAttributeValues"]
        expression = kwargs["ConditionExpression"]
        with self.lock:
            item = self.item
            if ":expected" in values:
                assert "#state = :expected" in expression and "#version = :version" in expression and "not_before <= :now" in expression
                if self.fail_claim or not item or item["state"] != values[":expected"] or item["version"] != values[":version"] or int(item["not_before"]["N"]) > int(values[":now"]["N"]):
                    raise RuntimeError("claim failed")
                item.update({"state": values[":issuing"], "version": values[":next"], "attempt": values[":attempt"]})
                return
            assert "#state = :issuing" in expression and "attempt = :attempt" in expression
            if not item or item["state"] != values[":issuing"] or item.get("attempt") != values[":attempt"]:
                raise RuntimeError("condition failed")
            if ":valid" in values:
                if self.fail_commit_before:
                    raise RuntimeError("commit before")
                item.update({"state": values[":valid"], "version": {"N": str(int(item["version"]["N"]) + 1)},
                             "token": values[":token"], "usable_until": values[":usable"],
                             "not_before": values[":not_before"]})
                item.pop("attempt", None)
                if self.fail_commit_after:
                    raise RuntimeError("commit response lost")
            else:
                if self.fail_uncertain:
                    raise RuntimeError("uncertain failed")
                item.update({"state": values[":uncertain"], "version": {"N": str(int(item["version"]["N"]) + 1)}})
                item.pop("attempt", None)


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.ddb = FakeDdb()
        self.now = 1000
        self.issue = mock.Mock(return_value={"access_token": "dummy-token", "expires_in": 86400})
        self.store = module.DynamoTokenStore(self.ddb, "test", "one")
        self.manager = module.SharedTokenManager(self.store, self.issue, clock=lambda: self.now)

    def test_one_issue_then_reuse_and_distinct_safety_boundaries(self):
        self.assertEqual(self.manager.get_token(), "dummy-token")
        self.assertEqual(self.manager.get_token(), "dummy-token")
        self.assertEqual(self.issue.call_count, 1)
        record = self.store.read()
        # DynamoDB storage encryption is transparent: table readers see plaintext.
        self.assertEqual(record["token"], b"dummy-token")
        self.assertEqual(record["usable_until"], 1000 + 86400 - 120)
        self.assertEqual(record["not_before"], 1000 + 86400 + 120)
        self.now = record["usable_until"]
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.assertEqual(self.issue.call_count, 1)
        self.now = record["not_before"]
        self.assertEqual(self.manager.get_token(), "dummy-token")
        self.assertEqual(self.issue.call_count, 2)

    def test_no_bootstrap_or_unresolved_states_do_not_issue(self):
        for state in (None, "ISSUING", "UNCERTAIN", "bad"):
            self.ddb.item = FakeDdb(state).item
            with self.assertRaises(module.TokenUnavailable):
                self.manager.get_token()
        self.issue.assert_not_called()

    def test_claim_failure_never_issues(self):
        self.ddb.fail_claim = True
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.issue.assert_not_called()

    def test_ambiguous_issue_is_fail_closed_and_not_retried(self):
        self.issue.side_effect = TimeoutError("sensitive")
        with self.assertRaises(module.TokenUnavailable) as error:
            self.manager.get_token()
        self.assertNotIn("sensitive", str(error.exception))
        self.assertEqual(self.store.read()["state"], "UNCERTAIN")
        self.now += 90000
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.assertEqual(self.issue.call_count, 1)

    def test_uncertain_write_failure_leaves_issuing_closed(self):
        self.issue.side_effect = TimeoutError()
        self.ddb.fail_uncertain = True
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.assertEqual(self.store.read()["state"], "ISSUING")
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.assertEqual(self.issue.call_count, 1)

    def test_commit_failure_and_lost_commit_response(self):
        self.ddb.fail_commit_before = True
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.assertEqual(self.store.read()["state"], "UNCERTAIN")
        self.ddb = FakeDdb()
        self.ddb.fail_commit_after = True
        self.store.ddb = self.ddb
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.assertEqual(self.store.read()["state"], "VALID")
        self.assertEqual(self.manager.get_token(), "dummy-token")
        self.assertEqual(self.issue.call_count, 2)

    def test_worker_stops_mid_issue_and_never_reissues_automatically(self):
        self.issue.side_effect = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.manager.get_token()
        self.assertEqual(self.store.read()["state"], "ISSUING")
        self.now += 90000
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.assertEqual(self.issue.call_count, 1)

    def test_corrupt_token_bytes_fail_closed_without_issuing(self):
        self.manager.get_token()
        self.ddb.item["token"] = {"B": b"\xff"}
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.assertEqual(self.issue.call_count, 1)

    def test_storage_errors_do_not_expose_token(self):
        with mock.patch.object(self.ddb, "get_item", side_effect=RuntimeError("sensitive-token-example")):
            with self.assertRaises(module.TokenUnavailable) as error:
                self.manager.get_token()
        self.assertNotIn("sensitive-token-example", str(error.exception))
        self.issue.assert_not_called()

    def test_bad_issue_response_does_not_retry(self):
        self.issue.return_value = {"access_token": "dummy", "expires_in": True}
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        self.assertEqual(self.store.read()["state"], "UNCERTAIN")
        self.assertEqual(self.issue.call_count, 1)

    def test_two_workers_only_one_issues(self):
        started, release = threading.Event(), threading.Event()
        def issue():
            started.set()
            release.wait(2)
            return {"access_token": "dummy-token", "expires_in": 86400}
        self.manager.issue_once = mock.Mock(side_effect=issue)
        results = []
        worker = threading.Thread(target=lambda: results.append(self.manager.get_token()))
        worker.start()
        self.assertTrue(started.wait(2))
        with self.assertRaises(module.TokenUnavailable):
            self.manager.get_token()
        release.set()
        worker.join(2)
        self.assertEqual(results, ["dummy-token"])
        self.assertEqual(self.manager.issue_once.call_count, 1)


if __name__ == "__main__":
    unittest.main()
