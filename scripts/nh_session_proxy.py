"""Preserve every existing Amplify rewrite; add only the private session proxy."""
from __future__ import annotations

import argparse
import logging

APP = 'd2pg7r2qjjb9u9'
RULE = {'source': '/api/private/nh/session/<*>',
        'target': 'https://dfx1foieoh.execute-api.us-east-1.amazonaws.com/api/private/nh/session/<*>',
        'status': '200'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    import boto3
    from botocore.config import Config
    logging.disable(logging.CRITICAL)
    cfg = Config(region_name='us-east-1', proxies={})
    session = boto3.Session(region_name='us-east-1')
    identity = session.client('sts', config=cfg).get_caller_identity()
    if identity['Account'] != '514670561185' or not identity['Arn'].endswith(':user/codex-amplify-manager'):
        raise RuntimeError('Unexpected AWS identity')
    amplify = session.client('amplify', config=cfg)
    app = amplify.get_app(appId=APP)['app']
    if app['repository'].removesuffix('.git') != 'https://github.com/madrock711/1trillion':
        raise RuntimeError('Unexpected repository')
    rules = app.get('customRules', [])
    existing = [rule for rule in rules if rule['source'] == RULE['source']]
    if existing:
        if any({k: r.get(k) for k in RULE} != RULE for r in existing) or len(existing) != 1:
            raise RuntimeError('Conflicting proxy rule; not overwriting')
        print('Private session proxy already configured.')
        return
    new_rules = [RULE] + rules
    if not args.apply:
        print(f'Plan: add one private session proxy; preserve {len(rules)} existing rules.')
        return
    amplify.update_app(appId=APP, customRules=new_rules)
    verified = amplify.get_app(appId=APP)['app']['customRules']
    if verified != new_rules:
        raise RuntimeError('Proxy configuration verification failed')
    print(f'Private session proxy configured; {len(rules)} existing rules preserved.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Private session proxy setup failed; inspect AWS permissions and configuration. No credentials printed.')
        raise SystemExit(1)
