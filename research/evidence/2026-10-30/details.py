import base64,json,re
from pathlib import Path
p=Path('research/evidence/2026-10-30')
s=base64.b64decode(json.loads((p/'Treasury.raw.json').read_text())['raw']).decode()
for row in re.findall(r'<tr[^>]*>.*?</tr>',s,re.S):
 if '10/29/2026' in row or '10/28/2026' in row: print(re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',row)))
s=(p/'TrendForce.txt').read_text(encoding='utf-8'); i=s.find('DRAM Spot Price');print(s[i:i+500])
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(json.loads((p/f'after-{k}.raw.json').read_text())['raw']))['chart']['result'][0]; z=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and t>=d['meta']['currentTradingPeriod']['post']['start']];print(k,z[-1] if z else None,d['meta']['regularMarketPrice'],(z[-1][1]/d['meta']['regularMarketPrice']-1)*100 if z else None)
