import datetime,json,re,base64,html
from pathlib import Path
from PIL import Image
R=Path.cwd(); P=R/'research/evidence/2026-11-03';DATE='2026-11-03';OLD='2026-11-02'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def num(v):return float(str(v).replace(',',''))
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='미국 반도체는 더 내리고 유가는 급락…코스피 반등의 지지력 시험'
SUMMARY='미국 반도체주의 추가 하락과 유가 급락이 엇갈렸습니다. 전날 5,859선으로 반등한 코스피는 기관 매수의 지속과 반도체 지지력을 시험합니다.'
IMAGE='market-2026-11-03-chip-oil-balance-1200x630.png';ALT='밝은 균형대 위 반도체와 아래로 움직이는 황금빛 기름방울';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
sources=[('Apple 실적','https://www.apple.com/newsroom/2026/11/apple-reports-fourth-quarter-results/'),('AMD 일정','https://ir.amd.com/news-events'),('BLS 일정','https://www.bls.gov/schedule/2026/11_sched.htm'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('유가·협상','https://live.euronext.com/en/financial-news/oil-drops-6-iran-signals-openness-peace-talks'),('국내 종가','https://markets.hankyung.com/indices/kospi'),('금리차','https://fred.stlouisfed.org/series/T10Y2Y')]
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
aftertable=''
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(json.loads((P/f'after-{k}.raw.json').read_text())['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];v=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']];t,c=v[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat();aftertable+=f'|{k}|{c:.2f}|{(c/d["meta"]["regularMarketPrice"]-1)*100:+.2f}%|{at}|\n'
notes='''# 2026-11-03 취재 노트
실제 수집 시작 07:58 KST. 정규장 11/2 16:00 EST=11/3 06:00 KST. 시간외는 진행 중 최근 유효봉.
## 이슈 후보와 순위
1. 미국 반도체 추가 매도: 12점. SOXX-3.79%, AMD-7.52%, MU-5.78%. 한국 전일 반등 이후 미국 정규장 신규 약세. 다만 Intel 이전 충격 전체를 재합산하지 않음.
2. 유가 급락과 이란 협상: 11점. Reuters/Euronext 협상 보도, WTI 최근96.26달러. 협상 기대이며 평화·해협 개방 확정 아님. 5일 일봉 단순변화는 계약 롤오버 영향 가능하므로 공개 일간 변화율 제외.
3. Apple 실적: 10점. 회사 공식 매출1145억달러+12%, EPS2.10달러+14%, 관세환급 EPS0.05달러 포함. 국내 부품 수요와 AI 자금조달 우려 구분.
4. AMD 실적 예정: 9점. 공식11/3 14:00 PST=11/4 07:00 KST 콜.
5. 중간선거와 규제: 7점. 결과 미확정, 독립 수치 전망 제외.
6. 메모리 현물: 7점. TrendForce11/2 18:10 GMT+8 DDR5 61.50달러 보합, DDR4 82.719달러-0.09%. NAND 오래된10/26·계약가격은 오늘 값 제외. HBM·서버DRAM·eSSD 신규 계약단가 미확인.
7. 청산·증자·공급계약: 5점. OpenAI 조달·Anthropic 신용·Binance 보도 탐색, 최신 1차 확정 근거 부족으로 주도사건 제외. 펀드 청산으로 단정하지 않음.
8. 금리·고용: 8점. FRED11/2 스프레드10Y-2Y0.32%p·10Y-3M0.70%p. 개별금리 최신10/30 3M4.16·2Y4.56·10Y4.94%, 날짜 섞어 차감하지 않음. BLS JOLTS11/4 00:00 KST, 고용11/6 22:30.
## 전일과 검증 한계
KOSPI5859.08(+2.24%), OHLC5637.77/5910.83/5616.50/5859.08, KODEX75850(+4.56%) OHLC70395/77465/69410/75850·22138069주. 지수 fchart·price와 한국경제 종가 교차. 개별주 전일비/연속일봉 불일치로 삼성·SK 등락 재계산 제외. 투자자별 합계 불일치와 원천 간 차이로 금액 확정 묶음 보류, 0 아님.
직전 기본5550~5750 실패, 강세5750~5900 범위에 종가 포함. 장중5616.50~5910.83은 직전90%포락5150~6100 안. 정확15:20 수급·분봉 경로 부재로 조건/발행후 경로 평가 유보. candidate 가설 미사용.
## 중심 명제·이미지
새 반도체 매도는 부담, 유가 하락·Apple 실적은 완충. 전일 국내 기관 반등의 지속성이 핵심. 신규 밝은 아이보리 균형대·칩·기름방울, 경계와 여유, 이전 이미지 참조 없음.
'''
write('research/notes/'+DATE+'.md',notes+'\n'+'\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n')
body='''<p>반도체 매도는 이어졌지만 에너지 부담은 줄었습니다. 2일 미국 정규장에서 SOXX는 3.79%, SMH는 2.71% 하락했습니다. 전날 5,859.08로 반등한 코스피에는 추가 부담입니다. 유가 하락과 Apple의 매출 성장은 하단을 받칠 재료지만 반도체 매수세의 복귀까지 보장하지는 않습니다.</p>
<h2>전날 반등 뒤 새로 쌓인 반도체 매도</h2><p>AMD는 7.52%, Micron은 5.78% 내렸고 Nvidia와 Broadcom도 각각 1.26%, 1.18% 하락했습니다. 지난주 Intel 전망 부진과 미국장의 급락은 전날 한국장에 이미 전달됐습니다. 오늘은 그 충격을 다시 전부 더하기보다 한국장 마감 이후 이어진 추가 매도와 시간외 반응을 구분해야 합니다. <a href="https://finance.yahoo.com/quote/SOXX/">미국 시세</a></p>
<p>한국장은 2일 2.24% 상승하며 5,800선을 회복했습니다. 오늘도 반등을 지키려면 기관 매수와 반도체 가격 지지가 함께 이어져야 합니다. 미국 시간외에서는 주요 반도체주가 정규장 종가보다 소폭 높은 가격에 거래됐습니다. 아직 진행 중인 거래여서 정규장 하락을 되돌렸다고 판단하기는 이릅니다.</p>
<h2>유가 하락과 Apple 실적이 주는 완충</h2><p>이란과 카타르의 협상 소식에 유가가 크게 내렸습니다. 원유 수입 비용과 물가 부담이 줄어드는 방향은 한국 증시에 우호적입니다. 협상 기대가 가격을 움직인 단계인 만큼 합의와 해협 통항 정상화까지 확정된 것으로 볼 수는 없습니다. <a href="https://live.euronext.com/en/financial-news/oil-drops-6-iran-signals-openness-peace-talks">협상과 유가</a></p>
<p>Apple은 4분기 매출 1,145억달러로 전년 대비 12% 성장했고 희석 주당순이익은 2.10달러로 14% 늘었습니다. 주당순이익에는 관세 환급 효과 0.05달러가 포함됐습니다. 소비자 기기 수요에는 힘을 주는 실적이지만 AI 설비투자의 수익성과 자금조달 문제를 곧바로 해결하는 재료는 아닙니다. <a href="https://www.apple.com/newsroom/2026/11/apple-reports-fourth-quarter-results/">Apple 발표</a></p>
<h2>메모리 현물과 주가는 다른 속도로 움직인다</h2><p>TrendForce의 2일 현물 세션에서 DDR5 16Gb 평균은 61.50달러로 보합, DDR4 16Gb는 82.719달러로 0.09% 하락했습니다. 현물의 완만한 움직임과 Micron의 주가 급락 사이에는 간격이 있습니다. 소비자 메모리 현물가격만으로 HBM과 서버용 메모리의 계약 수요를 판단할 수 없으며, 주가에는 실적 기대와 투자비 부담이 함께 반영됩니다. <a href="https://www.trendforce.com/price/dram/dram_spot">DRAM 현물</a></p>
<h2>5,700선 방어와 5,900선 회복을 나눠 본다</h2><p>기본 종가 범위는 5,700~5,900, 확률은 50%입니다. 5,900을 넘고 외국인·프로그램 순매수가 함께 붙으면 5,900 초과~6,050의 강세 시나리오 20%를 봅니다. 5,700 아래에서 두 수급이 순매도를 이어가면 5,450~5,700 미만의 약세 시나리오 30%로 기웁니다. 각 경계선을 반대로 넘으면 해당 판단을 접습니다.</p><p>KODEX 레버리지는 72,000원을 1차 지지, 전일 종가 75,850원을 반등 기준, 전일 고가 77,465원을 저항으로 봅니다. 공격 10·관망 45·방어 45로 두고 유가의 완충 효과보다 반도체 매도가 강한지 살펴봅니다.</p>
<p>미국 금리차는 2일 기준 10년물과 2년물 사이 0.32%포인트, 10년물과 3개월물 사이 0.70%포인트입니다. 4일 0시에는 미국 구인·이직 보고서, 오전 7시에는 AMD 실적 설명회가 예정돼 있습니다. 6일 오후 10시 30분 고용보고서도 금리와 성장주 평가를 바꿀 변수입니다. 모두 한국시간입니다. <a href="https://fred.stlouisfed.org/series/T10Y2Y">FRED</a> · <a href="https://www.bls.gov/schedule/2026/11_sched.htm">BLS 일정</a> · <a href="https://ir.amd.com/news-events">AMD 일정</a></p>'''
write('research/evidence/'+DATE+'/body.html',body)
report=f'# {DATE} KOSPI·KODEX 장전 리서치\n작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전\n\n'+notes+'\n## 미국 11월 2일 정규장\n|종목|종가 USD|등락|\n|---|---:|---:|\n'+ustable+'\n## 미국 시간외 진행 중\n|종목|USD|종가 대비|원천 시각|\n|---|---:|---:|---|\n'+aftertable+'\n## 최종 조회\nFAST_TABLE\n## 조건부 전망\n기본5700~5900(50%), 강세5900초과~6050(20%), 약세5450~5700미만(30%). 공격10 관망45 방어45. 90%장중포락5250~6250. 강세 지수>5900 AND 외국인>0 AND 프로그램>0, 약세 지수<5700 AND 외국인<0 AND 프로그램<0. 기본5700<=지수<=5900. 관측15:20, 범위 역진입시 무효. KODEX72000/75850/77465원.\n'+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+f'\n![90일](../charts/us_yield_spreads_90d_{DATE}.png)\n![2년](../charts/us_yield_spreads_long_term_{DATE}.png)\n'
write('reports/'+DATE+'.md',report)
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index('s=prior;s.update')];tail=tail.replace('market-2026-10-19-memory-credit-1200x630.png','market-2026-11-02-semiconductor-open-1200x630.png')
for a,b in [('2026.10.20','2026.11.03'),('2026.10.19','2026.11.02'),('2026-10-19','2026-11-02'),('10월 19일','11월 2일'),('10월 20일','11월 3일')]:tail=tail.replace(a,b)
exec(tail)
s=prior;s.update(headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'},sourceLabel='미국 11월 2일 정규장 · 한국 11월 3일 장전',marketState='한국 장전')
K=ev('KOSPI')['data'][0];L=ev('122630')['data'][0]
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='11월 2일 정규장 종가',stateLabel='종가',flows=[])
 if x['id']=='KOSPI':x.update(value=num(K['closePrice']),changePercent=num(K['fluctuationsRatio']),open=num(K['openPrice']),high=num(K['highPrice']),low=num(K['lowPrice']),previousClose=5730.74)
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'확정 묶음 미확인'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'반등 지지력 시험','attack':10,'wait':45,'defense':45,'note':'미국 반도체 추가 매도와 유가 하락이 엇갈립니다.'}
s['changes']=[{'label':'KOSPI','before':'5,730.74','after':'5,859.08','meaning':'11월 2일 2.24% 반등했습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX -3.79%','detail':'11월 2일 정규장','tone':'warning'},{'label':'Apple 매출','metric':'1,145억달러 · +12%','detail':'공식 4분기 실적','tone':'positive'}]
s['memory']=[{'label':'DDR5 16Gb','value':'$61.50','change':'11/2 보합'},{'label':'DDR4 16Gb','value':'$82.719','change':'11/2 -0.09%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,700','pivot':'5,859','resistance':'5,900'},{'asset':'KODEX 레버리지','support':'72,000원','pivot':'75,850원','resistance':'77,465원'}]
for x in s['scenarios']:
 k=x['id'];x.update(label={'bull':'강세 · 20%','base':'기본 · 50%','bear':'약세 · 30%'}[k],range={'bull':'KOSPI 5,900 초과~6,050','base':'KOSPI 5,700~5,900','bear':'KOSPI 5,450~5,700 미만'}[k],summary='반도체 가격과 수급의 동행',conditions={'bull':['5,900 초과','외국인 순매수','프로그램 순매수'],'base':['5,700 이상','5,900 이하'],'bear':['5,700 미만','외국인 순매도','프로그램 순매도']}[k],invalidation={'bull':'5,900 재이탈','base':'범위 이탈','bear':'5,700 회복'}[k])
