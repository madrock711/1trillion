"""Read deployment metadata and explicitly invoke closing collection without browser auth.

No credentials, NH tokens, Google claims, cookies or flow values are printed.
This checks the live collector path, not a future automatic scheduled invocation.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler


def main():
    if sys.argv[1:] != ['--run']:
        raise ValueError('Explicit --run is required')
    import boto3
    from botocore.config import Config
    logging.disable(logging.CRITICAL)
    config = Config(region_name='us-east-1', proxies={})
    aws = boto3.Session(region_name='us-east-1')
    who = aws.client('sts', config=config).get_caller_identity()
    assert who['Account'] == '514670561185' and who['Arn'].endswith(':user/codex-amplify-manager')
    cf, fn = aws.client('cloudformation', config=config), aws.client('lambda', config=config)
    stack = cf.describe_stacks(StackName='yeonma-nh-private')['Stacks'][0]
    assert stack['StackStatus'] == 'UPDATE_COMPLETE'
    resources = cf.list_stack_resources(StackName='yeonma-nh-private')['StackResourceSummaries']
    assert all(any(r['LogicalResourceId'] == name and r['ResourceStatus'].endswith('_COMPLETE') for r in resources)
               for name in ('ClosingArchiveRule', 'ClosingArchivePermission'))
    rule = 'arn:aws:events:us-east-1:514670561185:rule/yeonma-nh-close-archive'
    policy = json.loads(fn.get_policy(FunctionName='yeonma-nh-private')['Policy'])
    assert any(s.get('Principal', {}).get('Service') == 'events.amazonaws.com'
               and s.get('Condition', {}).get('ArnLike', {}).get('AWS:SourceArn') == rule
               and s.get('Condition', {}).get('StringEquals', {}).get('AWS:SourceAccount') == '514670561185'
               for s in policy['Statement'])
    event = {'version': '0', 'source': 'aws.events', 'detail-type': 'Scheduled Event',
             'account': '514670561185', 'region': 'us-east-1', 'resources': [rule], 'detail': {},
             'time': datetime.now(timezone.utc).isoformat()}
    response = fn.invoke(FunctionName='yeonma-nh-private', InvocationType='RequestResponse',
                         Payload=json.dumps(event).encode())
    data = json.loads(response['Payload'].read())
    assert not response.get('FunctionError') and data.get('status') == 'saved'
    print('Live closing collector without browser login:', json.dumps(data))
    try:
        build_opener(ProxyHandler({})).open('https://www.hpmplab.com/api/private/nh/session/flow', timeout=20)
        raise AssertionError('Anonymous flow access was allowed')
    except HTTPError as error:
        assert error.code == 401
    print('Anonymous access denied; scheduled collection did not make private flow public.')
    print('Future automatic execution is separate from this explicit live invocation.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Live closing schedule verification failed. No private values printed.', file=sys.stderr)
        raise SystemExit(1)
