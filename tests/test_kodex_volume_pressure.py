import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_kodex_volume_pressure.py"
SPEC = importlib.util.spec_from_file_location("kodex_volume_pressure", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def bar(date, time, close, volume):
    return MODULE.MinuteBar(
        timestamp=datetime.strptime(date + time, "%Y-%m-%d%H%M").replace(tzinfo=MODULE.SEOUL),
        close=close,
        volume=volume,
    )


class KodexVolumePressureTests(unittest.TestCase):
    def setUp(self):
        self.date = "2026-08-05"
        self.collected_at = datetime(2026, 8, 6, 7, 20, tzinfo=MODULE.timezone.utc)

    def complete_bars(self, second_close=101.0):
        rows = [bar(self.date, "0900", 100.0, 100)]
        for minute in range(1, 300):
            hour = 9 + minute // 60
            minute_of_hour = minute % 60
            rows.append(bar(self.date, f"{hour:02d}{minute_of_hour:02d}", second_close, 10))
        rows.append(bar(self.date, "1530", second_close, 100))
        return rows

    def test_rising_minutes_increase_estimated_buy_pressure(self):
        bars = self.complete_bars(second_close=110.0)
        result = MODULE.estimate_day(
            self.date,
            bars,
            sum(item.volume for item in bars) + 50,
            sigma=1.0,
            sigma_sample_size=300,
            collected_at=self.collected_at,
        )
        self.assertGreater(result["estimatedBuyVolume"], result["estimatedSellVolume"])
        self.assertEqual(result["estimatedBuyVolume"] + result["estimatedSellVolume"], result["dailyVolume"])

    def test_falling_minutes_increase_estimated_sell_pressure(self):
        bars = self.complete_bars(second_close=90.0)
        result = MODULE.estimate_day(
            self.date,
            bars,
            sum(item.volume for item in bars),
            sigma=1.0,
            sigma_sample_size=300,
            collected_at=self.collected_at,
        )
        self.assertGreater(result["estimatedSellVolume"], result["estimatedBuyVolume"])

    def test_auction_and_uncovered_volume_are_neutral(self):
        bars = self.complete_bars(second_close=100.0)
        minute_volume = sum(item.volume for item in bars)
        result = MODULE.estimate_day(
            self.date,
            bars,
            minute_volume + 100,
            sigma=1.0,
            sigma_sample_size=300,
            collected_at=self.collected_at,
        )
        self.assertEqual(result["estimatedBuyVolume"], result["estimatedSellVolume"])
        self.assertEqual(result["neutralVolume"], 300)

    def test_existing_date_is_not_replaced_without_explicit_request(self):
        archive = MODULE.empty_archive()
        original = {"date": self.date, "dailyVolume": 100, "estimatedBuyVolume": 55, "estimatedSellVolume": 45}
        archive["days"] = [original]
        incoming = [{"date": self.date, "dailyVolume": 200, "estimatedBuyVolume": 100, "estimatedSellVolume": 100}]
        merged, changed = MODULE.merge_days(archive, incoming, self.collected_at)
        self.assertEqual(changed, [])
        self.assertIs(merged, archive)
        self.assertEqual(merged["days"][0], original)

    def test_archive_write_is_stable_and_sorted(self):
        archive = MODULE.empty_archive()
        incoming = [
            {"date": "2026-08-05", "dailyVolume": 100, "estimatedBuyVolume": 50, "estimatedSellVolume": 50},
            {"date": "2026-08-04", "dailyVolume": 100, "estimatedBuyVolume": 50, "estimatedSellVolume": 50},
        ]
        merged, changed = MODULE.merge_days(archive, incoming, self.collected_at)
        self.assertEqual(changed, ["2026-08-04", "2026-08-05"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "archive.json"
            content = MODULE.serialize_archive(merged)
            MODULE.write_atomic(output, content)
            self.assertEqual(output.read_text(encoding="utf-8"), content)
            decoded = json.loads(content)
            self.assertEqual([row["date"] for row in decoded["days"]], ["2026-08-04", "2026-08-05"])


if __name__ == "__main__":
    unittest.main()
