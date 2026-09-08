"""2026-09-09 발행본 조립. --seal 전에는 임시 검토본이며 원장을 만들지 않는다."""
import copy,datetime,hashlib,html,json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
E=pathlib.Path(__file__).parent
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def write(p,s): (ROOT/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def base(p):return subprocess.check_output(['git','show','HEAD:'+p],cwd=ROOT).decode('utf-8')
def ev(k):return json.loads((E/(k+'.json')).read_text(encoding='utf-8'))
def num(v):return float(str(v).replace(',',''))
def md(s):
 def inline(t):
  t=html.escape(t)
  t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',t)
  return re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',t)
 out=[]
 for block in s.strip().split('\n\n'):
  lines=block.strip().splitlines()
  if not lines:continue
  if lines[0].startswith('|'):
   rows=[x for x in lines if not re.match(r'^\|[\s:|\-]+\|$',x)]
   out.append('<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+inline(c.strip())+'</th>' for c in rows[0].strip('|').split('|'))+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in r.strip('|').split('|'))+'</tr>' for r in rows[1:])+'</tbody></table></div>')
  elif lines[0].startswith('## '):out.append('<h2>'+inline(lines[0][3:])+'</h2>'+('' if len(lines)==1 else '<p>'+inline(' '.join(lines[1:]))+'</p>'))
  elif lines[0].startswith('- '):out.append('<ul>'+''.join('<li>'+inline(x[2:])+'</li>' for x in lines)+'</ul>')
  else:out.append('<p>'+inline(' '.join(lines))+'</p>')
 return '\n'.join(out)
seal='--seal' in sys.argv
if seal: assert (E/'overnight-notes.md').exists() and not (E/'seal.json').exists(), '이미 봉인했거나 취재 노트 없음'
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).replace(microsecond=0)
stamp=now.isoformat();hm=now.strftime('%H:%M');sid=now.strftime('%Y%m%d-%H%M')
man=read('research/evidence/2026-09-09/manuscript.md');title=man.splitlines()[0].lstrip('# ');body=man.split('\n',1)[1].strip()
summary='미국 반도체 ETF는 올랐지만 Nvidia와 Micron은 하락했습니다. 유가 부담 속에서 국내 메모리주 반등이 지수 전반으로 이어지는지가 관건입니다.'
img='market-2026-09-09-chips-oil-1200x630.webp';oldimg='market-2026-09-08-chips-oil-1200x630.webp'
alt='밝은 서울 새벽의 AI 데이터센터와 메모리 칩, 호박색 유가 파동'
fx=ev('FX')['data']['exchangeInfo'];nxt=ev('NXT')['data'];nx={x['itemCode']:x for x in nxt['datas']}
cutoff=max(ev(k)['fetchedAt'] for k in ['NXT','FX','NQF','ESF'])
nxttime=datetime.datetime.strptime(nxt['time'],'%Y%m%d%H%M%S').strftime('%H:%M:%S')
marketmd='## 장전 가격\n\n|항목|가격·변화|출처 기준 시각|\n|---|---:|---|\n'
for code,label in [('005930','삼성전자 NXT'),('000660','SK하이닉스 NXT')]:
 x=nx[code];marketmd+=f"|{label}|{x['closePrice']}원 · {x['fluctuationsRatio']}%|9월 9일 {nxttime} KST 조회|\n"
marketmd+=f"|달러/원 하나은행 고시|{fx['closePrice']}원|{fx['localTradedAt']}|\n"
for k,label in [('NQF','Nasdaq100 선물'),('ESF','S&P500 선물'),('BZF','브렌트 선물'),('CLF','WTI 선물')]:
 x=ev(k)['data']['chart']['result'][0]['meta'];t=datetime.datetime.fromtimestamp(x['regularMarketTime'],now.tzinfo).isoformat()
 marketmd+=f"|{label}|{x['regularMarketPrice']:,.2f} · {x['regularMarketChangePercent']:+.3f}%|{t} 지연 시세|\n"
marketmd+='\n[NXT](https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660) · [환율](https://api.stock.naver.com/marketindex/exchange/FX_USDKRW) · [Nasdaq100 선물](https://finance.yahoo.com/quote/NQ=F/) · [S&P500 선물](https://finance.yahoo.com/quote/ES=F/) · [브렌트](https://finance.yahoo.com/quote/BZ=F/) · [WTI](https://finance.yahoo.com/quote/CL=F/)\n\nNXT는 정규장과 별도 시장이다. 선물은 지연 시세이며, 등락률은 출처가 제공한 각 계약의 비교 기준을 따른다.\n'
body=body+'\n\n'+marketmd
chartbody='\n'.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{kind}_2026-09-09.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {label}"><figcaption>9월 8일 10년-2년 +0.41%p · 10년-3개월 +0.86%p. FRED.</figcaption></figure>' for kind,label in [('90d','최근 90일'),('long_term','최근 2년')])
old=base('articles/market-2026-09-08.html');oldtitle=re.search(r'<h1>(.*?)</h1>',old).group(1);oldsummary=re.search(r'<p class="article-dek">(.*?)</p>',old).group(1)
article=old.split('<article class="editorial-article reading-article">')[0]
article=article.replace(oldtitle,title).replace(oldsummary,summary).replace('2026-09-08T08:14:33+09:00',stamp).replace('market-2026-09-08.html','market-2026-09-09.html').replace(oldimg,img).replace('아침빛을 받는 메모리 칩 스택과 금빛 유리 문턱',alt)
article+=f'<article class="editorial-article reading-article"><header class="article-hero"><a class="article-category-badge" href="market.html?view=analysis#research-archive">시황분석</a><h1>{title}</h1><p class="article-dek">{summary}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{stamp}">2026.09.09 · {hm} KST</time><span>개장 전 브리핑</span></div><p class="article-disclosure">작성 {hm} KST · 데이터 최종 확인 {cutoff}. 국내 정규장 일봉은 9월 8일, 미국 정규장·시간외는 9월 8일 기준이다. 장전 가격의 개별 시각은 표에 표시했다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{img}" width="1200" height="630" decoding="async" fetchpriority="high" alt="{alt}"></figure></header><div class="article-body" id="article-body">'+md(body)+chartbody
article+=old[old.index('</div></article></main>'):]
write('articles/market-2026-09-09.html',article)
report=f'# {title}\n\n- 작성: {stamp}; 데이터 최종 확인: {cutoff}; 한국 개장 전.\n- 수치는 출처 관측값, 시나리오·확률·대응점수는 조건부 분석 가정이다.\n- 전일 6954.52 종가는 직전 장전판 기본 범위 안. 상세 정산은 evaluation 원장을 따른다.\n- 신규 변수: 미국 반도체 ETF와 개별 종목의 분화, Qualcomm·Amazon 협업, 99달러대 브렌트. 한국장 반납 흐름과 EWY 후행 반응은 새 충격으로 중복 적용하지 않는다.\n- 취재 원문과 미확인 항목: research/evidence/2026-09-09/overnight-notes.md. 전일18:59 마감후 수급·시장폭은 보존했으나 15:30 수급 원문 앵커는 결측이다.\n\n'+body+'\n\n## 미국 가격 세부·취재 근거\n\n'+(read('research/evidence/2026-09-09/overnight-notes.md') if (E/'overnight-notes.md').exists() else '취재 노트 수신 전 내부 초안')
report+='\n\n![금리차 90일](../charts/us_yield_spreads_90d_2026-09-09.png)\n\n![금리차 2년](../charts/us_yield_spreads_long_term_2026-09-09.png)\n'
write('reports/2026-09-09.md',report)
dash=json.loads(base('assets/data/market-dashboard-latest.json'))
dash.update(snapshotId=sid,generatedAt=stamp,asOf=cutoff,asOfDisplay=cutoff,marketState='한국 개장 전',sourceLabel='국내 9월 8일 정규장 종가 · 미국 9월 8일 정규장 · 장전 가격은 각 출처 시각',latestArticle={'title':title,'href':'market-2026-09-09.html'},headline='미국 반도체 강세가 메모리주 전반으로 번지는지 살필 때입니다.',summary=summary)
for m in dash['markets']:
 x=next(r for r in ev(m['id'])['data'] if r['localTradedAt']=='2026-09-08')
 m.update(value=num(x['closePrice']),changePercent=num(x['fluctuationsRatio']),open=num(x['openPrice']),high=num(x['highPrice']),low=num(x['lowPrice']),previousClose=num(x['closePrice'])-num(x['compareToPreviousClosePrice']),asOf='2026-09-08T15:30:00+09:00',asOfLabel='9월 8일 정규장 종가',stateLabel='전일 종가',flows=[])
 if m['id']=='KOSPI':m['asOfLabel']='9월 8일 종가 · 수급 18:59';m['breadth']={'advance':231,'flat':45,'decline':634};m['flows']=[{'label':l,'value':v,'unit':'억원'} for l,v in [('개인',-30329),('외국인',6316),('기관',6427)]]
dash['stance']={'label':'관망 우세','attack':30,'wait':50,'defense':20,'note':'6,900 지지와 7,100 돌파를 외국인·프로그램 수급과 함께 봅니다.'}
dash['checkpoints']=[{'label':'미국 반도체','value':'SOXX +1.64% · Micron -1.61%','detail':'9월 8일 정규장 종가','tone':'info'},{'label':'원/달러','value':fx['closePrice']+'원','detail':fx['localTradedAt']+' 고시','tone':'info'},{'label':'메모리 NXT','value':f"삼성 {nx['005930']['fluctuationsRatio']}% · 하이닉스 {nx['000660']['fluctuationsRatio']}%",'detail':nxttime+' KST 조회','tone':'info'},{'label':'브렌트 선물','value':str(ev('BZF')['data']['chart']['result'][0]['meta']['regularMarketPrice'])+'달러','detail':'지연 시세 · 개별 시각은 기사 표','tone':'warning'}]
dash['changes']=[{'label':'KOSPI','before':'6,995.39','after':'6,954.52','meaning':'9월 8일 장중 7,171.52에서 상승분을 반납했습니다.'},{'label':'반도체 주가','before':'미국 9월 7일 휴장','after':'SOXX +1.64% · Micron -1.61%','meaning':'9월 8일 ETF와 메모리 종목의 방향이 갈렸습니다.'}]
dash['factors']=[{'label':'유가 부담','metric':'브렌트 99달러대','detail':'장전 지연 시세 · 수입 비용과 물가에 부담을 줍니다.','tone':'warning'},{'label':'미국 반도체 분화','metric':'AMD +5.90% · Micron -1.61%','detail':'9월 8일 정규장 · AI 수요 기대가 모든 종목으로 번지지는 않았습니다.','tone':'info'},{'label':'국내 시장 폭','metric':'상승 231 · 하락 634','detail':'9월 8일 마감 자료 · 지수 반등의 확산이 필요합니다.','tone':'warning'}]
dash['flows']={'program':{'arbitrage':-444,'nonArbitrage':1252,'total':808,'unit':'억원'},'kospi200FuturesForeign':None,'futuresUnit':'계약','futuresAsOfLabel':'9월 8일 마감 후 자료'}
dash['memory']=[{'label':'DDR5 16Gb · 9/8 19:10 KST','value':'$54.333','change':'+0.06%'},{'label':'DDR4 16Gb · 9/8 19:10 KST','value':'$91.750','change':'-1.61%'},{'label':'DDR4 8Gb · 9/8 19:10 KST','value':'$45.364','change':'+0.02%'}]
dash['scenarios']=[{'id':'base','label':'기본 · 50%','range':'KOSPI 6,900~7,100','summary':'급등 뒤 소화 과정을 거칩니다.','conditions':['6,900 이상','7,100 이하','외국인 현물 순매매 0 이상'],'invalidation':'범위 이탈 또는 외국인 순매도'},{'id':'bull','label':'강세 · 30%','range':'KOSPI 7,100 초과~7,300','summary':'국내 매수가 추가 상승을 이끕니다.','conditions':['7,100 초과','외국인 현물 순매수','프로그램 순매수'],'invalidation':'7,100 이하 또는 어느 한 수급이 순매수 중단'},{'id':'bear','label':'약세 · 20%','range':'KOSPI 6,650~6,900 미만','summary':'반도체와 국내 수급이 함께 밀립니다.','conditions':['6,900 미만','외국인 현물 순매도','프로그램 순매도'],'invalidation':'6,900 회복 또는 어느 한 수급이 순매도 중단'}]
dash['strategyLevels']=[{'asset':'KOSPI','support':'6,900 / 6,650','pivot':'7,100','resistance':'7,300'},{'asset':'KODEX 레버리지','support':'112,000원','pivot':'115,000원','resistance':'120,000원'}]
dash['events']=[{'time':'9월 9일 10:30 KST','name':'중국 CPI·PPI','path':'중국 수요와 생산자 물가'},{'time':'9월 10일·11일 21:30 KST','name':'미국 PPI·CPI','path':'금리 기대와 물가'},{'time':'9월 17일 03:00 KST','name':'FOMC·경제전망','path':'정책금리와 전망'}]
dash['checklist']=[{'id':'support','label':'KOSPI 6,900을 지켰다'},{'id':'breakout','label':'KOSPI 7,100을 넘었다'},{'id':'flow','label':'외국인 현물·프로그램이 함께 순매수다'}]
dash['technical']['note']='9월 8일 확정 일봉과 9월 9일 분석 기준선입니다.'
for inst in dash['technical']['instruments']:
 key='122630' if inst['id']=='KODEX' else inst['id'];x=next(r for r in ev(key)['data'] if r['localTradedAt']=='2026-09-08');lev=[112000,115000,120000] if key=='122630' else [6900,7100,7300]
 inst.update(asOf='2026-09-08T15:30:00+09:00',asOfLabel='9월 8일 정규장 종가',points=[{'label':l,'value':num(x[k])} for l,k in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]],levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],lev)],interpretation=f'1차 지지 {lev[0]:,} · 반등 기준 {lev[1]:,} · 저항 {lev[2]:,}')
