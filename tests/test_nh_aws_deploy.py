import io
from pathlib import Path
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nh_aws_deploy as deploy


class MissingStack(Exception):
    response = {"Error": {"Code": "ValidationError", "Message": "Stack with id yeonma-nh-private does not exist"}}


class FakeSTS:
    identity = {"Account": deploy.ACCOUNT, "Arn": deploy.USER_ARN}
    def get_caller_identity(self):
        return self.identity


class FakeCF:
    def __init__(self):
        self.calls = []
        self.existing = None
        self.bootstrap = {"StackName": deploy.BOOTSTRAP_STACK, "StackStatus": "CREATE_COMPLETE", "Outputs": [
            {"OutputKey": "RuntimeRoleArn", "OutputValue": f"arn:aws:iam::{deploy.ACCOUNT}:role/yeonma-nh-runtime"},
            {"OutputKey": "CloudFormationRoleArn", "OutputValue": f"arn:aws:iam::{deploy.ACCOUNT}:role/yeonma-nh-cfn"},
            {"OutputKey": "ArtifactBucketName", "OutputValue": f"yeonma-nh-artifacts-{deploy.ACCOUNT}-{deploy.REGION}"},
            {"OutputKey": "PrivateApiId", "OutputValue": "abc123def4"}]}
    def describe_stacks(self, StackName):
        if StackName == deploy.BOOTSTRAP_STACK:
            return {"Stacks": [self.bootstrap]}
        if self.existing is None:
            raise MissingStack()
        return {"Stacks": [self.existing]}
    def validate_template(self, **kwargs):
        self.calls.append(("validate", kwargs))
        return {}
    def create_change_set(self, **kwargs):
        self.calls.append(("create", kwargs))
        name = kwargs["ChangeSetName"]
        return {"Id": f"arn:aws:cloudformation:{deploy.REGION}:{deploy.ACCOUNT}:changeSet/{name}/abc"}
    def list_stack_resources(self, **_kwargs):
        return {"StackResourceSummaries": [{"LogicalResourceId": name} for name in deploy.EXPECTED_LOGICAL_IDS]}


class FakeS3:
    def __init__(self):
        self.calls = []
        self.versioning = "Enabled"
        self.version = "version-123"
    def get_bucket_versioning(self, **kwargs):
        self.calls.append(("versioning", kwargs))
        return {"Status": self.versioning}
    def put_object(self, **kwargs):
        self.calls.append(("put", kwargs))
        return {"VersionId": self.version}


class DeployTest(unittest.TestCase):
    def setUp(self):
        self.sts, self.cf, self.s3 = FakeSTS(), FakeCF(), FakeS3()

    def prepare(self):
        with patch.object(deploy, "load_subject", return_value="123456789"):
            return deploy.prepare_change_set(self.sts, self.cf, self.s3, Path("unused"))

    def test_package_is_deterministic_and_contains_only_five_files(self):
        first, digest = deploy.package_code()
        second, digest2 = deploy.package_code()
        self.assertEqual(first, second)
        self.assertEqual(digest, digest2)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertFalse(deploy.package_guard_enabled(first))
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            self.assertEqual(archive.namelist(), list(deploy.CODE_FILES))
            self.assertIsNone(archive.testzip())

    def test_noecho_is_present_in_actual_template(self):
        self.assertIn("NoEcho: true", deploy.read_template())

    def test_create_only_uploads_versioned_package_and_does_not_print_subject(self):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            result = self.prepare()
        self.assertNotIn("123456789", output.getvalue())
        self.assertEqual(result["change_set_type"], "CREATE")
        self.assertFalse(result["nh_guard_enabled"])
        self.assertEqual([call[0] for call in self.cf.calls], ["validate", "create"])
        put = self.s3.calls[-1][1]
        self.assertEqual(put["Key"], f"deploy/{result['package_sha256']}.zip")
        self.assertEqual(put["ServerSideEncryption"], "AES256")
        with zipfile.ZipFile(io.BytesIO(put["Body"])) as archive:
            self.assertEqual(archive.namelist(), list(deploy.CODE_FILES))
        created = self.cf.calls[-1][1]
        self.assertEqual(created["ChangeSetType"], "CREATE")
        self.assertEqual(created["StackName"], deploy.STACK_NAME)
        self.assertEqual(created["RoleARN"], f"arn:aws:iam::{deploy.ACCOUNT}:role/yeonma-nh-cfn")
        params = {item["ParameterKey"]: item["ParameterValue"] for item in created["Parameters"]}
        self.assertEqual(params["OwnerGoogleSub"], "123456789")
        self.assertEqual(params["CodeObjectVersion"], "version-123")
        self.assertNotIn("123456789", repr(result))

    def test_wrong_identity_stops_before_write(self):
        self.sts.identity = {"Account": deploy.ACCOUNT, "Arn": f"arn:aws:iam::{deploy.ACCOUNT}:user/other"}
        with self.assertRaises(deploy.DeploymentError):
            self.prepare()
        self.assertEqual(self.cf.calls, [])
        self.assertEqual(self.s3.calls, [])

    def test_wrong_bootstrap_stops_before_write(self):
        self.cf.bootstrap["Outputs"][0]["OutputValue"] = f"arn:aws:iam::{deploy.ACCOUNT}:role/other"
        with self.assertRaises(deploy.DeploymentError):
            self.prepare()
        self.assertEqual(self.cf.calls, [])
        self.assertEqual(self.s3.calls, [])

    def test_unversioned_bucket_or_object_stops_change_set(self):
        self.s3.versioning = "Suspended"
        with self.assertRaises(deploy.DeploymentError):
            self.prepare()
        self.assertNotIn("put", [call[0] for call in self.s3.calls])
        self.assertEqual(self.cf.calls, [])
        self.s3.versioning, self.s3.version = "Enabled", "null"
        with self.assertRaises(deploy.DeploymentError):
            self.prepare()
        self.assertEqual([call[0] for call in self.cf.calls], ["validate"])

    def test_existing_stack_must_have_correct_ownership_and_resources(self):
        self.cf.existing = {"StackName": deploy.STACK_NAME, "StackStatus": "UPDATE_COMPLETE",
                            "RoleARN": f"arn:aws:iam::{deploy.ACCOUNT}:role/yeonma-nh-cfn",
                            "Tags": [{"Key": "Project", "Value": "yeonma-nh-private"}]}
        self.assertEqual(self.prepare()["change_set_type"], "UPDATE")
        self.cf.calls.clear()
        self.s3.calls.clear()
        self.cf.existing["Tags"] = []
        with self.assertRaises(deploy.DeploymentError):
            self.prepare()
        self.assertEqual(self.cf.calls, [])
        self.assertEqual(self.s3.calls, [])

    def test_subject_error_is_sanitized(self):
        path = SimpleNamespace(is_symlink=lambda: False, is_file=lambda: True,
                               stat=lambda: SimpleNamespace(st_size=10), read_bytes=lambda: b"encrypted")
        def fail(*_args, **_kwargs):
            raise RuntimeError("sensitive token and credential should not escape")
        with self.assertRaises(deploy.DeploymentError) as context:
            deploy.load_subject(path, decrypt=fail)
        self.assertNotIn("sensitive", str(context.exception))
        self.assertIsNone(context.exception.__cause__)


if __name__ == "__main__":
    unittest.main()
