"""검증된 취재 노트와 공개 원고를 분리하고 발행 자료를 준비한다."""
import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-23';OLD='2026-10-22';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='AI 투자비 부담에 반도체주 급락…KOSPI는 전일 저점 시험'
SUMMARY='미국 반도체주가 급락한 뒤 시간외에서는 종목별 흐름이 갈렸습니다. 전일 하락을 거친 KOSPI는 5,486선 방어와 국내 매수의 지속성을 시험합니다.'
IMAGE='market-2026-10-23-ai-cash-oil-1200x630.png';ALT='밝은 하늘 아래 실리콘 웨이퍼와 AI 칩이 원유통·금빛 추와 균형을 이루는 유리 저울';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8-sig'))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261022\|([^"\s]+)',base64.b64decode(ev(k+'-fchart.raw')['raw'])).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==5533.77 and L['close']==66770
assert float(ev('KOSPI-basic')['data']['closePrice'].replace(',',''))==K['close']
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO','META','TSLA']:
 d=json.loads(base64.b64decode(ev('after-'+k+'.raw')['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f"|{k}|{c:,.2f}|{(c/d['meta']['regularMarketPrice']-1)*100:+.2f}%|{at}|")
aftertable='\n'.join(after)
sources=[('Meta 3분기 실적','https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Third-Quarter-2026-Results/default.aspx'),('한국은행 10월22일 결정',ev('BOK-decision.raw')['url']),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('미 재무부',ev('Treasury.raw')['url']),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉','https://fchart.stock.naver.com/sise.nhn?symbol=KOSPI&timeframe=day&count=5&requestType=0'),('미국 실업수당','https://www.dol.gov/ui/data.pdf'),('미시간대 소비심리','https://www.sca.isr.umich.edu/'),('FOMC','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),('FRED 금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
notes='''# 2026-10-23 취재 노트

사전 환경 점검·탐색07:56~07:59, 정식08:00 이후 재확인·원고 작성. 실제 시각 사용. kospi→write-finished-manuscript→humanize-korean→Amplify 순서.

## 이슈 레이더
|후보|점수|사실·전달 경로·제외 경계|
|---|---:|---|
|Meta 투자·현금흐름 부담|14|회사10/21 실적 원문 웹 열람. 매출646.01억달러+26%, FCF -21.2억달러, 연CAPEX1350~1450억달러. 공급업체 수요와 고객 자금부담 분리|
|미국 반도체 급락|14|SOXX-6.79%,SMH-5.99%,AMD-8.10%. 10/22 정규장·시간외 별도. 한국 전일-3.52% 중복 충격 금지|
|유가 상승·이란 위험|11|CL·BZ 연속선물 최근거래. 계약월 롤과 현물수익률 혼동 금지. 지정학의 확정되지 않은 협상결과 제외|
|금통위 동결·추가인상 여지|11|공식10/22 기준금리3% 만장일치동결. 향후 인상 시기·속도 판단 문구, 완화로 오독 금지. 전일한국 반영|
|Lam 실적·장비주 약세|8|회사뉴스룸 실적발표 존재, 원문숫자 상세 추가확인 전 공개 금액 생략|
|메모리 현물|9|10/22 18:10 GMT+8 DDR5 61.10 +0.38%, DDR4 83.117 보합. 주가·현물수급 분리|
|미국 신규실업수당|8|DOL data.pdf 웹 원문10/22,194000·전주수정200000. 직접다운로드403은 원문웹열람과 구분|
|Meta 신주종류·주식배당|10|무의결권C주2027/1 신설과1주당1주 배당. 향후 자금조달 수단 확보이며 현금증자 완료·조달액 확정 아님|
|청산·규제·확정공급계약|4|최신 헤드라인·기업원문·주가 탐색. 오늘 확정금액으로 쓸 신규지배사건 미확인. 공개 비사건 생략|

## 사실 경계
Meta 발표는10/22한국장 전 이미 알려짐. KOSPI-3.52%와 미국 후행매도 전부를 독립 악재로 합산하지 않음. Nvidia 공급망 증설도 전일 재료. 새 판단에는 미국 매도 강도·시간외 종목별차이·오늘NXT·선물·원화 반응 사용.
전일KOSPI5533.77 OHLC5670.11/5740.28/5485.98/5533.77; KODEX66770 OHLC70280/72300/65385/66770. fchart·basic·stock price 교차. integration 개인3667+외국인505-기관4599=-427억원, 합계정합 및 최종정본묶음 미확보로 금액 보류. 프로그램-3294억원·시장폭174/32/709도 원문만 보존, 확정묶음 미인증. exact15:20 앵커 미확보.
전일 기본5600~5800 실패, 약세5350~5600 종가적중. 90% 경로5250~6100 안. 수급조건 원인판정 불가. 누적평가기 기존9/21해시불일치로 실패, active가설 없고 오래된 적중률 미사용.
HBM·서버DRAM·eSSD 신규계약 물량·가격 미확인. NAND 공개표10/12·계약8월, 최신으로 쓰지 않음. FRED 복구10/22 금리차0.31/0.74%p. Treasury10/22 3M4.22·2Y4.65·10Y4.96, FRED개별금리10/21과 혼합차감 금지.
휴장 공식KRX URL404·검색은10/23거래일. 최종 NXT OPEN·실거래량과 한국은행 달력 교차로 오늘 개장 상태 확인. PMI오늘22:45KST 보조캘린더 일치하나 공식403, 내부 잠정일정만. 미시간대공식10/23 10ET=23KST, FOMC10/27~28ET 확정.
새 이미지: 밝은 하늘·유리저울의 AI칩/웨이퍼와 원유·추. built-in imagegen, 기존이미지 참조 없음,1200×630 시각검수.
'''
write('research/notes/'+DATE+'.md',notes+'\n'+'\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n')
body='''<p>AI 설비 투자가 커질수록 반도체 주문은 늘지만, 그 비용을 감당할 기업의 현금흐름에는 부담이 쌓입니다. 미국 22일 정규장에서 SOXX는 6.79%, SMH는 5.99% 하락했습니다. 전일 3.52% 내린 KOSPI는 오늘 5,486선 부근에서 매도가 잦아드는지 시험하게 됩니다.</p>
<h2>매출이 늘어도 투자비가 더 빨리 나간다</h2><p>Meta의 3분기 매출은 646억달러로 전년보다 26% 늘었습니다. 그러나 설비 투자 등을 반영한 잉여현금흐름은 21억2천만달러 적자였습니다. 올해 자본지출 전망은 1,350억~1,450억달러입니다. AI가 광고 매출을 키우고 있어도 대규모 인프라 투자금을 회수하는 데는 시간이 걸립니다. <a href="https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Third-Quarter-2026-Results/default.aspx">Meta 실적 발표</a></p>
<p>Meta는 내년 1월 무의결권 C주 신설과 기존 주식 한 주당 C주 한 주를 배당하는 계획도 밝혔습니다. 향후 자금 조달 등에 쓸 주식을 확보하려는 조치입니다. 이번 발표 자체가 현금을 받는 증자를 완료했다는 뜻은 아닙니다.</p>
<h2>반도체주는 급락 뒤 시간외에서 갈렸다</h2><p>Nvidia는 정규장에서 4.40%, AMD는 8.10%, Micron은 6.26%, Broadcom은 4.31% 내렸습니다. 시간외에서는 Nvidia·AMD·Broadcom이 소폭 반등한 반면 Micron은 추가로 밀렸습니다. 지수 전체가 일제히 회복하는 흐름과는 거리가 있습니다.</p>
<p>Meta 실적과 AI 투자 부담은 전일 한국장에서도 이미 알려졌습니다. 국내 하락과 뒤이은 미국 매도를 서로 독립된 충격으로 모두 더하면 오늘의 하락 압력을 과대평가할 수 있습니다. 미국 매도가 삼성전자·SK하이닉스의 오늘 가격에 얼마나 더 반영되는지, 개장 뒤 매수가 이어지는지가 중요합니다.</p>
<h2>DDR5 현물은 올랐지만 주가는 흔들린다</h2><p>22일 대만시간 오후 6시 10분 기준 DDR5 16Gb 현물 평균은 61.10달러로 0.38% 올랐습니다. DDR4 16Gb는 83.117달러로 보합입니다. 현물시장의 가격 지지와 주식시장의 투자비·밸류에이션 부담이 동시에 나타납니다. DDR 현물 움직임을 HBM과 서버 메모리의 계약 단가 전체로 넓혀 읽을 수는 없습니다. <a href="https://www.trendforce.com/price/dram/dram_spot">TrendForce</a></p>
<p>미 재무부의 22일 금리는 3개월물 4.22%, 2년물 4.65%, 10년물 4.96%입니다. 10년물은 전일 5.13%보다 낮아졌습니다. 금리 하락은 성장주의 할인율 부담을 덜지만, 유가 상승은 기업 비용과 물가를 다시 압박합니다. 한국은행도 전일 기준금리를 3.00%로 동결하면서 향후 인상의 시기와 속도를 판단하겠다고 밝혔습니다. <a href="https://www.bok.or.kr/eng/bbs/E0000634/view.do?nttId=11065825&amp;menuNo=400069">한국은행 결정</a></p>
<h2>전일 저점과 종가 사이에서 매수를 시험한다</h2><p>전일 KOSPI는 5,740.28까지 올랐다가 5,485.98까지 밀린 뒤 5,533.77로 마쳤습니다. 오늘은 전일 저점 부근을 지키는지, 종가를 회복한 뒤에도 외국인·프로그램 매수가 이어지는지를 나눠 봅니다.</p>
<p>기본 종가 범위는 5,350~5,550(45%)으로 봅니다. 외국인·프로그램 순매수와 함께 5,550선을 넘기는 강세 범위는 5,550 초과~5,700(15%), 5,350선 아래에서 매도가 이어지는 약세 범위는 5,100~5,350 미만(40%)입니다. 5,550선 재이탈은 강세 판단을, 5,350선 회복은 약세 판단을 무효로 만듭니다. 예상 범위 밖의 변동도 가능합니다.</p>
<p>KODEX 레버리지는 전일 저점 65,385원을 첫 지지, 종가 66,770원을 반등 기준, 고점 72,300원을 저항으로 봅니다. 65,385원 아래에서 회복하지 못하면 전일 저점의 지지력을 전제로 한 판단은 접습니다. 오늘 밤 11시에는 미시간대 10월 소비심리 확정치가 나오고, 미국시간 27~28일에는 FOMC가 열립니다. 개장 초 가격보다 오전 10시와 오후 2시의 매수 지속 여부를 확인할 필요가 있습니다.</p>'''
write('research/evidence/'+DATE+'/body.html',body)
report=f'''# {DATE} KOSPI·KODEX 장전 리서치

작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전. 미국10/22 정규장 종료·시간외. 원천 지연 가능.

## 핵심 결론
{SUMMARY} 기본5350~5550(45%),강세5550초과~5700(15%),약세5100~5350미만(40%). 공격5·관망40·방어55. 90% 장중포락4950~5850. 수동 조건부 판단이며 점수는 확률과 별개.

## 밤사이 시장을 지배한 이슈
Meta FCF-21.2억달러·연CAPEX1350~1450억달러, C주신설은 자금조달수단 확보로 현금증자 완료 아님. 미국 반도체 급락·원유 부담. 후보9건·제외근거는 취재노트. Meta실적·Nvidia공급망·금통위10/22한국 반영분과 후행미국매도 중복합산 제외. 신규 판단은 미국매도강도·시간외차이·NXT/선물/환율 반응.

## 한국시장·KODEX 대시보드와 회고
|항목|10/22 시가|고가|저가|종가|
|---|---:|---:|---:|---:|
|KOSPI|5670.11|5740.28|5485.98|5533.77|
|KODEX|70280|72300|65385|66770|
KOSPI-3.52%,KODEX-6.93%,KODEX거래량23246556주. fchart/basic/stock price교차. 전일 기본실패·약세종가적중·경로포락내. 수급exact앵커없어 원인조건 미검증. 투자주체합계-427억원 정합미확인, 프로그램·시장폭 최종묶음 보류. 미확인수급 0채우지 않음.

## 메모리 반도체 수급
10/22 18:10 GMT+8 DDR5 16Gb61.10달러+0.38%,DDR4 16Gb83.117보합. 현물지지와 주식투자비부담 분리. HBM·서버DRAM·eSSD 신규계약 물량/단가미확인. NAND10/12·공개계약8월을 최신으로 쓰지 않음.

## 미국 반도체·AI 정규장
|종목|10/22종가 USD|등락|
|---|---:|---:|
{ustable}
10/22 16:00 ET=10/23 05:00KST. 일봉연속값 계산.

## 미국 시간외
|종목|USD|종가대비|원천시각 KST|
|---|---:|---:|---|
{aftertable}
진행중 유효봉으로 확정종가 아님.

## 달러/원·선물·NXT
FAST_TABLE
하나은행고시·연속선물최근거래·NXT와KRX 구분. 선물계약월롤을 현물당일등락으로 계산하지 않음.

## 경제 캘린더
한국은행10/22 3.00%만장일치동결, 향후인상시기/속도판단. DOL10/22 신규실업수당194000(전주수정200000), 계속수급1728000. 미시간대공식10/23 10ET=23KST확정치. PMI10/23 22:45KST보조출처일치·공식403으로 잠정일정. FOMC10/27~28ET.

## 미 국채와 장단기 금리차
Treasury10/22 3M4.22·2Y4.65·10Y4.96%, 전일4.25/4.81/5.13대비 -3/-16/-17bp. FRED10/22 10Y-2Y0.31·10Y-3M0.74%p. 장기금리급락으로 금리차축소. FRED개별금리10/21과 최신스프레드 혼합차감 금지. FRED복구로2년·90일차트 생성.
![90일](../charts/us_yield_spreads_90d_{DATE}.png)
![2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 오늘 시나리오·무효화
강세15%5550초과~5700:15:20지수>5550 AND 외국인>0 AND 프로그램>0,5550재이탈무효.
기본45%5350~5550:지수>=5350 AND <=5550 AND 외국인>=-8000억원,범위이탈·매도확대무효.
약세40%5100~5350미만:지수<5350 AND 외국인<0 AND 프로그램<0,5350회복무효.
KOSPI5350/5486/5550,KODEX65385/66770/72300. KODEX65385이탈미회복 지지무효. 09:30·10:00수급동행,14:00반전,15:20조건. 한시점매수의 지속성 단정금지.

## 출처와 확인 시각
취재원문 fetchedAt/rawHash는 research/evidence/{DATE}/. Meta·DOL은 웹원문별도열람, 직접403구분. 최종가격 각행원천시각.
'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
# 재사용 범위는 기존 기사 구조와 목록 마크업이다.
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index('s=prior;s.update')]
tail=tail.replace("oldimage='market-2026-10-19-memory-credit-1200x630.png'","oldimage='market-2026-10-22-ai-capacity-bok-1200x630.png'")
for a,b in [('2026.10.20','2026.10.23'),('2026.10.19','2026.10.22'),('2026-10-19','2026-10-22'),('10월 19일','10월 22일')]:tail=tail.replace(a,b)
exec(tail)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(snapshotId='20261023-prepared',generatedAt=NOW,asOf=NOW,asOfDisplay=NOW,sourceLabel='미국10월22일 정규장·국내10월22일 종가·10월23일 장전',headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'})
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='확정값 미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=-3.52,open=K['open'],high=K['high'],low=K['low'],previousClose=5735.66,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월22일 정규장 종가')
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'최종 묶음 검증 보류'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'전일 저점과 매수 지속 확인','attack':5,'wait':40,'defense':55,'note':'미국 반도체 급락 뒤 시간외 흐름이 갈렸습니다. 전일 저점 방어와 매수 지속을 함께 봅니다.'}
s['changes']=[{'label':'KOSPI','before':'5,735.66','after':'5,533.77','meaning':'장중 고점에서 밀려 전일 저점 부근에서 마쳤습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX -6.79% · SMH -5.99%','detail':'10월22일 정규장·시간외 종목별 차이','tone':'warning'},{'label':'AI 투자비','metric':'Meta FCF -21.2억달러','detail':'수요 증가와 고객 자금 부담이 함께 나타납니다.','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/22','value':'$61.10','change':'+0.38%'},{'label':'DDR4 16Gb · 10/22','value':'$83.117','change':'0.00%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,350','pivot':'5,486','resistance':'5,550'},{'asset':'KODEX 레버리지','support':'65,385원','pivot':'66,770원','resistance':'72,300원'}]
s['scenarios']=[{'id':k,'label':label,'range':ran,'summary':summ,'conditions':cond,'invalidation':inv} for k,label,ran,summ,cond,inv in [('bull','강세 · 15%','KOSPI 5,550 초과~5,700','매수가 동행하는 회복',['5,550 초과','외국인 순매수','프로그램 순매수'],'5,550 재이탈'),('base','기본 · 45%','KOSPI 5,350~5,550','전일 저점의 지지력 시험',['5,350 이상','5,550 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 매도 확대'),('bear','약세 · 40%','KOSPI 5,100~5,350 미만','하단 지지 실패',['5,350 미만','외국인 순매도','프로그램 순매도'],'5,350 회복')]]
s['events']=[{'time':'10월23일 23:00 KST','name':'미시간대 소비심리 확정치','path':'물가 기대·금리'},{'time':'10월27~28일 ET','name':'FOMC','path':'금리·AI 자금 조달'}];s['checklist']=[{'id':'support','label':'전일 저점 5,486선 방어'},{'id':'rebound','label':'5,550선 회복과 외국인·프로그램 매수 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5350,5486,5550] if x['id']=='KOSPI' else [65385,66770,72300];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월22일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월22일 확정 일봉과 10월23일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s);dump('research/evidence/'+DATE+'/prepared.json',{'title':TITLE,'summary':SUMMARY,'image':IMAGE,'asOf':NOW,'imageMode':'built-in imagegen','imagePrompt':'Bright glass seesaw balancing AI wafer and processor against oil barrel and funding weights; no text, new composition.'})
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5533.77(-3.52%),KODEX66770(-6.93%). 투자주체합계정합·정본묶음 미확인.\n- Meta AI투자비·FCF적자와 미국반도체매도. 전일한국반영분 중복가산 제외.\n- 다음 미시간대10/23 23KST·FOMC10/27~28ET.\n- 기본5350~5550(45%),강세5550초과~5700(15%),약세5100~5350미만(40%),대응5/40/55.\n- 보고서 reports/{DATE}.md,취재 research/notes/{DATE}.md,차트 charts/us_yield_spreads_*_{DATE}.png.\n- 직전기본실패·약세종가적중. 수급exact앵커미확보. actuals/2026-10-22.json·outcomes/2026-10-22-0808-same-close.json. 누적 기존9/21해시불일치.\n')
for page in ['index.html','articles/index.html','articles/market.html']:
 t=read(page)
 def card(m):
  if 'market-'+DATE+'.html' in m[0]:
   c=re.sub(r'2026\.10\.\d{2}', '2026.10.23',m[0]);c=re.sub(r'10월 \d{1,2}일','10월 23일',c);return re.sub(r'2026-10-\d{2}T[^"< ]+',NOW,c)
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 t=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,t,flags=re.S)
 if page=='index.html':t=t.replace('market-2026-10-22-ai-capacity-bok-1200x630.png',IMAGE)
 if page=='articles/market.html':t=t.replace('공급망 투자와 금통위 뒤 매수','전일 저점 방어와 매수 지속')
 write(page,t)
t=read('sitemap.xml')
for u in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:t=re.sub(r'(<loc>'+re.escape(u)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+DATE,t)
write('sitemap.xml',t)
print('prepared',NOW)
