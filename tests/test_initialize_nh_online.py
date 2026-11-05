import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from initialize_nh_online import initialize


class MigrationTests(unittest.TestCase):
    def test_initialization_is_conditional_and_contains_no_token(self):
        db = Mock()
        initialize(db, 'test-identity', 1000)
        args = db.update_item.call_args.kwargs
        self.assertEqual(args['TableName'], 'yeonma-nh-token')
        self.assertEqual(args['ConditionExpression'], 'attribute_not_exists(id)')
        self.assertEqual(args['ExpressionAttributeValues'][':ready'], {'S': 'READY'})
        self.assertNotIn('token', args['UpdateExpression'])

    def test_existing_state_or_ambiguous_write_is_never_reset_or_retried(self):
        db = Mock()
        db.update_item.side_effect = RuntimeError('conditional or ambiguous failure')
        with self.assertRaises(RuntimeError):
            initialize(db, 'test-identity', 1000)
        db.update_item.assert_called_once()


if __name__ == '__main__':
    unittest.main()
