import base64,concurrent.futures,datetime,hashlib,json,pathlib,urllib.request,re
P=pathlib.Path(__file__).parent
urls={'Meta':'https://finance.yahoo.com/markets/stocks/articles/meta-announces-launch-offering-depositary-105800284.html','Meta-SEC':'https://www.sec.gov/Archives/edgar/data/1326801/000119312526431009/d127909ds3asr.htm','Anthropic':'https://www.anthropic.com/news/s1-sec','Anthropic-SEC':'https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/anthropicpbc-sx1.htm','SpaceX':'https://ir.spacex.com/updates/releases-details/2026/SPACEX-SECURES-40-BILLION-IN-THE-LARGEST-GPU-FINANCING-EVER-2026-EnDqGhTAB3/default.aspx','SpaceX-SEC':'https://www.sec.gov/Archives/edgar/data/1181412/000110465926118614/tm2628247d1_8k.htm','Microsoft':'https://www.microsoft.com/en-us/investor/default','Amazon':'https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report'}
def fetch(kv):
 k,u=kv
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();v={'url':u,'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'rawHash':hashlib.sha256(b).hexdigest(),'raw':base64.b64encode(b).decode()};(P/(k+'.raw.json')).write_text(json.dumps(v)+'\n',encoding='utf-8',newline='\n');return k,len(b)
 except Exception as e:return k,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:print(list(pool.map(fetch,urls.items())))
