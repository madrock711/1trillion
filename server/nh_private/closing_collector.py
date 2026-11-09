"""Owner-independent closing collection, invoked only by the dedicated AWS rule."""
import json
from datetime import datetime, timedelta, timezone

RULE_ARN = 'arn:aws:events:us-east-1:514670561185:rule/yeonma-nh-close-archive'
FUNCTION_ARN = 'arn:aws:lambda:us-east-1:514670561185:function:yeonma-nh-private'
KST = timezone(timedelta(hours=9))


def collect(event, context, service_factory, utcnow=None):
    now = (utcnow or (lambda: datetime.now(timezone.utc)))()
    if (not isinstance(event, dict) or event.get('version') != '0'
            or event.get('source') != 'aws.events' or event.get('detail-type') != 'Scheduled Event'
            or event.get('account') != '514670561185' or event.get('region') != 'us-east-1'
            or event.get('resources') != [RULE_ARN] or event.get('detail') != {}
            or getattr(context, 'invoked_function_arn', '') != FUNCTION_ARN):
        return {'status': 'rejected'}
    try:
        stamp = datetime.fromisoformat(event['time'].replace('Z', '+00:00'))
        if stamp.tzinfo is None or not -60 <= (now - stamp).total_seconds() <= 900:
            return {'status': 'expired'}
    except (KeyError, TypeError, ValueError, AttributeError):
        return {'status': 'rejected'}
    local = now.astimezone(KST)
    date = local.date().isoformat()
    if (stamp.astimezone(KST).date() != local.date() or local.weekday() > 4
            or not (16 <= local.hour < 19)):
        return {'status': 'outside-window'}
    try:
        service = service_factory()
        session = service.session_provider()
        if session['date'] != date:
            result = {'status': 'skipped', 'date': date, 'reason': 'not-trading-day'}
        elif not session['closed']:
            result = {'status': 'skipped', 'date': date, 'reason': 'market-open'}
        else:
            data = service.get(date)
            if (data.get('tradeDate') != date or data.get('dateVerified') is not True
                    or data.get('persisted') is not True or data.get('sessionStatus') != 'closed'):
                raise ValueError('incomplete closing snapshot')
            result = {'status': 'saved', 'date': date,
                      'rows': {m: len(data[m]) for m in ('amount', 'quantity')}}
        # Only non-sensitive operational metadata reaches CloudWatch.
        print('NH closing collection: ' + json.dumps(result, separators=(',', ':')))
        return result
    except Exception:
        print('NH closing collection: failed')
        # Raising, rather than returning HTTP 503, enables Lambda asynchronous retries.
        raise RuntimeError('NH closing collection failed') from None
