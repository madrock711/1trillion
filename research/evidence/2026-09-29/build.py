import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path

R = Path(__file__).resolve().parents[3]
E = Path(__file__).parent
TZ = dt.timezone(dt.timedelta(hours=9))
TITLE = '유가와 금리가 누르는 반도체, KOSPI는 6,900선 회복이 먼저다'
SUMMARY = '미국 반도체 약세와 장전 메모리주 하락이 겹쳤습니다. KOSPI는 6,900선 회복과 수급 전환을 먼저 확인해야 합니다.'
IMAGE = 'market-2026-09-29-oil-yield-chip-pressure-1200x630.png'
URL = 'https://www.hpmplab.com/articles/market-2026-09-29.html'
ALT = '서울 아침 빛, 푸른 메모리 웨이퍼와 D램 모듈, 금빛 유가와 금리 곡선'

def read(path): return (R / path).read_text(encoding='utf-8')
def write(path, value): (R / path).write_text(value, encoding='utf-8', newline='\n')
def dump(path, value): write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def evidence(name): return json.loads((E / f'{name}.json').read_text(encoding='utf-8'))
def market(name): return evidence(f'yahoo-{name}')['data']['chart']['result'][0]['meta']
def stamp(name): return dt.datetime.fromtimestamp(market(name)['regularMarketTime'], TZ).isoformat()
def fmt(name):
    item = market(name)
    return f"{item['regularMarketPrice']:,.2f} · {item['regularMarketChangePercent']:+.2f}%"
def num(value): return float(str(value).replace(',', ''))
def body_html(markdown):
    rendered = []
    for section in markdown.split('\n\n')[1:]:
        if section.startswith('|'):
            rows = [line.strip('|').split('|') for line in section.splitlines() if not re.fullmatch(r'\|?[-| ]+\|?', line)]
            header, *items = rows
            table = '<table class="article-data-table"><thead><tr>' + ''.join(f'<th>{html.escape(x.strip())}</th>' for x in header) + '</tr></thead><tbody>'
            table += ''.join('<tr>' + ''.join(f'<td>{html.escape(x.strip())}</td>' for x in row) + '</tr>' for row in items)
            rendered.append('<div class="article-table-wrap">' + table + '</tbody></table></div>')
        else:
            rendered.append('<p>' + html.escape(section).replace('\n', '<br>') + '</p>')
    return '\n'.join(rendered)
def update_structured(value):
    def rewrite(match):
        node = json.loads(match.group(1))
        def visit(value):
            if isinstance(value, dict):
                if value.get('@type') == 'ItemList' and isinstance(value.get('itemListElement'), list) and value['itemListElement']:
                    retained = [item for item in value['itemListElement'] if 'market-2026-09-29.html' not in json.dumps(item, ensure_ascii=False)]
                    clone = json.loads(json.dumps(retained[0], ensure_ascii=False))
                    text = json.dumps(clone, ensure_ascii=False)
                    text = text.replace('market-2026-09-28.html', 'market-2026-09-29.html').replace('market-2026-09-28-ai-demand-yield-gate-1200x630.png', IMAGE).replace('2026-09-28', '2026-09-29').replace('AI 수요와 금리의 줄다리기, KOSPI 7,155선의 시험', TITLE).replace('AI 수요 계약은 이어졌지만, KOSPI 7,155선 앞엔 금리가 남았다', TITLE).replace('AI 수요와 장기금리가 맞서는 장에서 KOSPI는 7,155선 돌파의 조건을 확인합니다.', SUMMARY).replace('AI 수요 계약이 이어지는 가운데 KOSPI는 장기금리와 국내 수급을 함께 확인해야 합니다.', SUMMARY)
                    clone = json.loads(text)
                    clone.update(url=URL, name=TITLE, datePublished=issued.isoformat(), dateModified=issued.isoformat(), description=SUMMARY)
                    if isinstance(clone.get('image'), dict): clone['image']['url'] = 'https://www.hpmplab.com/assets/images/articles/' + IMAGE
                    value['itemListElement'] = [clone] + retained
                    for index, item in enumerate(value['itemListElement'], 1): item['position'] = index
                    value['numberOfItems'] = len(value['itemListElement'])
                for child in value.values(): visit(child)
            elif isinstance(value, list):
                for child in value: visit(child)
        visit(node)
        return '<script type="application/ld+json">' + json.dumps(node, ensure_ascii=False, indent=2) + '</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', rewrite, value, flags=re.S)
