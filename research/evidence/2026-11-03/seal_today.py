"""최종 시세를 병렬 조회하고 장중 전망과 대시보드를 봉인한다. 한 번만 실행한다."""
import concurrent.futures, datetime, hashlib, html, importlib.util, json, re, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3]; P=Path(__file__).parent; DATE='2026-11-03'; TZ=datetime.timezone(datetime.timedelta(hours=9))
def read(p): return (R/p).read_text(encoding='utf-8-sig')
def write(p,s): (R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v): write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def number(v): return float(str(v).replace(',',''))
urls={'NXT':'https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660','FX':'https://api.stock.naver.com/marketindex/exchange/FX_USDKRW','KOSPI-basic':'https://m.stock.naver.com/api/index/KOSPI/basic','KOSPI':'https://m.stock.naver.com/api/index/KOSPI/price?pageSize=10&page=1','122630':'https://m.stock.naver.com/api/stock/122630/price?pageSize=10&page=1'}
for k in ['NQ','ES','CL','BZ']: urls['yahoo-'+k+'F']=f'https://query1.finance.yahoo.com/v8/finance/chart/{k}=F?range=1d&interval=5m&includePrePost=true'
def fetch(kv):
 k,u=kv;b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();v={'url':u,'fetchedAt':datetime.datetime.now(TZ).isoformat(timespec='seconds'),'rawHash':hashlib.sha256(b).hexdigest(),'data':json.loads(b)};dump('research/evidence/'+DATE+'/final-'+k+'.json',v);return k,v
with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool: ev=dict(pool.map(fetch,urls.items()))
cutoff=max(x['fetchedAt'] for x in ev.values());issued=datetime.datetime.now(TZ).isoformat(timespec='seconds');sid='20261103-'+issued[11:16].replace(':','');fid=DATE+'-'+issued[11:16].replace(':','')+'-same-close'
nxt=ev['NXT']['data']['datas'];fx=ev['FX']['data']['exchangeInfo'];kb=ev['KOSPI-basic']['data'];kp=ev['KOSPI']['data'][0];le=next(x for x in ev['122630']['data'] if x['localTradedAt']=='2026-11-02');kb=dict(kb,fluctuationsRatio=kp['fluctuationsRatio'])
assert kp['localTradedAt']=='2026-11-02' and le['localTradedAt']=='2026-11-02'
nxt=[x for x in nxt if x['localTradedAt'].startswith(DATE) and x['marketStatus']=='OPEN' and x['localTradedAt'] <= cutoff]
fast=f"|KOSPI 전일 종가|{kb['closePrice']} · {kb['fluctuationsRatio']}%|{'2026-11-02T15:30:00+09:00'}|\n|KODEX 레버리지 전일 종가|{le['closePrice']}원 · {le['fluctuationsRatio']}%|조회 {ev['122630']['fetchedAt']}|\n"+'\n'.join(f"|{x['stockName']} NXT|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|" for x in nxt)+f"\n|하나은행 USD/KRW 고시|{fx['closePrice']}원|{fx['localTradedAt']}|"
for k in ['NQF','ESF','CLF','BZF']:
 m=ev['yahoo-'+k]['data']['chart']['result'][0]['meta'];t=datetime.datetime.fromtimestamp(m['regularMarketTime'],TZ).isoformat(timespec='seconds');fast+=f"\n|{k} 최근 거래|{m['regularMarketPrice']:,.2f}|{t}|"
report=read('reports/'+DATE+'.md');assert 'FAST_TABLE' in report;report=report.replace('작성 PREPARED / 데이터 최종 확인 PREPARED',f'작성 {issued} / 데이터 최종 확인 {cutoff}').replace('FAST_TABLE','|항목|최근값|원천 시각|\n|---|---:|---|\n'+fast);write('reports/'+DATE+'.md',report)
rows=[x.split('|')[1:-1] for x in ('|항목|최근값|원천 시각|\n'+fast).splitlines()];table='<div class="article-table-wrap"><table class="article-data-table"><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
s=read('articles/market-'+DATE+'.html');assert 'FAST_TABLE' in s;s=s.replace('FAST_TABLE',table).replace('작성 PREPARED · 데이터 최종 확인 PREPARED',f'작성 {issued} · 데이터 최종 확인 {cutoff}');s=re.sub(r'<time datetime="[^"]+">2026\.11\.03 · 작성 [^<]+',f'<time datetime="{issued}">2026.11.03 · 작성 {issued[11:16]} KST',s)
for prop in ['article:published_time','article:modified_time']:s=re.sub(r'(<meta property="'+prop+r'" content=")[^"]+',lambda m:m[1]+issued,s)
write('articles/market-'+DATE+'.html',s)
for page in ['articles/market-'+DATE+'.html','index.html','articles/index.html','articles/market.html']:
 s=read(page)
 def ld(m):
  j=json.loads(m[1]);
  if j.get('@type')=='Article':j.update(datePublished=issued,dateModified=issued)
  for n in j.get('@graph',[j]):
   for x in n.get('mainEntity',{}).get('itemListElement',[]):
    if x.get('url','').endswith('market-'+DATE+'.html'):x.update(datePublished=issued,dateModified=issued)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,s,flags=re.S)
 def cardtime(m): return re.sub(r'(<time[^>]*datetime=")[^"]+(">)[^<]+',lambda z:z[1]+issued+z[2]+'2026.11.03 · '+issued[11:16]+' KST',m[0]) if 'market-'+DATE+'.html' in m[0] else m[0]
 s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',cardtime,s,flags=re.S);write(page,s)