s['events']=[{'time':t,'name':n,'path':v} for t,n,v in [('11월 4일 00:00 KST','미국 JOLTS','노동시장·금리'),('11월 4일 07:00 KST','AMD 실적 설명회','AI·반도체 수요'),('11월 6일 22:30 KST','미국 고용보고서','금리와 성장주')]]
s['checkpoints']=[];s['checklist']=[{'id':'support','label':'5,700선 지지와 5,900선 회복'},{'id':'flow','label':'기관 매수 지속과 외국인·프로그램 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5700,5859.08,5900] if x['id']=='KOSPI' else [72000,75850,77465];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='11월 2일 종가',points=[{'label':a,'value':num(v[b])} for a,b in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation='전일 반등의 지지력과 반도체 수급을 살펴봅니다.')
s['technical']['note']='11월 2일 종가와 11월 3일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s)
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5859.08(+2.24%), KODEX75850원(+4.56%).\n- 미국 반도체 추가 매도·유가 하락·Apple 매출 성장. 이전 Intel 충격 중복 제외.\n- 기본5700~5900(50%), 강세5900초과~6050(20%), 약세5450~5700미만(30%), 대응10/45/45.\n- 직전 기본범위 실패·강세범위 종가, 수급조건 미검증.\n- 다음 JOLTS11/4 00:00, AMD11/4 07:00, 고용11/6 22:30 KST.\n- reports/{DATE}.md, research/notes/{DATE}.md.\n')
Image.open('C:/Users/madro/.codex/generated_images/01a19e7c-9c2e-7140-814d-29fd280d2e2a/exec-67890ea2-c9af-4b9c-9656-82b13b537ddb.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/'assets/images/articles'/IMAGE)
for fn in ['index.html','articles/index.html','articles/market.html']:
 p=R/fn;q=read(fn)
 def card(m):
  if f'market-{DATE}.html' in m[0]:return re.sub(r'2026\.11\.02|2026\.10\.\d\d','2026.11.03',m[0]).replace('11월 2일','11월 3일')
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 q=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,q,flags=re.S);write(fn,q)
q=read('sitemap.xml')
for path in ['','articles/','articles/market.html']:q=re.sub(r'(<loc>https://www\.hpmplab\.com/'+re.escape(path)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+DATE,q)
write('sitemap.xml',q)
print('prepared',NOW)
