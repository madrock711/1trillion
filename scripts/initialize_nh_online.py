"""One-time, explicitly approved migration to the AWS-only NH issuer.

No NH request is made here. Never resets an existing token record or prints
credentials, record identifiers or tokens. Token issuance happens in Lambda.
"""
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server' / 'nh_private'))
from runtime_service import _credential_id
from nh_private_server import dpapi_transform, SECRET_FILE, ONLINE_FILE


def initialize(ddb, key, now):
    ddb.update_item(TableName='yeonma-nh-token', Key={'id': {'S': key}},
        UpdateExpression='SET #s = :ready, #v = :zero, not_before = :now, migration_approved_at = :now',
        ConditionExpression='attribute_not_exists(id)',
        ExpressionAttributeNames={'#s': 'state', '#v': 'version'},
        ExpressionAttributeValues={':ready': {'S': 'READY'}, ':zero': {'N': '0'}, ':now': {'N': str(now)}})


def main():
    if sys.argv[1:] != ['--initialize-approved-once']:
        print('Explicit one-time migration approval required.')
        return 1
    check = subprocess.run(['powershell', '-NoProfile', '-Command',
        "$p=Get-CimInstance Win32_Process -Filter \"Name = 'python.exe' OR Name = 'pythonw.exe'\" | Where-Object { $_.CommandLine -match 'nh_private_server|nhplug-preview' -and $_.CommandLine -notmatch 'initialize_nh_online' }; if ($p) { exit 1 }"],
        capture_output=True, timeout=20)
    if check.returncode:
        raise RuntimeError('A local NH issuer may still be running')
    import boto3
    from botocore.config import Config
    logging.disable(logging.CRITICAL)
    cfg = Config(region_name='us-east-1', proxies={}, retries={'max_attempts': 0})
    aws = boto3.Session(region_name='us-east-1')
    who = aws.client('sts', config=cfg).get_caller_identity()
    if who['Account'] != '514670561185' or not who['Arn'].endswith(':user/codex-amplify-manager'):
        raise RuntimeError('Unexpected AWS identity')
    # Use the same DPAPI source that was securely uploaded; no SSM read by CLI.
    data = json.loads(dpapi_transform(SECRET_FILE.read_bytes(), decrypt=True))
    key = 'nh-' + _credential_id(data['key'], data['secret'])
    del data
    ddb = aws.client('dynamodb', config=cfg)
    if ddb.get_item(TableName='yeonma-nh-token', Key={'id': {'S': key}},
                    ProjectionExpression='id', ConsistentRead=True).get('Item'):
        print('Token state already exists; it was not reset and no token was issued.')
        return 1
    ONLINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ONLINE_FILE.exists():
        with ONLINE_FILE.open('x', encoding='utf-8') as stream:
            json.dump({'mode': 'aws-only', 'approvedAt': int(time.time())}, stream)
    else:
        if json.loads(ONLINE_FILE.read_text(encoding='utf-8')).get('mode') != 'aws-only':
            raise RuntimeError('Unexpected migration marker')
    initialize(ddb, key, int(time.time()))
    print('AWS token state initialized once. Local preview issuer disabled. No NH request made.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('Migration initialization failed; state was not forcibly reset. No private values printed.')
        raise SystemExit(1)
