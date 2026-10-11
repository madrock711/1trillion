import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATE = '2026-10-12'
ISSUED = '2026-10-12T08:13:40+09:00'
CUTOFF = '2026-10-12T08:13:40+09:00'
PUBLISHED = '2026-10-12T08:13:40+09:00'
MODIFIED = '2026-10-12T08:13:40+09:00'
TITLE = '미국 반도체 급락의 월요일…KOSPI는 6,530선 수급부터'
SUMMARY = '미국 지수는 반등했지만 SOXX는 5% 밀렸습니다. AI 자금조달 우려와 메모리 수요를 분리해 보며 KOSPI 6,530선 수급을 확인해야 합니다.'
IMAGE = 'market-2026-10-12-ai-funding-memory-1200x630.png'
URL = 'https://www.hpmplab.com/articles/market-2026-10-12.html'
ALT = '서울의 밝은 새벽과 실리콘 웨이퍼 위 HBM 메모리, 청록과 금색으로 갈라지는 유리 자금 흐름'
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

article_body = '''<p>미국 지수는 반등했지만 반도체는 크게 밀렸다. 10월 9일 QQQ는 0.23% 올랐고 SOXX는 5.01%, SMH는 4.32% 하락했다. AI 인프라 투자 자금조달 부담이 다시 부각되며 Nvidia·AMD·Micron이 동반 약세를 보였다.</p>
<p>메모리의 중기 수요는 하루 주가와 분리해서 봐야 한다. TrendForce는 서버 DRAM 다년 계약과 HBM 중심의 생산능력 배분이 현물 거래를 조용하게 만들고 있다고 설명한다. 오늘 국내 메모리주는 이 중기 흐름보다 미국 반도체 ETF 낙폭과 정규장 수급의 영향을 먼저 받을 가능성이 크다.</p>
<p>직전 KRX 거래일 KOSPI는 6,625.93으로 2.61%, KODEX 레버리지는 5.44% 하락했다. 장전 NXT에서 삼성전자는 259,500원(-0.95%), SK하이닉스는 1,653,000원(-1.67%)이다. 제한된 유동성의 참고값이므로 개장 후에는 6,530선과 외국인·프로그램 수급을 함께 확인해야 한다.</p>
<p>기본 시나리오는 KOSPI 6,530~6,700, 확률 45%다. 6,700을 회복하고 외국인 현물과 프로그램이 동반 순매수로 돌아서면 6,700 초과~6,830의 강세 범위를 본다. 6,530 아래에서 두 수급이 함께 매도로 확대되면 6,360~6,530 미만의 약세 범위가 열린다.</p>
<p>KODEX 레버리지는 99,350원을 1차 지지, 101,400원을 반등 기준, 103,250원을 저항으로 둔다. 대응 점수는 공격 10, 관망 50, 방어 40이다.</p>
<div class="article-table-wrap"><table class="article-data-table"><thead><tr><th>종가 시나리오</th><th>범위·확률</th><th>15시 20분 확인 조건</th><th>전환 신호</th></tr></thead><tbody><tr><td>강세</td><td>6,700 초과~6,830 · 20%</td><td>6,700 상회 · 외국인·프로그램 동반 순매수</td><td>6,700 아래 재진입</td></tr><tr><td>기본</td><td>6,530~6,700 · 45%</td><td>6,530 이상 · 외국인 순매도 8천억원 미만</td><td>범위 이탈</td></tr><tr><td>약세</td><td>6,360~6,530 미만 · 35%</td><td>6,530 미만 · 외국인·프로그램 동반 순매도</td><td>6,530 회복</td></tr></tbody></table></div>'''

charts = '<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_90d_2026-10-12.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 90일"><figcaption>FRED 최신 금리차 관측일은 10월 9일이다.</figcaption></figure><figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_long_term_2026-10-12.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 2년"></figure>'

