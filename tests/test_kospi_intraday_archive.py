import importlib.util
import sys
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_kospi_intraday_archive.py"
SPEC = importlib.util.spec_from_file_location("kospi_intraday_archive", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class KospiIntradayArchiveTests(unittest.TestCase):
    def test_csat_session_rejects_normal_close_and_keeps_extended_bars(self):
        date = "2026-11-19"
        opening = datetime.fromisoformat(date + "T10:00:00")
        rows = [
            {"localDateTime": (opening + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S"),
             "openPrice": 5000, "highPrice": 5001, "lowPrice": 5000,
             "currentPrice": 5001, "accumulatedTradingVolume": 100}
            for index in range(391)
        ]
        self.assertIn("endDateTime=202611191630", MODULE.minute_url(date))
        with self.assertRaisesRegex(ValueError, "completed minute session unavailable"):
            MODULE.normalize_minute_rows(rows[:331], date)
        self.assertEqual(MODULE.normalize_minute_rows(rows, date)[-1]["time"], "16:30")

    def test_retired_flow_endpoint_keeps_verified_prices_with_missing_flow(self):
        price = {"time": "15:30", "open": 6715, "high": 6717, "low": 6714, "close": 6716, "volume": 6809}
        gone = urllib.error.HTTPError("https://finance.naver.com/", 410, "Gone", {}, None)
        with patch.object(MODULE, "fetch_json", return_value=[]), \
                patch.object(MODULE, "normalize_minute_rows", return_value=[price]), \
                patch.object(MODULE, "collect_flow_rows", side_effect=gone):
            day = MODULE.build_day("2026-09-17", datetime(2026, 9, 18, tzinfo=timezone.utc))
        self.assertEqual(day["flowSnapshotCount"], 0)
        self.assertIsNone(day["flowSourceLastAt"])
        self.assertIsNone(day["bars"][0]["foreign"])
        self.assertEqual(day["bars"][0]["close"], 6716)

    def test_other_flow_http_failures_stay_visible(self):
        failure = urllib.error.HTTPError("https://finance.naver.com/", 503, "Unavailable", {}, None)
        with patch.object(MODULE, "fetch_json", return_value=[]), \
                patch.object(MODULE, "normalize_minute_rows", return_value=[{"time": "15:30", "close": 1, "volume": 1}]), \
                patch.object(MODULE, "collect_flow_rows", side_effect=failure):
            with self.assertRaises(urllib.error.HTTPError):
                MODULE.build_day("2026-09-17", datetime(2026, 9, 18, tzinfo=timezone.utc))
