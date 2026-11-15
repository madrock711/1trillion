import json,datetime as dt,sys,re,html
from pathlib import Path
from PIL import Image
R=Path.cwd();P=Path(__file__).parent;D='2026-11-16';PREV='2026-11-13';E=P/'collections/080016-543042';at=dt.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,t):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(t,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return load(E/(k+'.json'))
def rel(p):return str(p.relative_to(R)).replace('\\','/')
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
prev=runner.previous_session({k:ev(k) for k in ['KOSPI','KOSPI-history','KOSPI-basic']},PREV)
sources=[('미국 시세','https://finance.yahoo.com/quote/SMH/'),('미국 PPI','https://www.bls.gov/news.release/ppi.nr0.htm'),('Nvidia 경영진 교체','https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-CEO-Transition/default.aspx'),('Nvidia 실적 일정','https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Sets-Conference-Call-for-Third-Quarter-Financial-Results/default.aspx'),('Bessent 발언 Reuters','https://wqxc.com/2026/11/15/bessent-says-nvidia-must-go-outside-the-company-to-find-new-ceo/'),('DRAM','https://www.trendforce.com/price/dram/dram_spot'),('NAND','https://www.trendforce.com/price/flash/flash_spot'),('국내 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('환율','https://m.stock.naver.com/marketindex/exchange/FX_USDKRW'),('FRED 금리차','https://fred.stlouisfed.org/series/T10Y2Y'),('FRED 단기금리차','https://fred.stlouisfed.org/series/T10Y3M'),('FRED 10년','https://fred.stlouisfed.org/series/DGS10'),('연준 일정','https://www.federalreserve.gov/newsevents.htm')]
notes='''# 2026-11-16 취재 노트
실제 시작 run-status.startedAt. 08:00:16 공통수집21종 성공. Git fetch DNS 실패후 승인재시도 성공·rebase origin/main 성공. 웹 공식자료 대조 후 집필.
후보 8건(국내노출/가격/신규/신뢰/속도, 최대3/3/2/3/2)
1 미국 반도체 전반 하락 3/3/2/2/2=12: SOXX-3.671 SMH-2.986 AMD-8.754 AVGO-4.762 MU-2.521 NVDA-2.01. 한국 금요일 마감후 신규 가격변화.
2 PPI 3/2/2/3/2=12: BLS 11/13 08:30ET 최종수요 MoM+.3 YoY+6.5. 식품에너지유통제외+.5/+4.9. 공개글 수치와 해석 구분.
3 Nvidia 주말 외부CEO 요구 3/2/2/2/2=11. Fox 인터뷰 Reuters·Bloomberg·Fox 교차. 검색전문 추출 제한, 짧은 확인사실만. 신규법규/수출금지 확정으로 확대금지. 11/12 CEO 사임 자체는 국내13일 반영.
4 Nvidia 실적 3/1/2/3/2=11: 공식IR 11/17 13:20PT 발표/14:00콜=11/18 06:20/07:00KST. 고객주문/중국매출/현금흐름 관찰.
5 DRAM 3/1/2/3/1=10: 11/13 18:10GMT+8 DDR5 60.267 +.06%, DDR4 79.50 -.31%. NAND11/2 TLC51216.152. 수요붕괴로 일반화금지.
6 금리·환율 3/1/2/3/1=10: FRED11/13 spreads .27/.83, 개별만기11/12 5.10/4.86/4.32. 하나11/16 07:30:55 1338.00 고시. 선물은 주말종료후 재개시각 확인필요.
7 AMAT/빅테크 기존 실적·CAPEX 3/1/0/3/1=8. 기존발표중복제외, Nvidia 예정실적의 주문·FCF 검증관건.
8 청산/증자/공급계약/규제·지정학 탐색: 새 확정공식사건미확보, 비사건 공개본문제외.
논쟁: 경영진리스크가 AI전체주문 취소로 이어지는가? 현재 현물 DDR5 소폭상승과 주가하락은 별개. 중심명제: 경쟁사까지 매도 확산, 국내 종가지지와 수급회복 선행.
직전 기본5200~5400내 종가5290.53, 일중고가5504.44·저가5259.09. 수급조건미확보·추정안함. 활성가설없음. 누적9/21해시불일치와 당일 계약분리.
썸네일 논제: 경영공백/실적대기, 하방경계, 밝은 빈의자·진자/살구·하늘색. 최근 웨이퍼·칩/다리와 소재차별.
'''
write(R/f'research/notes/{D}.md',notes+'\n취재 완료 '+at+'\n'+'\n'.join(s+' '+u for s,u in sources))
title='미국 반도체 매도 확산…코스피는 5,200 지지와 수급 회복이 관건'
summary='AMD와 Broadcom까지 하락했고 미국 PPI는 전년 대비 6.5% 올랐습니다. Nvidia 실적을 앞두고 코스피 5,200 지지와 외국인·프로그램 매수 회복을 봅니다.'
paragraphs=[
('', '미국 반도체주의 매도가 Nvidia 경쟁사로도 번졌습니다. 금요일 반등을 지키지 못한 코스피에는 부담스러운 출발입니다. 이번 주 Nvidia 실적을 기다리는 동안 5,200 지지와 외국인·프로그램 매수 회복을 먼저 봐야 합니다.'),
('경쟁사로 옮겨갔던 매수도 흔들렸다','13일 미국 정규장에서 AMD는 8.75%, Broadcom은 4.76%, Micron은 2.52%, Nvidia는 2.01% 하락했습니다. SOXX는 3.67%, SMH는 2.99% 내렸고 QQQ와 TQQQ는 각각 1.20%, 3.67% 하락했습니다. 목요일의 종목별 차별화가 금요일에는 업종 전반의 매도로 바뀌었습니다. 한국장 마감 뒤의 추가 하락은 오늘 삼성전자·SK하이닉스의 반등 여력을 제약합니다. <a href="'+sources[0][1]+'">미국 시세</a>'),
('Nvidia 실적에 경영진과 수출 문제가 겹쳤다','Nvidia는 12일 젠슨 황의 사임과 Colette Kress의 임시 CEO 선임을 발표했습니다. 이 소식은 금요일 국내장에도 알려져 있었습니다. 주말에는 스콧 베선트 미국 재무장관이 방송 인터뷰에서 외부 인사를 차기 CEO로 선임해야 한다고 요구했다고 Reuters가 보도했습니다. 이는 경영진에 대한 정치적 압박이며 새로운 수출금지 조치가 확정됐다는 뜻은 아닙니다. <a href="'+sources[2][1]+'">회사 발표</a> · <a href="'+sources[4][1]+'">Reuters</a>'),
('', '실적 발표는 한국시간 18일 06:20경, 콘퍼런스콜은 07:00 예정입니다. 매출 전망뿐 아니라 고객 주문의 지속성, 중국 관련 매출과 수출규제 대응, 현금흐름을 함께 봐야 합니다. 경영진 교체가 국내 HBM 주문 취소로 이어진다고 단정할 단계는 아닙니다. 빅테크의 투자 계획이 실제 지출과 공급사의 현금창출로 이어지는지가 반도체 가치평가를 가릅니다. <a href="'+sources[3][1]+'">Nvidia 일정</a>'),
('물가 둔화의 속도는 아직 느리다','BLS가 13일 발표한 미국 10월 최종수요 PPI는 전월 대비 0.3%, 전년 대비 6.5% 상승했습니다. 식품·에너지·유통서비스를 제외한 지수도 전월 대비 0.5% 올랐습니다. 월간 상승 폭이 작아져도 높은 연간 물가는 금리 부담을 쉽게 덜어주지 못합니다. <a href="'+sources[1][1]+'">BLS</a>'),
('', 'FRED의 13일 관측에서 10년-2년 금리차는 0.27%포인트, 10년-3개월은 0.83%포인트입니다. 개별 만기의 최신 관측일은 12일이며 10년 5.10%, 2년 4.86%, 3개월 4.32%입니다. 높은 장기금리는 먼 미래 이익의 현재가치를 낮춰 성장주에 부담을 줍니다. <a href="'+sources[9][1]+'">10년-2년</a> · <a href="'+sources[10][1]+'">10년-3개월</a> · <a href="'+sources[11][1]+'">10년물</a>'),
('메모리 가격과 주식 매도는 나눠 봐야 한다','TrendForce의 13일 18:10 대만시간 현물표에서 DDR5 16Gb 평균은 60.267달러로 0.06% 올랐고 DDR4 16Gb는 79.50달러로 0.31% 내렸습니다. 주가가 동반 하락해도 메모리 전 품목의 수요가 같은 속도로 꺾인 것은 아닙니다. HBM·서버 DRAM 주문과 범용 DDR4 재고 흐름을 구분해야 합니다. <a href="'+sources[5][1]+'">DRAM</a>'),
('', 'NAND 웨이퍼 현물의 512Gb TLC 평균은 11월 2일 기준 16.152달러입니다. 기준일과 제품이 달라 오늘 서버 SSD 계약가격을 대신하지 않습니다. HBM 공급 제약과 고용량 SSD 수요가 유지되는지, 고객사의 투자 집행이 늦어지는지를 각각 봐야 합니다. <a href="'+sources[6][1]+'">NAND</a>'),
('금요일의 상승분 반납이 남긴 기준선','13일 코스피는 5,452.41에 출발해 5,504.44까지 올랐지만 5,290.53으로 0.98% 하락 마감했습니다. 저가는 5,259.09였습니다. KODEX 레버리지는 63,805원에 출발해 59,260~65,285원을 오간 뒤 59,925원으로 2.64% 내렸습니다. 상승 출발 자체보다 장 후반까지 매수가 유지되는지가 중요해진 흐름입니다. <a href="'+sources[7][1]+'">국내 일봉</a>'),
('', '직전 기본 종가 범위 5,200~5,400에는 들어왔지만 고점에서의 되밀림은 컸습니다. 오늘은 전일 저가 5,259.09와 5,200 지지를 차례로 살피고, 반등 시 전일 종가를 회복하는지 봅니다. 삼성전자·SK하이닉스 저점 유지, 외국인 현물과 KOSPI200 선물의 방향, 프로그램 비차익 매수와 상승 종목 확산이 함께 따라야 합니다.'),
('세 종가 시나리오와 대응','기본 종가 범위는 5,100~5,300(50%)입니다. 범위 안에서 외국인 현물이 순매도하지 않는 경우를 가정합니다. 5,300 초과와 외국인·프로그램 동반 순매수가 겹치면 강세 5,300 초과~5,450(15%), 5,100 미만과 두 수급의 동반 순매도가 겹치면 약세 4,850~5,100 미만(35%)입니다. 경계값은 기본 범위에 배정합니다. 범위 이탈이나 수급 반전은 해당 시나리오의 무효화 기준이며 장중 저가·고가 포락은 별도로 4,750~5,550을 둡니다.'),
('', '대응 점수는 공격 10·관망 45·방어 45입니다. KODEX의 1차 지지는 전일 저가 59,260원, 반등 기준은 전일 종가 59,925원, 저항은 전일 고가 65,285원입니다. 59,925원 회복 뒤 매수가 유지되는지 먼저 보고, 59,260원 이탈과 외국인·프로그램 매도가 겹치면 하방 위험을 경계합니다.'),
('이번 주 첫 관문은 국내 매수의 지속','16일 07:30:55 KST 하나은행 달러/원 고시는 1,338.00원으로 전회보다 1.50원 높았습니다. 고시환율과 서울 현물환 체결가는 구별해야 합니다. 미국 유가선물의 직전 전자거래 가격은 WTI 88.56달러, 브렌트 95.84달러로 급락에 따른 비용 완화는 제한적입니다. <a href="'+sources[8][1]+'">환율</a> · <a href="https://finance.yahoo.com/quote/CL=F/">유가</a>'),
('', '연준 일정에는 미국시간 16일 정오 의장 발언, 18일 14:00 FOMC 의사록이 예정돼 있습니다. 한국시간으로는 각각 17일 02:00, 19일 04:00입니다. 오늘은 09:30 첫 수급, 10:30 반도체 저점 유지, 14:00 이후 매도 가속 여부를 보고 시나리오 조건은 15:20까지 관찰합니다. <a href="'+sources[12][1]+'">연준 일정</a>')]
# 표와 actual/outcome 계약 구조만 재사용. 모든 가격은 오늘 원천에서 읽는다.
old=(R/'research/evidence/2026-11-10/prepare_inputs.py').read_text(encoding='utf-8')
charts=[f'charts/us_yield_spreads_{k}_{D}.png' for k in ['long_term','90d']]
exec(old[old.index('def table('):old.index('# 전일 actual')].replace('미국 11월 9일 정규장','미국 11월 13일 정규장').replace('11월 9일 미국 시간외','11월 13일 미국 시간외'))
exec(old[old.index('m=runner.evaluation()'):old.index("image=f'assets")].replace("'20261109'","'20261113'"))
image=f'assets/images/articles/market-{D}-empty-chair-1200x630.png'
Image.open(sys.argv[1]).resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5300,'high':5450,'probability':.15},'base':{'low':5100,'high':5300,'probability':.5},'bear':{'low':4850,'high':5100,'probability':.35}};posture={'attack':10,'wait':45,'defense':45};triggers={}
for k in scenarios:
 cs=[('floor','kospi_price','gte',5100),('cap','kospi_price','lte',5300),('foreign','foreign_cash','gte',0)] if k=='base' else [('price','kospi_price','gt' if k=='bull' else 'lt',5300 if k=='bull' else 5100),('foreign','foreign_cash','gt' if k=='bull' else 'lt',0),('program','program_total','gt' if k=='bull' else 'lt',0)]
 triggers[k]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':k+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':k+'-'+i} for i,met,oper,v in cs]}
