"""발행 전 정정판: 새 조회와 새 전망 ID를 사용한다."""
import concurrent.futures, datetime, hashlib, html, importlib.util, json, re, time, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3];DATE='2026-11-02';TZ=datetime.timezone(datetime.timedelta(hours=9))
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def n(v):return float(str(v).replace(',',''))
prev=json.loads(read('research/evidence/'+DATE+'/sealed.json'));oldid=prev['forecastId']
urls={'NXT':'https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660','FX':'https://api.stock.naver.com/marketindex/exchange/FX_USDKRW','KOSPI-basic':'https://m.stock.naver.com/api/index/KOSPI/basic','KOSPI':'https://m.stock.naver.com/api/index/KOSPI/price?pageSize=10&page=1','122630':'https://m.stock.naver.com/api/stock/122630/price?pageSize=10&page=1'}
for k in ['NQ','ES','CL','BZ']:urls['yahoo-'+k+'F']=f'https://query1.finance.yahoo.com/v8/finance/chart/{k}=F?range=1d&interval=5m&includePrePost=true'
def fetch(kv):
 k,u=kv;b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();return k,{'url':u,'fetchedAt':datetime.datetime.now(TZ).isoformat(timespec='microseconds'),'rawHash':hashlib.sha256(b).hexdigest(),'data':json.loads(b)}
with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:ev=dict(pool.map(fetch,urls.items()))
nxt=ev['NXT']['data']['datas'];fx=ev['FX']['data']['exchangeInfo'];kb=ev['KOSPI-basic']['data'];kp=ev['KOSPI']['data'][0];le=ev['122630']['data'][0]
assert len(nxt)==2 and all(x['marketStatus']=='OPEN' and x['localTradedAt'].startswith(DATE) for x in nxt)
assert kb['marketStatus']=='OPEN' and kb['localTradedAt'].startswith(DATE) and kp['localTradedAt']==DATE and le['localTradedAt']==DATE and n(kb['closePrice'])==n(kp['closePrice'])
fetched_nxt=datetime.datetime.fromisoformat(ev['NXT']['fetchedAt']);nxt_valid=all(datetime.datetime.fromisoformat(x['localTradedAt'])<=fetched_nxt for x in nxt)
now=datetime.datetime.now(TZ);cutoff=now.isoformat(timespec='seconds');issued=now.isoformat(timespec='seconds')
sid='20261102-'+issued[11:16].replace(':','');fid=DATE+'-'+issued[11:16].replace(':','')+'-same-close';assert fid!=oldid
for k,v in ev.items():dump('research/evidence/'+DATE+'/correction-'+k+'.json',v)
fast=f"|KOSPI|{kb['closePrice']} · {kb['fluctuationsRatio']}%|{kb['localTradedAt']}|\n|KODEX 레버리지|{le['closePrice']}원 · {le['fluctuationsRatio']}%|조회 {ev['122630']['fetchedAt']}|"+(''.join(f"\n|{x['stockName']} NXT|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|" for x in nxt) if nxt_valid else '')+f"\n|하나은행 USD/KRW 고시|{fx['closePrice']}원|{fx['localTradedAt']}|"
for k in ['NQF','ESF','CLF','BZF']:
 m=ev['yahoo-'+k]['data']['chart']['result'][0]['meta'];t=datetime.datetime.fromtimestamp(m['regularMarketTime'],TZ).isoformat(timespec='seconds');fast+=f"\n|{k} 최근 거래|{m['regularMarketPrice']:,.2f}|{t}|"
