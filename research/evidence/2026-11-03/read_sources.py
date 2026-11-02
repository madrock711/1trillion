import json,base64
from pathlib import Path
import re
p=Path('research/evidence/2026-11-03')
for k in ['TrendForce','NAND']:
 s=re.sub(r'<[^>]+>', ' ',base64.b64decode(json.loads((p/(k+'.raw.json')).read_text())['raw']).decode());s=re.sub(r'\s+',' ',s)
 for word in ['Last Update','DDR5 16Gb','DDR4 16Gb','512Gb']:
  i=s.find(word);print(k,s[max(0,i-50):i+400])
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(json.loads((p/('after-'+k+'.raw.json')).read_text())['raw']))['chart']['result'][0]; post=d['meta']['currentTradingPeriod']['post'];v=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']];print(k,v[-1] if v else None,d['meta']['regularMarketPrice'])
