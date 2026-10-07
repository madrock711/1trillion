import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATE = '2026-10-08'
ISSUED = '2026-10-08T08:15:00+09:00'
CUTOFF = '2026-10-08T08:14:07+09:00'
PUBLISHED = '2026-10-08T08:29:25+09:00'
MODIFIED = '2026-10-08T08:33:38+09:00'
TITLE = 'FOMC 의사록이 다시 올린 금리 경계…KOSPI는 6,800선 수급부터'
SUMMARY = '미국 반도체 ETF는 밀렸지만 Micron은 반등했습니다. 전일 대규모 순매도 뒤 KOSPI는 6,800선에서 수급을 먼저 확인해야 합니다.'
IMAGE = 'market-2026-10-08-fomc-yield-memory-1200x630.png'
URL = 'https://www.hpmplab.com/articles/market-2026-10-08.html'
ALT = '서울 새벽 하늘 아래 청록 실리콘 웨이퍼와 HBM 메모리, 유리처럼 빛나는 금리 곡선'

def read(name): return (ROOT / name).read_text(encoding='utf-8')
def write(name, value): (ROOT / name).write_text(value, encoding='utf-8', newline='\n')
def dump(name, value): write(name, json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def refresh_collection_jsonld(content):
    def replace(match):
        node = json.loads(match.group(1))
        collection = next((item for item in node.get('@graph', []) if item.get('@type') == 'CollectionPage'), None)
        if not collection:
            return match.group(0)
        entity = collection.get('mainEntity', {})
        items = entity.get('itemListElement', [])
        current = next((item for item in items if item.get('url') == URL), None)
        if current is None:
            current = {'@type':'ListItem','position':1,'url':URL}
            items.insert(0, current)
        current.update({'name':TITLE,'description':SUMMARY,'datePublished':PUBLISHED,'dateModified':MODIFIED,'image':{'@type':'ImageObject','url':'https://www.hpmplab.com/assets/images/articles/' + IMAGE}})
        current_items = [item for item in items if item.get('url') == URL]
        for item in current_items[1:]: items.remove(item)
        prior_url = 'https://www.hpmplab.com/articles/market-2026-10-07.html'
        if not any(item.get('url') == prior_url for item in items):
            items.insert(1, {'@type':'ListItem','position':2,'url':prior_url,'name':'미국은 신고가, 국내 메모리주는 장전 약세…KOSPI는 6,940선 확인부터','description':'유가와 금리 완화는 미국 신고가를 이끌었지만, 반도체 ETF와 국내 메모리 장전 호가는 약합니다. KOSPI는 6,940선의 수급을 먼저 봐야 합니다.','datePublished':'2026-10-07T08:18:19+09:00','dateModified':'2026-10-07T08:18:19+09:00','image':{'@type':'ImageObject','url':'https://www.hpmplab.com/assets/images/articles/market-2026-10-07-yield-oil-memory-1200x630.png'}})
        prior_items = [item for item in items if item.get('url') == prior_url]
        for item in prior_items[1:]: items.remove(item)
        for index, item in enumerate(items, 1): item['position'] = index
        entity['itemListElement'] = items
        entity['numberOfItems'] = len(items)
        collection['mainEntity'] = entity
        return '<script type="application/ld+json">' + json.dumps(node, ensure_ascii=False, indent=2) + '</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', replace, content, flags=re.S)

def refresh_article_jsonld(content):
    def replace(match):
        node = json.loads(match.group(1))
        if node.get('@type') != 'Article':
            return match.group(0)
        node.update({
            'headline': TITLE,
            'description': SUMMARY,
            'image': {'@type': 'ImageObject', 'url': 'https://www.hpmplab.com/assets/images/articles/' + IMAGE, 'width': 1200, 'height': 630},
            'datePublished': PUBLISHED,
            'dateModified': MODIFIED,
            'mainEntityOfPage': URL,
        })
        return '<script type="application/ld+json">' + json.dumps(node, ensure_ascii=False, separators=(',', ':')) + '</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', replace, content, flags=re.S)

