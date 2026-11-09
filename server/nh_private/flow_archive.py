"""Private dated flow snapshots; shares the existing table, never token keys."""
import json
import re
import zlib
from datetime import datetime, timezone, timedelta
from urllib.request import build_opener, ProxyHandler

KST = timezone(timedelta(hours=9))


def market_session():
    # Independent date anchor: NH's tradingStatus rows contain time, not date.
    with build_opener(ProxyHandler({})).open('https://m.stock.naver.com/api/index/KOSPI/basic', timeout=4) as r:
        data = json.loads(r.read(200000))
    stamp = datetime.fromisoformat(data['localTradedAt']).astimezone(KST)
    if data.get('itemCode') != 'KOSPI' or data.get('stockEndType') != 'index' or data.get('marketStatus') not in ('OPEN', 'CLOSE'):
        raise ValueError('invalid market date anchor')
    now = datetime.now(KST)
    if stamp.date() > now.date() or stamp.weekday() > 4:
        raise ValueError('invalid market date')
    return {'date': stamp.date().isoformat(), 'closed': data['marketStatus'] == 'CLOSE'}


class FlowArchive:
    def __init__(self, ddb, table, identity):
        self.ddb, self.table, self.prefix = ddb, table, 'flow#' + identity + '#'

    def read(self, date):
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
            raise ValueError('invalid archive date')
        row = self.ddb.get_item(TableName=self.table, Key={'id': {'S': self.prefix + date}}, ConsistentRead=True).get('Item')
        if not row:
            return None
        decoder = zlib.decompressobj()
        raw = decoder.decompress(bytes(row['payload']['B']), 2000001)
        if len(raw) > 2000000 or decoder.unconsumed_tail or not decoder.eof:
            raise ValueError('invalid archive size')
        data = json.loads(raw)
        if data.get('tradeDate') != date or data.get('dateVerified') is not True or not data.get('persisted'):
            raise ValueError('invalid archive')
        return data

    def latest(self):
        row = self.ddb.get_item(TableName=self.table, Key={'id': {'S': self.prefix + 'latest'}}, ConsistentRead=True).get('Item')
        return self.read(row['trade_date']['S']) if row else None

    def save(self, data):
        raw = zlib.compress(json.dumps(data, separators=(',', ':')).encode())
        if len(raw) > 350000:
            raise ValueError('archive too large')
        self.ddb.update_item(TableName=self.table, Key={'id': {'S': self.prefix + data['tradeDate']}},
            UpdateExpression='SET payload = :p, fetched_at = :at',
            ConditionExpression='attribute_not_exists(fetched_at) OR fetched_at <= :at',
            ExpressionAttributeValues={':p': {'B': raw}, ':at': {'S': data['fetchedAt']}})
        self.ddb.update_item(TableName=self.table, Key={'id': {'S': self.prefix + 'latest'}},
            UpdateExpression='SET trade_date = :d',
            ConditionExpression='attribute_not_exists(trade_date) OR trade_date <= :d',
            ExpressionAttributeValues={':d': {'S': data['tradeDate']}})