dash['sources']=[{'label':k,'href':u} for k,u in [('TrendForce','https://www.trendforce.com/price/dram/lpddr_spot'),('NYSE','https://www.nyse.com/trade/hours-calendars'),('BLS','https://www.bls.gov/schedule/2026/'),('KOSPI',ev('KOSPI')['url']),('NXT',ev('NXT')['url']),('환율',ev('FX')['url'])]]
dump('assets/data/market-dashboard-latest.json',dash)
if seal:dump('assets/data/market-dashboard-'+sid+'.json',dash)
for path,cls in [('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')]:
 s=base(path);pattern=r'<article class="'+re.escape(cls)+r'"[^>]*>.*?</article>';card=re.search(pattern,s,re.S).group(0)
 new=card.replace(oldtitle,title).replace(oldsummary,summary).replace('2026-09-08T08:14:33+09:00',stamp).replace('2026.09.08 · 08:14 KST','2026.09.09 · '+hm+' KST').replace('market-2026-09-08.html','market-2026-09-09.html').replace(oldimg,img).replace('9월 8일','9월 9일')
 s=s.replace(card,new+'\n'+card.replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"',''),1)
 if path=='articles/market.html':
  s=re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+',r'\g<1>market-2026-09-09.html',s).replace('최신순 · 30편','최신순 · 31편')
  s=s.replace('현물 반등과 지수 헤지의 공존','프로그램과 선물 수급').replace('주가보다 강한 공급 부족','품목별로 엇갈린 DRAM 가격')
  count=len(re.findall(r'<article class="market-article-item"',s))
  s=re.sub(r'(일일시황 <span class="article-category-count">)\d+',lambda m:m.group(1)+str(count),s)
  s=re.sub(r'최신순 · \d+편',f'최신순 · {count}편',s)
 def schema(m):
  obj=json.loads(m.group(1))
  def walk(x):
   if isinstance(x,dict):
    if x.get('@type')=='ItemList' and x.get('itemListElement'):
     arr=x['itemListElement'];first=json.loads(json.dumps(arr[0],ensure_ascii=False).replace(oldtitle,title).replace(oldsummary,summary).replace('2026-09-08T08:14:33+09:00',stamp).replace('market-2026-09-08.html','market-2026-09-09.html').replace(oldimg,img));arr.insert(0,first)
     for i,a in enumerate(arr):a['position']=i+1
     x['numberOfItems']=len(arr)
    for k,v in x.items():
     if k=='dateModified' and v=='2026-09-08T08:14:33+09:00':x[k]=stamp
     elif k!='itemListElement':walk(v)
   elif isinstance(x,list):
    for a in x:walk(a)
  walk(obj);return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',schema,s,flags=re.S)
 s=re.sub(r'(<meta[^>]+content=")[^"]*'+re.escape(oldimg),lambda m:m.group(0).replace(oldimg,img),s)
 counts={c:len(re.findall(r'<article[^>]+data-category="'+c+'"',s)) for c in ['market','health','essay']}
 counts['all']=sum(counts.values())
 for c,v in counts.items():s=re.sub(r'(data-category-count="'+c+r'">)\d+',lambda m:m.group(1)+str(v),s)
 write(path,s)
s=base('sitemap.xml').replace('</urlset>','<url><loc>https://www.hpmplab.com/articles/market-2026-09-09.html</loc><lastmod>2026-09-09</lastmod></url>\n</urlset>')
for loc in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:
 s=re.sub(r'(<loc>'+re.escape(loc)+r'</loc>\s*<lastmod>)[^<]+',r'\g<1>2026-09-09',s)
write('sitemap.xml',s)
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 {stamp}, 데이터 최종 확인 {cutoff}, 한국 개장 전.\n- 직전 KOSPI 6,954.52(-0.58%), KODEX 112,150원(-0.79%), 9월 8일 정규장 종가.\n- NXT 삼성 {nx["005930"]["closePrice"]}원({nx["005930"]["fluctuationsRatio"]}%), 하이닉스 {nx["000660"]["closePrice"]}원({nx["000660"]["fluctuationsRatio"]}%), {nxttime} KST 조회. 원/달러 {fx["closePrice"]}원({fx["localTradedAt"]}).\n- 핵심: Qualcomm·Amazon 조건부 협업, 미국 반도체 ETF 상승과 NVDA·MU 하락의 분화, 유가99달러대 부담. EWY 후행 반영을 중복 가산하지 않는다.\n- 수급: 전일18:59 외국인+6316·기관+6427·개인-30329억원, 프로그램+808억원. 정산과 앵커 결측은 actuals/2026-09-08.json 및 settlement-note 참조.\n- 대응 공격30/관망50/방어20. 기본6900~7100(50%),강세7100초과~7300(30%),약세6650~6900미만(20%),장중6600~7350(90%). KODEX112000/115000/120000.\n- 다음: 오늘10:30중국CPI·PPI,9/10PPI·9/11CPI21:30,9/15~16ET FOMC.\n- reports/2026-09-09.md; research/evidence/2026-09-09/overnight-notes.md; charts/us_yield_spreads_90d_2026-09-09.png 및 long_term.\n- assets/data/market-dashboard-{sid}.json; 최신 포인터 market-dashboard-latest.json.\n- 평가 research/evaluation/generated/latest.md, 직전 정산 outcomes/2026-09-08-0814-same-close.json.\n')
if seal:
 forecast=json.loads(base('research/evaluation/forecasts/2026-09-08-0814-same-close.json'));fid='2026-09-09-'+now.strftime('%H%M')+'-same-close'
 forecast.update(forecastId=fid,reportPath='reports/2026-09-09.md',reportSha256=hashlib.sha256((ROOT/'reports/2026-09-09.md').read_bytes()).hexdigest(),issuedAt=stamp,dataCutoffAt=cutoff,marketState='preopen',evaluationBucket='preopen',reference={'price':6954.52,'asOf':'2026-09-08T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':7100,'high':7300,'probability':.30},'base':{'low':6900,'high':7100,'probability':.5},'bear':{'low':6650,'high':6900,'probability':.20}},pathEnvelope={'low':6600,'high':7350,'coverage':.9},posture={'attack':30,'wait':50,'defense':20})
 forecast['target'].update(sessionDate='2026-09-09',previousSessionDate='2026-09-08')
 # base-foreign already exists in previous contract
 forecast['drivers']=[{'id':'domestic-demand','rank':1,'claim':'미국 반도체 ETF 상승이 국내 메모리와 시장 폭 개선으로 연결되어야 한다.','validationMetric':'KOSPI 가격·외국인·프로그램 수급'},{'id':'oil-risk','rank':2,'claim':'유가 상승은 물가와 지수 상단에 부담을 준다.','validationMetric':'브렌트·원화·KOSPI 종가'},{'id':'memory-differentiation','rank':3,'claim':'DRAM 품목별 가격은 실적 기대를 지지하되 주식 매수와 다르다.','validationMetric':'메모리 현물·삼성전자·SK하이닉스 가격'}]
 for scen,rule in forecast['scenarioTriggers'].items():
  rule['observeBy']='2026-09-09T15:20:00+09:00'
  for c in rule['conditions']:
   if c['metricId']=='kospi_price':c['threshold']=7100 if c['id'] in ['bull-price','base-cap'] else 6900;c['description']=f"{c['metricId']} {c['operator']} {c['threshold']}"
 forecast.pop('contentHash',None)
 forecast['contentHash']=hashlib.sha256(json.dumps(forecast,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 dump('research/evaluation/forecasts/'+fid+'.json',forecast)
 dump('research/evidence/2026-09-09/seal.json',{'forecastId':fid,'issuedAt':stamp,'dataCutoffAt':cutoff,'snapshotId':sid,'articleTitle':title,'files':['articles/market-2026-09-09.html','assets/data/market-dashboard-latest.json','assets/data/market-dashboard-'+sid+'.json','assets/images/articles/'+img,'charts/us_yield_spreads_90d_2026-09-09.png','charts/us_yield_spreads_long_term_2026-09-09.png','articles/index.html','articles/market.html','index.html']})
print('SEALED' if seal else 'DRAFT',stamp,cutoff,title)
