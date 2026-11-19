import urllib.request,json,datetime,hashlib,concurrent.futures
from pathlib import Path
P=Path(__file__).parent
urls={k:'https://api.stock.naver.com/stock/'+k+'.O/basic' for k in ['NVDA','AMD','MU','AVGO','QQQ','TQQQ','SOXX','SMH']}
urls.update({k:'https://query1.finance.yahoo.com/v8/finance/chart/'+k[6:]+'?range=1d&interval=1m&includePrePost=true' for k in ['after-NVDA','after-AMD','after-MU','after-AVGO']})
urls.update(anthropic='https://www.anthropic.com/news/anthropic-prices-initial-public-offering',DRAM='https://www.trendforce.com/price/dram/dram_spot',NAND='https://www.trendforce.com/price/flash/flash_spot',fed='https://www.federalreserve.gov/newsevents/speech/jefferson20261119a.htm',calendar='https://www.bls.gov/schedule/2026/home.htm')
def fetch(k):
 try:
  u=urls[k];b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read();(P/(k+'.raw')).write_bytes(b);(P/(k+'.source.json')).write_text(json.dumps(dict(url=u,fetchedAt=datetime.datetime.now().astimezone().isoformat(),rawHash=hashlib.sha256(b).hexdigest())),encoding='utf-8')
  if k in ['NVDA','AMD','MU','AVGO','QQQ','TQQQ','SOXX','SMH']:
   d=json.loads(b);print(k,d.get('closePrice'),d.get('fluctuationsRatio'),d.get('localTradedAt'),d.get('marketStatus'))
  else:print(k,len(b))
 except Exception as e:print(k,str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:list(ex.map(fetch,urls))
