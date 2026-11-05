import json
import os
import unittest
from unittest.mock import patch
import handler
from session_store import Sessions, cookie
from test_session_store import MemoryDdb

CONFIG = {'GOOGLE_CLIENT_ID': 'test.apps.googleusercontent.com', 'OWNER_GOOGLE_SUB': '1234',
          'OWNER_EMAIL': 'owner@gmail.com', 'SSM_PARAMETER_NAME': '/nh',
          'TOKEN_TABLE_NAME': 'table', 'ALLOWED_ORIGIN': 'https://www.hpmplab.com'}

def request(path, method='GET', token='', csrf='', claims=True, origin=CONFIG['ALLOWED_ORIGIN']):
    event = {'version': '2.0', 'rawPath': path, 'headers': {'origin': origin, 'x-yeonma-csrf': csrf},
             'cookies': [cookie(token)] if token else [], 'requestContext': {'http': {'method': method}}}
    if claims:
        event['requestContext']['authorizer'] = {'jwt': {'claims': {
            'aud': CONFIG['GOOGLE_CLIENT_ID'], 'iss': 'https://accounts.google.com',
            'sub': CONFIG['OWNER_GOOGLE_SUB'], 'email': CONFIG['OWNER_EMAIL'], 'email_verified': 'true'}}}
    return event

class BrowserSessionTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.store = Sessions(MemoryDdb(), 'table', '1234:owner@gmail.com', lambda: self.now)
        for p in [patch.dict(os.environ, CONFIG, clear=True), patch.object(handler, 'SESSION_STORE', self.store)]:
            p.start()
            self.addCleanup(p.stop)

    def login(self):
        response = handler.lambda_handler(request(handler.SESSION_LOGIN, 'POST'), None)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('no-store', response['headers']['Cache-Control'])
        token = response['cookies'][0].split('=', 1)[1].split(';', 1)[0]
        return token, json.loads(response['body'])

    def test_login_restore_logout_and_replay(self):
        token, payload = self.login()
        event = request(handler.SESSION_STATE, token=token, claims=False)
        self.assertEqual(json.loads(handler.lambda_handler(event, None)['body']), payload)
        result = handler.lambda_handler(request(handler.SESSION_LOGOUT, 'POST', token, payload['csrfToken'], claims=False), None)
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('Max-Age=0', result['cookies'][0])
        self.assertEqual(handler.lambda_handler(event, None)['statusCode'], 401)

    def test_expired_forged_and_missing_cannot_read_flow(self):
        token, payload = self.login()
        self.now = payload['expiresAt']
        with patch.object(handler, '_flow') as flow:
            for value in [token, '', 'x' * 43]:
                self.assertEqual(handler.lambda_handler(request(handler.SESSION_FLOW, token=value, claims=False), None)['statusCode'], 401)
            flow.assert_not_called()

    def test_login_requires_verified_owner_and_exact_origin(self):
        for event in [request(handler.SESSION_LOGIN, 'POST', claims=False), request(handler.SESSION_LOGIN, 'POST', origin=''),
                      request(handler.SESSION_LOGIN, 'POST', origin='https://evil.example')]:
            with patch.object(handler, '_sessions') as store:
                self.assertEqual(handler.lambda_handler(event, None)['statusCode'], 403)
                store.assert_not_called()

    def test_csrf_and_rotation(self):
        token, _ = self.login()
        for csrf in ['', 'wrong']:
            self.assertEqual(handler.lambda_handler(request(handler.SESSION_LOGOUT, 'POST', token, csrf), None)['statusCode'], 403)
        self.assertEqual(handler.lambda_handler(request(handler.SESSION_LOGIN, 'POST', token), None)['statusCode'], 200)
        self.assertIsNone(self.store.read(token))

    def test_session_never_initializes_nh(self):
        with patch.object(handler, '_flow') as flow, patch.object(handler, '_new_runtime_service') as nh:
            token, _ = self.login()
            handler.lambda_handler(request(handler.SESSION_STATE, token=token, claims=False), None)
            flow.assert_not_called()
            nh.assert_not_called()
        with patch.object(handler, 'TOKEN_CACHE_READY', False):
            self.assertEqual(handler.lambda_handler(request(handler.SESSION_FLOW, token=token, claims=False), None)['statusCode'], 503)

if __name__ == '__main__':
    unittest.main()
