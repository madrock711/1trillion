import datetime,json,re,base64,html
from pathlib import Path
from PIL import Image
R=Path.cwd(); P=R/'research/evidence/2026-11-04';DATE='2026-11-04';OLD='2026-11-03'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def num(v):return float(str(v).replace(',',''))
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='AMD 실적과 미국 반도체 반등…코스피는 5,800선 안착 시험'
SUMMARY='AMD의 데이터센터 성장과 미국 반도체 반등에 코스피가 상승 출발했습니다. 5,800선 지지와 외국인·프로그램 수급이 반등의 지속성을 가릅니다.'
IMAGE='market-2026-11-04-earnings-springboard-1200x630.png';ALT='밝은 아침 산호색 도약대에서 흰 플랫폼을 향해 떠오르는 청록색 구';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
sources=[('AMD 실적','https://newsroom.amd.com/news/amd-reports-third-quarter-2026-earnings/'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('BLS 일정','https://www.bls.gov/schedule/2026/11_sched.htm'),('금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
aftertable=''
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(json.loads((P/f'after-{k}.raw.json').read_text())['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];v=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']];t,c=v[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat();aftertable+=f'|{k}|{c:.2f}|{(c/d["meta"]["regularMarketPrice"]-1)*100:+.2f}%|{at}|\n'
notes='# 2026-11-04 취재 노트\n최초 시작08:01:44, 조사 초기 미완료 종료 후09:11 재개. 장전으로 소급하지 않고 장중판 발행.\n상위: 미국반도체반등(SOXX+2.50), AMD 매출133.77억·DC85억·4Q170억±3%, 국내 갭상승. 반론: 단기 반등과 신규 국내계약은 별개.\n후보: Apple 수익성 우려, JOLTS, 중간선거, AI 자금조달 위험, 신규 공급계약·규제·청산. JOLTS 원문 수치 미확정·선거결과 미확정·신규 청산/계약 1차근거 부족으로 확정 수치 제외. 기존 Intel 충격 중복 계산 제외.\n메모리11/3 DDR5 61.50·DDR4 82.719 모두보합. HBM·RDIMM·NAND·eSSD 신규계약단가 미확인. 개별금리11/2·스프레드11/3 혼합차감금지.\n국내 전일KOSPI5648.79(-3.59) OHLC5715.19/5735.92/5615.80/5648.79; KODEX70095(-7.59) OHLC71705/72460/69215/70095·21511946주. 전일기본5700~5900 실패·약세종가범위 포함. 15:20 수급앵커·발행후경로 미검증. 투자주체별/선물/프로그램 확정묶음 미확인으로 금액공개 제외.\n신규썸네일: 밝은도약대와구체. 집필→퇴고→사실고정윤문.\n'
body='<p>미국 반도체주의 반등에 코스피도 상승 출발했습니다. 전날 3.59% 하락한 뒤 되돌림이 나온 만큼 오늘은 상승률보다 개장 이후의 가격 지지가 중요합니다. 5,800선 안착과 외국인·프로그램 매수의 동행이 반등의 지속성을 가를 조건입니다.</p>\n<h2>AMD 실적이 반도체 반등에 힘을 보탰다</h2><p>3일 미국 정규장에서 SOXX는 2.50%, SMH는 2.01% 올랐습니다. Nvidia는 2.29%, Micron은 2.58%, Broadcom은 3.07% 상승했습니다. AMD는 정규장에서 3.65% 오른 뒤 시간외에서도 상승했습니다. 전날 한국장 하락 이후의 미국 반등과 실적 발표는 새 재료입니다. 앞선 Intel 충격을 오늘 하락 요인으로 다시 더할 필요는 없습니다.</p>\n<p>AMD의 3분기 매출은 133억7,700만달러로 전년 대비 45% 늘었고 데이터센터 매출은 85억달러로 97% 증가했습니다. 회사는 4분기 매출을 170억달러, 오차 범위 ±3%로 제시했습니다. 서버와 AI 가속기 수요가 매출로 이어지고 있다는 점은 국내 HBM·서버 메모리 수요에도 우호적입니다. 다만 이 실적이 삼성전자나 SK하이닉스의 신규 공급계약 또는 이익률을 확정하지는 않습니다. <a href="https://newsroom.amd.com/news/amd-reports-third-quarter-2026-earnings/">AMD 실적</a> · <a href="https://www.sec.gov/Archives/edgar/data/2488/000000248826000188/amdq32026earningsslidesf.htm">공시 자료</a></p>\n<h2>메모리 수요와 주식 매수는 따로 확인한다</h2><p>3일 TrendForce 현물 세션에서 DDR5 16Gb 평균은 61.50달러, DDR4 16Gb는 82.719달러로 모두 보합이었습니다. 이 현물가격만으로 HBM과 기업용 SSD의 계약 수요를 판단할 수는 없습니다. 미국 메모리주 반등은 투자심리 회복의 단서이며 국내 반도체의 수급 회복은 별도로 확인해야 합니다. <a href="https://www.trendforce.com/price/dram/dram_spot">DRAM 현물가격</a></p>\n<h2>5,800선 위에서 반등을 유지할 수 있을까</h2><p>기본 종가 범위는 5,700~5,900으로 확률 50%를 둡니다. 5,900을 넘고 외국인과 프로그램이 함께 순매수하면 5,900 초과~6,050의 강세 시나리오 25%에 무게가 실립니다. 5,700 아래에서 두 수급이 순매도를 이어가면 5,450~5,700 미만의 약세 시나리오 25%를 봅니다. 각 경계선을 반대로 넘으면 해당 판단을 접습니다.</p><p>KODEX 레버리지는 73,565원을 당일 첫 지지, 74,000원을 반등 유지 기준, 75,090원을 첫 저항으로 봅니다. 기준선은 오전 초반 관측 범위이며 이후 시세에 따라 저절로 바뀌는 목표가가 아닙니다. 공격 20·관망 50·방어 30으로 두고 상승 출발 뒤 저점을 높이는지 살펴봅니다.</p>\n<h2>금리와 미국 고용 일정도 남아 있다</h2><p>3일 미국 10년물과 2년물 금리차는 0.34%포인트, 10년물과 3개월물 차이는 0.74%포인트입니다. 개별 금리는 2일 자료에서 3개월물 4.21%, 2년물 4.59%, 10년물 4.91%였습니다. 서로 기준일이 다릅니다. 장단기 금리차가 벌어졌다는 이유만으로 성장주의 할인율 부담이 줄었다고 보기는 어렵습니다. 미국 고용보고서는 6일 오후 10시 30분 한국시간에 예정돼 있습니다. 중간선거 결과와 정책 변화도 확정 발표를 따라 확인할 변수입니다. <a href="https://fred.stlouisfed.org/series/T10Y2Y">FRED</a> · <a href="https://www.bls.gov/schedule/2026/11_sched.htm">BLS 일정</a></p>'
write('research/notes/'+DATE+'.md',notes)
write('research/evidence/'+DATE+'/body.html',body)
report=f'# {DATE} KOSPI·KODEX 장중 리서치\n작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장중\n\n'+notes+'\n## 미국 정규장 11/3\n|종목|USD|등락|\n|---|---:|---:|\n'+ustable+'\n## 미국 시간외\n|종목|USD|종가대비|원천시각|\n|---|---:|---:|---|\n'+aftertable+'\n## 최종 조회\nFAST_TABLE\n## 조건부 전망\n기본5700~5900(50),강세5900초과~6050(25),약세5450~5700미만(25). 공격20 관망50 방어30. 장중90%포락5450~6200. 15:20 지수와 외국인/프로그램 동행 조건. 반대경계 돌파시 무효.\n'+re.sub('<[^>]+>',' ',body)
write('reports/'+DATE+'.md',report)
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index('s=prior;s.update')];tail=tail.replace('market-2026-10-19-memory-credit-1200x630.png','market-2026-11-03-chip-oil-balance-1200x630.png')
for a,b in [('2026.10.20','2026.11.04'),('2026.10.19','2026.11.03'),('2026-10-19','2026-11-03'),('10월 19일','11월 3일'),('10월 20일','11월 3일')]:tail=tail.replace(a,b)
tail=tail.replace('market-2026-11-03-chip-oil-balance-1200x630.png','market-2026-11-03-chip-oil-balance-1200x630.png').replace('장전 브리핑','장중 브리핑').replace('장전 시세','장중 시세');exec(tail)
s=prior;s.update(headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'},sourceLabel='미국 11월 3일 정규장 · 한국 11월 4일 장중',marketState='한국 장전')
K=ev('KOSPI')['data'][0];L=ev('122630')['data'][0]
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='11월 3일 정규장 종가',stateLabel='종가',flows=[])
 if x['id']=='KOSPI':x.update(value=num(K['closePrice']),changePercent=num(K['fluctuationsRatio']),open=num(K['openPrice']),high=num(K['highPrice']),low=num(K['lowPrice']),previousClose=5859.08)
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'확정 묶음 미확인'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'실적 반등의 지속성','attack':20,'wait':50,'defense':30,'note':'AMD 실적과 반도체 반등 뒤 국내 수급을 확인합니다.'}
s['changes']=[{'label':'KOSPI','before':'5,730.74','after':'5,859.08','meaning':'11월 3일 2.24% 반등했습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX +2.50%','detail':'11월 3일 정규장','tone':'warning'},{'label':'AMD 매출','metric':'133.77억달러 · +45%','detail':'공식 4분기 실적','tone':'positive'}]
s['memory']=[{'label':'DDR5 16Gb','value':'$61.50','change':'11/3 보합'},{'label':'DDR4 16Gb','value':'$82.719','change':'11/3 보합'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,700','pivot':'5,859','resistance':'5,900'},{'asset':'KODEX 레버리지','support':'72,000원','pivot':'75,850원','resistance':'77,465원'}]
for x in s['scenarios']:
 k=x['id'];x.update(label={'bull':'강세 · 25%','base':'기본 · 50%','bear':'약세 · 25%'}[k],range={'bull':'KOSPI 5,900 초과~6,050','base':'KOSPI 5,700~5,900','bear':'KOSPI 5,450~5,700 미만'}[k],summary='반도체 가격과 수급의 동행',conditions={'bull':['5,900 초과','외국인 순매수','프로그램 순매수'],'base':['5,700 이상','5,900 이하'],'bear':['5,700 미만','외국인 순매도','프로그램 순매도']}[k],invalidation={'bull':'5,900 재이탈','base':'범위 이탈','bear':'5,700 회복'}[k])
s['events']=[{'time':'11월 6일 22:30 KST','name':'미국 고용보고서','path':'금리·성장주'}]
s['checkpoints']=[];s['checklist']=[{'id':'support','label':'5,700선 지지와 5,900선 회복'},{'id':'flow','label':'기관 매수 지속과 외국인·프로그램 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5700,5648.79,5900] if x['id']=='KOSPI' else [73565,74000,75090];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='11월 3일 종가',points=[{'label':a,'value':num(v[b])} for a,b in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation='전일 반등의 지지력과 반도체 수급을 살펴봅니다.')
s['technical']['note']='11월 3일 종가와 11월 4일 장중 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s)
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5648.79(+2.24%), KODEX70095원(+4.56%).\n- 미국 반도체 추가 매도·유가 하락·Apple 매출 성장. 이전 Intel 충격 중복 제외.\n- 기본5700~5900(50%), 강세5900초과~6050(20%), 약세5450~5700미만(30%), 대응10/45/45.\n- 직전 기본범위 실패·강세범위 종가, 수급조건 미검증.\n- 다음 JOLTS11/4 00:00, AMD11/4 07:00, 고용11/6 22:30 KST.\n- reports/{DATE}.md, research/notes/{DATE}.md.\n')
Image.open('C:/Users/madro/.codex/generated_images/01a1a3a5-4967-72d3-bde3-c431e3f305af/exec-d02576b3-3253-49bd-b3c3-c8c65fd08cea.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/'assets/images/articles'/IMAGE)
for fn in ['index.html','articles/index.html','articles/market.html']:
 p=R/fn;q=read(fn)
 def card(m):
  if f'market-{DATE}.html' in m[0]:return re.sub(r'2026\.11\.02|2026\.10\.\d\d','2026.11.04',m[0]).replace('11월 3일','11월 3일')
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 q=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,q,flags=re.S);write(fn,q)
q=read('sitemap.xml')
for path in ['','articles/','articles/market.html']:q=re.sub(r'(<loc>https://www\.hpmplab\.com/'+re.escape(path)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+DATE,q)
write('sitemap.xml',q)
print('prepared',NOW)