article_body = '''<p>10월 7일 미국 시장은 금리가 다시 중심에 섰다. 9월 FOMC 의사록에서 연준은 인플레이션 상방 위험을 경계했고, 일부 참가자는 에너지 충격과 AI 수요에서 나온 가격 압력이 더 넓게 번지지 않도록 높은 금리가 필요하다고 봤다. 장기금리가 올라가자 QQQ는 0.25%, SOXX는 1.13%, SMH는 1.18% 내렸다.</p>
<p>반도체 전체가 같은 방향으로 움직인 것은 아니다. Micron은 4.06% 반등했고 Broadcom도 0.19% 올랐다. 반면 Nvidia는 0.74%, AMD는 0.55% 하락했다. 메모리 수요의 중기 흐름과 당일 ETF 수급을 같은 신호로 읽으면 안 되는 장면이다.</p>
<p>국내장은 이미 수급 충격을 한 차례 겪었다. KOSPI는 10월 7일 6,803.90으로 1.98% 하락했다. 장중 6,977.77까지 올랐지만 6,803.81까지 밀렸고, 외국인 현물은 2조6,188억원, 프로그램 전체는 1조9,315억원 순매도였다. 삼성전자는 1.10%, SK하이닉스는 3.27% 내렸고 KODEX 레버리지는 4.09% 하락했다.</p>
<p>장전 NXT의 삼성전자 273,000원, SK하이닉스 1,740,000원은 전일 종가보다 각각 1.68%, 0.99% 높다. 이 가격만으로 전일 매도 압력이 끝났다고 보기 어렵다. 정규장에서는 6,800선 회복과 외국인·프로그램 매도 둔화가 먼저 나와야 한다.</p>
<p>기본 시나리오는 KOSPI 6,730~6,860, 확률 50%다. 6,730을 지키고 외국인 순매도가 1조원 아래로 줄어드는 구간이다. 6,860을 넘은 뒤 외국인 현물과 프로그램이 함께 순매수로 돌아서면 6,860 초과~6,990의 강세 범위를 본다. 6,730 아래에서 두 수급이 다시 매도로 기울면 6,580~6,730 미만의 약세 범위가 열린다.</p>
<p>KODEX 레버리지는 107,175원을 1차 지지, 107,230원을 반등 기준, 109,475원을 저항으로 둔다. 대응 점수는 공격 15, 관망 55, 방어 30이다.</p>
<div class="article-table-wrap"><table class="article-data-table"><thead><tr><th>종가 시나리오</th><th>범위·확률</th><th>15시 20분 확인 조건</th><th>전환 신호</th></tr></thead><tbody><tr><td>강세</td><td>6,860 초과~6,990 · 20%</td><td>6,860 상회 · 외국인·프로그램 동반 순매수</td><td>6,860 아래 재진입</td></tr><tr><td>기본</td><td>6,730~6,860 · 50%</td><td>6,730 이상 · 외국인 순매도 1조원 미만</td><td>범위 이탈</td></tr><tr><td>약세</td><td>6,580~6,730 미만 · 30%</td><td>6,730 미만 · 외국인·프로그램 동반 순매도</td><td>6,730 회복</td></tr></tbody></table></div>'''

charts = '<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_90d_2026-10-08.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 90일"><figcaption>FRED 최신 금리차 관측일은 10월 7일이다.</figcaption></figure><figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_long_term_2026-10-08.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 2년"></figure>'

old_article = read('articles/market-2026-10-07.html')
prefix = old_article.split('<article class="editorial-article reading-article">')[0]
prefix = prefix.replace('market-2026-10-07.html', 'market-2026-10-08.html').replace('market-2026-10-07-yield-oil-memory-1200x630.png', IMAGE)
prefix = re.sub(r'(<title>).*?( \| 연마</title>)', r'\1' + TITLE + r'\2', prefix)
prefix = re.sub(r'(<meta name="description" content=")[^"]+', r'\1' + SUMMARY, prefix)
for prop, value in [('og:title', TITLE), ('og:description', SUMMARY), ('twitter:title', TITLE), ('twitter:description', SUMMARY), ('article:published_time', PUBLISHED), ('article:modified_time', MODIFIED)]:
    prefix = re.sub(r'(<meta (?:property|name)="' + re.escape(prop) + r'" content=")[^"]+', r'\1' + value, prefix)
prefix = re.sub(r'2026-10-07T08:18:19\+09:00', ISSUED, prefix)
prefix = refresh_article_jsonld(prefix)
header = f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{PUBLISHED}">2026.10.08 · 작성 08:15 · 발행 08:29 KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 08:15 KST · 데이터 최종 확인 {CUTOFF} · 최초 발행 08:29 KST. 미국 정규장은 10월 7일, 국내 NXT·환율·미국 선물은 장전 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="{ALT}"></figure></header><div class="article-body" id="article-body">'
suffix = old_article[old_article.index('</div></article></main>'):]
write('articles/market-2026-10-08.html', prefix + header + article_body + charts + suffix)

