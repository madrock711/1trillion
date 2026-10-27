"""10월 28일 취재와 공개 원고를 분리해 준비한다. 최종 시세는 finalize.py에서 봉인."""
import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-28';OLD='2026-10-27';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='반도체 랠리 뒤 실적 시험대…KOSPI 5,700선과 SK하이닉스 발표 주목'
SUMMARY='미국 반도체주가 추가 상승했습니다. 전일 급등한 KOSPI는 오늘 SK하이닉스 실적과 매수 지속성을 시험하며, 밤사이에는 FOMC와 빅테크 실적이 이어집니다.'
IMAGE='market-2026-10-28-earnings-curtain-1200x630.png';ALT='아침 서울 풍경 앞 산호색 무대 커튼과 푸른 유리 발표대, 커튼 앞까지 이어진 흰 계단';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261027\|([^"\s]+)',base64.b64decode(ev(k+'-fchart.raw')['raw'])).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==5638.34 and L['close']==69955
assert float(ev('KOSPI-basic')['data']['closePrice'].replace(',',''))==K['close']
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(ev('after-'+k+'.raw')['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f"|{k}|{c:,.2f}|{(c/d['meta']['regularMarketPrice']-1)*100:+.2f}%|{at}|")
aftertable='\n'.join(after)
META='https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Announces-Pricing-of-Offering-of-Depositary-Shares-Representing-Series-A-Mandatory-Convertible-Preferred-Stock-and-Offering-of-Class-A-Common-Stock-in-Connection-with-Forward-Sale-Agreements/default.aspx'
SK='https://news.skhynix.com/en/q3-2026-earnings-conference-call-invitation/'
sources=[('SK하이닉스 실적 일정',SK),('Meta 공모 가격 확정',META),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('미 재무부',ev('Treasury.raw')['url']),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉',ev('KOSPI-fchart.raw')['url']),('FOMC','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),('BEA 일정','https://www.bea.gov/news/schedule'),('Microsoft IR','https://www.microsoft.com/en-us/investor/default'),('Amazon 실적 일정','https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report')]
notes='''# 2026-10-28 취재 노트

실제 조사 시작 08:01 KST 이후. 08:00 소급하지 않음. 1차 시세08:03대, 최종 재조회 별도. KRX PREOPEN·당일 NXT OPEN/거래량으로 오늘 정상거래 상태 확인. 사용자가 28일 글 미노출을 지적: 아직 발행 전임을 안내. 썸네일 반복 지적을 반영해 칩/웨이퍼/서버/서류/모래시계를 모두 배제하고 실적 공개를 상징하는 밝은 산호색 커튼·발표대·계단으로 신규 생성.

## 이슈 레이더
|후보|점수|확정 범위와 경계|
|---|---:|---|
|SK하이닉스 당일 실적|13|회사 뉴스룸 공식 초청장 웹 검색원문:10/28 09시 전 보도자료·09시 한영콜. 직접요청502. 수치·배당 확정 전이며 예상/보도는 실적으로 쓰지 않음|
|미국 반도체 추가랠리|13|10/27 SOXX+3.91 SMH+3.02 AMD+5.45 AVGO+4.00 NVDA+0.90 MU+2.77. 일봉원문·시간외 분리. 전일 한국반영 Anthropic/SpaceX 기대로 다시 독립호재 합산않음|
|Meta 공모증액·가격결정|12|회사원문 웹열람. 보통주250억·125억전환우선주=375억달러,기존350억보다25억증액. 보통주625달러. 600억ATM을 합친975억은 계획 포함,현금납입 아님. 회사페이지10/27·본문dateline10/26 혼재, 전일한국장반영가능성 표시. 납입10/29예정·보통주선도정산2027/11/19까지|
|FOMC·MS·GDP/PCE|12|연준/BEA원문. FOMC10/29 03시KST·MS미국28일·Amazon29일·GDP/PCE29일21:30. 기존예정 이벤트이며 방향확정 아님|
|전일국내급등·차익실현|11|KOSPI5638.34+3.09%,장중5737.61후반납. KODEX69955+6.84%. 주주환원미확정보도 전일반영·새 확정공시와구분|
|DRAM 현물 보합|8|10/27 18:10GMT+8 DDR5 61.333·DDR4 82.623 각보합. RDIMM2165 -0.92% 품목별차별화. HBM 신규계약 물량/단가미확인|
|금리·유가|9|Treasury10/27 3M4.22·2Y4.70·10Y4.99,금리차0.29/0.77. 전일대비2Y+2bp·10Y-1bp. FRED개별금리10/26과혼합차감금지|
|미국소비심리·비기술실적|6|CB원문이9월판으로남고10월보도91.7/전월수정84.2와기존81.9차이. 원문정정확인전핵심수치보류. Boeing실적하락·GM이전등은국내직접노출낮아보조|
|청산·블록딜·수출규제·대형계약|4|개방형검색·뉴스·기업원문검토. 새확정시장지배사건미확보. 공개비사건생략|

## 직전 전망과 데이터 한계
10/27 KOSPI5658.65/5737.61/5612.92/5638.34(+3.09%), KODEX69965/72745/69465/69955(+6.84%),20694302주. fchart와basic교차. 전일전망기본5400~5600초과·강세5600~5750내·경로5100~5900내. 오전급등을종가동등으로읽지않음. PREOPEN integration수급/프로그램0은거래전초기값이므로전일확정0으로쓰지않고null. exact앵커·최종수급정본미확보.
전일KOSPI+3.09%에AI금융·IPO·주주환원기대반영. 미국후행상승과ADR을별도충격으로모두합산금지. 신규가격반응·NXT·실적후조건만판단. HBM·서버DRAM·NAND/eSSD 신규단가/물량미확인. NAND표10/19·계약8월은오래된자료. 종목IR실적시간은공식일정외추정금지.

## 집필·윤문
중심명제: 미국추가반등이상방재료이나국내급등후실적확인이우선. write-finished-manuscript 집필·퇴고, humanize-korean 의미·사실고정최종윤문. 공개에는조사과정·레이더·미발견사건생략. 상위사건두개를제목/도입/새이미지에반영.
'''
write('research/notes/'+DATE+'.md',notes+'\n'+'\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n')
body=f'''<p>미국 반도체주가 하루 더 올랐습니다. 그러나 전일 3.09% 급등한 KOSPI에는 이미 AI 투자와 메모리 기업의 주주환원 기대가 들어와 있습니다. 오늘은 SK하이닉스의 실적 발표가 그 기대를 뒷받침하는지, 5,700선 부근에서 매수가 이어지는지를 시험합니다.</p>
<h2>오늘 아침 실적이 반등의 다음 조건을 정한다</h2><p>SK하이닉스는 오늘 오전 9시 전에 3분기 실적을 발표하고 9시에 설명회를 열 예정입니다. 매출과 영업이익뿐 아니라 HBM 출하, 고객 주문, 설비 투자와 현금흐름이 함께 중요합니다. 주주환원 확대를 기대하며 오른 가격은 실제 발표의 규모와 집행 조건에 다시 반응할 수 있습니다. <a href="{SK}">SK하이닉스 공식 일정</a></p>
<p>화요일 KOSPI는 5,658.65에 출발해 5,737.61까지 올랐지만 5,638.34로 마쳤습니다. KODEX 레버리지는 72,745원에서 밀려 69,955원으로 끝났습니다. 종가는 올랐어도 장중 고점에서 매물이 나온 만큼, 실적 발표 뒤 첫 상승보다 오전 10시 이후 매수의 지속성이 더 중요합니다.</p>
<h2>미국 반도체는 추가 상승, 국내 반영분은 따로 본다</h2><p>미국 27일 정규장에서 SOXX는 3.91%, SMH는 3.02% 올랐습니다. AMD가 5.45%, Broadcom이 4.00% 상승했고 Micron은 2.77%, Nvidia는 0.90% 올랐습니다. QQQ는 1.27%, TQQQ는 3.81% 상승했습니다. 주요 종목은 함께 올랐지만 상승 폭에는 차이가 있었습니다. <a href="https://finance.yahoo.com/quote/SOXX/">미국 시세</a></p>
<p>AI 기업의 자금 조달과 IPO 기대는 이미 전일 한국장 반등에도 작용했습니다. 미국의 뒤이은 상승을 같은 크기의 새 호재로 더하기보다, 오늘 삼성전자와 SK하이닉스가 실적 발표 후에도 상승분을 지키는지 봐야 합니다.</p>
<h2>Meta 공모는 커졌지만 현금 유입에는 시차가 있다</h2><p>Meta는 보통주 공모를 225억달러에서 250억달러로 늘리고 주당 가격을 625달러로 정했습니다. 125억달러 규모 전환우선주 관련 공모를 합하면 375억달러입니다. 여기에 향후 600억달러 시장가 매각 계획까지 더한 총액을 곧바로 확보한 현금으로 읽어서는 안 됩니다. 보통주 선도매매의 정산은 내년 11월까지 이어질 수 있습니다. 투자금 마련은 AI 설비 수요를 지지하지만 희석과 자금 회수 부담도 남깁니다. <a href="{META}">Meta 공모 가격 발표</a></p>
<h2>메모리 현물 보합과 높은 금리</h2><p>27일 대만시간 오후 6시 10분 기준 DDR5 16Gb 현물 평균은 61.333달러, DDR4 16Gb는 82.623달러로 모두 보합이었습니다. DDR5 RDIMM 32GB는 2,165달러로 0.92% 내렸습니다. 품목별 현물 흐름과 HBM 장기 계약의 수익성을 구분해 볼 시점입니다. <a href="https://www.trendforce.com/price/dram/dram_spot">TrendForce</a></p>
<p>미 재무부의 27일 금리는 3개월물 4.22%, 2년물 4.70%, 10년물 4.99%입니다. 전일보다 2년물은 2bp 올랐고 10년물은 1bp 내렸습니다. 장기금리가 여전히 5%에 가까워 대규모 AI 투자의 자금 비용 부담은 이어집니다. <a href="{ev('Treasury.raw')['url']}">미 재무부</a></p>
<h2>5,700선 회복에 수급이 붙는가</h2><p>기본 종가 범위는 5,600~5,800(50%)으로 봅니다. 지수가 이 범위에 있고 외국인 순매도가 8천억원을 넘지 않는 조건입니다. 5,800선을 넘으며 외국인·프로그램 매수가 동행하는 강세 범위는 5,800 초과~5,950(25%), 5,600선 아래에서 외국인·프로그램 매도가 겹치는 약세 범위는 5,400~5,600 미만(25%)입니다. 5,800선 재이탈은 강세 판단을, 5,600선 회복은 약세 판단을 무효로 만듭니다. 실적 내용에 따라 예상 범위 밖의 변동도 가능합니다.</p>
<p>KODEX 레버리지는 전일 저점 69,465원을 첫 지지, 종가 69,955원을 반등 기준, 고점 72,745원을 저항으로 봅니다. 69,465원을 밑돈 뒤 회복하지 못하면 전일 반등의 지속을 전제로 한 판단을 접습니다.</p>
<p>한국시간 내일 오전 3시에는 FOMC 결정이 나옵니다. Microsoft는 미국시간 28일, Amazon은 29일 실적을 발표하고, 내일 오후 9시 30분에는 미국 GDP 속보치와 PCE 물가를 포함한 개인소득·소비가 함께 나옵니다. 오늘 국내 실적을 통과하더라도 금리와 빅테크 투자 계획을 확인할 일정이 이어집니다. <a href="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm">연준</a> · <a href="https://www.bea.gov/news/schedule">BEA</a></p>'''
write('research/evidence/'+DATE+'/body.html',body)
report=f'''# {DATE} KOSPI·KODEX 장전 리서치

작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전. 미국10/27 정규장·10/28 KST 시간외 분리. 원천 지연 가능.

## 핵심 결론
{SUMMARY} 기본5600~5800(50%),강세5800초과~5950(25%),약세5400~5600미만(25%). 공격25·관망50·방어25. 90% 장중포락5250~6100. 수동 조건부 판단이며 대응점수는 확률과 별개.

## 밤사이 시장을 지배한 이슈
미국반도체추가상승·SK당일실적·Meta공모증액/가격결정·FOMC. 레이더9건과사실경계 research/notes/{DATE}.md. 이미한국반영AI금융·IPO·주주환원보도중복가산제외. Meta 375억공모+600억계획은975억즉시납입아님.

## 전일 대비 바뀐 변수와 유지 변수
SOXX+3.91%,SMH+3.02% 추가상승 신규 관측. 미국가격상승과그원인독립합산금지. 국내급등후고점반납·고금리·FOMC예정 유지. 당일SK실적수치발표전미확인,컨센서스를실적으로쓰지않음.

## 한국시장·KODEX 대시보드와 직전 전망
10/27 KOSPI5658.65/5737.61/5612.92/5638.34(+3.09%), KODEX69965/72745/69465/69955(+6.84%),20694302주. fchart와basic교차. 전일기본5400~5600초과·강세5600초과~5750내·장중포락내. final수급·exact앵커미확보로조건인과판정보류.

## 메모리 반도체 수급
10/27 18:10GMT+8 DDR5 61.333·DDR4 82.623 각보합. DDR5 RDIMM32GB2165달러-0.92%. HBM·서버DRAM·NAND/eSSD 신규계약단가/물량미확인. NAND현물10/19·공개계약8월은최신대체사용안함. 생산/수율/주문은오늘SK발표후검증. AI투자지속과수익화·주가수급별도평가.

## 미국 반도체·AI 정규장
|종목|10/27종가 USD|등락|
|---|---:|---:|
{ustable}
10/27 16ET=10/28 05KST. 원문 OHLC보존: SOXX500.245/513.160/498.410/511.060, SMH548.800/559.800/546.665/557.980. SOXX/SMH종가고점근처이나NVDA시가218.30→217.94로차별화.

## 미국 시간외
|종목|USD|종가대비|시각 KST|
|---|---:|---:|---|
{aftertable}
시간외 유효봉·정규종가와분리. SK ADR은전일한국장후행반영과분리해야하므로별도충격점수미사용.

## 달러/원·국내 수급·시장 구조
FAST_TABLE
하나은행고시·연속선물최근거래·NXT장전과KRX종가구분. 선물롤수익률미계산. PREOPEN수급/프로그램0은거래전초기값이며전일실제0이아님. 외국인현물/선물·기관세부·프로그램·시장폭최종묶음미확인. 오늘개장후재관찰,미확인은null.

## 경제 캘린더
SK하이닉스10/28 09시전발표·09시콜(공식초청장). FOMC10/27~28ET·결정10/29 03KST, MS10/28ET·Amazon10/29ET실적. BEA10/29 08:30ET=21:30KST GDP·개인소득소비/PCE동시. 삼성공식IR페이지수집·세부시간정본미확인. CB10월수치원문지연/전월수정충돌로보류.

## 미 국채와 장단기 금리차
Treasury10/27 3M4.22·2Y4.70·10Y4.99%. FRED동일10/27금리차0.29/0.77%p. 전일0.32/0.78에서축소:2Y+2bp·10Y-1bp. 개별FRED10/26값혼합차감안함. 성장주할인율에는10Y절대수준부담.
![90일](../charts/us_yield_spreads_90d_{DATE}.png)
![2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 오늘 KOSPI·KODEX 시나리오
강세25%5800초과~5950:15:20지수>5800 AND 외국인>0 AND 프로그램>0,5800재이탈무효.
기본50%5600~5800:지수>=5600 AND <=5800 AND 외국인>=-8000억원,범위이탈·매도확대무효.
약세25%5400~5600미만:지수<5600 AND 외국인<0 AND 프로그램<0,5600회복무효.
KOSPI5600/5700/5800,KODEX69465/69955/72745. 69465이탈미회복반등무효. 90%장중포락5250~6100,종가범위와별도.

## 장중 체크리스트
09:00SK콜·09:30초기반응·10시외국인/프로그램동행·14시지속성·15:20조건관측. 반도체두종목외금융/자동차/조선확산·시장폭도확인. 사전수급가설승격없음.

## 출처와 확인 시각
원천별 fetchedAt·거래일·rawHash는 evidence/{DATE}에보존. 최종조회시각상단표기.
'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
# 사이트 카드/메타 생성 코드는 검증된 템플릿 부분만 재사용한다.
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index('s=prior;s.update')]
tail=tail.replace("oldimage='market-2026-10-19-memory-credit-1200x630.png'","oldimage='market-2026-10-27-ai-financing-1200x630.png'")
for a,b in [('2026.10.20','2026.10.28'),('2026.10.19','2026.10.27'),('2026-10-19','2026-10-27'),('10월 19일','10월 27일')]:tail=tail.replace(a,b)
exec(tail)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(snapshotId='20261028-prepared',generatedAt=NOW,asOf=NOW,asOfDisplay=NOW,sourceLabel='미국10월27일 정규장·국내10월27일 종가·10월28일 장전',headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'})
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='확정값 미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=3.09,open=K['open'],high=K['high'],low=K['low'],previousClose=5469.47,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월27일 정규장 종가')
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'최종 묶음 미확인'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'실적 발표 뒤 매수 지속 확인','attack':25,'wait':50,'defense':25,'note':'전일 급등 뒤 SK하이닉스 실적과 매수 지속성을 시험합니다.'}
s['checkpoints']=[]
s['changes']=[{'label':'KOSPI','before':'5,469.47','after':'5,638.34','meaning':'3.09% 올랐지만 장중 고점에서 상승 폭을 줄였습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX +3.91% · SMH +3.02%','detail':'10월27일 정규장·AMD +5.45%','tone':'positive'},{'label':'오늘 실적','metric':'SK하이닉스 09시 설명회','detail':'HBM·현금흐름·주주환원 조건','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/27','value':'$61.333','change':'보합'},{'label':'DDR4 16Gb · 10/27','value':'$82.623','change':'보합'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,600','pivot':'5,700','resistance':'5,800'},{'asset':'KODEX 레버리지','support':'69,465원','pivot':'69,955원','resistance':'72,745원'}]
s['scenarios']=[{'id':k,'label':label,'range':ran,'summary':summ,'conditions':cond,'invalidation':inv} for k,label,ran,summ,cond,inv in [('bull','강세 · 25%','KOSPI 5,800 초과~5,950','실적과 매수 동행',['5,800 초과','외국인 순매수','프로그램 순매수'],'5,800 재이탈'),('base','기본 · 50%','KOSPI 5,600~5,800','급등 뒤 지지력 시험',['5,600 이상','5,800 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 매도 확대'),('bear','약세 · 25%','KOSPI 5,400~5,600 미만','실적 뒤 매도 확대',['5,600 미만','외국인 순매도','프로그램 순매도'],'5,600 회복')]]
s['events']=[{'time':'10월28일 09:00 KST','name':'SK하이닉스 실적 설명회','path':'HBM·현금흐름·주주환원'},{'time':'10월29일 03:00 KST','name':'FOMC 결정','path':'금리·자금조달'},{'time':'10월28일 ET','name':'Microsoft 실적','path':'AI 수요·현금흐름'},{'time':'10월29일 21:30 KST','name':'GDP·개인소득소비/PCE','path':'성장·물가'},{'time':'10월29일 ET','name':'Amazon 실적','path':'클라우드·AI 투자'}]
s['checklist']=[{'id':'support','label':'5,600선 방어'},{'id':'rebound','label':'실적 뒤 5,700선 회복과 외국인·프로그램 매수 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5600,5700,5800] if x['id']=='KOSPI' else [69465,69955,72745];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월27일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월27일 확정 일봉과 10월28일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s);dump('research/evidence/'+DATE+'/prepared.json',{'title':TITLE,'summary':SUMMARY,'image':IMAGE,'asOf':NOW,'imageMode':'built-in imagegen','prompt':'Coral earnings stage curtains, glass podium, staircase and morning Seoul. No semiconductor hardware.'})
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5638.34(+3.09%), KODEX69955(+6.84%). 최종 수급 묶음 미확인.\n- 미국반도체 추가상승·SK당일실적·Meta공모증액. 기존한국반영AI/주주환원기대중복제외.\n- 다음 SK10/28 09시·FOMC10/29 03시·MS10/28ET·GDP/PCE10/29 21:30KST·Amazon10/29ET.\n- 기본5600~5800(50%),강세5800초과~5950(25%),약세5400~5600미만(25%),대응25/50/25.\n- 보고서 reports/{DATE}.md,취재 research/notes/{DATE}.md,차트 charts/us_yield_spreads_*_{DATE}.png.\n- 직전기본초과·강세종가내·장중포락내,수급exact앵커미확보. 누적기존9/21해시불일치.\n')
for page in ['index.html','articles/index.html','articles/market.html']:
 t=read(page)
 def card(m):
  if 'market-'+DATE+'.html' in m[0]:
   c=re.sub(r'2026\.10\.\d{2}','2026.10.28',m[0]);c=re.sub(r'10월 \d{1,2}일','10월 28일',c);return re.sub(r'2026-10-\d{2}T[^"< ]+',NOW,c)
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 t=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,t,flags=re.S)
 if page=='index.html':
  head,rest=t.split('<body',1);head=head.replace('market-2026-10-27-ai-financing-1200x630.png',IMAGE);t=head+'<body'+rest
 if page=='articles/market.html':t=t.replace('AI 금융과 반도체 동반 반등','반도체 랠리와 SK하이닉스 실적')
 write(page,t)
t=read('sitemap.xml')
for u in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:t=re.sub(r'(<loc>'+re.escape(u)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+DATE,t)
write('sitemap.xml',t)
print('prepared',NOW)
