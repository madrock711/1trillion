"""One-time, non-overwriting upload of local DPAPI NH credentials to SSM.

No credential is accepted in arguments, environment variables or standard
input. The account, AWS region, service endpoints and parameter name are fixed.
Run only in the Windows account that created the local DPAPI file.
"""
from __future__ import annotations

import json
import logging
import sys

ACCOUNT = "514670561185"
REGION = "us-east-1"
PARAMETER = "/yeonma/private/nhplug"
STS_ENDPOINT = "https://sts.us-east-1.amazonaws.com"
SSM_ENDPOINT = "https://ssm.us-east-1.amazonaws.com"


def load_local_credentials():
    """Read and DPAPI-decrypt in memory; never print the result."""
    from nh_private_server import SECRET_FILE, dpapi_transform
    if not SECRET_FILE.is_file():
        raise RuntimeError("local credentials missing")
    return json.loads(dpapi_transform(SECRET_FILE.read_bytes(), decrypt=True))


def new_session():
    """Use only the named default AWS profile and fixed vendor endpoints."""
    import boto3
    from botocore.config import Config
    session = boto3.Session(profile_name="default", region_name=REGION)
    # Do not forward credentials through proxy settings. Do not retry an
    # ambiguous create: it may have succeeded even if the response was lost.
    config = Config(proxies={}, retries={"total_max_attempts": 1}, connect_timeout=5, read_timeout=15)
    return session, config


def run(session_factory, credential_loader, ask=input, say=print):
    """Return a process exit code; injected dependencies permit offline tests."""
    say("대상: AWS 계정 514670561185, us-east-1, /yeonma/private/nhplug")
    say("이 PC에 암호화된 NH 키를 AWS 표준 SecureString에 저장합니다. 기존 값은 덮어쓰지 않습니다.")
    write_attempted = False
    try:
        if ask("계속하려면 UPLOAD를 입력하세요: ").strip() != "UPLOAD":
            say("취소했습니다. AWS에 저장하지 않았습니다.")
            return 1
    except (EOFError, KeyboardInterrupt):
        say("취소했습니다. AWS에 저장하지 않았습니다.")
        return 1

    try:
        session, config = session_factory()
        sts = session.client("sts", region_name=REGION, endpoint_url=STS_ENDPOINT, config=config, verify=True)
        if sts.get_caller_identity().get("Account") != ACCOUNT:
            say("AWS 계정이 일치하지 않아 중단했습니다. 인증정보는 읽거나 전송하지 않았습니다.")
            return 1
        ssm = session.client("ssm", region_name=REGION, endpoint_url=SSM_ENDPOINT, config=config, verify=True)
        credentials = credential_loader()
        if not isinstance(credentials, dict):
            raise ValueError("invalid credential format")
        key, secret = credentials.get("key"), credentials.get("secret")
        if not all(isinstance(value, str) and 1 <= len(value) <= 4096
                   and all(33 <= ord(char) <= 126 for char in value) for value in (key, secret)):
            raise ValueError("invalid credential format")
        value = json.dumps({"key": key, "secret": secret}, separators=(",", ":"))
        write_attempted = True
        ssm.put_parameter(Name=PARAMETER, Value=value, Type="SecureString", Tier="Standard", Overwrite=False)
        say("AWS에 저장했습니다. 기존 값은 변경하지 않았습니다.")
        return 0
    except Exception as exc:
        # Provider error text may contain secrets or private headers. Do not log
        # or display it. A lost response can mean the create already succeeded.
        response = getattr(exc, "response", None)
        detail = response.get("Error") if isinstance(response, dict) else None
        code = detail.get("Code") if isinstance(detail, dict) else None
        if code == "ParameterAlreadyExists":
            say("같은 이름의 파라미터가 이미 있어 변경하지 않았습니다.")
        elif not write_attempted:
            say("AWS에 전송하지 않았습니다. 계정·권한과 로컬 인증정보 설정을 확인하세요.")
        else:
            say("저장 여부를 확인하지 못했습니다. 재시도하기 전에 AWS에서 대상 파라미터 존재 여부를 확인하세요.")
        return 1


def main():
    # Do not allow accidentally putting secrets in a process command line.
    if len(sys.argv) != 1:
        print("이 스크립트에는 인자를 전달하지 마세요.")
        return 2
    logging.disable(logging.CRITICAL)
    return run(new_session, load_local_credentials)


if __name__ == "__main__":
    raise SystemExit(main())