def card(old, css, date_label):
    pat = r'<article class="' + re.escape(css) + r'"[^>]*>.*?</article>'
    matches = [match for match in re.finditer(pat, old, re.S) if 'market-2026-10-08.html' in match.group(0)]
    if matches:
        for match in reversed(matches[1:]):
            old = old[:match.start()] + old[match.end():]
        return old.replace('2026.10.08 · 08:09 KST', date_label).replace('2026.10.08 · 08:15 KST', date_label).replace('2026-10-08T08:09:00+09:00', PUBLISHED).replace(ISSUED, PUBLISHED)
    item = next(x.group(0) for x in re.finditer(pat, old, re.S) if 'market-2026-10-07.html' in x.group(0))
    fresh = item.replace('market-2026-10-07.html', 'market-2026-10-08.html').replace('market-2026-10-07-yield-oil-memory-1200x630.png', IMAGE).replace('미국은 신고가, 국내 메모리주는 장전 약세…KOSPI는 6,940선 확인부터', TITLE).replace('유가와 금리 완화는 미국 신고가를 이끌었지만, 반도체 ETF와 국내 메모리 장전 호가는 약합니다. KOSPI는 6,940선의 수급을 먼저 봐야 합니다.', SUMMARY).replace('2026-10-07T08:16:11+09:00', ISSUED).replace('2026.10.07 · 08:16 KST', date_label).replace('10월 7일', '10월 8일')
    return old.replace(item, fresh + '\n' + item, 1)

for page, css, label in [('index.html','article-card home-article-card','2026.10.08 · 08:29 KST'),('articles/index.html','article-card','2026.10.08 · 08:29 KST'),('articles/market.html','market-article-item','2026.10.08 · 08:29 KST')]:
    content = card(read(page), css, label)
    head, tail = content.split('</head>', 1)
    for prop, value in [('og:title', TITLE), ('og:description', SUMMARY), ('twitter:title', TITLE), ('twitter:description', SUMMARY)]:
        head = re.sub(r'(<meta (?:property|name)="' + re.escape(prop) + r'" content=")[^"]+', r'\1' + value, head)
    content = head + '</head>' + tail
    if page == 'articles/market.html':
        archive_pattern = r'<article class="market-article-item">.*?</article>'
        if not any('market-2026-10-07.html' in match.group(0) for match in re.finditer(archive_pattern, content, re.S)):
            latest = next(match.group(0) for match in re.finditer(archive_pattern, content, re.S) if 'market-2026-10-08.html' in match.group(0))
            prior = latest.replace('market-2026-10-08.html', 'market-2026-10-07.html').replace(IMAGE, 'market-2026-10-07-yield-oil-memory-1200x630.png').replace(TITLE, '미국은 신고가, 국내 메모리주는 장전 약세…KOSPI는 6,940선 확인부터').replace(SUMMARY, '유가와 금리 완화는 미국 신고가를 이끌었지만, 반도체 ETF와 국내 메모리 장전 호가는 약합니다. KOSPI는 6,940선의 수급을 먼저 봐야 합니다.').replace('2026-10-08T08:15:00+09:00', '2026-10-07T08:18:19+09:00').replace('2026.10.08 · 08:15 KST', '2026.10.07 · 08:18 KST').replace('10월 8일', '10월 7일')
            content = content.replace(latest, latest + '\n' + prior, 1)
        content = re.sub(r'(일일시황 <span class="article-category-count">)\d+', r'\g<1>51', content)
        content = re.sub(r'(발행일 기준 최신순 · )\d+(편)', r'\g<1>51\2', content)
    else:
        categories = re.findall(r'<article class="article-card(?: home-article-card)?" data-category="([^"]+)"', content)
        for category in ('all', 'essay', 'market', 'health'):
            count = len(categories) if category == 'all' else categories.count(category)
            content = re.sub(r'(data-category-count="' + category + r'">)\d+', r'\g<1>' + str(count), content)
        content = refresh_collection_jsonld(content)
    write(page, content)

