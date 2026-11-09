import copy
from datetime import datetime
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from closing_collector import collect, RULE_ARN, FUNCTION_ARN
import handler
from flow_service import FlowService


class ClosingCollectorTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.fromisoformat('2026-11-09T07:10:10+00:00')
        self.event = {'version': '0', 'source': 'aws.events', 'detail-type': 'Scheduled Event',
                      'account': '514670561185', 'region': 'us-east-1', 'resources': [RULE_ARN],
                      'time': '2026-11-09T07:10:00Z', 'detail': {}}
        self.context = SimpleNamespace(invoked_function_arn=FUNCTION_ARN)
        self.service = Mock()
        self.service.session_provider.return_value = {'date': '2026-11-09', 'closed': True}
        self.service.get.return_value = {'tradeDate': '2026-11-09', 'dateVerified': True, 'persisted': True,
                                         'sessionStatus': 'closed', 'amount': [{}]*261, 'quantity': [{}]*261}
        self.factory = Mock(return_value=self.service)

    def run_collection(self):
        return collect(self.event, self.context, self.factory, utcnow=lambda: self.now)

    def test_collects_without_browser_or_google_session(self):
        result = self.run_collection()
        self.assertEqual(result, {'status': 'saved', 'date': '2026-11-09', 'rows': {'amount': 261, 'quantity': 261}})
        self.service.get.assert_called_once_with('2026-11-09')

    def test_repeated_scheduled_run_reuses_saved_close_without_nh_or_token(self):
        archive, token, transport = Mock(), Mock(), Mock()
        saved = []
        archive.read.side_effect = lambda _date: saved[0] if saved else None
        archive.save.side_effect = lambda data: saved.append(copy.deepcopy(data))
        transport.read_flow.return_value = {'Output_0': [
            {'bsop_hour': '15:30:00', 'timez12': '000000153000', 'frgn_val': '-10', 'prsn_val': '4', 'orgn_val': '6'}]}
        service = FlowService(token, transport, lambda p: p['Output_0'], utcnow=lambda: self.now,
                              archive=archive, session_provider=self.service.session_provider)
        self.factory.return_value = service
        self.assertEqual(self.run_collection()['status'], 'saved')
        service.cached = None
        self.assertEqual(self.run_collection()['status'], 'saved')
        self.assertEqual(transport.read_flow.call_count, 2)
        token.get_token.assert_called_once()
        archive.save.assert_called_once()

    def test_wrong_source_resource_context_and_http_envelope_are_rejected(self):
        original = copy.deepcopy(self.event)
        for key, value in [('version', '2.0'), ('source', 'external'), ('account', 'other'),
                           ('region', 'other'), ('resources', [RULE_ARN+'-other']), ('detail', {'command': 'x'})]:
            self.event = dict(original, **{key: value})
            self.assertEqual(self.run_collection()['status'], 'rejected')
        self.event = original
        self.context.invoked_function_arn = FUNCTION_ARN+'-other'
        self.assertEqual(self.run_collection()['status'], 'rejected')
        self.factory.assert_not_called()

    def test_late_future_and_invalid_events_do_not_touch_service(self):
        for stamp in ['2026-11-09T06:50:00Z', '2026-11-09T07:12:00Z', 'bad', '2026-11-09T07:10:00']:
            self.event['time'] = stamp
            self.assertIn(self.run_collection()['status'], ('expired', 'rejected'))
        self.factory.assert_not_called()

    def test_weekends_and_non_closing_hours_skip_without_credentials(self):
        for stamp in ['2026-11-07T07:10:00+00:00', '2026-11-09T01:10:00+00:00']:
            self.now = datetime.fromisoformat(stamp)
            self.event['time'] = stamp
            self.assertEqual(self.run_collection()['status'], 'outside-window')
        self.factory.assert_not_called()

    def test_holiday_and_market_open_do_not_call_nh_get(self):
        self.service.session_provider.return_value = {'date': '2026-11-06', 'closed': True}
        self.assertEqual(self.run_collection()['reason'], 'not-trading-day')
        self.service.session_provider.return_value = {'date': '2026-11-09', 'closed': False}
        self.assertEqual(self.run_collection()['reason'], 'market-open')
        self.service.get.assert_not_called()

    def test_incomplete_wrong_day_or_unverified_snapshot_raise_for_retry(self):
        original = self.service.get.return_value
        for key, value in [('sessionStatus', 'partial'), ('tradeDate', '2026-11-06'),
                           ('dateVerified', False), ('persisted', False)]:
            self.service.get.return_value = dict(original, **{key: value})
            with self.assertRaisesRegex(RuntimeError, '^NH closing collection failed$'):
                self.run_collection()

    def test_provider_exception_is_sanitized(self):
        self.service.session_provider.side_effect = RuntimeError('private token must not escape')
        with self.assertRaises(RuntimeError) as error:
            self.run_collection()
        self.assertNotIn('private token', str(error.exception))
        self.assertIsNone(error.exception.__cause__)

    def test_http_api_cannot_inject_scheduled_event(self):
        http_event = dict(self.event, version='2.0', rawPath='/api/private/nh/session/flow',
                          requestContext={'http': {'method': 'GET'}})
        with patch.object(handler, '_new_runtime_service') as factory:
            self.assertEqual(handler.lambda_handler(http_event, self.context), {'status': 'rejected'})
            factory.assert_not_called()


if __name__ == '__main__': unittest.main()
