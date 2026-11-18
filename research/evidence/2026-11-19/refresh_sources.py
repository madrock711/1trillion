import urllib.request,json,datetime,hashlib,concurrent.futures,time
from pathlib import Path
P=Path(__file__).parent
urls={k:'https://query1.finance.yahoo.com/v8/finance/chart/'+k+'?range=1d&interval=1m&includePrePost=true&x='+str(time.time()) for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO','CL=F','BZ=F']}
urls['fed']='https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm'
def fetch(k):
 try:
  u=urls[k];b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read();(P/(k+'.raw')).write_bytes(b);(P/(k+'.source.json')).write_text(json.dumps(dict(url=u,fetchedAt=datetime.datetime.now().astimezone().isoformat(),rawHash=hashlib.sha256(b).hexdigest())),encoding='utf-8')
  if k!='fed':
   r=json.loads(b)['chart']['result'][0];m=r['meta'];print(k,m['regularMarketPrice'],m.get('regularMarketChangePercent'),datetime.datetime.fromtimestamp(m['regularMarketTime']).isoformat())
  else:print(k,len(b))
 except Exception as e:print(k,str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=11) as ex:list(ex.map(fetch,urls))
