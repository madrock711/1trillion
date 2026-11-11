import sys,urllib.request,datetime,re,concurrent.futures
sys.path.insert(0,'scripts');import update_yield_spreads as y
original=y.fetch_series
def recent(k,u,d):
 url=f'https://fred.stlouisfed.org/series/{k}/downloaddata/{k}.txt'
 raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read()
 from pathlib import Path
 Path(f'research/evidence/2026-11-12/FRED-{k}.raw').write_bytes(raw)
 rows=[]
 for day,val in re.findall(r'(\d{4}-\d\d-\d\d)\s+(-?\d+\.\d+)',raw.decode()):
  day=datetime.date.fromisoformat(day)
  if day<=d:rows.append(y.Observation(day,float(val)))
 if not rows:raise ValueError(k+' no observations')
 print(k,rows[-1],flush=True)
 return rows
y.fetch_series=recent
raise SystemExit(y.main())
