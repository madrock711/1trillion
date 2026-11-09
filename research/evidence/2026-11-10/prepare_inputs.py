import json,datetime as dt,sys,html
from pathlib import Path
from PIL import Image
R=Path.cwd(); P=Path(__file__).parent; D='2026-11-10'; PREV='2026-11-09'; E=P/'collections/080205-159814'; at=dt.datetime.now().astimezone().isoformat()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(t,encoding='utf-8',newline='\n')
def dump(p,v): write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return load(E/(k+'.json'))
def rel(p):return str(p.relative_to(R)).replace('\\','/')
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
prev=runner.previous_session({k:ev(k) for k in ['KOSPI','KOSPI-history','KOSPI-basic']},PREV)
title='유가 하락과 미국 반도체 급반등…코스피는 5,250 회복을 시험한다'
summary='미국 반도체주가 폭넓게 올랐고 원화도 강해졌습니다. Nvidia의 개별 위험과 CPI 발표를 앞둔 경계 속에서 국내 외국인·프로그램 매수가 반등 지속을 가릅니다.'
sources=[('Nvidia 이사회 성명','https://investor.nvidia.com/news/press-release-details/2026/Statement-from-NVIDIA-Board-of-Directors/default.aspx'),('Reuters 미국장','https://www.marketscreener.com/news/wall-st-jumps-back-as-oil-slide-eases-inflation-worries-nvidia-slumps-ce785fd3de81f123'),('미국 정규장·시간외','https://finance.yahoo.com/quote/SMH/'),('BLS 일정','https://www.bls.gov/schedule/2026/11_sched.htm'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('NAND 가격','https://www.trendforce.com/price/flash/flash_spot'),('국내 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('하나은행 고시','https://m.stock.naver.com/marketindex/exchange/FX_USDKRW'),('FRED 금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
paragraphs=[
('', '코스피가 반등을 시도할 외부 여건은 전날보다 나아졌습니다. 미국 반도체주가 폭넓게 올랐고 유가와 달러/원 고시환율은 내렸습니다. 다만 월요일 국내장은 상승분을 지키지 못했습니다. 오늘은 개장 직후의 상승 폭보다 5,250 회복에 외국인과 프로그램 매수가 동참하는지가 관건입니다.'),
('반도체 전반은 올랐지만 Nvidia는 내렸다','9일 미국 정규장에서 AMD는 13.26%, Broadcom은 8.78%, Micron은 6.25% 상승했습니다. SOXX는 7.49%, SMH는 5.05% 올랐습니다. QQQ와 TQQQ도 각각 3.54%, 10.20% 상승했습니다. 이 반등은 월요일 한국장 마감 뒤 형성된 가격 변화여서 오늘 국내 반도체주를 지지하는 새 재료입니다. <a href="https://finance.yahoo.com/quote/SMH/">미국 시세</a>'),
('', '반면 Nvidia는 4.27% 하락했습니다. 이사회는 8일 해외 정보활동의 표적이 됐다는 보도와 관련해 독립 조사를 시작한다고 밝혔습니다. 성명은 국가안보나 회사 비밀이 침해됐다고 믿을 이유가 없으며 경영진을 신뢰한다고 명시했습니다. 조사 착수를 기술 유출 확정이나 최고경영자 교체로 확대해서는 안 됩니다. 일요일 발표 자체는 월요일 한국장에서도 접할 수 있었던 정보입니다. <a href="https://investor.nvidia.com/news/press-release-details/2026/Statement-from-NVIDIA-Board-of-Directors/default.aspx">이사회 성명</a>'),
('유가와 환율이 함께 부담을 덜었다','브렌트 선물은 10일 06:59:30 KST 전자거래 기준 배럴당 92.17달러로 전회 대비 6.26% 내렸습니다. 유가 하락은 에너지 수입 비용과 물가 압력을 낮추는 방향입니다. 다만 유가만으로 미국 금리 인하나 AI 투자 회복을 단정할 수는 없습니다. <a href="https://finance.yahoo.com/quote/BZ=F/">브렌트 선물</a>'),
('', '10일 07:25:56 KST 하나은행 달러/원 고시환율은 1,342.00원으로 전회보다 21.50원 낮았습니다. 서울 현물환 개장 체결가와는 구분해야 합니다. 전날의 원화 약세가 완화되면 외국인 매수 여건이 개선될 수 있습니다. 실제 주식 매수로 이어지는지는 현물과 프로그램 수급이 판단 기준입니다. <a href="https://m.stock.naver.com/marketindex/exchange/FX_USDKRW">하나은행 고시</a>'),
('주가 반등과 메모리 가격은 별개다','TrendForce의 9일 18:10 대만시간 DRAM 현물가격에서 DDR5 16Gb 평균은 60.167달러로 보합, DDR4 16Gb는 80.236달러로 0.72% 하락했습니다. Micron 주가 급등을 범용 메모리 가격 상승으로 읽기는 어렵습니다. HBM·서버 DRAM의 장기 주문과 NAND·eSSD의 수요는 품목별 계약과 출하 흐름을 따로 봐야 합니다. <a href="https://www.trendforce.com/price/dram/dram_spot">메모리 가격</a>'),
('', 'AI 설비투자가 메모리 매출로 이어지려면 고객의 자금 조달과 실제 집행이 뒷받침돼야 합니다. 빅테크의 CAPEX 계획이 커도 현금흐름 부담이나 데이터센터 인허가 지연이 커지면 주가는 먼저 조정받을 수 있습니다. 오늘 미국 업종 반등은 위험 선호 개선의 증거이며 삼성전자·SK하이닉스의 신규 주문이나 수율 개선을 직접 증명하지는 않습니다.'),
('월요일 반등 실패를 넘어서야 한다','9일 코스피는 5,034.20에 출발해 5,172.94까지 올랐지만 5,018.85로 마감했습니다. 저가는 4,990.66이며 종가는 전 거래일보다 0.81% 낮았습니다. KODEX 레버리지는 53,500원에 출발해 52,850~57,245원 사이에서 움직인 뒤 53,665원으로 1.46% 하락했습니다. 미국 반등을 기대한 선행 매수만으로 국내 상승이 지속되지는 않았습니다. <a href="https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle">국내 일봉</a>'),
('', '직전 전망의 기본 종가 범위 4,950~5,200에는 들어왔습니다. 그러나 종가가 범위에 들었다는 사실과 수급 조건이 충족됐다는 판단은 별개입니다. 오늘은 5,050 위 안착과 전일 고가 5,172.94 돌파를 거쳐 5,250을 회복하는지 봅니다. 전일 저가 부근으로 되밀리면 미국 업종 강세의 전달력이 약하다는 뜻입니다.'),
('세 종가 시나리오와 KODEX 기준선','기본 범위는 5,050~5,250, 확률은 50%입니다. 지수가 이 범위에 머물고 외국인 현물이 순매수 또는 보합인 경우를 가정합니다. 5,250을 넘으면서 외국인·프로그램이 함께 순매수하면 강세 범위 5,250 초과~5,450(30%)을 봅니다. 5,050 아래에서 외국인·프로그램 순매도가 겹치면 약세 범위 4,800~5,050 미만(20%)입니다. 경계값은 기본 범위에 배정하며 각 범위를 벗어나거나 수급 조건이 깨지면 해당 시나리오는 무효입니다. 별도의 장중 예상 저가·고가 포락은 4,700~5,550으로 둡니다.'),
('', '대응은 공격 25·관망 50·방어 25입니다. KODEX의 1차 지지는 전일 저가 52,850원, 반등 기준은 전일 종가 53,665원, 저항은 전일 고가 57,245원입니다. 갭 상승 뒤 57,245원을 넘어도 외국인·프로그램 매수가 이어지지 않으면 추격 근거는 약합니다. 53,665원 아래로 되밀리면 반등 지속을 재검토하고 52,850원 이탈 시 손실 확대 위험을 경계합니다.'),
('오늘 밤 CPI가 다음 방향을 정한다','미국 10월 CPI는 10일 08:30 ET, 한국시간 22:30에 발표됩니다. 오늘 한국장 종가 이후의 변수입니다. PPI는 13일 같은 시각에 예정돼 있습니다. 오늘은 09:30 외국인·프로그램 방향, 10:30 삼성전자·SK하이닉스 저점 유지, 14:00 이후 매수 지속을 차례로 확인합니다. 시나리오 조건 관측 시한은 15:20입니다. <a href="https://www.bls.gov/schedule/2026/11_sched.htm">BLS 공식 일정</a>'),
('미 국채 금리차','FRED의 9일 관측에서 10년-2년 금리차는 0.32%포인트, 10년-3개월은 0.64%포인트입니다. 개별 만기의 최신 관측일은 6일로 3개월 4.19%, 2년 4.51%, 10년 4.86%입니다. 관측일이 다른 수치를 같은 시점의 곡선으로 합쳐서는 안 됩니다. 유가 하락에도 높은 절대금리는 성장주 가치평가에 부담으로 남습니다. <a href="https://fred.stlouisfed.org/series/T10Y2Y">FRED</a>')]
def table(h,rows):return '<div class="article-table-wrap"><table class="article-data-table"><thead><tr>'+''.join('<th>'+x+'</th>' for x in h)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def mdtable(h,rows):return '|'+ '|'.join(h)+'|\n|'+'|'.join(['---']*len(h))+'|\n'+'\n'.join('|'+ '|'.join(map(str,row))+'|' for row in rows)
us=[];after=[]
for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO']:
 r=ev('yahoo-'+k)['data']['chart']['result'][0];q=r['indicators']['quote'][0];i=max(i for i,v in enumerate(q['close']) if v);us.append([k]+[f'{q[a][i]:,.2f}' for a in ['open','high','low','close']]+[f"{r['meta']['regularMarketChangePercent']:+.2f}%"])
for k in ['NVDA','AMD','MU','AVGO']:
 r=load(P/('after-'+k+'.raw'))['chart']['result'][0];post=r['meta']['currentTradingPeriod']['post'];v=[(t,c) for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if v:
  t,c=v[-1];after.append([k,f'{c:.2f}',f'{(c/r["meta"]["regularMarketPrice"]-1)*100:+.2f}%',dt.datetime.fromtimestamp(t,dt.timezone(dt.timedelta(hours=9))).isoformat()])
uh=['종목','시가 USD','고가','저가','종가','등락'];ah=['종목','시간외 USD','정규장 대비','시각 KST'];charts=[f'charts/us_yield_spreads_{k}_{D}.png' for k in ['long_term','90d']]
body=''.join(('<h2>'+h+'</h2>\n' if h else '')+'<p>'+t+'</p>\n' for h,t in paragraphs)
body+='<h2>발행 기준 시세</h2>{{fastTable}}<h2>미국 11월 9일 정규장</h2>'+table(uh,us)+'<h2>미국 시간외</h2><p>11월 9일 미국 시간외 거래이며 정규장 종가 대비입니다.</p>'+table(ah,after)
body+=''.join('<figure><img style="width:100%;height:auto" src="../'+c+'" alt="미국 국채 금리차"></figure>' for c in charts)+'<h2>출처</h2><ul>'+''.join('<li><a href="'+u+'">'+s+'</a></li>' for s,u in sources)+'</ul>'
write(P/'article-body.html',body)
import re
plain=lambda t:re.sub('<[^>]+>','',t)
write(P/'report-template.md',f'# {D} KOSPI·KODEX 리서치\n작성 {{{{issuedAt}}}} / 최종 데이터 {{{{cutoff}}}} / 한국 {{{{marketLabel}}}}\n\n'+'\n\n'.join(('## '+h+'\n' if h else '')+plain(t) for h,t in paragraphs)+'\n\n## 한국시장\n{{fastTable}}\n\n## 미국 정규장\n'+mdtable(uh,us)+'\n\n## 미국 시간외\n'+mdtable(ah,after)+'\n\n'+'\n'.join('![미국 금리차](../'+c+')' for c in charts)+'\n\n## 출처\n'+'\n'.join('- ['+s+']('+u+')' for s,u in sources)+'\n\n취재·집필 입력 '+at)
# 전일 actual과 outcome은 신규 생성만 허용.
m=runner.evaluation();reason='장전 응답은 당일 초기화되어 전일 최종 수급 묶음 및 발행 이후 경로 원천 미확보'
evidence={'sourceStatus':'unavailable','source':ev('KOSPI-integration')['url'],'asOf':PREV+'T15:30:00+09:00','fetchedAt':at,'missingReason':reason,'rawHash':ev('KOSPI-integration')['rawHash']}
a={'schemaVersion':1,'sessionDate':PREV,'bizdate':'20261109','fetchedAt':at,'marketStatus':'CLOSE','closeSnapshotMissingReason':reason,'flowTrajectoryMissingEvidence':evidence}
kr=next(v for v in ev('122630')['data'] if v['localTradedAt']==PREV)
for key,v,src in [('kospi',prev,ev('KOSPI-history')),('kodex',kr,ev('122630'))]:a[key]={j:runner.num(v[j+'Price']) for j in ['open','high','low','close']};a[key].update(asOf=PREV+'T15:30:00+09:00',source=src['url'],rawHash=src['rawHash'])
ap=R/f'research/evaluation/actuals/{PREV}.json';m.validate_actual(a,ap)
if not ap.exists():dump(ap,a)
fp=next((R/'research/evaluation/forecasts').glob(PREV+'-*-same-close.json'));f=load(fp);fid=f['forecastId'];op=R/f'research/evaluation/outcomes/{fid}.json'
o={'schemaVersion':1,'forecastId':fid,'recordedAt':at,'actualRef':PREV,'realizedScenario':'base','errorCodes':['cause_unverifiable'],'triggerResults':[{'id':c['id'],'status':'unavailable','reason':reason} for t in f['scenarioTriggers'].values() for c in t['conditions']],'driverAssessment':[{'id':d['id'],'status':'unverifiable'} for d in f['drivers']],'hypothesisTests':[]}
m.validate_outcome(o,op,m.validate_forecast(f,fp,R),m.validate_actual(a,ap))
if not op.exists():dump(op,o)
image=f'assets/images/articles/market-{D}-oil-recovery-1200x630.png';Image.open('C:/Users/madro/.codex/generated_images/01a1c28b-3452-7e60-902e-5129c995fe3d/exec-250c2fa7-dd94-4865-8b91-6c8afc256ed6.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5250,'high':5450,'probability':.30},'base':{'low':5050,'high':5250,'probability':.50},'bear':{'low':4800,'high':5050,'probability':.20}};posture={'attack':25,'wait':50,'defense':25};triggers={}
for kind in scenarios:
 cs=[('floor','kospi_price','gte',5050),('cap','kospi_price','lte',5250),('foreign','foreign_cash','gte',0)] if kind=='base' else [('price','kospi_price','gt' if kind=='bull' else 'lt',5250 if kind=='bull' else 5050),('foreign','foreign_cash','gt' if kind=='bull' else 'lt',0),('program','program_total','gt' if kind=='bull' else 'lt',0)]
 triggers[kind]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':kind+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':kind+'-'+i} for i,met,oper,v in cs]}
dash=load(R/'research/evidence/2026-11-09/dashboard-input.json')
dash.update(headline=title,summary=summary,stance=dict(label='반등 뒤 국내 매수 지속 확인',note='유가·환율 부담 완화와 국내 매수 지속을 함께 봅니다.',**posture),changes=[{'label':'KOSPI 전일','before':'5,059.69','after':'5,018.85','meaning':'0.81% 하락 뒤 미국 반도체 급반등'}],factors=[{'label':'미국 반도체','metric':'SOXX +7.49%','detail':'11월 9일 정규장','tone':'positive'},{'label':'Nvidia','metric':'-4.27%','detail':'이사회 조사 착수·경영진 신뢰 유지','tone':'negative'}],memory=[{'label':'DDR5 16Gb','value':'$60.167','change':'11/9 보합'},{'label':'DDR4 16Gb','value':'$80.236','change':'11/9 -0.72%'}],events=[{'time':'11월 10일 22:30 KST','name':'미국 10월 CPI','path':'물가·금리·성장주'},{'time':'11월 13일 22:30 KST','name':'미국 10월 PPI','path':'생산비용·물가'}],sources=[{'label':s,'href':u} for s,u in sources],scenarios=[])
for market in dash['markets']:market['asOf']=PREV+'T15:30:00+09:00'
for k,label,ran,cond,invalid in [('bull','강세 · 30%','5,250 초과~5,450',['5,250 초과','외국인 순매수','프로그램 순매수'],'5,250 재이탈 또는 수급 반전'),('base','기본 · 50%','5,050~5,250',['5,050 이상','5,250 이하','외국인 현물 0 이상'],'범위 이탈 또는 외국인 순매도'),('bear','약세 · 20%','4,800~5,050 미만',['5,050 미만','외국인 순매도','프로그램 순매도'],'5,050 회복 또는 수급 반전')]:dash['scenarios'].append({'id':k,'label':label,'range':'KOSPI '+ran,'summary':'국내 매수 지속과 가격 회복을 함께 판단','conditions':cond,'invalidation':invalid})
dash['strategyLevels']=[{'asset':'KOSPI','support':'5,050','pivot':'5,250','resistance':'5,450'},{'asset':'KODEX 레버리지','support':'52,850원','pivot':'53,665원','resistance':'57,245원'}]
for ins,values in zip(dash['technical']['instruments'],[[5050,5250,5450],[52850,53665,57245]]):ins.update(asOf=PREV+'T15:30:00+09:00',levels=[{'label':label,'value':v} for label,v in zip(['1차 지지','반등 기준','저항'],values)],interpretation='갭 상승 뒤 가격 지지와 외국인·프로그램 매수 지속을 확인합니다.')
dump(P/'dashboard-input.json',dash)
state='# KOSPI·KODEX 리서치 상태\n- 최신 기준일2026-11-10. 전일KOSPI5018.85(-0.81%),KODEX53665(-1.46%).\n- 미국반도체광범위반등·유가하락·원화강세, Nvidia개별조사위험. 전일최종수급미확보.\n- 기본5050~5250(50),강세5250초과~5450(30),약세4800~5050미만(20),대응25/50/25.\n- 전일기본종가범위충족,수급트리거/발행후경로미검증.\n- 다음11/10 22:30CPI·11/13 22:30PPI. 평가 '+rel(op)+'.\n- 낮은순위제외:TSMC부인주말재료·신규청산/계약원문없음. 연구노트 research/notes/2026-11-10.md.'
files=[image,rel(ap),rel(op),f'research/notes/{D}.md','docs/현재작업중.md']+charts+[rel(p) for p in P.rglob('*') if p.is_file() and p.name not in ['run-status.json','pipeline-state.json'] and '080149-382721' not in str(p)]
package=dict(date=D,previousSessionDate=PREV,title=title,summary=summary,image=image,imageAlt='햇빛 아래 청록색 유리 스프링과 내려오는 기름방울, 얇은 커튼 뒤 기둥',bodyPath=rel(P/'article-body.html'),reportTemplate=rel(P/'report-template.md'),dashboardPath=rel(P/'dashboard-input.json'),notesPath=f'research/notes/{D}.md',scenarios=scenarios,posture=posture,pathEnvelope={'low':4700,'high':5550,'coverage':.9},marketRegime='risk_off',scenarioTriggers=triggers,drivers=[{'id':'semiconductor','rank':1,'claim':'미국 반도체 광범위 반등','validationMetric':'반도체·KOSPI'},{'id':'fx-oil','rank':2,'claim':'유가·환율 부담 완화','validationMetric':'USD/KRW·브렌트·외국인'}],stateText=state,charts=charts,files=list(dict.fromkeys(files+[rel(P/'package.json')])));dump(P/'package.json',package)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+'\n## 2026-11-10 KOSPI 장전 발행\n\n- reports/2026-11-10.md, articles/market-2026-11-10.html, STATE.md, 홈·목록·대시보드·사이트맵을 오늘 자료로 갱신한다.\n- research/notes/2026-11-10.md, research/evidence/2026-11-10 입력·원천·package, 전일 actual/outcome, 신규 유가·회복 썸네일, charts/us_yield_spreads_*_2026-11-10.png를 보존한다.\n- 미국 반도체반등·유가/환율완화와 Nvidia 개별위험 분리, 기본5050~5250·대응25/50/25. 공통 발행기로 관련 검사·선별 커밋/푸시·배포·양도메인 대조를 수행한다.\n')
print('package ready',at)
