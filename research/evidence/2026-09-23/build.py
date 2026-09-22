"""Publish the 2026-09-23 pre-open market brief from this run's frozen evidence."""
import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path

R = Path(__file__).resolve().parents[3]
E = Path(__file__).parent
TZ = dt.timezone(dt.timedelta(hours=9))
TITLE = '반도체는 한 번 더 올랐지만, KOSPI 7,150선은 수급을 기다린다'
SUMMARY = 'Micron 강세와 원화 강세가 장전 기대를 높였습니다. KOSPI 7,150선 돌파는 외국인·프로그램 수급이 확인해야 합니다.'
IMAGE = 'market-2026-09-23-memory-oil-relief.png'
ALT = '서울 아침빛 속 웨이퍼와 메모리 모듈, 청록 상승 흐름과 완화되는 유가 곡선'
URL = 'https://www.hpmplab.com/articles/market-2026-09-23.html'
_sealed = Path(__file__).with_name('seal.json')
ISSUED = dt.datetime.fromisoformat(json.loads(_sealed.read_text(encoding='utf-8'))['issuedAt']) if _sealed.exists() else dt.datetime.now(TZ).replace(microsecond=0)

def read(path):
    return (R / path).read_text(encoding='utf-8')

def write(path, value):
    (R / path).write_text(value, encoding='utf-8', newline='\n')

def dump(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def evidence(name):
    return json.loads((E / f'{name}.json').read_text(encoding='utf-8'))

def market(name):
    return evidence(f'yahoo-{name}')['data']['chart']['result'][0]['meta']

def stamp(name):
    return dt.datetime.fromtimestamp(market(name)['regularMarketTime'], TZ).isoformat()

def fmt(name):
    value = market(name)
    return f"{value['regularMarketPrice']:,.2f} · {value['regularMarketChangePercent']:+.2f}%"

def replace_old(value):
    pairs = {
        'market-2026-09-22-chip-rebound-foreign-flow-1200x630.webp': IMAGE,
        'market-2026-09-22.html': 'market-2026-09-23.html',
        'AI 반도체 급등과 원화 강세, KOSPI 7,000선은 지킬까': TITLE,
        'AI 반도체 급등과 원화 강세가 장전 기대를 높였습니다. KOSPI 7,000선 위 수급의 지속성이 관건입니다.': SUMMARY,
        '미국 반도체주가 유가·금리 하락에 반등했습니다. KOSPI 6,850선 돌파는 국내 외국인 수급이 가릅니다.': SUMMARY,
        '서울의 아침 빛 속 웨이퍼와 메모리 모듈, 푸른 반등과 흰 원화 흐름': ALT,
        '2026-09-22T08:08:48+09:00': ISSUED.isoformat(),
        '2026.09.18 · 08:08 KST': f'2026.09.23 · {ISSUED:%H:%M} KST',
        '2026.09.22 · 08:08 KST': f'2026.09.23 · {ISSUED:%H:%M} KST',
    }
    for old, new in pairs.items():
        value = value.replace(old, new)
    return value

def body_html(markdown):
    sections = markdown.split('\n\n')
    rendered = []
    for section in sections[1:]:
        if section.startswith('|'):
            rows = [line.strip('|').split('|') for line in section.splitlines() if not re.fullmatch(r'\|?[-| ]+\|?', line)]
            header, *items = rows
            table = '<table class="article-data-table"><thead><tr>' + ''.join(f'<th>{html.escape(x.strip())}</th>' for x in header) + '</tr></thead><tbody>'
            table += ''.join('<tr>' + ''.join(f'<td>{html.escape(x.strip())}</td>' for x in row) + '</tr>' for row in items)
            rendered.append('<div class="article-table-wrap">' + table + '</tbody></table></div>')
        else:
            rendered.append('<p>' + html.escape(section).replace('\n', '<br>') + '</p>')
    return '\n'.join(rendered)

def card(path, article_class):
    old = read(path)
    pattern = r'<article class="' + re.escape(article_class) + r'"[^>]*>.*?</article>'
    matches = list(re.finditer(pattern, old, re.S))
    source = next((match.group(0) for match in matches if 'market-2026-09-22' in match.group(0)), None)
    if not source:
        raise RuntimeError(f'card not found: {path}')
    fresh = replace_old(source)
    fresh = fresh.replace('9월 22일', '9월 23일').replace('2026년 9월 22일', '2026년 9월 23일')
    fresh = re.sub(r'<time datetime="[^"]+">[^<]+</time>', f'<time datetime="{ISSUED.isoformat()}">2026.09.23 · {ISSUED:%H:%M} KST</time>', fresh, count=1)
    inserted = False
    def replace(match):
        nonlocal inserted
        value = match.group(0)
        if 'market-2026-09-23' in value:
            return ''
        if not inserted and 'market-2026-09-22' in value:
            inserted = True
            return fresh + '\n' + value
        return value
    return re.sub(pattern, replace, old, flags=re.S)

def update_structured(value):
    def rewrite(match):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            return match.group(0)
        def visit(node):
            if isinstance(node, dict):
                if node.get('@type') == 'ItemList' and isinstance(node.get('itemListElement'), list) and node['itemListElement']:
                    clone = json.loads(json.dumps(node['itemListElement'][0], ensure_ascii=False))
                    clone = json.loads(replace_old(json.dumps(clone, ensure_ascii=False)))
                    node['itemListElement'].insert(0, clone)
                    for index, item in enumerate(node['itemListElement'], 1):
                        if isinstance(item, dict): item['position'] = index
                    node['numberOfItems'] = len(node['itemListElement'])
                for child in node.values(): visit(child)
            elif isinstance(node, list):
                for child in node: visit(child)
        visit(value)
        return '<script type="application/ld+json">' + json.dumps(value, ensure_ascii=False, indent=2) + '</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', rewrite, value, flags=re.S)