report=read('reports/'+DATE+'.md');report=re.sub(r'작성 .*? / 데이터 최종 확인 .*?\n',f'작성 {issued} / 데이터 최종 확인 {cutoff}\n',report,count=1);report=re.sub(r'\n# 2026-11-02 장중 취재 노트.*?\n## 미국 10월 30일 정규장', '\n## 밤사이 시장을 지배한 이슈\nIntel 전망 부진과 공장 사고, 미국 반도체 동반 하락, 소비자 DRAM 현물과 계약가격의 차별화가 중심이다. Intel 전망의 일부는 전일 한국장에 이미 반영됐다. 상세 취재 근거는 research/notes/2026-11-02.md에 보관한다.\n\n## 미국 10월 30일 정규장',report,flags=re.S);report=re.sub(r'(## 발행 직전 조회\n).*?(\n## 조건부 전망)',lambda m:m[1]+'|항목|최근값|원천 시각|\n|---|---:|---|\n'+fast+('' if nxt_valid else '\n\nNXT 원천 표시 시각이 수집 시각보다 늦어 가격을 제외했다.')+m[2],report,flags=re.S)
rows=[x.split('|')[1:-1] for x in ('|항목|최근값|원천 시각|\n'+fast).splitlines()];table='<div class="article-table-wrap"><table class="article-data-table"><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
article=read('articles/market-'+DATE+'.html');article=re.sub(r'(<h2>장중 시세</h2>).*?(<h2>미국 시간외 최근 거래</h2>)',lambda m:m[1]+table+m[2],article,flags=re.S);article=re.sub(r'작성 2026-11-02T[^ ]+ · 데이터 최종 확인 2026-11-02T[^. ]+',f'작성 {issued} · 데이터 최종 확인 {cutoff}',article);article=re.sub(r'<time datetime="[^"]+">2026\.11\.02 · 작성 [^<]+',f'<time datetime="{issued}">2026.11.02 · 작성 {issued[11:16]} KST',article)
for prop in ['article:published_time','article:modified_time']:article=re.sub(r'(<meta property="'+prop+r'" content=")[^"]+',lambda m:m[1]+issued,article)
s=json.loads(read('assets/data/market-dashboard-'+prev['snapshotId']+'.json'));s.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff)
for x in s['markets']:
 if x['id']=='KOSPI':x.update(value=n(kb['closePrice']),changePercent=n(kb['fluctuationsRatio']),open=n(kp['openPrice']),high=n(kp['highPrice']),low=n(kp['lowPrice']),asOf=kb['localTradedAt'])
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=kp if x['id']=='KOSPI' else le;x.update(asOf=kb['localTradedAt'] if x['id']=='KOSPI' else cutoff,points=[{'label':a,'value':n(v[b])} for a,b in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('현재','closePrice')]])
s['checkpoints']=([{'label':x['stockName']+' NXT','value':x['closePrice']+'원 · '+x['fluctuationsRatio']+'%','detail':x['localTradedAt'],'tone':'warning'} for x in nxt] if nxt_valid else [])+[{'label':'하나은행 USD/KRW','value':fx['closePrice']+'원','detail':fx['localTradedAt'],'tone':'warning'}]
report_path='reports/'+DATE+'-'+issued[11:16].replace(':','')+'.md'
f=json.loads(read('research/evaluation/forecasts/'+oldid+'.json'));f.update(forecastId=fid,supersedes=oldid,reportPath=report_path,reportSha256=hashlib.sha256(report.encode()).hexdigest(),issuedAt=issued,dataCutoffAt=cutoff,reference={'price':n(kb['closePrice']),'asOf':kb['localTradedAt'],'kind':'live'});f.pop('contentHash');f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
path=R/'research/evaluation/forecasts'/f'{fid}.json';assert not path.exists() and not (R/'assets/data'/('market-dashboard-'+sid+'.json')).exists()
spec=importlib.util.spec_from_file_location('evaluation',R/'scripts/evaluate_market_research.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.validate_forecast(f,path)
write(report_path,report);write('articles/market-'+DATE+'.html',article);dump('assets/data/market-dashboard-'+sid+'.json',s);dump('assets/data/market-dashboard-latest.json',s);dump('research/evaluation/forecasts/'+fid+'.json',f);m.validate_forecast(f,path,R)
for page in ['articles/market-'+DATE+'.html','index.html','articles/index.html','articles/market.html']:
 text=read(page)
 def ld(m):
  j=json.loads(m[1]);
  if j.get('@type')=='Article':j.update(datePublished=issued,dateModified=issued)
  for node in j.get('@graph',[j]):
   for x in node.get('mainEntity',{}).get('itemListElement',[]):
    if x.get('url','').endswith('market-'+DATE+'.html'):x.update(datePublished=issued,dateModified=issued)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 text=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,text,flags=re.S)
 def card(m):return re.sub(r'(<time[^>]*datetime=")[^"]+(">)[^<]+',lambda z:z[1]+issued+z[2]+'2026.11.02 · '+issued[11:16]+' KST',m[0]) if 'market-'+DATE+'.html' in m[0] else m[0]
 text=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,text,flags=re.S);write(page,text)
state=read('STATE.md').replace(prev['issuedAt'],issued).replace(prev['cutoff'],cutoff).replace(prev['snapshotId'],sid).replace(oldid,fid).replace('reports/'+DATE+'.md',report_path);write('STATE.md',state)
dump('research/evidence/'+DATE+'/sealed.json',{'forecastId':fid,'snapshotId':sid,'cutoff':cutoff,'issuedAt':issued,'article':prev['article'],'supersedes':oldid});print(fid,cutoff)
