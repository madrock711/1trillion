"""Static contract checks only; they do not validate or deploy AWS resources."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "server" / "nh_infra" / "iam-bootstrap.json"
OPERATING = ROOT / "server" / "nh_infra" / "template.yaml"
GUIDE = ROOT / "server" / "nh_infra" / "AWS_IAM_설정_안내.md"


class PrivateNhInfrastructureContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = json.loads(BOOTSTRAP.read_text(encoding="utf-8"))
        cls.resources = cls.template["Resources"]
        cls.operating = OPERATING.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")

    @staticmethod
    def statements(resource):
        props = resource["Properties"]
        if resource["Type"] == "AWS::IAM::ManagedPolicy":
            return props["PolicyDocument"]["Statement"]
        return [statement for policy in props["Policies"] for statement in policy["PolicyDocument"]["Statement"]]

    def test_account_region_are_documented_not_hard_enforced(self):
        # The bootstrap is parameterized by AWS pseudo-parameters; account/region
        # checking is presently a manual step, not an enforced template rule.
        self.assertIn("514670561185", self.guide)
        self.assertIn("us-east-1", self.guide)
        encoded = json.dumps(self.template)
        self.assertIn("${AWS::AccountId}", encoded)
        self.assertIn("${AWS::Region}", encoded)
        self.assertNotIn("Rules", self.template)

    def test_dedicated_api_and_reused_api_id(self):
        api = self.resources["PrivateApi"]
        self.assertEqual(api["Type"], "AWS::ApiGatewayV2::Api")
        self.assertEqual(api["Properties"]["Name"], "yeonma-nh-private")
        self.assertEqual(api["Properties"]["ProtocolType"], "HTTP")
        self.assertEqual(api["Properties"]["CorsConfiguration"]["AllowOrigins"], ["https://www.hpmplab.com"])
        self.assertEqual(self.template["Outputs"]["PrivateApiId"]["Value"], {"Ref": "PrivateApi"})
        self.assertNotRegex(self.operating, r"(?m)^\s*Type:\s*AWS::ApiGatewayV2::Api\s*$")
        self.assertGreaterEqual(len(re.findall(r"(?m)^\s*ApiId:\s*!Ref ApiId\s*$", self.operating)), 4)
        api_policy = [s for s in self.statements(self.resources["CloudFormationRole"])
                      if "apigateway:POST" in s.get("Action", [])
                      and "/apis/${PrivateApi}" in json.dumps(s.get("Resource"))]
        self.assertEqual(len(api_policy), 1)
        resources = json.dumps(api_policy[0]["Resource"])
        self.assertIn("/apis/${PrivateApi}", resources)
        self.assertNotIn('::/apis/*"', resources)

    def test_stage_tag_permissions_are_confined_to_private_api(self):
        statements = {s.get("Sid"): s for s in self.statements(self.resources["CloudFormationRole"])}
        expected = {
            "PrivateApiStageTagOnCreate": "apigateway:TagResource",
            "PrivateApiStageUntag": "apigateway:UntagResource",
        }
        for sid, action in expected.items():
            statement = statements[sid]
            self.assertEqual(statement["Action"], action)
            self.assertIn("/apis/${PrivateApi}/stages", json.dumps(statement["Resource"]))
            self.assertEqual(statement["Condition"]["StringEquals"]["aws:RequestedRegion"], {"Ref": "AWS::Region"})
        endpoint = statements["PrivateApiStageTagsEndpoint"]
        self.assertEqual(set(endpoint["Action"]), {"apigateway:GET", "apigateway:POST", "apigateway:PUT",
                                                   "apigateway:PATCH", "apigateway:DELETE"})
        resources = endpoint["Resource"]
        self.assertEqual(len(resources), 2)
        for resource in resources:
            self.assertIn("/tags/arn%3A${AWS::Partition}%3Aapigateway%3A${AWS::Region}%3A%3A%2Fapis%2F${PrivateApi}%2Fstages",
                          resource["Fn::Sub"])
        self.assertEqual(endpoint["Condition"]["StringEquals"]["aws:RequestedRegion"], {"Ref": "AWS::Region"})

    def test_roles_user_and_passrole_targets(self):
        runtime = self.resources["RuntimeRole"]
        deploy = self.resources["CloudFormationRole"]
        self.assertEqual(runtime["Properties"]["RoleName"], "yeonma-nh-runtime")
        self.assertEqual(deploy["Properties"]["RoleName"], "yeonma-nh-cfn")
        self.assertEqual(runtime["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]["Principal"]["Service"], "lambda.amazonaws.com")
        self.assertEqual(deploy["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]["Principal"]["Service"], "cloudformation.amazonaws.com")
        policy = self.resources["CliDeploymentPolicy"]
        self.assertEqual(policy["Type"], "AWS::IAM::ManagedPolicy")
        self.assertEqual(policy["Properties"]["Users"], ["codex-amplify-manager"])
        for resource, expected, service in [(deploy, "RuntimeRole", "lambda.amazonaws.com"),
                                             (policy, "CloudFormationRole", "cloudformation.amazonaws.com")]:
            passes = [s for s in self.statements(resource) if s.get("Action") == "iam:PassRole"]
            self.assertEqual(len(passes), 1)
            self.assertEqual(passes[0]["Resource"], {"Fn::GetAtt": [expected, "Arn"]})
            self.assertEqual(passes[0]["Condition"]["StringEquals"]["iam:PassedToService"], service)
        self.assertRegex(self.operating, r"(?m)^\s*Role:\s*!Ref RuntimeRoleArn\s*$")
        self.assertNotRegex(self.operating, r"(?m)^\s*Type:\s*AWS::IAM::Role\s*$")

    def test_change_set_bound_to_named_stack(self):
        statements = self.statements(self.resources["CliDeploymentPolicy"])
        create = [s for s in statements if s.get("Action") == "cloudformation:CreateChangeSet"]
        self.assertEqual(len(create), 1)
        self.assertIn("stack/yeonma-nh-private/*", json.dumps(create[0]["Resource"]))
        self.assertEqual(create[0]["Condition"]["StringEquals"]["cloudformation:RoleARN"],
                         {"Fn::GetAtt": ["CloudFormationRole", "Arn"]})
        names = {action for s in statements for action in
                 ([s["Action"]] if isinstance(s["Action"], str) else s["Action"])}
        self.assertTrue({"cloudformation:DescribeChangeSet", "cloudformation:ExecuteChangeSet",
                         "cloudformation:DeleteChangeSet"}.issubset(names))

    def test_resource_wildcards_are_explicitly_conditioned(self):
        allowed = {"kms:Decrypt", "kms:Encrypt", "logs:DescribeLogGroups", "cloudformation:ValidateTemplate"}
        seen = set()
        for name in ("RuntimeRole", "CloudFormationRole", "CliDeploymentPolicy"):
            for statement in self.statements(self.resources[name]):
                actions = [statement["Action"]] if isinstance(statement["Action"], str) else statement["Action"]
                self.assertTrue(all(not action.endswith("*") for action in actions), name)
                if statement.get("Resource") != "*":
                    continue
                self.assertIsInstance(statement["Action"], str)
                action = statement["Action"]
                self.assertIn(action, allowed)
                conditions = statement.get("Condition", {}).get("StringEquals", {})
                self.assertTrue(conditions, f"unconditioned wildcard: {action}")
                if action.startswith("kms:"):
                    self.assertIn("kms:ViaService", conditions)
                    self.assertIn("kms:EncryptionContext:PARAMETER_ARN", conditions)
                else:
                    self.assertEqual(conditions.get("aws:RequestedRegion"), {"Ref": "AWS::Region"})
                seen.add(action)
        self.assertEqual(seen, allowed)

    def test_no_customer_kms_key_or_separate_token_kms(self):
        self.assertFalse(any(r["Type"] == "AWS::KMS::Key" for r in self.resources.values()))
        self.assertNotIn("TOKEN_KMS_KEY_ARN", self.operating)
        self.assertNotIn("CredentialKmsKeyArn", self.operating)
        self.assertIn("테이블의 항목 읽기 권한", self.guide)

    def test_artifact_bucket_private_versioned_and_retained(self):
        bucket = self.resources["ArtifactBucket"]
        props = bucket["Properties"]
        self.assertEqual(bucket["Type"], "AWS::S3::Bucket")
        self.assertEqual(bucket["DeletionPolicy"], "Retain")
        self.assertEqual(props["VersioningConfiguration"]["Status"], "Enabled")
        self.assertEqual(props["PublicAccessBlockConfiguration"], {
            "BlockPublicAcls": True, "BlockPublicPolicy": True,
            "IgnorePublicAcls": True, "RestrictPublicBuckets": True,
        })
        self.assertEqual(props["BucketEncryption"]["ServerSideEncryptionConfiguration"][0]
                         ["ServerSideEncryptionByDefault"]["SSEAlgorithm"], "AES256")
        self.assertIn("yeonma-nh-artifacts-${AWS::AccountId}-${AWS::Region}", json.dumps(props["BucketName"]))
        self.assertIn("/deploy/*", json.dumps(self.resources["CliDeploymentPolicy"]))
        self.assertRegex(self.operating, r"(?m)^\s*S3ObjectVersion:\s*!Ref CodeObjectVersion\s*$")

    def test_shared_token_table_and_ssm_contract(self):
        self.assertRegex(self.operating, r"(?m)^\s*TableName:\s*yeonma-nh-token\s*$")
        self.assertRegex(self.operating, r"(?m)^\s*TOKEN_TABLE_NAME:\s*!Ref TokenTable\s*$")
        self.assertRegex(self.operating, r"(?m)^\s*SSM_PARAMETER_NAME:\s*/yeonma/private/nhplug\s*$")
        runtime = json.dumps(self.resources["RuntimeRole"])
        self.assertIn("table/yeonma-nh-token", runtime)
        self.assertIn("parameter/yeonma/private/nhplug", runtime)
        self.assertRegex(self.operating, r"(?m)^\s*ReservedConcurrentExecutions:\s*1\s*$")
        self.assertRegex(self.operating, r"(?m)^\s*AuthorizationType:\s*JWT\s*$")


if __name__ == "__main__":
    unittest.main()
