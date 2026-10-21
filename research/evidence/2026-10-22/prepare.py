"""10월22일 검증 자료와 원고 준비. 시세 봉인은 finalize에서 수행."""
import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-22';OLD='2026-10-21';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='Nvidia 공급망 투자에도 시간외 약세…금통위 앞둔 KOSPI'
SUMMARY='미국 반도체 ETF는 올랐지만 주요 종목은 시간외에서 밀렸습니다. Nvidia의 국내 기판·패키징 투자와 금통위 결과가 KOSPI 반등의 지속성을 가를 변수입니다.'
IMAGE='market-2026-10-22-ai-capacity-bok-1200x630.png';ALT='밝은 공간에서 반도체 웨이퍼와 공장들을 연결하는 금빛 공급망';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8-sig'))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261021\|([^"\s]+)',base64.b64decode(ev(k+'-fchart.raw')['raw'])).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==5735.66 and L['close']==71740
assert float(ev('KOSPI-basic')['data']['closePrice'].replace(',',''))==K['close']
assert any(x['localTradedAt']==OLD and float(x['closePrice'].replace(',',''))==L['close'] for x in ev('122630')['data'])
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO','META','TSLA']:
 d=json.loads(base64.b64decode(ev('after-'+k+'.raw')['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f"|{k}|{c:,.2f}|{(c/d['meta']['regularMarketPrice']-1)*100:+.2f}%|{at}|")
aftertable='\n'.join(after)
sources=[('Nvidia 공급망 발표','https://nvidianews.nvidia.com/news/nvidia-and-supply-chain-partners-expand-capacity-to-accelerate-ai-infrastructure-buildout/'),('Tesla 공시','https://ir.tesla.com/_flysystem/s3/sec/000162828026066738/tsla-20261021-gen.pdf'),('Meta 실적 AP','https://apnews.com/article/13ecd6c459e39a3602f302bcc2412fe9'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('한국은행 금통위 일정','https://www.bok.or.kr/eng/main/contents.do?menuNo=400020'),('미 재무부 금리',ev('Treasury.raw')['url']),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉','https://fchart.stock.naver.com/sise.nhn?symbol=KOSPI&timeframe=day&count=5&requestType=0'),('FOMC','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm')]
notes='''# 2026-10-22 취재 노트

08:02 KST 조사 개시. 취재→집필→퇴고→humanize-korean 국소 윤문→Amplify 순서. 실제 시각 사용.

## 이슈 레이더
|후보|점수|근거와 전달 경로|
|---|---:|---|
|Nvidia 공급망 생산능력 확대|13|회사10/21 발표. 기판3년2.5배, 삼성전기 합류·세종/부산 투자, Amkor 한국 패키징2028년말300% 초과 증가 목표. 확정 실현 매출과 구분|
|미국 정규장 상승·시간외 약세|12|SOXX+2.07%·SMH+1.89%. NVDA·AMD·MU·AVGO 시간외 하락. 국내 NXT 약세와 비교|
|한국은행 금통위|12|공식10/22 일정. 결정 전 금리·환율 변동. 결과나 발표시각을 미리 단정하지 않음|
|Meta 실적|9|AP 매출646억달러+26%, 순이익98.6억달러. 회사 IR 직접403, 신규CAPEX 수치 미확인. AP원문 열기 실패·검색본문 교차 제약으로 공개 숫자 생략, 가격만 사용|
|Tesla 실적|9|회사8-K·첨부 업데이트 원문 확보. GAAP순이익약8억·영업이익7억달러. 시간외 주가하락, 합병은 검토 단계|
|메모리 현물 차별화|8|TrendForce10/21 18:10 GMT+8 DDR5 60.867 +0.28%, DDR4 83.117 -0.30%. HBM계약과 구분|
|유가·이란 운송위험|8|공개선물 최근거래. 지정학 속보와 선물종목·시각 구분. 지난 국내장 반영분 중복 가산 안 함|
|강제청산·증자·수출통제|4|광범위탐색에서 오늘 원문으로 확정할 신규 지배사건 없음. 비사건 공개 생략|

## 사실 경계와 누락
전일 KOSPI5735.66(+3.29%), KODEX71740(+6.80%), 일봉 fchart·basic·종목price 교차. KOSPI price는10/20로 지연되어10/21 종가 원천으로 사용하지 않음. NXT 삼성·하이닉스는 정규장과 분리. integration 최종수급·프로그램·시장폭 정본 묶음 및 정확15:20 앵커 없음, 0 채우지 않음.
전일 기본 범위5450~5650 실패·강세5650초과~5800 종가 적중. 고점5816.43·저점5630.14 모두 기존90%경로5100~5950 내. 원인 조건은 미검증. 표본성과 주장 없음.
Supermicro·SpaceX 실적은10/21 국내 장전 이미 알려져 국내+3.29%에 반영. 밤사이 미국 상승 전부를 새 호재로 가산하지 않음. 신규 Nvidia 공급망 발표는 삼성전기와 패키징 직접 노출, 삼성전자·SK하이닉스 확정 HBM수주로 바꾸지 않음.
NAND 공개표10/12·계약8월, RDIMM·eSSD 신규계약 미확인. FRED 점검중(공식 maintenance), 재무부10/21 3M4.25·2Y4.81·10Y5.13%, 금리차0.32/0.88%p 직접계산. 차트2026년·90일 재무부 원천 사용, 2년 시계열이라고 표기하지 않음.
누적 평가 기존9/21 보고서해시 불일치로 중단, 활성가설 없음. 오늘 판단에 과거 적중률 사용 안 함.

## 시각 논제
공급망 확대와 금통위 대기. 회복 속 경계, 라벤더·아이보리와 코발트·금색 자연광. 웨이퍼에서 공장들로 뻗는 선, 기존 썸네일 참조 없음.
'''
write('research/notes/'+DATE+'.md',notes+'\n'+'\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n')
body='''<p>미국 반도체주는 올랐지만 장 마감 뒤의 분위기는 달랐습니다. 21일 정규장에서 SOXX는 2.07%, SMH는 1.89% 상승했습니다. 한국시간 오전 8시 무렵에는 Nvidia·AMD·Micron·Broadcom이 모두 정규장 종가 아래에서 거래됐습니다. 전일 3.29% 반등한 KOSPI는 오늘 금통위 결과와 국내 매수의 지속성을 함께 살펴야 합니다.</p>
<h2>삼성전기가 합류한 Nvidia 공급망</h2><p>Nvidia는 기판·패키징·테스트·광학 부품 생산능력을 늘리는 계획을 발표했습니다. 삼성전기는 기존 한국 생산시설로 기판 공급망에 합류하며 세종·부산의 시설 개선과 신설도 추진합니다. 관련 기판 업체들의 증설을 합쳐 Nvidia 제품용 생산능력을 향후 3년간 2.5배로 늘린다는 계획입니다. 국내 부품·장비 업체에는 AI 수요가 실제 설비 투자로 이어지는 발표입니다. <a href="https://nvidianews.nvidia.com/news/nvidia-and-supply-chain-partners-expand-capacity-to-accelerate-ai-infrastructure-buildout/">Nvidia 발표</a></p>
<p>Amkor와는 한국의 첨단 패키징 생산능력 확대를 추진합니다. 2028년 말까지 인터포저 웨이퍼 생산능력을 300% 넘게 늘리는 것이 목표입니다. 다만 이 증설 계획을 삼성전자·SK하이닉스의 HBM 확정 수주액으로 환산할 수는 없습니다. 투자 일정과 실제 가동, 납품으로 이어지는 속도가 중요합니다.</p>
<h2>정규장 반등 뒤에도 남은 실적 부담</h2><p>정규장에서는 Nvidia가 2.54%, AMD가 3.36%, Micron이 1.96%, Broadcom이 1.03% 올랐습니다. 시간외에서는 Meta가 상승한 반면 Tesla와 주요 반도체 종목은 밀렸습니다. Tesla가 공개한 3분기 자료에는 GAAP 영업이익 약 7억달러, 순이익 약 8억달러가 담겼습니다. AI 투자 확대 소식만으로 모든 성장주가 함께 오르는 국면은 아닙니다. <a href="https://ir.tesla.com/_flysystem/s3/sec/000162828026066738/tsla-20261021-gen.pdf">Tesla 실적 자료</a></p>
<p>전일 한국장에서 이미 알려졌던 AI 서버 실적 호재와 미국 정규장의 뒤이은 반응은 하나의 흐름으로 봐야 합니다. 한국장의 반등과 미국 상승을 독립된 호재로 모두 더하면 오늘의 상승 여력을 과대평가할 수 있습니다.</p>
<h2>메모리 가격과 자금 비용은 별개다</h2><p>21일 대만시간 오후 6시 10분 기준 DDR5 16Gb 현물 평균은 60.867달러로 0.28% 올랐고 DDR4 16Gb는 83.117달러로 0.30% 내렸습니다. 제품별 수급은 갈립니다. 이 현물 가격이 HBM과 서버 메모리의 계약 단가를 그대로 뜻하지는 않습니다. <a href="https://www.trendforce.com/price/dram/dram_spot">TrendForce</a></p>
<p>미 재무부의 21일 금리는 3개월물 4.25%, 2년물 4.81%, 10년물 5.13%입니다. 10년물과 2년물 차이는 0.32%포인트, 3개월물과의 차이는 0.88%포인트입니다. 높은 장기금리는 AI 설비를 짓는 기업의 자금 조달 부담으로 남습니다.</p>
<h2>금통위 뒤에도 5,700선을 지킬까</h2><p>전일 KOSPI는 5,666.34에 출발해 5,816.43까지 오른 뒤 5,735.66으로 마쳤습니다. 장중 저점은 5,630.14였습니다. 오늘은 5,700선 유지와 전일 고점 회복을 구분해서 봅니다. 금통위 결정 뒤 원화와 외국인·프로그램 매수가 같은 방향으로 움직이는지가 관건입니다. <a href="https://www.bok.or.kr/eng/main/contents.do?menuNo=400020">한국은행 일정</a></p>
<p>기본 종가 범위는 5,600~5,800(50%)으로 봅니다. 외국인과 프로그램이 함께 순매수하며 5,800선을 넘기는 강세 범위는 5,800 초과~5,950(20%), 5,600선 아래에서 매도가 이어지는 약세 범위는 5,350~5,600 미만(30%)입니다. 5,800선을 다시 내주면 강세 판단을, 5,600선을 회복하면 약세 판단을 접습니다. 예상 범위를 벗어나는 변동도 가능합니다.</p>
<p>KODEX 레버리지는 전일 저점 69,220원을 첫 지지, 종가 71,740원을 반등 기준, 고점 74,365원을 저항으로 봅니다. 69,220원 아래에서 회복하지 못하면 지지 판단은 무효입니다. 한국은행의 오늘 결정과 미국시간 27~28일 FOMC를 앞두고, 개장 초 매수가 오후에도 이어지는지 확인할 필요가 있습니다.</p>'''
write('research/evidence/'+DATE+'/body.html',body)
report=f'''# {DATE} KOSPI·KODEX 장전 리서치

작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전. 미국10/21 정규장 종료·시간외 진행, 원천 지연 가능.

## 핵심 결론
{SUMMARY} 기본5600~5800(50%), 강세5800초과~5950(20%), 약세5350~5600미만(30%). 공격15·관망50·방어35. 90% 장중포락5250~6100. 조건부 수동판단으로 대응점수와 확률은 별개.

## 밤사이 지배 이슈
Nvidia 공식10/21 공급망 증설·삼성전기 기판 합류·Amkor한국 패키징 확대. 생산계획과 확정 매출 구분. 미국 정규장 반등 뒤 시간외 약세. 금통위10/22 공식일정. 후보8건·제외사유는 research/notes/{DATE}.md. 전일 한국 반영된 Supermicro·SpaceX 호재를 중복 충격으로 가산하지 않음.

## 국내 확정값·전망 회고
|항목|10/21 시가|고가|저가|종가|
|---|---:|---:|---:|---:|
|KOSPI|5666.34|5816.43|5630.14|5735.66|
|KODEX|69940|74365|69220|71740|
KOSPI+3.29%, KODEX+6.80%, 거래량27461872주. fchart·basic·price 교차. KOSPI price10/20 지연 제외. 전일 기본실패·강세종가적중, 경로포락내. 정확15:20 앵커 미확보로 원인조건 미검증. 수급·프로그램·시장폭 정본묶음 미확인, 0 채우지 않음.

## 메모리 펀더멘털
10/21 18:10 GMT+8 DDR5 16Gb60.867달러+0.28%, DDR4 16Gb83.117달러-0.30%. HBM·서버DRAM·eSSD 신규계약 물량/단가 미확인. NAND10/12·계약8월 공개표는 최신아님. 부품 증설을 메모리 확정수주로 치환하지 않음.

## 미국 정규장
|종목|10/21 종가 USD|등락|
|---|---:|---:|
{ustable}
10/21 16:00 ET=10/22 05:00 KST 종료. 연속 일봉 계산.

## 미국 시간외
|종목|USD|종가 대비|원천시각 KST|
|---|---:|---:|---|
{aftertable}
진행중 유효봉, 확정 종가 아님.

## 최종 환율·선물·NXT
FAST_TABLE
하나은행 고시·선물최근거래·NXT·KRX 구분. 계약월연속선물 종가 차이를 현물당일수익률로 사용하지 않음.

## 금리와 일정
재무부10/21 3M4.25%,2Y4.81%,10Y5.13%. 차이+0.32/+0.88%p. FRED점검중으로 공식재무부2026시계열 대체, 2년차트 아님.
한국은행10/22 금통위(정확 발표시각 공식일정 미기재), FOMC10/27~28 ET. 미국주간실업수당 통상목요일08:30 ET=21:30KST이나 오늘 개별공식일정 원문 미확인으로 확정시각 단정안함.
![최근90일](../charts/us_yield_spreads_90d_{DATE}.png)
![2026년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 조건과 무효화
강세20% 5800초과~5950:15:20 지수>5800 AND 외국인>0 AND 프로그램>0,5800재이탈무효.
기본50% 5600~5800:지수>=5600 AND <=5800 AND 외국인>=-8000억원,범위이탈·매도확대무효.
약세30% 5350~5600미만:지수<5600 AND 외국인<0 AND 프로그램<0,5600회복무효.
KOSPI5600/5700/5800, KODEX69220/71740/74365. 09:30·10:00 수급동행,14:00반전,15:20종가조건. 방어35·관망50·공격15.

## 출처
'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
# 기존 HTML 구조와 목록 연결만 재사용.
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index("s=prior;s.update")]
tail=tail.replace("oldimage='market-2026-10-19-memory-credit-1200x630.png'","oldimage='market-2026-10-21-gpu-bottleneck-1200x630.png'")
for a,b in [('2026.10.20','2026.10.22'),('2026.10.19','2026.10.21'),('2026-10-19','2026-10-21'),('10월 19일','10월 21일')]:tail=tail.replace(a,b)
exec(tail)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(snapshotId='20261022-prepared',generatedAt=NOW,asOf=NOW,asOfDisplay=NOW,sourceLabel='미국10월21일 정규장·국내10월21일 종가·10월22일 장전',headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'})
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='확정값 미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=3.29,open=K['open'],high=K['high'],low=K['low'],previousClose=5552.74,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월21일 정규장 종가')
s['stance']={'label':'금통위 뒤 매수 확인','attack':15,'wait':50,'defense':35,'note':'공급망 투자가 확대돼도 시간외 주가는 약합니다. 금통위 뒤 원화와 국내 매수를 함께 봅니다.'}
s['changes']=[{'label':'KOSPI','before':'5,552.74','after':'5,735.66','meaning':'반등했지만 전일 고점에서는 밀렸습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX +2.07% · SMH +1.89%','detail':'10월21일 정규장, 시간외 주요종목 약세','tone':'neutral'},{'label':'국내 공급망','metric':'삼성전기 기판 · Amkor 패키징','detail':'Nvidia 생산능력 확대 계획','tone':'positive'}]
s['memory']=[{'label':'DDR5 16Gb · 10/21','value':'$60.867','change':'+0.28%'},{'label':'DDR4 16Gb · 10/21','value':'$83.117','change':'-0.30%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,600','pivot':'5,700','resistance':'5,800'},{'asset':'KODEX 레버리지','support':'69,220원','pivot':'71,740원','resistance':'74,365원'}]
s['scenarios']=[{'id':k,'label':label,'range':ran,'summary':summ,'conditions':cond,'invalidation':inv} for k,label,ran,summ,cond,inv in [('bull','강세 · 20%','KOSPI 5,800 초과~5,950','매수가 동행하는 회복',['5,800 초과','외국인 순매수','프로그램 순매수'],'5,800 재이탈'),('base','기본 · 50%','KOSPI 5,600~5,800','반등 유지력 시험',['5,600 이상','5,800 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 매도 확대'),('bear','약세 · 30%','KOSPI 5,350~5,600 미만','하단 지지 실패',['5,600 미만','외국인 순매도','프로그램 순매도'],'5,600 회복')]]
s['events']=[{'time':'10월22일 KST','name':'한국은행 금통위','path':'금리·원화·외국인 수급'},{'time':'10월27~28일 ET','name':'FOMC','path':'금리·AI 자금 조달'}];s['checklist']=[{'id':'support','label':'5,600선 방어'},{'id':'rebound','label':'금통위 뒤 5,700선 유지와 수급 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5600,5700,5800] if x['id']=='KOSPI' else [69220,71740,74365];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월21일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월21일 확정 일봉과 10월22일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s);dump('research/evidence/'+DATE+'/prepared.json',{'title':TITLE,'summary':SUMMARY,'image':IMAGE,'asOf':NOW})
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5735.66(+3.29%), KODEX71740(+6.80%). 수급정본 묶음 미확인.\n- Nvidia 국내기판·패키징 증설, 미국정규장반등 뒤 시간외약세. 기존국내반등 중복가산 제외.\n- 다음 한국은행10/22 금통위·FOMC10/27~28 ET.\n- 기본5600~5800(50%),강세5800초과~5950(20%),약세5350~5600미만(30%),대응15/50/35.\n- 보고서 reports/{DATE}.md,취재 research/notes/{DATE}.md,차트 charts/us_yield_spreads_*_{DATE}.png.\n- 직전 기본실패·강세종가적중. exact수급앵커미확보. actuals/2026-10-21.json 및 outcomes/2026-10-21-0804-same-close.json. 누적 기존9/21해시오류.\n')
for page in ['index.html','articles/index.html','articles/market.html']:
 t=read(page)
 def card(m):
  if 'market-'+DATE+'.html' in m[0]:
   c=m[0].replace('2026.10.21','2026.10.22').replace('10월 21일','10월 22일');return re.sub(r'2026-10-21T[^"< ]+',NOW,c)
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 t=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,t,flags=re.S)
 if page=='index.html':t=t.replace('market-2026-10-21-gpu-bottleneck-1200x630.png',IMAGE)
 if page=='articles/market.html':t=t.replace('GPU 수요와 국내 매도 완화','공급망 투자와 금통위 뒤 매수')
 write(page,t)
t=read('sitemap.xml')
for u in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:t=re.sub(r'(<loc>'+re.escape(u)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+DATE,t)
write('sitemap.xml',t)
print('prepared',NOW)
