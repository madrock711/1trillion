import base64,concurrent.futures,datetime,hashlib,json,pathlib,urllib.request,re
P=pathlib.Path(__file__).parent
urls={'Meta':'https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Announces-Pricing-of-Offering-of-Depositary-Shares-Representing-Series-A-Mandatory-Convertible-Preferred-Stock-and-Offering-of-Class-A-Common-Stock-in-Connection-with-Forward-Sale-Agreements/default.aspx','SK-invitation':'https://news.skhynix.com/en/q3-2026-earnings-conference-call-invitation/','Microsoft':'https://www.microsoft.com/en-us/investor/default','Amazon':'https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report','Alphabet':'https://abc.xyz/investor/','Samsung':'https://www.samsung.com/global/ir/','CB':'https://www.conference-board.org/topics/consumer-confidence/'}

def fetch(kv):
 k,u=kv
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();v={'url':u,'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'rawHash':hashlib.sha256(b).hexdigest(),'raw':base64.b64encode(b).decode()};(P/(k+'.raw.json')).write_text(json.dumps(v)+'\n',encoding='utf-8',newline='\n');return k,len(b)
 except Exception as e:return k,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:print(list(pool.map(fetch,urls.items())))