sitemap = read('sitemap.xml')
if URL not in sitemap:
    sitemap = sitemap.replace('</urlset>', f'<url><loc>{URL}</loc><lastmod>{DATE}</lastmod><image:image><image:loc>https://www.hpmplab.com/assets/images/articles/{IMAGE}</image:loc></image:image></url>\n</urlset>')
for site_url in ('https://www.hpmplab.com/', 'https://www.hpmplab.com/articles/', 'https://www.hpmplab.com/articles/market.html'):
    sitemap = re.sub(r'(<loc>' + re.escape(site_url) + r'</loc>\s*<lastmod>)[^<]+', r'\g<1>' + DATE, sitemap)
write('sitemap.xml', sitemap)

snapshot = json.loads(read('assets/data/market-dashboard-latest.json'))
snapshot.update(snapshotId='20261008-0815', generatedAt=ISSUED, asOf=CUTOFF, asOfDisplay=CUTOFF, marketState='한국 장전', sourceLabel='미국 10월 7일 정규장 · 국내 10월 7일 종가 · 10월 8일 장전', latestArticle={'title': TITLE,'href':'market-2026-10-08.html'}, headline=TITLE, summary=SUMMARY)
for item in snapshot['markets']:
    if item['id'] == 'KOSPI': item.update(value=6803.90,changePercent=-1.98,open=6864.25,high=6977.77,low=6803.81,previousClose=6941.39,asOf='2026-10-07T15:30:00+09:00',asOfLabel='10월 7일 종가',stateLabel='정규장 종가',flows=[])
snapshot['stance']={'label':'6,800선과 수급 공백','attack':15,'wait':55,'defense':30,'note':'장기금리 경계와 전일 대규모 순매도 뒤 6,800선 수급을 확인한다.'}
snapshot['checkpoints']=[{'label':'S&P500 선물','value':'7,853.25 · +0.01%','detail':'2026-10-08T07:47:09+09:00 · 지연','tone':'info'},{'label':'원/달러','value':'1,341.00원','detail':'2026-10-08T07:09:29+09:00 하나은행 고시','tone':'warning'},{'label':'삼성전자 NXT','value':'273,000원 · +1.68%','detail':'2026-10-08T08:13:59+09:00','tone':'positive'},{'label':'SK하이닉스 NXT','value':'1,740,000원 · +0.99%','detail':'2026-10-08T08:14:07+09:00','tone':'positive'}]
snapshot['factors']=[{'label':'미국 기술주','metric':'QQQ -0.25% · NVDA -0.74%','detail':'10월 7일 미국 정규장','tone':'warning'},{'label':'미국 반도체','metric':'SOXX -1.13% · MU +4.06%','detail':'10월 7일 미국 정규장','tone':'warning'},{'label':'미 국채','metric':'10년-2년 +0.51%p','detail':'10월 7일 FRED 최신 관측','tone':'warning'},{'label':'전일 국내 수급','metric':'외국인 -2.62조원 · 프로그램 -1.93조원','detail':'10월 7일 정규장','tone':'warning'}]
snapshot['changes']=[{'label':'KOSPI','before':'6,941.39','after':'6,803.90','meaning':'10월 7일 외국인·프로그램 동반 순매도 속 1.98% 하락했습니다.'},{'label':'미국 반도체','before':'SOXX -0.01%','after':'SOXX -1.13%','meaning':'FOMC 의사록 뒤 장기금리 경계가 다시 커졌습니다.'}]
snapshot['scenarios']=[{'id':'bull','label':'강세 · 20%','range':'KOSPI 6,860 초과~6,990','summary':'외국인·프로그램 동반 순매수 전환 구간이다.','conditions':['6,860 초과','외국인 현물 순매수','프로그램 전체 순매수'],'invalidation':'6,860 아래 재진입'},{'id':'base','label':'기본 · 50%','range':'KOSPI 6,730~6,860','summary':'6,730 방어와 순매도 둔화를 확인하는 구간이다.','conditions':['6,730 이상','6,860 이하','외국인 순매도 1조원 미만'],'invalidation':'범위 이탈'},{'id':'bear','label':'약세 · 30%','range':'KOSPI 6,580~6,730 미만','summary':'전일 매도 압력이 다시 확대되는 경우다.','conditions':['6,730 미만','외국인 현물 순매도','프로그램 전체 순매도'],'invalidation':'6,730 회복'}]
snapshot['strategyLevels']=[{'asset':'KOSPI','support':'6,730 / 6,580','pivot':'6,860','resistance':'6,990'},{'asset':'KODEX 레버리지','support':'107,175원','pivot':'107,230원','resistance':'109,475원'}]
snapshot['events']=[{'time':'10월 7일 미국 정규장','name':'FOMC 의사록과 장기금리 경계','path':'성장주 할인율과 반도체 수급'},{'time':'10월 8일 08:00 KST','name':'한국 8월 경상수지','path':'원/달러와 수출 흐름'},{'time':'10월 14일 21:30 KST','name':'미국 9월 CPI','path':'인플레이션과 장기금리'}]
snapshot['checklist']=[{'id':'support','label':'KOSPI 6,730 방어'},{'id':'rebound','label':'6,860 회복과 메모리 동반 강세'},{'id':'flows','label':'외국인·프로그램 수급 동행 여부'}]
for item in snapshot['technical']['instruments']:
    if item['id']=='KOSPI': item.update(asOf='2026-10-07T15:30:00+09:00',asOfLabel='10월 7일 정규장 종가',points=[{'label':'시가','value':6864.25},{'label':'고가','value':6977.77},{'label':'저가','value':6803.81},{'label':'종가','value':6803.90}],levels=[{'label':'1차 지지','value':6730},{'label':'반등 기준','value':6860},{'label':'저항','value':6990}],interpretation='1차 지지 6,730 · 반등 기준 6,860 · 저항 6,990')
    if item['id']=='KODEX': item.update(asOf='2026-10-07T15:30:00+09:00',asOfLabel='10월 7일 정규장 종가',points=[{'label':'시가','value':109475},{'label':'고가','value':113430},{'label':'저가','value':107175},{'label':'종가','value':107230}],levels=[{'label':'1차 지지','value':107175},{'label':'반등 기준','value':107230},{'label':'저항','value':109475}],interpretation='1차 지지 107,175 · 반등 기준 107,230 · 저항 109,475')
