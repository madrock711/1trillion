import base64,datetime,hashlib,json,pathlib,urllib.request
P=pathlib.Path(__file__).parent
U={'Amazon-results':'https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Third-Quarter-Results/default.aspx','Intel-results':'https://www.intc.com/filings-reports/all-sec-filings/content/0000050863-26-000188/q326earningsrelease.htm','BEA-PCE':'https://bea.gov/index.php/news/2026/personal-income-and-outlays-september-2026','BEA-GDP':'https://bea.gov/data/gdp/gross-domestic-product','BLS-ECI':'https://www.bls.gov/schedule/news_release/eci.htm'}
for k,u in U.items():
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=15).read();(P/(k+'.raw.json')).write_text(json.dumps({'url':u,'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'rawHash':hashlib.sha256(b).hexdigest(),'raw':base64.b64encode(b).decode()})+'\n',encoding='utf-8');print(k,len(b))
 except Exception as e:print(k,str(e))
