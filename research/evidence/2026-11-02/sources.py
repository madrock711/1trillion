import base64, concurrent.futures, datetime, hashlib, json, pathlib, urllib.request
P=pathlib.Path(__file__).parent
urls={'Treasury':'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2026','TrendForce':'https://www.trendforce.com/price/dram/dram_spot','NAND':'https://www.trendforce.com/price/flash/flash_spot','Solidigm':'https://news.skhynix.com/en/fact-12/','FOMC':'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm','BEA':'https://www.bea.gov/news/schedule','KOSPI-fchart':'https://fchart.stock.naver.com/sise.nhn?symbol=KOSPI&timeframe=day&count=5&requestType=0','KODEX-fchart':'https://fchart.stock.naver.com/sise.nhn?symbol=122630&timeframe=day&count=5&requestType=0'}
for s in ['NVDA','AMD','MU','AVGO']:urls['after-'+s]=f'https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=1d&interval=5m&includePrePost=true'
def fetch(kv):
 k,u=kv
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();v={'url':u,'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'rawHash':hashlib.sha256(b).hexdigest(),'raw':base64.b64encode(b).decode()};(P/(k+'.raw.json')).write_text(json.dumps(v)+'\n',encoding='utf-8',newline='\n');return k,len(b)
 except Exception as e:return k,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:print(list(pool.map(fetch,urls.items())))
