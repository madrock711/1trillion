"""10월 20일 검증 원문으로 취재·공개 원고·대시보드 준비."""
import base64,datetime,html,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
DATE='2026-10-20';OLD='2026-10-19';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
TITLE='미국 반도체 반등…KOSPI 5,768선 위에서 매수 지속을 본다'
SUMMARY='미국 반도체주가 반등하고 국내 지수는 전일 고점에서 마쳤습니다. KOSPI 5,768선 유지와 외국인·프로그램 매수 동행이 상승 연장의 조건입니다.'
IMAGE='market-2026-10-20-chip-rebound-1200x630.png';ALT='밝은 하늘 아래 금빛 스프링에 받쳐 올라오는 실리콘 웨이퍼';URL=f'https://www.hpmplab.com/articles/market-{DATE}.html'
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8-sig'))
def num(x):return float(str(x).replace(',',''))
def ohlc(k):return dict(zip(['open','high','low','close','volume'],map(float,re.search(rb'20261019\|([^"\s]+)',base64.b64decode(ev(k+'-fchart.raw')['raw'])).group(1).decode().split('|'))))
K=ohlc('KOSPI');L=ohlc('KODEX');assert K['close']==5768.01 and L['close']==72255
for name,v in [('KOSPI',K),('122630',L)]:
 d=ev(name)['data'][0];assert d['localTradedAt']==OLD
 for a,b in [('open','openPrice'),('high','highPrice'),('low','lowPrice'),('close','closePrice')]:assert v[a]==num(d[b])
def us(k):
 d=ev('yahoo-'+k)['data']['chart']['result'][0];q=d['indicators']['quote'][0]['close'];assert datetime.datetime.fromtimestamp(d['timestamp'][-1],datetime.timezone.utc).strftime('%Y-%m-%d')==OLD;return q[-1],(q[-1]/q[-2]-1)*100
ustable='\n'.join(f'|{k}|{us(k)[0]:,.2f}|{us(k)[1]:+.2f}%|' for k in ['QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'])
after=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(ev('after-'+k+'.raw')['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']]
 if pairs:
  t,c=pairs[-1];at=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');after.append(f'|{k}|{c:,.2f}|{(c/us(k)[0]-1)*100:+.2f}%|{at}|')
