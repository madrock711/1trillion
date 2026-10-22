import base64,concurrent.futures,datetime,hashlib,json,pathlib,urllib.request
P=pathlib.Path(__file__).parent
urls={
'Treasury':'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2026',
'BOK-decision':'https://www.bok.or.kr/eng/bbs/E0000634/view.do?nttId=11065825&menuNo=400069',
'Claims':'https://www.dol.gov/ui/data.pdf',
'Michigan':'https://www.sca.isr.umich.edu/',
'PMI-calendar':'https://www.pmi.spglobal.com/Public/Release/ReleaseDates',
'Lam':'https://newsroom.lamresearch.com/',
'KRX-calendar':'https://global.krx.co.kr/contents/GLB/06/0601/0601/GLB06010101.jsp',
}
def fetch(kv):
 k,u=kv
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();v={'url':u,'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'rawHash':hashlib.sha256(b).hexdigest(),'raw':base64.b64encode(b).decode()};(P/(k+'.raw.json')).write_text(json.dumps(v)+'\n',encoding='utf-8',newline='\n');return k,len(b)
 except Exception as e:return k,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:print(list(pool.map(fetch,urls.items())))
