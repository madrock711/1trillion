"""두 도메인의 cache-busted 실제 자산 바이트를 로컬과 대조한다."""
import concurrent.futures,datetime,hashlib,json,time,urllib.request,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
paths=['articles/market-2026-10-30.html','assets/images/articles/market-2026-10-30-cloud-capex-1200x630.png','assets/data/market-dashboard-latest.json','charts/us_yield_spreads_90d_2026-10-30.png','charts/us_yield_spreads_long_term_2026-10-30.png']
def check(v):
 base,path=v;u=base+'/'+path+'?verify='+str(time.time_ns())
 with urllib.request.urlopen(u,timeout=20) as r:
  b=r.read();assert r.status==200;assert b==subprocess.check_output(['git','show','HEAD:'+path],cwd=R),path+' byte mismatch'
  return {'url':u,'status':200,'sha256':hashlib.sha256(b).hexdigest(),'checkedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:rows=list(pool.map(check,[(b,p) for b in ['https://www.hpmplab.com','https://main.d2pg7r2qjjb9u9.amplifyapp.com'] for p in paths]))
(P/'live-check.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8',newline='\n');print('10 assets HTTP 200 and byte-identical')
