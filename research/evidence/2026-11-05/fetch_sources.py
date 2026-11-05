import base64,concurrent.futures,datetime,hashlib,json,urllib.request
from pathlib import Path
P=Path(__file__).parent
urls={
 'DRAM':'https://www.trendforce.com/price/dram/dram_spot',
 'NAND':'https://www.trendforce.com/price/flash/flash_spot',
 'BLS':'https://www.bls.gov/schedule/2026/11_sched.htm',
 'FOMC':'https://www.federalreserve.gov/newsevents/2026-november.htm',
 'Siltronic':'https://www.siltronic.com/en/press/press-releases/siltronic-slightly-raises-sales-guidance-for-2026-higher-demand-drives-volume-development-in-q3-2026.html',
 'Qualcomm':'https://investor.qualcomm.com/news-events/press-releases/news-details/2026/Qualcomm-Earnings-Release-Available-on-Companys-Investor-Relations-Website-c5258267a/default.aspx',
 'Starlink':'https://www.qualcomm.com/news/releases/2026/11/spacex-selects-qualcomm-to-accelerate-starlink-mobile-s-nationwi',
 'Reuters':'https://live.euronext.com/en/financial-news/world-shares-advance-democrats-victory-eases-political-uncertainty',
}
for s in ['NVDA','AMD','MU','AVGO']:
 urls['after-'+s]=f'https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=1d&interval=5m&includePrePost=true'
def fetch(item):
 k,u=item
 try:
  raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read()
  v={'url':u,'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'rawHash':hashlib.sha256(raw).hexdigest(),'raw':base64.b64encode(raw).decode()}
  (P/(k+'.raw.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return k,len(raw)
 except Exception as error:return k,str(error)
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:print(list(pool.map(fetch,urls.items())))