old_article = read('articles/market-2026-10-08.html')
prefix = old_article.split('<article class="editorial-article reading-article">')[0]
prefix = prefix.replace('market-2026-10-08.html', 'market-2026-10-12.html').replace('market-2026-10-08-fomc-yield-memory-1200x630.png', IMAGE)
prefix = re.sub(r'(<title>).*?( \| 연마</title>)', r'\1' + TITLE + r'\2', prefix)
prefix = re.sub(r'(<meta name="description" content=")[^"]+', r'\1' + SUMMARY, prefix)
for prop, value in [('og:title', TITLE), ('og:description', SUMMARY), ('twitter:title', TITLE), ('twitter:description', SUMMARY), ('article:published_time', PUBLISHED), ('article:modified_time', MODIFIED)]:
    prefix = re.sub(r'(<meta (?:property|name)="' + re.escape(prop) + r'" content=")[^"]+', r'\1' + value, prefix)
prefix = re.sub(r'2026-10-08T08:15:00\+09:00', ISSUED, prefix)
prefix = refresh_article_jsonld(prefix)
prefix = re.sub(r'<meta property="og:image:alt" content="[^"]+">', f'<meta property="og:image:alt" content="{ALT}">', prefix)
prefix = re.sub(r'\s*P26-10-08T08:29:25\+09:00">P26-10-08T08:33:38\+09:00"><meta property="article:section" content="시황분석">', f'\n    <meta property="article:published_time" content="{PUBLISHED}"><meta property="article:modified_time" content="{MODIFIED}"><meta property="article:section" content="시황분석">', prefix)
header = f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{PUBLISHED}">2026.10.12 · 작성·발행 08:13 KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성·발행 08:13 KST · 데이터 최종 확인 {CUTOFF}. 미국 정규장은 10월 9일, 국내 NXT·환율은 장전 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="{ALT}"></figure></header><div class="article-body" id="article-body">'
suffix = old_article[old_article.index('</div></article></main>'):]
write('articles/market-2026-10-12.html', prefix + header + article_body + charts + suffix)

def card(old, css, date_label):
    pat = r'<article class="' + re.escape(css) + r'"[^>]*>.*?</article>'
    matches = [match for match in re.finditer(pat, old, re.S) if 'market-2026-10-12.html' in match.group(0)]
    if matches:
        for match in reversed(matches[1:]):
            old = old[:match.start()] + old[match.end():]
        return old.replace('2026.10.12 · 08:05 KST', date_label).replace(ISSUED, PUBLISHED)
    item = next(x.group(0) for x in re.finditer(pat, old, re.S) if 'market-2026-10-08.html' in x.group(0))
    fresh = item.replace('market-2026-10-08.html', 'market-2026-10-12.html').replace('market-2026-10-08-fomc-yield-memory-1200x630.png', IMAGE).replace('FOMC 의사록이 다시 올린 금리 경계…KOSPI는 6,800선 수급부터', TITLE).replace('미국 반도체 ETF는 밀렸지만 Micron은 반등했습니다. 전일 대규모 순매도 뒤 KOSPI는 6,800선에서 수급을 먼저 확인해야 합니다.', SUMMARY).replace('2026-10-08T08:15:00+09:00', ISSUED).replace('2026-10-08T08:29:25+09:00', PUBLISHED).replace('2026.10.08 · 08:29 KST', date_label).replace('10월 8일', '10월 12일')
    return old.replace(item, fresh + '\n' + item, 1)

for page, css, label in [('index.html','article-card home-article-card','2026.10.12 · 08:13 KST'),('articles/index.html','article-card','2026.10.12 · 08:13 KST'),('articles/market.html','market-article-item','2026.10.12 · 08:13 KST')]:
    content = card(read(page), css, label)
    head, tail = content.split('</head>', 1)
    for prop, value in [('og:title', TITLE), ('og:description', SUMMARY), ('twitter:title', TITLE), ('twitter:description', SUMMARY)]:
        head = re.sub(r'(<meta (?:property|name)="' + re.escape(prop) + r'" content=")[^"]+', r'\1' + value, head)
    head = head.replace('market-2026-10-08-fomc-yield-memory-1200x630.png', IMAGE).replace('서울 아침빛과 데이터센터 서버, 푸른 빛의 컴퓨팅 흐름과 금빛 장기금리 곡선', ALT)
    content = head + '</head>' + tail
    if page == 'articles/market.html':
        content = re.sub(r'(<a class="market-dashboard-cta" id="market-latest-article-link" href=")[^"]+', r'\g<1>market-2026-10-12.html', content)
        content = re.sub(r'(<a class="market-dashboard-card market-summary-card" id="market-summary-article-link" href=")[^"]+', r'\g<1>market-2026-10-12.html', content)
        archive_pattern = r'<article class="market-article-item">.*?</article>'
        content = re.sub(r'(일일시황 <span class="article-category-count">)\d+', r'\g<1>52', content)
        content = re.sub(r'(발행일 기준 최신순 · )\d+(편)', r'\g<1>52\2', content)
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
snapshot.update(snapshotId='20261012-0813', generatedAt=ISSUED, asOf=CUTOFF, asOfDisplay=CUTOFF, marketState='한국 장전', sourceLabel='미국 10월 9일 정규장 · 국내 10월 8일 종가 · 10월 12일 장전', latestArticle={'title': TITLE,'href':'market-2026-10-12.html'}, headline=TITLE, summary=SUMMARY)
for item in snapshot['markets']:
    if item['id'] == 'KOSPI': item.update(value=6625.93,changePercent=-2.62,open=6808.68,high=6810.83,low=6625.93,previousClose=6803.90,asOf='2026-10-08T15:30:00+09:00',asOfLabel='10월 8일 종가',stateLabel='정규장 종가',flows=[])
