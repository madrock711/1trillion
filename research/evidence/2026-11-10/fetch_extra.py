import concurrent.futures,urllib.request,json,datetime,hashlib
from pathlib import Path
P=Path(__file__).parent
urls={'DRAM':'https://www.trendforce.com/price/dram/dram_spot','NAND':'https://www.trendforce.com/price/flash/flash_spot','BLS':'https://www.bls.gov/news.release/empsit.nr0.htm'}
urls.update({'after-'+k:'https://query1.finance.yahoo.com/v8/finance/chart/'+k+'?range=1d&interval=1m&includePrePost=true' for k in ['NVDA','AMD','MU','AVGO']})
def fetch(item):
 k,u=item
 try:
  raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read(); (P/(k+'.raw')).write_bytes(raw)
  (P/(k+'.source.json')).write_text(json.dumps({'url':u,'fetchedAt':datetime.datetime.now().astimezone().isoformat(),'rawHash':hashlib.sha256(raw).hexdigest()}),encoding='utf-8'); print(k,len(raw))
 except Exception as e:print(k,str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:list(ex.map(fetch,urls.items()))
