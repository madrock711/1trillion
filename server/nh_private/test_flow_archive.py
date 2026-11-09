import copy
from datetime import datetime, timezone
import unittest
from unittest.mock import Mock
from flow_archive import FlowArchive
from flow_service import FlowService


class Ddb:
    def __init__(self): self.rows = {}
    def get_item(self, **k): return {'Item': copy.deepcopy(self.rows.get(k['Key']['id']['S']))}
    def update_item(self, **k):
        key, v = k['Key']['id']['S'], k['ExpressionAttributeValues']
        if ':p' in v:
            self.rows[key] = {'payload': v[':p'], 'fetched_at': v[':at']}
        else: self.rows[key] = {'trade_date': v[':d']}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.db = Ddb(); self.archive = FlowArchive(self.db, 'table', 'private-id')
        self.now = datetime.fromisoformat('2026-11-09T08:00:00+00:00')
        self.token = Mock(); self.token.get_token.return_value = 'fake'
        self.transport = Mock()
        self.rows = [{'bsop_hour': '15:30:00', 'timez12': '000000153000', 'frgn_val': '-10', 'prsn_val': '4', 'orgn_val': '6'},
                     {'bsop_hour': '15:25:00', 'timez12': '000000152500', 'frgn_val': '-9', 'prsn_val': '4', 'orgn_val': '5'}]
        self.transport.read_flow.return_value = {'Output_0': self.rows}
        self.provider = Mock(return_value={'date': '2026-11-09', 'closed': True})
        self.service = FlowService(self.token, self.transport, lambda p: p['Output_0'],
            utcnow=lambda: self.now, archive=self.archive, session_provider=self.provider)

    def test_close_persist_restore_and_no_further_nh_calls(self):
        data = self.service.get('2026-11-09')
        self.assertEqual(data['sessionStatus'], 'closed')
        self.assertEqual(self.archive.read('2026-11-09'), data)
        self.assertEqual(self.archive.latest(), data)
        self.service.cached = None  # Lambda replacement / fresh process
        self.assertEqual(self.service.get('2026-11-09'), data)
        self.assertEqual(self.transport.read_flow.call_count, 2)
        self.now = datetime.fromisoformat('2026-11-10T10:00:00+00:00')
        self.provider.side_effect = RuntimeError('provider unavailable')
        self.assertEqual(self.service.get('2026-11-09'), data)
        self.assertEqual(self.transport.read_flow.call_count, 2)

    def test_partial_is_not_mislabeled_closed(self):
        self.transport.read_flow.return_value = {'Output_0': self.rows[1:]}
        self.assertEqual(self.service.get()['sessionStatus'], 'partial')

    def test_wrong_day_and_missing_history_never_fetch_nh(self):
        self.provider.return_value = {'date': '2026-11-06', 'closed': True}
        with self.assertRaises(ValueError): self.service.get()
        with self.assertRaises(ValueError): self.service.get('2026-11-06')
        self.token.get_token.assert_not_called()

    def test_date_rollover_during_collection_is_not_saved(self):
        self.provider.side_effect = [{'date': '2026-11-09', 'closed': False}, {'date': '2026-11-10', 'closed': False}]
        with self.assertRaises(ValueError): self.service.get()
        self.assertIsNone(self.archive.read('2026-11-09'))

    def test_future_invalid_dates_and_non_regular_rows_rejected(self):
        for date in ('2026-11-10', '2026-02-30', '../secret'):
            with self.assertRaises(ValueError): self.service.get(date)
        self.transport.read_flow.return_value = {'Output_0': [{'bsop_hour': '20:00:00', 'timez12': '000000200000'}]}
        with self.assertRaises(ValueError): self.service.get()
        self.assertIsNone(self.archive.read('2026-11-09'))

    def test_date_provider_outage_returns_only_saved_snapshot(self):
        data = self.service.get()
        self.service.cached = None
        self.provider.side_effect = RuntimeError('offline')
        self.assertEqual(self.service.get('2026-11-09'), data)


if __name__ == '__main__': unittest.main()