def card(path, css):
    source = read(path)
    pattern = r'<article class="' + re.escape(css) + r'"[^>]*>.*?</article>'
    matches = list(re.finditer(pattern, source, re.S))
    old = next(match.group(0) for match in matches if 'market-2026-09-28' in match.group(0))
    fresh = old.replace('market-2026-09-28.html', 'market-2026-09-29.html').replace('market-2026-09-28-ai-demand-yield-gate-1200x630.png', IMAGE).replace('AI 수요와 금리의 줄다리기, KOSPI 7,155선의 시험', TITLE).replace('AI 수요 계약은 이어졌지만, KOSPI 7,155선 앞엔 금리가 남았다', TITLE).replace('AI 수요와 장기금리가 맞서는 장에서 KOSPI는 7,155선 돌파의 조건을 확인합니다.', SUMMARY).replace('AI 수요 계약이 이어지는 가운데 KOSPI는 장기금리와 국내 수급을 함께 확인해야 합니다.', SUMMARY).replace('9월 28일', '9월 29일').replace('2026년 9월 28일', '2026년 9월 29일')
    fresh = re.sub(r'(data-published=")2026-09-28T[^"]+', r'\g<1>' + issued.isoformat(), fresh)
    fresh = re.sub(r'(<h3[^>]*>.*?</h3>\s*<p[^>]*>).*?(</p>)', r'\g<1>' + SUMMARY + r'\2', fresh, count=1, flags=re.S)
    fresh = re.sub(r'<time datetime="[^"]+">[^<]+</time>', f'<time datetime="{issued.isoformat()}">2026.09.29 · {issued:%H:%M} KST</time>', fresh, count=1)
    inserted = False
    def replace(match):
        nonlocal inserted
        value = match.group(0)
        if 'market-2026-09-29' in value: return ''
        if not inserted and 'market-2026-09-28' in value:
            inserted = True
            return fresh + '\n' + value
        return value
    return update_structured(re.sub(pattern, replace, source, flags=re.S))

cutoff = max(evidence(name)['fetchedAt'] for name in ('NXT','FX','yahoo-NQF','yahoo-ESF','KOSPI-basic'))
issued = dt.datetime.now(TZ).replace(microsecond=0)
nxt = {item['itemCode']: item for item in evidence('NXT')['data']['datas']}
fx = evidence('FX')['data']['exchangeInfo']
kospi = evidence('KOSPI')['data'][0]
kodex = evidence('122630')['data'][1]
assert evidence('KOSPI-basic')['data']['marketStatus'] == 'PREOPEN'
assert kospi['localTradedAt'] == '2026-09-28'
assert all(item['localTradedAt'].startswith('2026-09-29') for item in nxt.values())
manuscript = read('research/evidence/2026-09-29/manuscript.md')
prices = ['## 장전 가격', '', '|항목|가격·변화|출처 시각|', '|---|---:|---|', f"|KOSPI 전일 종가|{num(kospi['closePrice']):,.2f} · {num(kospi['fluctuationsRatio']):+.2f}%|2026-09-28 정규장 종가|", f"|KODEX 레버리지 전일 종가|{kodex['closePrice']}원 · {kodex['fluctuationsRatio']}%|2026-09-28 정규장 종가|"]
for code, label in (('005930','삼성전자 NXT'),('000660','SK하이닉스 NXT')):
    item = nxt[code]; prices.append(f"|{label}|{item['closePrice']}원 · {item['fluctuationsRatio']}%|{item['localTradedAt']}|")
