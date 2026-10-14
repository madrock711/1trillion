"""최종 병렬 조회 뒤 시각·가격·보고서 해시를 함께 봉인한다."""
import concurrent.futures, datetime, hashlib, html, importlib.util, json, re, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
TZ=datetime.timezone(datetime.timedelta(hours=9))
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
urls={'NXT':'https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660','FX':'https://api.stock.naver.com/marketindex/exchange/FX_USDKRW'}
for k in ['NQ','ES','CL','BZ']:urls['yahoo-'+k+'F']=f'https://query1.finance.yahoo.com/v8/finance/chart/{k}=F?range=1d&interval=5m&includePrePost=true'
def fetch(kv):
 k,u=kv;b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();v={'url':u,'fetchedAt':datetime.datetime.now(TZ).isoformat(timespec='seconds'),'rawHash':hashlib.sha256(b).hexdigest(),'data':json.loads(b)};dump('research/evidence/2026-10-15/final-'+k+'.json',v);return k,v
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:ev=dict(pool.map(fetch,urls.items()))
cutoff=max(x['fetchedAt'] for x in ev.values());issued=datetime.datetime.now(TZ).isoformat(timespec='seconds');sid='20261015-'+issued[11:16].replace(':','');fid='2026-10-15-'+issued[11:16].replace(':','')+'-same-close'
nxt=ev['NXT']['data']['datas'];fx=ev['FX']['data']['exchangeInfo']
assert len(nxt)==2 and all(x['marketStatus']=='OPEN' and x['localTradedAt'].startswith('2026-10-15') and x['accumulatedTradingVolume'] not in ['-','0'] for x in nxt)
fast='\n'.join(f"|{x['stockName']} NXT ({x['marketStatus']})|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|" for x in nxt)+f"\n|하나은행 USD/KRW 고시|{fx['closePrice']}원|{fx['localTradedAt']}|"
for k in ['NQF','ESF','CLF','BZF']:
 m=ev['yahoo-'+k]['data']['chart']['result'][0]['meta'];t=datetime.datetime.fromtimestamp(m['regularMarketTime'],TZ).isoformat(timespec='seconds');fast+=f"\n|{k} 최근 거래|{m['regularMarketPrice']:,.2f}|{t}|"
report=read('reports/2026-10-15.md');report=re.sub(r'작성 .*? / 데이터 최종 확인 .*? / 한국 장전\.',f'작성 {issued} / 데이터 최종 확인 {cutoff} / 한국 장전.',report,count=1)
report=re.sub(r'(\|항목\|최근값\|원천 시각\|\n\|---\|---:\|---\|\n).*?(?=\n\n)',lambda m:m[1]+fast,report,flags=re.S)
write('reports/2026-10-15.md',report)
def table(md):
 rows=[l.split('|')[1:-1] for l in md.splitlines() if l.startswith('|')];return '<div class="article-table-wrap"><table class="article-data-table"><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
article=read('articles/market-2026-10-15.html');article=re.sub(r'(<h2>장전 시세</h2>).*?(?=<h2>미국 시간외)',lambda m:m[1]+table('|항목|최근값|원천 시각|\n'+fast),article,flags=re.S)
article=re.sub(r'작성 \d{4}-\d{2}-\d{2}T[^ ]+ · 데이터 최종 확인 [^.]+\.',f'작성 {issued} · 데이터 최종 확인 {cutoff}.',article)
article=re.sub(r'2026\.10\.15 · 작성 \d{2}:\d{2} KST',f'2026.10.15 · 작성 {issued[11:16]} KST',article)
article=article.replace('공개 시각은 아래 발행 기록 기준입니다.','')
article=re.sub(r'(<time datetime=")2026-10-15T[^"]+',lambda m:m[1]+issued,article)
for prop in ['article:published_time','article:modified_time']:
 article=re.sub(r'(<meta property="'+prop+r'" content=")[^"]+',lambda m:m[1]+issued,article)
