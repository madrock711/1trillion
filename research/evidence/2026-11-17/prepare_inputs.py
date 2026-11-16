import json,datetime as dt,sys,re,html
from pathlib import Path
from PIL import Image
R=Path.cwd();P=Path(__file__).parent;D='2026-11-17';PREV='2026-11-16';E=P/'collections/080541-710020';at=dt.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,t):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(t,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return load(E/(k+'.json'))
def rel(p):return str(p.relative_to(R)).replace('\\','/')
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
prev=runner.previous_session({k:ev(k) for k in ['KOSPI','KOSPI-history','KOSPI-basic']},PREV)
sources=[('미국 시세','https://finance.yahoo.com/quote/SMH/'),('BIS 원격접근 규칙','https://www.bis.gov/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology'),('Warsh 연설','https://www.federalreserve.gov/newsevents/speech/warsh20261116a.htm'),('Nvidia 실적 일정','https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Sets-Conference-Call-for-Third-Quarter-Financial-Results/default.aspx'),('DRAM','https://www.trendforce.com/price/dram/dram_spot'),('NAND','https://www.trendforce.com/price/flash/flash_spot'),('국내 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('환율','https://m.stock.naver.com/marketindex/exchange/FX_USDKRW'),('FRED 10년-2년','https://fred.stlouisfed.org/series/T10Y2Y'),('FRED 10년-3개월','https://fred.stlouisfed.org/series/T10Y3M'),('연준 일정','https://www.federalreserve.gov/newsevents/calendar.htm')]
notes='''# 2026-11-17 취재 노트
실제 시작 run-status.startedAt. 08:05:41 공통수집21종 성공, 첫 DNS실패 후 승인환경재시도. fetch/rebase 성공. 취재 완료 '''+at+'''
후보8건(한국노출/가격/신규/신뢰/속도 최대3/3/2/3/2)
1 BIS원격접근IFR 3/3/2/3/2=13: 11/16 공식발표. 제3국 데이터센터 원격연산을 통한 우회 차단. 한국메모리 주문취소 확정으로 확대금지.
2 미국반도체추가매도 3/3/2/2/2=12: SOXX-5.412 SMH-5.105 MU-7.618 AMD-5.576 AVGO-3.922 NVDA-4.120. 한국월요일 종가이후 변화. 전일한국급락-3.59 자체와 중복계산금지.
3 Nvidia실적 3/2/2/3/2=12: 11/18 06:20발표·07:00콜 공식IR. 매출/중국규제/가이던스/현금흐름·투자보증 관찰. 기존CEO사임은중복제외. 복귀보도는 이사회확정 아님.
4 Warsh AI시나리오 3/1/2/3/2=11: 공식11/16연설. 생산성상승/노동대체/투자실망세경로, 경기침체예측이나금리인하약속아님.
5 DRAM 3/1/2/3/1=10: 공식11/16 18:10GMT+8 DDR5 60.333 +.11%,DDR4 79.375 -.16%. NAND별도기준일. HBM/eSSD장기주문과분리.
6 금리·유가·환율 3/1/2/3/1=10: FRED11/16 .29/.78, 하나11/17 07:26:18 1336.50, WTI85.06/Brent91.84 전자거래. 현재만기등락률메타와 chartPreviousClose가 달라 메타의전회대비 사용.
7 AnthropicIPO·빅테크CAPEX·AI금융보증 2/1/1/2/1=7: 예정/보도, 새확정현금흐름수치미확보. 주문지속성과투자집행이라는쟁점에만반영.
8 청산·증자·공급계약·지정학 탐색 2/1/0/1/1=5: 핵심새확정원문미확보, 공개본문에비사건나열금지.
전일5100.50 기본5100~5300내지만 하단근접, 저가5069.83. 수급최종과발행후분봉경로 미확보. 범위충족을예측성공으로부풀리지않음. 누적9/21해시오류별도. 활성가설없음.
논쟁: 규제강화가전세계수요소멸인가? 아니다. 주문지역/최종고객재배치와현금집행지연이한국HBM전달경로. 중심명제:규제와실적이겹친추가매도,5000방어확인.
썸네일:밝은청록서버와반투명관문/호박색잠금장치, 원격접근제약.
'''
write(R/f'research/notes/{D}.md',notes+'\n'+'\n'.join(s+' '+u for s,u in sources))
title='AI칩 원격접근 규제에 반도체 급락…코스피 5,000 방어가 첫 관문'
summary='미국이 해외 데이터센터를 통한 AI칩 우회 접근을 제한했고 SOXX는 5.41% 하락했습니다. Nvidia 실적을 하루 앞두고 코스피 5,000 지지와 국내 매수 회복을 살핍니다.'
paragraphs=[
('', 'AI 반도체를 둘러싼 규제가 칩 수출에서 해외 데이터센터의 원격접근으로 넓어졌습니다. 미국 반도체주도 다시 큰 폭으로 내렸습니다. 전날 5,100선까지 밀린 코스피는 오늘 5,000 방어와 외국인·프로그램 매수 회복을 먼저 시험하게 됐습니다.'),
('해외 서버를 빌리는 경로에도 규제가 붙었다','미국 상무부 BIS는 16일 첨단 AI칩과 서버의 원격접근에 관한 잠정 최종규칙을 발표했습니다. 제3국 데이터센터의 원격연산을 이용해 기존 제한을 우회하는 경로를 막겠다는 취지입니다. 국내 HBM 업체에는 최종 고객과 데이터센터 위치에 따른 주문 집행 지연이나 재배치가 위험 경로입니다. 이를 전 세계 AI 수요의 소멸이나 이미 체결된 메모리 주문의 일괄 취소로 해석할 근거는 아닙니다. <a href="'+sources[1][1]+'">BIS 발표</a>'),
('Micron과 경쟁사까지 매도가 번졌다','16일 미국 정규장에서 Micron은 7.62%, AMD는 5.58%, Broadcom은 3.92%, Nvidia는 4.12% 하락했습니다. SOXX는 5.41%, SMH는 5.11% 내렸고 QQQ와 TQQQ도 각각 2.67%, 8.06% 하락했습니다. Nvidia 경영진 문제를 넘어 AI 투자와 반도체 업종의 위험을 함께 줄이는 움직임으로 읽힙니다. 이 미국장 하락은 월요일 한국장 마감 뒤 형성된 추가 가격 변화입니다. <a href="'+sources[0][1]+'">미국 시세</a>'),
('내일 아침 실적은 주문과 현금의 시험대다','Nvidia의 실적 발표는 한국시간 18일 06:20경, 콘퍼런스콜은 07:00 예정입니다. 매출과 다음 분기 전망뿐 아니라 중국 관련 규제 대응, 고객의 투자 집행, 현금흐름과 금융지원 부담이 관건입니다. 대규모 CAPEX 계획이 공급사의 실제 매출로 이어지려면 고객의 자금 조달과 데이터센터 가동이 따라야 합니다. 경영진 교체 자체는 지난주 국내장에 알려졌던 재료입니다. <a href="'+sources[3][1]+'">회사 일정</a>'),
('연준은 AI 투자 실망의 경로도 살핀다','워시 연준 의장은 16일 연설에서 AI가 생산성을 높이는 경우와 일자리 대체를 늘리는 경우, 투자 수익이 기대에 못 미쳐 주가와 경기가 둔화하는 경우를 제시했습니다. 이는 연준의 침체 예측이 아니라 대비를 위한 예시 시나리오입니다. 투자 규모가 큰 만큼 이익과 현금 회수가 늦어질 때 가치평가 조정도 커질 수 있다는 점이 반도체 주가에 중요합니다. <a href="'+sources[2][1]+'">연준 연설</a>'),
('', 'FRED의 16일 관측에서 미국 10년-2년 금리차는 0.29%포인트, 10년-3개월은 0.78%포인트입니다. 두 금리차의 방향도 서로 달랐습니다. 금리차 확대만으로 성장주 부담 완화를 단정하기보다 장기금리 수준과 실적 전망을 함께 봐야 합니다. <a href="'+sources[8][1]+'">10년-2년</a> · <a href="'+sources[9][1]+'">10년-3개월</a>'),
('DDR5 가격 상승과 주가 급락은 서로 다른 신호다','TrendForce의 16일 18:10 대만시간 현물표에서 DDR5 16Gb 평균은 60.333달러로 0.11% 올랐고 DDR4 16Gb는 79.375달러로 0.16% 내렸습니다. DDR5 현물의 소폭 상승은 범용 메모리까지 수요가 일제히 무너졌다는 해석과 거리가 있습니다. 반면 HBM·서버 DRAM·기업용 SSD는 제품별 장기 주문, 고객 재고와 출하를 따로 봐야 합니다. <a href="'+sources[4][1]+'">DRAM 현물</a>'),
('', 'NAND 웨이퍼 현물의 512Gb TLC 평균은 11월 2일 기준 16.152달러입니다. 이 수치는 오늘의 서버 SSD 계약가격을 대신하지 않습니다. 메모리 공급 제약이 남아 있어도 고객의 투자 집행이 늦어지면 주가에는 먼저 부담이 생길 수 있습니다. <a href="'+sources[5][1]+'">NAND 현물</a>'),
('월요일 저점과 5,000선이 가까워졌다','16일 코스피는 5,305.40에 출발해 5,327.99까지 올랐지만 5,100.50으로 3.59% 하락 마감했습니다. 저가는 5,069.83입니다. KODEX 레버리지는 60,205원에 출발해 54,440~60,795원을 오간 뒤 55,035원으로 8.16% 내렸습니다. 반등 출발 뒤 매도가 커진 만큼 개장 직후 상승만으로 수급 회복을 판단하기 어렵습니다. <a href="'+sources[6][1]+'">국내 일봉</a>'),
('', '직전 기본 종가 범위 5,100~5,300에는 들어왔지만 종가는 하단에 붙었고 장중에는 하단 아래로 내려갔습니다. 오늘은 5,069.83과 5,000 지지를 살피며 삼성전자·SK하이닉스의 저점 유지, 외국인 현물과 KOSPI200 선물, 프로그램 비차익 매수와 상승 종목 확산이 함께 회복되는지 봅니다.'),
('세 종가 시나리오와 KODEX 기준선','기본 종가 범위는 4,950~5,150(45%)입니다. 이 범위에서 외국인 현물이 순매도하지 않는 경우를 가정합니다. 5,150 초과와 외국인·프로그램 동반 순매수가 겹치면 강세 5,150 초과~5,300(15%), 4,950 미만과 두 수급의 동반 순매도가 겹치면 약세 4,700~4,950 미만(40%)입니다. 경계값은 기본 범위에 배정합니다. 범위 이탈이나 수급 반전은 무효화 기준이며 장중 저가·고가 포락은 별도로 4,600~5,400을 둡니다.'),
('', '대응 점수는 공격 5·관망 40·방어 55입니다. KODEX의 1차 지지는 전일 저가 54,440원, 반등 기준은 전일 종가 55,035원, 저항은 전일 고가 60,795원입니다. 55,035원 회복 뒤 매수가 유지되는지 먼저 보고, 54,440원 이탈과 외국인·프로그램 매도가 겹치면 하방 위험을 경계합니다.'),
('유가와 환율 완화가 매수로 이어지는지 본다','17일 07:26:18 KST 하나은행 달러/원 고시는 1,336.50원으로 전회보다 1.50원 낮았습니다. 서울 현물환 체결가와는 다릅니다. 미국 유가선물의 17일 06:59경 전자거래 가격은 WTI 85.06달러, 브렌트 91.84달러입니다. 원화 강세와 유가 하락은 비용 부담을 덜어주는 방향이지만 AI 규제와 실적 위험을 곧바로 상쇄하지는 못합니다. <a href="'+sources[7][1]+'">환율</a> · <a href="https://finance.yahoo.com/quote/CL=F/">유가</a>'),
('', '오늘 09:30 첫 수급과 10:30 반도체 저점 유지, 14:00 이후 매도 가속 여부를 확인합니다. 내일 아침 Nvidia 실적을 앞둔 포지션 조정과 신규 매수를 구별해야 합니다. FOMC 의사록은 한국시간 19일 04:00 예정입니다. <a href="'+sources[10][1]+'">연준 일정</a>')]
old=(R/'research/evidence/2026-11-10/prepare_inputs.py').read_text(encoding='utf-8')
charts=[f'charts/us_yield_spreads_{k}_{D}.png' for k in ['long_term','90d']]
exec(old[old.index('def table('):old.index('# 전일 actual')].replace('미국 11월 9일 정규장','미국 11월 16일 정규장').replace('11월 9일 미국 시간외','11월 16일 미국 시간외'))
exec(old[old.index('m=runner.evaluation()'):old.index("image=f'assets")].replace("'20261109'","'20261116'"))
image=f'assets/images/articles/market-{D}-compute-gate-1200x630.png'
Image.open(sys.argv[1]).resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5150,'high':5300,'probability':.15},'base':{'low':4950,'high':5150,'probability':.45},'bear':{'low':4700,'high':4950,'probability':.40}};posture={'attack':5,'wait':40,'defense':55};triggers={}
for k in scenarios:
 cs=[('floor','kospi_price','gte',4950),('cap','kospi_price','lte',5150),('foreign','foreign_cash','gte',0)] if k=='base' else [('price','kospi_price','gt' if k=='bull' else 'lt',5150 if k=='bull' else 4950),('foreign','foreign_cash','gt' if k=='bull' else 'lt',0),('program','program_total','gt' if k=='bull' else 'lt',0)]
 triggers[k]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':k+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':k+'-'+i} for i,met,oper,v in cs]}