prices.append(f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|")
for name, label in (('NQF','Nasdaq100 선물'),('ESF','S&P500 선물'),('BZF','브렌트 선물'),('CLF','WTI 선물')): prices.append(f'|{label}|{fmt(name)}|{stamp(name)} · 지연 시세|')
report = f'# 2026-09-29 KOSPI·KODEX 일일 리서치\n\n작성 {issued.isoformat()} / 데이터 최종 확인 {cutoff} / 한국 장전.\n\n확정 사실은 출처 시각 기준, 시나리오와 확률은 조건부 전망이다.\n\n' + manuscript.split('\n',1)[1].strip() + '\n\n' + '\n'.join(prices) + '\n\n## 취재 근거와 확인 시각\n\n' + read('research/notes/2026-09-29.md') + '\n\n## 미국 정규장 종목별 확인\n\n|종목|9/28 종가|전일 대비|\n|---|---:|---:|\n'
for ticker in ('QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'):
    item = market(ticker); report += f"|{ticker}|{item['regularMarketPrice']:.2f}|{item['regularMarketChangePercent']:+.2f}%|\n"
report += '\n![최근 90일](../charts/us_yield_spreads_90d_2026-09-29.png)\n\n![최근 2년](../charts/us_yield_spreads_long_term_2026-09-29.png)\n'
write('reports/2026-09-29.md', report)

old = read('articles/market-2026-09-28.html')
prefix = old.split('<article class="editorial-article reading-article">')[0]
prefix = (prefix.replace('AI 수요 계약은 이어졌지만, KOSPI 7,155선 앞엔 금리가 남았다', TITLE)
               .replace('미국 반도체 강세와 AI 장기 용량 계약이 하단을 지지합니다. KOSPI 7,155선 위는 장기금리와 국내 수급을 함께 넘어야 합니다.', SUMMARY)
               .replace('market-2026-09-28.html', 'market-2026-09-29.html')
               .replace('market-2026-09-28-ai-demand-yield-gate-1200x630.png', IMAGE)
               .replace('2026-09-28T08:21:05+09:00', issued.isoformat())
               .replace('서울 아침빛과 데이터센터 서버, 푸른 빛의 컴퓨팅 흐름과 금빛 장기금리 곡선', ALT))
suffix = old[old.index('</div></article></main>'):]
header = f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{issued.isoformat()}">2026.09.29 · {issued:%H:%M} KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 {issued:%H:%M} KST · 데이터 최종 확인 {cutoff}. 미국 정규장은 9월 28일, 국내 NXT·환율·미국 선물은 장전 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="{ALT}"></figure></header><div class="article-body" id="article-body">'
charts = '<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_90d_2026-09-29.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 90일"><figcaption>FRED 최신 금리차 관측일은 9월 28일이다.</figcaption></figure><figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_long_term_2026-09-29.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 2년"></figure>'
write('articles/market-2026-09-29.html', prefix + header + body_html(manuscript) + charts + suffix)

snapshot = json.loads(read('assets/data/market-dashboard-20260928-0821.json'))
sid = issued.strftime('%Y%m%d-%H%M')
snapshot.update(snapshotId=sid, generatedAt=issued.isoformat(), asOf=cutoff, asOfDisplay=cutoff, marketState='한국 장전', sourceLabel='미국 9월 28일 정규장 · 국내 9월 28일 종가 · 9월 29일 장전', latestArticle={'title':TITLE,'href':'market-2026-09-29.html'}, headline=TITLE, summary=SUMMARY)
for item in snapshot['markets']:
    if item['id']=='KOSPI': item.update(value=num(kospi['closePrice']),changePercent=num(kospi['fluctuationsRatio']),open=num(kospi['openPrice']),high=num(kospi['highPrice']),low=num(kospi['lowPrice']),asOf='2026-09-28T15:30:00+09:00',asOfLabel='9월 28일 종가',stateLabel='정규장 종가',flows=[])
snapshot['stance']={'label':'6,900선 회복과 수급 전환','attack':15,'wait':40,'defense':45,'note':'미국 반도체 약세 뒤 6,900선 회복과 외국인·프로그램 동행을 본다.'}
snapshot['checkpoints']=[{'label':'Nasdaq100 선물','value':fmt('NQF'),'detail':stamp('NQF')+' · 지연','tone':'info'},{'label':'원/달러','value':fx['closePrice']+'원','detail':fx['localTradedAt']+' 고시','tone':'warning'},{'label':'삼성전자 NXT','value':nxt['005930']['closePrice']+'원','detail':nxt['005930']['localTradedAt'],'tone':'warning'},{'label':'SK하이닉스 NXT','value':nxt['000660']['closePrice']+'원','detail':nxt['000660']['localTradedAt'],'tone':'warning'}]
snapshot['factors']=[{'label':'미국 반도체','metric':'SOXX -2.08% · MU -2.62%','detail':'9월 28일 미국 정규장','tone':'warning'},{'label':'미 국채','metric':'10년-2년 +0.32%p','detail':'FRED 9월 28일','tone':'warning'},{'label':'유가','metric':'Brent 98.71달러 · +0.90%','detail':'장전 지연 선물 시세','tone':'warning'}]
snapshot['memory']=[{'label':'DDR5 16Gb · 9/24','value':'$57.667','change':'+0.29% 일간'},{'label':'DDR4 16Gb · 9/24','value':'$83.784','change':'-0.70% 일간'},{'label':'DDR4 8Gb · 9/24','value':'$46.107','change':'+0.47% 일간'}]
snapshot['scenarios']=[{'id':'base','label':'기본 · 45%','range':'KOSPI 6,800~6,950','summary':'전날 급락을 소화하며 6,900선 회복을 시도하지만 금리와 유가가 상단을 누른다.','conditions':['6,800 이상','6,950 이하','외국인 매도 급확대 없음'],'invalidation':'범위 이탈'},{'id':'bull','label':'강세 · 15%','range':'KOSPI 6,950 초과~7,100','summary':'외국인 현물과 프로그램 순매수가 함께 돌아서며 반도체 매도가 멈춘다.','conditions':['6,950 초과','외국인 현물 순매수','프로그램 전체 순매수'],'invalidation':'6,950 아래 재진입'},{'id':'bear','label':'약세 · 40%','range':'KOSPI 6,550~6,800 미만','summary':'금리·유가 부담과 메모리주 약세가 수급 매도와 겹친다.','conditions':['6,800 미만','외국인 현물 순매도','프로그램 전체 순매도'],'invalidation':'6,800 회복'}]
snapshot['strategyLevels']=[{'asset':'KOSPI','support':'6,800 / 6,550','pivot':'6,950','resistance':'7,100'},{'asset':'KODEX 레버리지','support':'106,000원','pivot':'109,370원','resistance':'112,000원'}]
snapshot['events']=[{'time':'9월 29일 22:00 KST','name':'미국 JOLTS','path':'미 국채금리와 달러'},{'time':'9월 30일 미국 장 마감 뒤','name':'Micron 실적','path':'메모리 수요와 AI 투자 기대'}]
for item in snapshot['technical']['instruments']:
    if item['id']=='KOSPI': levels, points = [6800,6950,7100], [num(kospi['openPrice']),num(kospi['highPrice']),num(kospi['lowPrice']),num(kospi['closePrice'])]
    elif item['id']=='KODEX': levels, points = [106000,109370,112000], [float(kodex['openPrice'].replace(',','')),float(kodex['highPrice'].replace(',','')),float(kodex['lowPrice'].replace(',','')),float(kodex['closePrice'].replace(',',''))]
    else: continue
    item.update(asOf='2026-09-28T15:30:00+09:00',asOfLabel='9월 28일 정규장 종가',levels=[{'label':label,'value':value} for label,value in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=f'1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}',points=[{'label':label,'value':value} for label,value in zip(['시가','고가','저가','종가'],points)])
dump('assets/data/market-dashboard-' + sid + '.json',snapshot); dump('assets/data/market-dashboard-latest.json',snapshot)
for path, css in (('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')):
    content=card(path,css); head,rest=content.split('</head>',1)
    for prop,value in [('og:title',TITLE),('og:description',SUMMARY),('twitter:title',TITLE),('twitter:description',SUMMARY)]: head=re.sub(r'(<meta (?:property|name)="'+re.escape(prop)+r'" content=")[^"]+',r'\g<1>'+value,head)
    head=re.sub(r'(<meta property="og:image(?::secure_url)?" content=")[^"]+',r'\g<1>https://www.hpmplab.com/assets/images/articles/'+IMAGE,head)
    head=re.sub(r'(<meta name="twitter:image" content=")[^"]+',r'\g<1>https://www.hpmplab.com/assets/images/articles/'+IMAGE,head)
    content=head+'</head>'+rest
    if path in ('index.html','articles/index.html'):
        categories=re.findall(r'<article class="[^\"]*article-card[^\"]*" data-category="([^\"]+)"',content)
        for category in ('all','market','essay','health'): content=re.sub(r'(data-category-count="'+category+r'">)\d+',r'\g<1>'+str(len(categories) if category=='all' else categories.count(category)),content)
    else:
        content=re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+',r'\g<1>market-2026-09-29.html',content)
        count=len(list((R/'articles').glob('market-*.html'))); content=re.sub(r'(일일시황 <span class="article-category-count">)\d+',r'\g<1>'+str(count),content); content=re.sub(r'(최신순 · )\d+(편)',r'\g<1>'+str(count)+r'\2',content)
    write(path,content)
sitemap=read('sitemap.xml').replace('</urlset>',f'<url><loc>{URL}</loc><lastmod>2026-09-29</lastmod><image:image><image:loc>https://www.hpmplab.com/assets/images/articles/{IMAGE}</image:loc></image:image></url>\n</urlset>')
for site_url in ('https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html'): sitemap=re.sub(r'(<loc>'+re.escape(site_url)+r'</loc>\s*<lastmod>)[^<]+',r'\g<1>2026-09-29',sitemap)
write('sitemap.xml',sitemap)

sessions=json.loads(read('research/evaluation/trading-sessions.json')); sessions.update(asOf=cutoff,source='Naver Finance KOSPI PREOPEN 2026-09-29; KRX 거래일',rawHash=evidence('KOSPI-basic')['rawHash']);
for date in ('2026-09-28','2026-09-29'):
    if date not in sessions['sessions']: sessions['sessions'].append(date)
sessions['sessions'].sort(); dump('research/evaluation/trading-sessions.json',sessions)
actual={'schemaVersion':1,'sessionDate':'2026-09-28','bizdate':'20260928','fetchedAt':cutoff,'marketStatus':'CLOSE','kospi':{'open':num(kospi['openPrice']),'high':num(kospi['highPrice']),'low':num(kospi['lowPrice']),'close':num(kospi['closePrice']),'asOf':'2026-09-28T15:30:00+09:00','source':evidence('KOSPI')['url'],'rawHash':evidence('KOSPI')['rawHash'],'rawPath':'research/evidence/2026-09-29/KOSPI.json'},'kodex':{'open':int(kodex['openPrice'].replace(',','')),'high':int(kodex['highPrice'].replace(',','')),'low':int(kodex['lowPrice'].replace(',','')),'close':int(kodex['closePrice'].replace(',','')),'volume':int(kodex['accumulatedTradingVolume']),'source':evidence('122630')['url'],'rawHash':evidence('122630')['rawHash']},'closeSnapshot':None,'closeSnapshotMissingReason':'15시 20분 정확 시각 외국인·프로그램·시장 폭 원문 부재. 종가로 소급하지 않음','flowTrajectory':None,'flowTrajectoryMissingEvidence':{'sourceStatus':'unavailable','source':evidence('KOSPI-integration')['url'],'asOf':'2026-09-28T15:30:00+09:00','fetchedAt':cutoff,'missingReason':'09:30·10:00·14:00·15:20 동일 시각 수급 앵커 원문 미확보','rawHash':evidence('KOSPI-integration')['rawHash']}}
dump('research/evaluation/actuals/2026-09-28.json',actual)
outcome={'schemaVersion':1,'forecastId':'2026-09-28-0821-same-close','recordedAt':cutoff,'actualRef':'2026-09-28','realizedScenario':'bear','errorCodes':['range_too_narrow_down'],'triggerResults':[{'id':'all','status':'unavailable','reason':'15시 20분 정확 시각 수급 원문 미확보'}],'driverAssessment':[{'id':'ai-capacity-contract','status':'rejected'},{'id':'long-yield','status':'confirmed'},{'id':'domestic-flow','status':'unavailable'}],'hypothesisTests':[]}
dump('research/evaluation/outcomes/2026-09-28-0821-same-close.json',outcome)
forecast={'schemaVersion':1,'forecastId':f'2026-09-29-{issued:%H%M}-same-close','visibility':'public','reportPath':'reports/2026-09-29.md','reportSha256':hashlib.sha256((R/'reports/2026-09-29.md').read_bytes()).hexdigest(),'issuedAt':issued.isoformat(),'dataCutoffAt':cutoff,'marketState':'preopen','marketRegime':'risk_off','evaluationBucket':'preopen','target':{'sessionDate':'2026-09-29','horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-09-28'},'reference':{'price':num(kospi['closePrice']),'asOf':'2026-09-28T15:30:00+09:00','kind':'previous_close'},'scenarios':{'bull':{'low':6950,'high':7100,'probability':.15},'base':{'low':6800,'high':6950,'probability':.45},'bear':{'low':6550,'high':6800,'probability':.40}},'closeEnvelopeCoverage':.9,'pathEnvelope':{'low':6450,'high':7100,'coverage':.9},'drivers':[{'id':'us-chip-risk-off','rank':1,'claim':'미국 반도체 약세가 국내 메모리주 장전 약세로 이어진다.','validationMetric':'SOXX·MU·삼성전자·SK하이닉스'},{'id':'oil-yield-pressure','rank':2,'claim':'유가 상승과 높은 장기금리가 6,950선 위 추격을 제한한다.','validationMetric':'Brent·미 10년물·KOSPI'},{'id':'domestic-flow','rank':3,'claim':'6,900선 회복은 외국인과 프로그램 수급의 동행이 확인해야 한다.','validationMetric':'외국인·프로그램·KOSPI'}],'scenarioTriggers':{'bull':{'logic':'AND','observeBy':'2026-09-29T15:20:00+09:00','conditions':[{'id':'bull-price','metricId':'kospi_price','operator':'gt','threshold':6950,'source':'Naver Finance KOSPI'},{'id':'bull-foreign','metricId':'foreign_cash','operator':'gt','threshold':0,'source':'Naver Finance KOSPI 수급 (억원)'},{'id':'bull-program','metricId':'program_total','operator':'gt','threshold':0,'source':'Naver Finance KOSPI 수급 (억원)'}]},'base':{'logic':'AND','observeBy':'2026-09-29T15:20:00+09:00','conditions':[{'id':'base-floor','metricId':'kospi_price','operator':'gte','threshold':6800,'source':'Naver Finance KOSPI'},{'id':'base-cap','metricId':'kospi_price','operator':'lte','threshold':6950,'source':'Naver Finance KOSPI'},{'id':'base-foreign','metricId':'foreign_cash','operator':'gte','threshold':-10000,'source':'Naver Finance KOSPI 수급 (억원)'}]},'bear':{'logic':'AND','observeBy':'2026-09-29T15:20:00+09:00','conditions':[{'id':'bear-price','metricId':'kospi_price','operator':'lt','threshold':6800,'source':'Naver Finance KOSPI'},{'id':'bear-foreign','metricId':'foreign_cash','operator':'lt','threshold':0,'source':'Naver Finance KOSPI 수급 (억원)'},{'id':'bear-program','metricId':'program_total','operator':'lt','threshold':0,'source':'Naver Finance KOSPI 수급 (억원)'}]}},'hypothesisTrials':[],'posture':{'attack':15,'wait':40,'defense':45},'supersedes':None}
forecast['contentHash']=hashlib.sha256(json.dumps(forecast,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(); dump('research/evaluation/forecasts/'+forecast['forecastId']+'.json',forecast)
dump('research/evidence/2026-09-29/seal.json',{'forecastId':forecast['forecastId'],'issuedAt':issued.isoformat(),'dataCutoffAt':cutoff,'snapshotId':sid})
write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 {issued.isoformat()}, 데이터 최종 확인 {cutoff}, 한국 장전.\n- 직전 KOSPI {num(kospi["closePrice"]):,.2f}({num(kospi["fluctuationsRatio"]):+.2f}%), KODEX {kodex["closePrice"]}원({kodex["fluctuationsRatio"]}%), 9월 28일 정규장.\n- 핵심: SOXX -2.08%, Micron -2.62%, 유가 상승과 미 장기금리 고점권이 장전 메모리주 약세와 겹친다. 전날 국내 하락폭은 중복 가산하지 않고 6,900선 회복과 수급 전환을 본다.\n- 대응 15/40/45. 기본 6800~6950(45%), 강세6950초과~7100(15%), 약세6550~6800미만(40%), 경로6450~7100(90%). KODEX 106000/109370/112000.\n- 보고서 reports/2026-09-29.md, 취재 research/notes/2026-09-29.md. 차트는 charts/us_yield_spreads_90d_2026-09-29.png 및 long_term.\n- 대시보드 assets/data/market-dashboard-{sid}.json 및 latest.json.\n- 다음: 9월 29일 22:00 KST JOLTS, 9월 30일 21:30 KST BEA GDP·개인소득 및 지출, Micron 실적.\n')
print(json.dumps({'forecastId':forecast['forecastId'],'issuedAt':issued.isoformat(),'dataCutoffAt':cutoff,'snapshotId':sid},ensure_ascii=False))