snapshot['technical']['note']='10월 7일 확정 일봉과 10월 8일 장전 분석 기준선입니다.'
dump('assets/data/market-dashboard-20261008-0815.json',snapshot); dump('assets/data/market-dashboard-latest.json',snapshot)

actual={'schemaVersion':1,'sessionDate':'2026-10-07','bizdate':'20261007','fetchedAt':CUTOFF,'marketStatus':'CLOSE','kospi':{'open':6864.25,'high':6977.77,'low':6803.81,'close':6803.90,'asOf':'2026-10-07T15:30:00+09:00','source':'https://m.stock.naver.com/api/index/KOSPI/basic','rawHash':'captured-20261008-preopen'},'kodex':{'open':109475,'high':113430,'low':107175,'close':107230,'volume':12955432,'source':'https://m.stock.naver.com/api/stock/122630/price?pageSize=5&page=1','rawHash':'captured-20261008-preopen'},'closeSnapshot':None,'closeSnapshotMissingReason':'15시 20분 정확 시각 외국인·프로그램·시장 폭 원문 부재. 종가로 소급하지 않음','flowTrajectory':None,'flowTrajectoryMissingEvidence':{'sourceStatus':'unavailable','source':'https://m.stock.naver.com/api/index/KOSPI/integration','asOf':'2026-10-07T15:30:00+09:00','fetchedAt':CUTOFF,'missingReason':'09:30·10:00·14:00·15:20 동일 시각 수급 앵커 원문 미확보','rawHash':'captured-20261008-preopen'}}
dump('research/evaluation/actuals/2026-10-07.json',actual)
outcome={'schemaVersion':1,'forecastId':'2026-10-07-0818-same-close','recordedAt':CUTOFF,'actualRef':'2026-10-07','realizedScenario':'bear','errorCodes':['range_too_narrow_down'],'triggerResults':[{'id':'price','status':'confirmed','value':6803.90,'threshold':6880},{'id':'flows','status':'unavailable','reason':'15시 20분 정확 시각 수급 원문 미확보'}],'driverAssessment':[{'id':'us-record-yields','status':'not_confirmed'},{'id':'selective-chip-signal','status':'confirmed'},{'id':'domestic-flow','status':'unavailable'}],'hypothesisTests':[]}
dump('research/evaluation/outcomes/2026-10-07-0818-same-close.json',outcome)
report_bytes = (ROOT / 'reports/2026-10-08.md').read_text(encoding='utf-8').encode('utf-8')
forecast={'schemaVersion':1,'forecastId':'2026-10-08-0815-same-close','visibility':'public','reportPath':'reports/2026-10-08.md','reportSha256':hashlib.sha256(report_bytes).hexdigest(),'issuedAt':ISSUED,'dataCutoffAt':CUTOFF,'marketState':'preopen','marketRegime':'risk-off','evaluationBucket':'preopen','target':{'sessionDate':DATE,'horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-10-07'},'reference':{'price':6803.90,'asOf':'2026-10-07T15:30:00+09:00','kind':'previous_close'},'scenarios':{'bull':{'low':6860,'high':6990,'probability':0.2},'base':{'low':6730,'high':6860,'probability':0.5},'bear':{'low':6580,'high':6730,'probability':0.3}},'closeEnvelopeCoverage':0.9,'pathEnvelope':{'low':6550,'high':7000,'coverage':0.9},'drivers':[{'id':'fomc-yield-pressure','rank':1,'claim':'FOMC 의사록과 장기금리 경계가 성장주·반도체 ETF를 누른다.','validationMetric':'QQQ·SOXX·미국 10년물'},{'id':'mixed-memory-signal','rank':2,'claim':'Micron 반등은 메모리 수요를 받치지만 국내 반등에는 수급 전환이 필요하다.','validationMetric':'Micron·삼성전자·SK하이닉스·KOSPI'},{'id':'domestic-flow','rank':3,'claim':'6,860 회복은 외국인과 프로그램 수급의 동행이 필요하다.','validationMetric':'외국인·프로그램·KOSPI'}],'scenarioTriggers':{},'hypothesisTrials':[],'posture':{'attack':15,'wait':55,'defense':30},'supersedes':None}
for name,conds in {'bull':[('bull-price','kospi_price','gt',6860),('bull-foreign','foreign_cash','gt',0),('bull-program','program_total','gt',0)],'base':[('base-floor','kospi_price','gte',6730),('base-cap','kospi_price','lte',6860),('base-foreign','foreign_cash','gte',-10000)],'bear':[('bear-price','kospi_price','lt',6730),('bear-foreign','foreign_cash','lt',0),('bear-program','program_total','lt',0)]}.items():
    forecast['scenarioTriggers'][name]={'logic':'AND','observeBy':'2026-10-08T15:20:00+09:00','conditions':[{'id':i,'metricId':m,'operator':o,'threshold':t,'source':'Naver Finance KOSPI 수급' if 'cash' in m or 'program' in m else 'Naver Finance KOSPI','description':i} for i,m,o,t in conds]}
