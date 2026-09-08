import concurrent.futures,datetime,hashlib,json,pathlib,urllib.request
ROOT=pathlib.Path(__file__).parent
urls={
 'KOSPI':'https://m.stock.naver.com/api/index/KOSPI/price?pageSize=10&page=1',
 'KOSDAQ':'https://m.stock.naver.com/api/index/KOSDAQ/price?pageSize=10&page=1',
 'KOSPI-integration':'https://m.stock.naver.com/api/index/KOSPI/integration',
 'KOSPI-basic':'https://m.stock.naver.com/api/index/KOSPI/basic',
 'FX':'https://api.stock.naver.com/marketindex/exchange/FX_USDKRW',
 'NXT':'https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660',
}
for code in ['122630','005930','000660']:
 urls[code]=f'https://m.stock.naver.com/api/stock/{code}/price?pageSize=10&page=1'
 urls[code+'-integration']=f'https://m.stock.naver.com/api/stock/{code}/integration'
for symbol in ['NQ','ES','BZ','CL']:
 urls[symbol+'F']=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}=F?range=5d&interval=1d&includePrePost=true'
def fetch(item):
 key,url=item
 try:
  raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read()
  obj={'url':url,'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds'),'rawHash':hashlib.sha256(raw).hexdigest(),'data':json.loads(raw)}
  (ROOT/(key+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
  return key,'OK'
 except Exception as e:return key,str(e)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  for r in pool.map(fetch,urls.items()):print(r)
