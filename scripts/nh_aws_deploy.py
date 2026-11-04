"""연마 개인 NH API 변경 세트 준비. 이 스크립트는 변경 세트를 실행하지 않는다.

AWS 자격증명, Google ID 토큰, NH 키 및 Google subject를 화면이나 명령행에
전달하지 않는다. 이전에 검증한 Google subject는 Windows DPAPI에서 메모리로만
읽고, CloudFormation의 NoEcho 매개변수로 전달한다.
"""
from __future__ import annotations

import hashlib
import ast
import io
import logging
import re
import secrets
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from nh_private_server import dpapi_transform

ACCOUNT = "514670561185"
REGION = "us-east-1"
USER_ARN = f"arn:aws:iam::{ACCOUNT}:user/codex-amplify-manager"
BOOTSTRAP_STACK = "yeonma-nh-bootstrap"
STACK_NAME = "yeonma-nh-private"
CLIENT_ID = "343043233969-95mv3utlrbafcj1673dpl33ont9mh2j9.apps.googleusercontent.com"
ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = ROOT / "server" / "nh_private"
TEMPLATE = ROOT / "server" / "nh_infra" / "template.yaml"
CODE_FILES = ("handler.py", "runtime_service.py", "flow_service.py", "token_store.py", "nh_transport.py")
EXPECTED_LOGICAL_IDS = {"TokenTable", "ReaderLogGroup", "Reader", "GoogleAuthorizer", "ReaderIntegration",
                        "ReadFlow", "GatewayPermission", "ReadSession", "SessionGatewayPermission", "LiveStage"}


class DeploymentError(RuntimeError):
    """Public-safe deployment failure. Never embed subject or provider data."""


def _output_map(stack):
    values = {}
    for output in stack.get("Outputs", []):
        key, value = output.get("OutputKey"), output.get("OutputValue")
        if not isinstance(key, str) or not isinstance(value, str) or key in values:
            raise DeploymentError("부트스트랩 출력 형식이 올바르지 않습니다.")
        values[key] = value
    return values


def checked_bootstrap(sts, cloudformation):
    identity = sts.get_caller_identity()
    if identity.get("Account") != ACCOUNT or identity.get("Arn") != USER_ARN:
        raise DeploymentError("AWS 계정 또는 배포 사용자가 일치하지 않습니다.")
    result = cloudformation.describe_stacks(StackName=BOOTSTRAP_STACK)
    stacks = result.get("Stacks", [])
    if (len(stacks) != 1 or stacks[0].get("StackName") != BOOTSTRAP_STACK
            or stacks[0].get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}):
        raise DeploymentError("승인된 부트스트랩 스택을 확인하지 못했습니다.")
    values = _output_map(stacks[0])
    expected = {"RuntimeRoleArn": f"arn:aws:iam::{ACCOUNT}:role/yeonma-nh-runtime",
                "CloudFormationRoleArn": f"arn:aws:iam::{ACCOUNT}:role/yeonma-nh-cfn",
                "ArtifactBucketName": f"yeonma-nh-artifacts-{ACCOUNT}-{REGION}"}
    if any(values.get(key) != value for key, value in expected.items()):
        raise DeploymentError("부트스트랩 자원 식별자가 예상과 다릅니다.")
    if not re.fullmatch(r"[a-z0-9]{10}", values.get("PrivateApiId", "")):
        raise DeploymentError("부트스트랩 API 식별자가 올바르지 않습니다.")
    return values


