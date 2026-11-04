import json
import unittest
from unittest import mock

from runtime_service import RuntimeConfigurationError, build_service


CONFIG = {
    "SSM_PARAMETER_NAME": "/yeonma/private/nhplug",
    "TOKEN_TABLE_NAME": "yeonma-nh-token",
}


class RuntimeServiceTest(unittest.TestCase):
    def setUp(self):
        self.ssm = mock.Mock()
        self.ssm.get_parameter.return_value = {"Parameter": {"Value": json.dumps({"key": "test-app-key", "secret": "test-secret"})}}
        self.ddb = mock.Mock()
        self.transport = mock.Mock()
        self.factory = mock.Mock(return_value=self.transport)
        self.clients = {"ssm": self.ssm, "dynamodb": self.ddb}

    def build(self):
        return build_service(CONFIG, self.clients, lambda payload: payload, self.factory)

    def test_construction_does_not_issue_or_query_nh(self):
        service = self.build()
        self.ssm.get_parameter.assert_called_once_with(Name=CONFIG["SSM_PARAMETER_NAME"], WithDecryption=True)
        self.factory.assert_called_once_with("test-app-key", "test-secret")
        self.transport.issue_once.assert_not_called()
        self.transport.read_flow.assert_not_called()
        self.ddb.get_item.assert_not_called()
        self.assertEqual(service.token_manager.store.table, CONFIG["TOKEN_TABLE_NAME"])
        self.assertNotIn("test-app-key", service.token_manager.store.key)
        self.assertNotIn("test-secret", service.token_manager.store.key)

    def test_changed_credentials_select_new_uninitialized_record(self):
        first = self.build().token_manager.store.key
        self.ssm.get_parameter.return_value = {"Parameter": {"Value": json.dumps({"key": "test-app-key", "secret": "new-secret"})}}
        second = self.build().token_manager.store.key
        self.assertNotEqual(first, second)

    def test_missing_token_record_fails_closed_without_issuing(self):
        self.ddb.get_item.return_value = {}
        with self.assertRaises(Exception):
            self.build().get()
        self.transport.issue_once.assert_not_called()
        self.transport.read_flow.assert_not_called()

    def test_invalid_config_does_not_read_ssm(self):
        for key, value in (("SSM_PARAMETER_NAME", "/unrelated/key"), ("TOKEN_TABLE_NAME", "x")):
            with self.subTest(key=key):
                invalid = dict(CONFIG, **{key: value})
                with self.assertRaises(RuntimeConfigurationError):
                    build_service(invalid, self.clients, lambda x: x, self.factory)
        self.ssm.get_parameter.assert_not_called()

    def test_provider_errors_and_bad_values_do_not_leak(self):
        self.ssm.get_parameter.side_effect = RuntimeError("private-example-sensitive-value")
        with self.assertRaises(RuntimeConfigurationError) as caught:
            self.build()
        self.assertNotIn("private-example-sensitive-value", str(caught.exception))
        self.ssm.get_parameter.side_effect = None
        self.ssm.get_parameter.return_value = {"Parameter": {"Value": json.dumps({"key": "bad\nkey", "secret": "test-secret"})}}
        with self.assertRaises(RuntimeConfigurationError):
            self.build()


if __name__ == "__main__":
    unittest.main()
