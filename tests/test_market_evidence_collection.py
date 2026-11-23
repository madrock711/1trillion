import importlib.util
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('collector', ROOT/'scripts/collect_market_evidence.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
sys.path.insert(0, str(ROOT/'scripts'))
import market_research_indicators as indicators


class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return b'{"price": 10}'


class CollectionTest(unittest.TestCase):
    def test_one_failure_preserves_other_sources_and_manifest(self):
        base = ROOT/'.tmp-market-tests'
        base.mkdir(exist_ok=True)
        def open_url(req, **kwargs):
            if req.full_url.endswith('/fail'):
                raise urllib.error.URLError('fixture DNS failure')
            return Response()
        with tempfile.TemporaryDirectory(dir=base) as temp, patch.object(collector.urllib.request, 'urlopen', side_effect=open_url):
            output = Path(temp)
            manifest = collector.collect({'failed':'https://example.org/fail', 'good':'https://example.org/ok'}, output)
            self.assertEqual(['failed'], manifest['failed'])
            self.assertEqual('collected', manifest['sources']['good']['status'])
            self.assertEqual('failed', json.loads((output/'failed.json').read_text())['status'])
            self.assertTrue(json.loads((output/'good.json').read_text())['rawHash'])
            self.assertTrue((output/'collection-status.json').exists())

    def test_final_query_keeps_fx_nxt_and_futures(self):
        urls = collector.sources(final=True)
        self.assertTrue({'FX','NXT','yahoo-NQF','yahoo-ESF','005930','000660'} <= urls.keys())
        self.assertNotIn('yahoo-QQQ', urls)
        self.assertIn('interval=5m', urls['yahoo-NQF'])

    def test_weekly_comparison_and_trailing_complete_months(self):
        start = dt.date(2026, 6, 1)
        as_of = dt.date(2026, 10, 12)
        latest = dt.date(2026, 10, 8)
        points = {day: day.month * 10 for day in indicators.date_range(start, latest + dt.timedelta(days=1))}
        points[latest] = 108
        data = indicators.summarize_nsi(points, as_of)
        self.assertEqual(('2026-10-08', 8, '2026-09', 80, 10), (
            data['period'], data['change7d'], data['average3mPeriod'], data['average3m'], data['average3mChange']
        ))
        del points[dt.date(2026, 9, 15)]
        self.assertIsNone(indicators.summarize_nsi(points, as_of)['average3m'])
        with self.assertRaises(ValueError):
            indicators.summarize_nsi(points, dt.date(2026, 11, 1))

    def test_optional_failure_keeps_other_series_and_old_evidence_is_hidden(self):
        base = ROOT/'.tmp-market-tests'
        base.mkdir(exist_ok=True)
        today = dt.datetime.now(indicators.TZ).date()
        with tempfile.TemporaryDirectory(dir=base) as temp, \
                patch.object(indicators, 'fetch_nsi', side_effect=urllib.error.URLError('timeout')), \
                patch.object(indicators, 'fetch_market_history', side_effect=urllib.error.URLError('timeout')), \
                patch.object(indicators, 'fetch_leading', return_value={
                    'period': indicators.month_before(today, 1).strftime('%Y-%m'),
                    'value': 104.1, 'change': -0.1, 'rawHash': 'a' * 64,
                }):
            output = Path(temp)
            indicators.collect_indicators(output)
            evidence = json.loads((output/indicators.FILENAME).read_text(encoding='utf-8'))
        cutoff = dt.datetime.now(indicators.TZ)
        self.assertEqual('unavailable', evidence['nsi']['status'])
        self.assertEqual('unavailable', evidence['marketHistory']['nasdaq']['status'])
        rows = indicators.indicator_rows(evidence, cutoff)
        self.assertEqual(['104.1'], [row['value'] for row in rows])
        self.assertIn('0.1포인트 하락', indicators.render_indicator_block(rows)[0])
        self.assertEqual([], indicators.indicator_rows(evidence, cutoff + dt.timedelta(days=1)))


if __name__ == '__main__': unittest.main()
