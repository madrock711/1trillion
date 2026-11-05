"""오늘의 검증된 취재 결과를 공통 발행기에 넘기는 입력 패키지. 발행 로직은 scripts에 둔다."""
import base64,datetime,html,importlib.util,json,re,sys
from pathlib import Path
from PIL import Image
R=Path.cwd();P=Path(__file__).parent;D='2026-11-05';PREV='2026-11-04';TZ=datetime.timezone(datetime.timedelta(hours=9));at=datetime.datetime.now(TZ).isoformat(timespec='seconds')
E=P/'collections/083512-536584'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,s):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(s,encoding='utf-8',newline='\n')
def ev(k):return load(E/(k+'.json'))
def n(v):return float(str(v).replace(',',''))
regular=[]
for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO']:
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0];v=[(i,c) for i,c in enumerate(q['close']) if c];i,c=v[-1];_,prev=v[-2]
 regular.append(f'|{k}|{q["open"][i]:,.2f}|{q["high"][i]:,.2f}|{q["low"][i]:,.2f}|{c:,.2f}|{(c/prev-1)*100:+.2f}%|')
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(load(P/f'after-{k}.raw.json')['raw']))['chart']['result'][0];period=d['meta']['currentTradingPeriod']['post'];values=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and period['start']<=t<period['end']]
 t,c=values[-1];after.append(f'|{k}|{c:,.2f}|{(c/d["meta"]["regularMarketPrice"]-1)*100:+.2f}%|{datetime.datetime.fromtimestamp(t,TZ).isoformat()}|')