snapshot['stance']={'label':'반도체 급락과 6,530선','attack':10,'wait':50,'defense':40,'note':'AI 자금조달 우려로 미국 반도체가 급락한 뒤 6,530선과 국내 수급을 확인한다.'}
snapshot['checkpoints']=[{'label':'WTI 최근 거래','value':'92.42달러 · +3.33%','detail':'2026-10-12T07:52:44+09:00','tone':'warning'},{'label':'원/달러','value':'1,341.31원 · -0.18%','detail':'2026-10-12T08:12:32+09:00','tone':'info'},{'label':'삼성전자 NXT','value':'259,000원 · -1.15%','detail':'2026-10-12T08:13:40+09:00','tone':'warning'},{'label':'SK하이닉스 NXT','value':'1,646,000원 · -2.08%','detail':'2026-10-12T08:13:40+09:00','tone':'warning'}]
snapshot['factors']=[{'label':'미국 기술주','metric':'QQQ +0.23% · NVDA -2.00%','detail':'10월 9일 미국 정규장','tone':'warning'},{'label':'미국 반도체','metric':'SOXX -5.01% · MU -4.27%','detail':'10월 9일 미국 정규장','tone':'warning'},{'label':'미 국채','metric':'10년-2년 +0.44%p','detail':'10월 9일 FRED 최신 관측','tone':'warning'},{'label':'직전 국내 종가','metric':'KOSPI -2.61% · KODEX -5.44%','detail':'10월 8일 정규장','tone':'warning'}]
snapshot['changes']=[{'label':'KOSPI','before':'6,803.90','after':'6,625.93','meaning':'10월 8일 KOSPI가 2.61% 하락했습니다.'},{'label':'미국 반도체','before':'SOXX +0.23%','after':'SOXX -5.01%','meaning':'AI 자금조달 우려로 10월 9일 반도체 ETF 낙폭이 확대됐습니다.'}]
snapshot['scenarios']=[{'id':'bull','label':'강세 · 20%','range':'KOSPI 6,700 초과~6,830','summary':'외국인·프로그램 동반 순매수 전환 구간이다.','conditions':['6,700 초과','외국인 현물 순매수','프로그램 전체 순매수'],'invalidation':'6,700 아래 재진입'},{'id':'base','label':'기본 · 45%','range':'KOSPI 6,530~6,700','summary':'6,530 방어와 순매도 둔화를 확인하는 구간이다.','conditions':['6,530 이상','6,700 이하','외국인 순매도 8천억원 미만'],'invalidation':'범위 이탈'},{'id':'bear','label':'약세 · 35%','range':'KOSPI 6,360~6,530 미만','summary':'미국 반도체 급락과 국내 매도가 겹치는 경우다.','conditions':['6,530 미만','외국인 현물 순매도','프로그램 전체 순매도'],'invalidation':'6,530 회복'}]
snapshot['strategyLevels']=[{'asset':'KOSPI','support':'6,530 / 6,360','pivot':'6,700','resistance':'6,830'},{'asset':'KODEX 레버리지','support':'99,350원','pivot':'101,400원','resistance':'103,250원'}]
snapshot['events']=[{'time':'10월 9일 미국 정규장','name':'AI 자금조달 우려와 반도체 ETF 급락','path':'AI 투자 수익화·성장주 할인율'},{'time':'10월 12일 장전','name':'유가 재상승과 국내 메모리주 NXT 약세','path':'수입물가·국내 수급'},{'time':'10월 14일 21:30 KST','name':'미국 9월 CPI','path':'인플레이션과 장기금리'}]
snapshot['checklist']=[{'id':'support','label':'KOSPI 6,530 방어'},{'id':'rebound','label':'6,700 회복과 외국인·프로그램 전환'},{'id':'flows','label':'삼성전자·SK하이닉스 정규장 회복 여부'}]
for item in snapshot['technical']['instruments']:
    if item['id']=='KOSPI': item.update(asOf='2026-10-08T15:30:00+09:00',asOfLabel='10월 8일 정규장 종가',points=[{'label':'시가','value':6808.68},{'label':'고가','value':6810.83},{'label':'저가','value':6625.93},{'label':'종가','value':6625.93}],levels=[{'label':'1차 지지','value':6530},{'label':'반등 기준','value':6700},{'label':'저항','value':6830}],interpretation='1차 지지 6,530 · 반등 기준 6,700 · 저항 6,830')
    if item['id']=='KODEX': item.update(asOf='2026-10-08T15:30:00+09:00',asOfLabel='10월 8일 정규장 종가',points=[{'label':'시가','value':106985},{'label':'고가','value':107475},{'label':'저가','value':101400},{'label':'종가','value':101400}],levels=[{'label':'1차 지지','value':99350},{'label':'반등 기준','value':101400},{'label':'저항','value':103250}],interpretation='1차 지지 99,350 · 반등 기준 101,400 · 저항 103,250')