write('articles/market-2026-10-15.html',article)
for page in ['articles/market-2026-10-15.html','index.html','articles/index.html','articles/market.html']:
 s=read(page)
 def ld(m):
  j=json.loads(m[1])
  if j.get('@type')=='Article':j.update(datePublished=issued,dateModified=issued)
  for n in j.get('@graph',[j]):
   for x in n.get('mainEntity',{}).get('itemListElement',[]):
    if x.get('url','').endswith('market-2026-10-15.html'):x.update(datePublished=issued,dateModified=issued)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,s,flags=re.S)
 if page!='articles/market-2026-10-15.html':
  def card(m):
   if 'market-2026-10-15.html' not in m[0]:return m[0]
   c=re.sub(r'2026-10-15T\d{2}:\d{2}:\d{2}\+09:00',issued,m[0]);return re.sub(r'2026\.10\.15 · \d{2}:\d{2} KST','2026.10.15 · '+issued[11:16]+' KST',c)
  s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,s,flags=re.S)
 write(page,s)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff)
s['checkpoints']=[{'label':x['stockName']+' NXT','value':x['closePrice']+'원 · '+x['fluctuationsRatio']+'%','detail':x['marketStatus']+' · '+x['localTradedAt'],'tone':'warning'} for x in nxt]+[{'label':'하나은행 USD/KRW','value':fx['closePrice']+'원','detail':fx['localTradedAt'],'tone':'warning'}]
dump('assets/data/market-dashboard-'+sid+'.json',s);dump('assets/data/market-dashboard-latest.json',s)
state=read('STATE.md');state=re.sub(r'- 작성 .*?, 데이터 최종 확인 .*?, 한국 장전\.',f'- 작성 {issued}, 데이터 최종 확인 {cutoff}, 한국 장전.',state);state=re.sub(r'market-dashboard-20261015-\d{4}',f'market-dashboard-{sid}',state);state=state.replace('새 계약은 최종 조회 뒤 봉인.',f'최종 계약 research/evaluation/forecasts/{fid}.json.');write('STATE.md',state)
f=json.loads(read('research/evaluation/forecasts/2026-10-14-0815-same-close.json'));f.update(forecastId=fid,reportPath='reports/2026-10-15.md',reportSha256=hashlib.sha256(report.encode()).hexdigest(),issuedAt=issued,dataCutoffAt=cutoff,reference={'price':6008.81,'asOf':'2026-10-14T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':6050,'high':6200,'probability':.15},'base':{'low':5800,'high':6050,'probability':.45},'bear':{'low':5600,'high':5800,'probability':.4}},pathEnvelope={'low':5450,'high':6300,'coverage':.9},posture={'attack':5,'wait':45,'defense':50},drivers=[{'id':'cpi','rank':1,'claim':'CPI 재가속이 AI 할인율·자금조달 부담을 높임','validationMetric':'BLS·미국 반도체·국내 메모리 가격'}, {'id':'domestic-flow','rank':2,'claim':'외국인 매도가 이어진 국내 수급','validationMetric':'외국인 현물·프로그램'}]);f['target'].update(sessionDate='2026-10-15',previousSessionDate='2026-10-14')
for k,t in f['scenarioTriggers'].items():
 t['observeBy']='2026-10-15T15:20:00+09:00'
 for c in t['conditions']:
  if c['metricId']=='kospi_price':c['threshold']=6050 if k=='bull' or c['operator']=='lte' else 5800
f.pop('contentHash');f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
path=R/'research/evaluation/forecasts'/f'{fid}.json';assert not path.exists();dump(str(path.relative_to(R)),f)
sessions=json.loads(read('research/evaluation/trading-sessions.json'));sessions.update(asOf=cutoff,source='KRX 10월 휴장 안내 및 10/15 NXT OPEN',rawHash=ev['NXT']['rawHash']);sessions['sessions']=sorted(set(sessions['sessions']+['2026-10-14','2026-10-15']));dump('research/evaluation/trading-sessions.json',sessions)
spec=importlib.util.spec_from_file_location('evaluation',R/'scripts/evaluate_market_research.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.validate_forecast(f,path,R)
dump('research/evidence/2026-10-15/sealed.json',{'forecastId':fid,'snapshotId':sid,'cutoff':cutoff,'issuedAt':issued,'article':'https://www.hpmplab.com/articles/market-2026-10-15.html'})
print(fid,cutoff,issued)