dash=load(R/'research/evidence/2026-11-13/dashboard-input.json')
dash.update(headline=title,summary=summary,stance=dict(label='반도체 매도 확산 경계',note='5,200 지지와 국내 매수 회복을 봅니다.',**posture),changes=[{'label':'KOSPI 전일','before':'5,342.73','after':'5,290.53','meaning':'0.98% 하락·상승분 반납'}],factors=[{'label':'반도체 매도 확산','metric':'SOXX -3.67% · AMD -8.75%','detail':'11월 13일 미국 정규장','tone':'negative'},{'label':'미국 생산자물가','metric':'10월 전년 대비 +6.5%','detail':'금리 부담 지속','tone':'negative'}],memory=[{'label':'DDR5 16Gb','value':'$60.267','change':'11/13 +0.06%'},{'label':'DDR4 16Gb','value':'$79.50','change':'11/13 -0.31%'}],events=[{'time':'11월 17일 02:00 KST','name':'연준 의장 발언','path':'금리·성장주'},{'time':'11월 18일 06:20·07:00 KST','name':'Nvidia 실적·콜','path':'주문·수출규제·현금흐름'},{'time':'11월 19일 04:00 KST','name':'FOMC 의사록','path':'정책금리 전망'}],sources=[{'label':s,'href':u} for s,u in sources],scenarios=[])
for x in dash['markets']:x['asOf']=PREV+'T15:30:00+09:00'
for k,label,ran,cond,invalid in [('bull','강세 · 15%','5,300 초과~5,450',['5,300 초과','외국인 순매수','프로그램 순매수'],'5,300 재이탈 또는 수급 반전'),('base','기본 · 50%','5,100~5,300',['5,100 이상','5,300 이하','외국인 현물 0 이상'],'범위 이탈 또는 외국인 순매도'),('bear','약세 · 35%','4,850~5,100 미만',['5,100 미만','외국인 순매도','프로그램 순매도'],'5,100 회복 또는 수급 반전')]:dash['scenarios'].append({'id':k,'label':label,'range':'KOSPI '+ran,'summary':'09:30·10:30·14:00 확인, 15:20 마감','conditions':cond,'invalidation':invalid})
dash['strategyLevels']=[{'asset':'KOSPI','support':'5,100','pivot':'5,200','resistance':'5,300'},{'asset':'KODEX 레버리지','support':'59,260원','pivot':'59,925원','resistance':'65,285원'}]
for ins,vals in zip(dash['technical']['instruments'],[[5100,5200,5300],[59260,59925,65285]]):ins.update(asOf=PREV+'T15:30:00+09:00',levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],vals)],interpretation='전일 종가 회복과 국내 매수 지속을 봅니다.')
dump(P/'dashboard-input.json',dash)
state=f'# KOSPI·KODEX 리서치 상태\n- 최신 {D}. 전일KOSPI5290.53(-0.98%),KODEX59925(-2.64%).\n- 미국반도체동반하락·PPI6.5%·주말Nvidia외부CEO요구. DDR5소폭상승/DDR4약세. 전일최종수급미확보.\n- 기본5100~5300(50),강세5300초과~5450(15),약세4850~5100미만(35),대응10/45/45.\n- 전일기본범위충족·장중상승반납·수급조건미검증. 평가 {rel(op)}.\n- 11/18 06:20실적·07:00Nvidia콜·11/19 04:00FOMC의사록. 11/12CEO사임/기존CAPEX 중복제외. 노트 research/notes/{D}.md.'
files=[image,rel(ap),rel(op),f'research/notes/{D}.md','docs/현재작업중.md']+charts+[rel(p) for p in P.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.html','.md','.raw'] and p.name not in ['run-status.json','pipeline-state.json'] and '/080003-' not in rel(p)]
package=dict(date=D,previousSessionDate=PREV,title=title,summary=summary,image=image,imageAlt='햇살이 비치는 회의실의 빈 살구색 의자와 호박색 진자',bodyPath=rel(P/'article-body.html'),reportTemplate=rel(P/'report-template.md'),dashboardPath=rel(P/'dashboard-input.json'),notesPath=f'research/notes/{D}.md',scenarios=scenarios,posture=posture,pathEnvelope={'low':4750,'high':5550,'coverage':.9},marketRegime='risk_off',scenarioTriggers=triggers,drivers=[{'id':'semiconductor','rank':1,'claim':'미국 반도체 매도 확산','validationMetric':'반도체·KOSPI·외국인'},{'id':'inflation','rank':2,'claim':'높은 물가와 금리 부담','validationMetric':'금리·환율·프로그램'}],stateText=state,charts=charts,files=list(dict.fromkeys(files+[rel(P/'package.json')])));dump(P/'package.json',package)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+f'\n## {D} KOSPI 장전 발행\n\n- reports/{D}.md, articles/market-{D}.html, STATE.md, 홈·목록·대시보드·사이트맵 갱신.\n- research/evidence/{D}/ 원천·입력·package·스크립트, research/notes/{D}.md, 전일 actual/outcome, 신규 빈의자 썸네일, 당일 금리차 차트.\n- 반도체매도확산·PPI·Nvidia실적, 기본5100~5300·대응10/45/45. 공통발행기 검사·선별commit/push·최종배포·양도메인 대조.\n')
status=load(P/'run-status.json');status['stages'].update(research=at,writing=at,image=at);status['artifacts']={'package':rel(P/'package.json'),'report':f'reports/{D}.md','article':f'articles/market-{D}.html'};dump(P/'run-status.json',status)
print('ready',at)
