import concurrent.futures,datetime,hashlib,json,pathlib,urllib.request
p=pathlib.Path('research/evidence/2026-10-15')
urls={'CPI':'https://www.bls.gov/news.release/cpi.nr0.htm','ASML':'https://www.investor.asml.com/news-releases/news-release-details/asml-reports-eu11.7-billion-total-net-sales-and-eu5.0-billion-net-income-q3-2026','TrendForce':'https://www.trendforce.com/price/dram/dram_spot','TSMC':'https://investor.tsmc.com/english/quarterly-results/2026/q3','BLS-calendar':'https://www.bls.gov/schedule/2026/10_sched.htm','BAC-Treasury':'https://home.treasury.gov/news/press-releases/sb0657','BeigeBook':'https://www.federalreserve.gov/monetarypolicy/beigebook202610.htm','KOSPI-fchart':'https://fchart.stock.naver.com/sise.nhn?symbol=KOSPI&timeframe=day&count=5&requestType=0','KODEX-fchart':'https://fchart.stock.naver.com/sise.nhn?symbol=122630&timeframe=day&count=5&requestType=0'}
for s in ['NVDA','AMD','MU','AVGO']:urls['after-'+s]=f'https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=1d&interval=5m&includePrePost=true'
def fetch(kv):
 k,u=kv
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();(p/(k+'.txt')).write_bytes(b);print(k,len(b))
  return {'id':k,'url':u,'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'rawHash':hashlib.sha256(b).hexdigest(),'status':'available'}
 except Exception as e:return {'id':k,'url':u,'status':'unavailable','reason':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:rows=list(pool.map(fetch,urls.items()))
(p/'source-manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(rows,ensure_ascii=False))
