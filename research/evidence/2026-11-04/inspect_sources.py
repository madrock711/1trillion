from pathlib import Path
import json,base64,re,datetime
P=Path('research/evidence/2026-11-04')
for k in ['AMD','NVDA','MU','AVGO']:
 d=json.loads(base64.b64decode(json.loads((P/f'after-{k}.raw.json').read_text())['raw']))['chart']['result'][0];p=d['meta']['currentTradingPeriod']['post'];v=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and p['start']<=t<p['end']]; print(k,v[-1] if v else None)
for k in ['KOSPI','122630']:print(k,json.loads((P/f'{k}.json').read_text())['data'][:2])
