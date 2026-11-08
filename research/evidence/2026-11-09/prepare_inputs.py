import json,datetime as dt,html,sys
from pathlib import Path
from PIL import Image
R=Path.cwd();P=Path(__file__).parent;D='2026-11-09';PREV='2026-11-06';E=P/'collections/080420-182285';at=dt.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def write(p,t):Path(p).write_text(t,encoding='utf-8',newline='\n')
def ev(k):return load(E/(k+'.json'))
def n(v):return float(str(v).replace(',',''))
def rel(p):return str(p.relative_to(R)).replace('\\','/')
sources=[('미국 정규장·시간외','https://finance.yahoo.com/quote/SMH/'),('미국 고용 원문','https://www.bls.gov/news.release/empsit.nr0.htm'),('미국 경제 일정','https://www.bls.gov/schedule/2026/11_sched.htm'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('NAND 공개 가격','https://www.trendforce.com/price/flash/flash_spot'),('국내 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('하나은행 고시','https://m.stock.naver.com/marketindex/exchange/FX_USDKRW'),('미국 금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
title='미국 반도체 반등…코스피 회복은 환율과 외국인 수급이 가른다'
summary='AMD와 Micron이 반등했지만 원화 약세와 메모리 현물 하락은 이어졌습니다. 코스피 5,200 회복과 외국인·프로그램 동반 매수가 반등 지속의 조건입니다.'
paragraphs=[
('', '미국 반도체주가 금요일 반등하면서 코스피도 급락 뒤 회복을 시도할 여건이 생겼습니다. 다만 원화는 약해졌고 메모리 현물가격도 내렸습니다. 오늘은 상승 출발 자체보다 삼성전자·SK하이닉스의 반등에 외국인과 프로그램 매수가 동참하는지가 중요합니다.'),
('미국 반도체 반등은 새로운 재료다','6일 미국 정규장에서 AMD는 11.04%, Micron은 5.12%, Nvidia는 2.78%, Broadcom은 0.74% 올랐습니다. SOXX는 3.51%, SMH는 3.63%, QQQ는 1.40%, TQQQ는 3.54% 상승했습니다. 한국장이 끝난 뒤 나온 반등이므로 오늘 국내 메모리주에는 새로운 지지 재료입니다. 목요일 미국 급락은 금요일 국내장에 이미 반영됐습니다. 같은 하락을 오늘 한 번 더 차감할 이유는 없습니다.'),
('', '반등의 크기와 추세 회복은 구분해야 합니다. Nvidia와 Micron은 미국 정규장 고가 아래에서 마감했습니다. 급락 이전 가격까지 되돌린 것도 아닙니다. 미국 반도체의 회복이 국내 반등으로 이어질 수 있지만, 외국인 매도가 계속되면 개장 직후 상승분을 지키기 어려울 수 있습니다.'),
('고용은 경기 우려를 덜었지만 금리 부담을 남겼다','미 노동통계국이 6일 발표한 10월 비농업 고용은 16만5,000명 증가했고 실업률은 4.1%였습니다. 시간당 평균임금은 전월보다 0.4% 올랐습니다. 고용 증가는 경기 둔화 우려를 덜어 주지만 임금 상승은 물가와 금리 부담을 남깁니다. 반도체 반등만으로 금융 여건이 완화됐다고 보기 어려운 이유입니다.'),
('원화 약세가 국내 반등의 제약이다','9일 07:48:18 KST 하나은행 달러/원 고시환율은 1,363.50원으로 전회 대비 6.50원 높았습니다. 서울 현물환 개장 체결가는 아닙니다. 원화 약세가 이어지면 외국인이 국내 주식을 적극적으로 늘리기 어렵고, 수출주의 환산이익 기대보다 시장의 위험 축소가 먼저 나타날 수 있습니다. 환율 상승이 진정되는지와 외국인 현물·선물의 방향을 함께 봅니다.'),
('메모리 현물은 주가와 다른 방향이다','TrendForce의 6일 18:10 대만시간 DRAM 현물가격은 DDR5 16Gb 평균 60.167달러로 0.82%, DDR4 16Gb 평균 80.815달러로 1.06% 내렸습니다. 미국 메모리주 반등이 당장 범용 메모리 가격 회복을 뜻하지는 않습니다. HBM과 서버용 장기계약의 수요도 이 현물 지표 하나로 판단할 수 없습니다. NAND와 RDIMM 공개 표는 10월 자료여서 이번 거래일 가격 변화의 근거로 삼기 어렵습니다.'),
('', 'AI 투자에서는 이미 발표한 설비투자 계획보다 실제 집행과 현금흐름이 주가의 다음 시험대입니다. 반등이 지속되려면 투자 취소 우려가 줄고 주문과 매출 전환을 뒷받침하는 공시가 따라와야 합니다. 오늘 반등만으로 신규 공급계약이나 투자 확대가 확정됐다고 해석하지 않습니다.'),
('전일 저점을 지키고 5,200을 회복하는가','금요일 코스피는 5,263.26에 출발해 고가 5,269.10, 저가 4,911.28을 기록한 뒤 5,059.69로 마감했습니다. 하루 하락률은 6.02%입니다. KODEX 레버리지는 12.86% 내린 54,460원으로 끝났고 장중 범위는 51,065~58,585원이었습니다. 코스피가 전일 저가 위에서 저점을 높이고 5,200을 되찾는다면 단기 회복의 근거가 강해집니다. 반대로 4,950을 지키지 못하면 전일 저점 재시험을 경계합니다.'),
('', '직전 전망의 기본 종가 범위 5,050~5,350에는 들어왔지만 장중에는 하단을 크게 밑돌았습니다. 종가 범위에 들었다는 사실만으로 하루의 위험을 잘 포착했다고 평가하기 어렵습니다. 오늘도 종가 전망과 장중 손실 위험을 따로 봅니다.'),
('오늘의 세 시나리오와 KODEX 기준선','기본 종가 범위는 4,950~5,200으로 확률 50%입니다. 4,950 이상 유지, 5,200 이하의 매물 소화, 외국인 현물 매도 진정을 함께 확인하는 경우입니다. 외국인 매도 진정의 관측 기준은 순매수액 0 이상으로 둡니다. 5,200을 넘고 외국인·프로그램이 함께 순매수하면 강세 범위 5,200 초과~5,400(25%)을 봅니다. 4,950 아래에서 외국인·프로그램 순매도가 겹치면 약세 범위 4,700~4,950 미만(25%)입니다. 각 종가 범위를 벗어나면 해당 시나리오는 무효이며 경계값은 기본 범위에 배정합니다. 세 시나리오의 장중 예상 저가·고가 포락은 4,600~5,500으로 둡니다.'),
('', '공격 15·관망 50·방어 35로 관망에 무게를 둡니다. KODEX는 전일 저가 51,065원, 종가 54,460원, 고가 58,585원을 기준선으로 봅니다. 갭 상승 때는 54,460원 위 안착과 거래량을 확인하고 58,585원 부근에서는 매물 소화 여부를 봅니다. 51,065원을 이탈하면 반등 가정이 약해집니다. 외국인 매수가 없는 급등을 추격할 근거는 부족합니다.'),
('내일 CPI 전까지 수급을 확인한다','미국 10월 CPI는 10일 22:30 KST에 발표됩니다. 오늘 한국장 종가 뒤의 일정이며 아직 결과는 나오지 않았습니다. 오늘은 09:30 외국인·프로그램 방향, 10:30 삼성전자·SK하이닉스 저점 유지, 14:00 이후 매수 지속 여부를 차례로 확인합니다. 시나리오 조건은 15:20까지 관측합니다.'),
('미 국채 금리차','FRED의 6일 기준 10년-2년 금리차는 0.35%포인트, 10년-3개월은 0.67%포인트입니다. 개별 만기 금리의 최신 관측일은 5일이며 3개월 4.17%, 2년 4.46%, 10년 4.84%입니다. 서로 다른 관측일의 수준을 한 시점의 곡선으로 혼동하지 않아야 합니다. 장단기 금리차가 양수라는 사실만으로 반도체주의 밸류에이션 부담이 사라지는 것은 아닙니다.')]
us=[]
for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO']:
 r=ev('yahoo-'+k)['data']['chart']['result'][0];q=r['indicators']['quote'][0];i=max(i for i,v in enumerate(q['close']) if v)
 us.append([k]+[f'{q[a][i]:,.2f}' for a in ['open','high','low','close']]+[f"{r['meta']['regularMarketChangePercent']:+.2f}%"])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 r=load(P/('after-'+k+'.raw'))['chart']['result'][0];post=r['meta']['currentTradingPeriod']['post'];v=[(t,c) for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if v:
  t,c=v[-1];after.append([k,f'{c:.2f}',f'{(c/r["meta"]["regularMarketPrice"]-1)*100:+.2f}%',dt.datetime.fromtimestamp(t,dt.timezone(dt.timedelta(hours=9))).isoformat()])
def table(h,rows):return '<div class="article-table-wrap"><table class="article-data-table"><thead><tr>'+''.join('<th>'+x+'</th>' for x in h)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+x+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def mdtable(h,rows):return '|'+ '|'.join(h)+'|\n|'+'|'.join(['---']*len(h))+'|\n'+'\n'.join('|'+ '|'.join(row)+'|' for row in rows)
uh=['종목','시가 USD','고가','저가','종가','등락'];ah=['종목','시간외 USD','정규장 대비','시각 KST']
body=''.join(('<h2>'+h+'</h2>\n' if h else '')+'<p>'+t+'</p>\n' for h,t in paragraphs)
body+='<h2>발행 기준 시세</h2>{{fastTable}}<h2>미국 11월 6일 정규장</h2>'+table(uh,us)+'<h2>미국 시간외</h2><p>11월 6일 시간외 거래이며 정규장 종가 대비입니다.</p>'+table(ah,after)
charts=[f'charts/us_yield_spreads_{k}_{D}.png' for k in ['long_term','90d']]
body+=''.join('<figure><img style="width:100%;height:auto" src="../'+c+'" alt="미국 국채 금리차"></figure>' for c in charts)
body+='<h2>출처</h2><ul>'+''.join('<li><a href="'+u+'">'+s+'</a></li>' for s,u in sources)+'</ul>'
write(P/'article-body.html',body)
report=f'# {D} KOSPI·KODEX 일일 리서치\n작성 {{{{issuedAt}}}} / 최종 데이터 {{{{cutoff}}}} / 한국 {{{{marketLabel}}}}\n\n'+'\n\n'.join(('## '+h+'\n' if h else '')+t for h,t in paragraphs)+'\n\n## 한국시장\n{{fastTable}}\n\n## 미국 정규장\n'+mdtable(uh,us)+'\n\n## 시간외\n'+mdtable(ah,after)+'\n\n'+ '\n'.join('!['+c+'](../'+c+')' for c in charts)+'\n\n## 출처와 확인 시각\n취재·집필 입력 '+at+'\n'+ '\n'.join('- ['+s+']('+u+')' for s,u in sources)
write(P/'report-template.md',report)
# 전일 확정값과 평가: 원본 전망은 변경하지 않는다.
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
m=runner.evaluation();reason='전일 최종 수급 묶음과 발행 후 시각별 경로 원천 미확보'
evidence={'sourceStatus':'unavailable','source':ev('KOSPI-integration')['url'],'asOf':PREV+'T15:30:00+09:00','fetchedAt':at,'missingReason':reason,'rawHash':ev('KOSPI-integration')['rawHash']}
a={'schemaVersion':1,'sessionDate':PREV,'bizdate':'20261106','fetchedAt':at,'marketStatus':'CLOSE','closeSnapshotMissingReason':reason,'flowTrajectoryMissingEvidence':evidence}
for key,k in [('kospi','KOSPI'),('kodex','122630')]:
 v=next(v for v in ev(k)['data'] if v['localTradedAt']==PREV);a[key]={j:n(v[j+'Price']) for j in ['open','high','low','close']};a[key].update(asOf=PREV+'T15:30:00+09:00',source=ev(k)['url'],rawHash=ev(k)['rawHash'])
ap=R/f'research/evaluation/actuals/{PREV}.json';m.validate_actual(a,ap)
if not ap.exists():dump(ap,a)
fp=next((R/'research/evaluation/forecasts').glob(PREV+'-*-same-close.json'));f=load(fp);fid=f['forecastId']
o={'schemaVersion':1,'forecastId':fid,'recordedAt':at,'actualRef':PREV,'realizedScenario':'base','errorCodes':['cause_unverifiable'],'triggerResults':[{'id':c['id'],'status':'unavailable','reason':reason} for t in f['scenarioTriggers'].values() for c in t['conditions']],'driverAssessment':[{'id':d['id'],'status':'unverifiable'} for d in f['drivers']],'hypothesisTests':[],'postForecastPathStatus':'missing','postForecastPathMissingReason':reason,'postForecastPathMissingEvidence':{k:('incomplete' if k=='sourceStatus' else v) for k,v in evidence.items() if k!='missingReason'}}
for k in ['postForecastPathStatus','postForecastPathMissingReason','postForecastPathMissingEvidence']:o.pop(k)
op=R/f'research/evaluation/outcomes/{fid}.json';m.validate_outcome(o,op,m.validate_forecast(f,fp,R),m.validate_actual(a,ap))
if not op.exists():dump(op,o)
image=f'assets/images/articles/market-{D}-chip-rebound-fx-1200x630.png'
Image.open('C:/Users/madro/.codex/generated_images/01a1bd66-f315-7fb2-a862-85e7ae620c87/exec-5e7e1886-ad5c-490d-88af-f9d85f1e794c.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5200,'high':5400,'probability':.25},'base':{'low':4950,'high':5200,'probability':.50},'bear':{'low':4700,'high':4950,'probability':.25}};posture={'attack':15,'wait':50,'defense':35};triggers={}
for kind in scenarios:
 cs=[('floor','kospi_price','gte',4950),('cap','kospi_price','lte',5200),('foreign','foreign_cash','gte',0)] if kind=='base' else [('price','kospi_price','gt' if kind=='bull' else 'lt',5200 if kind=='bull' else 4950),('foreign','foreign_cash','gt' if kind=='bull' else 'lt',0),('program','program_total','gt' if kind=='bull' else 'lt',0)]
 triggers[kind]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':kind+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':kind+'-'+i} for i,met,oper,v in cs]}
dash=load(R/'research/evidence/2026-11-06/dashboard-input.json')
dash.update(headline=title,summary=summary,stance=dict(label='반등 지속 조건 확인',note='환율과 외국인·프로그램 동반 매수를 확인합니다.',**posture),changes=[{'label':'KOSPI 전일','before':'5,383.80','after':'5,059.69','meaning':'6.02% 하락 뒤 미국 반도체 반등'}],factors=[{'label':'미국 반도체','metric':'SMH +3.63%','detail':'11월 6일 정규장','tone':'positive'},{'label':'미국 메모리','metric':'Micron +5.12%','detail':'11월 6일 정규장','tone':'positive'}],memory=[{'label':'DDR5 16Gb','value':'$60.167','change':'11/6 -0.82%'},{'label':'DDR4 16Gb','value':'$80.815','change':'11/6 -1.06%'}],events=[{'time':'11월 10일 22:30 KST','name':'미국 10월 CPI','path':'물가·금리·성장주'}],sources=[{'label':s,'href':u} for s,u in sources],scenarios=[])
for market in dash['markets']:market['asOf']=PREV+'T15:30:00+09:00'
for k,label,ran,cond,invalid in [('bull','강세 · 25%','5,200 초과~5,400',['5,200 초과','외국인 순매수','프로그램 순매수'],'5,200 재이탈'),('base','기본 · 50%','4,950~5,200',['4,950 이상','5,200 이하','외국인 현물 0 이상'],'4,950~5,200 이탈'),('bear','약세 · 25%','4,700~4,950 미만',['4,950 미만','외국인 순매도','프로그램 순매도'],'4,950 회복')]:dash['scenarios'].append({'id':k,'label':label,'range':'KOSPI '+ran,'summary':'환율과 수급으로 반등 지속 판단','conditions':cond,'invalidation':invalid})
dash['strategyLevels']=[{'asset':'KOSPI','support':'4,950','pivot':'5,200','resistance':'5,400'},{'asset':'KODEX 레버리지','support':'51,065원','pivot':'54,460원','resistance':'58,585원'}]
dash['technical']['note']='전일 저가·종가·고가와 오늘 조건부 기준선입니다.'
for ins,values in zip(dash['technical']['instruments'],[[4950,5200,5400],[51065,54460,58585]]):
 ins['asOf']=PREV+'T15:30:00+09:00';ins['levels']=[{'label':label,'value':v} for label,v in zip(['1차 지지','반등 기준','저항'],values)];ins['interpretation']='갭 상승 뒤 지지와 외국인·프로그램 동반 매수를 확인합니다.'
dump(P/'dashboard-input.json',dash)
state='# KOSPI·KODEX 리서치 상태\n- 최신 기준일2026-11-09. 직전KOSPI5059.69(-6.02%),KODEX54460(-12.86%).\n- 미국반도체반등과 원화약세 충돌. DRAM현물하락. 전일수급확정묶음 미확인.\n- 기본4950~5200(50),강세5200초과~5400(25),약세4700~4950미만(25),대응15/50/35.\n- 전일기본종가범위충족·장중하단이탈. 수급조건/발행후경로미확보.\n- 다음11/10 22:30CPI. 전일평가 '+rel(op)+'.'
files=[image,rel(ap),rel(op),f'research/notes/{D}.md','docs/현재작업중.md']+charts+[rel(p) for p in P.rglob('*') if p.is_file() and p.name not in ['run-status.json','pipeline-state.json'] and '080403-746547' not in str(p)]
package=dict(date=D,previousSessionDate=PREV,title=title,summary=summary,image=image,imageAlt='밝은 하늘 아래 반등하는 청록색 반도체와 달러·원화 표시의 황금빛 장벽',bodyPath=rel(P/'article-body.html'),reportTemplate=rel(P/'report-template.md'),dashboardPath=rel(P/'dashboard-input.json'),notesPath=f'research/notes/{D}.md',scenarios=scenarios,posture=posture,pathEnvelope={'low':4600,'high':5500,'coverage':.9},marketRegime='risk_off',scenarioTriggers=triggers,drivers=[{'id':'semiconductor','rank':1,'claim':'미국 반도체 반등의 국내 전달','validationMetric':'반도체·KOSPI'},{'id':'fx','rank':2,'claim':'원화 약세와 외국인 수급 제약','validationMetric':'USD/KRW·외국인·프로그램'}],stateText=state,charts=charts,files=list(dict.fromkeys(files+[rel(P/'package.json')])))
dump(P/'package.json',package)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+'\n## 2026-11-09 KOSPI 장전 발행\n\n- reports/2026-11-09.md, articles/market-2026-11-09.html, STATE.md, 홈·목록·대시보드·사이트맵을 오늘 원천으로 갱신한다.\n- research/notes/2026-11-09.md, research/evidence/2026-11-09 입력·원천·package, 전일 actual/outcome, 신규 반등·환율 썸네일과 금리차 차트를 보존한다.\n- 미국 반도체 반등과 원화 약세를 분리하고 기본4950~5200, 대응15/50/35를 적용한다. 공통 발행기로 검증·선별푸시·두 도메인 배포를 수행한다.\n')
print('package ready',at)