def main():
    cutoff = max(evidence(item)['fetchedAt'] for item in ('NXT', 'FX', 'yahoo-NQF', 'yahoo-ESF'))
    nxt = {item['itemCode']: item for item in evidence('NXT')['data']['datas']}
    fx = evidence('FX')['data']['exchangeInfo']
    if evidence('KOSPI-basic')['data']['marketStatus'] != 'PREOPEN':
        raise RuntimeError('KOSPI is not in PREOPEN')
    if any(not item['localTradedAt'].startswith('2026-09-23') for item in nxt.values()):
        raise RuntimeError('NXT snapshot date mismatch')
    manuscript = read('research/evidence/2026-09-23/manuscript.md')
    report_prices = ['\n## 장전 가격', '', '|항목|가격·변화|출처 시각|', '|---|---:|---|', '|KOSPI 전일 종가|7,017.91 · +0.15%|2026-09-22 정규장 종가|', '|KODEX 레버리지 전일 종가|114,400원 · +0.30%|2026-09-22 정규장 종가|']
    for code, label in (('005930', '삼성전자 NXT'), ('000660', 'SK하이닉스 NXT')):
        item = nxt[code]
        report_prices.append(f"|{label}|{item['closePrice']}원 · {item['fluctuationsRatio']}%|{item['localTradedAt']}|")
    report_prices += [f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|"]
    for name, label in (('NQF','Nasdaq100 선물'), ('ESF','S&P500 선물'), ('BZF','브렌트 선물'), ('CLF','WTI 선물')):
        report_prices.append(f'|{label}|{fmt(name)}|{stamp(name)} · 지연 시세|')
    report = '# 2026-09-23 KOSPI·KODEX 일일 리서치\n\n' + f'작성 {ISSUED.isoformat()} / 데이터 최종 확인 {cutoff} / 한국 장전.\n\n확정 사실은 출처 시각 기준, 시나리오와 확률은 조건부 전망이다.\n\n' + manuscript.split('\n', 1)[1].strip() + '\n' + '\n'.join(report_prices) + '\n\n## 취재 근거와 확인 시각\n\n' + read('research/evidence/2026-09-23/overnight-notes.md') + '\n\n![최근 90일](../charts/us_yield_spreads_90d_2026-09-22.png)\n\n![최근 2년](../charts/us_yield_spreads_long_term_2026-09-22.png)\n\n## 미국 정규장 종목별 확인\n\n|종목|9/22 종가|전일 대비|\n|---|---:|---:|\n'
    for ticker in ('QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'):
        item = market(ticker); report += f"|{ticker}|{item['regularMarketPrice']:.2f}|{item['regularMarketChangePercent']:+.2f}%|\n"
    write('reports/2026-09-23.md', report)
    old_article = read('articles/market-2026-09-22.html')
    prefix = replace_old(old_article.split('<article class="editorial-article reading-article">')[0]).replace('image/webp', 'image/png')
    suffix = old_article[old_article.index('</div></article></main>'):]
    header = f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{ISSUED.isoformat()}">2026.09.23 · {ISSUED:%H:%M} KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 {ISSUED:%H:%M} KST · 데이터 최종 확인 {cutoff}. 미국 정규장은 9월 22일, 국내 NXT·환율·미국 선물은 장전 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="{ALT}"></figure></header><div class="article-body" id="article-body">'
    charts = '<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_90d_2026-09-22.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 90일"><figcaption>FRED 최신 확정 관측일은 9월 21일이며, 9월 23일 장전 원고에서 참조했다.</figcaption></figure><figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_long_term_2026-09-22.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 2년"></figure>'
    write('articles/market-2026-09-23.html', prefix + header + body_html(manuscript) + charts + suffix)
    snapshot = json.loads(read('assets/data/market-dashboard-20260922-0808.json'))
    sid = ISSUED.strftime('%Y%m%d-%H%M')
    snapshot.update(snapshotId=sid, generatedAt=ISSUED.isoformat(), asOf=cutoff, asOfDisplay=cutoff, marketState='한국 장전', sourceLabel='미국 9월 22일 정규장 · 국내 9월 22일 종가 · 9월 23일 장전', latestArticle={'title':TITLE,'href':'market-2026-09-23.html'}, headline=TITLE, summary=SUMMARY)
    for item in snapshot['markets']:
        if item['id'] == 'KOSPI':
            item.update(value=7017.91, changePercent=.15, open=7161.61, high=7171.44, low=6986.27, previousClose=7007.72, asOf='2026-09-22T15:30:00+09:00', asOfLabel='9월 22일 종가', stateLabel='정규장 종가', flows=[])
    snapshot['stance']={'label':'7,150선 수급 확인','attack':30,'wait':50,'defense':20,'note':'반도체 강세가 외국인·프로그램 순매수로 이어지는지 봅니다.'}
    snapshot['checkpoints']=[{'label':'Nasdaq100 선물','value':fmt('NQF'),'detail':stamp('NQF')+' · 지연','tone':'info'},{'label':'원/달러','value':fx['closePrice']+'원','detail':fx['localTradedAt']+' 고시','tone':'positive'},{'label':'삼성전자 NXT','value':nxt['005930']['closePrice']+'원','detail':nxt['005930']['localTradedAt'],'tone':'info'},{'label':'SK하이닉스 NXT','value':nxt['000660']['closePrice']+'원','detail':nxt['000660']['localTradedAt'],'tone':'info'}]
    snapshot['factors']=[{'label':'미국 반도체','metric':'SOXX +2.40% · MU +5.00%','detail':'9월 22일 미국 정규장','tone':'positive'},{'label':'메모리 현물','metric':'DDR5 16Gb +0.41%','detail':'TrendForce 9월 22일','tone':'positive'},{'label':'유가','metric':'Brent 98.44달러 · -0.82%','detail':'지연 선물 시세','tone':'warning'}]
    snapshot['memory']=[{'label':'DDR5 16Gb · 9/22','value':'$57.167','change':'+0.41% 일간'},{'label':'DDR4 16Gb · 9/22','value':'$84.500','change':'-0.59% 일간'},{'label':'DDR4 8Gb · 9/22','value':'$46.036','change':'0.00% 일간'}]
    snapshot['scenarios']=[{'id':'base','label':'기본 · 50%','range':'KOSPI 7,000~7,150','summary':'반도체 강세를 반영하되 전날 장중 고점 부근에서는 수급 확인이 필요합니다.','conditions':['7,000 이상','7,150 이하','외국인 매도 확대 없음'],'invalidation':'7,000 이탈 또는 7,150 돌파'},{'id':'bull','label':'강세 · 30%','range':'KOSPI 7,150 초과~7,300','summary':'메모리주 강세와 외국인·프로그램 순매수가 함께 이어집니다.','conditions':['7,150 초과','외국인 현물 순매수','프로그램 전체 순매수'],'invalidation':'7,150 아래 재진입'},{'id':'bear','label':'약세 · 20%','range':'KOSPI 6,800~7,000 미만','summary':'차익 실현과 수급 매도가 장전 반도체 강세를 압도합니다.','conditions':['7,000 미만','외국인 현물 순매도','프로그램 전체 순매도'],'invalidation':'7,000 회복'}]
    snapshot['strategyLevels']=[{'asset':'KOSPI','support':'7,000 / 6,800','pivot':'7,150','resistance':'7,300'},{'asset':'KODEX 레버리지','support':'113,410원','pivot':'114,400원','resistance':'120,080원'}]
    snapshot['events']=[{'time':'9월 23일 09:00 KST','name':'한국 정규장 개장','path':'7,150선과 외국인·프로그램 수급'},{'time':'9월 24일 21:30 KST','name':'미국 신규 실업수당 청구','path':'미 국채금리와 달러'}]
    for item in snapshot['technical']['instruments']:
        if item['id'] == 'KOSPI':
            levels=[7000,7150,7300]; points=[7161.61,7171.44,6986.27,7017.91]
        elif item['id'] == 'KODEX':
            levels=[113410,114400,120080]; points=[119200,120080,113410,114400]
        else: continue
        item.update(asOf='2026-09-22T15:30:00+09:00',asOfLabel='9월 22일 정규장 종가',levels=[{'label':label,'value':value} for label,value in zip(['1차 지지','반등 기준','저항'], levels)],interpretation=f'1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}',points=[{'label':label,'value':value} for label,value in zip(['시가','고가','저가','종가'], points)])
    dump('assets/data/market-dashboard-' + sid + '.json', snapshot)
    dump('assets/data/market-dashboard-latest.json', snapshot)
    for path, cls in (('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')):
        content = update_structured(card(path, cls))
        head, rest = content.split('</head>', 1)
        head = re.sub(r'(<meta property="og:title" content=")[^"]+', r'\g<1>' + TITLE, head)
        head = re.sub(r'(<meta property="og:description" content=")[^"]+', r'\g<1>' + SUMMARY, head)
        head = re.sub(r'(<meta property="og:image(?::secure_url)?" content=")[^"]+', r'\g<1>https://www.hpmplab.com/assets/images/articles/' + IMAGE, head)
        head = re.sub(r'(<meta name="twitter:title" content=")[^"]+', r'\g<1>' + TITLE, head)
        head = re.sub(r'(<meta name="twitter:description" content=")[^"]+', r'\g<1>' + SUMMARY, head)
        head = re.sub(r'(<meta name="twitter:image" content=")[^"]+', r'\g<1>https://www.hpmplab.com/assets/images/articles/' + IMAGE, head)
        content = head + '</head>' + rest
        if path in ('index.html', 'articles/index.html'):
            categories = re.findall(r'<article class="[^\"]*article-card[^\"]*" data-category="([^"]+)"', content)
            for category in ('all', 'market', 'essay', 'health'):
                count = len(categories) if category == 'all' else categories.count(category)
                content = re.sub(r'(data-category-count="' + category + r'">)\d+', r'\g<1>' + str(count), content)
        if path == 'articles/market.html':
            content = re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+', r'\g<1>market-2026-09-23.html', content)
            market_count = len(list((R / 'articles').glob('market-*.html')))
            content = re.sub(r'(일일시황 <span class="article-category-count">)\d+', r'\g<1>' + str(market_count), content)
            content = re.sub(r'(최신순 · )\d+(편)', r'\g<1>' + str(market_count) + r'\2', content)
        write(path, content)
    sitemap = read('sitemap.xml').replace('</urlset>', f'<url><loc>{URL}</loc><lastmod>2026-09-23</lastmod><image:image><image:loc>https://www.hpmplab.com/assets/images/articles/{IMAGE}</image:loc></image:image></url>\n</urlset>')
    for site_url in ('https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html'):
        sitemap = re.sub(r'(<loc>' + re.escape(site_url) + r'</loc>\s*<lastmod>)[^<]+', r'\g<1>2026-09-23', sitemap)
    write('sitemap.xml', sitemap)
    sessions = json.loads(read('research/evaluation/trading-sessions.json'))
    sessions['asOf'] = cutoff; sessions['source'] = 'Naver Finance KOSPI PREOPEN 2026-09-23; KRX 거래일'; sessions['rawHash'] = evidence('KOSPI-basic')['rawHash']
    for day in ('2026-09-22','2026-09-23'):
        if day not in sessions['sessions']: sessions['sessions'].append(day)
    sessions['sessions'].sort(); dump('research/evaluation/trading-sessions.json', sessions)
    forecast = json.loads(read('research/evaluation/forecasts/2026-09-22-0808-same-close.json'))
    fid = f'2026-09-23-{ISSUED:%H%M}-same-close'
    forecast.update(forecastId=fid, reportPath='reports/2026-09-23.md', reportSha256=hashlib.sha256((R/'reports/2026-09-23.md').read_bytes()).hexdigest(), issuedAt=ISSUED.isoformat(), dataCutoffAt=cutoff, marketState='preopen', marketRegime='mixed', evaluationBucket='preopen', target={'sessionDate':'2026-09-23','horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-09-22'}, reference={'price':7017.91,'asOf':'2026-09-22T15:30:00+09:00','kind':'previous_close'}, scenarios={'bull':{'low':7150,'high':7300,'probability':.3},'base':{'low':7000,'high':7150,'probability':.5},'bear':{'low':6800,'high':7000,'probability':.2}}, pathEnvelope={'low':6750,'high':7350,'coverage':.9}, posture={'attack':30,'wait':50,'defense':20}, supersedes=None, drivers=[{'id':'memory-rally','rank':1,'claim':'Micron과 미국 반도체 강세가 국내 메모리주 장전 상승으로 전달된다.','validationMetric':'SOXX·MU·삼성전자·SK하이닉스'},{'id':'domestic-flow','rank':2,'claim':'7,150선 돌파는 외국인 현물과 프로그램 수급의 동행이 확인해야 한다.','validationMetric':'외국인·프로그램·KOSPI'},{'id':'oil-relief','rank':3,'claim':'Brent 하락이 성장주 할인율 부담을 일부 낮춘다.','validationMetric':'Brent·미 국채금리·KOSPI'}])
    thresholds={'bull-price':7150,'base-support':7000,'base-cap':7150,'bear-price':7000}
    for group in forecast['scenarioTriggers'].values():
        group['observeBy']='2026-09-23T15:20:00+09:00'
        for condition in group['conditions']:
            if condition['id'] in thresholds:
                condition['threshold']=thresholds[condition['id']]; condition['description']='KOSPI '+str(condition['threshold'])+' '+condition['operator']
    forecast.pop('contentHash', None)
    forecast['contentHash']=hashlib.sha256(json.dumps(forecast,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    dump('research/evaluation/forecasts/' + fid + '.json', forecast)
    dump('research/evidence/2026-09-23/seal.json', {'forecastId':fid,'issuedAt':ISSUED.isoformat(),'dataCutoffAt':cutoff,'snapshotId':sid})
    write('STATE.md', f'# KOSPI·KODEX 리서치 상태\n\n- 작성 {ISSUED.isoformat()}, 데이터 최종 확인 {cutoff}, 한국 장전.\n- 직전 KOSPI 7,017.91(+0.15%), KODEX 114,400원(+0.30%), 9월 22일 정규장.\n- 핵심: Micron +5.00%와 SOXX +2.40%, 원화 강세가 장전 반도체 기대를 지지한다. 전일 7,171.44 장중 고점의 소화 여부와 수급을 분리해 본다.\n- 대응 30/50/20. 기본 7000~7150(50%), 강세7150초과~7300(30%), 약세6800~7000미만(20%), 경로6750~7350(90%). KODEX 113410/114400/120080.\n- 보고서 reports/2026-09-23.md, 취재 research/evidence/2026-09-23/overnight-notes.md. 차트는 FRED 최신 확정치 charts/us_yield_spreads_90d_2026-09-22.png 및 long_term.\n- 대시보드 assets/data/market-dashboard-{sid}.json 및 latest.json.\n- 다음: 9월 24일 미국 신규 실업수당 청구·신규주택판매, 국내 추석 휴장 9월 24~25일.\n')
    print(json.dumps({'forecastId':fid,'issuedAt':ISSUED.isoformat(),'dataCutoffAt':cutoff,'snapshotId':sid},ensure_ascii=False))

if __name__ == '__main__':
    main()
