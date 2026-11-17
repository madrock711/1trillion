import json,datetime as dt,sys,re,html,hashlib
from pathlib import Path
from PIL import Image
R=Path.cwd();P=Path(__file__).parent;D='2026-11-18';PREV='2026-11-17';E=P/'collections/080546-706919';at=dt.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,t):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(t,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return load(E/(k+'.json'))
def rel(p):return str(p.relative_to(R)).replace('\\','/')
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
prev=runner.previous_session({k:ev(k) for k in ['KOSPI','KOSPI-history','KOSPI-basic']},PREV)
sources=[('Nvidia 실적 원문','https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-third-quarter-fiscal-2027'),('미국 시세','https://finance.yahoo.com/quote/NVDA/'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('NAND 현물','https://www.trendforce.com/price/flash/flash_spot'),('국내 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('환율','https://m.stock.naver.com/marketindex/exchange/FX_USDKRW'),('FRED 10년-2년','https://fred.stlouisfed.org/series/T10Y2Y'),('FRED 10년-3개월','https://fred.stlouisfed.org/series/T10Y3M'),('연준 일정','https://www.federalreserve.gov/newsevents/calendar.htm')]
notes='''# 2026-11-18 취재 노트
실제 시작 run-status.startedAt. 08:05:46 수집21종 성공, fetch DNS실패 후 승인재시도/rebase91a3702 보존. 원문 취재 완료 '''+at+'''
후보8건: 한국노출/가격/신규/신뢰/속도 (3/3/2/3/2)
1 Nvidia실적·전망 13: 공식뉴스룸 원문 직접HTTPS 저장. 매출115.844B, 데이터센터107.6B, 전망130B±3%,추가1주·중국compute0가정. GAAP74.8→전망71~72. 현금흐름48.253B,FCF43.777B. 단위환산점검.
2 실적후시간외반등 12: Yahoo4종 분봉저장,정규장과별도 표. 미국정규SOXX+.17/SMH-.39/QQQ-.725/TQQQ-2.301/NVDA-.436/AMD-.173/MU-.918/AVGO+2.46. 발표후상승은한국종가후신규.
3 BIS규제·지배구조 10: 전일한국반영,추가동일충격중복계산금지. 수요이전/중국규제는실적회복의반론.
4 금리·FOMC 10: FRED CSV승인재시도성공·장기/90일전체이력.11/17금리차 .30/.77,절대금리11/16 5.12/4.83/4.34.11/19 04시의사록.
5 메모리제품차별화 10: 공식웹DRAM11/17 18:10GMT+8 DDR5 60.333보합/DDR4 79.125-.32. NAND11/9 512GbTLC14.267 -11.67%,eSSD계약과구분. 직접수집TLS실패,웹도구공식표대체.
6 환율·유가 9: 하나11/18 07:36:12 1335.50(-1). WTI85.61/Brent93.07 06:59전자거래. 정산/당일수익률혼용금지.
7 빅테크CAPEX·자금회수 8: 새CAPEX확정수치없이 Nvidia매출채권81.033B/재고39.724B와현금흐름으로집행질평가.
8 공급계약·청산·증자·규제·지정학 5: 광역검색,핵심신규확정원문미확보·본문비사건나열제외.
전일 KOSPI4968.48(-2.59),OHLC5008.09/5084.06/4957/4968.48,KODEX53315/55005/52000/52175(-5.20). 전일기본4950~5150범위충족이나최종수급미확보:성공단정금지.누적9/21해시오류별도.
중심논지:실적과현금흐름은반등근거,마진둔화·중국규제는추격제약.한국5000회복과국내수급결합.
신규썸네일:아이보리실적발표연단·열린장부·상승종이리본,밝은산호/금색. built-in imagegen 신규생성,최근서버/관문과구분.
'''
write(R/f'research/notes/{D}.md',notes+'\n'+'\n'.join(s+' '+u for s,u in sources))
dump(P/'nvidia-results.source.json',{'url':sources[0][1],'fetchedAt':at,'rawHash':hashlib.sha256((P/'nvidia-results.raw').read_bytes()).hexdigest()})
title='Nvidia 실적이 반등 불씨 살렸다…코스피 5,000 회복과 매수 지속이 관건'
summary='Nvidia 매출과 다음 분기 전망이 늘며 시간외 반도체주가 반등했습니다. 낮아지는 매출총이익률과 중국 규제 부담 속에서 코스피 5,000 회복과 외국인·프로그램 매수 지속을 살핍니다.'
paragraphs=[
('', 'Nvidia가 실적과 다음 분기 매출 전망을 내놓자 미국 시간외 반도체주가 반등했습니다. 전날 5,000 아래로 내려간 코스피에도 반등의 근거가 생겼습니다. 다만 개장 직후 상승이 이어지려면 삼성전자·SK하이닉스의 저점 유지와 국내 매수 회복이 따라야 합니다.'),
('실적은 수요를 보여 줬고, 이익률은 숙제를 남겼다','Nvidia의 2027회계연도 3분기 매출은 1,158억 달러로 전년보다 103% 늘었습니다. 데이터센터 매출은 1,076억 달러로 110% 증가했습니다. 다음 분기 매출 전망은 1,300억 달러±3%이며 한 주가 추가로 포함됩니다. 중국 데이터센터 연산 매출은 전망에 넣지 않았습니다. <a href="'+sources[0][1]+'">회사 실적</a>'),
('', '대규모 AI 투자가 실제 공급사 매출로 이어지고 있다는 점은 국내 HBM 수요에도 긍정적인 근거입니다. 반면 GAAP 매출총이익률은 이번 분기 74.8%에서 다음 분기 전망 71~72%로 낮아집니다. 매출 증가만으로 공급사의 수익성 개선까지 같은 속도로 이어진다고 보기는 어렵습니다.'),
('현금은 늘었지만 매출채권과 재고도 커졌다','분기 영업현금흐름은 약 483억 달러, 잉여현금흐름은 약 438억 달러입니다. 매출채권은 약 810억 달러, 재고는 약 397억 달러로 회계연도 초보다 늘었습니다. 현금 창출은 투자 지속의 버팀목이지만 고객의 결제와 재고 소화도 함께 봐야 합니다. 이 수치가 다른 빅테크의 CAPEX 집행을 보장하지는 않습니다. <a href="'+sources[0][1]+'">재무제표</a>'),
('정규장과 실적 발표 뒤의 방향이 달랐다','17일 미국 정규장에서 QQQ는 0.73%, TQQQ는 2.30% 하락했습니다. SOXX는 0.17% 올랐고 SMH는 0.39% 내렸습니다. Nvidia -0.44%, AMD -0.17%, Micron -0.92%와 달리 Broadcom은 2.46% 상승했습니다. 실적 발표 전에는 업종 전체가 한 방향으로 회복한 장세가 아니었습니다. 발표 후 시간외 반응은 아래 표의 별도 시각을 기준으로 봅니다. <a href="'+sources[1][1]+'">미국 시세</a>'),
('', '해외 데이터센터 원격접근 규제와 경영진 교체는 이미 전날 국내장에 알려진 재료입니다. 오늘 새로 더해진 실적과 시간외 반응을 구분해야 같은 악재를 두 번 계산하지 않습니다. 실적이 견조해도 지역별 주문 집행과 규제 부담은 남습니다.'),
('메모리 현물도 제품별 방향이 갈린다','TrendForce의 17일 18:10 대만시간 표에서 DDR5 16Gb는 평균 60.333달러로 보합, DDR4 16Gb는 79.125달러로 0.32% 하락했습니다. NAND 512Gb TLC 웨이퍼 현물은 9일 기준 14.267달러로 11.67% 내렸습니다. 관측일과 제품이 다른 만큼 이를 HBM이나 기업용 SSD 계약가격의 당일 변화로 읽어서는 안 됩니다. <a href="'+sources[2][1]+'">DRAM</a> · <a href="'+sources[3][1]+'">NAND</a>'),
('', 'AI 서버 매출 확대는 고성능 메모리 주문에 유리한 배경입니다. 범용 제품의 가격 약세와 높은 주가 변동성은 별개입니다. 삼성전자·SK하이닉스의 출하와 수익성, 국내 외국인 매수를 함께 확인해야 업황 기대가 주가 회복으로 이어지는지 판단할 수 있습니다.'),
('전날 5,000을 내준 코스피, 회복 뒤 지지가 중요하다','17일 코스피는 5,008.09에 출발해 5,084.06까지 올랐지만 4,968.48로 2.59% 하락 마감했습니다. 저가는 4,957.00입니다. KODEX 레버리지는 53,315원에 출발해 52,000~55,005원을 오간 뒤 52,175원으로 5.20% 내렸습니다. <a href="'+sources[4][1]+'">국내 일봉</a>'),
('', '직전 기본 종가 범위 4,950~5,150에는 들어왔지만 반등 뒤 매도가 커진 흐름은 이어졌습니다. 오늘도 5,000 회복만으로 추세 전환을 판단하기 어렵습니다. 외국인 현물·KOSPI200 선물과 프로그램 비차익 매수가 동반되는지, 상승이 반도체 밖으로 확산하는지 봅니다.'),
('세 종가 시나리오와 KODEX 기준선','기본 종가 범위는 4,950~5,150(50%)입니다. 이 범위에서 외국인 현물이 순매도하지 않는 경우를 가정합니다. 5,150 초과와 외국인·프로그램 동반 순매수가 겹치면 강세 5,150 초과~5,350(30%), 4,950 미만과 두 수급의 동반 순매도가 겹치면 약세 4,700~4,950 미만(20%)입니다. 경계값은 기본 범위에 배정합니다. 범위 이탈이나 수급 반전은 무효화 기준이며 장중 저가·고가 포락은 별도로 4,600~5,450을 둡니다.'),
('', '대응 점수는 공격 20·관망 55·방어 25입니다. KODEX의 1차 지지는 전일 저가 52,000원, 반등 기준은 전일 종가 52,175원, 저항은 전일 고가 55,005원입니다. 갭 상승 뒤 55,005원을 넘더라도 매수가 유지돼야 반등 지속의 근거가 됩니다. 52,175원 아래로 되밀리면 반등을 재검토하고 52,000원 이탈과 동반 매도에는 하방 위험을 경계합니다.'),
('환율 부담은 줄었지만 금리 수준은 높다','18일 07:36:12 KST 하나은행 달러/원 고시는 1,335.50원으로 전회보다 1원 낮았습니다. 서울 현물환 체결가와는 다릅니다. 06:59경 유가선물 전자거래 가격은 WTI 85.61달러, 브렌트 93.07달러입니다. 원화 강세가 수입 비용을 덜어도 유가와 금리의 절대 수준은 기업의 비용과 성장주 가치평가에 영향을 줍니다. <a href="'+sources[5][1]+'">환율</a> · <a href="https://finance.yahoo.com/quote/CL=F/">유가</a>'),
('', 'FRED의 17일 관측에서 10년-2년 금리차는 0.30%포인트, 10년-3개월은 0.77%포인트입니다. 개별 만기는 16일 기준 10년 5.12%, 2년 4.83%, 3개월 4.34%입니다. 관측일이 다른 수치를 한 시점의 곡선으로 합치지 않아야 합니다. <a href="'+sources[6][1]+'">10년-2년</a> · <a href="'+sources[7][1]+'">10년-3개월</a>'),
('', '오늘은 09:30 외국인·프로그램 방향, 10:30 반도체 저점 유지, 14:00 이후 매수 지속을 확인합니다. 조건 관측 시한은 15:20입니다. FOMC 의사록은 한국시간 19일 04:00 예정으로 다음 거래일 금리와 환율에 영향을 줄 수 있습니다. <a href="'+sources[8][1]+'">연준 일정</a>')]
old=(R/'research/evidence/2026-11-10/prepare_inputs.py').read_text(encoding='utf-8')
exec(old[old.index('def table('):old.index('# 전일 actual')].replace('11월 9일','11월 17일'))
exec(old[old.index('m=runner.evaluation()'):old.index("image=f'assets")].replace("'20261109'","'20261117'"))
image=f'assets/images/articles/market-{D}-earnings-dawn-1200x630.png'
Image.open('C:/Users/madro/.codex/generated_images/01a1ebc1-a9ea-7023-a650-ee042fa399bb/exec-c95abfc9-1f2a-4fbd-aa2b-77c8b0ebaa91.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5150,'high':5350,'probability':.30},'base':{'low':4950,'high':5150,'probability':.50},'bear':{'low':4700,'high':4950,'probability':.20}};posture={'attack':20,'wait':55,'defense':25};triggers={}
for k in scenarios:
 cs=[('floor','kospi_price','gte',4950),('cap','kospi_price','lte',5150),('foreign','foreign_cash','gte',0)] if k=='base' else [('price','kospi_price','gt' if k=='bull' else 'lt',5150 if k=='bull' else 4950),('foreign','foreign_cash','gt' if k=='bull' else 'lt',0),('program','program_total','gt' if k=='bull' else 'lt',0)]
 triggers[k]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':k+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':k+'-'+i} for i,met,oper,v in cs]}
dash=load(R/'research/evidence/2026-11-17/dashboard-input.json')
dash.update(headline=title,summary=summary,stance=dict(label='실적 반등과 매수 지속 확인',note='5,000 회복과 국내 매수 지속을 봅니다.',**posture),changes=[{'label':'KOSPI 전일','before':'5,100.50','after':'4,968.48','meaning':'2.59% 하락·5,000 하회'}],factors=[{'label':'Nvidia 실적','metric':'매출 1,158억 달러','detail':'전년 +103%·다음 분기 1,300억 달러 전망','tone':'positive'},{'label':'수익성 전망','metric':'매출총이익률 71~72%','detail':'이번 분기 GAAP 74.8%에서 하락 전망','tone':'negative'}],memory=[{'label':'DDR5 16Gb','value':'$60.333','change':'11/17 보합'},{'label':'DDR4 16Gb','value':'$79.125','change':'11/17 -0.32%'}],events=[{'time':'11월 18일 09:30·10:30 KST','name':'실적 이후 국내 수급','path':'반도체 저점·외국인 매수'},{'time':'11월 19일 04:00 KST','name':'FOMC 의사록','path':'정책금리 전망'}],sources=[{'label':s,'href':u} for s,u in sources],scenarios=[])
for x in dash['markets']:x['asOf']=PREV+'T15:30:00+09:00'
for k,label,ran,cond,invalid in [('bull','강세 · 30%','5,150 초과~5,350',['5,150 초과','외국인 순매수','프로그램 순매수'],'5,150 재이탈 또는 수급 반전'),('base','기본 · 50%','4,950~5,150',['4,950 이상','5,150 이하','외국인 현물 0 이상'],'범위 이탈 또는 외국인 순매도'),('bear','약세 · 20%','4,700~4,950 미만',['4,950 미만','외국인 순매도','프로그램 순매도'],'4,950 회복 또는 수급 반전')]:dash['scenarios'].append({'id':k,'label':label,'range':'KOSPI '+ran,'summary':'09:30·10:30·14:00 확인, 15:20 마감','conditions':cond,'invalidation':invalid})
dash['strategyLevels']=[{'asset':'KOSPI','support':'4,950','pivot':'5,000','resistance':'5,150'},{'asset':'KODEX 레버리지','support':'52,000원','pivot':'52,175원','resistance':'55,005원'}]
for ins,vals in zip(dash['technical']['instruments'],[[4950,5000,5150],[52000,52175,55005]]):ins.update(asOf=PREV+'T15:30:00+09:00',levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],vals)],interpretation='반등 뒤 국내 매수 지속과 전일 저가 지지를 봅니다.')
dump(P/'dashboard-input.json',dash)
state=f'# KOSPI·KODEX 리서치 상태\n- 최신 {D}. 전일KOSPI4968.48(-2.59%),KODEX52175(-5.20%).\n- Nvidia실적·시간외반등,전망마진하락. DDR5보합/DDR4약세/NAND11월9일하락. 전일최종수급미확보.\n- 기본4950~5150(50),강세5150초과~5350(30),약세4700~4950미만(20),대응20/55/25.\n- 전일기본종가범위충족·수급조건미검증. 평가 {rel(op)}.\n- 11/19 04:00의사록. 노트 research/notes/{D}.md.'
files=[image,rel(ap),rel(op),f'research/notes/{D}.md','docs/현재작업중.md']+charts+[rel(p) for p in P.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.html','.md','.raw'] and p.name not in ['run-status.json','pipeline-state.json']]
package=dict(date=D,previousSessionDate=PREV,title=title,summary=summary,image=image,imageAlt='밝은 실적 발표 연단과 열린 장부 위로 솟는 산호색·금색 종이 리본',bodyPath=rel(P/'article-body.html'),reportTemplate=rel(P/'report-template.md'),dashboardPath=rel(P/'dashboard-input.json'),notesPath=f'research/notes/{D}.md',scenarios=scenarios,posture=posture,pathEnvelope={'low':4600,'high':5450,'coverage':.9},marketRegime='risk_off',scenarioTriggers=triggers,drivers=[{'id':'earnings','rank':1,'claim':'Nvidia실적과시간외반등','validationMetric':'반도체·KOSPI·외국인'},{'id':'margin','rank':2,'claim':'수익성전망과규제부담','validationMetric':'금리·환율·프로그램'}],stateText=state,charts=charts,files=list(dict.fromkeys(files+[rel(P/'package.json')])));dump(P/'package.json',package)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+f'\n## {D} KOSPI 장전 발행\n\n- 보고서·기사·홈·목록·대시보드·STATE·사이트맵, 당일 원천·입력·package, 전일 actual/outcome, 신규 earnings-dawn 썸네일과 전체이력 금리차 차트.\n- Nvidia실적·현금흐름·마진전망, 기본4950~5150·대응20/55/25. 공통발행기 검사·선별commit/push·최종배포·양도메인 대조.\n')
status=load(P/'run-status.json');status['stages'].update(research=at,writing=at,image=at);status['artifacts']={'package':rel(P/'package.json'),'report':f'reports/{D}.md','article':f'articles/market-{D}.html'};dump(P/'run-status.json',status)
print('ready',at)
