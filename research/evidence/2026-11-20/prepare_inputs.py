import json,datetime as dt,sys,re,html
from pathlib import Path
from PIL import Image
R=Path.cwd();P=Path(__file__).parent;D='2026-11-20';PREV='2026-11-19';E=P/'collections/075816-688069';at=dt.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,t):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(t,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return load(E/(k+'.json'))
def rel(p):return str(p.relative_to(R)).replace('\\','/')
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
prev=runner.previous_session({k:ev(k) for k in ['KOSPI','KOSPI-history','KOSPI-basic']},PREV)
title='Anthropic 상장에도 반도체주 하락…코스피 5,000선과 매도 압력 주목'
summary='AMD가 7.72%, Nvidia가 3.30% 하락했습니다. AI 상장 열기와 기존 반도체주 매도가 갈린 가운데 코스피 5,000선 지지와 외국인·프로그램 수급을 살핍니다.'
sources=[('Anthropic 공모가 발표','https://www.anthropic.com/news/anthropic-prices-initial-public-offering'),('AMD 공매도 보고서 관련 Reuters','https://finance.yahoo.com/technology/articles/amd-shares-slide-short-seller-174947184.html'),('AMD 반론 보도','https://finance.yahoo.com/markets/stocks/articles/amd-shares-tumble-7-short-211846447.html'),('Jefferson 연설','https://www.federalreserve.gov/newsevents/speech/jefferson20261119a.htm'),('미국 종가','https://m.stock.naver.com/worldstock/stock/NVDA.O/total'),('국내 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('NAND 현물','https://www.trendforce.com/price/flash/flash_spot'),('FRED 10년-2년','https://fred.stlouisfed.org/series/T10Y2Y'),('FRED 10년-3개월','https://fred.stlouisfed.org/series/T10Y3M'),('미국 경제 일정','https://www.bls.gov/schedule/2026/home.htm')]
notes=f'''# {D} 취재 노트
실제 조사 시작 run-status.startedAt, 07:58:16 원천21종 수집, 08시경 공식발표/미국종가8종 교차확인. 작성 {at}.
후보 순위: 1 미국 반도체 동반하락과 장초반 반등 소멸(14점), 2 AMD 공매도 보고서/수출규제 우려(13), 3 Anthropic IPO 자금조달과 기존 AI주 괴리(12), 4 Jefferson AI 건설 물가압력(10), 5 국내 전일 반등과 매도 지속위험(10), 6 DDR5/DDR4 차별화(8), 7 유가 반등(7), 8 신규 공급계약/청산/재해(새 확정사실 미확보 제외).
상위1~3 우선. AMD 의혹은 공매도측 주장/이해관계 명시, 법위반 확정 아님. 원문 직접접근 불가로 Reuters와 AMD 반론 보도 대조. 펌웨어 기술 세부 단정 제외. Anthropic 980m주*$83=$81.34B는 구주포함 총공모액, 회사순유입과 다름. 별도사모액 본문 제외. IPO가 매도를 유발했다는 인과 확정 금지.
Yahoo와 Naver 11/19 16:00 ET 종가8종 일치. 시간외 마지막 표본 UTC22:57~22:59(07:57~07:59KST): NVDA146.0847 AMD479.5617 MU685.8 AVGO347.1542. 20시ET 최종시간외 아님. 유가 선물은 원천시각을 별도 표기. 국내수급은 새벽 초기화로 전일 최종자료 미확보, 0 추정 금지.
TrendForce 공식웹 11/19 18:10 GMT+8 DDR5 60.667 +0.28%, DDR4 78.75 -0.25%; NAND11/9 512TLC14.267 -11.67%. Python TLS실패는 공식웹 대체. HBM 계약가/물량/수율로 일반화 안함. 신규 기업 CAPEX/FCF 공시 미확보. 신규 기업매출 숫자를 구판에서 재사용하지 않음.
FRED11/19 spread0.28/0.70, 개별만기11/18 5.07/4.80/4.34. 전체2년/90일신규차트 생성. 전일5137.89 기본4950~5150내, 수급조건 판정불가. 사임/실적/원격접근 규제는 기존 국내반영분과 분리, 미국11/19 추가매도만 새 가격충격.
전망확률은 판단값, 활성 정량가설 없음. 누적평가기9/21해시불일치는 오늘 계약과 분리.
'''
write(R/f'research/notes/{D}.md',notes)
paragraphs=[
('상장 열기가 반도체 매도를 막지 못했다','19일 미국 정규장에서 AMD는 7.72%, Nvidia는 3.30%, Micron은 2.10%, Broadcom은 2.09% 하락했습니다. 반도체 ETF인 SOXX와 SMH도 각각 2.75%, 2.62% 내렸습니다. 전날 종목별로 엇갈렸던 흐름이 동반 하락으로 바뀌어, 오늘 국내 반도체주에도 매도 압력이 커질 수 있습니다. <a href="'+sources[4][1]+'">미국 종가</a>'),
('', 'Anthropic은 주당 83달러에 9억8천만 주를 공모하고 19일 나스닥 거래를 시작하도록 일정을 잡았습니다. 총공모액은 구주매출을 포함해 813억4천만 달러입니다. 새 AI 기업을 향한 자금 수요가 크더라도 기존 장비·반도체 기업의 주가까지 함께 오르는 것은 아닙니다. 상장과 같은 날 나타난 하락만으로 자금 이동이 매도의 원인이라고 단정할 수도 없습니다. <a href="'+sources[0][1]+'">회사 발표</a>'),
('AMD 의혹은 확정된 제재와 구분해야 한다','Hunterbrook은 AMD에 대한 공매도 포지션을 공개하면서 중국 관련 거래와 수출규제 위험을 제기했습니다. AMD는 해당 주장이 사업 관행과 관계를 잘못 묘사한다며 미국 수출통제 법규를 준수한다고 반박했습니다. 의혹 제기와 회사 반론이 맞서는 단계이며 법 위반이 확정된 사건으로 볼 수 없습니다. <a href="'+sources[1][1]+'">Reuters</a> · <a href="'+sources[2][1]+'">AMD 반론</a>'),
('', '한국 메모리 업체에 전해지는 당장의 위험은 AI 투자 수요의 소멸보다 반도체주 전반의 위험 회피입니다. 규제 불안이 고객의 주문과 실제 출하를 줄이는지, 주식시장의 매도에 머무는지는 나눠 봐야 합니다. Nvidia의 앞선 실적과 경영진 변화는 이미 지난 한국장에 반영된 재료이고, 오늘 새 부담은 이후 미국 정규장의 추가 하락입니다.'),
('코스피 5,000선에서 매수의 지속을 본다','19일 코스피는 5,090.04에 출발해 4,963.61까지 밀렸다가 당일 고가인 5,137.89로 1.39% 상승 마감했습니다. KODEX 레버리지도 55,265원에 출발해 52,170원까지 하락한 뒤 고가인 56,035원으로 3.01% 올랐습니다. 두 거래일 연속 반등했지만 미국 반도체 매도가 오늘도 그 회복을 시험합니다. <a href="'+sources[5][1]+'">국내 일봉</a>'),
('', '기본 종가 범위는 4,950~5,150, 확률은 45%입니다. 외국인 현물이 순매도로 기울지 않는 경우를 가정합니다. 5,150 초과와 외국인·프로그램 동반 순매수가 겹치면 강세 5,150 초과~5,350(15%), 4,950 미만과 두 수급의 동반 순매도가 겹치면 약세 4,700~4,950 미만(40%)을 둡니다. 경계값은 기본 범위에 배정하고, 범위 이탈이나 수급 반전은 각 가정을 무효화합니다. 장중 저가·고가의 예상 포락은 별도로 4,550~5,450입니다.'),
('', '대응 점수는 공격 10·관망 40·방어 50입니다. KODEX의 1차 지지는 전일 저가 52,170원, 반등 기준은 전일 시가 55,265원, 저항은 전일 고가이자 종가인 56,035원입니다. 갭 하락 뒤 55,265원 회복과 외국인·프로그램 매수가 함께 나타나야 반등의 지속을 기대할 수 있습니다. 52,170원 이탈과 동반 매도에는 방어 비중을 높일 조건이 됩니다.'),
('메모리 현물과 주가는 다른 속도로 움직인다','TrendForce의 19일 18:10 대만시간 현물 표에서 DDR5 16Gb 평균은 60.667달러로 0.28% 상승했고 DDR4 16Gb는 78.75달러로 0.25% 하락했습니다. 품목별 가격 차별화가 이어지는 가운데 미국 메모리 주식은 하락했습니다. 현물가격의 소폭 상승만으로 주식 매도를 상쇄하기는 어렵습니다. <a href="'+sources[6][1]+'">DRAM 현물</a>'),
('', 'NAND 512Gb TLC 웨이퍼 현물은 9일 관측 기준 14.267달러로 11.67% 하락했습니다. 관측일과 제품이 다른 이 가격을 오늘 HBM이나 기업용 SSD의 계약가격 변화로 옮겨 읽어서는 안 됩니다. 삼성전자·SK하이닉스의 이익을 판단하려면 고부가 제품의 출하와 수익성, 주가를 판단하려면 외국인 현물과 선물 수급을 각각 봐야 합니다. <a href="'+sources[7][1]+'">NAND 현물</a>'),
('AI 투자에는 자금 비용도 따른다','Jefferson 연준 부의장은 19일 연설에서 AI 설비투자가 현재 수요와 물가를 밀어 올리는 한편 미래 생산성 향상은 물가를 낮출 수 있다고 설명했습니다. 투자 지출과 생산성 효과가 나타나는 시점이 다르다는 뜻입니다. 수요 증가만으로 금리 부담이 빠르게 낮아질 것으로 기대하기는 어렵습니다. <a href="'+sources[3][1]+'">연준 연설</a>'),
('', 'FRED의 19일 관측에서 10년-2년 금리차는 0.28%포인트, 10년-3개월은 0.70%포인트입니다. 개별 금리는 18일 기준 10년 5.07%, 2년 4.80%, 3개월 4.34%입니다. 서로 다른 관측일의 값을 같은 날 금리곡선으로 합치지 않아야 합니다. 높은 장기금리는 AI 기업의 자금 비용과 주식 가치평가에 부담으로 남습니다. <a href="'+sources[8][1]+'">10년-2년</a> · <a href="'+sources[9][1]+'">10년-3개월</a>'),
('', '09:30에는 외국인 현물·선물과 프로그램 매도 규모, 10:30에는 삼성전자·SK하이닉스의 저점 유지, 14:00 이후에는 매수 전환이 이어지는지 살핍니다. 시나리오 조건 관측 시한은 15:20입니다. 미국 BLS는 20일 10:00 ET, 한국시간 21일 00:00에 주별 고용·실업 통계를 발표할 예정입니다. <a href="'+sources[10][1]+'">공식 일정</a>')]
us=[]
for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO']:
 v=load(P/(k+'.raw'));assert v['marketStatus']=='CLOSE' and v['localTradedAt'].startswith(PREV);m=ev('yahoo-'+k)['data']['chart']['result'][0]['meta'];assert abs(float(v['closePrice'].replace(',',''))-m['regularMarketPrice'])<.02;us.append([k,v['closePrice'],v['fluctuationsRatio']+'%',v['localTradedAt']])
def table(headers,rows):return '<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'
charts=[f'charts/us_yield_spreads_{k}_{D}.png' for k in ['long_term','90d']]
body=''.join(('<h2>'+h+'</h2>' if h else '')+'<p>'+t+'</p>\n' for h,t in paragraphs)
body+='<h2>発行基準</h2>{{fastTable}}<h2>미국 11월 19일 정규장 종가</h2>'+table(['종목','종가 USD','등락','시각 ET'],us)
body=body.replace('発行基準','발행 기준 시세')
body+='<p>미국 시간외는 20일 07:57~07:59 KST 마지막 관측에서 Nvidia 146.0847달러, AMD 479.5617달러, Micron 685.80달러, Broadcom 347.1542달러입니다. 시간외 거래 종료 전 표본이며 정규장 종가와 구분합니다. <a href="https://finance.yahoo.com/quote/AMD/">시간외 시세</a></p>'
body+=''.join('<figure><img style="width:100%;height:auto" src="../'+c+'" alt="미국 국채 금리차"></figure>' for c in charts)
body+='<h2>출처</h2><ul>'+''.join('<li><a href="'+u+'">'+s+'</a></li>' for s,u in sources)+'</ul>'
write(P/'article-body.html',body)
write(P/'report-template.md',f'# {D} KOSPI·KODEX 리서치\n작성 {{{{issuedAt}}}} / 최종 데이터 {{{{cutoff}}}} / 한국 {{{{marketLabel}}}}\n\n'+'\n\n'.join(('## '+h+'\n' if h else '')+re.sub('<[^>]+>','',t) for h,t in paragraphs)+'\n\n## 한국시장\n{{fastTable}}\n\n## 미국 정규장\n'+str(us)+'\n\n시간외는 기사 본문 별도시각 표본. 국내 전일최종수급/시장폭/선물 미확인. 신규 CAPEX/FCF 공시 미확인.\n'+ '\n'.join('![금리차](../'+c+')' for c in charts)+'\n\n## 출처\n'+'\n'.join('- ['+s+']('+u+')' for s,u in sources)+'\n취재 '+at)
old=(R/'research/evidence/2026-11-10/prepare_inputs.py').read_text(encoding='utf-8');exec(old[old.index('m=runner.evaluation()'):old.index("image=f'assets")].replace("'20261109'","'20261119'"))
image=f'assets/images/articles/market-{D}-ipo-divergence-1200x630.png';Image.open('C:/Users/madro/.codex/generated_images/01a1f607-0a1b-7f82-9c68-44c165a45728/exec-4d40e304-166d-4839-a38b-8e653262fc88.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5150,'high':5350,'probability':.15},'base':{'low':4950,'high':5150,'probability':.45},'bear':{'low':4700,'high':4950,'probability':.40}};posture={'attack':10,'wait':40,'defense':50};triggers={}
for k in scenarios:
 cs=[('floor','kospi_price','gte',4950),('cap','kospi_price','lte',5150),('foreign','foreign_cash','gte',0)] if k=='base' else [('price','kospi_price','gt' if k=='bull' else 'lt',5150 if k=='bull' else 4950),('foreign','foreign_cash','gt' if k=='bull' else 'lt',0),('program','program_total','gt' if k=='bull' else 'lt',0)]
 triggers[k]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':k+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':k+'-'+i} for i,met,oper,v in cs]}
dash=load(R/'research/evidence/2026-11-19/dashboard-input.json')
dash.update(headline=title,summary=summary,stance=dict(label='미국 반도체 매도 속 지지 확인',note='5,000선 지지와 외국인·프로그램 매도 압력을 봅니다.',**posture),changes=[{'label':'KOSPI 전일','before':'5,067.44','after':'5,137.89','meaning':'1.39% 반등 뒤 미국 반도체 동반하락'}],factors=[{'label':'미국 반도체','metric':'SOXX -2.75%','detail':'11/19 정규장·AMD -7.72%','tone':'negative'},{'label':'Anthropic','metric':'공모가 $83','detail':'신규 AI 상장 열기와 기존 반도체주 매도 괴리','tone':'neutral'}],memory=[{'label':'DDR5 16Gb','value':'$60.667','change':'11/19 +0.28%'},{'label':'DDR4 16Gb','value':'$78.75','change':'11/19 -0.25%'}],events=[{'time':'11월 20일 09:30·10:30 KST','name':'국내 반도체 지지와 수급','path':'외국인·프로그램 매도 압력'},{'time':'11월 21일 00:00 KST','name':'미국 주별 고용·실업','path':'노동시장·금리'}],sources=[{'label':s,'href':u} for s,u in sources],scenarios=[])
for x in dash['markets']:x['asOf']=PREV+'T15:30:00+09:00'
for k,label,ran,cond,invalid in [('bull','강세 · 15%','5,150 초과~5,350',['5,150 초과','외국인 순매수','프로그램 순매수'],'5,150 재이탈 또는 수급 반전'),('base','기본 · 45%','4,950~5,150',['4,950 이상','5,150 이하','외국인 현물 0 이상'],'범위 이탈 또는 외국인 순매도'),('bear','약세 · 40%','4,700~4,950 미만',['4,950 미만','외국인 순매도','프로그램 순매도'],'4,950 회복 또는 수급 반전')]:dash['scenarios'].append({'id':k,'label':label,'range':'KOSPI '+ran,'summary':'09:30·10:30·14:00 확인, 15:20 마감','conditions':cond,'invalidation':invalid})
dash['strategyLevels']=[{'asset':'KOSPI','support':'4,950','pivot':'5,000','resistance':'5,150'},{'asset':'KODEX 레버리지','support':'52,170원','pivot':'55,265원','resistance':'56,035원'}]
for ins,vals in zip(dash['technical']['instruments'],[[4950,5000,5150],[52170,55265,56035]]):ins.update(asOf=PREV+'T15:30:00+09:00',levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],vals)],interpretation='갭 하락 이후 기준선 회복과 매도 완화를 봅니다.')
dump(P/'dashboard-input.json',dash)
state=f'# KOSPI·KODEX 리서치 상태\n- 최신 {D}. 전일 KOSPI5137.89(+1.39%), KODEX56035(+3.01%).\n- AMD-7.72/NVDA-3.30/SOXX-2.75. Anthropic IPO와 기존주 매도 괴리.\n- 기본4950~5150(45), 강세5150초과~5350(15), 약세4700~4950미만(40), 대응10/40/50.\n- 전일 기본범위충족·수급조건 미검증. 신규 actual/outcome. 다음11/21 00:00 BLS주별고용.\n- 신규청산/계약 제외는 근거미확보, 기존사임/실적/규제중복제외. 취재 research/notes/{D}.md.'
files=[image,rel(ap),rel(op),f'research/notes/{D}.md','docs/현재작업중.md']+charts+[rel(p) for p in P.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.html','.md','.raw'] and p.name not in ['run-status.json','pipeline-state.json'] and '075758-802675' not in str(p)]
package=dict(date=D,previousSessionDate=PREV,title=title,summary=summary,image=image,imageAlt='햇빛 아래 청록색 유리 종과 투명 계단을 따라 흐르는 산호색·파란색 리본',bodyPath=rel(P/'article-body.html'),reportTemplate=rel(P/'report-template.md'),dashboardPath=rel(P/'dashboard-input.json'),notesPath=f'research/notes/{D}.md',scenarios=scenarios,posture=posture,pathEnvelope={'low':4550,'high':5450,'coverage':.9},marketRegime='risk_off',scenarioTriggers=triggers,drivers=[{'id':'semiconductor','rank':1,'claim':'미국 반도체 동반매도','validationMetric':'반도체·KOSPI·외국인'},{'id':'regulation','rank':2,'claim':'AMD 규제위험 의혹과 위험회피','validationMetric':'반도체·프로그램'}],stateText=state,charts=charts,files=list(dict.fromkeys(files+[rel(P/'package.json')])));dump(P/'package.json',package)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+f'\n## {D} KOSPI 장전 발행\n\n- 보고서·기사·홈·목록·대시보드·STATE·사이트맵, 취재·원천·입력·package, 전일 actual/outcome, ipo-divergence 신규 썸네일과 금리차 두 차트.\n- 미국 반도체 동반매도·AMD 의혹/반론·Anthropic 공식IPO. 기본4950~5150·대응10/40/50. 공통발행기 회귀·훅·선별commit/push·배포·두도메인/브라우저 확인.\n')
status=load(P/'run-status.json');status['stages'].update(research=at,writing=at,image=at);status['artifacts']={'package':rel(P/'package.json'),'report':f'reports/{D}.md','article':f'articles/market-{D}.html'};dump(P/'run-status.json',status)
print('ready',at)
