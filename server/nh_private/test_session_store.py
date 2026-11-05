import copy
import unittest
from session_store import Sessions, read_cookie, cookie, LIFETIME

class MemoryDdb:
    def __init__(self):
        self.items = {}

    def update_item(self, **kw):
        key, values = kw['Key']['id']['S'], kw['ExpressionAttributeValues']
        if ':exp' in values:
            assert key not in self.items
            self.items[key] = {'expires_at': values[':exp'], 'csrf': values[':csrf'],
                               'owner_hash': values[':owner'], 'revoked': values[':no']}
        else:
            self.items.setdefault(key, {})['revoked'] = values[':yes']

    def get_item(self, **kw):
        assert kw['ConsistentRead']
        return {'Item': copy.deepcopy(self.items.get(kw['Key']['id']['S']))}

class SessionTests(unittest.TestCase):
    def setUp(self):
        self.now, self.ddb = 1000, MemoryDdb()
        self.store = Sessions(self.ddb, 'table', 'owner', lambda: self.now)

    def test_create_hash_only_expiry_and_revocation(self):
        token, payload = self.store.create()
        self.assertNotIn(token, repr(self.ddb.items))
        self.assertEqual(self.store.read(token), payload)
        self.assertEqual(payload['expiresAt'], 1000 + LIFETIME)
        self.now = payload['expiresAt']
        self.assertIsNone(self.store.read(token))
        self.now = 1000
        self.store.revoke(token)
        self.assertIsNone(self.store.read(token))

    def test_wrong_owner_missing_and_malformed_records(self):
        token, _ = self.store.create()
        self.assertIsNone(Sessions(self.ddb, 'table', 'other').read(token))
        self.assertIsNone(self.store.read('unknown'))
        self.ddb.items[self.store.key(token)['id']['S']]['expires_at'] = {'N': 'bad'}
        self.assertIsNone(self.store.read(token))

    def test_cookie_parsing_and_flags(self):
        token, _ = self.store.create()
        self.assertEqual(read_cookie({'cookies': [cookie(token, LIFETIME)]}), token)
        self.assertEqual(read_cookie({'headers': {'cookie': cookie(token)}}), token)
        self.assertEqual(read_cookie({'cookies': [cookie(token), cookie(token)]}), '')
        self.assertEqual(read_cookie({'cookies': ['__Host-yeonma_session=short']}), '')
        for flag in ['HttpOnly', 'Secure', 'SameSite=Lax', 'Path=/', 'Max-Age=0']:
            self.assertIn(flag, cookie())
        self.assertNotIn('Domain=', cookie())

if __name__ == '__main__':
    unittest.main()