forecast['contentHash']=hashlib.sha256(json.dumps(forecast,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
dump('research/evaluation/forecasts/2026-10-08-0815-same-close.json',forecast)
write('STATE.md',f'''# KOSPI·KODEX 리서치 상태

- 작성 {ISSUED}, 데이터 최종 확인 {CUTOFF}, 한국 장전.
- 직전 KOSPI 6,803.90(-1.98%), KODEX 107,230원(-4.09%), 10월 7일 정규장.
- 핵심: FOMC 의사록과 장기금리 경계가 미국 반도체 ETF를 눌렀다. Micron 반등은 메모리 수요의 중기 버팀목이지만, 국내 반등에는 6,800선과 외국인·프로그램 수급 전환이 필요하다.
- 대응 15/55/30. 기본 6,730~6,860(50%), 강세 6,860 초과~6,990(20%), 약세 6,580~6,730 미만(30%), 경로 6,550~7,000(90%). KODEX 107,175/107,230/109,475원.
- 보고서 reports/2026-10-08.md, 취재 research/notes/2026-10-08.md, 차트 charts/us_yield_spreads_*_2026-10-08.png.
- 대시보드 assets/data/market-dashboard-20261008-0815.json 및 latest.json.
- 다음: 10월 8일 08:00 KST 한국 8월 경상수지, 10월 14일 21:30 KST 미국 9월 CPI.
- 직전 정산 research/evaluation/outcomes/2026-10-07-0818-same-close.json. 수급 앵커는 원문 미확보로 추정하지 않는다.
''')
print(json.dumps({'forecastId':forecast['forecastId'],'contentHash':forecast['contentHash']},ensure_ascii=False))
