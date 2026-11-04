"""Offline tests: all AWS calls and local credentials are fake."""
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "nh_secure_upload.py"
spec = importlib.util.spec_from_file_location("nh_secure_upload", SCRIPT)
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)


class ProviderError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.response = {"Error": {"Code": code, "Message": message}}


class SecureUploadTests(unittest.TestCase):
    def setUp(self):
        self.sts = mock.Mock()
        self.sts.get_caller_identity.return_value = {"Account": upload.ACCOUNT}
        self.ssm = mock.Mock()
        self.session = mock.Mock()
        self.session.client.side_effect = lambda name, **_: {"sts": self.sts, "ssm": self.ssm}[name]
        self.config = object()
        self.factory = mock.Mock(return_value=(self.session, self.config))
        self.loader = mock.Mock(return_value={"key": "fake-app-key", "secret": "fake-app-secret"})
        self.messages = []

    def run_upload(self, answer="UPLOAD"):
        return upload.run(self.factory, self.loader, ask=lambda _: answer, say=self.messages.append)

    def assert_no_secrets_in_messages(self):
        messages = " ".join(self.messages)
        self.assertNotIn("fake-app-key", messages)
        self.assertNotIn("fake-app-secret", messages)

    def test_fixed_target_standard_securestring_no_overwrite(self):
        self.assertEqual(self.run_upload(), 0)
        self.sts.get_caller_identity.assert_called_once_with()
        self.loader.assert_called_once_with()
        kwargs = self.ssm.put_parameter.call_args.kwargs
        self.assertEqual(kwargs["Name"], "/yeonma/private/nhplug")
        self.assertEqual(kwargs["Type"], "SecureString")
        self.assertEqual(kwargs["Tier"], "Standard")
        self.assertIs(kwargs["Overwrite"], False)
        self.assertNotIn("KeyId", kwargs)  # SSM default AWS managed key
        self.assertEqual(json.loads(kwargs["Value"]), self.loader.return_value)
        for name, endpoint in (("sts", upload.STS_ENDPOINT), ("ssm", upload.SSM_ENDPOINT)):
            self.session.client.assert_any_call(name, region_name="us-east-1", endpoint_url=endpoint,
                                                config=self.config, verify=True)
        self.assert_no_secrets_in_messages()

    def test_cancel_does_not_contact_aws_or_read_local_credentials(self):
        self.assertEqual(self.run_upload("NO"), 1)
        self.factory.assert_not_called()
        self.loader.assert_not_called()

    def test_wrong_account_aborts_before_reading_credentials(self):
        self.sts.get_caller_identity.return_value = {"Account": "000000000000"}
        self.assertEqual(self.run_upload(), 1)
        self.loader.assert_not_called()
        self.ssm.put_parameter.assert_not_called()
        self.assert_no_secrets_in_messages()

    def test_existing_parameter_is_never_overwritten(self):
        self.ssm.put_parameter.side_effect = ProviderError("ParameterAlreadyExists", "fake-app-secret")
        self.assertEqual(self.run_upload(), 1)
        self.assertIs(self.ssm.put_parameter.call_args.kwargs["Overwrite"], False)
        self.assertIn("이미 있어", " ".join(self.messages))
        self.assert_no_secrets_in_messages()

    def test_ambiguous_error_does_not_leak_or_retry(self):
        self.ssm.put_parameter.side_effect = TimeoutError("fake-app-key fake-app-secret")
        self.assertEqual(self.run_upload(), 1)
        self.ssm.put_parameter.assert_called_once()
        self.assertIn("저장 여부를 확인하지 못했습니다", " ".join(self.messages))
        self.assert_no_secrets_in_messages()

    def test_bad_credentials_are_never_uploaded(self):
        self.loader.return_value = {"key": "fake-app-key\n", "secret": "fake-app-secret"}
        self.assertEqual(self.run_upload(), 1)
        self.ssm.put_parameter.assert_not_called()
        self.assert_no_secrets_in_messages()

    def test_local_read_error_is_redacted_and_never_sent(self):
        self.loader.side_effect = RuntimeError("fake-app-secret")
        self.assertEqual(self.run_upload(), 1)
        self.ssm.put_parameter.assert_not_called()
        self.assertIn("전송하지 않았습니다", " ".join(self.messages))
        self.assert_no_secrets_in_messages()

    def test_default_profile_and_network_settings_are_fixed(self):
        boto = types.ModuleType("boto3")
        boto.Session = mock.Mock(return_value=self.session)
        botocore = types.ModuleType("botocore")
        config_module = types.ModuleType("botocore.config")
        config_module.Config = mock.Mock(return_value=self.config)
        with mock.patch.dict(sys.modules, {"boto3": boto, "botocore": botocore, "botocore.config": config_module}):
            session, config = upload.new_session()
        self.assertIs(session, self.session)
        self.assertIs(config, self.config)
        boto.Session.assert_called_once_with(profile_name="default", region_name="us-east-1")
        config_module.Config.assert_called_once_with(proxies={}, retries={"total_max_attempts": 1},
                                                     connect_timeout=5, read_timeout=15)

    def test_cli_arguments_are_rejected_without_echo_or_aws_calls(self):
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["nh_secure_upload.py", "fake-app-secret"]), contextlib.redirect_stdout(output):
            self.assertEqual(upload.main(), 2)
        self.assertNotIn("fake-app-secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
