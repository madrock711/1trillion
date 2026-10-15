"""검증한 취재 노트로 오늘의 공개 원고와 대시보드를 준비한다."""
import base64, datetime, hashlib, html, json, re
from pathlib import Path
R=Path(__file__).resolve().parents[3]; P=Path(__file__).parent
DATE='2026-10-16'; OLD='2026-10-15'
TITLE='TSMC 호실적에도 반도체 약세…급락한 KOSPI의 반등 조건'
SUMMARY='TSMC의 주문 전망은 강했지만 미국 생산자물가와 AI 자금조달 부담이 남았습니다. Micron 반등 속에서 KOSPI 5,450선 방어와 5,650선 회복을 봅니다.'
IMAGE='market-2026-10-16-chip-demand-funding-1200x630.png'
ALT='밝은 하늘 아래 반도체 웨이퍼가 건너는 다리와 호박색 압력 아치'
URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def num(v):return float(str(v).replace(',',''))
def raw(k):return base64.b64decode(ev(k+'.raw')['raw'])
def ohlc(k):
 row=re.search(rb'20261015\|([^"\s]+)',raw(k+'-fchart')).group(1).decode().split('|');return dict(zip(['open','high','low','close','volume'],map(float,row)))
K=ohlc('KOSPI'); L=ohlc('KODEX')
assert K['close']==num(ev('KOSPI-basic')['data']['closePrice'])
v=ev('122630')['data'][0]
assert [L[k] for k in ['open','high','low','close','volume']]==[num(v[k]) for k in ['openPrice','highPrice','lowPrice','closePrice','accumulatedTradingVolume']]
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(raw('after-'+k));d=d['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f'|{k}|{c:,.2f}|{(c/us(k)[0]-1)*100:+.2f}%|{at}|')
aftertable='\n'.join(after)
sources=[('TSMC 공식 실적','https://investor.tsmc.com/english/quarterly-results/2026/q3'),('미국 PPI','https://www.bls.gov/news.release/ppi.nr0.htm'),('AI 금융비용 Reuters','https://www.investing.com/news/stock-market-news/coreweave-shares-bonds-slide-further-as-ai-debt-fears-mount-4951350'),('미국 가격','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉','https://fchart.stock.naver.com/sise.nhn?symbol=KOSPI&timeframe=day&count=5&requestType=0'),('메모리 현물','https://www.trendforce.com/price/dram/dram_spot'),('경제 일정','https://www.bls.gov/schedule/2026/10_sched.htm'),('FRED 금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
fast='최종 조회 전'
report=f'''# {DATE} KOSPI·KODEX 장전 리서치

작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전. 미국 10/15 정규장 종료, 시간외 최근 거래 별도 표기.

## 핵심 결론

{SUMMARY} 기본 종가 5,450~5,650(45%), 강세 5,650 초과~5,800(25%), 약세 5,200~5,450 미만(30%). 대응 공격 10·관망 50·방어 40. 장중 90% 포락 5,050~5,950. 확률과 대응 점수는 별개이며 판단 범위 밖 결과도 가능.

## 밤사이 시장을 지배한 이슈

BLS PPI 전월 1.3%·전년 6.3%, 식품·에너지·무역서비스 제외 0.5%·5.0%. 10/15 21:30 KST로 한국 마감 뒤 새 정보. TSMC 3분기 매출 467.2억달러와 4분기 523~543억달러 전망은 전일 15:00 KST 발표로 한국 막판 반영 가능. 두 재료의 시간차를 구분한다. TSMC 실적 수치는 공식 IR 기준. 물가→금리·자금조달→AI 투자속도 경로는 해석이다.

Reuters 10/15 16:00 ET 갱신: CoreWeave 주식은 장중 반등했으나 채권 금리는 약 15%. Axios 별도 보도와 대조. 실제 파산·청산 확정이 아니다. 기존 AI 금융비용과 CPI·CXMT 우려는 한국장 반영분을 다시 가산하지 않는다. 신규 확정 공급계약·대규모 증자·수출규제·빅테크 실적 원문은 미확인. 후보 순위·반론은 research/notes/{DATE}.md.

## 직전 전망 회고와 국내 시장

전일 KOSPI 5,554.22(-7.57%)는 약세 하단 5,600도 이탈했다. 기본 범위 실패, 전체 종가 포락 실패. 저가 5,450.81은 장중 포락 5,450 바로 위였다. 방어적 대응과 종가 예측 정확성은 별개. 15:20 수급 앵커 누락으로 조건 정산은 미검증.

|항목|10/15 시가|고가|저가|종가|
|---|---:|---:|---:|---:|
|KOSPI|5,673.01|5,751.45|5,450.81|5,554.22|
|KODEX|72,505|73,800|64,920|67,785|

KODEX 거래량 35,584,318주. fchart와 price OHLCV 일치. 삼성·하이닉스의 API 중복 일봉은 NXT/통합시세와 KRX 정규장 범위 차이가 있어 정규장값으로 단정하지 않는다. 전일 서킷브레이커는 뉴스핌·뉴스웨이 대조, 오늘 신규 사건으로 가산하지 않는다.

## 메모리 반도체 수급

TrendForce 10/15 18:10 GMT+8 DDR5 16Gb 60.433달러(+0.55%), DDR4 16Gb 83.66달러(+0.06%). 현물 수요와 주가 수급은 분리. HBM·서버 DRAM·RDIMM·NAND·eSSD·TLC·SLC/MLC 신규 계약가격, 실제 수율·생산량·고객 주문은 미확인. 빅테크 투자 계획을 확정 메모리 매출로 치환하지 않는다. TSMC 가이던스와 MU 반등은 수요 붕괴 주장에 반대 근거다.

## 미국 정규장·시간외

|종목|10/15 정규장 종가 USD|등락|
|---|---:|---:|
{ustable}

정규장 종료 10/16 05:00 KST. Yahoo 시세 원천, Reuters 업종 하락 대조. SOXX·SMH 하락과 Micron 상승이 공존한다.

|종목|시간외 USD|정규장 대비|원천 시각 KST|
|---|---:|---:|---|
{aftertable}

시간외는 마지막 관측 5분봉이며 확정 종가와 다르다. 거래량·종목별 시차 주의.

## 발행 직전 환율·미국 선물·국내 NXT

FAST_TABLE

하나은행 고시는 역외 현물환과 다르다. 선물은 최근 거래, NXT는 실제 거래일·OPEN·거래량을 확인한다. KRX 종가와 기준이 다를 수 있다.

## 국내 수급·시장 구조

오늘 integration이 초기화되어 전일 최종 현물·프로그램·시장 폭 묶음을 복구하지 못했다. 당일 0은 장전 미개시이므로 전일 확정값으로 쓰지 않는다. 언론 외국인 순매도 금액도 3.6253조/4.8196조로 충돌해 정확값 미확인. 금융투자·연기금·사모·보험·투신 및 선물 수급 미확인. 현재 환율과 전일 수급을 같은 시점으로 연결하지 않는다. 삼성·하이닉스 비중이 큰 지수와 방어업종의 차이를 개장 후 시장 폭과 함께 점검.

## 금리·경제 캘린더

FRED 개별금리 10/14: 3개월 4.28%, 2년 4.82%, 10년 5.19%. 10/15 금리차 10년-2년 +0.33%p, 10년-3개월 +0.82%p. 서로 다른 기준일이므로 동일 날짜 차감·금리방향으로 일반화하지 않는다. PPI를 근거로 국채 종가 상승을 단정하지 않음.

오늘 10/16 미국 수출입물가 08:30 ET=21:30 KST(BLS). 산업생산은 연준 일정 후속 확인, Warsh 발언 시각은 공식 원문 미확보로 확정 일정에서 제외. 다음 KRX 거래일 월요일 10/19, 주말 신규 정책·신용 뉴스 점검.

![최근 90일](../charts/us_yield_spreads_90d_{DATE}.png)
![최근 2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 조건부 시나리오·무효화

- 강세 25%: 5,650 초과~5,800. 15:20 지수>5,650 AND 외국인>0 AND 프로그램>0. 5,650 재이탈 시 무효.
- 기본 45%: 5,450~5,650. 15:20 지수>=5,450 AND <=5,650 AND 외국인>=-8,000억원. 범위 이탈·매도 확대 시 무효.
- 약세 30%: 5,200~5,450 미만. 15:20 지수<5,450 AND 외국인<0 AND 프로그램<0. 5,450 회복 시 무효.
- KODEX 64,920/67,785/73,800원: 1차 지지/반등 기준/저항. 64,920 이탈 후 미회복 시 지지 판단 무효.

## 장중 확인

09:30·10:00 외국인·프로그램의 동행과 NXT 반등의 KRX 지속 여부. 14:00 수급 반전, 15:20 지수 구간과 수급 조건. 장중 예상 고저와 종가 범위는 별도 평가.

## 출처

'''+ '\n'.join(f'- [{a}]({b}) — 수집 08:01~08:04 KST, 각 원천 시각 우선.' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
old=read('articles/market-'+OLD+'.html');prefix=old.split('<article class="editorial-article reading-article">')[0];suffix=old[old.index('</div></article></main>'):]
oldimage=re.search(r'assets/images/articles/([^"\s]+)',prefix)[1]
prefix=prefix.replace('market-'+OLD+'.html','market-'+DATE+'.html').replace(oldimage,IMAGE)
prefix=re.sub(r'<title>.*?</title>',f'<title>{TITLE} | 연마</title>',prefix)
for prop,val in [('description',SUMMARY),('og:title',TITLE),('twitter:title',TITLE),('og:description',SUMMARY),('twitter:description',SUMMARY),('og:image:alt',ALT),('article:published_time',NOW),('article:modified_time',NOW)]:prefix=re.sub(r'(<meta (?:property|name)="'+re.escape(prop)+r'" content=")[^"]+',lambda m:m[1]+val,prefix)
def ld(m):
 j=json.loads(m[1]);j.update(headline=TITLE,description=SUMMARY,datePublished=NOW,dateModified=NOW,mainEntityOfPage=URL,image={'@type':'ImageObject','url':'https://www.hpmplab.com/assets/images/articles/'+IMAGE,'width':1200,'height':630});return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False)+'</script>'
prefix=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,prefix,flags=re.S)
def table(md):
 rows=[l.split('|')[1:-1] for l in md.splitlines() if l.startswith('|') and '---' not in l];return '<div class="article-table-wrap"><table class="article-data-table"><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
header=f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong>HPMPLab</strong><time datetime="{NOW}">2026.10.16 · 작성 {NOW[11:16]} KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 PREPARED · 데이터 최종 확인 PREPARED. 특정 상품의 매매 권유가 아닌 조건부 시장 분석입니다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" alt="{ALT}" fetchpriority="high"></figure></header><div class="article-body" id="article-body">'
charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{span}_{DATE}.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {span}"></figure>' for span in ['90d','long_term'])
links='<p>'+' · '.join(f'<a href="{b}">{a}</a>' for a,b in sources)+'</p>'
write('articles/market-'+DATE+'.html',prefix+header+(P/'body.html').read_text(encoding='utf-8')+'<h2>장전 시세</h2>FAST_TABLE<h2>미국 시간외 최근 거래</h2>'+table('|종목|USD|종가 대비|원천 시각|\n'+aftertable)+'<h2>미국 정규장</h2>'+table('|종목|종가 USD|등락|\n'+ustable)+charts+links+suffix)
for page,css in [('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')]:
 s=read(page);pat=r'<article class="'+css+r'"[^>]*>.*?</article>';match=next(m for m in re.finditer(pat,s,re.S) if 'market-'+OLD+'.html' in m[0]);card=match[0]
 oldtitle=json.loads(read('assets/data/market-dashboard-latest.json'))['headline'];oldsummary=json.loads(read('assets/data/market-dashboard-latest.json'))['summary']
 card=card.replace('market-'+OLD+'.html','market-'+DATE+'.html').replace(oldimage,IMAGE).replace(oldtitle,TITLE).replace(oldsummary,SUMMARY).replace('2026.10.15','2026.10.16').replace('10월 15일','10월 16일')
 card=re.sub(r'2026-10-15T[^"< ]+',NOW,card);card=re.sub(r'2026\.10\.16 · [^<]+','2026.10.16 · '+NOW[11:16]+' KST',card)
 s=s[:match.start()]+card+'\n'+s[match.start():]
 def collection(m):
  j=json.loads(m[1])
  for n in j.get('@graph',[j]):
   if n.get('@type')=='CollectionPage':
    e=n.get('mainEntity',{});items=e.get('itemListElement',[]);items.insert(0,{'@type':'ListItem','position':1,'url':URL,'name':TITLE,'description':SUMMARY,'datePublished':NOW,'dateModified':NOW,'image':{'@type':'ImageObject','url':'https://www.hpmplab.com/assets/images/articles/'+IMAGE}})
    for i,x in enumerate(items,1):x['position']=i
    e['numberOfItems']=len(items)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',collection,s,flags=re.S)
 if page=='articles/market.html':
  s=s.replace(oldtitle,TITLE).replace(oldsummary,SUMMARY);s=re.sub(r'(id="market-(?:latest-article|summary-article)-link" href=")[^"]+',lambda m:m[1]+f'market-{DATE}.html',s)
  s=re.sub(r'(일일시황 <span class="article-category-count">)\d+',lambda m:m[1]+str(len(list(R.glob('articles/market-20*.html')))),s);s=re.sub(r'(발행일 기준 최신순 · )\d+(편)',lambda m:m[1]+str(len(list(re.finditer(pat,s,re.S))))+m[2],s)
 else:
  cats=re.findall(r'<article class="article-card(?: home-article-card)?" data-category="([^"]+)"',s)
  for c in ['all','market','essay','health']:s=re.sub(r'(data-category-count="'+c+r'">)\d+',lambda m:m[1]+str(len(cats) if c=='all' else cats.count(c)),s)
 write(page,s)
s=read('sitemap.xml').replace('</urlset>',f'<url><loc>{URL}</loc><lastmod>{DATE}</lastmod><image:image><image:loc>https://www.hpmplab.com/assets/images/articles/{IMAGE}</image:loc></image:image></url>\n</urlset>');write('sitemap.xml',s)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(snapshotId='prepared',generatedAt=NOW,asOf=NOW,asOfDisplay=NOW,sourceLabel='미국 10월 15일 정규장 · 국내 10월 15일 종가 · 10월 16일 장전',headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'})
for x in s['markets']:
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=-7.57,open=K['open'],high=K['high'],low=K['low'],previousClose=6008.81,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월 15일 정규장 종가',flows=[])
 else:x.update(value=None,changePercent=None,open=None,high=None,low=None,previousClose=None,flows=[],asOf=NOW,asOfLabel='장전 미개시')
s['stance']={'label':'반등 지속에는 수급 회복 필요','attack':10,'wait':50,'defense':40,'note':'Micron 반등과 물가·AI 금융비용 부담이 공존합니다.'}
s['changes']=[{'label':'KOSPI','before':'6,008.81','after':'5,554.22','meaning':'전일 급락 뒤 5,450선 방어와 수급 회복을 봅니다.'}]
s['factors']=[{'label':'생산자물가','metric':'전월 +1.3% · 전년 +6.3%','detail':'10월 15일 BLS 발표','tone':'warning'},{'label':'미국 반도체','metric':'SOXX -0.91% · MU +1.87%','detail':'10월 15일 정규장','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/15','value':'$60.433','change':'+0.55%'},{'label':'DDR4 16Gb · 10/15','value':'$83.66','change':'+0.06%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,450','pivot':'5,650','resistance':'5,800'},{'asset':'KODEX 레버리지','support':'64,920원','pivot':'67,785원','resistance':'73,800원'}]
s['scenarios']=[{'id':k,'label':label,'range':ran,'summary':summ,'conditions':cond,'invalidation':inv} for k,label,ran,summ,cond,inv in [('bull','강세 · 25%','KOSPI 5,650 초과~5,800','수급이 함께 회복하는 반등',['5,650 초과','외국인 순매수','프로그램 순매수'],'5,650 재이탈'),('base','기본 · 45%','KOSPI 5,450~5,650','급락 이후 가격 탐색',['5,450 이상','5,650 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 매도 확대'),('bear','약세 · 30%','KOSPI 5,200~5,450 미만','전일 저점 이탈',['5,450 미만','외국인 순매도','프로그램 순매도'],'5,450 회복')]]
s['events']=[{'time':'10월 16일 21:30 KST','name':'미국 수출입물가','path':'물가·금리 기대 변화'},{'time':'10월 19일 한국장','name':'다음 정규 거래일','path':'주말 정책·신용 뉴스 반영'}]
s['checklist']=[{'id':'support','label':'5,450 방어'},{'id':'rebound','label':'5,650 회복과 수급 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5450,5650,5800] if x['id']=='KOSPI' else [64920,67785,73800];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월 15일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월 15일 확정 일봉과 10월 16일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s)
dump('research/evidence/'+DATE+'/prepared.json',{'title':TITLE,'summary':SUMMARY,'image':IMAGE,'asOf':NOW})
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI 5,554.22(-7.57%), KODEX 67,785원(-16.42%). 최종 수급·프로그램·시장 폭은 오늘 초기화로 원문 미확보.\n- 신규 PPI +1.3%/+6.3%, TSMC 호실적·MU 반등과 금융비용 부담 공존. 기존 국내 급락 재료 중복 제외.\n- 오늘 21:30 미국 수출입물가. 다음 KRX 거래일 10/19.\n- 기본 5,450~5,650(45%), 강세 5,650 초과~5,800(25%), 약세 5,200~5,450 미만(30%), 대응 10/50/40.\n- 보고서 reports/{DATE}.md, 취재 research/notes/{DATE}.md, 차트 charts/us_yield_spreads_*_{DATE}.png.\n- 직전 전망 약세 하단도 이탈. 수급 앵커 미확보로 조건 미검증. 누적 전체 평가는 기존 9/21 해시 불일치로 중단.\n')
print('준비 완료',NOW)
