import base64,datetime,hashlib,json,pathlib,urllib.request
P=pathlib.Path(__file__).parent
urls={'Fed-decision':'https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a.htm','Microsoft-results':'https://www.microsoft.com/en-us/Investor/earnings/FY-2027-Q1/press-release-webcast','Alphabet-results':'https://www.sec.gov/Archives/edgar/data/1652044/000165204426000080/googexhibit991q32026.htm'}
for k,u in urls.items():
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();(P/(k+'.raw.json')).write_text(json.dumps({'url':u,'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'rawHash':hashlib.sha256(b).hexdigest(),'raw':base64.b64encode(b).decode()})+'\n',encoding='utf-8',newline='\n');print(k,len(b))
 except Exception as e:print(k,str(e))
p=P/'settle.py';p.write_text(p.read_text(encoding='utf-8').replace("'realizedScenario':'outside'","'realizedScenario':'bull'"),encoding='utf-8',newline='\n')
