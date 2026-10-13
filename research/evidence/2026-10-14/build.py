import datetime, hashlib, html, json, re
from pathlib import Path
R=Path(__file__).resolve().parents[3]
P=Path(__file__).parent
DATE='2026-10-14'
TITLE='중국 메모리 경쟁 우려 뒤 급락…오늘은 6,000선과 CPI'
SUMMARY='국내 급락 뒤 미국 메모리주는 더 밀렸지만 Nvidia·AMD는 반등했습니다. KOSPI 6,000선 방어와 국내 메모리주 반등의 지속성을 봐야 합니다.'
IMAGE='market-2026-10-14-memory-competition-cpi-1200x630.png'
ALT='밝은 하늘빛 배경에서 마주한 두 메모리 칩과 물가 발표를 기다리는 금빛 시계'
URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p): return (R/p).read_text(encoding='utf-8')
def write(p,s): (R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,s): write(p,json.dumps(s,ensure_ascii=False,indent=2)+'\n')
def ev(k): return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def num(s): return float(str(s).replace(',',''))
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
CUTOFF=max(ev(k)['fetchedAt'] for k in ['NXT','FX','yahoo-NQF','yahoo-ESF'])
SID='20261014-'+NOW[11:16].replace(':','')
FID=DATE+'-'+NOW[11:16].replace(':','')+'-same-close'
prev={k:next(x for x in ev(k)['data'] if x['localTradedAt']=='2026-10-13') for k in ['KOSPI','122630','005930','000660']}
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0]; q=d['indicators']['quote'][0]; return q['close'][-1],(q['close'][-1]/q['close'][-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
nxt=ev('NXT')['data']['datas']; fx=ev('FX')['data']['exchangeInfo']
fast='\n'.join(f"|{x['stockName']} NXT|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|" for x in nxt)
fast+=f"\n|하나은행 USD/KRW|{fx['closePrice']}원|{fx['localTradedAt']}|"
for k in ['NQF','ESF','CLF','BZF']:
 m=ev('yahoo-'+k)['data']['chart']['result'][0]['meta']; t=datetime.datetime.fromtimestamp(m['regularMarketTime'],datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds'); fast+=f"\n|{k} 최근 거래|{m['regularMarketPrice']:,.2f}|{t}|"
body='''<p>중국 메모리 경쟁에 대한 우려가 국내 반도체주를 크게 밀었다. 10월 13일 KOSPI는 6,035.35로 5.46% 하락했고 KODEX 레버리지는 81,965원으로 12.45% 내렸다. 미국에서도 Micron이 3.62% 더 하락했지만 Nvidia는 0.97%, AMD는 1.90% 반등했다. 반도체 안에서도 가격 흐름이 갈렸다.</p>
<h2>공급 경쟁의 우려와 현재 가격은 다르다</h2><p>Reuters는 CXMT의 메모리 밀도를 높이는 기술 진전 보도와 AI 투자 수익성에 대한 경계가 매도 압력을 키웠다고 전했다. 이 재료는 전일 서울장에서 이미 큰 낙폭으로 반영됐다. 미국 메모리주의 후행 하락을 국내에 같은 크기의 새 충격으로 더할 이유는 없다.</p>
<p>실물 가격은 아직 다른 방향이다. TrendForce의 10월 13일 DDR5 16Gb 현물 평균은 59.90달러로 0.79%, DDR4 16Gb는 83.858달러로 0.06% 올랐다. 새 기술이 장기 공급 경쟁을 바꿀 수 있어도 오늘 서버용 메모리 공급이 즉시 늘어난 것은 아니다. 주가는 미래 경쟁과 높은 기대치를 먼저 조정하고 있다.</p>
<h2>6,000선을 지키는 반등인가</h2><p>장전 국내 메모리주의 반등이 정규장까지 이어지는지가 첫 관문이다. KOSPI가 6,000선을 지키고 외국인·프로그램 매도가 둔화하면 전일 급락을 소화하는 구간으로 본다. 6,200선을 넘는 반등은 두 수급이 함께 순매수로 바뀌어야 힘을 얻는다.</p>
<p>기본 종가 범위는 5,900~6,200(45%)이다. 6,200 초과~6,350의 강세 가능성은 20%, 5,750~5,900 미만의 약세 가능성은 35%로 둔다. 5,900 아래에서 외국인과 프로그램이 동반 매도하면 반등 기대를 낮춘다. KODEX 레버리지는 전일 저가 78,780원, 종가 81,965원, 고가 88,340원을 각각 1차 지지·반등 기준·저항으로 본다.</p>
<h2>오늘 밤 물가가 다음 장의 할인율을 바꾼다</h2><p>미국 9월 CPI는 오늘 21:30 KST에 발표된다. 국내 정규장 뒤의 일정이므로 오늘은 결과보다 발표를 앞둔 포지션 조정이 영향을 준다. 최신 FRED 개별 금리 관측에서 10년물은 5.24%다. 유가와 물가가 높은 장기금리를 더 밀어 올리면 메모리 현물의 강세만으로 주가 부담을 상쇄하기 어렵다.</p>
<p>오전 반등 폭보다 09:30 이후 외국인 현물·프로그램의 방향과 삼성전자·SK하이닉스의 전일 종가 회복 여부를 함께 봐야 한다.</p>'''
sources=[('KOSPI·국내 종가','https://m.stock.naver.com/domestic/index/KOSPI/total'),('미국 ETF·종목 정규장','https://finance.yahoo.com/quote/SOXX/'),('중국 메모리 경쟁과 AI 투자 경계','https://www.marketscreener.com/news/us-chip-stocks-extend-slide-as-china-memory-report-ai-spending-jitters-hit-sector-ce785dddd18ff02c'),('메모리 현물','https://www.trendforce.com/price/dram/dram_spot'),('CPI·PPI 일정','https://www.bls.gov/schedule/2026/10_sched.htm'),('미국 금리','https://fred.stlouisfed.org/series/T10Y2Y')]
report=f'''# {DATE} KOSPI·KODEX 일일 리서치

작성 {NOW} / 데이터 최종 확인 {CUTOFF} / 한국 장전. 시장별 원천 시각은 아래 표에 따름.

## 핵심 결론

{SUMMARY} 대응 점수 공격 10·관망 50·방어 40. 기본 5,900~6,200(45%), 강세 6,200 초과~6,350(20%), 약세 5,750~5,900 미만(35%). 장중 90% 포락 5,650~6,450. 조건부 추론이며 확정 시세와 구분한다.

## 밤사이 시장을 지배한 이슈

Reuters는 CXMT 기술 진전 보도와 AI 투자 수익성 경계를 반도체 매도 배경으로 전했다. 10월 13일 국내 급락에 이미 반영된 재료다. 미국에서 MU -3.62%와 NVDA +0.97%·AMD +1.90%의 차별화가 새 관측이다. CXMT 4F² 양산·수율·고객 검증은 미확인이고 새 공급량으로 환산하지 않는다. CXMT 공식 G5 양산 발표는 9월 20일로 당일 신규 발표가 아니다.

## 전일 대비 바뀐 변수와 유지 변수

KOSPI는 6,384.24에서 6,035.35(-5.46%)로 하락했다. 전일 전망 하단 6,100도 이탈해 낙폭을 과소평가했다. 메모리 현물 강세를 당일 수급 회복으로 연결하지 않아야 한다. 미국 비메모리 반등은 새 변수이나 국내 정규장 반전은 아직 조건부다.

## 한국시장·KODEX 대시보드

|항목|10월 13일 종가|등락|
|---|---:|---:|
'''+ '\n'.join(f"|{k}|{v['closePrice']}|{v['fluctuationsRatio']}%|" for k,v in prev.items())+f'''

## 메모리 반도체 수급

TrendForce 10월 13일 18:10 GMT+8: DDR5 16Gb 59.90달러(+0.79%), DDR4 16Gb 83.858달러(+0.06%). 미래 공급 경쟁과 현재 현물 수급은 분리한다. HBM·eSSD·NAND 최신 계약 세부값과 고객별 공급량은 미확인으로 남긴다. 오래된 CAPEX 수치를 오늘 발표처럼 쓰지 않는다.

## 미국 반도체·AI

|ETF·종목|10월 13일 정규장 종가|전일 대비|
|---|---:|---:|
{ustable}

Yahoo 직접 차트의 마지막 두 정규장 일봉 기준. 시간외 별도 확정 시세는 미확인. Reuters 장중 등락률을 종가로 혼용하지 않는다. Broadcom의 OCP 네트워크 제품 발표는 10월 8일 원문이고, 새로운 매출·공급 계약으로 해석하지 않는다. Citi 3분기 순이익 52억달러는 SEC 원문 확인. 빅테크 신규 실적·대규모 강제청산·새 규제·확정 증자는 핵심 원문 미확보이며 시장 원인으로 채택하지 않는다.

## 달러/원·국내 수급·시장 구조

|항목|최근값|원천 시각|
|---|---:|---|
{fast}

NXT 등락은 NXT 원천의 비교 기준이며 KRX 종가 대비와 다를 수 있다. 전일 KRX 삼성전자 234,000원, SK하이닉스 1,456,000원과 별도 비교한다. 하나은행 값은 고시환율이며 역외 현물과 구분한다. 장전 0 수급·시장 폭은 미개시 값으로 제외. 전일 확정 현물·선물·프로그램·시장 폭 원문은 미확보, 0으로 추정하지 않는다.

## 경제 캘린더

10월 14일 21:30 KST(08:30 ET) 미국 9월 CPI, 15일 21:30 KST PPI. 발표 결과는 오늘 한국 정규장 뒤에 반영된다.

## 미 국채와 장단기 금리차

FRED 최신 스프레드 10월 13일: 10년-2년 +0.42%p, 10년-3개월 +0.95%p. 개별 금리 최신 관측 10월 9일: 3개월 4.25%, 2년 4.80%, 10년 5.24%. 서로 다른 날짜의 절대금리와 스프레드를 같은 날짜 차감값처럼 쓰지 않는다.

![최근 90일](../charts/us_yield_spreads_90d_{DATE}.png)
![최근 2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 오늘 KOSPI·KODEX 시나리오

강세 20%: 6,200 초과~6,350. 15:20 기준 KOSPI 6,200 초과 AND 외국인 현물 순매수 AND 프로그램 순매수. 6,200 재이탈 시 무효.
기본 45%: 5,900~6,200. 15:20 기준 하단 이상 AND 상단 이하 AND 외국인 순매도 8천억원 이하. 범위 이탈 시 무효.
약세 35%: 5,750~5,900 미만. 15:20 기준 5,900 미만 AND 외국인 순매도 AND 프로그램 순매도. 5,900 회복 시 무효.
KODEX 78,780/81,965/88,340원. 공격·관망·방어 10/50/40.

## 장중 체크리스트

09:30·10:00에 메모리 반등과 수급 동행, 14:00·15:20에 5,900 방어와 6,200 회복을 확인한다. 전일 저가 5,911.11 이탈 여부도 확인한다.

## 출처와 확인 시각

'''+ '\n'.join(f'- [{a}]({b}) — {CUTOFF} 확인, 표별 원천 시각 우선.' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
old=read('articles/market-2026-10-13.html'); prefix=old.split('<article class="editorial-article reading-article">')[0]; suffix=old[old.index('</div></article></main>'):]
prefix=prefix.replace('market-2026-10-13.html',f'market-{DATE}.html').replace('market-2026-10-13-chip-selloff-support-1200x630.png',IMAGE)
prefix=re.sub(r'<title>.*?</title>',f'<title>{TITLE} | 연마</title>',prefix)
for prop,val in [('description',SUMMARY),('og:title',TITLE),('twitter:title',TITLE),('og:description',SUMMARY),('twitter:description',SUMMARY),('og:image:alt',ALT),('article:published_time',NOW),('article:modified_time',NOW)]: prefix=re.sub(r'(<meta (?:property|name)="'+re.escape(prop)+r'" content=")[^"]+',lambda m:m[1]+val,prefix)
def article_ld(m):
 j=json.loads(m[1]); j.update(headline=TITLE,description=SUMMARY,datePublished=NOW,dateModified=NOW,mainEntityOfPage=URL,image={'@type':'ImageObject','url':'https://www.hpmplab.com/assets/images/articles/'+IMAGE,'width':1200,'height':630}); return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False)+'</script>'
prefix=re.sub(r'<script type="application/ld\+json">(.*?)</script>',article_ld,prefix,flags=re.S)
def table(md):
 rows=[l.split('|')[1:-1] for l in md.splitlines() if l.startswith('|') and '---' not in l]; return '<div class="article-table-wrap"><table class="article-data-table"><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
header=f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong>HPMPLab</strong><time datetime="{NOW}">2026.10.14 · 작성 {NOW[11:16]} KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 {NOW} · 데이터 최종 확인 {CUTOFF}. 공개 시각은 아래 발행 기록 기준입니다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석입니다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" alt="{ALT}" fetchpriority="high"></figure></header><div class="article-body" id="article-body">'
charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{span}_{DATE}.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {span}"></figure>' for span in ['90d','long_term'])
links='<p>'+ ' · '.join(f'<a href="{b}">{a}</a>' for a,b in sources)+'</p>'
write(f'articles/market-{DATE}.html',prefix+header+body+'<h2>장전 시세</h2>'+table('|항목|최근값|원천 시각|\n'+fast)+ '<h2>미국 정규장</h2>'+table('|종목|종가|등락|\n'+ustable)+charts+links+suffix)
for page,css in [('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')]:
 s=read(page); pat=r'<article class="'+css+r'"[^>]*>.*?</article>'; match=next(m for m in re.finditer(pat,s,re.S) if 'market-2026-10-13.html' in m[0]); card=match[0].replace('market-2026-10-13.html',f'market-{DATE}.html').replace('market-2026-10-13-chip-selloff-support-1200x630.png',IMAGE).replace('반도체 5일 연속 하락…KOSPI는 6,384선 지지부터',TITLE).replace('미국 반도체와 국내 메모리주가 함께 밀린 뒤입니다. 6,384선의 지지와 6,450선 회복, 외국인·프로그램 수급을 순서대로 봐야 합니다.',SUMMARY).replace('2026.10.13 · 08:09 KST','2026.10.14 · '+NOW[11:16]+' KST').replace('2026-10-13T08:09:54+09:00',NOW).replace('10월 13일','10월 14일'); s=s[:match.start()]+card+'\n'+s[match.start():]
 s=s.replace('market-2026-10-13-chip-selloff-support-1200x630.png',IMAGE,1)
 for prop,val in [('og:title',TITLE),('twitter:title',TITLE),('og:description',SUMMARY),('twitter:description',SUMMARY)]: s=re.sub(r'(<meta (?:property|name)="'+prop+r'" content=")[^"]+',lambda m:m[1]+val,s)
 def collection(m):
  j=json.loads(m[1]); nodes=j.get('@graph',[j]);
  for n in nodes:
   if n.get('@type')=='CollectionPage':
    e=n.get('mainEntity',{}); items=e.get('itemListElement',[]); items.insert(0,{'@type':'ListItem','position':1,'url':URL,'name':TITLE,'description':SUMMARY,'datePublished':NOW,'dateModified':NOW,'image':{'@type':'ImageObject','url':'https://www.hpmplab.com/assets/images/articles/'+IMAGE}})
    for i,x in enumerate(items,1): x['position']=i
    e['numberOfItems']=len(items)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',collection,s,flags=re.S)
 if page=='articles/market.html':
  s=re.sub(r'(일일시황 <span class="article-category-count">)\d+',lambda m:m[1]+str(len(list(R.glob('articles/market-20*.html')))),s)
  s=re.sub(r'(id="market-(?:latest-article|summary-article)-link" href=")[^"]+',lambda m:m[1]+f'market-{DATE}.html',s)
  s=re.sub(r'(발행일 기준 최신순 · )\d+(편)',lambda m:m[1]+str(len(list(re.finditer(pat,s,re.S))))+m[2],s)
 else:
  cats=re.findall(r'<article class="article-card(?: home-article-card)?" data-category="([^"]+)"',s)
  for c in ['all','market','essay','health']: s=re.sub(r'(data-category-count="'+c+r'">)\d+',lambda m:m[1]+str(len(cats) if c=='all' else cats.count(c)),s)
 write(page,s)
s=read('sitemap.xml'); s=s.replace('</urlset>',f'<url><loc>{URL}</loc><lastmod>{DATE}</lastmod><image:image><image:loc>https://www.hpmplab.com/assets/images/articles/{IMAGE}</image:loc></image:image></url>\n</urlset>'); write('sitemap.xml',s)
s=json.loads(read('assets/data/market-dashboard-latest.json')); s.update(snapshotId=SID,generatedAt=NOW,asOf=CUTOFF,asOfDisplay=CUTOFF,marketState='한국 장전',sourceLabel='미국 10월 13일 정규장 · 국내 10월 13일 종가 · 10월 14일 장전',latestArticle={'title':TITLE,'href':f'market-{DATE}.html'},headline=TITLE,summary=SUMMARY)
for x in s['markets']:
 if x['id']=='KOSPI':
  v=prev['KOSPI']; x.update(value=num(v['closePrice']),changePercent=num(v['fluctuationsRatio']),open=num(v['openPrice']),high=num(v['highPrice']),low=num(v['lowPrice']),previousClose=6384.24,asOf='2026-10-13T15:30:00+09:00',asOfLabel='10월 13일 종가',flows=[])
 else: x.update(value=None,changePercent=None,open=None,high=None,low=None,previousClose=None,flows=[],asOf=CUTOFF,asOfLabel='장전 미개시')
s['stance']={'label':'급락 뒤 6,000선과 CPI','attack':10,'wait':50,'defense':40,'note':'국내 메모리 반등과 외국인·프로그램 수급의 동행을 본다.'}
s['checkpoints']=[{'label':x['stockName']+' NXT','value':x['closePrice']+'원 · '+x['fluctuationsRatio']+'%','detail':x['localTradedAt'],'tone':'info'} for x in nxt]+[{'label':'하나은행 USD/KRW','value':fx['closePrice']+'원','detail':fx['localTradedAt'],'tone':'warning'}]
s['changes']=[{'label':'KOSPI','before':'6,384.24','after':'6,035.35','meaning':'국내 메모리 경쟁 우려가 전일 급락에 반영됐습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'MU -3.62% · NVDA +0.97%','detail':'10월 13일 정규장','tone':'warning'},{'label':'미 국채','metric':'10년 5.24% · 2년 4.80%','detail':'10월 9일 FRED 개별 금리','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/13','value':'$59.90','change':'+0.79%'},{'label':'DDR4 16Gb · 10/13','value':'$83.858','change':'+0.06%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,900 / 5,750','pivot':'6,200','resistance':'6,350'},{'asset':'KODEX 레버리지','support':'78,780원','pivot':'81,965원','resistance':'88,340원'}]
s['scenarios']=[{'id':n,'label':label,'range':ran,'summary':summ,'conditions':conds,'invalidation':inv} for n,label,ran,summ,conds,inv in [('bull','강세 · 20%','KOSPI 6,200 초과~6,350','수급이 동반 회복하는 반등',['6,200 초과','외국인 순매수','프로그램 순매수'],'6,200 재이탈'),('base','기본 · 45%','KOSPI 5,900~6,200','급락을 소화하는 구간',['5,900 이상','6,200 이하','외국인 순매도 8천억원 이하'],'범위 이탈'),('bear','약세 · 35%','KOSPI 5,750~5,900 미만','반등 실패와 매도 지속',['5,900 미만','외국인 순매도','프로그램 순매도'],'5,900 회복')]]
s['events']=[{'time':'10월 13일 국내 정규장','name':'메모리 경쟁 우려와 급락','path':'국내에 이미 반영된 재료'},{'time':'10월 14일 21:30 KST','name':'미국 9월 CPI','path':'다음 한국장 금리·환율'}]
s['checklist']=[{'id':'support','label':'5,900 방어'},{'id':'rebound','label':'6,200 회복과 수급 동행'}]; s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=prev['KOSPI' if x['id']=='KOSPI' else '122630']; levels=[5900,6200,6350] if x['id']=='KOSPI' else [78780,81965,88340]; x.update(asOf='2026-10-13T15:30:00+09:00',asOfLabel='10월 13일 정규장 종가',points=[{'label':label,'value':num(v[key])} for label,key in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월 13일 확정 일봉과 10월 14일 장전 분석 기준선입니다.'
dump('assets/data/market-dashboard-'+SID+'.json',s); dump('assets/data/market-dashboard-latest.json',s)
f=json.loads(read('research/evaluation/forecasts/2026-10-13-0812-same-close.json')); f.update(forecastId=FID,reportPath='reports/'+DATE+'.md',reportSha256=hashlib.sha256(report.encode()).hexdigest(),issuedAt=NOW,dataCutoffAt=CUTOFF,reference={'price':6035.35,'asOf':'2026-10-13T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':6200,'high':6350,'probability':.2},'base':{'low':5900,'high':6200,'probability':.45},'bear':{'low':5750,'high':5900,'probability':.35}},pathEnvelope={'low':5650,'high':6450,'coverage':.9},posture={'attack':10,'wait':50,'defense':40},drivers=[{'id':'memory-competition','rank':1,'claim':'国内急落後の米国メモリ弱含み','validationMetric':'MU・国内メモリ'}, {'id':'cpi','rank':2,'claim':'오늘 밤 CPI','validationMetric':'BLS'}]); f['drivers'][0].update(claim='국내 급락 뒤 미국 메모리 약세',validationMetric='MU·국내 메모리'); f['target'].update(sessionDate=DATE,previousSessionDate='2026-10-13')
for k,t in f['scenarioTriggers'].items():
 t['observeBy']=DATE+'T15:20:00+09:00'
 for c in t['conditions']:
  if c['metricId']=='kospi_price': c['threshold']=6200 if k=='bull' or c['operator']=='lte' else 5900
f.pop('contentHash',None); f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(); dump('research/evaluation/forecasts/'+FID+'.json',f)
sessions=json.loads(read('research/evaluation/trading-sessions.json')); sessions.update(asOf=CUTOFF,source='KRX 10월 휴장 공지 및 Naver PREOPEN',rawHash=ev('KOSPI-basic')['rawHash']); sessions['sessions']=sorted(set(sessions['sessions']+['2026-10-13',DATE])); dump('research/evaluation/trading-sessions.json',sessions)
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 {NOW}, 최종 데이터 확인 {CUTOFF}, 한국 장전.\n- 직전 KOSPI 6,035.35(-5.46%), KODEX 81,965원(-12.45%).\n- 핵심: 중국 메모리 경쟁 우려는 전일 반영. 미국 메모리 약세와 비메모리 반등이 차별화.\n- 다음 이벤트 오늘 21:30 CPI, 내일 21:30 PPI.\n- 대응 10/50/40, 기본 5,900~6,200(45%), 강세 6,200 초과~6,350(20%), 약세 5,750~5,900 미만(35%).\n- 보고서 reports/{DATE}.md, 취재 research/notes/{DATE}.md, 대시보드 assets/data/market-dashboard-{SID}.json.\n- 차트 charts/us_yield_spreads_*_{DATE}.png. 직전 전망은 하단도 이탈해 낙폭 과소평가. 수급 앵커 미확보.\n- 평가 전체 실행은 기존 2026-09-21 보고서 해시 불일치로 실패.\n')
print(FID,NOW,CUTOFF)
