import json, pathlib, datetime
p=pathlib.Path('research/evidence/2026-11-04')
for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO','NQF','ESF','BZF','CLF']:
 d=json.loads((p/f'yahoo-{k}.json').read_text())['data']['chart']['result'][0]; q=d['indicators']['quote'][0]['close']; m=d['meta']; print(k,'close',q[-1], 'change',round((q[-1]/q[-2]-1)*100,2),'marketTime',datetime.datetime.fromtimestamp(m['regularMarketTime'],datetime.timezone(datetime.timedelta(hours=9))))
for k in ['005930','000660','122630']:
 d=json.loads((p/f'{k}.json').read_text()); print(k,d['data'][:2])

