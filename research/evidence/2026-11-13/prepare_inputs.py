import json,datetime as dt,sys,re,html
from pathlib import Path
from PIL import Image
R=Path.cwd();P=Path(__file__).parent;D='2026-11-13';PREV='2026-11-12';E=P/'collections/080316-080781';at=dt.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,t):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(t,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return load(E/(k+'.json'))
def rel(p):return str(p.relative_to(R)).replace('\\','/')
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
prev=runner.previous_session({k:ev(k) for k in ['KOSPI','KOSPI-history','KOSPI-basic']},PREV)
title='젠슨 황 사임에 반도체주 혼조…코스피는 5,300 지지를 시험한다'
summary='Nvidia는 하락했지만 AMD와 Broadcom은 올랐습니다. 코스피의 5,300 지지와 국내 외국인·프로그램 수급, 오늘 밤 미국 PPI가 다음 방향을 가릅니다.'
sources=[('Nvidia 경영진 교체','https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-CEO-Transition/default.aspx'),('Applied Materials 실적','https://ir.appliedmaterials.com/node/29886/pdf'),('미국 시세','https://finance.yahoo.com/quote/SMH/'),('BLS PPI','https://www.bls.gov/ppi/'),('DRAM','https://www.trendforce.com/price/dram/dram_spot'),('NAND','https://www.trendforce.com/price/flash/flash_spot'),('국내 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('고시환율','https://m.stock.naver.com/marketindex/exchange/FX_USDKRW'),('FRED 금리차','https://fred.stlouisfed.org/series/T10Y2Y'),('FRED 10년물','https://fred.stlouisfed.org/series/DGS10')]
notes='''# 2026-11-13 취재 노트
실제 시작 run-status startedAt. 08:03:16부터 공통수집 21종 성공, collection-status 확인. 공식 웹 재조회와 검색 결과 원문 대조 08:04~08:10 KST.
후보 레이더 점수(국내노출/가격/신규/신뢰/전달 각0~3)
1. Nvidia CEO 사임 3/3/3/3/3=15. 회사 IR 발표 확인. Jensen Huang 즉시사임, CFO Colette Kress 임시CEO, Harvey Jones 의장. 사임 이유·조사결론 추정금지. 한국장 종료후 신호.
2. 미국 업종 내 분화 3/3/3/2/3=14. NVDA-4.34, AMD+5.86, AVGO+5.544, MU-1.585, SOXX-.264, SMH-1.032. 종가와 장중 뉴스 수치 구분.
3. AMAT 4Q 실적 3/2/3/3/2=13. 매출104.09억달러(+53%), FCF26억달러 공식발표. 한국시간오늘06:01 장마감후. HBM주문액으로 환산금지.
4. PPI 오늘22:30 2/1/2/3/2=10. BLS 공식 11/13 08:30ET. 한국장마감후·주말위험.
5. DRAM 현물 3/1/2/3/1=10. 11/12 18:10 GMT+8 DDR5 60.233 보합, DDR4 79.75 -.15%. NAND11/2 TLC512 16.152 시차.
6. 환율 3/1/2/2/1=9. 하나고시06:56:52 1336.50(-1), 서울현물체결 아님.
7. 유가 2/1/2/2/1=8. 브렌트95.77 WTI88.70 최근거래. 일중상승뉴스와 전자거래메타 비교기준 다름. 인과추정제외.
8. CoreWeave/TSMC 기발표실적·투자 3/1/0/3/1=8. 전일이전 알려짐 새충격중복제외.
9. 청산/증자/규제/지정학 신규 확정공식문서 부족. 비사건 공개본문 생략.
논쟁/반론: Nvidia 개별지배구조 위험 vs AI공급망 전체수요. AMAT 현금창출 견조 vs 높은금리/메모리현물 약세. 중심명제: 업종혼조에서는 국내가격지지와 매수지속이 우선.
전일 기본5300~5500 범위내 종가5342.73. 고가5458.84에서 반락·저가5293.05. 수급최종원천/15:20앵커 불가로 조건판정 보류. 활성가설없음·가중치미적용.
FRED CSV두차례 timeout. 공식웹 재조회: 11/12 T10Y2Y .24/T10Y3M .78, 11/10 DGS10 4.98 DGS2 4.73 DGS3MO4.30. 날짜혼합곡선금지. 공개그림은 공식웹에서 확인된 11/6,9,10,12 네 관측만 사용.
'''
write(R/f'research/notes/{D}.md',notes+'\n확인 '+at+'\n'+'\n'.join(s+' '+u for s,u in sources))
paragraphs=[
('', 'Nvidia의 최고경영자 교체가 미국 반도체주를 흔들었습니다. 하지만 AMD와 Broadcom은 상승했고 업종 전체가 같은 방향으로 움직이지는 않았습니다. 전날 고점에서 밀린 코스피에는 미국 기술주 반등을 그대로 따라가기보다 5,300 부근의 지지와 국내 매수 지속을 확인하는 접근이 맞습니다.'),
('Nvidia의 경영 공백과 경쟁사의 반등','Nvidia 이사회는 12일 젠슨 황이 사장·CEO·이사회 이사직에서 즉시 사임했다고 발표했습니다. CFO Colette Kress가 재무책임자를 겸하면서 임시 CEO를 맡고 Harvey C. Jones가 이사회 의장에 선임됐습니다. 경영진 교체는 고객과 공급망의 의사결정 불확실성을 키울 수 있습니다. <a href="'+sources[0][1]+'">Nvidia 발표</a>'),
('', '12일 미국 정규장에서 Nvidia는 4.34%, Micron은 1.59% 내렸습니다. 반면 AMD는 5.86%, Broadcom은 5.54% 올랐습니다. SOXX는 0.26%, SMH는 1.03%, QQQ는 0.32%, TQQQ는 0.93% 하락했습니다. 경쟁사로 매수가 옮겨간 흐름과 메모리주의 약세가 공존합니다. 삼성전자·SK하이닉스가 받는 영향도 고객별 주문과 제품 구성에 따라 달라질 수 있습니다. <a href="'+sources[2][1]+'">미국 시세</a>'),
('장비업체의 현금창출은 수요를 뒷받침한다','미국장 마감 후 Applied Materials는 회계연도 4분기 매출 104억900만달러로 전년 대비 53% 성장했다고 발표했습니다. 분기 잉여현금흐름은 26억달러였습니다. 장비업체의 매출과 현금창출은 반도체 설비투자의 실체를 뒷받침합니다. 다만 이 실적을 국내 메모리업체의 HBM 신규 주문액이나 수율 개선으로 바로 환산할 수는 없습니다. <a href="'+sources[1][1]+'">회사 실적</a>'),
('범용 메모리 가격은 여전히 차별화된다','TrendForce의 12일 18:10 대만시간 DRAM 현물표에서 DDR5 16Gb 평균은 60.233달러로 보합, DDR4 16Gb는 79.75달러로 0.15% 하락했습니다. 미국 반도체 경쟁사의 주가 상승이 범용 메모리 전 품목의 강세를 뜻하지는 않습니다. HBM·서버 DRAM의 장기 주문과 DDR4 재고 흐름을 나눠 봐야 합니다. <a href="'+sources[4][1]+'">DRAM</a>'),
('', 'NAND 웨이퍼 현물표는 11월 2일 기준 512Gb TLC 평균 16.152달러입니다. 품목과 기준일이 다른 이 수치는 오늘의 eSSD 계약가격을 대신하지 않습니다. SLC·MLC의 가격과 고용량 서버 SSD 수요도 구별해야 합니다. <a href="'+sources[5][1]+'">NAND</a>'),
('5,300 지지와 전일 고가 회복이 관건','전날 코스피는 5,385.94에 출발해 5,458.84까지 올랐지만 5,342.73으로 0.61% 하락 마감했습니다. 저가는 5,293.05였습니다. KODEX 레버리지는 62,105원에 출발해 60,230~64,295원을 오간 뒤 61,550원으로 0.72% 내렸습니다. 고점 대비 되밀린 흐름은 미국 반도체 강세만으로 국내 상승이 지속되지는 않는다는 점을 보여줍니다. <a href="'+sources[6][1]+'">국내 일봉</a>'),
('', '직전 기본 종가 범위 5,300~5,500에는 들어왔지만 장중에는 하단을 밑돌았습니다. 오늘은 5,300을 지키면서 전일 종가를 회복하는지가 첫 관문입니다. 삼성전자·SK하이닉스의 저점, 외국인 현물과 KOSPI200 선물 방향, 프로그램 비차익 매수와 반도체 밖의 상승 확산을 함께 봐야 합니다.'),
('원화는 소폭 강세, 금리는 부담','13일 06:56:52 KST 하나은행 달러/원 고시환율은 1,336.50원으로 전회보다 1원 낮았습니다. 서울 현물환 개장 체결가와는 다릅니다. 소폭의 원화 강세는 완충 요인이지만 국내 주식 순매수 지속까지 보장하지 않습니다. <a href="'+sources[7][1]+'">환율</a>'),
('', 'FRED의 12일 관측에서 10년-2년 금리차는 0.24%포인트, 10년-3개월은 0.78%포인트입니다. 개별 만기의 최신 관측은 10일로 10년 4.98%, 2년 4.73%, 3개월 4.30%입니다. 관측일이 달라 하나의 당일 곡선으로 합칠 수 없습니다. 높은 장기금리는 AI 성장주의 가치평가에 부담으로 남습니다. <a href="'+sources[8][1]+'">금리차</a> · <a href="'+sources[9][1]+'">10년물</a>'),
('세 종가 시나리오와 KODEX 기준선','기본 종가 범위는 5,200~5,400(50%)입니다. 이 범위에서 외국인 현물이 순매도하지 않는 경우를 가정합니다. 5,400 초과와 외국인·프로그램 동반 순매수가 겹치면 강세 5,400 초과~5,550(20%), 5,200 미만과 두 수급의 동반 순매도가 겹치면 약세 4,950~5,200 미만(30%)입니다. 경계값은 기본 범위에 배정합니다. 범위 이탈이나 수급 반전은 해당 시나리오의 무효화 기준입니다. 별도의 장중 저가·고가 포락은 4,850~5,650입니다.'),
('', '대응 점수는 공격 15·관망 50·방어 35입니다. KODEX의 1차 지지는 전일 저가 60,230원, 반등 기준은 전일 종가 61,550원, 저항은 전일 고가 64,295원입니다. 61,550원 위에서 매수가 유지되는지 먼저 보고, 60,230원 이탈과 외국인·프로그램 매도가 겹치면 하방 위험을 경계합니다. 상승 출발만으로 추격할 근거는 부족합니다.'),
('오늘 밤 PPI와 다음 주 Nvidia 실적','미국 10월 PPI는 오늘 08:30 ET, 한국시간 22:30에 발표됩니다. 국내장 마감 뒤 물가와 금리가 다시 움직일 수 있어 주말 보유 위험에 영향을 줍니다. Nvidia의 실적 콘퍼런스콜은 17일 14:00 PT, 한국시간 18일 07:00 예정입니다. 오늘은 09:30 첫 수급, 10:30 반도체 저점 유지, 14:00 이후 매수 지속을 확인하며 시나리오 관측 시한은 15:20입니다. <a href="'+sources[3][1]+'">BLS</a> · <a href="https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Sets-Conference-Call-for-Third-Quarter-Financial-Results/default.aspx">Nvidia 일정</a>')]
# 검증된 표 렌더 및 actual 계약 구조만 재사용, 시세는 이번 수집에서 읽는다.
old=(R/'research/evidence/2026-11-10/prepare_inputs.py').read_text(encoding='utf-8')
charts=[f'charts/us_yield_spreads_{k}_{D}.png' for k in ['long_term','90d']]
exec(old[old.index('def table('):old.index('# 전일 actual')].replace('미국 11월 9일 정규장','미국 11월 12일 정규장').replace('11월 9일 미국 시간외','11월 12일 미국 시간외'))
exec(old[old.index('m=runner.evaluation()'):old.index("image=f'assets")].replace("'20261109'","'20261112'"))
image=f'assets/images/articles/market-{D}-wafer-test-1200x630.png'
Image.open('C:/Users/madro/.codex/generated_images/01a1d1ff-838b-7a42-8888-9af34d0faf14/exec-9aa4e2b9-4b81-480e-b820-fa4fe67b4457.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5400,'high':5550,'probability':.2},'base':{'low':5200,'high':5400,'probability':.5},'bear':{'low':4950,'high':5200,'probability':.3}};posture={'attack':15,'wait':50,'defense':35};triggers={}
for k in scenarios:
 cs=[('floor','kospi_price','gte',5200),('cap','kospi_price','lte',5400),('foreign','foreign_cash','gte',0)] if k=='base' else [('price','kospi_price','gt' if k=='bull' else 'lt',5400 if k=='bull' else 5200),('foreign','foreign_cash','gt' if k=='bull' else 'lt',0),('program','program_total','gt' if k=='bull' else 'lt',0)]
 triggers[k]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':k+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':k+'-'+i} for i,met,oper,v in cs]}
dash=load(R/'research/evidence/2026-11-12/dashboard-input.json')
dash.update(headline=title,summary=summary,stance=dict(label='국내 지지와 수급 확인',note='5,300 지지와 반도체 저점 유지를 봅니다.',**posture),changes=[{'label':'KOSPI 전일','before':'5,375.36','after':'5,342.73','meaning':'0.61% 하락·장중 고점에서 반락'}],factors=[{'label':'미국 반도체 혼조','metric':'NVDA -4.34% · AMD +5.86%','detail':'11월 12일 정규장','tone':'negative'},{'label':'경영진 교체','metric':'Nvidia 임시 CEO 선임','detail':'경영 불확실성과 경쟁사 매수 공존','tone':'neutral'}],memory=[{'label':'DDR5 16Gb','value':'$60.233','change':'11/12 보합'},{'label':'DDR4 16Gb','value':'$79.75','change':'11/12 -0.15%'}],events=[{'time':'11월 13일 22:30 KST','name':'미국 10월 PPI','path':'물가·금리·주말 위험'},{'time':'11월 18일 07:00 KST','name':'Nvidia 실적 콜','path':'경영 공백·가이던스'}],sources=[{'label':s,'href':u} for s,u in sources],scenarios=[])
for x in dash['markets']:x['asOf']=PREV+'T15:30:00+09:00'
for k,label,ran,cond,invalid in [('bull','강세 · 20%','5,400 초과~5,550',['5,400 초과','외국인 순매수','프로그램 순매수'],'5,400 재이탈 또는 수급 반전'),('base','기본 · 50%','5,200~5,400',['5,200 이상','5,400 이하','외국인 현물 0 이상'],'범위 이탈 또는 외국인 순매도'),('bear','약세 · 30%','4,950~5,200 미만',['5,200 미만','외국인 순매도','프로그램 순매도'],'5,200 회복 또는 수급 반전')]:dash['scenarios'].append({'id':k,'label':label,'range':'KOSPI '+ran,'summary':'09:30·10:30·14:00 확인, 15:20 마감','conditions':cond,'invalidation':invalid})
dash['strategyLevels']=[{'asset':'KOSPI','support':'5,200','pivot':'5,300','resistance':'5,400'},{'asset':'KODEX 레버리지','support':'60,230원','pivot':'61,550원','resistance':'64,295원'}]
for ins,vals in zip(dash['technical']['instruments'],[[5200,5300,5400],[60230,61550,64295]]):ins.update(asOf=PREV+'T15:30:00+09:00',levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],vals)],interpretation='전일 종가 회복과 국내 매수 지속을 봅니다.')
dump(P/'dashboard-input.json',dash)
state=f'# KOSPI·KODEX 리서치 상태\n- 최신 {D}. 전일KOSPI5342.73(-0.61%),KODEX61550(-0.72%).\n- Nvidia CEO사임과 미국반도체혼조. DDR5보합·DDR4약세. 전일최종수급미확보.\n- 기본5200~5400(50),강세5400초과~5550(20),약세4950~5200미만(30),대응15/50/35.\n- 전일 기본범위충족·수급조건미검증. 평가 {rel(op)}.\n- 오늘22:30PPI·11/18 07:00Nvidia콜. 기존CoreWeave/TSMC중복제외. 노트 research/notes/{D}.md.'
files=[image,rel(ap),rel(op),f'research/notes/{D}.md','docs/현재작업중.md']+charts+[rel(p) for p in P.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.html','.md','.raw'] and p.name not in ['run-status.json','pipeline-state.json']]
package=dict(date=D,previousSessionDate=PREV,title=title,summary=summary,image=image,imageAlt='밝은 민트색 배경의 은빛 웨이퍼와 호박색 측정기, 서로 다른 높이의 반도체 칩',bodyPath=rel(P/'article-body.html'),reportTemplate=rel(P/'report-template.md'),dashboardPath=rel(P/'dashboard-input.json'),notesPath=f'research/notes/{D}.md',scenarios=scenarios,posture=posture,pathEnvelope={'low':4850,'high':5650,'coverage':.9},marketRegime='risk_off',scenarioTriggers=triggers,drivers=[{'id':'semiconductor','rank':1,'claim':'Nvidia 경영진교체와 업종내분화','validationMetric':'국내반도체·KOSPI·외국인'},{'id':'domestic-flow','rank':2,'claim':'국내매수지속이반등관건','validationMetric':'외국인·프로그램'}],stateText=state,charts=charts,files=list(dict.fromkeys(files+[rel(P/'package.json')])));dump(P/'package.json',package)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+f'\n## {D} KOSPI 장전 발행\n\n- reports/{D}.md, articles/market-{D}.html, STATE.md, 홈·목록·대시보드·사이트맵 동기화.\n- research/evidence/{D}/ 원천·입력·package·스크립트, research/notes/{D}.md, 전일 actual/outcome, 신규 wafer-test 썸네일, 당일 FRED 관측 차트.\n- Nvidia CEO 교체·AMAT실적·PPI, 기본5200~5400·대응15/50/35. 공통발행기 검사·선별commit/push·최종배포·양도메인 대조.\n')
status=load(P/'run-status.json');status['stages'].update(research=at,writing=at,image=at);status['artifacts']={'package':rel(P/'package.json'),'report':f'reports/{D}.md','article':f'articles/market-{D}.html'};dump(P/'run-status.json',status)
print('ready',at)
