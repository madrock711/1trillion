"""11월 6일 새로 검증한 취재 입력. 실제 봉인과 발행은 공통 실행기가 담당한다."""
import base64, datetime as dt, html, json, re, sys
from pathlib import Path
from PIL import Image
R=Path.cwd(); P=Path(__file__).parent; D='2026-11-06'; PREV='2026-11-05'
TZ=dt.timezone(dt.timedelta(hours=9)); at=dt.datetime.now(TZ).isoformat()
E=P/'collections/080100-313700'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v): Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(t,encoding='utf-8',newline='\n')
def ev(k): return load(E/(k+'.json'))
def raw(k): return json.loads(base64.b64decode(load(P/(k+'.raw.json'))['raw']))
def rel(p): return str(p.relative_to(R)).replace('\\','/')
def n(v): return float(str(v).replace(',',''))
sources=[('미국 시세','https://finance.yahoo.com/quote/SMH/'),('AI 관련주 매도','https://in.marketscreener.com/news/trading-day-a-november-5-market-bonfire-ce785fddda8ff126'),('Qualcomm 공시','https://www.sec.gov/Archives/edgar/data/804328/000080432826000127/qcom092726erex991.htm'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('2027년 AI 수요 전망','https://www.trendforce.com.tw/presscenter/news/20261105-13295.html'),('BLS 일정','https://www.bls.gov/schedule/2026/11_sched.htm'),('네이버 KOSPI 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('SOXX 분할 공지','https://www.bmv.com.mx/docs-pub/sicderec/sicderec_1584512_1.pdf'),('FRED 금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
us=[]
for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO']:
 r=ev('yahoo-'+k)['data']['chart']['result'][0];q=r['indicators']['quote'][0];v=[(i,c) for i,c in enumerate(q['close']) if c];i,c=v[-1]
 change=r['meta']['regularMarketChangePercent'] if k=='SOXX' else (c/v[-2][1]-1)*100
 us.append([k,*[f'{q[a][i]:,.2f}' for a in ['open','high','low','close']],f'{change:+.2f}%'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 r=raw('after-'+k)['chart']['result'][0];post=r['meta']['currentTradingPeriod']['post'];v=[(t,c) for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']];t,c=v[-1]
 after.append([k,f'{c:.2f}',f'{(c/r["meta"]["regularMarketPrice"]-1)*100:+.2f}%',dt.datetime.fromtimestamp(t,TZ).isoformat()])
def mdtable(headers,rows): return '|'+ '|'.join(headers)+'|\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('|'+ '|'.join(row)+'|' for row in rows)
def htable(headers,rows): return '<div class="article-table-wrap"><table class="article-data-table"><thead><tr>'+''.join('<th>'+html.escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
uh=['종목','시가 USD','고가','저가','종가','등락']; ah=['종목','시간외 USD','정규장 대비','원천 시각 KST']
title='미국 반도체 급락과 원화 약세…코스피는 추가 매물 소화가 먼저'
summary='Micron과 AMD가 17%대 하락하고 원·달러 고시환율이 올랐습니다. 전일 급락의 반영분을 구분하며 메모리주 저점과 외국인 수급을 살핍니다.'
paragraphs=[
('','미국 반도체주가 다시 크게 밀렸습니다. 한국 증시는 전날 이미 5% 넘게 하락했지만, 그 뒤 미국 정규장에서 매도가 더 거세졌고 원화도 약해졌습니다. 오늘 코스피는 낙폭만 보고 반등을 기대하기보다 삼성전자·SK하이닉스가 추가 매물을 받아낼 수 있는지부터 살펴야 합니다.'),
('미국 매도는 반도체 전반으로 번졌다','5일 미국 정규장에서 QQQ는 6.49%, TQQQ는 18.92%, SMH는 11.21% 하락했습니다. Nvidia는 9.26%, AMD는 17.26%, Micron은 17.46%, Broadcom은 10.43% 떨어졌습니다. QQQ는 일중 저가에서 끝났고 AMD와 Micron도 저가 부근으로 밀렸습니다. 장중 반등 시도가 종가까지 매물을 이기지 못한 모습입니다.'),
('','SOXX는 3대 1 분할을 반영한 정규장 기준 12.15% 하락했습니다. 주식 수 증가로 낮아진 주당 가격까지 손실로 계산하면 실제 하락폭을 크게 부풀리게 됩니다.'),
('','미국 중간선거 뒤 AI 데이터센터 건설 규제가 강화될 수 있다는 우려가 관련주 가격에 반영되고 있습니다. 이는 향후 투자 속도에 대한 시장의 판단입니다. 모든 기업의 설비투자가 취소됐거나 메모리 주문이 일제히 끊겼다는 확정 사실과는 구분해야 합니다.'),
('스마트폰 부진과 AI 수요를 나눠 봐야 한다','Qualcomm 공시에서 4분기 핸드셋 매출은 51억3,700만달러로 전년보다 26% 줄었습니다. 반면 회사는 2027회계연도 데이터센터 매출 목표 50억달러를 유지했습니다. 소비자 기기 부진과 데이터센터 사업 확대가 공존합니다. 이 실적은 5일 한국장 개장 전에 공개됐으므로 오늘 새로운 실적 충격으로 다시 더하지 않습니다. 이후 미국장에서 확대된 업종 매도가 오늘의 추가 부담입니다.'),
('메모리 현물은 내렸지만 장기 수요 전망은 유지됐다','5일 대만시간 18:10 DRAM 현물에서 DDR5 16Gb 평균은 60.667달러로 1.09%, DDR4 16Gb는 81.679달러로 0.30% 내렸습니다. 범용 현물가격 약세는 단기 재고와 가격 협상에 부담입니다. 다만 HBM·서버 DRAM·eSSD 계약가격과 같은 지표는 아닙니다.'),
('','TrendForce는 같은 날 2027년 세계 AI 서버 출하량이 36% 증가할 것으로 전망했습니다. 장기 수요 기대가 남아 있어도 자금조달 비용과 정책 변화가 투자 집행 시점을 늦추면 주가는 먼저 조정받을 수 있습니다. 오늘은 실수요 전망과 주식 매도를 한 방향으로 단순화하지 않는 편이 타당합니다. NAND·RDIMM의 공개 가격표는 기준일이 더 오래돼 당일 변화 판단에는 쓰기 어렵습니다.'),
('환율 상승이 금리 하락의 효과를 누른다','원·달러 하나은행 고시환율은 6일 07:30:05 기준 1,357.00원으로 전회 대비 14.50원 높았습니다. 서울 현물환의 개장 체결가와는 다릅니다. 미국 금리가 내려도 원화 약세와 반도체 매도가 겹치면 국내 성장주의 반등을 제약할 수 있습니다.'),
('','FRED 최신 금리차는 5일 기준 10년-2년 0.38%포인트, 10년-3개월 0.67%포인트입니다. 개별 만기 수익률은 4일 기준 3개월 4.21%, 2년 4.58%, 10년 4.90%입니다. 금리차와 개별 금리의 관측일이 다릅니다. 10년-2년 차 확대만으로 경기 낙관을 뜻한다고 볼 수 없고, 단기물의 하락 속도와 안전자산 수요를 함께 봐야 합니다.'),
('전일 급락을 오늘 한 번 더 빼지는 않는다','전일 코스피는 시가 5,580.09, 고가 5,586.46, 저가 5,336.88을 거쳐 5,383.80으로 5.28% 하락했습니다. KODEX 레버리지는 11.35% 내린 62,500원이며 저가는 61,500원이었습니다. 정책 우려와 기존 실적 부담은 이 가격에 이미 일부 반영됐습니다. 미국 ETF 하락률을 오늘 한국장 하락률로 그대로 옮기지 않는 이유입니다.'),
('','국내 외국인 현물과 선물, 프로그램이 함께 돌아서는지가 반등의 지속성을 가릅니다. 개장 전 수급표의 0은 오늘 거래 결과가 아닙니다. 메모리주만 반등하고 하락 종목이 계속 늘면 시장 전체의 회복으로 판단하기 이릅니다. 전일 전망은 기본 범위를 벗어나 약세 종가 범위에서 끝났습니다. 개별 수급 조건과 발행 후 경로의 적중 여부는 별도 확인이 필요합니다.'),
('오늘의 범위와 대응','기본 종가 범위는 5,050~5,350, 확률은 45%로 둡니다. 개장 매물을 소화하고 환율 상승이 진정되며 메모리주가 저점을 높이는 경우입니다. 외국인·프로그램 동반 순매수와 함께 5,350을 넘으면 강세 범위 5,350 초과~5,550(15%)을 봅니다. 5,050 아래에서 외국인·프로그램 매도가 이어지면 약세 범위 4,800~5,050 미만(40%)입니다. 경계값은 기본 범위에 배정하며 각 범위를 이탈하면 해당 시나리오는 무효입니다. 장중 예상 저가·고가 포락은 4,700~5,650으로 종가 범위와 구분합니다.'),
('','공격 5·관망 30·방어 65로 방어 비중을 높입니다. KODEX는 전일 저가 61,500원, 종가 62,500원, 시가 67,995원을 기준선으로 봅니다. 아래로 갭이 생기면 61,500원은 지지 확인선에서 회복 여부를 볼 선으로 바뀝니다. 반등 때는 가격 회복과 거래량, 외국인·프로그램 동행을 함께 봅니다. 큰 낙폭 자체를 추가매수 근거로 삼지 않습니다.'),
('오늘 밤 고용지표까지 남았다','미국 10월 고용보고서는 오늘 22:30 KST, 미국 동부시간 08:30에 나옵니다. 고용 둔화는 금리 부담을 낮출 수 있지만 경기 우려도 키웁니다. 다음 주요 일정은 10일 22:30 KST 미국 CPI입니다. 장중 판단은 09:30 첫 수급, 10:30 저점 유지, 14:00 이후 수급 가속 여부 순서로 다시 점검합니다.')]
body=''
for h,t in paragraphs:
 if h: body+='<h2>'+h+'</h2>\n'
 body+='<p>'+t+'</p>\n'
body+='<h2>발행 기준 시세</h2>\n{{fastTable}}\n<h2>미국 정규장 OHLC</h2>'+htable(uh,us)+'<h2>미국 시간외</h2><p>시간외 수치는 정규장 종가 대비이며 정규장 등락률과 합산하지 않습니다.</p>'+htable(ah,after)
body+='<h2>미국 금리차</h2>'+''.join(f'<figure><img src="../charts/us_yield_spreads_{k}_{D}.png" alt="미국 금리차 {k}" loading="lazy"></figure>' for k in ['long_term','90d'])
body+='<h2>출처</h2><ul>'+''.join(f'<li><a href="{u}">{s}</a></li>' for s,u in sources)+'</ul>'
write(P/'article-body.html',body)
report=f'# {D} KOSPI·KODEX 일일 리서치\n작성 {{{{issuedAt}}}} / 데이터 최종 확인 {{{{cutoff}}}} / 한국 {{{{marketLabel}}}}\n\n'
report+='\n\n'.join(('## '+h+'\n' if h else '')+t for h,t in paragraphs)
report+='\n\n## 한국시장 최종 시세\n{{fastTable}}\n\n## 미국 11월 5일 정규장\n'+mdtable(uh,us)+'\n\n## 시간외\n'+mdtable(ah,after)+'\n\n## 출처와 확인 시각\n'+at+' KST 취재·집필. 시세 원문 조회 08:01~08:03 KST, 최종 국내/선물 조회는 발행 기준 표 시각.\n'+'\n'.join(f'- [{s}]({u})' for s,u in sources)+'\n'
write(P/'report-template.md',report)
notes=f'''# {D} 취재 노트
시작 08:00 KST, 조사·집필 입력 완료 {at}. 정규장 종가와 시간외·당일 고시환율 분리.

## 후보 순위 및 전달경로
1. 미국 AI/반도체 광범위 매도: QQQ -6.49%, SMH -11.21%, MU -17.46%, AMD -17.26%. 국내 메모리 가중치와 외국인 위험 축소. 최상위.
2. 환율: 07:30 고시1357원(+14.5). 현물환 개장 체결가 아님. 외국인 수급 및 수입 비용 경로. 최상위.
3. DRAM 11/5 18:10 GMT+8 DDR5 60.667(-1.09%), DDR4 81.679(-0.30%). HBM계약수요와 분리. 상위.
4. Qualcomm 공시: 핸드셋-26%, 데이터센터FY27목표50억달러. 11/5한국장 이전발표. 새충격중복제외.
5. TrendForce AI서버2027출하+36% 전망. 장기수요반론이며 확정주문아님.
6. 금리/유가: FRED11/5스프레드0.38/0.67, 만기11/4금리4.21/4.58/4.90. 유가일봉OHLC역전 발견, 원유수치는 최종 선물원천시각 표만 사용. Reuters유가상승 방향 보조.
7. 고용11/6·CPI11/10 08:30ET=22:30KST BLS공식확인. 오늘한국종가뒤사건.
8. 강제청산/증자/블록딜·규제 확정·공급계약 탐색: 특정청산이나새CAPEX취소확정근거없음. 단정제외. 빅테크당일CAPEX/현금흐름신규원문수치 미확인.

## 원천 불일치 처리
KOSPI price API 11/4까지 지연. basic/integration 전일5383.80, 네이버 chart API와 fchart 11/5 OHLC5580.09/5586.46/5336.88/5383.80 대조. 마감보도/Investing도 일치. 공통수집기에history추가·발행기검증대체. 원문보존.
SOXX 11/5 3:1분할 BMV공지. 분할전일종가450.41과131.90단순비교금지. meta regularMarketChangePercent -12.14663사용, 분할조정계산과일치. 다른시세사이트134.61은차이기록,채택안함.
NAND10/26·RDIMM10/26·계약표9/30·PCSSD8/5 지연. 오늘값대입안함. 국내수급0은개장전초기화. 전일최종수급/선물/프로그램/폭 미확인.
SEC/BLS urllib403은web공식원문대체. html원문 재수집차단과내용확인분리. 전일발행후분봉경로미확보.

## 판단
미국하락을한국에기계적이식하지않음. 전일기본실패·약세종가범위. 오늘기본5050~5350(45%),강세5350초과~5550(15%),약세4800~5050미만(40%).경로4700~5650(90%).대응5/30/65. 조건부 추론이며수급조건은개장후검증.
집필→구조퇴고→humanize-korean윤문완료, 수치고정. 신규imagegen썸네일:밝은광장칩·하강계단·안전난간. 원본보존,1200x630패키징.
'''+ '\n'.join(f'- [{s}]({u})' for s,u in sources)
write(R/f'research/notes/{D}.md',notes)
# 전일 확정값과 판정은 신규 파일로만 보존한다.
chart=raw('naver-history');kr=next(x for x in chart['priceInfos'] if x['localDate']=='20261105');le=next(x for x in ev('122630')['data'] if x['localTradedAt']==PREV)
reason='장전 초기화 응답으로 전일 최종 수급·프로그램·시장 폭 묶음 및 발행 후 분봉 경로를 확보하지 못함'
evidence={'sourceStatus':'unavailable','source':ev('KOSPI-integration')['url'],'asOf':PREV+'T15:30:00+09:00','fetchedAt':at,'missingReason':reason,'rawHash':ev('KOSPI-integration')['rawHash']}
a={'schemaVersion':1,'sessionDate':PREV,'bizdate':'20261105','fetchedAt':at,'marketStatus':'CLOSE','closeSnapshotMissingReason':reason,'flowTrajectoryMissingEvidence':evidence}
for key,v,src in [('kospi',kr,load(P/'naver-history.raw.json')),('kodex',le,ev('122630'))]:
 a[key]={k:n(v[vk]) for k,vk in [('open','openPrice'),('high','highPrice'),('low','lowPrice'),('close','closePrice')]};a[key].update(asOf=PREV+'T15:30:00+09:00',source=src['url'],rawHash=src['rawHash'])
 if key=='kodex':a[key]['volume']=v['accumulatedTradingVolume']
ap=R/f'research/evaluation/actuals/{PREV}.json'
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
m=runner.evaluation();m.validate_actual(a,ap)
if not ap.exists():dump(ap,a)
fp=next((R/'research/evaluation/forecasts').glob('2026-11-05-090050-same-close.json'));f=load(fp);fid=f['forecastId']
o={'schemaVersion':1,'forecastId':fid,'recordedAt':at,'actualRef':PREV,'realizedScenario':'bear','errorCodes':['cause_unverifiable'],'triggerResults':[{'id':c['id'],'status':'unavailable','reason':reason} for t in f['scenarioTriggers'].values() for c in t['conditions']],'driverAssessment':[{'id':d['id'],'status':'unverifiable'} for d in f['drivers']],'hypothesisTests':[],'postForecastPathStatus':'missing','postForecastPathMissingReason':reason,'postForecastPathMissingEvidence':{k:('incomplete' if k=='sourceStatus' else v) for k,v in evidence.items() if k!='missingReason'}}
op=R/f'research/evaluation/outcomes/{fid}.json';pf=m.validate_forecast(f,fp,R);pa=m.validate_actual(a,ap);m.validate_outcome(o,op,pf,pa)
if not op.exists():dump(op,o)
image=f'assets/images/articles/market-{D}-chip-protection-1200x630.png'
Image.open('C:/Users/madro/.codex/generated_images/01a1adf0-e9dc-72c2-8e03-1fa826b0a9af/exec-0261b623-5c59-47e6-9b22-8ad716da15bb.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5350,'high':5550,'probability':.15},'base':{'low':5050,'high':5350,'probability':.45},'bear':{'low':4800,'high':5050,'probability':.40}}
posture={'attack':5,'wait':30,'defense':65};triggers={}
for kind in scenarios:
 cs=[('floor','kospi_price','gte',5050),('cap','kospi_price','lte',5350)] if kind=='base' else [('price','kospi_price','gt' if kind=='bull' else 'lt',5350 if kind=='bull' else 5050),('foreign','foreign_cash','gt' if kind=='bull' else 'lt',0),('program','program_total','gt' if kind=='bull' else 'lt',0)]
 triggers[kind]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':kind+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':kind+'-'+i} for i,met,oper,v in cs]}
dash={'schemaVersion':1,'headline':title,'summary':summary,'markets':[{'id':k,'label':k,'symbol':s,'value':None,'changePercent':None,'open':None,'high':None,'low':None,'previousClose':None,'asOf':PREV+'T15:30:00+09:00','asOfLabel':'전일 종가 미확인','stateLabel':'미확인','flows':[]} for k,s in [('KOSPI','K'),('KOSDAQ','Q')]],'stance':dict(label='추가 매물 소화 우선',note='메모리주 저점과 외국인·프로그램 수급을 확인합니다.',**posture),'checkpoints':[],'changes':[{'label':'KOSPI 전일','before':'5,683.80','after':'5,383.80','meaning':'5.28% 하락. 기존 반영분과 밤사이 추가 매도 분리.'}],'factors':[{'label':k,'metric':v,'detail':'11월 5일 미국 정규장','tone':'warning'} for k,v in [('미국 반도체','SMH -11.21%'),('미국 메모리','Micron -17.46%')]],'flows':{'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'개장 전·전일 최종 묶음 미확인'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'},'memory':[{'label':'DDR5 16Gb','value':'$60.667','change':'11/5 -1.09%'},{'label':'DDR4 16Gb','value':'$81.679','change':'11/5 -0.30%'}],'events':[{'time':'11월 6일 22:30 KST','name':'미국 10월 고용보고서','path':'금리·경기·성장주'},{'time':'11월 10일 22:30 KST','name':'미국 10월 CPI','path':'물가·금리'}],'strategyLevels':[{'asset':'KOSPI','support':'5,050','pivot':'5,350','resistance':'5,550'},{'asset':'KODEX 레버리지','support':'61,500원','pivot':'62,500원','resistance':'67,995원'}],'checklist':[{'id':'open','label':'09:30 외국인·프로그램 첫 수급'},{'id':'memory','label':'10:30 메모리주 저점 유지'},{'id':'late','label':'14:00 이후 매도 가속 여부'}],'sources':[{'label':s,'href':u} for s,u in sources],'scenarios':[],'technical':{'note':'오늘 리서치의 고정 기준선입니다. 갭 하락시 전일 저가는 회복 확인선이 됩니다.','instruments':[]}}
conditions={'bull':['5,350 초과','외국인 현물 순매수','프로그램 순매수'],'base':['5,050 이상','5,350 이하','환율 안정과 메모리주 저점 관찰'],'bear':['5,050 미만','외국인 현물 순매도','프로그램 순매도']}
for k,v in scenarios.items():dash['scenarios'].append({'id':k,'label':{'bull':'강세 · 15%','base':'기본 · 45%','bear':'약세 · 40%'}[k],'range':{'bull':'KOSPI 5,350 초과~5,550','base':'KOSPI 5,050~5,350','bear':'KOSPI 4,800~5,050 미만'}[k],'summary':'추가 매물 소화와 수급 전환','conditions':conditions[k],'invalidation':{'bull':'5,350 재이탈','base':'5,050~5,350 이탈','bear':'5,050 회복'}[k]})
for k,label,unit,values in [('KOSPI','KOSPI','pt',[5050,5350,5550]),('KODEX','KODEX 레버리지','원',[61500,62500,67995])]:dash['technical']['instruments'].append({'id':k,'label':label,'unit':unit,'asOf':PREV+'T15:30:00+09:00','asOfLabel':'전일 종가','points':[],'levels':[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],values)],'interpretation':'갭과 외국인·프로그램 수급을 함께 확인합니다.'})
dump(P/'dashboard-input.json',dash)
state='# KOSPI·KODEX 리서치 상태\n- 최신 기준일 2026-11-06. 전일 KOSPI5383.80(-5.28%), KODEX62500(-11.35%).\n- 미국 SMH-11.21%, Micron-17.46%, 고시환율1357원. DRAM현물하락·장기AI수요전망 분리.\n- 기본5050~5350(45%),강세5350초과~5550(15%),약세4800~5050미만(40%),대응5/30/65.\n- 전일 기본실패·약세종가범위. 수급조건/발행후경로미확보로 적중 주장 안 함.\n- 다음11/6 22:30고용·11/10 22:30CPI. 전일평가 research/evaluation/outcomes/'+fid+'.json.'
files=['scripts/collect_market_evidence.py','scripts/publish_market_research.py','tests/test_market_previous_session.py','docs/현재작업중.md',image,f'research/notes/{D}.md',rel(ap),rel(op)]
files += [rel(x) for x in P.glob('*.raw.json')]+[rel(x) for x in E.glob('*.json')]+[rel(P/x) for x in ['prepare_inputs.py','article-body.html','report-template.md','dashboard-input.json','package.json']]
charts=[f'charts/us_yield_spreads_{k}_{D}.png' for k in ['long_term','90d']];files+=charts
package={'date':D,'previousSessionDate':PREV,'title':title,'summary':summary,'image':image,'imageAlt':'밝은 광장의 청록색 반도체와 붉은 하강 계단, 푸른 안전 난간','bodyPath':rel(P/'article-body.html'),'reportTemplate':rel(P/'report-template.md'),'dashboardPath':rel(P/'dashboard-input.json'),'notesPath':f'research/notes/{D}.md','scenarios':scenarios,'posture':posture,'pathEnvelope':{'low':4700,'high':5650,'coverage':.9},'marketRegime':'risk_off','scenarioTriggers':triggers,'drivers':[{'id':'semiconductor','rank':1,'claim':'미국 반도체 추가 매도와 국내 매물 부담','validationMetric':'미국 반도체·국내 반도체·KOSPI'},{'id':'fx','rank':2,'claim':'원화 약세와 외국인 위험 축소','validationMetric':'USD/KRW·외국인·프로그램'}],'stateText':state,'charts':charts,'files':files}
dump(P/'package.json',package)
s=load(P/'run-status.json');s.update(status='prepared');s['stages'].update(research=at,writing=at,image=at);s['artifacts'].update(notes=f'research/notes/{D}.md',image=image);dump(P/'run-status.json',s)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+f'\n## 2026-11-06 장전 리서치\n\n- 오늘 신규 원천·취재·공개 원고·대시보드·이미지·금리차 차트·전일 actual/outcome·package 준비.\n- scripts/collect_market_evidence.py와 scripts/publish_market_research.py: 지연된 KOSPI 일봉을 별도 네이버 차트로 대조하고 지수·OHLC·장전 기준값 일치 때만 사용. 원문과 해시 보존. tests/test_market_previous_session.py로 지연/불일치/OHLC 검증.\n- 최종 조회와 봉인·배포는 공통 발행기 실행. SOXX 3:1분할 반영, 전일 한국장 반영분 중복 제외.\n')
print('prepared',at,'previous actual/outcome validated')
