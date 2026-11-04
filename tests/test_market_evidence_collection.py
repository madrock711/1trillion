import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('collector', ROOT/'scripts/collect_market_evidence.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


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


if __name__ == '__main__': unittest.main()