def package_code(code_dir=CODE_DIR):
    """검토 범위 5개 파일만 결정적으로 압축한다. 자격증명 파일은 포함하지 않는다."""
    resolved = code_dir.resolve(strict=True)
    if not resolved.is_dir() or code_dir.is_symlink():
        raise DeploymentError("코드 디렉터리를 확인하지 못했습니다.")
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in CODE_FILES:
            path = code_dir / name
            if path.is_symlink() or not path.is_file() or path.resolve(strict=True).parent != resolved:
                raise DeploymentError("Lambda 코드 파일을 확인하지 못했습니다.")
            raw = path.read_bytes()
            if not raw or len(raw) > 1_000_000:
                raise DeploymentError("Lambda 코드 크기가 예상과 다릅니다.")
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    payload = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.namelist() != list(CODE_FILES) or archive.testzip() is not None:
            raise DeploymentError("Lambda 패키지를 검증하지 못했습니다.")
    return payload, hashlib.sha256(payload).hexdigest()


def package_guard_enabled(payload):
    """패키지에 실제 포함된 핸들러의 정적 안전 차단 선언을 읽는다."""
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            module = ast.parse(archive.read("handler.py"))
        flags = [node.value.value for node in module.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "TOKEN_CACHE_READY" for target in node.targets)
                 and isinstance(node.value, ast.Constant) and isinstance(node.value.value, bool)]
        if len(flags) != 1:
            raise ValueError("unexpected guard declaration")
        return not flags[0]
    except Exception:
        raise DeploymentError("패키지의 NH 안전 차단 선언을 확인하지 못했습니다.") from None


def read_template(path=TEMPLATE):
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True).parent != (ROOT / "server" / "nh_infra").resolve():
        raise DeploymentError("배포 템플릿을 확인하지 못했습니다.")
    template = path.read_text(encoding="utf-8")
    if len(template.encode("utf-8")) > 51200:
        raise DeploymentError("배포 템플릿이 너무 큽니다.")
    block = re.search(r"(?m)^  OwnerGoogleSub:\s*\n((?:    [^\n]*\n)+)", template)
    if not block or not re.search(r"(?m)^    NoEcho:\s*true\s*$", block.group(1)):
        raise DeploymentError("계정 식별자 보호 설정이 없습니다.")
    return template


def load_subject(path, decrypt=dpapi_transform):
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 8192:
            raise ValueError("invalid subject file")
        subject = decrypt(path.read_bytes(), decrypt=True).decode("ascii")
        if not re.fullmatch(r"[0-9]{1,64}", subject):
            raise ValueError("invalid subject")
        return subject
    except Exception:
        raise DeploymentError("검증된 Google 계정 식별자를 읽지 못했습니다.") from None


def change_set_type(cloudformation, role_arn):
    try:
        response = cloudformation.describe_stacks(StackName=STACK_NAME)
    except Exception as exc:
        error = getattr(exc, "response", {}).get("Error", {})
        if error.get("Code") == "ValidationError" and "does not exist" in str(error.get("Message", "")).lower():
            return "CREATE"
        raise DeploymentError("대상 스택 상태를 확인하지 못했습니다.") from None
    stacks = response.get("Stacks", [])
    if len(stacks) != 1:
        raise DeploymentError("대상 스택이 예상과 다릅니다.")
    stack = stacks[0]
    tags = {item.get("Key"): item.get("Value") for item in stack.get("Tags", [])}
    if (stack.get("StackName") != STACK_NAME or stack.get("RoleARN") != role_arn
            or stack.get("StackStatus") not in {"CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"}
            or tags.get("Project") != "yeonma-nh-private"):
        raise DeploymentError("기존 스택의 소유자 또는 상태를 확인하지 못했습니다.")
    resource_response = cloudformation.list_stack_resources(StackName=STACK_NAME)
    if resource_response.get("NextToken"):
        raise DeploymentError("기존 스택의 자원 목록이 예상보다 많아 변경하지 않습니다.")
    resources = resource_response.get("StackResourceSummaries", [])
    if {item.get("LogicalResourceId") for item in resources} != EXPECTED_LOGICAL_IDS:
        raise DeploymentError("기존 스택 자원이 예상과 달라 변경하지 않습니다.")
    return "UPDATE"