s=json.loads(read('research/evidence/'+DATE+'/prepared-dashboard.json'));s.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff)
for x in s['markets']:
 if x['id']=='KOSPI':x.update(value=number(kb['closePrice']),changePercent=number(kb['fluctuationsRatio']),open=number(kp['openPrice']),high=number(kp['highPrice']),low=number(kp['lowPrice']),asOf='2026-11-02T15:30:00+09:00')
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=kp if x['id']=='KOSPI' else le;x.update(asOf='2026-11-02T15:30:00+09:00' if x['id']=='KOSPI' else cutoff,points=[{'label':a,'value':number(v[b])} for a,b in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('현재','closePrice')]])
s['checkpoints']=[{'label':x['stockName']+' NXT','value':x['closePrice']+'원 · '+x['fluctuationsRatio']+'%','detail':x['localTradedAt'],'tone':'warning'} for x in nxt]+([{'label':'NXT','value':'당일 유효 가격 없음','detail':'원천 시각·시장 상태 불일치','tone':'neutral'}] if not nxt else [])+[{'label':'하나은행 USD/KRW','value':fx['closePrice']+'원','detail':fx['localTradedAt'],'tone':'warning'}]
assert not (R/'assets/data'/('market-dashboard-'+sid+'.json')).exists();dump('assets/data/market-dashboard-'+sid+'.json',s);dump('assets/data/market-dashboard-latest.json',s)
state=read('STATE.md').replace('작성 PREPARED, 데이터 최종 확인 PREPARED',f'작성 {issued}, 데이터 최종 확인 {cutoff}');state+=f'- 대시보드 assets/data/market-dashboard-{sid}.json, 전망 research/evaluation/forecasts/{fid}.json.\n';write('STATE.md',state)
f=json.loads(read('research/evaluation/forecasts/2026-10-30-0804-same-close.json')); issuedtime=datetime.datetime.fromisoformat(issued).time();bucket='open_0900_0930' if issuedtime<=datetime.time(9,30) else 'morning_0931_1130' if issuedtime<=datetime.time(11,30) else 'afternoon_1131_1500' if issuedtime<=datetime.time(15,0) else 'closing_1501_1529'
f.update(forecastId=fid,reportPath='reports/'+DATE+'.md',reportSha256=hashlib.sha256(report.encode()).hexdigest(),issuedAt=issued,dataCutoffAt=cutoff,marketState='preopen',evaluationBucket='preopen',reference={'price':number(kb['closePrice']),'asOf':'2026-11-02T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':5900,'high':6050,'probability':.20},'base':{'low':5700,'high':5900,'probability':.50},'bear':{'low':5450,'high':5700,'probability':.30}},pathEnvelope={'low':5250,'high':6250,'coverage':.9},posture={'attack':10,'wait':45,'defense':45},drivers=[{'id':'semiconductor','rank':1,'claim':'미국 반도체 추가 매도와 유가 하락','validationMetric':'미국 반도체·한국 지수'},{'id':'memory','rank':2,'claim':'소비자 DRAM 현물·계약가 차별화','validationMetric':'TrendForce·국내 수급'}]);f['target'].update(sessionDate=DATE,previousSessionDate='2026-11-02')
for k,t in f['scenarioTriggers'].items():
 t['observeBy']=DATE+'T15:20:00+09:00'
 if k=='base':t['conditions']=[c for c in t['conditions'] if c['metricId']=='kospi_price']
 for c in t['conditions']:
  if c['metricId']=='kospi_price':c['threshold']=5900 if k=='bull' or c['operator']=='lte' else 5700
f.pop('contentHash');f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();path=R/'research/evaluation/forecasts'/f'{fid}.json';assert not path.exists();dump(str(path.relative_to(R)),f)
sessions=json.loads(read('research/evaluation/trading-sessions.json'));sessions.update(asOf=cutoff,source='KRX 전일 종가와 BLS 공식 달력 대조, 11/3 정상 거래일',rawHash=ev['KOSPI-basic']['rawHash']);sessions['sessions']=sorted(set(sessions['sessions']+[DATE]));dump('research/evaluation/trading-sessions.json',sessions)
spec=importlib.util.spec_from_file_location('evaluation',R/'scripts/evaluate_market_research.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.validate_forecast(f,path,R)
dump('research/evidence/'+DATE+'/sealed.json',{'forecastId':fid,'snapshotId':sid,'cutoff':cutoff,'issuedAt':issued,'article':'https://www.hpmplab.com/articles/market-'+DATE+'.html'})
print(fid,cutoff)
