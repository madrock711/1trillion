import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-30';OLD='2026-10-29';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='Amazon 성장에도 커진 AI 투자 부담…5,900선 지지 시험'
SUMMARY='Amazon의 클라우드 성장에도 현금 지출 부담이 커졌고 미국 반도체주가 하락했습니다. KOSPI는 5,900선 지지와 외국인 매수 복귀를 시험합니다.'
IMAGE='market-2026-10-30-cloud-capex-1200x630.png';ALT='밝은 아침 도시 위에서 민트색과 호박색 길로 갈라지는 흰 고가도로와 유리 구름';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261029\|([^"\s]+)',base64.b64decode(ev(k+'-fchart.raw')['raw'])).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==5937.66 and L['close']==78550
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(ev('after-'+k+'.raw')['raw']));d=d['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f"|{k}|{c:,.2f}|{(c/d['meta']['regularMarketPrice']-1)*100:+.2f}%|{at}|")
aftertable='\n'.join(after)
sources=[('연준 10월 결정','https://www.federalreserve.gov/newsevents/pressreleases/monetary20261029a.htm'),('Microsoft 실적','https://www.microsoft.com/en-us/Investor/earnings/FY-2027-Q1/press-release-webcast'),('Alphabet SEC 실적','https://www.sec.gov/Archives/edgar/data/1652044/000165204426000080/googexhibit991q32026.htm'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉',ev('KOSPI-fchart.raw')['url']),('BEA 일정','https://www.bea.gov/news/schedule')]
body='<p>KOSPI가 5,937.66으로 1.24% 하락한 뒤 미국 기술주도 밀렸습니다. Amazon은 클라우드 매출을 크게 늘렸지만 AI 인프라 지출이 현금흐름을 압박했습니다. 오늘은 성장률보다 그 성장을 뒷받침하는 비용과 국내 반도체 매수세가 관건입니다.</p><h2>클라우드 성장과 현금 지출의 간격</h2><p>Amazon의 3분기 AWS 매출은 460억달러로 전년보다 39.3% 증가했습니다. 최근 12개월 잉여현금흐름은 마이너스 424억달러였습니다. 연간 현금 설비투자 계획 2,200억달러는 유지됐습니다. 지출 확대를 이미 예상했어도 현금 회수까지의 시간이 길어지면 주가에는 부담이 됩니다. <a href="https://ir.aboutamazon.com/quarterly-results/default.aspx">Amazon 실적</a></p><h2>반도체 약세와 물가 부담</h2><p>미국 정규장에서 SOXX는 1.55%, SMH는 1.06% 내렸고 Micron은 4.98% 하락했습니다. 미국 3분기 GDP는 연율 3.4% 성장했고 9월 PCE 물가는 전월보다 0.5%, 전년보다 3.6% 올랐습니다. 견조한 성장과 높은 물가가 함께 나타나면서 금리 부담도 이어집니다. <a href="https://www.bea.gov/">BEA 발표</a></p><p>전일 한국장에 반영된 Alphabet 실적 우려와 미국장의 후행 반응을 다시 같은 크기의 충격으로 더할 수는 없습니다. 한국장 마감 뒤 나온 Amazon 실적과 시간외 반도체 약세가 오늘 새로 소화할 변수입니다. 메모리 현물 가격과 주식의 투자비·할인율 부담은 별도로 봐야 합니다.</p><h2>5,900선과 외국인 매수 복귀</h2><p>기본 종가 범위는 5,750~5,950(45%)입니다. 5,950선을 넘고 외국인·프로그램이 함께 순매수하면 5,950 초과~6,100(15%)을 봅니다. 5,750선 아래에서 매도가 동행하면 5,550~5,750 미만(40%)으로 낮춰 봅니다. 기본 범위를 이탈하면 해당 판단은 무효이며 다음 확인은 09:30, 10:00, 14:00입니다.</p><p>KODEX 레버리지는 75,200원을 첫 지지, 78,550원을 반등 기준, 80,595원을 저항으로 봅니다. 75,200원을 이탈한 뒤 회복하지 못하면 지지 판단을 접습니다. 공격 5·관망 40·방어 55로 두고, 환율 상승과 미국 선물 약세가 국내 반도체 매도로 이어지는지 확인합니다. 오늘 21:30 KST 미국 고용비용지수도 금리 기대에 영향을 줄 일정입니다.</p>'
write('research/evidence/'+DATE+'/body.html',body)
report=f"# {DATE} KOSPI·KODEX 장전 리서치\n작성 PREPARED / 데이터 최종 확인 PREPARED\n\n"+read('research/notes/'+DATE+'.md')+'\n## 미국 정규장\n|종목|종가 USD|등락|\n|---|---:|---:|\n'+ustable+'\n## 시간외\n'+aftertable+'\n## 발행 직전 조회\nFAST_TABLE\n## 조건부 전망\n기본5750~5950(45%), 강세5950초과~5950(15%), 약세5550~5750미만(40%). 강세: 지수>5950 AND 외국인>0 AND 프로그램>0. 기본: 지수>=5750 AND <=5950 AND 외국인>=-8000억원. 약세: 지수<5750 AND 외국인<0 AND 프로그램<0. 관측15:20, 범위재진입/이탈시무효. 다음09:30/10:00/14:00. 경로90%포락5350~6100. 대응5/40/55. KODEX75200/78550/80595. 수급확정묶음과앵커미확인.\n'+f'![90일](../charts/us_yield_spreads_90d_{DATE}.png)\n![2년](../charts/us_yield_spreads_long_term_{DATE}.png)\n'
write('reports/'+DATE+'.md',report)
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index('s=prior;s.update')]
tail=tail.replace("oldimage='market-2026-10-19-memory-credit-1200x630.png'","oldimage='market-2026-10-29-cloud-crossroads-1200x630.png'")
for a,b in [('2026.10.20','2026.10.30'),('2026.10.19','2026.10.29'),('2026-10-19','2026-10-29'),('10월 19일','10월 28일')]:tail=tail.replace(a,b)
exec(tail)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'},sourceLabel='미국10/28 정규장·국내10/28 종가·10/29 장전')
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=-1.24,open=K['open'],high=K['high'],low=K['low'],previousClose=6012.44,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월28일 정규장 종가')
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'최종 묶음 미확인'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'급등 뒤 지지력 확인','attack':5,'wait':40,'defense':55,'note':'클라우드 성장과 투자 부담이 엇갈린 가운데 6,000선 안착을 시험합니다.'}
s['changes']=[{'label':'KOSPI','before':'5,638.34','after':'6,012.44','meaning':'SK하이닉스 실적을 반영하며 -1.24% 상승했습니다.'}]
s['factors']=[{'label':'클라우드 수요','metric':'Azure +48%','detail':'Microsoft 10/28 실적','tone':'positive'},{'label':'투자 부담','metric':'Alphabet FCF -90.65억달러','detail':'10/28 분기 실적','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/28','value':'$61.333','change':'보합'},{'label':'DDR4 16Gb · 10/28','value':'$82.92','change':'+0.36%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,900','pivot':'6,000','resistance':'6,100'},{'asset':'KODEX 레버리지','support':'78,000원','pivot':'80,280원','resistance':'81,010원'}]
for x in s['scenarios']:
 k=x['id'];x.update(label={'bull':'강세 · 20%','base':'기본 · 50%','bear':'약세 · 30%'}[k],range={'bull':'KOSPI 6,100 초과~6,250','base':'KOSPI 5,900~6,100','bear':'KOSPI 5,700~5,900 미만'}[k],summary='급등 뒤 매수 지속성 확인',conditions={'bull':['6,100 초과','외국인 순매수','프로그램 순매수'],'base':['5,900 이상','6,100 이하','외국인 순매도 8천억원 이하'],'bear':['5,900 미만','외국인 순매도','프로그램 순매도']}[k],invalidation={'bull':'6,100 재이탈','base':'범위 이탈','bear':'5,900 회복'}[k])
s['events']=[{'time':'10월29일 21:30 KST','name':'미국 GDP·PCE','path':'성장·물가·금리'},{'time':'10월29일 ET','name':'Amazon 실적','path':'클라우드·AI 투자'}];s['checkpoints']=[];s['checklist']=[{'id':'support','label':'5,900선 지지와 6,000선 안착'},{'id':'flow','label':'외국인·프로그램 매수 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5750,6000,5950] if x['id']=='KOSPI' else [75200,78550,80595];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월28일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation='급등 뒤 지지력과 매수 동행을 확인합니다.')
s['technical']['note']='10월28일 확정 일봉과 10월29일 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s)
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5937.66(+-1.24%), KODEX78550(+-2.15%), 수급최종묶음미확인.\n- 클라우드성장/현금부담·금리동결, SK실적전일반영중복제외.\n- 다음 GDP/PCE10/29 21:30KST·Amazon10/29ET.\n- 기본5750~5950(50%),강세5950초과~6100(20%),약세5550~5750미만(30%),대응15/50/35.\n- 보고서 reports/{DATE}.md, 취재 research/notes/{DATE}.md.\n- 직전전망강세상단초과, 경로5950내. 평가 generated/latest.md,수급앵커미정산.\n')
for page in ['index.html','articles/index.html','articles/market.html']:
 t=read(page)
 def card(m):
  if 'market-'+DATE+'.html' in m[0]:return re.sub(r'2026\.10\.\d{2}','2026.10.30',re.sub(r'10월 \d{1,2}일','10월 29일',m[0]))
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 t=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,t,flags=re.S)
 if page=='articles/market.html':t=t.replace('반도체 랠리와 SK하이닉스 실적','급등 뒤 클라우드 실적과 지지력')
 write(page,t)
print('prepared',NOW)