def prepare_change_set(sts, cloudformation, s3, subject_path, *, code_dir=CODE_DIR, template_path=TEMPLATE):
    """패키지 업로드와 변경 세트 생성까지만 수행하고 실행은 하지 않는다."""
    resources = checked_bootstrap(sts, cloudformation)
    template = read_template(template_path)
    subject = load_subject(subject_path)
    change_type = change_set_type(cloudformation, resources["CloudFormationRoleArn"])
    package, digest = package_code(code_dir)
    guarded = package_guard_enabled(package)
    bucket = resources["ArtifactBucketName"]
    if s3.get_bucket_versioning(Bucket=bucket).get("Status") != "Enabled":
        raise DeploymentError("배포 버킷의 버전 관리가 활성화되지 않았습니다.")
    cloudformation.validate_template(TemplateBody=template)
    key = f"deploy/{digest}.zip"
    result = s3.put_object(Bucket=bucket, Key=key, Body=package, ContentType="application/zip",
                           ServerSideEncryption="AES256", Metadata={"sha256": digest})
    version = result.get("VersionId")
    if not isinstance(version, str) or not version or version == "null":
        raise DeploymentError("배포 패키지 버전을 확인하지 못했습니다.")
    parameters = {"GoogleClientId": CLIENT_ID, "OwnerGoogleSub": subject, "ApiId": resources["PrivateApiId"],
                  "RuntimeRoleArn": resources["RuntimeRoleArn"], "CodeBucket": bucket,
                  "CodeKey": key, "CodeObjectVersion": version}
    name = "review-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "-" + secrets.token_hex(4)
    response = cloudformation.create_change_set(
        StackName=STACK_NAME, ChangeSetName=name, ChangeSetType=change_type,
        TemplateBody=template, RoleARN=resources["CloudFormationRoleArn"],
        Parameters=[{"ParameterKey": key, "ParameterValue": value} for key, value in parameters.items()],
        Tags=[{"Key": "Project", "Value": "yeonma-nh-private"}],
        ClientToken=secrets.token_hex(16))
    change_id = response.get("Id")
    if not isinstance(change_id, str) or not change_id.startswith(f"arn:aws:cloudformation:{REGION}:{ACCOUNT}:changeSet/{name}/"):
        raise DeploymentError("생성된 변경 세트를 확인하지 못했습니다.")
    return {"change_set_id": change_id, "package_sha256": digest, "change_set_type": change_type,
            "nh_guard_enabled": guarded}


def main():
    try:
        # Suppress SDK debug logging that could disclose request bodies.
        logging.disable(logging.CRITICAL)
        import boto3
        from botocore.config import Config
        from nh_google_identity_check import SUB_FILE
        config = Config(region_name=REGION, proxies={}, retries={"max_attempts": 2, "mode": "standard"})
        session = boto3.session.Session(region_name=REGION)
        sts = session.client("sts", endpoint_url=f"https://sts.{REGION}.amazonaws.com", config=config, verify=True)
        cf = session.client("cloudformation", endpoint_url=f"https://cloudformation.{REGION}.amazonaws.com", config=config, verify=True)
        s3 = session.client("s3", endpoint_url=f"https://s3.{REGION}.amazonaws.com", config=config, verify=True)
        result = prepare_change_set(sts, cf, s3, SUB_FILE)
        print("변경 세트를 생성했습니다. 아직 실행하지 않았습니다.")
        print("변경 세트 ID:", result["change_set_id"])
        print("패키지 SHA-256:", result["package_sha256"])
        if result["nh_guard_enabled"]:
            print("패키지의 NH 호출은 안전 차단 중이며 실제 시세는 아직 제공되지 않습니다.")
        else:
            print("패키지의 NH 안전 차단 선언이 꺼져 있습니다. 실제 사용 전 별도 검증이 필요합니다.")
        return 0
    except DeploymentError as exc:
        print(str(exc), file=sys.stderr)
    except Exception:
        # Provider exceptions can contain private values. Never print details.
        print("배포 준비에 실패했습니다. 계정·권한과 사전 설정을 확인하세요.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