snapshot['technical']['note']='10월 8일 확정 일봉과 10월 12일 장전 분석 기준선입니다.'
dump('assets/data/market-dashboard-20261012-0813.json',snapshot); dump('assets/data/market-dashboard-latest.json',snapshot)

actual={'schemaVersion':1,'sessionDate':'2026-10-08','bizdate':'20261008','fetchedAt':CUTOFF,'marketStatus':'CLOSE','kospi':{'open':None,'high':None,'low':None,'close':6625.93,'asOf':'2026-10-08T15:30:00+09:00','source':'https://m.stock.naver.com/api/index/KOSPI/basic','rawHash':'captured-20261012-preopen'},'kodex':{'open':106985,'high':107475,'low':101400,'close':101400,'volume':15532590,'source':'https://m.stock.naver.com/api/stock/122630/price?pageSize=5&page=1','rawHash':'captured-20261012-preopen'},'closeSnapshot':None,'closeSnapshotMissingReason':'15시 20분 정확 시각 외국인·프로그램·시장 폭 원문 미확보. 종가로 소급하지 않음','flowTrajectory':None,'flowTrajectoryMissingEvidence':{'sourceStatus':'unavailable','source':'https://m.stock.naver.com/api/index/KOSPI/integration','asOf':'2026-10-08T15:30:00+09:00','fetchedAt':CUTOFF,'missingReason':'09:30·10:00·14:00·15:20 동일 시각 수급 앵커 원문 미확보','rawHash':'captured-20261012-preopen'}}
dump('research/evaluation/actuals/2026-10-08.json',actual)
outcome={'schemaVersion':1,'forecastId':'2026-10-08-0815-same-close','recordedAt':CUTOFF,'actualRef':'2026-10-08','realizedScenario':'bear','errorCodes':['range_too_narrow_down'],'triggerResults':[{'id':'price','status':'confirmed','value':6625.93,'threshold':6730},{'id':'flows','status':'unavailable','reason':'15시 20분 정확 시각 수급 원문 미확보'}],'driverAssessment':[{'id':'fomc-yield-pressure','status':'confirmed'},{'id':'mixed-memory-signal','status':'not_confirmed'},{'id':'domestic-flow','status':'unavailable'}],'hypothesisTests':[]}
dump('research/evaluation/outcomes/2026-10-08-0815-same-close.json',outcome)
report_bytes = (ROOT / 'reports/2026-10-12.md').read_text(encoding='utf-8').encode('utf-8')
forecast={'schemaVersion':1,'forecastId':'2026-10-12-0805-same-close','visibility':'public','reportPath':'reports/2026-10-12.md','reportSha256':hashlib.sha256(report_bytes).hexdigest(),'issuedAt':ISSUED,'dataCutoffAt':CUTOFF,'marketState':'preopen','marketRegime':'risk-off','evaluationBucket':'preopen','target':{'sessionDate':DATE,'horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-10-08'},'reference':{'price':6625.93,'asOf':'2026-10-08T15:30:00+09:00','kind':'previous_close'},'scenarios':{'bull':{'low':6700,'high':6830,'probability':0.2},'base':{'low':6530,'high':6700,'probability':0.45},'bear':{'low':6360,'high':6530,'probability':0.35}},'closeEnvelopeCoverage':0.9,'pathEnvelope':{'low':6310,'high':6850,'coverage':0.9},'drivers':[{'id':'ai-financing-chip-selloff','rank':1,'claim':'AI 투자 자금조달 우려가 미국 반도체 ETF를 크게 눌렀다.','validationMetric':'SOXX·SMH·Nvidia·AMD·Micron'},{'id':'memory-contract-resilience','rank':2,'claim':'서버 DRAM 장기계약과 HBM 공급 제약은 중기 메모리 수요를 지지한다.','validationMetric':'TrendForce DDR5·DDR4 현물과 계약 코멘트'},{'id':'domestic-flow','rank':3,'claim':'6,700 회복은 외국인과 프로그램 수급의 동행이 필요하다.','validationMetric':'외국인·프로그램·KOSPI'}],'scenarioTriggers':{},'hypothesisTrials':[],'posture':{'attack':10,'wait':50,'defense':40},'supersedes':None}
for name,conds in {'bull':[('bull-price','kospi_price','gt',6700),('bull-foreign','foreign_cash','gt',0),('bull-program','program_total','gt',0)],'base':[('base-floor','kospi_price','gte',6530),('base-cap','kospi_price','lte',6700),('base-foreign','foreign_cash','gte',-8000)],'bear':[('bear-price','kospi_price','lt',6530),('bear-foreign','foreign_cash','lt',0),('bear-program','program_total','lt',0)]}.items():
    forecast['scenarioTriggers'][name]={'logic':'AND','observeBy':'2026-10-12T15:20:00+09:00','conditions':[{'id':i,'metricId':m,'operator':o,'threshold':t,'source':'Naver Finance KOSPI 수급' if 'cash' in m or 'program' in m else 'Naver Finance KOSPI','description':i} for i,m,o,t in conds]}
