import json,base64,re
from pathlib import Path
p=Path('research/evidence/2026-10-30')
for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO','NQF','ESF','BZF','CLF']:
 d=json.loads((p/f'yahoo-{k}.json').read_text())['data']['chart']['result'][0]; q=d['indicators']['quote'][0]['close'];print(k,q[-1],(q[-1]/q[-2]-1)*100)
for k in ['TrendForce','Treasury','BEA']:
 d=json.loads((p/f'{k}.raw.json').read_text());s=base64.b64decode(d['raw']).decode(errors='replace');s=re.sub('<[^>]+>',' ',s);s=re.sub(r'\s+',' ',s);(p/f'{k}.txt').write_text(s,encoding='utf-8');print(k,s[-1600:] if k=='Treasury' else [s[max(0,m.start()-100):m.start()+500] for m in re.finditer('DDR5|Oct. 30|October 30',s)][:5])
