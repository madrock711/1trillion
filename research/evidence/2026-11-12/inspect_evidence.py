import json,sys
from pathlib import Path
sys.path.insert(0,'scripts');import publish_market_research as r
P=Path('research/evidence/2026-11-12/collections/075858-945125')
e=lambda k:json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
print('PREV',r.previous_session({k:e(k) for k in ['KOSPI','KOSPI-history','KOSPI-basic']},'2026-11-11'))
print('KODEX',e('122630')['data'][:2]);print('FX',e('FX')['data'])
for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO','BZF','CLF']:
 m=e('yahoo-'+k)['data']['chart']['result'][0]['meta'];print(k,{i:m.get(i) for i in ['regularMarketPrice','regularMarketChangePercent','regularMarketTime']})
from bs4 import BeautifulSoup
for k in ['DRAM','NAND']:
 s=BeautifulSoup(Path('research/evidence/2026-11-12/'+k+'.raw').read_bytes(),'html.parser').get_text(' ',strip=True);ix=s.find('Last Update');print(k,s[ix:ix+3500])
