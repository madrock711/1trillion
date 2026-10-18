"""검증한 10/19 취재 노트로 공개 산출물 준비."""
import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-19';OLD='2026-10-16';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='미국 반도체 다시 급락…KOSPI 반등은 5,590선에서 시험대'
SUMMARY='미국 반도체 매도와 수입물가 상승이 금요일 국내 반등을 압박합니다. DRAM 현물 가격은 견조한 가운데 KOSPI 5,590선 방어와 5,700선 회복을 봅니다.'
IMAGE='market-2026-10-19-memory-credit-1200x630.png';ALT='민트색 받침 위 웨이퍼와 구리색 조임 장치가 달린 투명 관';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8-sig'))
def raw(k):return base64.b64decode(ev(k+'.raw')['raw'])
def num(x):return float(str(x).replace(',',''))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261016\|([^"\s]+)',raw(k+'-fchart')).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==5668.05 and L['close']==70415
v=ev('122630')['data'][0];assert [L[k] for k in ['open','high','low','close','volume']]==[num(v[k]) for k in ['openPrice','highPrice','lowPrice','closePrice','accumulatedTradingVolume']]
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(raw('after-'+k))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f'|{k}|{c:,.2f}|{(c/us(k)[0]-1)*100:+.2f}%|{at}|')
aftertable='\n'.join(after)
sources=[('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉','https://fchart.stock.naver.com/sise.nhn?symbol=KOSPI&timeframe=day&count=5&requestType=0'),('미국 수출입물가','https://www.bls.gov/news.release/ximpim.nr0.htm'),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('SK하이닉스','https://news.skhynix.com/en/all/'),('BLS 일정','https://www.bls.gov/schedule/2026/10_sched.htm'),('FOMC','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),('FRED','https://fred.stlouisfed.org/series/T10Y2Y')]
report=f'''# {DATE} KOSPI·KODEX 장전 리서치

작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전. 미국 10/16 정규장 및 시간외 종료. 월요일 선물·NXT 별도 시각.

## 핵심 결론

{SUMMARY} 기본 종가 5,500~5,700(45%), 강세 5,700 초과~5,850(20%), 약세 5,250~5,500 미만(35%). 공격10·관망45·방어45. 90% 장중 포락5,100~6,000. 수동 조건부 전망이며 확률과 대응점수는 별개.

## 밤사이 시장을 지배한 이슈

금요일 미국 SOXX -4.14%, SMH -3.41%, MU -5.63%. 한국 10/16 마감 이후 거래이므로 국내 반등 뒤 추가 부담이다. CoreWeave 신용 우려는 기존 사건 연장으로 분리하고 파산·강제청산으로 확대하지 않는다. BLS 수입물가 +1.1%/+8.1%, 수출물가 +2.2%(10/16 08:30 ET=21:30 KST)는 한국 마감 뒤 새 물가 정보다. 금리·AI 금융비용·반도체 할인율 경로는 해석. 후보 8건·반론·제외 사유는 research/notes/{DATE}.md.

## 국내 확정값·직전 전망 회고

|항목|10/16 시가|고가|저가|종가|
|---|---:|---:|---:|---:|
|KOSPI|5,653.99|5,809.94|5,590.33|5,668.05|
|KODEX|70,405|73,980|68,460|70,415|

KOSPI +2.05%, KODEX +3.88%, 거래량27,605,409주. KRX 기반 price·fchart 교차. 직전 기본5450~5650 실패, 강세 종가범위 적중. 고가5809.94는 강세 종가상단 초과하나 장중포락5050~5950 안. 정확15:20 앵커 부재로 수급조건 미검증. 누적 평가기는 기존9/21 보고서 해시 불일치로 중단, 활성 가설 없음.

현물 수급 API의 개인·기관·외국인 합계가 불일치해 금액 검증 보류. 프로그램 합계는 +4278억원이나 최종 전체묶음·기타 주체 대조 미완료로 공개 전략에 사용하지 않음. 금융투자·연기금·사모·보험·투신·선물 확정값 미확인. 장전 0을 최종값으로 채우지 않음.

## 메모리 펀더멘털과 주가 수급

TrendForce 10/16 18:10 GMT+8 DDR5 16Gb 60.60달러(+0.28%), DDR4 16Gb83.66달러(보합). 현물 가격 견조와 주식 매도 공존. SK하이닉스10/16 OCP 메모리 중심 서버 비전은 제품 로드맵이며 확정 수주와 다름. HBM·서버 DRAM·RDIMM·NAND·eSSD 신규 계약단가·수율·물량 미확인. NAND 공개현물10/5·계약8/31을 최신가격으로 쓰지 않음. Solidigm 협상 보도는 확정 미국 신규공장 계약으로 쓰지 않음.

## 미국 정규장

|종목|10/16 종가 USD|등락|
|---|---:|---:|
{ustable}

미국10/16 16:00 ET=10/17 05:00 KST 종료. 연속 정규장 종가로 등락 계산, 시간외와 분리.

|종목|시간외 USD|종가 대비|최근 5분봉 KST|
|---|---:|---:|---|
{aftertable}

시간외 마지막 유효5분봉이며 확정종가·현재거래와 다름. 월요일 미국 정규장 아직 개장 전.

## 최종 환율·선물·NXT

FAST_TABLE

하나은행 고시는 역외 현물환과 다르다. 선물은 최근 거래값과 원천시각을 구분, 유가는 최근선물 가격이며 현물·결제값이 아님. NXT와 KRX 가격 기준 차이 주의. 기존 CXMT·CPI·급락 반영분 및 후행ADR·EWY를 새 충격으로 이중 계산하지 않음.

## 금리와 경제 일정

FRED 10/16 10Y-2Y +0.35%p, 10Y-3M +0.83%p. 개별금리 최신10/15 3M4.28%, 2Y4.77%, 10Y5.10%. 기준일 혼합 차감·금리방향 추정 금지. 금리차 양수만으로 경기·주가 강세 단정 불가.

BLS 공식달력10/19 주요발표 없음. Netflix10/20 13:01 PT=10/21 05:01 KST, Tesla10/21 미국마감후=10/22 KST, FOMC10/27~28 ET. 확정되지 않은 빅테크 날짜는 추가하지 않음.

![최근 90일](../charts/us_yield_spreads_90d_{DATE}.png)
![최근 2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 조건부 전망과 무효화

- 강세20%: 5700초과~5850. 15:20 지수>5700 AND 외국인>0 AND 프로그램>0. 5700 재이탈 시 무효.
- 기본45%: 5500~5700. 15:20 지수>=5500 AND <=5700 AND 외국인>=-8000억원. 범위이탈·매도확대 시 무효.
- 약세35%: 5250~5500미만. 15:20 지수<5500 AND 외국인<0 AND 프로그램<0. 5500회복 시 무효.
- KOSPI 단기 기술지지5590, 반등기준5700, 저항5810. 종가 시나리오 경계5500과 구별.
- KODEX 지지68460·반등기준70415·저항73980원. 68460이탈 후 미회복시 방어 실패.
- 09:30·10:00 외국인·프로그램 동행, 14:00 반전,15:20 종가조건 점검. 한 시점 매수를 지속수급으로 간주하지 않음.

## 출처

'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
body='''<p>금요일 KOSPI의 반등이 월요일 아침 다시 시험대에 올랐습니다. 국내 지수가 2.05% 오른 뒤 미국에서는 반도체주가 큰 폭으로 밀렸습니다. 오늘은 전 거래일 저점인 5,590선에서 매도가 멎는지, 반등할 때 외국인과 프로그램 매수가 함께 붙는지가 중요합니다.</p>
<h2>한국장 마감 뒤 더해진 반도체 매도</h2>
<p>미국 금요일 정규장에서 SOXX는 4.14%, SMH는 3.41% 하락했습니다. Micron은 5.63%, AMD는 5.95%, Broadcom은 4.52% 떨어졌습니다. AI 투자에 들어갈 자금의 비용을 걱정하는 시장에서 메모리와 장비·설계 기업이 함께 압박받았습니다. 이는 금요일 한국장 반등 이후의 움직임입니다.</p>
<p>같은 날 한국시간 밤 9시 30분 발표된 미국 9월 수입물가는 전월보다 1.1%, 수출물가는 2.2% 올랐습니다. 수입물가는 전년 대비 8.1% 상승했습니다. 물가 부담이 길어지면 금리 인하 기대와 AI 설비투자의 자금 조달 여건도 제약받습니다. <a href="https://www.bls.gov/news.release/ximpim.nr0.htm">BLS 발표</a></p>
<h2>메모리 가격은 버티지만 주가는 수급을 따릅니다</h2>
<p>DRAM 현물 가격은 주식시장과 다른 모습을 보였습니다. 16일 대만시간 오후 6시 10분 기준 DDR5 16Gb 평균 가격은 60.60달러로 0.28% 올랐고 DDR4 16Gb는 83.66달러로 보합이었습니다. 메모리 가격이 견조해도 투자자들이 위험을 줄이면 관련 주가는 하락할 수 있습니다. 현물 강세를 곧바로 오늘의 주가 반등으로 연결하기 어려운 이유입니다. <a href="https://www.trendforce.com/price/dram/dram_spot">TrendForce</a></p>
<p>SK하이닉스는 OCP 행사에서 메모리를 중심에 둔 서버 구조의 방향을 제시했습니다. 기술 수요의 장기적 확장과 단기 주식 매도는 함께 나타날 수 있습니다. 오늘 반등의 힘은 제품 로드맵에 대한 기대와 함께 실제 매수세로 판단해야 합니다. <a href="https://news.skhynix.com/en/all/">SK하이닉스 뉴스룸</a></p>
<h2>5,590선 방어와 5,700선 회복</h2>
<p>금요일 KOSPI는 5,809.94까지 올랐다가 5,668.05로 마쳤습니다. 장중 고점에서 상승 폭을 상당 부분 반납했습니다. 전 거래일 저점인 5,590선이 무너지면 5,500선까지 다시 가격을 탐색할 수 있고, 5,700선을 회복하더라도 매수가 따라오지 않으면 반등이 짧아질 수 있습니다.</p>
<p>오늘 기본 종가 범위는 5,500~5,700으로 봅니다. 외국인과 프로그램이 함께 순매수하면서 5,700선을 유지하면 5,700 초과~5,850의 강세 경로가 열립니다. 두 수급이 순매도로 기울고 5,500선을 밑돌면 약세 범위는 5,250~5,500 미만입니다. 각각의 확률은 기본 45%, 강세 20%, 약세 35%이며 예상 범위 밖 움직임도 가능합니다.</p>
<p>KODEX 레버리지는 금요일 저점 68,460원, 종가 70,415원, 고가 73,980원을 순서대로 봅니다. 68,460원을 이탈한 뒤 되찾지 못하면 지지 판단을 접어야 합니다. 70,415원을 회복하고 지수와 수급이 함께 개선될 때 다음 저항인 73,980원을 시험할 여지가 커집니다.</p>
<h2>이번 주 실적과 금리 일정</h2>
<p>Netflix 실적은 한국시간 21일 오전 5시 1분, Tesla는 22일 새벽에 나옵니다. 다음 FOMC는 미국시간 27~28일입니다. 16일 미국 10년물과 2년물 금리차는 0.35%포인트, 10년물과 3개월물은 0.83%포인트였습니다. 장단기 금리차의 모양과 기업이 실제로 부담하는 조달금리는 구분해서 봐야 합니다.</p>'''
# Public prose completed and locally polished; source facts fixed.
write('research/evidence/'+DATE+'/body.html',body)
old=read('articles/market-'+OLD+'.html');prefix=old.split('<article class="editorial-article reading-article">')[0];suffix=old[old.index('</div></article></main>'):];oldimage=re.search(r'assets/images/articles/([^"\s]+)',prefix)[1]
prefix=prefix.replace('market-'+OLD+'.html','market-'+DATE+'.html').replace(oldimage,IMAGE)
prefix=re.sub(r'<title>.*?</title>',f'<title>{TITLE} | 연마</title>',prefix)
for prop,val in [('description',SUMMARY),('og:title',TITLE),('twitter:title',TITLE),('og:description',SUMMARY),('twitter:description',SUMMARY),('og:image:alt',ALT),('article:published_time',NOW),('article:modified_time',NOW)]:prefix=re.sub(r'(<meta (?:property|name)="'+re.escape(prop)+r'" content=")[^"]+',lambda m:m[1]+val,prefix)
def ld(m):
 j=json.loads(m[1]);j.update(headline=TITLE,description=SUMMARY,datePublished=NOW,dateModified=NOW,mainEntityOfPage=URL,image={'@type':'ImageObject','url':'https://www.hpmplab.com/assets/images/articles/'+IMAGE,'width':1200,'height':630});return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False)+'</script>'
prefix=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,prefix,flags=re.S)
def table(md):
 rows=[l.split('|')[1:-1] for l in md.splitlines() if l.startswith('|') and '---' not in l];return '<div class="article-table-wrap"><table class="article-data-table"><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
header=f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong>HPMPLab</strong><time datetime="{NOW}">2026.10.19 · 작성 {NOW[11:16]} KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 PREPARED · 데이터 최종 확인 PREPARED. 특정 상품의 매매 권유가 아닌 조건부 시장 분석입니다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" alt="{ALT}" fetchpriority="high"></figure></header><div class="article-body" id="article-body">'
charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{span}_{DATE}.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {span}"></figure>' for span in ['90d','long_term'])
links='<p>'+' · '.join(f'<a href="{b}">{a}</a>' for a,b in sources)+'</p>'
write('articles/market-'+DATE+'.html',prefix+header+body+'<h2>장전 시세</h2>FAST_TABLE<h2>미국 시간외 최근 거래</h2>'+table('|종목|USD|종가 대비|원천 시각|\n'+aftertable)+'<h2>미국 정규장</h2>'+table('|종목|종가 USD|등락|\n'+ustable)+charts+links+suffix)
# Add cards without altering historical cards.
prior=json.loads(read('assets/data/market-dashboard-latest.json'))
for page,css in [('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')]:
 s=read(page);pat=r'<article class="'+css+r'"[^>]*>.*?</article>';match=next(m for m in re.finditer(pat,s,re.S) if 'market-'+OLD+'.html' in m[0]);card=match[0].replace('market-'+OLD+'.html','market-'+DATE+'.html').replace(oldimage,IMAGE).replace(prior['headline'],TITLE).replace(prior['summary'],SUMMARY).replace('2026.10.16','2026.10.19').replace('10월 16일','10월 19일')
 card=re.sub(r'2026-10-16T[^"< ]+',NOW,card);card=re.sub(r'2026\.10\.19 · [^<]+','2026.10.19 · '+NOW[11:16]+' KST',card);card=re.sub(r'(<img[^>]*alt=")[^"]+',lambda m:m[1]+ALT,card)
 s=s[:match.start()]+card+'\n'+s[match.start():]
 def collection(m):
  j=json.loads(m[1])
  for n in j.get('@graph',[j]):
   if n.get('@type')=='CollectionPage':
    e=n.get('mainEntity',{});items=e.get('itemListElement',[]);items.insert(0,{'@type':'ListItem','position':1,'url':URL,'name':TITLE,'description':SUMMARY,'datePublished':NOW,'dateModified':NOW,'image':{'@type':'ImageObject','url':'https://www.hpmplab.com/assets/images/articles/'+IMAGE}})
    for i,x in enumerate(items,1):x['position']=i
    e['numberOfItems']=len(items)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',collection,s,flags=re.S)
 if page=='articles/market.html':
  # Only hero fields, do not replace text in prior article cards.
  head,tail=s.split('<article class="market-article-item"',1);head=head.replace(prior['headline'],TITLE).replace(prior['summary'],SUMMARY);head=re.sub(r'(id="market-(?:latest-article|summary-article)-link" href=")[^"]+',lambda m:m[1]+f'market-{DATE}.html',head);s=head+'<article class="market-article-item"'+tail
  s=re.sub(r'(일일시황 <span class="article-category-count">)\d+',lambda m:m[1]+str(len(list(R.glob('articles/market-20*.html')))),s);s=re.sub(r'(발행일 기준 최신순 · )\d+(편)',lambda m:m[1]+str(len(list(re.finditer(pat,s,re.S))))+m[2],s)
 else:
  cats=re.findall(r'<article class="article-card(?: home-article-card)?" data-category="([^"]+)"',s)
  for c in ['all','market','essay','health']:s=re.sub(r'(data-category-count="'+c+r'">)\d+',lambda m:m[1]+str(len(cats) if c=='all' else cats.count(c)),s)
 write(page,s)
write('sitemap.xml',read('sitemap.xml').replace('</urlset>',f'<url><loc>{URL}</loc><lastmod>{DATE}</lastmod><image:image><image:loc>https://www.hpmplab.com/assets/images/articles/{IMAGE}</image:loc></image:image></url>\n</urlset>'))
s=prior;s.update(snapshotId='20261019-prepared',generatedAt=NOW,asOf=NOW,asOfDisplay=NOW,sourceLabel='미국 10월 16일 정규장 · 국내 10월 16일 종가 · 10월 19일 장전',headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'})
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='확정값 미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=2.05,open=K['open'],high=K['high'],low=K['low'],previousClose=5554.22,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월 16일 정규장 종가')
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'최종 묶음 검증 보류'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'반등 유지 확인 우선','attack':10,'wait':45,'defense':45,'note':'미국 반도체 매도와 견조한 DRAM 현물이 엇갈립니다.'}
s['checkpoints']=[];s['changes']=[{'label':'KOSPI','before':'5,554.22','after':'5,668.05','meaning':'장중 고점 5,809.94에서 반등 폭을 반납했습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX -4.14% · MU -5.63%','detail':'10월 16일 정규장','tone':'warning'},{'label':'수입물가','metric':'전월 +1.1% · 전년 +8.1%','detail':'10월 16일 BLS 발표','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/16','value':'$60.60','change':'+0.28%'},{'label':'DDR4 16Gb · 10/16','value':'$83.66','change':'보합'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,590','pivot':'5,700','resistance':'5,810'},{'asset':'KODEX 레버리지','support':'68,460원','pivot':'70,415원','resistance':'73,980원'}]
s['scenarios']=[{'id':k,'label':label,'range':ran,'summary':summ,'conditions':cond,'invalidation':inv} for k,label,ran,summ,cond,inv in [('bull','강세 · 20%','KOSPI 5,700 초과~5,850','매수세가 동행하는 반등',['5,700 초과','외국인 순매수','프로그램 순매수'],'5,700 재이탈'),('base','기본 · 45%','KOSPI 5,500~5,700','반등 유지력 시험',['5,500 이상','5,700 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 매도 확대'),('bear','약세 · 35%','KOSPI 5,250~5,500 미만','하단 지지 실패',['5,500 미만','외국인 순매도','프로그램 순매도'],'5,500 회복')]]
s['events']=[{'time':'10월 21일 05:01 KST','name':'Netflix 실적','path':'성장주 실적 평가'},{'time':'10월 22일 새벽 KST','name':'Tesla 실적','path':'기술주 투자 심리'},{'time':'10월 27~28일 ET','name':'FOMC','path':'금리·자금조달 여건'}]
s['checklist']=[{'id':'support','label':'5,590선 방어'},{'id':'rebound','label':'5,700선 회복과 수급 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5590,5700,5810] if x['id']=='KOSPI' else [68460,70415,73980];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월 16일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월 16일 확정 일봉과 10월 19일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s);dump('assets/data/market-dashboard-latest.json',s);dump('research/evidence/'+DATE+'/prepared.json',{'title':TITLE,'summary':SUMMARY,'image':IMAGE,'asOf':NOW})
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI 5,668.05(+2.05%), KODEX70,415원(+3.88%). 현물수급 합계 검증 보류, flows 초기화.\n- 미국 반도체 재매도·수출입물가 신규 부담, DRAM 현물 견조. 기존 반영분 중복 제외.\n- 다음 Netflix10/21 05:01 KST·Tesla10/22 새벽·FOMC10/27~28 ET.\n- 기본5500~5700(45%), 강세5700초과~5850(20%), 약세5250~5500미만(35%), 대응10/45/45.\n- 보고서 reports/{DATE}.md, 취재 research/notes/{DATE}.md, 차트 charts/us_yield_spreads_*_{DATE}.png.\n- 직전 기본실패·강세종가 적중, 수급조건 미검증. actuals/2026-10-16.json·outcomes/2026-10-16-0810-same-close.json. 누적 기존9/21 해시 오류로 중단.\n')
print('prepared',NOW)
