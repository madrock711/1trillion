"""발행 직전 빠른 핵심값만 병렬 조회. 전일 확정 원천은 보존한다."""
import concurrent.futures
from collect import urls,fetch
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  results=list(pool.map(fetch,[(k,urls[k]) for k in ['FX','NXT','NQF','ESF','BZF','CLF']]))
 print(results)
 assert all(x[1]=='OK' for x in results)
