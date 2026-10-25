"""10월 26일 검증 자료로 작성한 발행 준비물. 최종 시세는 별도 봉인한다."""
import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-26';OLD='2026-10-23';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='반도체 반등에도 금리·유가 부담…KOSPI는 회복 지속 시험'
SUMMARY='미국 반도체 ETF가 소폭 반등했지만 종목별 흐름은 갈렸습니다. 금요일 저점에서 회복한 KOSPI는 FOMC를 앞두고 5,550선 유지와 매수 지속성을 시험합니다.'
IMAGE='market-2026-10-26-chips-rates-1200x630.png';ALT='밝은 반도체 공장 앞 메모리 칩과 투명한 호박색 금리 기둥';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261023\|([^"\s]+)',base64.b64decode(ev(k+'-fchart.raw')['raw'])).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==5550.30 and L['close']==67415
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(ev('after-'+k+'.raw')['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f"|{k}|{c:,.2f}|{(c/d['meta']['regularMarketPrice']-1)*100:+.2f}%|{at}|")
sources=[('SK하이닉스 솔리다임 발표','https://news.skhynix.com/en/fact-12/'),('SEC 6-K','https://www.sec.gov/Archives/edgar/data/2120882/000119312526429184/d159239d6k.htm'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('미 재무부',ev('Treasury.raw')['url']),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉',ev('KOSPI-fchart.raw')['url']),('FOMC','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),('BEA 일정','https://www.bea.gov/news/schedule'),('Microsoft IR','https://www.microsoft.com/en-us/investor/default'),('Amazon 실적 일정','https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report'),('FRED 금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
notes='''# 2026-10-26 취재 노트

08:00 KST 시작. 정상 거래일: Naver KOSPI basic PREOPEN·오늘 NXT OPEN 실거래량 확인. 공식 휴장목록 직접 획득은 미확인. 과거 STATE는 현재 시세 원천으로 사용하지 않음.

## 이슈 레이더
|후보|점수|검증 사실·전달 경로·경계|
|---|---:|---|
|금요일 반도체 반등과 종목 차별화|12|SOXX+0.53 SMH+0.74 MU+2.46 AMD+1.74%, NVDA-0.59 AVGO-0.48%. 금요일 미국 정규장, 전일 한국반등과 독립호재 중복합산 금지|
|유가·금리 재상승|12|Treasury10/23 3M4.22 2Y4.69 10Y5.00. 이란 긴장 보도, 연속선물 롤·오늘최근값과 금요일 결제 구분|
|FOMC·GDP/PCE 집중|13|Fed10/27~28ET, BEA 최신10/25갱신 일정 GDP·소득소비 모두10/29 08:30ET. 기존10/30 PCE 추정 배제|
|솔리다임 IPO검토중단|13|회사10/23·SEC6K 원문 일치. preIPO·IPO 검토중단, 성장투자필요 유지. 청산·투자철회·5조원확정조달실패로 표현 금지. 한국금요일 반영분|
|빅테크 실적|10|MS IR10/28ET·Amazon 공식10/29ET 발표예정. 미래 CAPEX·현금흐름 평가 변수. 아직 결과 없음|
|DRAM현물 차별화|9|10/23 18:10GMT+8 DDR5 61.267 +0.27%,DDR4 82.87 -0.30%. HBM가격으로 확대금지|
|공급계약·생산능력 선점|4|주말·금요일 검색의 NVIDIA TSMC3nm요청 보도는 회사원문 미확보, 확정계약으로 쓰지 않음|
|강제청산·증자·블록딜·규제|4|폭넓은 검색에서 직접확정할 새 지배사건 미확보. 공개 비사건 생략|

## 한국 시장·회고
10/23 KOSPI5403.17/5550.30/5305.98/5550.30(+0.30%), KODEX64005/67415/61145/67415(+0.97%),24520732주. fchart 최신과 basic/ETF가격 교차. KOSPI price API는10/22까지라 최신 종가로 사용금지. 전망 기본5350~5550은0.30p상회, 강세범위 종가이나 장중5305.98로 약세범위도 통과. 수급exact앵커 미확보로 인과검증 보류. 최종프로그램·시장폭·선물·투자주체 정본묶음 미확인,0채우지 않음.
Meta투자부담·솔리다임공시·미국목요일급락은 금요일한국에 반영된 재료. 오늘 독립추가충격으로 합산금지. 금요일미국반도체회복강도와 오늘환율/NXT/선물 반응을 별도 관찰.
HBM·서버DRAM·RDIMM·NAND/eSSD 신규계약 단가·물량 미확인. 공개계약8월·모듈10/12는 최신값아님. 메모리수요와기업자금조달/주가평가분리.
FRED10/23금리차10Y2Y0.31·10Y3M0.78%p, 개별FRED금리10/22시차. Treasury동일10/23 4.22/4.69/5.00사용. 새밝은반도체·금리이미지생성.
누적평가 기존9/21reportSha256불일치로 중단, 오래된 적중률 미사용·활성가설없음. 시간외는10/24KST마지막유효봉으로 주말최신거래이며 월요일실시간아님.
'''
write('research/notes/'+DATE+'.md',notes+'\n'+'\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n')
body='''<p>금요일 반도체주는 급락을 잠시 멈췄지만 회복 속도는 달랐습니다. 미국 23일 정규장에서 SOXX는 0.53%, SMH는 0.74% 올랐습니다. Micron과 AMD는 반등했지만 Nvidia와 Broadcom은 하락했습니다. 오늘 한국장은 업종 전체의 강한 반등을 기대하기보다 금요일 되찾은 가격을 지킬 수 있는지부터 확인해야 합니다.</p>
<h2>낙폭을 줄인 반도체, 여전히 높은 자금 비용</h2><p>Micron은 2.46%, AMD는 1.74% 올랐습니다. 반면 Nvidia는 0.59%, Broadcom은 0.48% 내렸습니다. QQQ는 0.01%, TQQQ는 0.20% 하락했습니다. 전날 급락을 되돌리는 힘이 일부 종목에 머물렀습니다. <a href="https://finance.yahoo.com/quote/SOXX/">미국 시세</a></p>
<p>미 재무부의 23일 금리는 2년물 4.69%, 10년물 5.00%입니다. 전날보다 각각 4bp 높습니다. 3개월물은 4.22%입니다. 이란을 둘러싼 긴장과 높은 유가는 기업 비용과 물가 부담을 키웁니다. AI 설비 주문이 늘더라도 높은 금리가 이어지면 투자금을 조달하고 회수하는 부담은 남습니다. <a href="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&amp;field_tdr_date_value=2026">미 재무부</a></p>
<h2>솔리다임은 IPO 검토를 멈췄지만 투자는 필요하다</h2><p>SK하이닉스는 23일 솔리다임의 상장 전 자금 조달과 IPO 검토를 중단했다고 밝혔습니다. 시장 여건과 주가 흐름을 고려한 결정입니다. 회사는 미국 생산시설 확충과 성장 투자 필요성은 유지된다고 설명했습니다. 지분 희석 우려가 줄어드는 측면과 대체 자금 조달을 고민해야 하는 측면을 함께 봐야 합니다. <a href="https://news.skhynix.com/en/fact-12/">SK하이닉스 발표</a></p>
<p>이 발표와 AI 투자비 부담은 금요일 한국장에서도 알려진 재료입니다. 국내 하락과 뒤이은 미국 움직임에 같은 악재를 다시 더해서는 안 됩니다. 오늘은 삼성전자·SK하이닉스 가격과 외국인 매수가 회복을 이어가는지가 관건입니다.</p>
<h2>DDR5 가격 지지와 DDR4 약세가 갈린다</h2><p>23일 대만시간 오후 6시 10분 기준 DDR5 16Gb 현물 평균은 61.267달러로 0.27% 올랐습니다. DDR4 16Gb는 82.87달러로 0.30% 내렸습니다. 메모리 전체의 수급을 하나의 방향으로 묶기 어렵습니다. 이 현물 가격을 HBM이나 서버 메모리 계약 단가로 넓혀 읽을 수도 없습니다. <a href="https://www.trendforce.com/price/dram/dram_spot">TrendForce</a></p>
<h2>5,550선 회복이 하루짜리로 끝나는가</h2><p>금요일 KOSPI는 5,403.17로 출발해 5,305.98까지 밀렸다가 당일 고점인 5,550.30으로 마쳤습니다. 종가는 0.30% 올랐지만 장중 진폭은 컸습니다. KODEX 레버리지도 61,145원까지 하락한 뒤 67,415원으로 회복했습니다. 종가 상승만으로 매도 압력이 사라졌다고 판단하기는 이릅니다.</p>
<p>오늘 기본 종가 범위는 5,400~5,600(50%)으로 봅니다. 외국인·프로그램 매수와 함께 5,600선을 넘기는 강세 범위는 5,600 초과~5,750(25%), 5,400선 아래에서 매도가 이어지는 약세 범위는 5,200~5,400 미만(25%)입니다. 5,600선 재이탈은 강세 판단을, 5,400선 회복은 약세 판단을 무효로 만듭니다. 범위를 벗어나는 변동도 가능합니다.</p>
<p>KODEX 레버리지는 금요일 시가 64,005원을 첫 지지, 종가 67,415원을 반등 유지 기준, 목요일 고점 72,300원을 저항으로 봅니다. 64,005원을 밑돌고 회복하지 못하면 반등 지속 판단을 접습니다. 금요일 저점 61,145원은 그 아래의 추가 확인선입니다.</p>
<h2>이번 주는 FOMC와 실적, GDP·PCE가 겹친다</h2><p>FOMC는 미국시간 27~28일 열립니다. Microsoft는 미국시간 28일, Amazon은 29일 실적을 발표할 예정입니다. AI 매출 증가가 설비 투자와 현금흐름 부담을 얼마나 감당하는지가 관심사입니다. <a href="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm">연준 일정</a> · <a href="https://www.microsoft.com/en-us/investor/default">Microsoft IR</a> · <a href="https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report">Amazon 일정</a></p>
<p>한국시간 29일 오후 9시 30분에는 미국 3분기 GDP 속보치와 9월 개인소득·소비가 함께 발표됩니다. PCE 물가가 포함된 일정입니다. 주 초의 반등이 이 발표들을 앞둔 포지션 조정으로 흔들릴 수 있어 개장 직후와 오전 10시 이후의 매수 지속성을 나눠 볼 필요가 있습니다. <a href="https://www.bea.gov/news/schedule">BEA 발표 일정</a></p>'''
write('research/evidence/'+DATE+'/body.html',body)
report=f'''# {DATE} KOSPI·KODEX 장전 리서치

작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전. 미국10/23 정규장·10/24KST 시간외 종료. 원천 지연 가능.

## 핵심 결론
{SUMMARY} 기본5400~5600(50%),강세5600초과~5750(25%),약세5200~5400미만(25%). 공격20·관망55·방어25. 90% 장중포락5050~5900. 수동 조건부 판단.

## 밤사이 시장 지배 이슈
반도체 회복 차별화·유가/금리 부담·FOMC/빅테크실적. 솔리다임 IPO검토중단과투자유지는별개. 금요일한국에반영된Meta·솔리다임·미국목요일매도 중복합산금지. 후보8건과제외경계는취재노트.

## 한국 시장·회고
10/23 KOSPI OHLC5403.17/5550.30/5305.98/5550.30(+0.30%), KODEX64005/67415/61145/67415(+0.97%),24520732주. KOSPI price API10/22지연제외, fchart/basic/ETF일봉교차. 이전기본5350~5550은0.30p상회·강세종가. 장중약세범위통과,수급조건미검증. 확정수급·프로그램·시장폭·선물정본묶음미확인.

## 메모리 수급
10/23 18:10GMT+8 DDR5 61.267달러+0.27%,DDR4 82.87달러-0.30%. HBM·서버DRAM·RDIMM·NAND·eSSD 신규계약단가/물량미확인. 현물과투자/주가분리. 공개계약8월·모듈10/12 최신값으로사용안함.

## 미국 정규장
|종목|10/23종가 USD|등락|
|---|---:|---:|
{ustable}
10/23 16ET=10/24 05KST. 원문 OHLC·종가위치는각yahoo JSON보존.

## 미국 시간외
|종목|USD|종가대비|시각 KST|
|---|---:|---:|---|
'''+ '\n'.join(after)+f'''
주말 이전 마지막 유효봉. 월요일시간외가격아님.

## 달러/원·선물·NXT
FAST_TABLE
연속선물 최근거래값, 계약월롤로 금요일결제대비수익률미계산. 하나고시·NXT/KRX구분.

## 국채·캘린더
Treasury10/23 3M4.22·2Y4.69·10Y5.00%. 2Y/10Y전일대비+4bp. FRED10/23금리차0.31/0.78%p. 개별금리10/22와혼합금지.
FOMC10/27~28ET(결정10/29 03KST), Microsoft10/28ET·Amazon10/29ET실적예정. BEA10/29 08:30ET=21:30KST GDP·소득소비/PCE동시. 중국PMI·한국기업실적 정확시각미확인,추정안함.
![90일](../charts/us_yield_spreads_90d_{DATE}.png)
![2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 시나리오·무효화
강세25%5600초과~5750:15:20지수>5600 AND 외국인>0 AND 프로그램>0,5600재이탈무효.
기본50%5400~5600:지수>=5400 AND <=5600 AND 외국인>=-8000억원,범위이탈·매도확대무효.
약세25%5200~5400미만:지수<5400 AND 외국인<0 AND 프로그램<0,5400회복무효.
KOSPI5400/5550/5600,KODEX64005/67415/72300.64005이탈미회복반등무효.09:30·10시·14시·15:20각각관찰. 한시점순매수지속단정금지.

## 출처
원문수집시각·해시는 research/evidence/{DATE}/. 누적평가기기존9/21해시불일치·활성가설없음.
'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
# 기존 사이트의 검증된 기사·목록 마크업만 재사용한다.
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index('s=prior;s.update')]
tail=tail.replace("oldimage='market-2026-10-19-memory-credit-1200x630.png'","oldimage='market-2026-10-23-ai-cash-oil-1200x630.png'")
for a,b in [('2026.10.20','2026.10.26'),('2026.10.19','2026.10.23'),('2026-10-19','2026-10-23'),('10월 19일','10월 23일')]:tail=tail.replace(a,b)
aftertable='\n'.join(after)
exec(tail)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(snapshotId='20261026-prepared',generatedAt=NOW,asOf=NOW,asOfDisplay=NOW,sourceLabel='미국10월23일 정규장·국내10월23일 종가·10월26일 장전',headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'})
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='확정값 미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=.30,open=K['open'],high=K['high'],low=K['low'],previousClose=5533.77,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월23일 정규장 종가')
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'최종 묶음 검증 보류'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'반등 지속과 수급 확인','attack':20,'wait':55,'defense':25,'note':'반도체 회복이 종목별로 갈렸습니다. 높은 금리와 유가 속에서 매수 지속을 봅니다.'}
s['changes']=[{'label':'KOSPI','before':'5,533.77','after':'5,550.30','meaning':'금요일 저점에서 회복해 당일 고점으로 마쳤습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX +0.53% · SMH +0.74%','detail':'10월23일 정규장·종목별 차별화','tone':'warning'},{'label':'자금 비용','metric':'미 10년물 5.00%','detail':'높은 유가·금리가 투자 부담을 남깁니다.','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/23','value':'$61.267','change':'+0.27%'},{'label':'DDR4 16Gb · 10/23','value':'$82.87','change':'-0.30%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,400','pivot':'5,550','resistance':'5,600'},{'asset':'KODEX 레버리지','support':'64,005원','pivot':'67,415원','resistance':'72,300원'}]
s['scenarios']=[{'id':k,'label':label,'range':ran,'summary':summ,'conditions':cond,'invalidation':inv} for k,label,ran,summ,cond,inv in [('bull','강세 · 25%','KOSPI 5,600 초과~5,750','매수가 동행하는 회복',['5,600 초과','외국인 순매수','프로그램 순매수'],'5,600 재이탈'),('base','기본 · 50%','KOSPI 5,400~5,600','반등 지속력 시험',['5,400 이상','5,600 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 매도 확대'),('bear','약세 · 25%','KOSPI 5,200~5,400 미만','하단 지지 실패',['5,400 미만','외국인 순매도','프로그램 순매도'],'5,400 회복')]]
s['events']=[{'time':'10월27~28일 ET','name':'FOMC','path':'금리·자금조달'},{'time':'10월28일 ET','name':'Microsoft 실적','path':'AI 수요·현금흐름'},{'time':'10월29일 21:30 KST','name':'GDP·개인소득소비/PCE','path':'성장·물가'},{'time':'10월29일 ET','name':'Amazon 실적','path':'클라우드·AI 투자'}]
s['checklist']=[{'id':'support','label':'5,400선 방어'},{'id':'rebound','label':'5,600선 회복과 외국인·프로그램 매수 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5400,5550,5600] if x['id']=='KOSPI' else [64005,67415,72300];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월23일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월23일 확정 일봉과 10월26일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s);dump('research/evidence/'+DATE+'/prepared.json',{'title':TITLE,'summary':SUMMARY,'image':IMAGE,'asOf':NOW,'imageMode':'built-in imagegen'})
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5550.30(+0.30%),KODEX67415(+0.97%). 최종 수급 묶음 미확인.\n- 반도체 회복 차별화·유가/금리 부담. 솔리다임·Meta 전일한국반영분 중복가산제외.\n- 다음 FOMC10/27~28ET·MS10/28ET·GDP/PCE10/29 21:30KST·Amazon10/29ET.\n- 기본5400~5600(50%),강세5600초과~5750(25%),약세5200~5400미만(25%),대응20/55/25.\n- 보고서 reports/{DATE}.md,취재 research/notes/{DATE}.md,차트 charts/us_yield_spreads_*_{DATE}.png.\n- 이전기본0.30p상회·강세종가,장중약세범위통과,수급exact앵커미확보. 누적기존9/21해시불일치.\n')
for page in ['index.html','articles/index.html','articles/market.html']:
 t=read(page)
 def card(m):
  if 'market-'+DATE+'.html' in m[0]:
   c=re.sub(r'2026\.10\.\d{2}','2026.10.26',m[0]);c=re.sub(r'10월 \d{1,2}일','10월 26일',c);return re.sub(r'2026-10-\d{2}T[^"< ]+',NOW,c)
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 t=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,t,flags=re.S)
 if page=='index.html':t=t.replace('market-2026-10-23-ai-cash-oil-1200x630.png',IMAGE)
 if page=='articles/market.html':t=t.replace('전일 저점 방어와 매수 지속','반등 지속과 금리·유가 부담')
 write(page,t)
t=read('sitemap.xml')
for u in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:t=re.sub(r'(<loc>'+re.escape(u)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+DATE,t)
write('sitemap.xml',t)
print('prepared',NOW)