dash=load(R/'research/evidence/2026-11-16/dashboard-input.json')
dash.update(headline=title,summary=summary,stance=dict(label='규제·실적 앞두고 하방 경계',note='5,000 지지와 국내 매수 회복을 봅니다.',**posture),changes=[{'label':'KOSPI 전일','before':'5,290.53','after':'5,100.50','meaning':'3.59% 하락·장중 5,100 이탈'}],factors=[{'label':'미국 반도체','metric':'SOXX -5.41% · MU -7.62%','detail':'11월 16일 미국 정규장','tone':'negative'},{'label':'AI칩 원격접근 규제','metric':'BIS 잠정 최종규칙','detail':'제3국 우회 접근 제한','tone':'negative'}],memory=[{'label':'DDR5 16Gb','value':'$60.333','change':'11/16 +0.11%'},{'label':'DDR4 16Gb','value':'$79.375','change':'11/16 -0.16%'}],events=[{'time':'11월 18일 06:20·07:00 KST','name':'Nvidia 실적·콜','path':'주문·규제·현금흐름'},{'time':'11월 19일 04:00 KST','name':'FOMC 의사록','path':'정책금리 전망'}],sources=[{'label':s,'href':u} for s,u in sources],scenarios=[])
for x in dash['markets']:x['asOf']=PREV+'T15:30:00+09:00'
for k,label,ran,cond,invalid in [('bull','강세 · 15%','5,150 초과~5,300',['5,150 초과','외국인 순매수','프로그램 순매수'],'5,150 재이탈 또는 수급 반전'),('base','기본 · 45%','4,950~5,150',['4,950 이상','5,150 이하','외국인 현물 0 이상'],'범위 이탈 또는 외국인 순매도'),('bear','약세 · 40%','4,700~4,950 미만',['4,950 미만','외국인 순매도','프로그램 순매도'],'4,950 회복 또는 수급 반전')]:dash['scenarios'].append({'id':k,'label':label,'range':'KOSPI '+ran,'summary':'09:30·10:30·14:00 확인, 15:20 마감','conditions':cond,'invalidation':invalid})
dash['strategyLevels']=[{'asset':'KOSPI','support':'4,950','pivot':'5,000','resistance':'5,150'},{'asset':'KODEX 레버리지','support':'54,440원','pivot':'55,035원','resistance':'60,795원'}]
for ins,vals in zip(dash['technical']['instruments'],[[4950,5000,5150],[54440,55035,60795]]):ins.update(asOf=PREV+'T15:30:00+09:00',levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],vals)],interpretation='전일 저가 지지와 국내 매수 회복을 봅니다.')
dump(P/'dashboard-input.json',dash)
state=f'# KOSPI·KODEX 리서치 상태\n- 최신 {D}. 전일KOSPI5100.50(-3.59%),KODEX55035(-8.16%).\n- BIS원격접근규칙·미국반도체추가매도·Nvidia실적대기. DDR5상승/DDR4약세. 전일최종수급미확보.\n- 기본4950~5150(45),강세5150초과~5300(15),약세4700~4950미만(40),대응5/40/55.\n- 전일기본하단충족·일중하회·수급조건미검증. 평가 {rel(op)}.\n- 11/18 06:20실적·07:00콜,11/19 04:00의사록. 기존CEO사임중복제외. 노트 research/notes/{D}.md.'
files=[image,rel(ap),rel(op),f'research/notes/{D}.md','docs/현재작업중.md']+charts+[rel(p) for p in P.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.html','.md','.raw'] and p.name not in ['run-status.json','pipeline-state.json'] and '/080524-' not in rel(p)]
package=dict(date=D,previousSessionDate=PREV,title=title,summary=summary,image=image,imageAlt='밝은 청록색 서버와 반투명 관문의 호박색 잠금장치, 앞쪽의 은빛 웨이퍼',bodyPath=rel(P/'article-body.html'),reportTemplate=rel(P/'report-template.md'),dashboardPath=rel(P/'dashboard-input.json'),notesPath=f'research/notes/{D}.md',scenarios=scenarios,posture=posture,pathEnvelope={'low':4600,'high':5400,'coverage':.9},marketRegime='risk_off',scenarioTriggers=triggers,drivers=[{'id':'export-rule','rank':1,'claim':'AI칩 원격접근 규제 부담','validationMetric':'반도체·KOSPI·외국인'},{'id':'earnings','rank':2,'claim':'실적 전 투자집행 경계','validationMetric':'금리·환율·프로그램'}],stateText=state,charts=charts,files=list(dict.fromkeys(files+[rel(P/'package.json')])));dump(P/'package.json',package)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+f'\n## {D} KOSPI 장전 발행\n\n- 보고서·기사·홈·목록·대시보드·STATE·사이트맵, 당일 원천·입력·package, 전일 actual/outcome, 신규 compute-gate 썸네일과 금리차 차트.\n- BIS규제와 미국 추가매도, 기본4950~5150·대응5/40/55. 공통발행기 검사·선별commit/push·최종배포·양도메인 대조.\n')
status=load(P/'run-status.json');status['stages'].update(research=at,writing=at,image=at);status['artifacts']={'package':rel(P/'package.json'),'report':f'reports/{D}.md','article':f'articles/market-{D}.html'};dump(P/'run-status.json',status)
print('ready',at)