forecast['contentHash']=hashlib.sha256(json.dumps(forecast,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
dump('research/evaluation/forecasts/2026-10-12-0813-same-close.json',forecast)
write('STATE.md',f'''# KOSPI·KODEX 리서치 상태

- 작성 {ISSUED}, 데이터 최종 확인 {CUTOFF}, 한국 장전.
- 직전 KOSPI 6,625.93(-2.61%), KODEX 101,400원(-5.44%), 10월 8일 정규장.
- 핵심: AI 투자 자금조달 우려가 미국 반도체 ETF를 급락시켰다. 서버 DRAM 계약과 HBM 공급 제약은 중기 수요를 지지하지만, 국내 반등에는 6,700 회복과 외국인·프로그램 수급 전환이 필요하다.
- 대응 10/50/40. 기본 6,530~6,700(45%), 강세 6,700 초과~6,830(20%), 약세 6,360~6,530 미만(35%), 경로 6,310~6,850(90%). KODEX 99,350/101,400/103,250원.
- 보고서 reports/2026-10-12.md, 취재 research/notes/2026-10-12.md, 차트 charts/us_yield_spreads_*_2026-10-12.png.
- 대시보드 assets/data/market-dashboard-20261012-0813.json 및 latest.json.
- 다음: 10월 14일 21:30 KST 미국 9월 CPI, 10월 27~28일 FOMC.
- 직전 정산 research/evaluation/outcomes/2026-10-08-0815-same-close.json. 수급 앵커는 원문 미확보로 추정하지 않는다.
''')
print(json.dumps({'forecastId':forecast['forecastId'],'contentHash':forecast['contentHash']},ensure_ascii=False))
