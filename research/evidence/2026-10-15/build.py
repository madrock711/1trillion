"""2026-10-15 검증 자료로 보고서·공개 원고·대시보드를 준비한다."""
import datetime, hashlib, html, json, re
from pathlib import Path

R=Path(__file__).resolve().parents[3]
P=Path(__file__).parent
DATE='2026-10-15'
TITLE='미국 물가 재가속에 반도체 급락…KOSPI 6,000선 다시 시험'
SUMMARY='미국 CPI가 3.7%로 높아지고 반도체주가 동반 하락했습니다. 전일 외국인 매도가 이어진 KOSPI는 6,000선 방어와 오늘 TSMC 실적이 관건입니다.'
IMAGE='market-2026-10-15-cpi-chip-pressure-1200x630.png'
ALT='밝은 자연광 속 반도체 칩 위로 올라가는 금빛 고리와 옆에 놓인 실리콘 웨이퍼'
URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,s):write(p,json.dumps(s,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def num(v):return float(str(v).replace(',',''))
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
CUTOFF=max(ev(k)['fetchedAt'] for k in ['NXT','FX','yahoo-NQF','yahoo-ESF'])
SID='20261015-'+NOW[11:16].replace(':','')
FID=DATE+'-'+NOW[11:16].replace(':','')+'-same-close'
prev={k:next(v for v in ev(k)['data'] if v['localTradedAt']=='2026-10-14') for k in ['KOSPI','122630','005930','000660']}
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0];return q['close'][-1],(q['close'][-1]/q['close'][-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
nxt=ev('NXT')['data']['datas'];fx=ev('FX')['data']['exchangeInfo']
fast='\n'.join(f"|{x['stockName']} NXT ({x['marketStatus']})|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|" for x in nxt)
fast+=f"\n|하나은행 USD/KRW 고시|{fx['closePrice']}원|{fx['localTradedAt']}|"
for k in ['NQF','ESF','CLF','BZF']:
 m=ev('yahoo-'+k)['data']['chart']['result'][0]['meta'];t=datetime.datetime.fromtimestamp(m['regularMarketTime'],datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');fast+=f"\n|{k} 최근 거래|{m['regularMarketPrice']:,.2f}|{t}|"
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads((P/('after-'+k+'.txt')).read_text())['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<t<post['end']]
 if pairs:
  t,c=pairs[-1];stamp=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f'|{k}|{c:,.2f}|{(c/us(k)[0]-1)*100:+.2f}%|{stamp}|')
aftertable='\n'.join(after)
sources=[('미국 9월 CPI','https://www.bls.gov/news.release/cpi.nr0.htm'),('미국 정규장 가격','https://finance.yahoo.com/quote/SOXX/'),('KOSPI·국내 종가','https://m.stock.naver.com/domestic/index/KOSPI/total'),('ASML 3분기 실적','https://investor.asml.com/news-releases/news-release-details/asml-reports-eu11.7-billion-total-net-sales-and-eu5.0-billion-net-income-q3-2026'),('TSMC 실적 일정','https://investor.tsmc.com/english/quarterly-results/2026/q3'),('메모리 현물','https://www.trendforce.com/price/dram/dram_spot'),('PPI 일정','https://www.bls.gov/schedule/2026/10_sched.htm'),('미국 금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
body='''<p>밤사이 미국 물가가 다시 높아지자 반도체주가 함께 밀렸다. 9월 CPI는 전년 대비 3.7%, 전월 대비 0.6% 상승했다. SOXX는 4.50%, SMH는 3.98% 하락했고 Nvidia·AMD·Micron·Broadcom도 모두 내렸다. 전일 서울장 마감 뒤 나온 물가 발표가 오늘 국내 반도체주에 새 부담을 더한다.</p>
<h2>물가 부담이 메모리 밖으로 번졌다</h2><p>전날까지는 중국 메모리 경쟁 우려가 매도의 중심이었다. 이번에는 AMD가 5.73%, Nvidia가 3.16% 하락하며 비메모리주도 흔들렸다. 높은 물가가 금리 인하 기대를 약하게 만들면, 미래 이익에 높은 값을 지불해 온 AI 주식과 자금 조달이 필요한 데이터센터 투자가 함께 압박받는다.</p>
<p>물가의 내부 구성도 봐야 한다. 에너지 가격은 한 달 새 5.2% 올랐지만 식품·에너지를 뺀 근원 CPI는 전월 대비 0.3%, 전년 대비 2.6% 상승했다. 에너지발 충격과 기조적인 물가 압력을 구분할 필요가 있다. <a href="https://www.bls.gov/news.release/cpi.nr0.htm">미 노동통계국 CPI</a>의 발표값이다.</p>
<h2>설비와 메모리 수요는 주가와 다른 속도로 움직인다</h2><p>ASML의 3분기 매출은 117억유로, 순이익은 50억유로였다. 회사는 올해 매출 전망을 440억~450억유로로 제시했다. 반도체 설비 수요가 버티고 있다는 근거다. 그렇다고 오늘 한국 주식의 매도 물량이 곧바로 사라지는 것은 아니다. <a href="https://investor.asml.com/news-releases/news-release-details/asml-reports-eu11.7-billion-total-net-sales-and-eu5.0-billion-net-income-q3-2026">ASML 실적 발표</a>에 따른 수치다.</p>
<p>메모리 현물도 한 방향으로 움직이지 않았다. 10월 14일 DDR5 16Gb 평균은 60.10달러로 0.33% 올랐고 DDR4 16Gb는 83.611달러로 0.30% 내렸다. 현물 일부 품목의 강세를 HBM·NAND 전체의 계약가격이나 당일 주가 반등으로 넓혀 읽기는 어렵다. <a href="https://www.trendforce.com/price/dram/dram_spot">TrendForce 현물가격</a> 기준이다.</p>
<h2>6,000선 회복에는 수급이 따라야 한다</h2><p>전일 KOSPI는 6,008.81로 0.44% 하락했다. 외국인은 현물을 1조 1,614억원 순매도했고 기관은 7,876억원 순매수했다. 프로그램 합계는 3억원 순매수였지만 비차익은 631억원 순매도였다. 지수가 6,000선을 지켜도 외국인 매도가 크게 남아 있는 상태다.</p>
<p>오늘 기본 종가 범위는 5,800~6,050으로 가능성을 45%로 둔다. 6,050 초과~6,200의 강세 가능성은 15%, 5,600~5,800 미만의 약세 가능성은 40%다. 6,050 위에서 외국인과 프로그램이 함께 순매수해야 강세 판단에 힘이 실린다. 5,800 아래에서 두 수급이 동반 매도하면 약세 흐름으로 본다. 범위를 벗어나거나 수급 방향이 바뀌면 해당 판단도 다시 봐야 한다.</p>
<p>KODEX 레버리지는 전일 저가 79,070원, 종가 81,100원, 고가 86,295원을 각각 1차 지지·반등 기준·저항으로 둔다. 전일 저가 아래에서 반등하지 못하면 저점이 내려가는 흐름에 더 무게를 둔다. 급락한 미국 ETF와 한국장의 기존 메모리 충격을 같은 악재로 두 번 더하지 않고, 새 물가 발표와 오늘 실제 가격·수급을 함께 봐야 한다.</p>
<h2>오후 TSMC, 밤에는 생산자물가</h2><p>TSMC 실적 설명회는 오늘 15:00 KST다. 매출뿐 아니라 다음 분기 전망, 설비투자와 첨단공정·패키징 수요가 한국 메모리주의 오후 흐름을 바꿀 수 있다. <a href="https://investor.tsmc.com/english/quarterly-results/2026/q3">TSMC 공식 일정</a>은 대만 시각 14:00로 공지돼 있다.</p>
<p>오늘 21:30 KST에는 미국 9월 PPI가 나온다. CPI에 이어 기업의 비용 부담이 얼마나 커졌는지 볼 수 있는 일정이다. 국내 정규장 이후 발표이므로 결과의 직접적인 반영은 다음 거래일로 넘어간다. <a href="https://www.bls.gov/schedule/2026/10_sched.htm">BLS 발표 일정</a>에 따른다.</p>'''
report=f'''# {DATE} KOSPI·KODEX 일일 리서치

작성 {NOW} / 데이터 최종 확인 {CUTOFF} / 한국 장전. 시세별 원천 거래 시각을 분리한다.

## 핵심 결론

{SUMMARY} 조건부 기본 종가 5,800~6,050(45%), 강세 6,050 초과~6,200(15%), 약세 5,600~5,800 미만(40%). 대응 점수 공격 5·관망 45·방어 50. 장중 90% 포락 5,450~6,300. 확률은 분석 판단이며 보장하지 않는다.

## 밤사이 시장을 지배한 이슈

BLS 9월 CPI 전년 3.7%, 전월 0.6%, 근원 2.6%/0.3%, 에너지 전월 5.2%. 10/14 21:30 KST 발표로 전일 KRX 마감 뒤 신규 정보. 미국 반도체 전반 하락이 할인율·AI 자금조달 부담을 보여준다. 물가가 모든 매도의 단일 원인이라는 주장은 하지 않는다. 전일 반영된 CXMT 경쟁 우려와 ADR 후행 하락은 별도 충격으로 중복 가산하지 않는다.

ASML 3분기 매출 117억·순익 50억유로, 연간 매출 440~450억유로는 반대 근거. NVIDIA cuPotential은 제품 생태계 발표로 계약금액·신규 실적으로 바꾸지 않는다. BAC 제재는 Treasury 10/13 발표, 한국 반도체 직접성 낮음. Anthropic 매출 Reuters 보도는 회사 원문 미확보. 새 강제청산·증자·규제·확정 공급계약은 미확인. 후보 점수·제외 근거는 research/notes/{DATE}.md에 보존.

## 전일 대비 바뀐 변수와 유지 변수

KOSPI 종가 6,008.81은 직전 기본 5,900~6,200 안이고 고저 경로 5,944.65~6,190.65도 포락 안. 외국인 -11,614억원은 기본 조건 -8,000억원을 이탈했다. 범위 적중을 수급 지속성 적중으로 바꾸지 않는다. 15:20 앵커 미확보로 구조화 조건은 미검증. 새 CPI 발표와 비메모리 동반 매도가 오늘의 변화.

## 한국시장·KODEX 대시보드

|항목|10월 14일 종가|등락|
|---|---:|---:|
'''+ '\n'.join(f"|{k}|{v['closePrice']}|{v['fluctuationsRatio']}%|" for k,v in prev.items())+f'''

## 메모리 반도체 수급

TrendForce 10/14 18:10 GMT+8: DDR5 16Gb 60.10달러(+0.33%), DDR4 16Gb 83.611달러(-0.30%). 현물 품목 혼조와 주식 매도 압력은 분리한다. HBM·NAND·eSSD 신규 계약가격, 고객별 실제 공급량·양산 수율은 미확인. ASML 설비 실적을 메모리 가격 전반의 상승으로 치환하지 않는다.

## 미국 반도체·AI

|ETF·종목|10월 14일 정규장 종가 USD|전일 대비|
|---|---:|---:|
{ustable}

Yahoo 마지막 두 정규장 일봉, AP 종목 등락 대조. 정규장 종료 10/15 05:00 KST.

|종목|시간외 최근 USD|정규장 종가 대비|원천 거래 시각 KST|
|---|---:|---:|---|
{aftertable}

시간외 최근 5분봉 관측이며 완료 종가가 아니다. 낮은 유동성과 종목별 거래 시각 차이를 고려한다.

## 달러/원·유가·선물·국내 수급

|항목|최근값|원천 시각|
|---|---:|---|
{fast}

하나은행 고시환율과 역외 현물환을 구분한다. 선물 값은 최근 거래이며 정규장 지수 종가가 아니다. NXT 등락 기준과 KRX 전일 종가가 다를 수 있다. PREOPEN/거래량 없음은 당일 체결로 읽지 않는다.

전일 확정 원문(10/14 CLOSE·bizdate 20261014): 외국인 -11,614·기관 +7,876·개인 -3,203억원. 프로그램 차익 +634·비차익 -631·합계 +3억원. 상승 503·하락 371·보합 44종목, 상한 4 별도. 수급 앵커 09:30·10:00·14:00은 미확보. 장전 당일 0은 미개시로 제외. 선물 투자자 수급은 미확인.

## 경제 캘린더

TSMC 10/15 14:00 대만(02:00 ET)=15:00 KST, 당일 오후. 미국 9월 PPI 10/15 08:30 ET=21:30 KST. 미국 수출입물가 10/16 08:30 ET=21:30 KST. 빅테크 새 실적 원문은 미확보, 과거 분기 실적을 당일 발표로 쓰지 않음.

## 미 국채와 장단기 금리차

FRED 개별 최신 금리 10/13: 3개월 4.26%, 2년 4.79%, 10년 5.21%. 10/14 최신 금리차 10년-2년 +0.37%p, 10년-3개월 +0.91%p. 서로 다른 날짜의 자료이므로 동일 날짜 차감값으로 쓰지 않는다. CPI 직후 금리 상승 보도를 하루 종가 상승으로 일반화하지 않는다.

![최근 90일](../charts/us_yield_spreads_90d_{DATE}.png)
![최근 2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 오늘 KOSPI·KODEX 시나리오

- 강세 15%: 6,050 초과~6,200. 15:20 KOSPI>6,050 AND 외국인>0 AND 프로그램>0. 6,050 재이탈 시 무효.
- 기본 45%: 5,800~6,050. 15:20 KOSPI>=5,800 AND <=6,050 AND 외국인>=-8,000억원. 범위 이탈 또는 외국인 매도 확대 시 무효.
- 약세 40%: 5,600~5,800 미만. 15:20 KOSPI<5,800 AND 외국인<0 AND 프로그램<0. 5,800 회복 시 무효.
- KODEX 1차 지지 79,070원·반등 기준 81,100원·저항 86,295원. 전일 OHLC 기준, 이탈 시 보장 지지로 해석하지 않음.

## 장중 체크리스트

09:30·10:00 실제 외국인·프로그램 방향, 삼성전자·SK하이닉스 전일 종가 회복. 14:00 수급 변화, 15:00 TSMC 발표, 15:20 5,800 방어/6,050 회복. 원천 시각이 다르면 같은 시점의 동행으로 단정하지 않는다.

## 출처와 확인 시각

'''+ '\n'.join(f'- [{a}]({b}) — 확인 {NOW}, 표별 원천 시각 우선.' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)

# 이미 검증된 기사/목록 마크업을 재사용하고 오늘의 문구만 새로 삽입한다.
template=read('research/evidence/2026-10-14/build.py')
fragment=template[template.index("old=read('articles/market-2026-10-13.html')"):template.index("s=json.loads(read('assets/data/market-dashboard-latest.json'))")]
fragment=fragment.replace('market-2026-10-13.html','market-2026-10-14.html').replace('market-2026-10-13-chip-selloff-support-1200x630.png','market-2026-10-14-memory-competition-cpi-1200x630.png')
fragment=fragment.replace('반도체 5일 연속 하락…KOSPI는 6,384선 지지부터','중국 메모리 경쟁 우려 뒤 급락…오늘은 6,000선과 CPI').replace('미국 반도체와 국내 메모리주가 함께 밀린 뒤입니다. 6,384선의 지지와 6,450선 회복, 외국인·프로그램 수급을 순서대로 봐야 합니다.','국내 급락 뒤 미국 메모리주는 더 밀렸지만 Nvidia·AMD는 반등했습니다. KOSPI 6,000선 방어와 국내 메모리주 반등의 지속성을 봐야 합니다.')
fragment=fragment.replace(".replace('2026.10.13 · 08:09 KST','2026.10.14 · '",".replace('2026.10.14 · 08:13 KST','2026.10.15 · '")
fragment=fragment.replace(".replace('2026-10-13T08:09:54+09:00',NOW)",".replace('2026-10-14T08:13:01+09:00',NOW).replace('2026-10-14T08:14:06.869000+09:00',NOW)")
fragment=fragment.replace(".replace('10월 13일','10월 14일')",".replace('10월 14일','10월 15일')").replace('2026.10.14 · 작성','2026.10.15 · 작성')
fragment=fragment.replace("card+'\\n'+s[match.start():]","card+'\\n'+s[match.start():].replace('loading=\"eager\"','loading=\"lazy\"').replace('fetchpriority=\"high\"','loading=\"lazy\"')")
fragment=fragment.replace("'+charts+links+suffix)","'+charts+links+suffix)")
exec(fragment)
# 카드 날짜와 대표 이미지·본문 시각 및 시간외 표를 보강한다.
for page in ['index.html','articles/index.html','articles/market.html']:
 s=read(page);pat=r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>'
 def card_fix(m):
  c=m[0]
  if 'market-2026-10-15.html' not in c:return c
  c=c.replace('2026.10.14','2026.10.15').replace('2026-10-14T08:13:01+09:00',NOW)
  if page=='index.html':
   c=c.replace('loading="lazy"','loading="eager"',1)
   c=c.replace('decoding="async"','decoding="async" fetchpriority="high"',1)
  return c
 s=re.sub(pat,card_fix,s,flags=re.S)
 write(page,s)
s=read('articles/market-'+DATE+'.html');s=s.replace('<h2>미국 정규장</h2>','<h2>미국 시간외 최근 거래</h2>'+table('|종목|USD|종가 대비|원천 시각|\n'+aftertable)+'<h2>미국 정규장</h2>');write('articles/market-'+DATE+'.html',s)

s=json.loads(read('assets/data/market-dashboard-latest.json'))
s.update(snapshotId=SID,generatedAt=NOW,asOf=CUTOFF,asOfDisplay=CUTOFF,marketState='한국 장전',sourceLabel='미국 10월 14일 정규장 · 국내 10월 14일 종가 · 10월 15일 장전',latestArticle={'title':TITLE,'href':f'market-{DATE}.html'},headline=TITLE,summary=SUMMARY)
for x in s['markets']:
 if x['id']=='KOSPI':
  v=prev['KOSPI'];x.update(value=num(v['closePrice']),changePercent=num(v['fluctuationsRatio']),open=num(v['openPrice']),high=num(v['highPrice']),low=num(v['lowPrice']),previousClose=6035.35,asOf='2026-10-14T15:30:00+09:00',asOfLabel='10월 14일 종가',flows=[{'label':'외국인','value':-11614},{'label':'기관','value':7876},{'label':'개인','value':-3203}])
 else:x.update(value=None,changePercent=None,open=None,high=None,low=None,previousClose=None,flows=[],asOf=CUTOFF,asOfLabel='장전 미개시')
s['stance']={'label':'물가 재가속과 반도체 매도','attack':5,'wait':45,'defense':50,'note':'6,000선 회복과 실제 외국인·프로그램 방향을 함께 봅니다.'}
s['checkpoints']=[{'label':x['stockName']+' NXT','value':x['closePrice']+'원 · '+x['fluctuationsRatio']+'%','detail':x['marketStatus']+' · '+x['localTradedAt'],'tone':'warning'} for x in nxt]+[{'label':'하나은행 USD/KRW','value':fx['closePrice']+'원','detail':fx['localTradedAt'],'tone':'warning'}]
s['changes']=[{'label':'KOSPI','before':'6,035.35','after':'6,008.81','meaning':'전일 외국인 현물 매도가 이어졌습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX -4.50% · AMD -5.73%','detail':'10월 14일 정규장','tone':'warning'},{'label':'미국 물가','metric':'CPI 3.7% · 전월 0.6%','detail':'9월 · BLS 10월 14일 발표','tone':'warning'},{'label':'설비 수요','metric':'ASML 매출 117억유로','detail':'3분기 공식 실적','tone':'info'}]
s['memory']=[{'label':'DDR5 16Gb · 10/14','value':'$60.10','change':'+0.33%'},{'label':'DDR4 16Gb · 10/14','value':'$83.611','change':'-0.30%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,800 / 5,600','pivot':'6,050','resistance':'6,200'},{'asset':'KODEX 레버리지','support':'79,070원','pivot':'81,100원','resistance':'86,295원'}]
s['scenarios']=[{'id':a,'label':b,'range':c,'summary':d,'conditions':e,'invalidation':f} for a,b,c,d,e,f in [('bull','강세 · 15%','KOSPI 6,050 초과~6,200','외국인·프로그램 동반 회복',['6,050 초과','외국인 순매수','프로그램 순매수'],'6,050 재이탈'),('base','기본 · 45%','KOSPI 5,800~6,050','물가 충격을 소화하는 구간',['5,800 이상','6,050 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 외국인 매도 확대'),('bear','약세 · 40%','KOSPI 5,600~5,800 미만','동반 매도와 지지 이탈',['5,800 미만','외국인 순매도','프로그램 순매도'],'5,800 회복')]]
s['events']=[{'time':'10월 15일 15:00 KST','name':'TSMC 3분기 실적 설명회','path':'첨단공정·패키징·설비투자 전망'},{'time':'10월 15일 21:30 KST','name':'미국 9월 PPI','path':'다음 한국장 금리·환율'}]
s['checklist']=[{'id':'support','label':'5,800 방어'},{'id':'rebound','label':'6,050 회복과 수급 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=prev['KOSPI' if x['id']=='KOSPI' else '122630'];levels=[5800,6050,6200] if x['id']=='KOSPI' else [79070,81100,86295];x.update(asOf='2026-10-14T15:30:00+09:00',asOfLabel='10월 14일 정규장 종가',points=[{'label':a,'value':num(v[b])} for a,b in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월 14일 확정 일봉과 10월 15일 장전 분석 기준선입니다.'
dump('assets/data/market-dashboard-'+SID+'.json',s);dump('assets/data/market-dashboard-latest.json',s)
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 {NOW}, 데이터 최종 확인 {CUTOFF}, 한국 장전.\n- 직전 KOSPI 6,008.81(-0.44%), KODEX 81,100원(-1.06%). 외국인 -11,614억원, 기관 +7,876억원, 프로그램 +3억원.\n- 핵심 CPI 3.7%와 미국 반도체 동반 하락. ASML 실적·DDR5 현물은 반대 근거. 기존 CXMT/ADR 반영분 중복 제외.\n- 다음 일정 오늘 15:00 TSMC, 21:30 PPI.\n- 기본 5,800~6,050(45%), 강세 6,050 초과~6,200(15%), 약세 5,600~5,800 미만(40%). 대응 5/45/50.\n- 보고서 reports/{DATE}.md, 취재 research/notes/{DATE}.md, 대시보드 assets/data/market-dashboard-{SID}.json, 차트 charts/us_yield_spreads_*_{DATE}.png.\n- 직전 기본 범위는 적중했으나 외국인 매도 조건은 이탈. 정확 시각 앵커 미확보로 조건 미검증.\n- 누적 평가 갱신 실패: 기존 2026-09-21 보고서 해시 불일치. 새 계약은 최종 조회 뒤 봉인. 스킬 전용 검증기는 없음(SKIP).\n')
dump('research/evidence/'+DATE+'/prepared.json',{'snapshotId':SID,'article':URL,'preparedAt':NOW})
print(SID,NOW)
