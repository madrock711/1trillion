import json,datetime as dt,sys,re,html,hashlib
from pathlib import Path
from PIL import Image
R=Path.cwd();P=Path(__file__).parent;D='2026-11-19';PREV='2026-11-18';E=P/'collections/080223-006588';at=dt.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,t):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(t,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return load(E/(k+'.json'))
def rel(p):return str(p.relative_to(R)).replace('\\','/')
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
prev=runner.previous_session({k:ev(k) for k in ['KOSPI','KOSPI-history','KOSPI-basic']},PREV)
title='Nvidia 실적 뒤 주가는 하락…금리 부담 속 코스피 5,000선 지지가 관건'
summary='Nvidia가 실적 발표 뒤 2.89% 하락한 반면 AMD와 Broadcom은 올랐습니다. 추가 금리 인상 가능성을 담은 연준 의사록 속에서 코스피 5,000선과 국내 매수 지속을 살핍니다.'
sources=[('연준 의사록','https://www.federalreserve.gov/monetarypolicy/fomcminutes20261028.htm'),('미국 종가','https://m.stock.naver.com/worldstock/stock/NVDA.O/total'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('NAND 현물','https://www.trendforce.com/price/flash/flash_spot'),('국내 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('FRED 10년-2년','https://fred.stlouisfed.org/series/T10Y2Y'),('FRED 10년-3개월','https://fred.stlouisfed.org/series/T10Y3M'),('연준 일정','https://www.federalreserve.gov/newsevents/calendar.htm')]
notes='''# 2026-11-19 취재 노트
실제 조사 시작 08:00경 KST. 지침·동기화 이후 수집 08:02:23, 미국 종가 대체조회 08:05경. 공개 원고와 분리.
후보: 1 연준 의사록 추가 인상 및 AI 투자 금융위험(13점), 2 Nvidia 실적 이후 -2.89%와 업종 차별화(12), 3 전일 국내 +1.99% 반등 반영(11), 4 DDR5 상승/DDR4 하락(8), 5 유가 하락(7), 6 Anthropic IPO 대규모 자금조달(7, 최종 공모가 공식 미확인 제외), 7 수출규제(기존 재료 중복 제외), 8 강제청산·공급계약(새 확정 원문 미확보 제외).
연준 공식 원문 fed.raw: 대다수 추가 인상 예상, AI 건설 물가압력·자산가치 재평가 위험. 금리 결정 자체는 10월 동결 3.75~4.00%, 12월 확정 결정 아님.
Yahoo 21종 수집 성공이나 미국 주식 source time이 11/19 00:52 KST 장중에 머묾. cache-bust 재시도도 동일. 이를 종가로 쓰지 않고 Naver 미국 basic의 11/18 16:00 ET CLOSE 8종을 새 조회해 대체. 시간외 최종값 미확인, 오래된 1분봉 제외.
TrendForce 공식 웹 11/18 18:10 GMT+8 DDR5 60.50 +0.28%, DDR4 16Gb 78.95 -0.22%. NAND 11/9 TLC512 14.267 -11.67%, SLC2Gb4.50 +1.01/MLC64Gb44.174 +0.42는 이전 관측일. HBM·eSSD·계약가로 대체하지 않음. 신규 고객/출하/수율 공시 미확인.
금리차 11/18 0.27/0.73%p, 개별 11/17 10년5.10/2년4.80/3개월4.33. 전일 보고서 종가 기본범위 적중, 수급조건 최종자료 부재로 판정불가. 누적 9/21 해시 문제와 당일 분리. 신규 강제청산 발생 확인 없음.
오늘 가설: 전날 국내 Nvidia실적 반등 이미 반영, 미국 실적후 매도는 추가 위험. SOXX 소폭 상승·AMD/AVGO 상승으로 업종 전면 매도로 확대하지 않음. 공개 확률은 판단이며 정량모델 산출치 아님.
'''
write(R/f'research/notes/{D}.md',notes+'\n확인 '+at)
paragraphs=[
('실적 발표 뒤에도 Nvidia는 하락했다','Nvidia의 실적이 좋았다는 사실만으로 반도체주 전체의 회복을 기대하기는 어려워졌습니다. 18일 미국 정규장에서 Nvidia는 150.96달러로 2.89% 하락했습니다. AMD는 5.31%, Broadcom은 3.64% 올랐고 Micron은 1.00% 내렸습니다. SOXX는 0.28% 상승, SMH는 0.12% 하락해 업종 안에서도 차이가 컸습니다. <a href="'+sources[1][1]+'">미국 종가</a>'),
('', 'Nvidia 실적은 전날 한국장 개장 전에 발표됐고 코스피는 이미 1.99% 반등했습니다. 오늘 새로 더해지는 것은 실적 발표 이후 미국 정규장에서 확인된 매도와 업종별 차별화입니다. 삼성전자·SK하이닉스가 전날 상승을 지키는지, 외국인 현물과 프로그램 비차익 매수가 함께 붙는지가 반등 지속을 가릅니다.'),
('연준은 추가 인상 가능성을 열어 뒀다','한국시간 19일 새벽 공개된 10월 FOMC 의사록에서 거의 모든 참석자는 기본 경제전망 아래 추가 금리 인상이 적절할 가능성이 있다고 봤습니다. 당시 정책금리는 3.75~4.00%로 동결됐습니다. 의사록은 12월 금리 결정을 확정한 문서가 아닙니다. <a href="'+sources[0][1]+'">연준 의사록</a>'),
('', 'AI 설비투자는 반도체 수요를 지탱하지만 공사비와 전력·인력 수요를 늘려 물가와 조달비용을 높일 수도 있습니다. 의사록은 AI 관련 자산가치 재평가와 금융 취약성도 논의했습니다. 기업 매출 증가와 투자 자금의 회수 속도를 함께 봐야 하는 이유입니다. 금리가 높은 상태에서는 매출 전망이 좋아져도 주가의 평가배수가 낮아질 수 있습니다.'),
('5,000 회복 뒤에도 매수의 지속이 필요하다','18일 코스피는 5,098.82에 출발해 4,943.17~5,133.14를 오간 뒤 5,067.44로 1.99% 상승 마감했습니다. KODEX 레버리지는 54,875원에 출발해 51,750~56,090원 사이에서 움직인 뒤 54,400원으로 4.26% 올랐습니다. 반등한 날에도 장중 변동폭은 컸습니다. <a href="'+sources[4][1]+'">국내 일봉</a>'),
('', '오늘 기본 종가 범위는 4,950~5,150이며 확률은 50%입니다. 범위 안에서 외국인 현물이 순매도로 기울지 않는 경우를 가정합니다. 5,150 초과와 외국인·프로그램 동반 순매수가 겹치면 강세 5,150 초과~5,350(20%), 4,950 미만과 두 수급의 동반 순매도가 겹치면 약세 4,700~4,950 미만(30%)입니다. 경계값은 기본 범위에 배정합니다. 범위 이탈 또는 수급 반전이 각 가정을 무효화합니다. 장중 저가·고가의 예상 포락은 별도로 4,600~5,450을 둡니다.'),
('', '대응 점수는 공격 15·관망 50·방어 35입니다. KODEX의 1차 지지는 전일 저가 51,750원, 반등 기준은 전일 종가 54,400원, 저항은 전일 고가 56,090원입니다. 54,400원을 회복해도 반도체와 프로그램 매수가 이어져야 반등을 신뢰할 수 있습니다. 51,750원 이탈과 동반 매도에는 하방 위험이 커집니다.'),
('DDR5와 DDR4 가격 방향도 갈렸다','TrendForce의 18일 18:10 대만시간 현물 표에서 DDR5 16Gb 평균은 60.50달러로 0.28% 올랐고 DDR4 16Gb는 78.95달러로 0.22% 내렸습니다. 서버용 고성능 메모리 수요와 범용 제품의 가격은 같은 속도로 움직이지 않습니다. <a href="'+sources[2][1]+'">DRAM 현물</a>'),
('', 'NAND 512Gb TLC 웨이퍼 현물은 9일 관측 기준 14.267달러, 11.67% 하락입니다. 같은 날 SLC 2Gb는 4.50달러로 1.01%, MLC 64Gb는 44.174달러로 0.42% 올랐습니다. 품목별 수요 차이가 크며 이 가격을 오늘의 HBM·기업용 SSD 계약가격 변화로 해석할 수는 없습니다. AI 투자 확대가 실제 출하와 이익으로 이어지는지와 주식시장의 자금 흐름은 나눠 봐야 합니다. <a href="'+sources[3][1]+'">NAND 현물</a>'),
('환율과 금리, 장중 수급을 함께 본다','19일 05:41:29 KST 하나은행 달러/원 고시는 1,334.00원으로 전회보다 1.50원 낮았습니다. 서울 현물환 체결가와는 다릅니다. 환율 하락은 국내 주식에 우호적인 배경이지만 미국 금리 부담을 모두 상쇄하지는 않습니다. 아래 발행 기준 표의 최신 고시와 선물 가격을 함께 살핍니다.'),
('', 'FRED 18일 관측에서 10년-2년 금리차는 0.27%포인트, 10년-3개월은 0.73%포인트입니다. 개별 만기는 17일 기준 10년 5.10%, 2년 4.80%, 3개월 4.33%입니다. 관측일이 다른 금리차와 개별 금리를 한 시점의 곡선으로 합치지 않아야 합니다. 10년물 절대 수준은 성장주 가치평가의 부담으로 남습니다. <a href="'+sources[5][1]+'">10년-2년</a> · <a href="'+sources[6][1]+'">10년-3개월</a>'),
('', '09:30에는 외국인 현물·선물과 프로그램의 방향, 10:30에는 반도체 저점 유지와 자동차·금융 등으로의 상승 확산, 14:00 이후에는 매수 지속을 봅니다. 시나리오 조건의 관측 시한은 15:20입니다. 연준 일정상 Jefferson 부의장 토론은 19일 09:25 ET, 한국시간 19일 23:25에 예정돼 있습니다. 다음 FOMC는 12월 8~9일입니다. <a href="'+sources[7][1]+'">연준 일정</a>')]
body=''.join(('<h2>'+h+'</h2>' if h else '')+'<p>'+t+'</p>\n' for h,t in paragraphs)
us=[]
for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO']:
 v=load(P/('close-'+k+'.O.json'));assert v['marketStatus']=='CLOSE' and v['localTradedAt'].startswith(PREV);us.append([k,v['closePrice'],v['fluctuationsRatio']+'%',v['localTradedAt']])
def table(headers,rows):return '<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'
charts=[f'charts/us_yield_spreads_{k}_{D}.png' for k in ['long_term','90d']]
body+='<h2>발행 기준 시세</h2>{{fastTable}}<h2>미국 11월 18일 정규장 종가</h2>'+table(['종목','종가 USD','등락','시각 ET'],us)
body+=''.join('<figure><img style="width:100%;height:auto" src="../'+c+'" alt="미국 국채 금리차"></figure>' for c in charts)
body+='<h2>출처</h2><ul>'+''.join('<li><a href="'+u+'">'+s+'</a></li>' for s,u in sources)+'</ul>'
write(P/'article-body.html',body)
write(P/'report-template.md',f'# {D} KOSPI·KODEX 리서치\n작성 {{{{issuedAt}}}} / 최종 데이터 {{{{cutoff}}}} / 한국 {{{{marketLabel}}}}\n\n'+'\n\n'.join(('## '+h+'\n' if h else '')+re.sub('<[^>]+>','',t) for h,t in paragraphs)+'\n\n## 한국시장\n{{fastTable}}\n\n## 미국 정규장\n'+str(us)+'\n\n미국 시간외 최종값 미확인. 유가 수집원천은 00:41~00:42 KST WTI82.94/Brent89.21의 과거 장중값으로 최신 해설에서 제외. 국내 세부 투자자·선물·시장폭 전일 최종자료 미확인. 신규 빅테크 CAPEX·현금흐름 공시 미확인.\n\n'+'\n'.join('![금리차](../'+c+')' for c in charts)+'\n\n## 출처\n'+'\n'.join('- ['+s+']('+u+')' for s,u in sources)+'\n취재 '+at)
# 전일 정산은 신규 파일만 추가한다.
old=(R/'research/evidence/2026-11-10/prepare_inputs.py').read_text(encoding='utf-8')
exec(old[old.index('m=runner.evaluation()'):old.index("image=f'assets")].replace("'20261109'","'20261118'"))
image=f'assets/images/articles/market-{D}-chips-rates-1200x630.png'
Image.open('C:/Users/madro/.codex/generated_images/01a1f0e4-4464-7582-a651-1a3a680c3bc3/exec-3e0a2eae-06fd-499a-8058-0a16c85a1e0a.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5150,'high':5350,'probability':.20},'base':{'low':4950,'high':5150,'probability':.50},'bear':{'low':4700,'high':4950,'probability':.30}};posture={'attack':15,'wait':50,'defense':35};triggers={}
for k in scenarios:
 cs=[('floor','kospi_price','gte',4950),('cap','kospi_price','lte',5150),('foreign','foreign_cash','gte',0)] if k=='base' else [('price','kospi_price','gt' if k=='bull' else 'lt',5150 if k=='bull' else 4950),('foreign','foreign_cash','gt' if k=='bull' else 'lt',0),('program','program_total','gt' if k=='bull' else 'lt',0)]
 triggers[k]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':k+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':k+'-'+i} for i,met,oper,v in cs]}
dash=load(R/'research/evidence/2026-11-18/dashboard-input.json')
dash.update(headline=title,summary=summary,stance=dict(label='금리 부담 속 반등 유지 확인',note='5,000선 지지와 국내 매수 지속을 봅니다.',**posture),changes=[{'label':'KOSPI 전일','before':'4,968.48','after':'5,067.44','meaning':'1.99% 반등·5,000 회복'}],factors=[{'label':'Nvidia','metric':'-2.89%','detail':'실적 발표 이후 미국 정규장 매도','tone':'negative'},{'label':'연준 의사록','metric':'추가 금리 인상 가능성','detail':'10월 동결·향후 결정은 경제지표에 달림','tone':'negative'}],memory=[{'label':'DDR5 16Gb','value':'$60.50','change':'11/18 +0.28%'},{'label':'DDR4 16Gb','value':'$78.95','change':'11/18 -0.22%'}],events=[{'time':'11월 19일 09:30·10:30 KST','name':'반등 유지와 국내 수급','path':'반도체 저점·외국인 매수'},{'time':'11월 19일 23:25 KST','name':'Jefferson 부의장 토론','path':'금리 전망'}],sources=[{'label':s,'href':u} for s,u in sources],scenarios=[])
for x in dash['markets']:x['asOf']=PREV+'T15:30:00+09:00'
for k,label,ran,cond,invalid in [('bull','강세 · 20%','5,150 초과~5,350',['5,150 초과','외국인 순매수','프로그램 순매수'],'5,150 재이탈 또는 수급 반전'),('base','기본 · 50%','4,950~5,150',['4,950 이상','5,150 이하','외국인 현물 0 이상'],'범위 이탈 또는 외국인 순매도'),('bear','약세 · 30%','4,700~4,950 미만',['4,950 미만','외국인 순매도','프로그램 순매도'],'4,950 회복 또는 수급 반전')]:dash['scenarios'].append({'id':k,'label':label,'range':'KOSPI '+ran,'summary':'09:30·10:30·14:00 확인, 15:20 마감','conditions':cond,'invalidation':invalid})
dash['strategyLevels']=[{'asset':'KOSPI','support':'4,950','pivot':'5,000','resistance':'5,150'},{'asset':'KODEX 레버리지','support':'51,750원','pivot':'54,400원','resistance':'56,090원'}]
for ins,vals in zip(dash['technical']['instruments'],[[4950,5000,5150],[51750,54400,56090]]):ins.update(asOf=PREV+'T15:30:00+09:00',levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],vals)],interpretation='반등 뒤 국내 매수 지속과 전일 저가 지지를 봅니다.')
dump(P/'dashboard-input.json',dash)
state=f'# KOSPI·KODEX 리서치 상태\n- 최신 {D}. 전일 KOSPI5067.44(+1.99%), KODEX54400(+4.26%).\n- Nvidia-2.89%·AMD+5.31/AVGO+3.64, 연준 추가 인상 논의. DDR5+0.28/DDR4-0.22.\n- 기본4950~5150(50), 강세5150초과~5350(20), 약세4700~4950미만(30), 대응15/50/35.\n- 전일 기본범위 충족, 수급조건 미검증. 전일 actual/outcome 신규 보존.\n- 11/19 23:25 Jefferson, 다음 FOMC12/8~9. 취재 research/notes/{D}.md.'
files=[image,rel(ap),rel(op),f'research/notes/{D}.md','docs/현재작업중.md']+charts+[rel(p) for p in P.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.html','.md','.raw'] and p.name not in ['run-status.json','pipeline-state.json'] and '080204-355410' not in str(p)]
package=dict(date=D,previousSessionDate=PREV,title=title,summary=summary,image=image,imageAlt='밝은 배경의 반도체 칩과 중앙은행 건물이 금리 추와 함께 놓인 산호색 시소',bodyPath=rel(P/'article-body.html'),reportTemplate=rel(P/'report-template.md'),dashboardPath=rel(P/'dashboard-input.json'),notesPath=f'research/notes/{D}.md',scenarios=scenarios,posture=posture,pathEnvelope={'low':4600,'high':5450,'coverage':.9},marketRegime='mixed',scenarioTriggers=triggers,drivers=[{'id':'earnings-response','rank':1,'claim':'Nvidia 실적 이후 매도와 업종 차별화','validationMetric':'반도체·KOSPI·외국인'},{'id':'rates','rank':2,'claim':'연준 추가 인상 가능성','validationMetric':'금리·환율·프로그램'}],stateText=state,charts=charts,files=list(dict.fromkeys(files+[rel(P/'package.json')])));dump(P/'package.json',package)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+f'\n## {D} KOSPI 장전 발행\n\n- 보고서·기사·홈·목록·대시보드·STATE·사이트맵, 당일 취재·원천·입력·package, 전일 actual/outcome, chips-rates 신규 썸네일과 금리차 차트.\n- Nvidia 실적 이후 매도·연준 의사록·미국 종가 대체조회. 기본4950~5150·대응15/50/35. 공통발행기 회귀·훅·선별commit/push·배포·양도메인 및 브라우저 검증.\n')
status=load(P/'run-status.json');status['stages'].update(research=at,writing=at,image=at);status['artifacts']={'package':rel(P/'package.json'),'report':f'reports/{D}.md','article':f'articles/market-{D}.html'};dump(P/'run-status.json',status)
print('ready',at)
