import concurrent.futures, datetime, hashlib, json, re, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3]; P=Path(__file__).parent
def read(p): return (R/p).read_text(encoding='utf-8')
def write(p,v): (R/p).write_text(v,encoding='utf-8',newline='\n')
def dump(p,v): write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k): return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
keys=['NXT','FX','yahoo-NQF','yahoo-ESF','yahoo-CLF','yahoo-BZF']
old={k:ev(k) for k in keys}
def fetch(k):
 raw=urllib.request.urlopen(urllib.request.Request(old[k]['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read(); t=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds'); v={'url':old[k]['url'],'fetchedAt':t,'rawHash':hashlib.sha256(raw).hexdigest(),'data':json.loads(raw)}; dump('research/evidence/2026-10-14/final-'+k+'.json',v); return k,v
new=dict(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(fetch,keys))
now=max(v['fetchedAt'] for v in new.values()); snap=json.loads(read('assets/data/market-dashboard-latest.json')); before=snap['asOf']; issued=snap['generatedAt']
replacements={before:now,issued:now}
for k in ['NXT','FX']:
 rowsold=old[k]['data']['datas'] if k=='NXT' else [old[k]['data']['exchangeInfo']]; rowsnew=new[k]['data']['datas'] if k=='NXT' else [new[k]['data']['exchangeInfo']]
 for a,b in zip(rowsold,rowsnew):
  replacements[a['localTradedAt']]=b['localTradedAt']; replacements[a['closePrice']+'원']=b['closePrice']+'원'
  if k=='NXT': replacements[a['closePrice']+'원 · '+a['fluctuationsRatio']+'%']=b['closePrice']+'원 · '+b['fluctuationsRatio']+'%'
for k in keys[2:]:
 a=old[k]['data']['chart']['result'][0]['meta']; b=new[k]['data']['chart']['result'][0]['meta']; replacements[f"{a['regularMarketPrice']:,.2f}"]=f"{b['regularMarketPrice']:,.2f}"
 for m in [a,b]: m['iso']=datetime.datetime.fromtimestamp(m['regularMarketTime'],datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
 replacements[a['iso']]=b['iso']
def substitute(s):
 for a,b in sorted(replacements.items(),key=lambda x:-len(x[0])): s=s.replace(a,b)
 return s
for p in ['reports/2026-10-14.md','articles/market-2026-10-14.html','STATE.md']: write(p,substitute(read(p)))
snap=json.loads(substitute(json.dumps(snap,ensure_ascii=False))); snap['generatedAt']=now; snap['asOf']=now; snap['asOfDisplay']=now; snap['snapshotId']='20261014-'+now[11:16].replace(':','')
dump('assets/data/market-dashboard-'+snap['snapshotId']+'.json',snap); dump('assets/data/market-dashboard-latest.json',snap)
fp=next(R.glob('research/evaluation/forecasts/2026-10-14-0809-same-close.json')); f=json.loads(fp.read_text(encoding='utf-8')); f.update(forecastId='2026-10-14-'+now[11:16].replace(':','')+'-same-close',supersedes=f['forecastId'],issuedAt=now,dataCutoffAt=now,reportSha256=hashlib.sha256(read('reports/2026-10-14.md').encode()).hexdigest()); f.pop('contentHash',None); f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(); dump('research/evaluation/forecasts/'+f['forecastId']+'.json',f)
for p in ['index.html','articles/index.html','articles/market.html']:
 s=read(p); s=s.replace(issued,now).replace('2026.10.14 · '+issued[11:16]+' KST','2026.10.14 · '+now[11:16]+' KST'); write(p,s)
print(now,f['forecastId'],f['contentHash'])
