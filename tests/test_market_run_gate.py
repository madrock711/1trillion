import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gate", ROOT / "scripts/check_market_run.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class RunGateTest(unittest.TestCase):
    def setUp(self):
        base = ROOT / ".tmp-market-tests"
        base.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.day = "2026-11-05"
        self.evidence = self.root / "research/evidence" / self.day
        self.evidence.mkdir(parents=True)

    def save(self, data):
        (self.evidence / "run-status.json").write_text(json.dumps(data), encoding="utf-8")

    def complete(self):
        state = {"status": "complete", "finalCommit": "a" * 40, "deploymentJob": "1",
                 "stages": {s: "2026-11-05T08:15:00+09:00" for s in gate.STAGES}}
        self.save(state)
        for name in ("reports/2026-11-05.md", "articles/market-2026-11-05.html"):
            p = self.root / name
            p.parent.mkdir(exist_ok=True)
            p.write_text("fixture", encoding="utf-8")
        (self.evidence / "live-check.json").write_text(json.dumps([
            {"status": 200, "sha256": "a" * 64, "checkedAt": "2026-11-05T08:16:00+09:00"}]), encoding="utf-8")
        return state

    def test_missing_status_continues(self):
        self.assertTrue(gate.inspect(self.root, self.day))

    def test_collection_success_is_not_completion(self):
        self.save({"status": "incomplete", "stages": {"research": "started"}, "evidence": ["collect exit0"]})
        remaining = gate.inspect(self.root, self.day)
        self.assertIn("writing: 완료 시각 없음", remaining)
        self.assertIn("최종 라이브 증거 없음", remaining)

    def test_complete_label_cannot_hide_missing_proof(self):
        self.save({"status": "complete", "stages": {}})
        self.assertTrue(gate.inspect(self.root, self.day))

    def test_previous_day_stages_rejected(self):
        state = self.complete()
        state["stages"]["live"] = "2026-11-04T08:00:00+09:00"
        self.save(state)
        self.assertIn("live: 완료 시각 없음", gate.inspect(self.root, self.day))

    def test_evidence_presence_not_network_proof(self):
        self.complete()
        self.assertEqual([], gate.inspect(self.root, self.day))

    def test_http_failure_rejected(self):
        self.complete()
        (self.evidence / "live-check.json").write_text('[{"status": 404}]', encoding="utf-8")
        self.assertTrue(gate.inspect(self.root, self.day))


if __name__ == "__main__":
    unittest.main()
