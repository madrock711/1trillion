import concurrent.futures, json, time, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3]
paths=['/articles/market-2026-10-14.html','/assets/images/articles/market-2026-10-14-memory-competition-cpi-1200x630.png','/assets/data/market-dashboard-latest.json']
urls=[b+p+'?verify='+str(time.time_ns()) for b in ['https://www.hpmplab.com','https://main.d2pg7r2qjjb9u9.amplifyapp.com'] for p in paths]
def check(u):
 with urllib.request.urlopen(u,timeout=20) as r:
  data=r.read(); assert r.status==200
  if '.html?' in u: assert '중국 메모리 경쟁'.encode() in data and b'market-2026-10-14-memory-competition-cpi' in data
  if '.json?' in u: assert json.loads(data)['snapshotId']=='20261014-0813'
  if '.png?' in u: assert data[:8]==b'\x89PNG\r\n\x1a\n'
  return {'url':u,'status':r.status,'bytes':len(data)}
results=list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(check,urls))
(R/'research/evidence/2026-10-14/live-check.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
for v in results: print(v['status'],v['url'].split('?')[0],v['bytes'])
