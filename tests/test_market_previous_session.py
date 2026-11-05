import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publish_market_research import previous_session


class PreviousSessionTests(unittest.TestCase):
    def evidence(self):
        return {'KOSPI': {'data': []}, 'KOSPI-basic': {'data': {'marketStatus': 'PREOPEN', 'closePrice': '5383.8'}},
                'KOSPI-history': {'data': {'code': 'KOSPI', 'priceInfos': [
                    {'localDate': '20261104', 'closePrice': 5683.8},
                    {'localDate': '20261105', 'openPrice': 5580.09, 'highPrice': 5586.46, 'lowPrice': 5336.88, 'closePrice': 5383.8}]}}}

    def test_delayed_daily_list_uses_matching_valid_chart(self):
        row = previous_session(self.evidence(), '2026-11-05')
        self.assertEqual(float(row['closePrice']), 5383.8)
        self.assertEqual(float(row['fluctuationsRatio']), -5.28)

    def test_rejects_conflicting_preopen_close(self):
        ev = self.evidence()
        ev['KOSPI-basic']['data']['closePrice'] = '5683.8'
        with self.assertRaises(ValueError):
            previous_session(ev, '2026-11-05')

    def test_rejects_invalid_ohlc(self):
        ev = self.evidence()
        ev['KOSPI-history']['data']['priceInfos'][-1]['lowPrice'] = 6000
        with self.assertRaises(ValueError):
            previous_session(ev, '2026-11-05')
