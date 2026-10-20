"""오늘 검증 자료로 원고와 공개 연결을 준비한다. 최종 시세 봉인은 별도."""
import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-21';OLD='2026-10-20';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='AI 서버 실적에 시간외 반등…KOSPI 5,550선 회복을 본다'
SUMMARY='미국 반도체주는 정규장 약세 뒤 시간외에서 반등했습니다. AI 서버 잠정실적과 중국 GPU 주문 수요가 부각된 가운데 KOSPI는 5,550선 회복과 국내 매도 완화가 관건입니다.'
IMAGE='market-2026-10-21-gpu-bottleneck-1200x630.png';ALT='밝은 산호색 공간에서 좁은 문을 통과하려고 줄지어 선 GPU 카드';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8-sig'))
def num(x):return float(str(x).replace(',',''))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261020\|([^"\s]+)',base64.b64decode(ev(k+'-fchart.raw')['raw'])).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==5552.74 and L['close']==67170
for name,v in [('KOSPI',K),('122630',L)]:
 d=ev(name)['data'][0];assert d['localTradedAt']==OLD
 for a,b in [('open','openPrice'),('high','highPrice'),('low','lowPrice'),('close','closePrice')]:assert v[a]==num(d[b])
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(ev('after-'+k+'.raw')['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f'|{k}|{c:,.2f}|{(c/us(k)[0]-1)*100:+.2f}%|{at}|')
aftertable='\n'.join(after)
sources=[('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉',ev('KOSPI')['url']),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('중국 GPU 주문 Reuters','https://www.investing.com/news/stock-market-news/exclusivebytedance-alibaba-tencent-place-over-35-billion-worth-of-nvidia-chip-orders-4959231'),('Netflix 주주서한','https://ir.netflix.net/files/doc_financials/2026/q3/FINAL-Q3-26-Shareholder-Letter.pdf'),('Supermicro 잠정실적','https://ir.supermicro.com/news/news-details/2026/Supermicro-Provides-First-Quarter-of-Fiscal-Year-2027-Preliminary-Business-Update/default.aspx'),('Amazon 독일 투자','https://press.aboutamazon.com/de/2026/10/invest-in-germany-summit-amazon-kuendigt-16-milliarden-euro-investitionen-fuer-2027-in-deutschland-an'),('BLS 일정','https://www.bls.gov/schedule/2026/10_sched.htm'),('Tesla 일정','https://ir.tesla.com/press-release/tesla-third-quarter-2026-production-deliveries-and-deployments'),('FOMC','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),('FRED','https://fred.stlouisfed.org/series/T10Y2Y')]
notes='''# 2026-10-21 취재 노트

사전 준비 07:57 KST, 첫 원천 탐색 07:58, 08시 이후 시세 재수집. 실제 시각 소급 없음. KRX 달력·휴일 보조달력 확인, 최종 NXT OPEN 대조.

## 이슈 레이더
|후보|점수|확정 범위·전달 경로|
|---|---:|---|
|GPU 수요와 반도체 주가 괴리|12|Reuters 익명 소식통의 중국 RTX PRO 5500 300만장·표시가격350억달러 주문 보도. 납품 불확실, HBM 계약 아님. SOXX -0.38%|
|국내 반등 실패|12|KOSPI 5552.74(-3.73%), 전일 기본 전망 실패·약세 범위 적중. 원인 조건은 정확15:20 앵커 부재|
|Supermicro 잠정 매출|11|회사 잠정 Q1 FY27 발표, 확정 감사 실적과 구분. AI 서버 수요 반대 근거|
|Netflix 광고 전망 하향|9|회사 주주서한 연간 광고매출 약27억달러, 이전30억달러. 성장주 수익화 평가|
|Amazon 독일 투자|9|2027년160억유로 전체 투자 중 AWS Frankfurt48억유로, 전액을 AI CAPEX로 계산 금지|
|MS 영국 데이터센터 철수|7|Reuters 사업 전력연결 지연, 이전부터 보도된 사건. 전체 AI 투자 취소로 일반화 금지|
|Tesla·SpaceX 합병 검토|7|실적콜 발언 보도·독립이사 위원회 검토 단계, 확정 합병 아님. 한국 메모리 직접 계약 연결 없음|
|OpenAI 자금조달 협상|5|300억달러 협상 보도, 기존 계획 반복·미확정. 신규 확정 자금으로 사용 금지|
|신규 강제청산·증자·규제|3|공시·주요 헤드라인 탐색, 오늘 지배 이슈로 확정할 원문 부족. 비사건 공개 제외|

## 논쟁점·제약
중국 GPU 수요 보도는 10/20 05:03 ET=18:03 KST로 한국 정규장 이후. 한국 전일 급락 원인으로 역귀속하지 않는다. 미국 반도체 약세는 한국 선행 하락과 같은 위험선호 흐름을 일부 반영할 수 있어 독립 충격으로 전부 재가산하지 않는다. RTX 워크스테이션 수요를 HBM 물량이나 삼성·하이닉스 확정매출로 변환하지 않는다.
국내 종목 price 응답은 일부 날짜별 종가와 전일대비 기준이 연속일봉과 맞지 않고 시간외 성격도 혼재한다. 개별주 정규장 종가는 공개 표에 넣지 않고 최종 NXT 원천을 별도 표시. KOSPI·KODEX는 fchart와 price 교차 일치.
integration 개인+8475·외국인-4884·기관-9901억원은 기타법인 누락 및 보도값 충돌로 완전 묶음 보류. 0 채우지 않음. 프로그램·시장폭도 장마감 정본 묶음 미확인으로 과거값 이월 금지.
DDR5 16Gb60.70달러(+0.11%), DDR4 16Gb83.364달러(-0.06%),10/20 18:10 GMT+8. RDIMM·NAND 표는10/12 및8월 자료로 최신값인 양 쓰지 않는다. HBM·서버 DRAM·eSSD 신규 계약단가·물량 미확인.
FRED10/20 금리차 +0.33/+0.86%p, 개별금리10/19 3M4.27·2Y4.77·10Y5.15%. 서로 다른 날짜 차감 금지. 활성 가설 없음. 기존9/21 해시 오류는 이번 전망 근거로 사용하지 않음.

## 시각 논제와 편집
주도사건 GPU 주문과 납품 병목, 방향은 수요와 주가의 괴리, 정서는 경계. 산호·민트 자연광, GPU 대기열과 좁은 관문의 새 구성. 이전 이미지 참조 없음.
취재 뒤 write-finished-manuscript 집필·퇴고, humanize-korean 사실 고정 윤문. 중심 문장은 5550선 회복과 매도 완화 조건. 공개 원고에 작업 설명 제외.
'''
write('research/notes/'+DATE+'.md',notes+'\n'+'\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n')
body='''<p>미국 반도체주는 정규장에서 밀렸지만 AI 서버 실적 발표 뒤 시간외에서 반등했습니다. 20일 정규장에서 SOXX와 SMH는 각각 0.38%, Micron은 0.98% 내렸습니다. 한국시간 오전 7시 58분 무렵의 시간외 최근 거래에서는 Nvidia가 정규장 종가보다 약 2.0%, AMD와 Micron이 약 2.5% 높았습니다. 전일 3.73% 급락한 KOSPI가 반등을 이어 가려면 수요 뉴스에 더해 국내 매도세가 줄어야 합니다.</p>
<h2>주문 수요와 매출 사이에 남은 납품 병목</h2><p>Reuters는 사안을 아는 소식통을 인용해 ByteDance·Alibaba·Tencent가 Nvidia RTX PRO 5500을 300만 장 넘게 주문했다고 보도했습니다. 표시가격 기준 350억달러가 넘지만 Nvidia가 주문 전량을 공급할 수 있는지는 불투명하다는 내용도 함께 전했습니다. 워크스테이션용 GPU의 주문 보도로, HBM 공급계약이나 확정 매출과는 구분해야 합니다. <a href="https://www.investing.com/news/stock-market-news/exclusivebytedance-alibaba-tencent-place-over-35-billion-worth-of-nvidia-chip-orders-4959231">Reuters 보도</a></p>
<p>AI 설비 수요를 뒷받침하는 발표도 이어졌습니다. Supermicro는 2027회계연도 1분기 잠정 매출을 185억~195억달러로 제시해 기존 전망 145억~155억달러를 웃돌았습니다. 최종 결산 전 추정치입니다. Amazon은 2027년 독일 투자 계획을 내놨습니다. Amazon의 전체 투자 160억유로 가운데 AWS 프랑크푸르트 클라우드·AI 인프라 몫은 48억유로입니다. 전체 투자액에는 물류·위성통신·콘텐츠도 포함됩니다. <a href="https://ir.supermicro.com/news/news-details/2026/Supermicro-Provides-First-Quarter-of-Fiscal-Year-2027-Preliminary-Business-Update/default.aspx">Supermicro 발표</a> · <a href="https://press.aboutamazon.com/de/2026/10/invest-in-germany-summit-amazon-kuendigt-16-milliarden-euro-investitionen-fuer-2027-in-deutschland-an">Amazon 발표</a></p>
<h2>현물 메모리는 버티지만 성장주 평가는 까다롭다</h2><p>20일 대만시간 오후 6시 10분 기준 DDR5 16Gb 현물 평균은 60.70달러로 0.11% 올랐고 DDR4 16Gb는 83.364달러로 0.06% 내렸습니다. 메모리 수요가 한꺼번에 꺾인 모습과는 거리가 있지만 제품별 가격 차이는 남아 있습니다. 이 현물 가격만으로 HBM·서버 메모리의 계약 물량과 이익을 확정할 수는 없습니다. <a href="https://www.trendforce.com/price/dram/dram_spot">TrendForce 현물 가격</a></p>
<p>Netflix는 3분기 매출이 전년보다 12% 늘었다고 밝혔지만 연간 광고매출 전망은 약 30억달러에서 27억달러로 낮췄습니다. 반도체의 직접 수요 지표는 아니어도 성장주 투자자가 매출의 질과 향후 전망을 따지는 분위기를 보여 줍니다. <a href="https://ir.netflix.net/files/doc_financials/2026/q3/FINAL-Q3-26-Shareholder-Letter.pdf">Netflix 주주서한</a></p>
<h2>KOSPI 5,550선 회복을 먼저 본다</h2><p>전일 KOSPI는 시가이자 고가인 5,733.57에서 밀려 5,552.74로 마쳤고 장중 저점은 5,493.24였습니다. 한국에서 이미 발생한 급락과 뒤이은 미국 반도체 약세를 별개의 충격으로 모두 더할 필요는 없습니다. 오늘은 5,550선 위로 올라선 뒤 외국인·프로그램 매도가 줄어드는지가 먼저입니다.</p>
<p>기본 종가 범위는 5,450~5,650(45%)으로 봅니다. 외국인·프로그램이 함께 순매수하고 5,650선을 넘겨 유지하는 강세 범위는 5,650 초과~5,800(20%)입니다. 5,450선 아래에서 매도가 이어지는 약세 범위는 5,200~5,450 미만(35%)입니다. 예상 범위를 벗어나는 변동도 가능합니다.</p>
<p>KODEX 레버리지는 전일 저점 65,335원을 첫 지지, 종가 67,170원을 반등 기준, 고점 71,300원을 저항으로 봅니다. 65,335원 아래에서 회복하지 못하면 지지 판단은 무효입니다. 개장 직후 한 차례 매수보다 오전과 오후에 매수가 이어지는지가 중요합니다.</p>
<h2>다음 실적과 자금 조달 비용</h2><p>Tesla는 미국시간 21일 장 마감 뒤 실적을 발표하고 한국시간 22일 오전 6시 30분에 설명회를 엽니다. 다음 FOMC는 미국시간 27~28일입니다. 20일 미국 10년물과 2년물 금리차는 0.33%포인트, 10년물과 3개월물은 0.86%포인트였습니다. 금리차와 함께 금리 자체의 수준도 기업 자금 조달 부담을 판단하는 기준입니다.</p>'''
write('research/evidence/'+DATE+'/body.html',body)
report=f'''# {DATE} KOSPI·KODEX 장전 리서치

작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전. 미국10/20 정규장 종료·시간외 구분.

## 핵심 결론
{SUMMARY} 기본5450~5650(45%), 강세5650초과~5800(20%), 약세5200~5450미만(35%). 공격10·관망45·방어45. 90% 장중 포락5100~5950. 수동 조건부 전망이며 확률과 대응 점수는 별개다.

## 밤사이 지배 이슈
중국향 GPU 주문 Reuters 보도는350억달러 표시가격·익명취재·납품불확실. HBM 확정 계약과 구분. Supermicro 잠정 매출과 Amazon2027 독일투자160억유로 중 AWS48억유로. Netflix 광고전망30억→27억달러. 후보9개와 제외근거는 research/notes/{DATE}.md. 전일 한국 급락과 미국 후행 약세를 중복 충격으로 계산하지 않음.

## 국내 확정값·직전 전망
|항목|10/20 시가|고가|저가|종가|
|---|---:|---:|---:|---:|
|KOSPI|5733.57|5733.57|5493.24|5552.74|
|KODEX|71265|71300|65335|67170|
KOSPI-3.73%, KODEX-7.04%, 거래량23418195주. fchart·price 교차. 직전 기본 실패·약세 종가범위 적중, 장중 고저 모두90%포락 안. 정확15:20 앵커 누락으로 조건·원인 미검증. integration 수급 보도값 충돌·기타법인 누락으로 정본묶음 보류. 개별주 일봉 종가·대비 기준 혼재로 공개 정규장 종가 제외. 기관·선물·프로그램 최종 묶음 미확인, 0 채우지 않음.

## 메모리 펀더멘털
TrendForce10/20 18:10 GMT+8 DDR5 16Gb60.70달러(+0.11%), DDR4 16Gb83.364달러(-0.06%). HBM·서버DRAM·RDIMM·NAND·eSSD 신규 단가·물량 미확인. 공개 RDIMM·NAND 표의10/12 및8월 값은 최신값 아님. 빅테크 CAPEX 계획과 공급사 확정매출을 구분한다.

## 미국 정규장
|종목|10/20 종가 USD|등락|
|---|---:|---:|
{ustable}
미국10/20 16:00 ET=10/21 05:00 KST 종료. 연속 일봉 종가 계산.

## 미국 시간외
|종목|USD|종가 대비|유효 5분봉 시각 KST|
|---|---:|---:|---|
{aftertable}
진행 중 최근 유효봉이며 확정 종가 아님.

## 최종 환율·선물·NXT
FAST_TABLE
하나은행 고시·역외현물·NXT·KRX 및 선물 최근거래·결제값을 구분한다.

## 금리와 일정
FRED10/20 10Y-2Y+0.33%p·10Y-3M+0.86%p. 개별금리10/19 3M4.27%·2Y4.77%·10Y5.15%, 날짜 혼합 차감 금지.
BLS10/21 10:00 ET=23:00 KST 분기 통상주급, Tesla10/21 마감후·설명회10/22 06:30 KST(10/21 17:30 ET), FOMC10/27~28 ET. BLS10/20 발표는 주별 고용이 아닌 주별(State) 고용·실업 월간통계였음. 과거 보고서 원문은 보존.
![최근90일](../charts/us_yield_spreads_90d_{DATE}.png)
![최근2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 조건·무효화
- 강세20%:5650초과~5800.15:20 지수>5650 AND 외국인>0 AND 프로그램>0.5650재이탈 무효.
- 기본45%:5450~5650.15:20 지수>=5450 AND <=5650 AND 외국인>=-8000억원.범위이탈·매도확대 무효.
- 약세35%:5200~5450미만.15:20 지수<5450 AND 외국인<0 AND 프로그램<0.5450회복 무효.
- KOSPI지지5450·반등5550·저항5650.KODEX65335/67170/71300원.지지이탈 후 미회복 무효.
- 09:30·10:00 수급 동행,14:00반전,15:20종가조건. 단일 시점 매수는 지속수급과 다름.

## 출처
'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
# 검증된 HTML 골격·목록·대시보드 구조만 재사용한다.
oldscript=read('research/evidence/2026-10-20/build.py')
tail=oldscript[oldscript.index("old=read('articles/market-'+OLD+'.html')"):]
tail=tail[:tail.index("write('STATE.md'")]
tail=tail.replace("oldimage='market-2026-10-19-memory-credit-1200x630.png'","oldimage='market-2026-10-20-chip-rebound-1200x630.png'")
for a,b in [('2026.10.20','2026.10.21'),('2026.10.19','2026.10.20'),('2026-10-19','2026-10-20'),('20261020','20261021'),('10月','10月'),('10월 19일','10월 20일'),('10월 20일 장전','10월 21일 장전'),('10/19','10/20')]:tail=tail.replace(a,b)
# 아래에서 모든 시황 필드 재구성. 골격 내 이전 문장을 공개하지 않는다.
exec(tail)
s=json.loads(read('research/evidence/'+DATE+'/prepared-dashboard.json'))
s['stance']={'label':'지지 회복 확인','attack':10,'wait':45,'defense':45,'note':'GPU 수요와 주가가 엇갈립니다. 국내 매도 완화와 5,550선 회복이 먼저입니다.'}
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='확정값 미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=5552.74,changePercent=-3.73,open=5733.57,high=5733.57,low=5493.24,previousClose=5768.01,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월 20일 정규장 종가')
s['changes']=[{'label':'KOSPI','before':'5,768.01','after':'5,552.74','meaning':'반등 다음 날 다시 밀려 전일 상승분을 반납했습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX -0.38% · MU -0.98%','detail':'10월 20일 정규장','tone':'negative'},{'label':'수요와 납품','metric':'GPU 주문 · AI 서버 잠정매출','detail':'수요가 실제 납품·현금흐름으로 이어질지가 관건입니다.','tone':'neutral'}]
s['memory']=[{'label':'DDR5 16Gb · 10/20','value':'$60.70','change':'+0.11%'},{'label':'DDR4 16Gb · 10/20','value':'$83.364','change':'-0.06%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,450','pivot':'5,550','resistance':'5,650'},{'asset':'KODEX 레버리지','support':'65,335원','pivot':'67,170원','resistance':'71,300원'}]
s['scenarios']=[{'id':k,'label':label,'range':ran,'summary':summ,'conditions':cond,'invalidation':inv} for k,label,ran,summ,cond,inv in [('bull','강세 · 20%','KOSPI 5,650 초과~5,800','매수가 동행하는 회복',['5,650 초과','외국인 순매수','프로그램 순매수'],'5,650 재이탈'),('base','기본 · 45%','KOSPI 5,450~5,650','지지 회복 시험',['5,450 이상','5,650 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 매도 확대'),('bear','약세 · 35%','KOSPI 5,200~5,450 미만','하단 지지 실패',['5,450 미만','외국인 순매도','프로그램 순매도'],'5,450 회복')]]
s['events']=[{'time':'10월 21일 23:00 KST','name':'미국 분기 통상주급','path':'노동비용'},{'time':'10월 22일 06:30 KST','name':'Tesla 실적 설명회','path':'성장주 수익성'},{'time':'10월 27~28일 ET','name':'FOMC','path':'금리·자금 조달'}]
s['checklist']=[{'id':'support','label':'5,450선 방어'},{'id':'rebound','label':'5,550선 회복과 매도 완화'}]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5450,5550,5650] if x['id']=='KOSPI' else [65335,67170,71300];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월 20일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월 20일 확정 일봉과 10월 21일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s)
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5552.74(-3.73%), KODEX67170원(-7.04%). 수급 원천 불일치로 금액 보류.\n- GPU 주문·Supermicro 잠정매출·Amazon AWS투자와 반도체 약세 괴리. Netflix 광고전망 하향. 국내 선행하락 중복가산 제외.\n- 다음 Tesla10/22 06:30 설명회·FOMC10/27~28 ET.\n- 기본5450~5650(45%), 강세5650초과~5800(20%), 약세5200~5450미만(35%), 대응10/45/45.\n- 보고서 reports/{DATE}.md, 취재 research/notes/{DATE}.md, 차트 charts/us_yield_spreads_*_{DATE}.png.\n- 직전 기본실패·약세종가 적중, 수급조건 미검증. actuals/2026-10-20.json·outcomes/2026-10-20-0801-same-close.json. 누적 기존9/21 해시 오류.\n')
# 이전 카드의 우선 로딩과 홈 공유 이미지·사이트맵을 동기화.
for page in ['index.html','articles/index.html','articles/market.html']:
 t=read(page)
 def card(m):
  if 'market-'+DATE+'.html' in m[0]:return m[0]
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 t=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,t,flags=re.S)
 if page=='index.html':t=t.replace('market-2026-10-20-chip-rebound-1200x630.png',IMAGE)
 if page=='articles/market.html':t=t.replace('반도체 반등과 매수 지속','GPU 수요와 국내 매도 완화')
 write(page,t)
t=read('sitemap.xml')
for u in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:
 t=re.sub(r'(<loc>'+re.escape(u)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+DATE,t)
write('sitemap.xml',t)
print('prepared',NOW)
