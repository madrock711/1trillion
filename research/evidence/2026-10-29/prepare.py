import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-29';OLD='2026-10-28';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='6,000선 회복 뒤 갈라진 클라우드 실적…급등한 반도체의 지지력 시험'
SUMMARY='KOSPI가 6,000선을 회복한 뒤 Microsoft의 클라우드 성장과 Alphabet의 현금흐름 부담이 엇갈렸습니다. 오늘은 6,000선 안착과 반도체 매수 지속성을 확인할 차례입니다.'
IMAGE='market-2026-10-29-cloud-crossroads-1200x630.png';ALT='밝은 아침 도시 위에서 민트색과 호박색 길로 갈라지는 흰 고가도로와 유리 구름';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261028\|([^"\s]+)',base64.b64decode(ev(k+'-fchart.raw')['raw'])).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==6012.44 and L['close']==80280
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(ev('after-'+k+'.raw')['raw']));d=d['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f"|{k}|{c:,.2f}|{(c/d['meta']['regularMarketPrice']-1)*100:+.2f}%|{at}|")
aftertable='\n'.join(after)
sources=[('연준 10월 결정','https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a.htm'),('Microsoft 실적','https://www.microsoft.com/en-us/Investor/earnings/FY-2027-Q1/press-release-webcast'),('Alphabet SEC 실적','https://www.sec.gov/Archives/edgar/data/1652044/000165204426000080/googexhibit991q32026.htm'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉',ev('KOSPI-fchart.raw')['url']),('BEA 일정','https://www.bea.gov/news/schedule')]
notes='''# 2026-10-29 취재 노트
08:46 KST 재개, 08:47 시세 수집. KRX PREOPEN와 NXT 당일 OPEN 확인. 기존 08시 실행은 중단됐으며 소급하지 않는다.
레이더: Microsoft Azure48% 성장(13점), Alphabet Cloud103%와 FCF-90.65억달러(13), 연준3.75~4%동결·2인인상반대(12), 국내SK실적후급등6.63%(12), SOXX추가상승/MU강세(11), 메모리현물품목차별화(9), GDP/PCE·Amazon예정(9), 청산/블록딜/규제신규사건(미확인,공개생략).
확정: 전일KOSPI6012.44·KODEX80280, fchart/API교차. SK실적은전일국내반영으로중복호재계산금지. 미국ADR후행도동일. 새충격은연준결정·미국마감후클라우드실적. 메모리현물과주식포지션/밸류에이션분리.
한계: 최종국내수급/프로그램/시장폭·15:20앵커없음. PREOPEN0을확정0으로취급하지않음. HBM신규계약물량/단가·NAND/eSSD당일계약가격미확인. FRED금리차10/28과개별금리10/27시차를표시,혼합차감금지.
집필 중심명제: 수요성장과투자현금부담의충돌,급등후6000지지력. write-finished-manuscript 집필/퇴고 뒤 humanize-korean 사실고정국소윤문. 밝은분기도로신규썸네일.
'''
write('research/notes/'+DATE+'.md',notes+'\n'+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n')
body='''<p>KOSPI가 하루 6.63% 올라 6,012.44로 마쳤습니다. SK하이닉스 실적을 소화하며 단숨에 올라선 자리에서 오늘은 매수세가 남아 있는지를 시험합니다. 미국 반도체의 추가 상승은 힘을 보태지만, 밤사이 클라우드 기업 실적은 AI 수요의 성장과 투자 부담을 동시에 드러냈습니다.</p>
<h2>성장은 이어졌지만 현금흐름은 갈렸다</h2>
<p>Microsoft의 분기 매출은 922.79억달러로 19% 늘었고 Azure 매출은 48% 증가했습니다. 클라우드 수요가 이어진다는 근거입니다. <a href="https://www.microsoft.com/en-us/Investor/earnings/FY-2027-Q1/press-release-webcast">Microsoft 실적</a></p>
<p>Alphabet은 Cloud 매출이 103% 늘어난 307억달러였지만 설비투자 513.55억달러가 영업현금흐름 422.90억달러를 웃돌았습니다. 잉여현금흐름은 90.65억달러 적자입니다. 메모리를 사들이는 고객의 수요 성장과 그 투자를 감당하는 현금 여력을 함께 볼 이유입니다. <a href="https://www.sec.gov/Archives/edgar/data/1652044/000165204426000080/googexhibit991q32026.htm">Alphabet 실적</a></p>
<h2>금리 동결 뒤에도 할인율 부담은 남았다</h2>
<p>연준은 기준금리를 3.75~4.00%로 유지했습니다. 표결은 10대 2였고 반대한 두 위원은 0.25%포인트 인상을 원했습니다. 동결 자체를 곧바로 완화 신호로 읽기는 어렵습니다. 높은 금리가 이어지면 AI 투자기업의 자금조달과 성장주의 가치평가에 부담이 남습니다. <a href="https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a.htm">연준 성명</a></p>
<h2>6,000선 안착과 반도체 매수의 폭</h2>
<p>전일 KODEX 레버리지는 14.76% 오른 80,280원으로 마쳤습니다. 오늘은 KOSPI 6,000선에서 매물이 나와도 5,900선 위로 지지를 높이는지, 반도체 두 종목의 상승이 금융·자동차·조선으로 퍼지는지가 관건입니다. 미국의 반도체 상승 중 한국 실적을 뒤따른 부분은 전일 급등과 같은 재료입니다.</p>
<p>기본 시나리오는 KOSPI 5,900~6,100, 확률 50%입니다. 6,100을 넘고 외국인과 프로그램 매수가 함께 들어오면 6,100 초과~6,250의 강세 시나리오 20%를 봅니다. 5,900 아래에서 외국인·프로그램 매도가 동행하면 5,700~5,900 미만의 약세 시나리오 30%로 기웁니다. 각각 경계선을 되돌아 넘으면 해당 판단을 접습니다.</p>
<p>KODEX는 78,000원 지지, 80,280원 회복·유지, 전일 고가 81,010원 돌파를 순서대로 봅니다. 공격 15·관망 50·방어 35로 두며, 급등 폭만으로 추격할 근거를 삼지 않습니다. 오늘 오후 9시 30분 미국 GDP·PCE와 미국시간 29일 Amazon 실적이 다음 시험대입니다. <a href="https://www.bea.gov/news/schedule">BEA 일정</a></p>'''
write('research/evidence/'+DATE+'/body.html',body)
report=f'''# {DATE} KOSPI·KODEX 장전 리서치
작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전, 미국10/28정규장·시간외 별도

## 핵심 결론
급등후6000안착확인. 공격15·관망50·방어35. MS수요성장과Alphabet현금부담충돌.
## 밤사이 시장을 지배한 이슈
연준3.75~4%동결10:2·소수2인인상선호. MS매출922.79억+19%·Azure+48%. Alphabet매출1275.77억·Cloud307억+103%·CAPEX513.55억/OCF422.90억/FCF-90.65억. 사실과해석분리: 수요성장은확정,국내매수지속은조건부.
## 전일 대비 바뀐 변수와 유지 변수
새변수연준결정/빅테크실적. SK실적전일반영·미국후행분중복합산제외.
## 한국시장·KODEX 대시보드
전일KOSPI{K}·+6.63%,KODEX{L}·+14.76%. fchart/API교차.
FAST_TABLE
## 메모리 반도체 수급
10/28 DRAM표DDR5 16Gb61.333달러보합·DDR4 16Gb82.92달러+0.36%. 현물과HBM계약구분. HBM/서버DRAM/NAND/eSSD신규물량·계약단가미확인. 수요성장과할인율·포지션위험분리.
## 미국 반도체·AI
|종목|종가USD|등락|
|---|---:|---:|
{ustable}
시간외는별도:
{aftertable}
## 달러/원·국내 수급·시장 구조
FAST_TABLE
최종현물/선물·기관세부·프로그램·시장폭미확인(null),PREOPEN0재사용금지.
## 경제 캘린더
10/29 21:30KST GDP/PCE,Amazon미국29일. 연준결정은이미발표됨.
## 미 국채와 장단기 금리차
FRED10/28 10Y-2Y0.38%p·10Y-3M0.87%p. 개별금리최신10/27 3M4.22·2Y4.70·10Y4.99%. 서로다른날혼합차감안함.
![90일](../charts/us_yield_spreads_90d_{DATE}.png)
![2년](../charts/us_yield_spreads_long_term_{DATE}.png)
## 오늘 KOSPI·KODEX 시나리오
강세20%6100초과~6250:지수>6100 AND 외국인>0 AND 프로그램>0,6100재이탈무효.
기본50%5900~6100:지수>=5900 AND <=6100 AND 외국인>=-8000억원,범위이탈무효.
약세30%5700~5900미만:지수<5900 AND 외국인<0 AND 프로그램<0,5900회복무효.
관측15:20·다음확인09:30/10시/14시. 장중90%포락5500~6400. KODEX78000/80280/81010.
## 장중 체크리스트
6000안착·5900지지·반도체매수확산·환율/선물동행. 가설승격없음.
## 출처와 확인 시각
evidence/{DATE} 원문rawHash/fetchedAt별도. 최초수집08:47,최종표시상단.
'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
src=read('research/evidence/2026-10-20/build.py');tail=src[src.index("old=read('articles/market-'+OLD+'.html')"):];tail=tail[:tail.index('s=prior;s.update')]
tail=tail.replace("oldimage='market-2026-10-19-memory-credit-1200x630.png'","oldimage='market-2026-10-28-earnings-curtain-1200x630.png'")
for a,b in [('2026.10.20','2026.10.29'),('2026.10.19','2026.10.28'),('2026-10-19','2026-10-28'),('10월 19일','10월 28일')]:tail=tail.replace(a,b)
exec(tail)
s=json.loads(read('assets/data/market-dashboard-latest.json'));s.update(headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'},sourceLabel='미국10/28 정규장·국내10/28 종가·10/29 장전')
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=6.63,open=K['open'],high=K['high'],low=K['low'],previousClose=5638.34,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월28일 정규장 종가')
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'최종 묶음 미확인'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'급등 뒤 지지력 확인','attack':15,'wait':50,'defense':35,'note':'클라우드 성장과 투자 부담이 엇갈린 가운데 6,000선 안착을 시험합니다.'}
s['changes']=[{'label':'KOSPI','before':'5,638.34','after':'6,012.44','meaning':'SK하이닉스 실적을 반영하며 6.63% 상승했습니다.'}]
s['factors']=[{'label':'클라우드 수요','metric':'Azure +48%','detail':'Microsoft 10/28 실적','tone':'positive'},{'label':'투자 부담','metric':'Alphabet FCF -90.65억달러','detail':'10/28 분기 실적','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/28','value':'$61.333','change':'보합'},{'label':'DDR4 16Gb · 10/28','value':'$82.92','change':'+0.36%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,900','pivot':'6,000','resistance':'6,100'},{'asset':'KODEX 레버리지','support':'78,000원','pivot':'80,280원','resistance':'81,010원'}]
for x in s['scenarios']:
 k=x['id'];x.update(label={'bull':'강세 · 20%','base':'기본 · 50%','bear':'약세 · 30%'}[k],range={'bull':'KOSPI 6,100 초과~6,250','base':'KOSPI 5,900~6,100','bear':'KOSPI 5,700~5,900 미만'}[k],summary='급등 뒤 매수 지속성 확인',conditions={'bull':['6,100 초과','외국인 순매수','프로그램 순매수'],'base':['5,900 이상','6,100 이하','외국인 순매도 8천억원 이하'],'bear':['5,900 미만','외국인 순매도','프로그램 순매도']}[k],invalidation={'bull':'6,100 재이탈','base':'범위 이탈','bear':'5,900 회복'}[k])
s['events']=[{'time':'10월29일 21:30 KST','name':'미국 GDP·PCE','path':'성장·물가·금리'},{'time':'10월29일 ET','name':'Amazon 실적','path':'클라우드·AI 투자'}];s['checkpoints']=[];s['checklist']=[{'id':'support','label':'5,900선 지지와 6,000선 안착'},{'id':'flow','label':'외국인·프로그램 매수 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5900,6000,6100] if x['id']=='KOSPI' else [78000,80280,81010];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월28일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation='급등 뒤 지지력과 매수 동행을 확인합니다.')
s['technical']['note']='10월28일 확정 일봉과 10월29일 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s)
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI6012.44(+6.63%), KODEX80280(+14.76%), 수급최종묶음미확인.\n- 클라우드성장/현금부담·금리동결, SK실적전일반영중복제외.\n- 다음 GDP/PCE10/29 21:30KST·Amazon10/29ET.\n- 기본5900~6100(50%),강세6100초과~6250(20%),약세5700~5900미만(30%),대응15/50/35.\n- 보고서 reports/{DATE}.md, 취재 research/notes/{DATE}.md.\n- 직전전망강세상단초과, 경로6100내. 평가 generated/latest.md,수급앵커미정산.\n')
for page in ['index.html','articles/index.html','articles/market.html']:
 t=read(page)
 def card(m):
  if 'market-'+DATE+'.html' in m[0]:return re.sub(r'2026\.10\.\d{2}','2026.10.29',re.sub(r'10월 \d{1,2}일','10월 29일',m[0]))
  return m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 t=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,t,flags=re.S)
 if page=='articles/market.html':t=t.replace('반도체 랠리와 SK하이닉스 실적','급등 뒤 클라우드 실적과 지지력')
 write(page,t)
print('prepared',NOW)
