"""검증 원문을 이용한 10월 27일 장전 발행 준비. 최종 시세는 별도 봉인."""
import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-27';OLD='2026-10-26';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='AI 자금 조달에 반도체 동반 반등…KOSPI는 5,500선 회복 시험'
SUMMARY='Meta의 공모와 SpaceX의 GPU 금융 약정이 AI 투자 지속 기대를 높였습니다. 미국 반도체주가 동반 상승한 가운데 KOSPI는 5,500선 회복과 국내 매수 동행을 시험합니다.'
IMAGE='market-2026-10-27-ai-financing-1200x630.png';ALT='밝은 서버 시설 앞 보라색 웨이퍼와 GPU, 산호색 리본으로 묶인 금융 서류';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261026\|([^"\s]+)',base64.b64decode(ev(k+'-fchart.raw')['raw'])).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==5469.47 and L['close']==65475
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(ev('after-'+k+'.raw')['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f"|{k}|{c:,.2f}|{(c/d['meta']['regularMarketPrice']-1)*100:+.2f}%|{at}|")
aftertable='\n'.join(after)
sources=[('Meta会社発表','https://finance.yahoo.com/markets/stocks/articles/meta-announces-launch-offering-depositary-105800284.html'),('SpaceX 금융 약정','https://ir.spacex.com/updates/releases-details/2026/SPACEX-SECURES-40-BILLION-IN-THE-LARGEST-GPU-FINANCING-EVER-2026-EnDqGhTAB3/default.aspx'),('Anthropic S-1','https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/anthropicpbc-sx1.htm'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('미 재무부',ev('Treasury.raw')['url']),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉',ev('KOSPI-fchart.raw')['url']),('FOMC','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),('BEA 일정','https://www.bea.gov/news/schedule'),('Microsoft IR','https://www.microsoft.com/en-us/investor/default'),('Amazon 실적 일정','https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report')]
sources[0]=('Meta 회사 발표',sources[0][1])
notes='''# 2026-10-27 취재 노트

자동화 시작 07:56대 KST. 예약 조사 시작 08:00 이전에는 규칙 확인·수집 환경 준비. 최초 원천 수집 07:58:44, 최종 발행전 재조회 별도 기록. 휴장 일반일 아님: 당일 NXT OPEN 거래량·거래일로 최종 검증.

## 이슈 레이더
|후보|점수|확정 범위·전달 경로·경계|
|---|---:|---|
|Meta 공모·추가 ATM 계획|13|회사 배포 보도자료 직접 보존. 350억달러 공모 개시(보통주225억·전환우선주125억),600억ATM 향후계획. 납입완료 아님. NVDA/AMD/AVGO 최대50억 관심표명은 비구속적. 한국10/26장 이후 미국발표|
|SpaceX GPU 금융|13|기업 발표 검색원문과 SEC8K 검색원문 일치. Apollo 관리법인과 약400억달러 금융리스 구속력약정, 종결조건·연말예정·2027상반기장비인도. 즉시집행·매출확정 아님. 직접요청403 기록|
|Anthropic S1 공개|11|SEC 정본 URL·회사발표 경로, AP/Reuters/axios 교차. IPO 등록 공개, 가격·주식수 미정. 2조달러 확정가치·조달성공으로 쓰지 않음. 직접SEC403, 회사응답 본문 미검출로 구체손실액 인용보류|
|반도체 동반상승|12|SOXX+2.85 SMH+2.74 NVDA+2.39 AMD+2.80 MU+2.98 AVGO+2.33. 일봉 원문·시간외 별도|
|FOMC·MS/Amazon·GDP/PCE|11|FOMC10/27~28ET·BEA10/29 08:30ET GDP·개인소득소비 동시. 기존 기대 일정은 새 충격으로 가산않음|
|DRAM차별화|9|10/26 18:10GMT+8 DDR5 61.333 +0.11%,DDR4 82.623 -0.30%. HBM·서버장기계약으로 일반화 금지|
|금리·유가|8|Treasury10/26 3M4.22 2Y4.68 10Y5.00. FRED금리차0.32/0.78. 선물가격최종조회·롤수익률계산보류|
|청산·블록딜·규제·공급계약|4|검색했으나 공시확정 새 시장지배 사건 미확보. 공개 비사건 생략. 공급업체의 고객출자는 주문확정으로 해석금지|

## 사실 경계·직전 전망
10/26 KOSPI5499.05/5565.67/5455.11/5469.47(-1.46%), KODEX66075/67985/65115/65475(-2.88%),18823219주. fchart와basic/ETF일봉 교차. 직전기본5400~5600 안·장중포락 안. 전일회복지속이실패한조건은 외국인/프로그램 exact앵커없어 인과판정 보류. 최종수급묶음 미검증,부분수치·0채움안함.
지난주 Meta구조개편·기존CAPEX부담·솔리다임 검토중단은 이미 한국 반영. 오늘 신규350억공모 개시·SpaceX약정·S1공개만 신규사건. 미국반도체가격반응과그사건을독립호재로합산금지.
HBM·서버DRAM·RDIMM·NAND/eSSD 신규계약단가·물량 미확인. NAND현물10/19·계약8월은 오래된자료로별도. 금리차는동일10/26 관측. SK하이닉스10/27실적일정은 보조매체/커뮤니티단서만으로 정확시각확정불가,공개일정표생략.
## 집필·윤문·썸네일
중심명제: AI 자금조달이 칩수요기대를지지하나 실제납입·수익성은미확정. 국내5500회복·수급동행조건. write-finished-manuscript 집필/퇴고후 humanize-korean 사실고정윤문. 밝은라벤더·청록 서버시설과웨이퍼·금융서류,회복과경계. built-in imagegen 새이미지·이전참조없음.
'''
write('research/notes/'+DATE+'.md',notes+'\n'+'\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n')
body='''<p>AI 기업들이 투자금을 마련할 새 통로를 열자 미국 반도체주가 함께 올랐습니다. Meta는 대규모 공모를 시작했고 SpaceX는 GPU 금융 약정을 발표했습니다. 월요일 하락한 한국장에는 반등을 시도할 재료가 생겼지만, KOSPI가 5,500선을 되찾은 뒤 매수를 이어갈 수 있는지가 관건입니다.</p>
<h2>Meta의 공모와 SpaceX의 GPU 금융이 바꾼 기대</h2><p>Meta는 26일 약 350억달러 규모의 공모를 시작했습니다. 보통주 225억달러와 전환우선주 관련 증권 125억달러로 구성됩니다. 향후 약 600억달러의 시장가 매각 프로그램도 계획하고 있습니다. 보통주 선도매매분의 자금은 향후 정산 때 들어오며 추가 매각의 시기와 조건도 정해지지 않았습니다. <a href="https://finance.yahoo.com/markets/stocks/articles/meta-announces-launch-offering-depositary-105800284.html">Meta 회사 발표</a></p>
<p>Nvidia·AMD·Broadcom이 합계 최대 50억달러의 보통주 매입에 관심을 보였다는 점도 눈에 띕니다. 구매 의향은 구속력 있는 약정이 아닙니다. 칩 공급업체가 고객의 자금 조달에 참여할 수 있다는 기대가 생겼지만 실제 주문과 투자금 회수는 앞으로의 실적에 달려 있습니다.</p>
<p>SpaceX는 Apollo가 관리하는 법인과 약 400억달러의 GPU 금융리스에 들어가기 위한 구속력 있는 약정을 발표했습니다. 종결 조건을 충족하면 연말 이전 거래를 마치고 2027년 상반기 장비 인도에 따라 리스가 시작될 예정입니다. Nvidia의 차세대 Vera Rubin 칩을 사용할 계획입니다. 금융 약정은 투자 지속에 도움이 되지만 장비 인도와 매출 발생까지는 시간이 남아 있습니다. <a href="https://ir.spacex.com/updates/releases-details/2026/SPACEX-SECURES-40-BILLION-IN-THE-LARGEST-GPU-FINANCING-EVER-2026-EnDqGhTAB3/default.aspx">SpaceX 발표</a></p>
<p>Anthropic도 IPO 등록 서류를 공개했습니다. 공모가격과 주식 수는 아직 정해지지 않았습니다. AI 기업의 자본시장 접근이 넓어지면 설비 투자를 이어갈 여지가 커집니다. 반대로 대형 조달이 잇따르면 투자자의 자금과 관심을 나눠 가져야 합니다. <a href="https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/anthropicpbc-sx1.htm">Anthropic S-1</a></p>
<h2>반도체주는 함께 올랐고 메모리 현물은 갈렸다</h2><p>미국 26일 정규장에서 SOXX는 2.85%, SMH는 2.74% 올랐습니다. Nvidia 2.39%, AMD 2.80%, Micron 2.98%, Broadcom 2.33%로 주요 종목이 동반 상승했습니다. QQQ는 1.11%, TQQQ는 3.23% 올랐습니다. 자금 조달 소식이 투자 지속 기대를 높인 가운데 반도체 매수가 업종 전반으로 퍼졌습니다. <a href="https://finance.yahoo.com/quote/SOXX/">미국 시세</a></p>
<p>26일 대만시간 오후 6시 10분 기준 DDR5 16Gb 현물 평균은 61.333달러로 0.11% 올랐고 DDR4 16Gb는 82.623달러로 0.30% 내렸습니다. 제품별 가격 차이가 이어지고 있습니다. 이 현물 가격만으로 HBM과 서버 메모리 장기 계약의 수익성을 판단할 수는 없습니다. <a href="https://www.trendforce.com/price/dram/dram_spot">TrendForce</a></p>
<h2>KOSPI 5,500선 회복에 매수가 붙는가</h2><p>월요일 KOSPI는 5,565.67까지 올랐다가 5,469.47로 마쳐 1.46% 하락했습니다. KODEX 레버리지도 67,985원에서 밀려 65,475원으로 끝났습니다. 장중 반등 뒤 매도가 다시 우세해진 만큼 오늘은 개장 상승 폭보다 오전 10시 이후 삼성전자·SK하이닉스 가격과 외국인·프로그램 매수의 동행을 봐야 합니다.</p>
<p>오늘 기본 종가 범위는 5,400~5,600(50%)으로 봅니다. 5,600선을 넘고 외국인·프로그램 매수가 동행하는 강세 범위는 5,600 초과~5,750(30%), 5,400선 아래에서 매도가 이어지는 약세 범위는 5,200~5,400 미만(20%)입니다. 5,600선 재이탈은 강세 판단을, 5,400선 회복은 약세 판단을 무효로 만듭니다. 예상 범위를 벗어나는 변동도 가능합니다.</p>
<p>KODEX 레버리지는 전일 저점 65,115원을 첫 지지, 시가 66,075원을 반등 기준, 고점 67,985원을 저항으로 봅니다. 65,115원 아래에서 회복하지 못하면 반등 지속 판단을 접습니다. 지난주 솔리다임 소식과 기존 AI 투자비 부담에 더해 오늘 새로 발표된 금융 약정이 국내 주가에 얼마나 힘을 보태는지 확인할 차례입니다.</p>
<h2>FOMC 앞에서 5%인 미국 장기금리</h2><p>미 재무부의 26일 금리는 3개월물 4.22%, 2년물 4.68%, 10년물 5.00%입니다. 2년물은 전 거래일보다 1bp 낮아졌지만 장기금리는 높은 수준에 머물렀습니다. 자금 조달 규모가 커져도 투자비 회수 부담은 남습니다. <a href="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&amp;field_tdr_date_value=2026">미 재무부</a></p>
<p>FOMC는 미국시간 27~28일 열리며 결정은 한국시간 29일 오전 3시에 나옵니다. Microsoft는 미국시간 28일, Amazon은 29일 실적을 발표할 예정입니다. 한국시간 29일 오후 9시 30분에는 GDP 속보치와 PCE 물가를 포함한 개인소득·소비가 함께 발표됩니다. 금리 경로와 AI 투자 수익성이 짧은 기간에 다시 평가받을 일정입니다. <a href="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm">연준</a> · <a href="https://www.bea.gov/news/schedule">BEA</a></p>'''
write('research/evidence/'+DATE+'/body.html',body)
report=f'''# {DATE} KOSPI·KODEX 장전 리서치

작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전. 미국10/26 정규장·10/27 KST 시간외 분리. 원천 지연 가능.

## 핵심 결론
{SUMMARY} 기본5400~5600(50%),강세5600초과~5750(30%),약세5200~5400미만(20%). 공격30·관망50·방어20. 90% 장중포락5100~5900. 수동 조건부 판단.

## 밤사이 지배 이슈
Meta350억달러 공모개시·600억ATM계획(납입완료아님), SpaceX400억GPU리스 구속력약정(종결조건), Anthropic IPO등록공개(가격미정). 기업발표·SEC·보도 경계와 레이더8건 research/notes/{DATE}.md. 전일한국반영 Meta기존CAPEX·솔리다임중복제외. 사건과미국반도체가격반응독립합산금지.

## 국내 확정·회고
10/26 KOSPI5499.05/5565.67/5455.11/5469.47(-1.46%), KODEX66075/67985/65115/65475(-2.88%),18823219주. fchart와basic/ETF교차. 직전기본5400~5600내·포락내. 정확수급앵커미확보로지속성·인과판정보류. 최종현물·프로그램·시장폭·선물정본묶음미확인.

## 메모리
10/26 18:10GMT+8 DDR5 61.333달러+0.11%,DDR4 82.623달러-0.30%. HBM·서버DRAM·RDIMM·NAND/eSSD 신규계약단가·물량미확인. NAND현물10/19·공개계약8월은최신값으로사용안함. 수요·자금조달·주식평가분리.

## 미국 정규장
|종목|10/26종가 USD|등락|
|---|---:|---:|
{ustable}
10/26 16ET=10/27 05KST. OHLC·종가위치원문보존.

## 미국 시간외
|종목|USD|종가대비|시각 KST|
|---|---:|---:|---|
{aftertable}
시간외 최근 유효봉·정규종가와분리.

## 최종 환율·선물·NXT
FAST_TABLE
연속선물최근거래·롤수익률미계산. 하나고시·NXT/KRX구분.

## 국채·일정
Treasury10/26 3M4.22·2Y4.68·10Y5.00%. FRED동일10/26금리차0.32/0.78%p. 개별FRED10/23값혼합안함.
FOMC10/27~28ET·결정10/29 03KST, MS10/28ET·Amazon10/29ET실적. BEA10/29 08:30ET=21:30KST GDP·개인소득소비/PCE동시. 국내기업실적정확시각미확인.
![90일](../charts/us_yield_spreads_90d_{DATE}.png)
![2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 조건·무효화
강세30%5600초과~5750:15:20지수>5600 AND 외국인>0 AND 프로그램>0,5600재이탈무효.
기본50%5400~5600:지수>=5400 AND <=5600 AND 외국인>=-8000억원,범위이탈·매도확대무효.
약세20%5200~5400미만:지수<5400 AND 외국인<0 AND 프로그램<0,5400회복무효.
KOSPI5400/5500/5600,KODEX65115/66075/67985.65115이탈미회복반등무효.09:30·10시·14시·15:20별도관찰.

## 출처
'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
# 기존 검증된 사이트 마크업의 생성 부분만 사용한다.
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index('s=prior;s.update')]
tail=tail.replace("oldimage='market-2026-10-19-memory-credit-1200x630.png'","oldimage='market-2026-10-26-chips-rates-1200x630.png'")
for a,b in [('2026.10.20','2026.10.27'),('2026.10.19','2026.10.26'),('2026-10-19','2026-10-26'),('10월 19일','10월 26일')]:tail=tail.replace(a,b)
exec(tail)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(snapshotId='20261027-prepared',generatedAt=NOW,asOf=NOW,asOfDisplay=NOW,sourceLabel='미국10월26일 정규장·국내10월26일 종가·10월27일 장전',headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'})
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='확정값 미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=-1.46,open=K['open'],high=K['high'],low=K['low'],previousClose=5550.30,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월26일 정규장 종가')
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'최종 묶음 검증 보류'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'반등과 매수 동행 확인','attack':30,'wait':50,'defense':20,'note':'AI 자금 조달 소식에 미국 반도체가 동반 상승했습니다. 국내 매수 지속을 봅니다.'}
s['changes']=[{'label':'KOSPI','before':'5,550.30','after':'5,469.47','meaning':'월요일 장중 반등 뒤 다시 밀려 마쳤습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX +2.85% · SMH +2.74%','detail':'10월26일 정규장·주요 종목 동반상승','tone':'positive'},{'label':'AI 금융','metric':'Meta 공모 · SpaceX GPU 약정','detail':'투자 지속 기대와 자금 회수 부담','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/26','value':'$61.333','change':'+0.11%'},{'label':'DDR4 16Gb · 10/26','value':'$82.623','change':'-0.30%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,400','pivot':'5,500','resistance':'5,600'},{'asset':'KODEX 레버리지','support':'65,115원','pivot':'66,075원','resistance':'67,985원'}]
s['scenarios']=[{'id':k,'label':label,'range':ran,'summary':summ,'conditions':cond,'invalidation':inv} for k,label,ran,summ,cond,inv in [('bull','강세 · 30%','KOSPI 5,600 초과~5,750','매수가 동행하는 회복',['5,600 초과','외국인 순매수','프로그램 순매수'],'5,600 재이탈'),('base','기본 · 50%','KOSPI 5,400~5,600','반등 지속력 시험',['5,400 이상','5,600 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 매도 확대'),('bear','약세 · 20%','KOSPI 5,200~5,400 미만','하단 지지 실패',['5,400 미만','외국인 순매도','프로그램 순매도'],'5,400 회복')]]
s['events']=[{'time':'10월27~28일 ET','name':'FOMC','path':'금리·자금조달'},{'time':'10월28일 ET','name':'Microsoft 실적','path':'AI 수요·현금흐름'},{'time':'10월29일 21:30 KST','name':'GDP·개인소득소비/PCE','path':'성장·물가'},{'time':'10월29일 ET','name':'Amazon 실적','path':'클라우드·AI 투자'}]
s['checklist']=[{'id':'support','label':'5,400선 방어'},{'id':'rebound','label':'5,500선 회복과 외국인·프로그램 매수 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5400,5500,5600] if x['id']=='KOSPI' else [65115,66075,67985];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월26일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월26일 확정 일봉과 10월27일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s);dump('research/evidence/'+DATE+'/prepared.json',{'title':TITLE,'summary':SUMMARY,'image':IMAGE,'asOf':NOW,'imageMode':'built-in imagegen','prompt':'Bright lavender and turquoise AI server atrium, wafer, GPU and blank financing documents with coral ribbon; no text or logos.'})
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5469.47(-1.46%), KODEX65475(-2.88%). 최종 수급 묶음 미확인.\n- Meta공모·SpaceX GPU약정·Anthropic S1공개와 반도체동반상승. 기존Meta/솔리다임한국반영분중복제외.\n- 다음 FOMC10/27~28ET·MS10/28ET·GDP/PCE10/29 21:30KST·Amazon10/29ET.\n- 기본5400~5600(50%),강세5600초과~5750(30%),약세5200~5400미만(20%),대응30/50/20.\n- 보고서 reports/{DATE}.md,취재 research/notes/{DATE}.md,차트 charts/us_yield_spreads_*_{DATE}.png.\n- 직전기본범위내·장중포락내,수급exact앵커미확보. 누적기존9/21해시불일치.\n')
for page in ['index.html','articles/index.html','articles/market.html']:
 t=read(page)
 def card(m):
  if 'market-'+DATE+'.html' in m[0]:
   c=re.sub(r'2026\.10\.\d{2}','2026.10.27',m[0]);c=re.sub(r'10월 \d{1,2}일','10월 27일',c);return re.sub(r'2026-10-\d{2}T[^"< ]+',NOW,c)
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 t=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,t,flags=re.S)
 if page=='index.html':t=t.replace('market-2026-10-26-chips-rates-1200x630.png',IMAGE)
 if page=='articles/market.html':t=t.replace('반등 지속과 금리·유가 부담','AI 금융과 반도체 동반 반등')
 write(page,t)
t=read('sitemap.xml')
for u in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:t=re.sub(r'(<loc>'+re.escape(u)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+DATE,t)
write('sitemap.xml',t)
print('prepared',NOW)
