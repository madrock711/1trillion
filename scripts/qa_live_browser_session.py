"""Explicit live session QA, not a Google OAuth or NH-token test.

Creates only a random owner browser-session record and revokes it in finally.
The opaque value travels to the isolated headless browser via stdin only.
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
from session_store import Sessions


def main():
    if sys.argv[1:] != ['--run']:
        print('Explicit --run required for live synthetic session QA.')
        return 1
    import boto3
    from botocore.config import Config
    logging.disable(logging.CRITICAL)
    cfg = Config(region_name='us-east-1', proxies={})
    aws = boto3.Session(region_name='us-east-1')
    identity = aws.client('sts', config=cfg).get_caller_identity()
    if identity['Account'] != '514670561185' or not identity['Arn'].endswith(':user/codex-amplify-manager'):
        raise RuntimeError('Wrong deployment identity')
    settings = aws.client('lambda', config=cfg).get_function_configuration(FunctionName='yeonma-nh-private')['Environment']['Variables']
    if settings['TOKEN_TABLE_NAME'] != 'yeonma-nh-token' or settings['OWNER_EMAIL'] != 'madrock711@gmail.com':
        raise RuntimeError('Unexpected session owner or table')
    # Shorter test lifetime; actual production policy remains seven days.
    store = Sessions(aws.client('dynamodb', config=cfg), settings['TOKEN_TABLE_NAME'],
                     settings['OWNER_GOOGLE_SUB'] + ':' + settings['OWNER_EMAIL'].lower(),
                     clock=lambda: time.time() - 7*24*60*60 + 600)
    token, _ = store.create()
    try:
        result = subprocess.run(['node', str(ROOT / 'tests' / 'test_live_browser_session.cjs')],
                                input=json.dumps({'token': token}), text=True, cwd=ROOT, timeout=100)
        return result.returncode
    finally:
        store.revoke(token)
        print('Synthetic QA session revoked on server.')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('Live session QA failed; no private values printed.')
        raise SystemExit(1)
