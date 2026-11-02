import datetime, html, json, re
from pathlib import Path

R = Path(__file__).resolve().parents[3]
P = Path(__file__).parent
DATE = '2026-11-02'
OLD = '2026-10-30'
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE = '미국 반도체 급락 뒤 코스피 하락 출발…5,600선 지지 시험'
SUMMARY = '미국 반도체주가 크게 내린 뒤 코스피도 하락 출발했습니다. 국내에 앞서 반영된 충격을 구분하며 5,600선 지지와 매수 복귀를 살펴봅니다.'
IMAGE = 'market-2026-11-02-semiconductor-open-1200x630.png'
ALT = '밝은 반도체 웨이퍼와 서울 금융가를 비추는 아침 햇살'
URL = f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p): return (R / p).read_text(encoding='utf-8-sig')
def write(p,s): (R / p).write_text(s, encoding='utf-8', newline='\n')
def dump(p,v): write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k): return json.loads((P / (k+'.json')).read_text(encoding='utf-8'))
def num(x): return float(str(x).replace(',',''))
K0=ev('KOSPI')['data'][0]; L0=ev('122630')['data'][0]
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
sources=[('Intel 실적','https://www.intc.com/filings-reports/all-sec-filings/content/0000050863-26-000188/q326earningsrelease.htm'),('Intel 공시','https://www.intc.com/filings-reports/all-sec-filings/content/0000050863-26-000191/0000050863-26-000191.pdf'),('미국 고용비용지수','https://www.bls.gov/news.release/eci.htm'),('TrendForce DRAM','https://www.trendforce.com/research/download/RP261030HH'),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 지수','https://m.stock.naver.com/domestic/index/KOSPI'),('미국 고용 일정','https://www.bls.gov/schedule/news_release/empsit.htm')]
body='''<p>미국 반도체주가 크게 내린 뒤 코스피도 하락 출발했습니다. Intel의 전망 부진이 국내 시장에 먼저 반영된 만큼 미국장의 낙폭을 새로운 충격으로 전부 더하기보다, 5,600선 부근에서 반도체 매도와 매수의 균형이 어떻게 바뀌는지 살펴야 합니다.</p>
<h2>반도체 매도와 이미 반영된 충격</h2><p>10월 30일 미국 정규장에서 SOXX는 8.24%, SMH는 6.98% 하락했습니다. Nvidia는 4.22%, AMD는 10.88%, Micron은 5.30%, Broadcom은 5.48% 내렸습니다. 같은 날 한국장은 미국 정규장에 앞서 Intel의 실적 전망을 소화하며 3.48% 하락했습니다. 미국 종가의 하락을 모두 오늘 새로 발생한 충격으로 계산할 수 없는 이유입니다.</p>
<p>Intel은 4분기 매출을 150억~160억달러, 조정 주당순이익을 0.25달러로 전망했습니다. 이스라엘 Kiryat Gat 공장의 사고와 가동 중단도 공시했습니다. 반도체 업종 전체의 주가 약세와 개별 공장 사고의 생산 영향은 구분해 봐야 합니다. <a href="https://www.intc.com/filings-reports/all-sec-filings/content/0000050863-26-000188/q326earningsrelease.htm">Intel 실적</a> · <a href="https://www.intc.com/filings-reports/all-sec-filings/content/0000050863-26-000191/0000050863-26-000191.pdf">공시</a></p>
<h2>소비자 메모리와 AI 수요의 간격</h2><p>TrendForce에 따르면 소비자 DRAM 공급은 빠듯하지만 높은 가격과 연말 구매 관망으로 계약가격 상승 폭이 줄고 현물 가격은 고점에서 물러났습니다. 소비자용 메모리의 현물 약세만으로 HBM 계약가격이나 서버 수요 전체를 판단하기는 어렵습니다. 메모리의 실물 수급과 주식시장의 투자 심리도 따로 볼 필요가 있습니다. <a href="https://www.trendforce.com/research/download/RP261030HH">TrendForce 분석</a></p>
<h2>5,600선 지지와 반등의 조건</h2><p>기본 종가 범위는 5,550~5,750, 확률 50%입니다. 5,750을 넘고 외국인과 프로그램 순매수가 동행하면 5,750 초과~5,900의 강세 시나리오 20%를 봅니다. 5,550 아래에서 외국인과 프로그램 매도가 이어지면 5,350~5,550 미만의 약세 시나리오 30%로 기웁니다. 해당 경계선을 다시 넘으면 각 시나리오의 판단을 접습니다.</p><p>KODEX 레버리지는 69,000원을 지지, 70,500원을 반등 기준, 전 거래일 종가인 72,545원을 저항으로 봅니다. 공격 10·관망 45·방어 45로 두고 지수 회복과 반도체 매수세가 함께 나타나는지 확인합니다.</p>
<p>미국 3분기 고용비용지수는 전분기보다 0.8%, 전년보다 3.4% 올랐습니다. 다음 고용보고서는 11월 6일 오후 10시 30분 한국시간 발표 예정입니다. 임금과 고용 흐름은 금리 기대를 통해 성장주 평가에 영향을 줍니다. <a href="https://www.bls.gov/news.release/eci.htm">고용비용지수</a> · <a href="https://www.bls.gov/schedule/news_release/empsit.htm">고용보고서 일정</a></p>'''
write('research/evidence/'+DATE+'/body.html',body)
report=f'# {DATE} KOSPI·KODEX 장중 리서치\n작성 PREPARED / 데이터 최종 확인 PREPARED\n\n'+read('research/notes/'+DATE+'.md')+'\n## 미국 10월 30일 정규장\n|종목|종가 USD|등락|\n|---|---:|---:|\n'+ustable+'\n## 발행 직전 조회\nFAST_TABLE\n## 조건부 전망\n기본 5550~5750(50%), 강세 5750 초과~5900(20%), 약세 5350~5550 미만(30%). 강세: 지수>5750 AND 외국인>0 AND 프로그램>0. 기본: 5550<=지수<=5750 AND 외국인>=-8000억원. 약세: 지수<5550 AND 외국인<0 AND 프로그램<0. 관측 15:20, 범위 경계 재진입시 무효. 장중 경로 90% 포락 5150~6100. 공격10 관망45 방어45. KODEX 69000/70500/72545원. 수급 확정값 미확인.\n'+f'![90일](../charts/us_yield_spreads_90d_{DATE}.png)\n![2년](../charts/us_yield_spreads_long_term_{DATE}.png)\n'
write('reports/'+DATE+'.md',report)
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index('s=prior;s.update')]
tail=tail.replace("oldimage='market-2026-10-19-memory-credit-1200x630.png'","oldimage='market-2026-10-30-cloud-capex-1200x630.png'")
for a,b in [('2026.10.20','2026.11.02'),('2026.10.19','2026.10.30'),('2026-10-19','2026-10-30'),('10월 19일','10월 30일'),('장전 브리핑','장중 브리핑'),('장전 시세','장중 시세')]:tail=tail.replace(a,b)
aftertable='';exec(tail)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'},sourceLabel='미국 10월 30일 정규장 · 국내 11월 2일 장중',marketState='한국 장중')
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='미확인',stateLabel='장중',flows=[])
 if x['id']=='KOSPI':x.update(value=num(K0['closePrice']),changePercent=num(K0['fluctuationsRatio']),open=num(K0['openPrice']),high=num(K0['highPrice']),low=num(K0['lowPrice']),previousClose=5730.74,asOf=ev('KOSPI-basic')['data']['localTradedAt'],asOfLabel='11월 2일 장중')
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'미확인'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'반도체 매도와 지지력 확인','attack':10,'wait':45,'defense':45,'note':'5,600선 부근에서 반도체 매수 복귀를 살펴봅니다.'}
s['changes']=[{'label':'KOSPI','before':'5,937.66','after':'5,730.74','meaning':'10월 30일 3.48% 하락했습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX -8.24%','detail':'10월 30일 정규장','tone':'warning'},{'label':'미국 고용비용','metric':'3분기 +0.8%','detail':'전분기 대비','tone':'neutral'}]
s['memory']=[{'label':'소비자 DRAM','value':'계약가 상승폭 축소','change':'10월 30일 TrendForce'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,550','pivot':'5,600','resistance':'5,750'},{'asset':'KODEX 레버리지','support':'69,000원','pivot':'70,500원','resistance':'72,545원'}]
for x in s['scenarios']:
 k=x['id'];x.update(label={'bull':'강세 · 20%','base':'기본 · 50%','bear':'약세 · 30%'}[k],range={'bull':'KOSPI 5,750 초과~5,900','base':'KOSPI 5,550~5,750','bear':'KOSPI 5,350~5,550 미만'}[k],summary='반도체 매도와 수급 동행 확인',conditions={'bull':['5,750 초과','외국인 순매수','프로그램 순매수'],'base':['5,550 이상','5,750 이하','외국인 순매도 8천억원 이하'],'bear':['5,550 미만','외국인 순매도','프로그램 순매도']}[k],invalidation={'bull':'5,750 재이탈','base':'범위 이탈','bear':'5,550 회복'}[k])
s['events']=[{'time':'11월 6일 22:30 KST','name':'미국 고용보고서','path':'노동시장과 금리'}];s['checkpoints']=[];s['checklist']=[{'id':'support','label':'5,550선 지지와 5,600선 회복'},{'id':'flow','label':'외국인·프로그램 수급 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K0 if x['id']=='KOSPI' else L0;levels=[5550,5600,5750] if x['id']=='KOSPI' else [69000,70500,72545];x.update(asOf=NOW,asOfLabel='11월 2일 장중',points=[{'label':a,'value':num(v[b])} for a,b in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('현재','closePrice')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation='반도체 수급과 주요 가격대의 지지력을 확인합니다.')
s['technical']['note']='11월 2일 장중 가격과 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s)
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장중.\n- 전일 KOSPI 5730.74(-3.48%), KODEX 72545원(-7.64%).\n- Intel 전망·미국 반도체 하락, 한국장 선반영분 중복 제외.\n- 미국 10월 고용보고서 11/6 22:30 KST.\n- 기본 5550~5750(50%), 강세 5750초과~5900(20%), 약세 5350~5550미만(30%), 대응 10/45/45.\n- reports/{DATE}.md, research/notes/{DATE}.md.\n')
print('prepared',NOW)