us='|종목|시가 USD|고가|저가|종가|등락|\n|---|---:|---:|---:|---:|---:|\n'+'\n'.join(regular)
aft='|종목|시간외 USD|정규장 대비|원천 시각 KST|\n|---|---:|---:|---|\n'+'\n'.join(after)
sources=[
 ('미국 정규장·시간외','https://finance.yahoo.com/quote/SOXX/'),
 ('미국 선거 이후 시장','https://live.euronext.com/en/financial-news/world-shares-advance-democrats-victory-eases-political-uncertainty'),
 ('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),
 ('Siltronic 실적','https://www.siltronic.com/en/press/press-releases/siltronic-slightly-raises-sales-guidance-for-2026-higher-demand-drives-volume-development-in-q3-2026.html'),
 ('Qualcomm·Starlink 공급 발표','https://www.qualcomm.com/news/releases/2026/11/spacex-selects-qualcomm-to-accelerate-starlink-mobile-s-nationwi'),
 ('BLS 공식 일정','https://www.bls.gov/schedule/2026/11_sched.htm'),
 ('FRED 금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
notes=f'''# {D} 취재 노트
실제 재개 {at}. 최초 자동 실행에서 수집 뒤 종료한 사실과 구분. 오늘 아직 공개 기사 없음. 이후 발행기는 현재 시각에 따라 장전/장중을 자동 분리한다.

## 이슈 레이더 순위와 전달 경로
1. 미국 지수/반도체 분화: QQQ +0.97%, SOXX -3.14%, SMH -2.75%, MU -7.00%. Reuters 선거 후 위험선호와 데이터센터 규제 우려 해석, 정규장 시세 원문 교차. 한국 반도체 비중에 직접 하방. 새 법률 확정으로 쓰지 않음.
2. 미국 유가·달러 하락: Reuters Brent 정산94.62달러 약9%하락, 10Y시장수익률4.88%와 달러약세. 수입물가/할인율 완화는 반론. 가격과 투자자 해석 분리.
3. DRAM 11/4 18:10GMT+8: DDR5 16Gb61.333(-0.27%), DDR4 16Gb81.926(-0.96%). HBM/서버계약가와 동일시 금지.
4. Siltronic 11/4 공식 매출3.554억유로·전분기+10.5%, 300/200mm 판매량 증가. 공급망 실수요는 유지된다는 반론. 보도 CEO의 PC생산 제약은 공식 숫자와 구분.
5. Qualcomm 11/4 실적 공개 자체 공식확인(브라우저 web 원문); 수치표 접근불가로 실적금액/전망 새 숫자 제외. Starlink용 Dragonwing 공급·2027년 전국망 전개 착수 계획은 공식 원문 확인. 한국 HBM확정계약으로 해석하지 않음.
6. AMD 전일 실적/성장 전망: 어제 국내장에 이미 반영한 Q3 매출/가이던스는 오늘 새 충격으로 중복 가산하지 않음. 오늘 미국 정규장AMD +1.01은 다른 반도체와 분리.
7. Nvidia 중국고객 이용비중 규제 보도: 최초보도 전일, 공식문서 미확정. 오늘 규제확정 사실로 쓰지 않음.
8. 강제청산/블록딜/증자 탐색: 오늘 시세하락을 특정청산으로 확정할 1차근거 없음. Siltronic 6월증자는 과거사건이므로 새증자로 쓰지 않음.

## 자료 한계와 시각
Python BLS/Qualcomm403은 web 도구 공식 원문으로 대체. NAND 공개 현물/웨이퍼표는10/26, PC-SSD표8/5로 오늘 신규가격 제외. HBM/RDIMM/eSSD계약단가 공개값 없음. 국내 최종 수급·프로그램·폭·선물 묶음은 전일 종료원천 상태를 확인할 수 없어 임의0으로 채우지 않음. FRED 11/4 스프레드0.32/0.69, 개별금리11/3 4.21/4.61/4.95는 기준일 혼합 차감 금지.

## 전일 평가
11/4 KOSPI OHLC5786.13/5828.13/5421.72/5683.80(+0.62%), KODEX73605/75205/64115/70500(+0.58%)·35301275주. 기본5700~5900 실패·약세종가범위. 저가5421.72는전체일봉, 발행뒤발생시각은일별자료만으로확정불가. 발행후경로·조건수급미확정으로미검증. 오늘 범위를 정하는 단일표본성공법칙으로 쓰지 않음.

## 확정 전망과 이미지 방향
기본5500~5750(50%),강세5750초과~5900(15%),약세5250~5500미만(35%),90%경로5200~6000. 공격5/관망40/방어55. 강/약은15:20 지수경계+외국인현물+전체프로그램 AND. 기본은지수범위와프로그램>=0 OR 지수범위와외국인>=0 대신 정본지원상 기본지수범위조건만 사용, 서술조건은 환율/메모리주의 지속관찰로 분리.
KODEX64115/70500/73605는전일저가/종가/시가. 추격상승보다갭회복·수급확인.
이미지: 대형기술주유입과 AI설비제약의분화, 밝은석회광장·청색저수조/좁은산호수문. 기존칩/도약대와다른소재. 생성완료후원본보존·1200x630포장.
집필→구조퇴고→humanize-korean 사실고정윤문을 적용. 내부제작과정은공개본문제외.

## 출처
'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)
write(R/f'research/notes/{D}.md',notes)
body='''<p>미국 증시가 올랐다고 한국 반도체주까지 같은 방향으로 움직일 여건은 아닙니다. 밤사이 대형 기술주는 반등했지만 반도체와 메모리는 다시 밀렸습니다. 오늘 코스피는 미국 지수의 상승률보다 삼성전자·SK하이닉스가 매물을 받아내는지, 외국인과 프로그램 수급이 함께 돌아서는지가 중요합니다.</p>
<h2>기술주는 올랐지만 메모리주는 팔렸다</h2>
<p>4일 미국 정규장에서 QQQ는 0.97%, TQQQ는 2.79% 올랐습니다. 반면 SOXX는 3.14%, SMH는 2.75% 하락했습니다. Nvidia는 3.17%, Micron은 7.00%, Broadcom은 2.00% 떨어졌고 AMD만 1.01% 상승했습니다. 같은 기술주 안에서도 투자자들이 서로 다른 가격을 매겼습니다. <a href="https://finance.yahoo.com/quote/SOXX/">미국 반도체 시세</a></p>
<p>미국 중간선거 이후 정책 불확실성 완화가 주식시장 전반에 힘을 보탰습니다. 동시에 데이터센터 규제 강화 가능성이 AI 설비투자 관련주에는 부담으로 작용했습니다. 이는 앞으로의 정책에 대한 시장의 기대이며, 데이터센터 투자가 일제히 중단됐다는 뜻은 아닙니다. 코스피에서 비중이 큰 메모리주에는 미국 증시 전체의 상승보다 반도체 업종의 약세가 더 직접적인 신호입니다. <a href="https://live.euronext.com/en/financial-news/world-shares-advance-democrats-victory-eases-political-uncertainty">선거 이후 시장 반응</a></p>
<h2>메모리 현물도 약해졌다</h2>
<p>4일 대만시간 오후 6시 10분 DRAM 현물 세션에서 DDR5 16Gb 평균은 61.333달러로 0.27%, DDR4 16Gb는 81.926달러로 0.96% 내렸습니다. 현물가격과 Micron 주가가 함께 하락한 만큼 단기 가격 부담을 가볍게 보기 어렵습니다. 다만 이 표는 범용 DRAM 현물입니다. HBM과 서버용 메모리의 계약 수요까지 같은 폭으로 줄었다고 해석할 수는 없습니다. <a href="https://www.trendforce.com/price/dram/dram_spot">DRAM 현물가격</a></p>
<p>공급망 실적에는 다른 신호도 있습니다. Siltronic은 3분기 매출이 전분기보다 10.5% 늘어난 3억5,540만유로라고 발표했고, 300mm와 200mm 웨이퍼 판매량 증가를 설명했습니다. 최종 수요가 모두 무너졌다기보다 실수요와 주식시장의 투자 속도 우려가 충돌하는 국면입니다. <a href="https://www.siltronic.com/en/press/press-releases/siltronic-slightly-raises-sales-guidance-for-2026-higher-demand-drives-volume-development-in-q3-2026.html">Siltronic 실적</a></p>
<h2>유가 하락은 완충재, 국내 수급은 별도 변수</h2>
<p>브렌트유 선물은 94.62달러에 정산되며 약 9% 하락했습니다. 유가와 달러의 약세는 한국의 수입 비용과 물가 부담을 낮추는 방향입니다. 이 효과가 반도체 매도를 얼마나 상쇄하는지는 국내 거래에서 갈립니다. 어제 코스피는 0.62% 올랐지만 5,828.13에서 5,421.72까지 큰 폭으로 흔들린 뒤 5,683.80에 마감했습니다. 상승 마감만으로 매도 압력이 해소됐다고 보기는 어렵습니다.</p>
<p>오늘 기본 종가 범위는 5,500~5,750에 확률 50%를 둡니다. 5,750을 넘고 외국인 현물과 프로그램이 함께 순매수하면 5,750 초과~5,900의 강세 시나리오 15%를 봅니다. 5,500 아래에서 두 수급이 순매도를 이어가면 5,250~5,500 미만의 약세 시나리오 35%에 무게를 둡니다. 기본 범위는 경계 이탈, 강세는 5,750 재이탈, 약세는 5,500 회복을 무효화 기준으로 삼습니다.</p>
<p>KODEX 레버리지는 전일 저가 64,115원, 종가 70,500원, 시가 73,605원을 차례로 지지·반등 기준·저항으로 봅니다. 대응은 공격 5·관망 40·방어 55입니다. 미국 지수 상승에 곧바로 기대기보다 메모리주 저점과 외국인·프로그램 매매가 함께 개선되는지 살필 때입니다.</p>
<h2>오늘 밤 생산성, 내일 밤 고용</h2>
<p>미국 3분기 생산성·단위노동비용 잠정치는 오늘 오후 10시 30분, 10월 고용보고서는 내일 오후 10시 30분 한국시간에 예정돼 있습니다. 임금·고용 지표가 금리 기대를 바꾸면 반도체 밸류에이션도 다시 움직일 수 있습니다. FRED의 4일 금리차는 10년물-2년물 0.32%포인트, 10년물-3개월물 0.69%포인트입니다. <a href="https://www.bls.gov/schedule/2026/11_sched.htm">BLS 일정</a> · <a href="https://fred.stlouisfed.org/series/T10Y2Y">FRED 금리차</a></p>
<h2>발행 기준 시세</h2>{{fastTable}}<p class="article-disclosure">환율은 하나은행 고시환율이며 선물과 NXT는 각 행에 적힌 원천 시각의 최근 거래값입니다.</p>'''
write(P/'article-body.html',body)
report='''# 2026-11-05 KOSPI·KODEX 일일 리서치
작성 {{issuedAt}} / 최종 데이터 확인 {{cutoff}} / 한국 {{marketLabel}}
미국 정규장 11/4 종가, 시간외 원천별 시각을 분리. 선물은 지연 최근거래이며 환율은 하나은행 고시.

## 핵심 결론
미국 대형기술주 상승과 반도체 약세 분리. Micron -7%와 DDR5/DDR4 현물 하락이 국내 메모리주에 직접 하방. 유가/달러약세는 완충. 공격5 관망40 방어55.

## 밤사이 시장을 지배한 이슈
선거결과확인→정책불확실성완화와 데이터센터규제우려의 상반경로. 새법률확정아님. AI설비투자속도우려와 웨이퍼실수요구분. 상세후보·반론은 research/notes/2026-11-05.md.

## 전일 대비 바뀐 변수와 유지 변수
새재료는 전일한국장후 미국반도체분리약세·11/4 DRAM현물하락·미국유가급락. 어제국내장반영 AMD Q3실적을 오늘새호재로 중복가산하지 않음. HBM/서버수요확정급감주장안함.

## 한국시장·KODEX 대시보드
전일 KOSPI5786.13/5828.13/5421.72/5683.80(+0.62%), KODEX73605/75205/64115/70500(+0.58%)·35301275주. 실제값은 오늘새로조회한전일일봉원천.
{{fastTable}}

## 메모리 반도체 수급
11/4 18:10GMT+8 DDR5 16Gb61.333(-0.27%),DDR4 16Gb81.926(-0.96%). HBM/RDIMM/서버DDR5/eSSD 신규계약가격 미확인. NAND 공개표는10/26·PC-SSD8/5 기준으로오늘가격에대입하지않음. Siltronic웨이퍼실수요와주식리스크프리미엄분리.

## 미국 반도체·AI
11/4 미국정규장 USD OHLC. 가격/고가반납을표에서대조.
US_TABLE

## 미국 시간외
정규장종가대비이며정규장등락과합산안함.
AFTER_TABLE

## 달러/원·국내 수급·시장 구조
환율고시/선물/NXT기준시각은위표. 외국인현물/선물·기관세부·프로그램·시장폭은거래일/종료상태가맞는최종묶음미확보로미확인.0대입하지않음. 반도체지수영향과유가하락수혜업종확산을별도관찰. 발생확인없는사이드카·청산은사건으로쓰지않음.

## 경제 캘린더
11/5 08:30ET=22:30KST 생산성/단위노동비용잠정.11/6 08:30ET=22:30KST10월고용.11/18 14:00ET=11/19 04:00KST10/27~28FOMC의사록.실제발표전수치없음. BLS/Fed공식달력확인.

## 미 국채와 장단기 금리차
FRED11/4 10Y-2Y0.32%p,10Y-3M0.69%p.개별금리최근공개11/3 3M4.21%,2Y4.61%,10Y4.95%. Reuters11/4시장10Y4.88%와종가/표시시각다름.개별금리기준일을섞어스프레드를재계산하지않음.
![장기 금리차](../charts/us_yield_spreads_long_term_2026-11-05.png)
![90일 금리차](../charts/us_yield_spreads_90d_2026-11-05.png)

## 오늘 KOSPI·KODEX 시나리오
기본5500~5750 50%:범위유지조건·환율급등억제/메모리저점안정관찰. 경계이탈무효.
강세5750초과~5900 15%:5750초과 AND외국인현물>0 AND전체프로그램>0.5750재이탈무효.
약세5250~5500미만35%:5500미만 AND외국인현물<0 AND전체프로그램<0.5500회복무효.
가격경계는기본구간우선.15:20관측,다음점검09:30/10:00/14:00.90%잔여장중포락5200~6000. 공격5 관망40 방어55. KODEX64115지지/70500반등/73605저항.

## 전일 전망 평가
기본5700~5900실패,5683.80약세종가범위.일별저가5421.72의발행후시각은자료미확보. 수급조건과발행후경로는미검증.단일표본으로가설승격안함.

## 장중 체크리스트
반도체저점·수급동행·5500/5750·USD/KRW·유가하락업종확산.한축만개선되면공격판단유보. 대응점수는확률이아님.

## 출처와 확인 시각
SOURCE_LIST
취재원문조회08:51KST전후,최종국내조회는첫부분시각. BLS/Qualcomm직접403은web공식원문열람으로확인.자세한원천·해시는research/evidence/2026-11-05에보존.
'''.replace('US_TABLE',us).replace('AFTER_TABLE',aft).replace('SOURCE_LIST','\n'.join(f'- [{a}]({b})' for a,b in sources))
write(P/'report-template.md',report)
# 전일 확정값은 조회한 일봉만 사용한다.
a=load(R/'research/evaluation/actuals/2026-11-03.json');a.update(sessionDate=PREV,bizdate='20261104',fetchedAt=at)
for key,k in [('kospi','KOSPI'),('kodex','122630')]:
 d=ev(k);v=next(x for x in d['data'] if x['localTradedAt']==PREV)
 a[key]={x:n(v[y]) for x,y in [('open','openPrice'),('high','highPrice'),('low','lowPrice'),('close','closePrice')]};a[key].update(asOf=PREV+'T15:30:00+09:00',source=d['url'],rawHash=d['rawHash'])
 if key=='kodex':a[key]['volume']=v['accumulatedTradingVolume']
reason='조회시점은다음날장전이며전일최종수급묶음및발행후분봉경로의시각/상태정본을확보하지못함'
a['closeSnapshotMissingReason']=reason;a['flowTrajectoryMissingEvidence'].update(asOf=PREV+'T15:30:00+09:00',fetchedAt=at,missingReason=reason,rawHash=ev('KOSPI-integration')['rawHash'])
ap=R/f'research/evaluation/actuals/{PREV}.json'
if not ap.exists():dump(ap,a)
f=load(R/'research/evaluation/forecasts/2026-11-04-0916-same-close.json');fid=f['forecastId']
o={'schemaVersion':1,'forecastId':fid,'recordedAt':at,'actualRef':PREV,'realizedScenario':'bear','errorCodes':['cause_unverifiable'],'triggerResults':[{'id':c['id'],'status':'unavailable','reason':reason} for t in f['scenarioTriggers'].values() for c in t['conditions']],'driverAssessment':[{'id':d['id'],'status':'unverifiable'} for d in f['drivers']],'hypothesisTests':[],
 'postForecastPathStatus':'missing','postForecastPathMissingReason':reason,'postForecastPathMissingEvidence':{'sourceStatus':'incomplete','source':ev('KOSPI')['url'],'asOf':PREV+'T15:30:00+09:00','fetchedAt':at,'rawHash':ev('KOSPI')['rawHash']}}
op=R/f'research/evaluation/outcomes/{fid}.json'
if not op.exists():dump(op,o)
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
m=runner.evaluation();pf=m.validate_forecast(f,R/f'research/evaluation/forecasts/{fid}.json',None);pa=m.validate_actual(a,ap);m.validate_outcome(o,op,pf,pa)
print('previous actual/outcome validated')
image=f'assets/images/articles/market-{D}-technology-watergate-1200x630.png'
Image.open('C:/Users/madro/.codex/generated_images/01a1a8ce-cedd-77a1-964f-9db2ba5f6bcc/exec-892d6bda-4331-4649-8386-b9029b2e4c5e.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
title='미국 증시는 올랐지만 반도체는 하락…코스피는 메모리주 매물 부담'
summary='미국 기술주 반등 속에서도 Micron은 7% 하락했고 DRAM 현물도 내렸습니다. 유가·달러 약세의 완충 효과와 국내 반도체 매물을 함께 봅니다.'
dash=load(R/'assets/data/market-dashboard-20261104-0916.json')
dash['headline']=title;dash['summary']=summary
dash['stance']={'label':'메모리 매물 부담','attack':5,'wait':40,'defense':55,'note':'미국 기술주 상승과 반도체 하락을 분리해 판단합니다.'}
dash['checkpoints']=[]
dash['changes']=[{'label':'KOSPI 전일','before':'5,648.79','after':'5,683.80','meaning':'0.62% 상승 마감했지만 장중 변동폭이 컸습니다.'}]
dash['factors']=[{'label':'미국 반도체','metric':'SOXX -3.14%','detail':'11월 4일 정규장','tone':'warning'},{'label':'미국 메모리','metric':'Micron -7.00%','detail':'11월 4일 정규장','tone':'warning'},{'label':'브렌트유','metric':'정산 $94.62','detail':'11월 4일 약 9% 하락','tone':'positive'}]
dash['memory']=[{'label':'DDR5 16Gb','value':'$61.333','change':'11/4 -0.27%'},{'label':'DDR4 16Gb','value':'$81.926','change':'11/4 -0.96%'}]
for market in dash['markets']:
 market['flows']=[]
 if market['id']=='KOSDAQ':market.update(value=None,changePercent=None,open=None,high=None,low=None,previousClose=None,asOf=PREV+'T15:30:00+09:00',asOfLabel='전일 종가 미확인',stateLabel='미확인')
dash['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'최종 묶음 미확인'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
dash['events']=[{'time':'11월 5일 22:30 KST','name':'미국 생산성·단위노동비용 잠정','path':'임금·물가·금리'},{'time':'11월 6일 22:30 KST','name':'미국 10월 고용보고서','path':'금리·성장주'}]
dash['strategyLevels']=[{'asset':'KOSPI','support':'5,500','pivot':'5,683.80','resistance':'5,750'},{'asset':'KODEX 레버리지','support':'64,115원','pivot':'70,500원','resistance':'73,605원'}]
conditions={'bull':['5,750 초과','외국인 현물 순매수','프로그램 순매수'],'base':['5,500 이상','5,750 이하','메모리주 저점과 환율 안정 관찰'],'bear':['5,500 미만','외국인 현물 순매도','프로그램 순매도']}
for row in dash['scenarios']:
 k=row['id'];row.update(label={'bull':'강세 · 15%','base':'기본 · 50%','bear':'약세 · 35%'}[k],range={'bull':'KOSPI 5,750 초과~5,900','base':'KOSPI 5,500~5,750','bear':'KOSPI 5,250~5,500 미만'}[k],summary='메모리주 매물과 외국인·프로그램 동행',conditions=conditions[k],invalidation={'bull':'5,750 재이탈','base':'5,500~5,750 이탈','bear':'5,500 회복'}[k])
dash['checklist']=[{'id':'memory','label':'삼성전자·SK하이닉스 저점과 수급 동행'},{'id':'price','label':'5,500 방어·5,750 회복'},{'id':'fx','label':'환율 안정과 유가 하락의 업종 확산'}]
dash['technical']['note']='오늘 리서치의 분석 기준선이며 시세 갱신으로 바뀌지 않습니다.'
for row in dash['technical']['instruments']:
 if row['id'] in ['KOSPI','KODEX']:
  row['levels']=[{'label':k,'value':v} for k,v in zip(['1차 지지','반등 기준','저항'],[5500,5683.8,5750] if row['id']=='KOSPI' else [64115,70500,73605])];row['interpretation']='메모리주 저점과 반등 기준선 회복을 살펴봅니다.'
dash['sources']=[{'label':a,'href':b} for a,b in sources]
dump(P/'dashboard-input.json',dash)
triggers={}
for kind in ['bull','base','bear']:
 cond=[]
 for id,metric,operator,threshold in ([('base-floor','kospi_price','gte',5500),('base-cap','kospi_price','lte',5750)] if kind=='base' else [(kind+'-price','kospi_price','gt' if kind=='bull' else 'lt',5750 if kind=='bull' else 5500),(kind+'-foreign','foreign_cash','gt' if kind=='bull' else 'lt',0),(kind+'-program','program_total','gt' if kind=='bull' else 'lt',0)]):
  cond.append({'id':id,'metricId':metric,'operator':operator,'threshold':threshold,'source':'Naver Finance KOSPI','description':id})
 triggers[kind]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':cond}
files=['.gitignore','AGENTS.md','scripts/publish_market_research.py','scripts/collect_market_evidence.py','tests/test_market_publication_pipeline.py','docs/MARKET_AUTOMATION_RELIABILITY.md','docs/현재작업중.md',image,f'charts/us_yield_spreads_long_term_{D}.png',f'charts/us_yield_spreads_90d_{D}.png',f'research/notes/{D}.md',str(ap.relative_to(R)).replace('\\','/'),str(op.relative_to(R)).replace('\\','/')]
files += [str(x.relative_to(R)).replace('\\','/') for x in P.glob('*.raw.json')]
files += [str(x.relative_to(R)).replace('\\','/') for x in E.glob('*.json')]
files += [str((P/f).relative_to(R)).replace('\\','/') for f in ['prepare_inputs.py','fetch_sources.py','article-body.html','report-template.md','dashboard-input.json','package.json']]
package={'date':D,'previousSessionDate':PREV,'title':title,'summary':summary,'image':image,'imageAlt':'밝은 광장의 넓은 청색 수로와 좁은 산호색 수문',
 'bodyPath':str((P/'article-body.html').relative_to(R)).replace('\\','/'),'reportTemplate':str((P/'report-template.md').relative_to(R)).replace('\\','/'),'dashboardPath':str((P/'dashboard-input.json').relative_to(R)).replace('\\','/'),'notesPath':f'research/notes/{D}.md',
 'scenarios':{'bull':{'low':5750,'high':5900,'probability':0.15},'base':{'low':5500,'high':5750,'probability':0.5},'bear':{'low':5250,'high':5500,'probability':0.35}},'pathEnvelope':{'low':5200,'high':6000,'coverage':0.9},'posture':{'attack':5,'wait':40,'defense':55},'marketRegime':'risk_off','scenarioTriggers':triggers,
 'drivers':[{'id':'semiconductor','rank':1,'claim':'미국 지수 상승과 반도체·메모리 하락의 분화','validationMetric':'미국 반도체·국내 반도체·KOSPI'},{'id':'memory','rank':2,'claim':'범용 DRAM 현물 하락과 국내 수급 부담','validationMetric':'TrendForce·외국인·프로그램'}],
 'stateText':'# KOSPI·KODEX 리서치 상태\n- 전일 KOSPI5683.80(+0.62%), KODEX70500(+0.58%).\n- 미국 지수상승/반도체하락분화·Micron-7%·DRAM현물하락, 유가/달러약세완충.\n- 기본5500~5750(50%),강세5750초과~5900(15%),약세5250~5500미만(35%),대응5/40/55.\n- 전일기본실패·약세종가범위, 수급조건/발행후경로미검증.\n- 다음11/5 22:30생산성·11/6 22:30고용. 전일평가는research/evaluation/outcomes/2026-11-04-0916-same-close.json.\n- 낮은순위제외:확정청산/증자근거없음·NAND공개표시차·AMD전일반영분중복제외.',
 'charts':[f'charts/us_yield_spreads_long_term_{D}.png',f'charts/us_yield_spreads_90d_{D}.png'],'files':files}
dump(P/'package.json',package)
status=load(P/'run-status.json');status['status']='prepared';status.setdefault('stages',{}).update(research=at,writing=at,image=at);status['artifacts']={'notes':f'research/notes/{D}.md','package':str((P/'package.json').relative_to(R)).replace('\\','/'),'image':image};dump(P/'run-status.json',status)
print('package prepared',at)