aftertable='\n'.join(after)
sources=[('미국 시세','https://finance.yahoo.com/quote/SOXX/'),('국내 일봉',ev('KOSPI')['url']),('DRAM 현물','https://www.trendforce.com/price/dram/dram_spot'),('BLS 일정','https://www.bls.gov/schedule/2026/10_sched.htm'),('Netflix 실적','https://ir.netflix.net/investor-news-and-events/financial-releases/press-release-details/2026/Netflix-to-Announce-Third-Quarter-2026-Financial-Results/default.aspx'),('Tesla 실적','https://ir.tesla.com/press-release/tesla-third-quarter-2026-production-deliveries-and-deployments'),('FOMC','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),('FRED','https://fred.stlouisfed.org/series/T10Y2Y')]
notes='''# 2026-10-20 취재 노트

수집 07:56 KST부터. 한국 장전, 미국 10/19 정규장 종료·시간외 진행 중. 정상 거래일 여부는 휴일 달력 및 최종 NXT OPEN으로 대조한다.

## 이슈 레이더
|후보|점수|확정 범위·전달 경로·제외 판단|
|---|---:|---|
|미국 반도체 기술적 반등|12|SOXX +1.73%, SMH +1.61%, MU +2.97%. 한국 마감 이후 신규 가격 변화, 신규 계약 실적 개선과 구분|
|국내 저가 매수와 종가 고점|12|KOSPI 5488.41 시가·저가에서 5768.01 고가·종가. 수급 지속 여부는 오늘 재검증|
|AI 투자 자금 비용|9|장기금리 절대 수준과 실적 대기. 지난주 우려를 새 청산 사건으로 재가산하지 않음|
|메모리 현물 차별화|9|10/19 18:10 GMT+8 DDR5 60.633 +0.05%, DDR4 83.414 -0.29%|
|Netflix·Tesla 실적 대기|8|기업 공식 일정. 확정 실적 수치로 취급하지 않음|
|유럽 시위·시장 불안|5|미국 기술주 반등과 해외 시장 폭 차이 탐색. 국내 직접 전달 경로 부족|
|신규 청산·증자·블록딜|3|개방형 검색에서 국내 지배 재료로 확정할 원문 미확보, 비사건 공개 제외|
|신규 공급계약·수출규제|3|검색 단서만으로 확정 금액·계약·규제를 만들지 않음|

## 논쟁점과 반론
가격 반등은 신규 AI 수익화나 수주 확정을 뜻하지 않는다. 미국 10/19 프리마켓의 반등 기대는 국내 오후장과 겹칠 수 있으므로 밤사이 종가 상승률 전부를 별도 상승 충격으로 더하지 않는다. 전일 한국 반등과 미국 후행 반응은 같은 위험선호 회복의 일부다.
현물 수급 integration은 개인 -11767·외국인 +947·기관 +5302억원으로 합계 불일치, 보도 6247·8789억원과도 충돌. 완전 묶음 보류·공개 금액 제외. 프로그램도 원문 보존하되 현물과 결합한 확정 인과 판단 유보. 기존 flows 초기화.
HBM·서버 DRAM·RDIMM·NAND·eSSD 신규 계약단가·수율·고객 물량 미확인. NAND 및 공개 계약 표의 오래된 날짜를 최신값으로 사용하지 않음. DDR5·DDR4 현물로 메모리 전체 업황 일반화 금지.
FRED 금리차 10/19 +0.38/+0.88%p. 개별금리 최신 10/16 3M4.26·2Y4.74·10Y5.09%, 서로 다른 날짜로 금리차 역산 금지.
공식 BLS 10/20 10:00 ET=23:00 KST 주별 고용, Netflix 10/20 13:01 PT=10/21 05:01 KST, Tesla 10/21 미국 마감 후=10/22 새벽, FOMC10/27~28 ET.
직전 기본5500~5700 실패·강세5700초과~5850 종가범위 적중. 장중 저점5488.41은 기본 하단 이탈, 90% 포락5100~6000 안. 정확15:20 수급 앵커 부재로 조건·원인 미검증. 활성 가설 없음. 과거 전체 평가기9/21 해시 오류는 오늘 예측 근거로 사용하지 않음.

## 중심 명제와 썸네일
국내 종가 고점과 미국 반도체 반등은 우호적이지만 오늘 5768선 지지·수급 동행이 상승 지속 조건이다. 회복·경계, 아이보리·하늘색·금빛 스프링의 새 구도. 이전 이미지 참조 없음.
취재 후 write-finished-manuscript 집필·퇴고, humanize-korean 사실 고정 윤문 적용. 웹 원문 확인 BLS·Netflix·Tesla, 직접 수집 시세·TrendForce·FRED. 일부 공식 웹 요청403은 source-manifest에 기록.
'''
write('research/notes/'+DATE+'.md',notes+'\n'+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n')
report=f'''# {DATE} KOSPI·KODEX 장전 리서치

작성 PREPARED / 데이터 최종 확인 PREPARED / 한국 장전. 미국10/19 정규장 종가와 진행 중 시간외 구분.

## 핵심 결론
{SUMMARY} 기본 종가5700~5900(50%), 강세5900초과~6050(25%), 약세5450~5700미만(25%). 공격25·관망50·방어25. 90% 장중 포락5300~6200. 수동 조건부 전망이며 확률과 대응점수는 별개다.

## 밤사이 지배 이슈
미국 SOXX +1.73%, SMH +1.61%, MU +2.97%. 기술주 반등은 신규 확정 수주와 구분한다. 전일 한국 오후장과 겹치는 미국 프리마켓 기대와 밤사이 정규장 반등 전체를 독립 충격으로 중복 합산하지 않는다. 신규계약·청산·증자·규제 탐색과 제외 사유는 research/notes/{DATE}.md.

## 국내 확정값과 직전 전망
|항목|10/19 시가|고가|저가|종가|
|---|---:|---:|---:|---:|
|KOSPI|5488.41|5768.01|5488.41|5768.01|
|KODEX|65920|72255|65750|72255|
KOSPI+1.76%, KODEX+2.61%, 거래량25923397주. Naver KRX 기반 price·fchart 교차. 직전 기본범위 실패·강세종가 적중, 장중 기본하단 이탈·포락 안. 정확15:20 앵커 부재로 수급 원인 미검증. integration 수급 합계 및 보도와 불일치로 확정 묶음 보류. 세부 기관·선물 수급 미확인, 0으로 채우지 않음.

## 메모리 펀더멘털
TrendForce10/19 18:10 GMT+8 DDR5 16Gb60.633달러(+0.05%), DDR4 16Gb83.414달러(-0.29%). 현물 차별화와 주식 반등은 다른 층위다. HBM·서버DRAM·RDIMM·NAND·eSSD 신규 계약단가·수율·물량 미확인. 미국 빅테크 신규 AI CAPEX 확정치 없이 반등을 신규 수요 확정으로 쓰지 않는다.

## 미국 정규장
|종목|10/19 종가 USD|등락|
|---|---:|---:|
{ustable}
미국10/19 16:00 ET=10/20 05:00 KST 종료. 등락은 연속 일봉 종가 계산.

## 미국 시간외
|종목|USD|종가 대비|유효 5분봉 시각 KST|
|---|---:|---:|---|
{aftertable}
시간외 진행 중의 최근 유효봉이며 확정 종가가 아니다.

## 최종 환율·선물·NXT
FAST_TABLE
하나은행 고시·역외 현물·NXT·KRX의 시장 기준을 구분한다. 선물은 최근 거래이며 현물·결제값과 다르다.

## 금리와 일정
FRED10/19 10Y-2Y+0.38%p·10Y-3M+0.88%p. 개별금리 최신10/16 3M4.26%·2Y4.74%·10Y5.09%. 혼합 날짜 차감 금지. 금리차 확대만으로 금융여건 완화 단정 불가.
BLS10/20 10:00 ET=23:00 KST 주별 고용, Netflix10/21 05:01 KST(10/20 13:01 PT), Tesla10/22 새벽(10/21 미국마감후), FOMC10/27~28 ET.
![최근90일](../charts/us_yield_spreads_90d_{DATE}.png)
![최근2년](../charts/us_yield_spreads_long_term_{DATE}.png)

## 조건과 무효화
- 강세25%: 5900초과~6050. 15:20 지수>5900 AND 외국인>0 AND 프로그램>0. 5900 재이탈 시 무효.
- 기본50%: 5700~5900. 15:20 지수>=5700 AND <=5900 AND 외국인>=-8000억원. 범위이탈·매도확대 시 무효.
- 약세25%: 5450~5700미만. 15:20 지수<5700 AND 외국인<0 AND 프로그램<0. 5700회복 시 무효.
- KOSPI지지5700·반등기준5768·저항5900. KODEX지지70000·반등기준72255·저항73980원. 70000 이탈 후 미회복 시 방어 실패.
- 09:30·10:00 외국인·프로그램 동행,14:00 반전,15:20 종가조건 점검. 한 시점 매수는 지속수급과 다르다.

## 출처
'''+ '\n'.join(f'- [{a}]({b})' for a,b in sources)+'\n'
write('reports/'+DATE+'.md',report)
body='''<p>전일 KOSPI는 3% 넘게 낮게 출발한 뒤 5,768.01로 올라 하루 고점에서 마쳤습니다. 미국 반도체주도 뒤이어 반등했습니다. 오늘은 반등 자체보다 전일 종가 부근에서 매수가 이어지는지가 중요합니다.</p>
<h2>반도체 반등이 열어 준 여지</h2><p>미국 19일 정규장에서 SOXX는 1.73%, SMH는 1.61% 올랐습니다. Micron은 2.97%, AMD는 1.76%, Nvidia는 1.38%, Broadcom은 1.78% 상승했습니다. 지난주 크게 밀렸던 반도체주로 매수가 돌아왔지만 하루 반등만으로 AI 투자의 자금 부담이 사라졌다고 보기는 어렵습니다.</p>
<p>한국장은 미국 정규장 개장 전에 이미 저가 매수로 돌아섰습니다. 오늘 아침의 우호적인 출발 여건을 보더라도 전일 국내 반등과 미국 상승을 별개의 호재 두 개로 더해 평가할 수는 없습니다. 개장 뒤 삼성전자·SK하이닉스의 상승 폭이 유지되고 외국인과 프로그램이 함께 매수하는지 봐야 합니다.</p>
<h2>DDR5와 DDR4가 갈리는 현물시장</h2><p>19일 대만시간 오후 6시 10분 기준 DDR5 16Gb 현물 평균은 60.633달러로 0.05% 올랐습니다. DDR4 16Gb는 83.414달러로 0.29% 내렸습니다. 메모리 가격 전체가 같은 방향으로 움직이는 장세는 아닙니다. 제품별 현물 변화와 HBM·서버 메모리의 장기 수요, 주식시장의 단기 위험선호를 구분해서 볼 필요가 있습니다. <a href="https://www.trendforce.com/price/dram/dram_spot">TrendForce 현물 가격</a></p>
<h2>5,768선 위에서 매수가 이어질까</h2><p>전일 고점이자 종가인 5,768선 위에 머물면 5,900선 회복을 시험할 여지가 생깁니다. 5,700선 아래로 밀리고 외국인·프로그램이 함께 순매도로 기울면 상승 지속 판단을 접어야 합니다.</p>
<p>오늘 기본 종가 범위는 5,700~5,900이며 확률은 50%로 봅니다. 외국인·프로그램 순매수와 함께 5,900선을 넘겨 유지하는 강세 범위는 5,900 초과~6,050(25%), 5,700선이 무너지는 약세 범위는 5,450~5,700 미만(25%)입니다. 예상 범위를 벗어나는 변동도 가능합니다.</p>
<p>KODEX 레버리지는 70,000원을 첫 지지, 전일 종가 72,255원을 반등 유지 기준, 직전 금요일 고점 73,980원을 저항으로 봅니다. 70,000원 아래에서 회복하지 못하면 지지 판단은 무효입니다. 전일 저점 65,750원은 급락 때의 가격 범위를 보여 주지만 오늘의 첫 지지선과는 거리가 있습니다.</p>
<h2>실적을 앞둔 성장주와 금리</h2><p>Netflix 실적은 한국시간 21일 오전 5시 1분, Tesla는 22일 새벽에 나옵니다. 미국 주별 고용지표는 오늘 밤 11시, 다음 FOMC는 미국시간 27~28일입니다. 반등이 실적과 현금흐름으로 이어질지 확인할 일정이 남아 있습니다.</p><p>19일 미국 10년물과 2년물 금리차는 0.38%포인트, 10년물과 3개월물은 0.88%포인트였습니다. 금리차가 벌어졌다는 사실만으로 기업의 자금 조달 여건이 좋아졌다고 판단할 수는 없습니다.</p>'''
write('research/evidence/'+DATE+'/body.html',body)
old=read('articles/market-'+OLD+'.html');prefix=old.split('<article class="editorial-article reading-article">')[0];suffix=old[old.index('</div></article></main>'):];oldimage='market-2026-10-19-memory-credit-1200x630.png'
prefix=prefix.replace('market-'+OLD+'.html','market-'+DATE+'.html').replace(oldimage,IMAGE)
prefix=re.sub(r'<title>.*?</title>',f'<title>{TITLE} | 연마</title>',prefix)
for prop,val in [('description',SUMMARY),('og:title',TITLE),('twitter:title',TITLE),('og:description',SUMMARY),('twitter:description',SUMMARY),('og:image:alt',ALT),('article:published_time',NOW),('article:modified_time',NOW)]:prefix=re.sub(r'(<meta (?:property|name)="'+re.escape(prop)+r'" content=")[^"]+',lambda m:m[1]+val,prefix)
def ld(m):
 j=json.loads(m[1]);j.update(headline=TITLE,description=SUMMARY,datePublished=NOW,dateModified=NOW,mainEntityOfPage=URL,image={'@type':'ImageObject','url':'https://www.hpmplab.com/assets/images/articles/'+IMAGE,'width':1200,'height':630});return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False)+'</script>'
prefix=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,prefix,flags=re.S)
def table(md):
 rows=[l.split('|')[1:-1] for l in md.splitlines() if l.startswith('|') and '---' not in l];return '<div class="article-table-wrap"><table class="article-data-table"><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
header=f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong>HPMPLab</strong><time datetime="{NOW}">2026.10.20 · 작성 {NOW[11:16]} KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 PREPARED · 데이터 최종 확인 PREPARED. 특정 상품의 매매 권유가 아닌 조건부 시장 분석입니다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" alt="{ALT}" fetchpriority="high"></figure></header><div class="article-body" id="article-body">'
charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{span}_{DATE}.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {span}"></figure>' for span in ['90d','long_term'])
write('articles/market-'+DATE+'.html',prefix+header+body+'<h2>장전 시세</h2>FAST_TABLE<h2>미국 시간외 최근 거래</h2>'+table('|종목|USD|종가 대비|원천 시각|\n'+aftertable)+'<h2>미국 정규장</h2>'+table('|종목|종가 USD|등락|\n'+ustable)+charts+'<p>'+' · '.join(f'<a href="{b}">{a}</a>' for a,b in sources)+'</p>'+suffix)
prior=json.loads(read('assets/data/market-dashboard-latest.json'))
for page,css in [('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')]:
 s=read(page);pat=r'<article class="'+css+r'"[^>]*>.*?</article>';match=next(m for m in re.finditer(pat,s,re.S) if 'market-'+OLD+'.html' in m[0]);card=match[0].replace('market-'+OLD+'.html','market-'+DATE+'.html').replace(oldimage,IMAGE).replace(prior['headline'],TITLE).replace(prior['summary'],SUMMARY).replace('2026.10.19','2026.10.20').replace('10월 19일','10월 20일');card=re.sub(r'2026-10-19T[^"< ]+',NOW,card);card=re.sub(r'(<img[^>]*alt=")[^"]+',lambda m:m[1]+ALT,card);card=re.sub(r'2026\.10\.20 · [^<]+','2026.10.20 · '+NOW[11:16]+' KST',card)
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
  head,tail=s.split('<article class="market-article-item"',1);head=head.replace(prior['headline'],TITLE).replace(prior['summary'],SUMMARY);head=re.sub(r'(id="market-(?:latest-article|summary-article)-link" href=")[^"]+',lambda m:m[1]+f'market-{DATE}.html',head);s=head+'<article class="market-article-item"'+tail
  s=re.sub(r'(일일시황 <span class="article-category-count">)\d+',lambda m:m[1]+str(len(list(R.glob('articles/market-20*.html')))),s);s=re.sub(r'(발행일 기준 최신순 · )\d+(편)',lambda m:m[1]+str(len(list(re.finditer(pat,s,re.S))))+m[2],s)
 else:
  cats=re.findall(r'<article class="article-card(?: home-article-card)?" data-category="([^"]+)"',s)
  for c in ['all','market','essay','health']:s=re.sub(r'(data-category-count="'+c+r'">)\d+',lambda m:m[1]+str(len(cats) if c=='all' else cats.count(c)),s)
  if page=='index.html':s=s.replace(oldimage,IMAGE)
 write(page,s)
write('sitemap.xml',read('sitemap.xml').replace('</urlset>',f'<url><loc>{URL}</loc><lastmod>{DATE}</lastmod><image:image><image:loc>https://www.hpmplab.com/assets/images/articles/{IMAGE}</image:loc></image:image></url>\n</urlset>'))
s=prior;s.update(snapshotId='20261020-prepared',generatedAt=NOW,asOf=NOW,asOfDisplay=NOW,sourceLabel='미국 10월 19일 정규장 · 국내 10월 19일 종가 · 10월 20일 장전',headline=TITLE,summary=SUMMARY,latestArticle={'title':TITLE,'href':f'market-{DATE}.html'})
for x in s['markets']:
 for k in ['value','changePercent','open','high','low','previousClose']:x[k]=None
 x.update(asOf=NOW,asOfLabel='확정값 미확인',flows=[])
 if x['id']=='KOSPI':x.update(value=K['close'],changePercent=1.76,open=K['open'],high=K['high'],low=K['low'],previousClose=5668.05,asOf=OLD+'T15:30:00+09:00',asOfLabel='10월 19일 정규장 종가')
s['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원','asOfLabel':'최종 묶음 검증 보류'},'kospi200FuturesForeign':None,'futuresUnit':'억원','futuresAsOfLabel':'미확인'}
s['stance']={'label':'반등 지속 확인','attack':25,'wait':50,'defense':25,'note':'미국 반도체 반등과 국내 종가 고점, 매수 지속이 관건입니다.'};s['checkpoints']=[]
s['changes']=[{'label':'KOSPI','before':'5,668.05','after':'5,768.01','meaning':'전일 저점에서 반등해 고점에서 마쳤습니다.'}]
s['factors']=[{'label':'미국 반도체','metric':'SOXX +1.73% · MU +2.97%','detail':'10월 19일 정규장','tone':'positive'},{'label':'미국 금리차','metric':'10Y-2Y +0.38%p','detail':'10월 19일 FRED','tone':'neutral'}]
s['memory']=[{'label':'DDR5 16Gb · 10/19','value':'$60.633','change':'+0.05%'},{'label':'DDR4 16Gb · 10/19','value':'$83.414','change':'-0.29%'}]
s['strategyLevels']=[{'asset':'KOSPI','support':'5,700','pivot':'5,768','resistance':'5,900'},{'asset':'KODEX 레버리지','support':'70,000원','pivot':'72,255원','resistance':'73,980원'}]
s['scenarios']=[{'id':k,'label':label,'range':ran,'summary':summ,'conditions':cond,'invalidation':inv} for k,label,ran,summ,cond,inv in [('bull','강세 · 25%','KOSPI 5,900 초과~6,050','매수세가 동행하는 상승',['5,900 초과','외국인 순매수','프로그램 순매수'],'5,900 재이탈'),('base','기본 · 50%','KOSPI 5,700~5,900','반등 유지력 시험',['5,700 이상','5,900 이하','외국인 순매도 8천억원 이하'],'범위 이탈 또는 매도 확대'),('bear','약세 · 25%','KOSPI 5,450~5,700 미만','하단 지지 실패',['5,700 미만','외국인 순매도','프로그램 순매도'],'5,700 회복')]]
s['events']=[{'time':'10월 20일 23:00 KST','name':'미국 주별 고용','path':'노동시장'},{'time':'10월 21일 05:01 KST','name':'Netflix 실적','path':'성장주 실적 평가'},{'time':'10월 22일 새벽 KST','name':'Tesla 실적','path':'기술주 투자 심리'},{'time':'10월 27~28일 ET','name':'FOMC','path':'금리·자금조달 여건'}]
s['checklist']=[{'id':'support','label':'5,700선 방어'},{'id':'rebound','label':'5,768선 유지와 수급 동행'}];s['sources']=[{'label':a,'href':b} for a,b in sources]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=K if x['id']=='KOSPI' else L;levels=[5700,5768,5900] if x['id']=='KOSPI' else [70000,72255,73980];x.update(asOf=OLD+'T15:30:00+09:00',asOfLabel='10월 19일 정규장 종가',points=[{'label':a,'value':v[b]} for a,b in [('시가','open'),('고가','high'),('저가','low'),('종가','close')]],levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=' · '.join(f'{a} {b:,}' for a,b in zip(['1차 지지','반등 기준','저항'],levels)))
s['technical']['note']='10월 19일 확정 일봉과 10월 20일 장전 분석 기준선입니다.'
dump('research/evidence/'+DATE+'/prepared-dashboard.json',s);dump('research/evidence/'+DATE+'/prepared.json',{'title':TITLE,'summary':SUMMARY,'image':IMAGE,'asOf':NOW})
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI5768.01(+1.76%), KODEX72255원(+2.61%). 수급 원천 불일치로 금액 보류.\n- 미국 반도체 반등·DDR5/DDR4 현물 차별화. 한국 전일 반등 중복 가산 제외.\n- 다음 미국 주별고용10/20 23:00·Netflix10/21 05:01·Tesla10/22 새벽·FOMC10/27~28 ET.\n- 기본5700~5900(50%), 강세5900초과~6050(25%), 약세5450~5700미만(25%), 대응25/50/25.\n- 보고서 reports/{DATE}.md, 취재 research/notes/{DATE}.md, 차트 charts/us_yield_spreads_*_{DATE}.png.\n- 직전 기본실패·강세종가 적중, 수급조건 미검증. actuals/2026-10-19.json·outcomes/2026-10-19-0803-same-close.json. 누적 기존9/21 해시 오류.\n')
print('prepared',NOW)
