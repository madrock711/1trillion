"""발행 직전 병렬 조회와 동일 기준 시각 봉인."""
import concurrent.futures,datetime,hashlib,html,importlib.util,json,re,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent;TZ=datetime.timezone(datetime.timedelta(hours=9));DATE='2026-10-16'
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
urls={'NXT':'https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660','FX':'https://api.stock.naver.com/marketindex/exchange/FX_USDKRW'}
for k in ['NQ','ES','CL','BZ']:urls['yahoo-'+k+'F']=f'https://query1.finance.yahoo.com/v8/finance/chart/{k}=F?range=1d&interval=5m&includePrePost=true'
def fetch(kv):
 k,u=kv;b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();v={'url':u,'fetchedAt':datetime.datetime.now(TZ).isoformat(timespec='seconds'),'rawHash':hashlib.sha256(b).hexdigest(),'data':json.loads(b)};dump('research/evidence/'+DATE+'/final-'+k+'.json',v);return k,v
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:ev=dict(pool.map(fetch,urls.items()))
cutoff=max(x['fetchedAt'] for x in ev.values());issued=datetime.datetime.now(TZ).isoformat(timespec='seconds');sid='20261016-'+issued[11:16].replace(':','');fid=DATE+'-'+issued[11:16].replace(':','')+'-same-close'
nxt=ev['NXT']['data']['datas'];fx=ev['FX']['data']['exchangeInfo'];assert len(nxt)==2 and all(x['marketStatus']=='OPEN' and x['localTradedAt'].startswith(DATE) and x['accumulatedTradingVolume'] not in ['-','0'] for x in nxt)
fast='\n'.join(f"|{x['stockName']} NXT ({x['marketStatus']})|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|" for x in nxt)+f"\n|하나은행 USD/KRW 고시|{fx['closePrice']}원|{fx['localTradedAt']}|"
for k in ['NQF','ESF','CLF','BZF']:
 m=ev['yahoo-'+k]['data']['chart']['result'][0]['meta'];t=datetime.datetime.fromtimestamp(m['regularMarketTime'],TZ).isoformat(timespec='seconds');fast+=f"\n|{k} 최근 거래|{m['regularMarketPrice']:,.2f}|{t}|"
report=read('reports/'+DATE+'.md').replace('작성 PREPARED / 데이터 최종 확인 PREPARED',f'작성 {issued} / 데이터 최종 확인 {cutoff}').replace('FAST_TABLE','|항목|최근값|원천 시각|\n|---|---:|---|\n'+fast);write('reports/'+DATE+'.md',report)
rows=[x.split('|')[1:-1] for x in ('|항목|최근값|원천 시각|\n'+fast).splitlines()];table='<div class="article-table-wrap"><table class="article-data-table"><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
s=read('articles/market-'+DATE+'.html').replace('FAST_TABLE',table).replace('작성 PREPARED · 데이터 최종 확인 PREPARED',f'작성 {issued} · 데이터 최종 확인 {cutoff}');s=re.sub(r'2026\.10\.16 · 작성 \d{2}:\d{2} KST','2026.10.16 · 작성 '+issued[11:16]+' KST',s)
for prop in ['article:published_time','article:modified_time']:s=re.sub(r'(<meta property="'+prop+r'" content=")[^"]+',lambda m:m[1]+issued,s)
write('articles/market-'+DATE+'.html',s)
for page in ['articles/market-'+DATE+'.html','index.html','articles/index.html','articles/market.html']:
 s=read(page)
 def ld(m):
  j=json.loads(m[1])
  if j.get('@type')=='Article':j.update(datePublished=issued,dateModified=issued)
  for n in j.get('@graph',[j]):
   for x in n.get('mainEntity',{}).get('itemListElement',[]):
    if x.get('url','').endswith('market-'+DATE+'.html'):x.update(datePublished=issued,dateModified=issued)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,s,flags=re.S);write(page,s)
s=json.loads(read('research/evidence/'+DATE+'/prepared-dashboard.json'));s.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff)
s['checkpoints']=[{'label':x['stockName']+' NXT','value':x['closePrice']+'원 · '+x['fluctuationsRatio']+'%','detail':x['marketStatus']+' · '+x['localTradedAt'],'tone':'warning'} for x in nxt]+[{'label':'하나은행 USD/KRW','value':fx['closePrice']+'원','detail':fx['localTradedAt'],'tone':'warning'}]
assert not (R/'assets/data'/('market-dashboard-'+sid+'.json')).exists();dump('assets/data/market-dashboard-'+sid+'.json',s);dump('assets/data/market-dashboard-latest.json',s)
state=read('STATE.md').replace('작성 PREPARED, 데이터 최종 확인 PREPARED',f'작성 {issued}, 데이터 최종 확인 {cutoff}');state+=f'- 대시보드 assets/data/market-dashboard-{sid}.json, 전망 research/evaluation/forecasts/{fid}.json.\n';write('STATE.md',state)
f=json.loads(read('research/evaluation/forecasts/2026-10-15-0807-same-close.json'));f.update(forecastId=fid,reportPath='reports/'+DATE+'.md',reportSha256=hashlib.sha256(report.encode()).hexdigest(),issuedAt=issued,dataCutoffAt=cutoff,reference={'price':5554.22,'asOf':'2026-10-15T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':5650,'high':5800,'probability':.25},'base':{'low':5450,'high':5650,'probability':.45},'bear':{'low':5200,'high':5450,'probability':.30}},pathEnvelope={'low':5050,'high':5950,'coverage':.9},posture={'attack':10,'wait':50,'defense':40},drivers=[{'id':'ppi-financing','rank':1,'claim':'PPI와 AI 금융비용 부담','validationMetric':'BLS·미국 반도체·환율'},{'id':'demand','rank':2,'claim':'TSMC 주문 전망과 MU 반등','validationMetric':'TSMC IR·MU·국내 메모리'}]);f['target'].update(sessionDate=DATE,previousSessionDate='2026-10-15')
for k,t in f['scenarioTriggers'].items():
 t['observeBy']=DATE+'T15:20:00+09:00'
 for c in t['conditions']:
  if c['metricId']=='kospi_price':c['threshold']=5650 if k=='bull' or c['operator']=='lte' else 5450
f.pop('contentHash');f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();path=R/'research/evaluation/forecasts'/f'{fid}.json';assert not path.exists();dump(str(path.relative_to(R)),f)
sessions=json.loads(read('research/evaluation/trading-sessions.json'));sessions.update(asOf=cutoff,source='KRX 거래일 일봉 및 10/16 NXT OPEN',rawHash=ev['NXT']['rawHash']);sessions['sessions']=sorted(set(sessions['sessions']+[DATE]));dump('research/evaluation/trading-sessions.json',sessions)
spec=importlib.util.spec_from_file_location('evaluation',R/'scripts/evaluate_market_research.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.validate_forecast(f,path,R)
dump('research/evidence/'+DATE+'/sealed.json',{'forecastId':fid,'snapshotId':sid,'cutoff':cutoff,'issuedAt':issued,'article':'https://www.hpmplab.com/articles/market-'+DATE+'.html'})
print(fid,cutoff)
