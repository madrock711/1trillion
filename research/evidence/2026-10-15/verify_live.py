"""두 도메인의 cache-busted 기사·대시보드·이미지·차트를 검사한다."""
import concurrent.futures, datetime, hashlib, json, time, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
paths=['/articles/market-2026-10-15.html','/assets/images/articles/market-2026-10-15-cpi-chip-pressure-1200x630.png','/assets/data/market-dashboard-latest.json','/charts/us_yield_spreads_90d_2026-10-15.png','/charts/us_yield_spreads_long_term_2026-10-15.png']
def check(u):
 with urllib.request.urlopen(u,timeout=20) as r:
  data=r.read();assert r.status==200
  if '.html?' in u:assert '미국 물가 재가속'.encode() in data and b'2026-10-15T08:07:53+09:00' in data and b'market-2026-10-15-cpi-chip-pressure' in data
  if '.json?' in u:assert json.loads(data)['snapshotId']=='20261015-0807'
  if '.png?' in u:assert data[:8]==b'\x89PNG\r\n\x1a\n'
  return {'url':u,'status':r.status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'checkedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')}
urls=[b+p+'?verify='+str(time.time_ns()) for b in ['https://www.hpmplab.com','https://main.d2pg7r2qjjb9u9.amplifyapp.com'] for p in paths]
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:rows=list(pool.map(check,urls))
(P/'live-check.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8',newline='\n')
for x in rows:print(x['status'],x['url'].split('?')[0],x['bytes'])
