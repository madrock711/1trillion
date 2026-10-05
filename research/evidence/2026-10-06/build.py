import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).parent
TZ = dt.timezone(dt.timedelta(hours=9))
DATE = "2026-10-06"
TITLE = "나스닥은 올랐지만, KOSPI 7,000선 위는 수급이 답한다"
SUMMARY = "원화 강세와 장전 메모리주 상승이 하단을 받치지만, 반도체 신호가 엇갈려 7,000선 위는 국내 수급을 확인해야 합니다."
IMAGE = "market-2026-10-06-nasdaq-memory-won-1200x630.png"
URL = "https://www.hpmplab.com/articles/market-2026-10-06.html"
ALT = "서울 아침 아래 HBM 메모리와 실리콘 웨이퍼, 데이터센터와 완만한 상승선"

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def write(path, text):
    (ROOT / path).write_text(text, encoding="utf-8", newline="\n")

def dump(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def evidence(name):
    return json.loads((EVIDENCE / f"{name}.json").read_text(encoding="utf-8"))

def market(name):
    return evidence(f"yahoo-{name}")["data"]["chart"]["result"][0]["meta"]

def number(value):
    return float(str(value).replace(",", ""))

def stamp(name):
    return dt.datetime.fromtimestamp(market(name)["regularMarketTime"], TZ).isoformat()

def price(name):
    item = market(name)
    return f"{item['regularMarketPrice']:,.2f} · {item['regularMarketChangePercent']:+.2f}%"

def body_html(markdown):
    rendered = []
    for section in markdown.split("\n\n")[1:]:
        if section.startswith("|"):
            rows = [line.strip("|").split("|") for line in section.splitlines() if not re.fullmatch(r"\|?[-| ]+\|?", line)]
            header, *items = rows
            table = "<table class=\"article-data-table\"><thead><tr>" + "".join(f"<th>{html.escape(cell.strip())}</th>" for cell in header) + "</tr></thead><tbody>"
            table += "".join("<tr>" + "".join(f"<td>{html.escape(cell.strip())}</td>" for cell in row) + "</tr>" for row in items)
            rendered.append("<div class=\"article-table-wrap\">" + table + "</tbody></table></div>")
        else:
            rendered.append("<p>" + html.escape(section).replace("\n", "<br>") + "</p>")
    return "\n".join(rendered)

def structured(content):
    def rewrite(match):
        node = json.loads(match.group(1))
        def visit(value):
            if isinstance(value, dict):
                if value.get("@type") == "ItemList" and value.get("itemListElement"):
                    items = [item for item in value["itemListElement"] if "market-2026-10-06.html" not in json.dumps(item, ensure_ascii=False)]
                    source = next(item for item in items if "market-2026-10-02.html" in json.dumps(item, ensure_ascii=False))
                    clone = json.loads(json.dumps(source, ensure_ascii=False).replace("market-2026-10-02.html", "market-2026-10-06.html").replace("market-2026-10-02-memory-yield-holiday-1200x630.png", IMAGE).replace(OLD_TITLE, TITLE).replace(OLD_SUMMARY, SUMMARY).replace("2026-10-02", DATE))
                    clone.update(url=URL, name=TITLE, description=SUMMARY, datePublished=issued.isoformat(), dateModified=issued.isoformat())
                    if isinstance(clone.get("image"), dict):
                        clone["image"]["url"] = "https://www.hpmplab.com/assets/images/articles/" + IMAGE
                    value["itemListElement"] = [clone] + items
                    for index, item in enumerate(value["itemListElement"], 1):
                        item["position"] = index
                    value["numberOfItems"] = len(value["itemListElement"])
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(node)
        return "<script type=\"application/ld+json\">" + json.dumps(node, ensure_ascii=False, indent=2) + "</script>"
    return re.sub(r"<script type=\"application/ld\+json\">(.*?)</script>", rewrite, content, flags=re.S)

def add_card(path, css):
    content = read(path)
    if "market-2026-10-06.html" in content:
        return content
    pattern = r"<article class=\"" + re.escape(css) + r"\"[^>]*>.*?</article>"
    matches = list(re.finditer(pattern, content, re.S))
    old = next(match.group(0) for match in matches if "market-2026-10-02.html" in match.group(0))
    fresh = old.replace("market-2026-10-02.html", "market-2026-10-06.html").replace("market-2026-10-02-memory-yield-holiday-1200x630.png", IMAGE).replace(OLD_TITLE, TITLE).replace(OLD_SUMMARY, SUMMARY).replace("2026-10-02", DATE).replace("10월 2일", "10월 6일")
    fresh = re.sub(r'(data-published=")[^"]+', r'\g<1>' + issued.isoformat(), fresh)
    fresh = re.sub(r'<time datetime="[^"]+">[^<]+</time>', f'<time datetime="{issued.isoformat()}">2026.10.06 · {issued:%H:%M} KST</time>', fresh, count=1)
    content = content.replace(old, fresh + "\n" + old, 1)
    return structured(content)

issued = dt.datetime.now(TZ).replace(microsecond=0)
raw_names = ("NXT", "FX", "yahoo-NQF", "yahoo-ESF", "yahoo-BZF", "yahoo-CLF", "KOSPI-basic")
cutoff = max(evidence(name)["fetchedAt"] for name in raw_names)
kospi_rows = evidence("KOSPI")["data"]
kodex_rows = evidence("122630")["data"]
kospi_basic = evidence("KOSPI-basic")["data"]
kospi_last = next(row for row in kospi_rows if row["localTradedAt"] == "2026-10-02")
kospi = {"openPrice": kospi_last["openPrice"], "highPrice": kospi_last["highPrice"], "lowPrice": kospi_last["lowPrice"], "closePrice": kospi_basic["closePrice"], "fluctuationsRatio": (number(kospi_basic["closePrice"]) / 6971.35 - 1) * 100}
kodex = next(row for row in kodex_rows if row["localTradedAt"] == "2026-10-02")
nxt = {row["itemCode"]: row for row in evidence("NXT")["data"]["datas"]}
fx = evidence("FX")["data"]["exchangeInfo"]
assert evidence("KOSPI-basic")["data"]["marketStatus"] == "PREOPEN"
assert all(row["localTradedAt"].startswith(DATE) for row in nxt.values())

manuscript = read("research/evidence/2026-10-06/manuscript.md")
notes = read("research/notes/2026-10-06.md")
price_lines = ["## 장전 가격", "", "|항목|가격·변화|출처 시각|", "|---|---:|---|", f"|KOSPI 전일 종가|{number(kospi['closePrice']):,.2f} · {number(kospi['fluctuationsRatio']):+.2f}%|2026-10-02 정규장 종가|", f"|KODEX 레버리지 전일 종가|{kodex['closePrice']}원 · {kodex['fluctuationsRatio']}%|2026-10-02 정규장 종가|"]
for code, label in (("005930", "삼성전자 NXT"), ("000660", "SK하이닉스 NXT")):
    item = nxt[code]
    price_lines.append(f"|{label}|{item['closePrice']}원 · {item['fluctuationsRatio']}%|{item['localTradedAt']}|")
price_lines.append(f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|")
for key, label in (("NQF", "Nasdaq100 선물"), ("ESF", "S&P500 선물"), ("BZF", "브렌트 선물"), ("CLF", "WTI 선물")):
    price_lines.append(f"|{label}|{price(key)}|{stamp(key)} · 지연 시세|")
report = f"# {DATE} KOSPI·KODEX 일일 리서치\n\n작성 {issued.isoformat()} / 데이터 최종 확인 {cutoff} / 한국 장전.\n\n확정 사실은 출처 시각 기준, 시나리오와 확률은 조건부 전망이다.\n\n" + manuscript.split("\n", 1)[1].strip() + "\n\n" + "\n".join(price_lines) + "\n\n## 취재 근거와 확인 시각\n\n" + notes + "\n\n## 미국 정규장 종목별 확인\n\n|종목|9/30 종가|전일 대비|\n|---|---:|---:|\n"
for ticker in ("QQQ", "TQQQ", "SOXX", "SMH", "NVDA", "AMD", "MU", "AVGO"):
    item = market(ticker)
    report += f"|{ticker}|{item['regularMarketPrice']:.2f}|{item['regularMarketChangePercent']:+.2f}%|\n"
report += "\n![최근 90일](../charts/us_yield_spreads_90d_2026-10-06.png)\n\n![최근 2년](../charts/us_yield_spreads_long_term_2026-10-06.png)\n"
write("reports/2026-10-06.md", report)

old_article = read("articles/market-2026-10-02.html")
OLD_TITLE = re.search(r"<h1>(.*?)</h1>", old_article).group(1)
OLD_SUMMARY = re.search(r'<p class="article-dek">(.*?)</p>', old_article).group(1)
prefix = old_article.split('<article class="editorial-article reading-article">')[0]
prefix = prefix.replace(OLD_TITLE, TITLE).replace(OLD_SUMMARY, SUMMARY).replace("market-2026-10-02.html", "market-2026-10-06.html").replace("market-2026-10-02-memory-yield-holiday-1200x630.png", IMAGE)
prefix = re.sub(r"2026-10-02T\d\d:\d\d:\d\d\+09:00", issued.isoformat(), prefix).replace("2026.10.02", "2026.10.06").replace("서울 일출과 푸른 메모리 칩·실리콘 웨이퍼, 금빛 수익률 곡선", ALT)
suffix = old_article[old_article.index("</div></article></main>"):]
header = f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{issued.isoformat()}">2026.10.06 · {issued:%H:%M} KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 {issued:%H:%M} KST · 데이터 최종 확인 {cutoff}. 미국 정규장은 10월 5일, 국내 NXT·환율·미국 선물은 장전 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="{ALT}"></figure></header><div class="article-body" id="article-body">'
charts = '<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_90d_2026-10-06.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 90일"><figcaption>FRED 최신 금리차 관측일은 10월 5일이다.</figcaption></figure><figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_long_term_2026-10-06.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 최근 2년"></figure>'
write("articles/market-2026-10-06.html", prefix + header + body_html(manuscript) + charts + suffix)

snapshot = json.loads(read("assets/data/market-dashboard-latest.json"))
snapshot_id = issued.strftime("%Y%m%d-%H%M")
snapshot.update(snapshotId=snapshot_id, generatedAt=issued.isoformat(), asOf=cutoff, asOfDisplay=cutoff, marketState="한국 장전", sourceLabel="미국 10월 5일 정규장 · 국내 10월 2일 종가 · 10월 6일 장전", latestArticle={"title": TITLE, "href": "market-2026-10-06.html"}, headline=TITLE, summary=SUMMARY)
for item in snapshot["markets"]:
    if item["id"] == "KOSPI":
        item.update(value=number(kospi["closePrice"]), changePercent=number(kospi["fluctuationsRatio"]), open=number(kospi["openPrice"]), high=number(kospi["highPrice"]), low=number(kospi["lowPrice"]), previousClose=6971.35, asOf="2026-10-02T15:30:00+09:00", asOfLabel="10월 2일 종가", stateLabel="정규장 종가", flows=[])
snapshot["stance"] = {"label": "원화 강세와 7,000선 수급", "attack": 30, "wait": 50, "defense": 20, "note": "원화 강세와 장전 메모리주 상승이 7,000선 위 수급으로 이어지는지 본다."}
snapshot["checkpoints"] = [{"label": "Nasdaq100 선물", "value": price("NQF"), "detail": stamp("NQF") + " · 지연", "tone": "info"}, {"label": "원/달러", "value": fx["closePrice"] + "원", "detail": fx["localTradedAt"] + " 고시", "tone": "positive"}, {"label": "삼성전자 NXT", "value": nxt["005930"]["closePrice"] + "원", "detail": nxt["005930"]["localTradedAt"], "tone": "positive"}, {"label": "SK하이닉스 NXT", "value": nxt["000660"]["closePrice"] + "원", "detail": nxt["000660"]["localTradedAt"], "tone": "positive"}]
snapshot["factors"] = [{"label": "미국 기술주", "metric": "QQQ +0.88% · NVDA +2.12%", "detail": "10월 5일 미국 정규장", "tone": "positive"}, {"label": "미국 반도체", "metric": "SOXX +0.10% · MU -1.02%", "detail": "10월 5일 미국 정규장", "tone": "neutral"}, {"label": "미 국채", "metric": "10년물 5.28% · 10년-2년 +0.47%p", "detail": "10월 2일~5일 최신 관측", "tone": "warning"}, {"label": "유가", "metric": "Brent 100.24달러", "detail": "10월 6일 장전 지연 선물 시세", "tone": "warning"}]
snapshot["memory"] = [{"label": "DDR5 16Gb · 9/24", "value": "$57.667", "change": "+0.29% 일간"}, {"label": "DDR4 16Gb · 9/24", "value": "$83.784", "change": "-0.70% 일간"}, {"label": "DDR4 8Gb · 9/24", "value": "$46.107", "change": "+0.47% 일간"}]
snapshot["scenarios"] = [{"id": "base", "label": "기본 · 50%", "range": "KOSPI 6,950~7,080", "summary": "원화 강세와 장전 메모리주 상승이 하단을 지지하지만, 7,080선 위는 수급 확인이 필요하다.", "conditions": ["6,950 이상", "7,080 이하", "외국인 매도 급확대 없음"], "invalidation": "범위 이탈"}, {"id": "bull", "label": "강세 · 30%", "range": "KOSPI 7,080 초과~7,220", "summary": "외국인 현물과 프로그램 순매수가 함께 돌아서며 기술주 강세가 확산한다.", "conditions": ["7,080 초과", "외국인 현물 순매수", "프로그램 전체 순매수"], "invalidation": "7,080 아래 재진입"}, {"id": "bear", "label": "약세 · 20%", "range": "KOSPI 6,780~6,950 미만", "summary": "반도체 신호가 약해지고 수급 매도가 겹친다.", "conditions": ["6,950 미만", "외국인 현물 순매도", "프로그램 전체 순매도"], "invalidation": "6,950 회복"}]
snapshot["strategyLevels"] = [{"asset": "KOSPI", "support": "6,950 / 6,780", "pivot": "7,080", "resistance": "7,220"}, {"asset": "KODEX 레버리지", "support": "111,500원", "pivot": "114,395원", "resistance": "117,500원"}]
snapshot["events"] = [{"time": "10월 5일 미국 정규장", "name": "나스닥 사상 최고치", "path": "기술주 위험선호와 반도체 확산"}, {"time": "10월 14일 21:30 KST", "name": "미국 9월 CPI", "path": "미 국채금리와 달러"}]
snapshot["checklist"] = [{"id": "support", "label": "KOSPI 6,950 방어"}, {"id": "rebound", "label": "7,080 돌파와 메모리 동반 강세"}, {"id": "flows", "label": "외국인·프로그램 수급 동행 여부"}]
for item in snapshot["technical"]["instruments"]:
    if item["id"] == "KOSPI":
        levels, points = [6950, 7080, 7220], [number(kospi[key]) for key in ("openPrice", "highPrice", "lowPrice", "closePrice")]
    elif item["id"] == "KODEX":
        levels, points = [111500, 114395, 117500], [number(kodex[key]) for key in ("openPrice", "highPrice", "lowPrice", "closePrice")]
    else:
        continue
    item.update(asOf="2026-10-02T15:30:00+09:00", asOfLabel="10월 2일 정규장 종가", levels=[{"label": label, "value": value} for label, value in zip(("1차 지지", "반등 기준", "저항"), levels)], interpretation=f"1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}", points=[{"label": label, "value": value} for label, value in zip(("시가", "고가", "저가", "종가"), points)])
snapshot["sources"] = [{"label": "미 재무부·FRED 금리", "href": "https://fred.stlouisfed.org/series/T10Y2Y"}, {"label": "미국 정규장 SOXX", "href": "https://finance.yahoo.com/quote/SOXX/"}, {"label": "KOSPI 종가", "href": "https://m.stock.naver.com/domestic/index/KOSPI/total"}, {"label": "Micron 4분기 실적", "href": "https://investors.micron.com/news/press-release/2026/Micron-Technology-Inc--Reports-Record-Fiscal-Fourth-Quarter-and-Full-Year-2026-Results/default.aspx"}]
dump(f"assets/data/market-dashboard-{snapshot_id}.json", snapshot)
dump("assets/data/market-dashboard-latest.json", snapshot)

for path, css in (("index.html", "article-card home-article-card"), ("articles/index.html", "article-card"), ("articles/market.html", "market-article-item")):
    content = add_card(path, css)
    head, rest = content.split("</head>", 1)
    for prop, value in (("og:title", TITLE), ("og:description", SUMMARY), ("twitter:title", TITLE), ("twitter:description", SUMMARY)):
        head = re.sub(r'(<meta (?:property|name)="' + re.escape(prop) + r'" content=")[^"]+', r'\g<1>' + value, head)
    head = re.sub(r'(<meta property="og:image(?::secure_url)?" content=")[^"]+', r'\g<1>https://www.hpmplab.com/assets/images/articles/' + IMAGE, head)
    head = re.sub(r'(<meta name="twitter:image" content=")[^"]+', r'\g<1>https://www.hpmplab.com/assets/images/articles/' + IMAGE, head)
    content = head + "</head>" + rest
    if path in ("index.html", "articles/index.html"):
        categories = re.findall(r'<article class="[^\"]*article-card[^\"]*" data-category="([^\"]+)"', content)
        for category in ("all", "market", "essay", "health"):
            content = re.sub(r'(data-category-count="' + category + r'">)\d+', r'\g<1>' + str(len(categories) if category == "all" else categories.count(category)), content)
    else:
        content = re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+', r'\g<1>market-2026-10-06.html', content)
        count = len(list((ROOT / "articles").glob("market-*.html")))
        content = re.sub(r'(일일시황 <span class="article-category-count">)\d+', r'\g<1>' + str(count), content)
        content = re.sub(r'(최신순 · )\d+(편)', r'\g<1>' + str(count) + r'\2', content)
    write(path, content)

sitemap = read("sitemap.xml")
if URL not in sitemap:
    sitemap = sitemap.replace("</urlset>", f"<url><loc>{URL}</loc><lastmod>{DATE}</lastmod><image:image><image:loc>https://www.hpmplab.com/assets/images/articles/{IMAGE}</image:loc></image:image></url>\n</urlset>")
for site_url in ("https://www.hpmplab.com/", "https://www.hpmplab.com/articles/", "https://www.hpmplab.com/articles/market.html"):
    sitemap = re.sub(r"(<loc>" + re.escape(site_url) + r"</loc>\s*<lastmod>)[^<]+", r"\g<1>" + DATE, sitemap)
write("sitemap.xml", sitemap)

sessions = json.loads(read("research/evaluation/trading-sessions.json"))
sessions.update(asOf=cutoff, source="Naver Finance KOSPI PREOPEN 2026-10-06; KRX 거래일", rawHash=evidence("KOSPI-basic")["rawHash"])
for date in ("2026-10-02", DATE):
    if date not in sessions["sessions"]:
        sessions["sessions"].append(date)
sessions["sessions"].sort()
dump("research/evaluation/trading-sessions.json", sessions)

actual = {"schemaVersion": 1, "sessionDate": "2026-10-02", "bizdate": "20261001", "fetchedAt": cutoff, "marketStatus": "CLOSE", "kospi": {"open": None, "high": None, "low": None, "close": number(kospi["closePrice"]), "asOf": "2026-10-02T15:30:00+09:00", "source": evidence("KOSPI-basic")["url"], "rawHash": evidence("KOSPI-basic")["rawHash"], "rawPath": "research/evidence/2026-10-06/KOSPI-basic.json"}, "kodex": {"open": int(number(kodex["openPrice"])), "high": int(number(kodex["highPrice"])), "low": int(number(kodex["lowPrice"])), "close": int(number(kodex["closePrice"])), "volume": int(number(kodex["accumulatedTradingVolume"])), "source": evidence("122630")["url"], "rawHash": evidence("122630")["rawHash"]}, "closeSnapshot": None, "closeSnapshotMissingReason": "15시 20분 정확 시각 외국인·프로그램·시장 폭 원문 부재. 종가로 소급하지 않음", "flowTrajectory": None, "flowTrajectoryMissingEvidence": {"sourceStatus": "unavailable", "source": evidence("KOSPI-integration")["url"], "asOf": "2026-10-02T15:30:00+09:00", "fetchedAt": cutoff, "missingReason": "09:30·10:00·14:00·15:20 동일 시각 수급 앵커 원문 미확보", "rawHash": evidence("KOSPI-integration")["rawHash"]}}
dump("research/evaluation/actuals/2026-10-02.json", actual)
outcome = {"schemaVersion": 1, "forecastId": "2026-10-02-0811-same-close", "recordedAt": cutoff, "actualRef": "2026-10-02", "realizedScenario": "base", "errorCodes": [], "triggerResults": [{"id": "all", "status": "unavailable", "reason": "15시 20분 정확 시각 수급 원문 미확보"}], "driverAssessment": [{"id": "us-chip-strength", "status": "partially_confirmed"}, {"id": "yield-fx-ceiling", "status": "partially_confirmed"}, {"id": "domestic-flow", "status": "unavailable"}], "hypothesisTests": []}
dump("research/evaluation/outcomes/2026-10-02-0811-same-close.json", outcome)

forecast = {"schemaVersion": 1, "forecastId": f"{DATE}-{issued:%H%M}-same-close", "visibility": "public", "reportPath": f"reports/{DATE}.md", "reportSha256": hashlib.sha256((ROOT / f"reports/{DATE}.md").read_bytes()).hexdigest(), "issuedAt": issued.isoformat(), "dataCutoffAt": cutoff, "marketState": "preopen", "marketRegime": "mixed", "evaluationBucket": "preopen", "target": {"sessionDate": DATE, "horizon": "session_close", "instrument": "KOSPI", "leadSessions": 0, "previousSessionDate": "2026-10-02"}, "reference": {"price": number(kospi["closePrice"]), "asOf": "2026-10-02T15:30:00+09:00", "kind": "previous_close"}, "scenarios": {"bull": {"low": 6900, "high": 7050, "probability": 0.30}, "base": {"low": 6750, "high": 6900, "probability": 0.50}, "bear": {"low": 6550, "high": 6750, "probability": 0.20}}, "closeEnvelopeCoverage": 0.9, "pathEnvelope": {"low": 6500, "high": 7050, "coverage": 0.9}, "drivers": [{"id": "micron-guidance", "rank": 1, "claim": "Micron의 강한 메모리 가이던스와 국내 NXT 상승이 6,750선 하단을 지지한다.", "validationMetric": "Micron 가이던스·SOXX·삼성전자·SK하이닉스"}, {"id": "yield-fx-ceiling", "rank": 2, "claim": "5%대 미국 10년물과 원/달러 상승이 6,900선 위 추격을 제한한다.", "validationMetric": "미국 10년물·USD/KRW·KOSPI"}, {"id": "domestic-flow", "rank": 3, "claim": "6,900선 회복은 외국인과 프로그램 수급의 동행이 확인해야 한다.", "validationMetric": "외국인·프로그램·KOSPI"}], "scenarioTriggers": {"bull": {"logic": "AND", "observeBy": f"{DATE}T15:20:00+09:00", "conditions": [{"id": "bull-price", "metricId": "kospi_price", "operator": "gt", "threshold": 6900, "source": "Naver Finance KOSPI"}, {"id": "bull-foreign", "metricId": "foreign_cash", "operator": "gt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"}, {"id": "bull-program", "metricId": "program_total", "operator": "gt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"}]}, "base": {"logic": "AND", "observeBy": f"{DATE}T15:20:00+09:00", "conditions": [{"id": "base-floor", "metricId": "kospi_price", "operator": "gte", "threshold": 6750, "source": "Naver Finance KOSPI"}, {"id": "base-cap", "metricId": "kospi_price", "operator": "lte", "threshold": 6900, "source": "Naver Finance KOSPI"}, {"id": "base-foreign", "metricId": "foreign_cash", "operator": "gte", "threshold": -10000, "source": "Naver Finance KOSPI 수급 (억원)"}]}, "bear": {"logic": "AND", "observeBy": f"{DATE}T15:20:00+09:00", "conditions": [{"id": "bear-price", "metricId": "kospi_price", "operator": "lt", "threshold": 6750, "source": "Naver Finance KOSPI"}, {"id": "bear-foreign", "metricId": "foreign_cash", "operator": "lt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"}, {"id": "bear-program", "metricId": "program_total", "operator": "lt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"}]}}, "hypothesisTrials": [], "posture": {"attack": 30, "wait": 55, "defense": 15}, "supersedes": None}
forecast["contentHash"] = hashlib.sha256(json.dumps(forecast, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
dump("research/evaluation/forecasts/" + forecast["forecastId"] + ".json", forecast)
dump("research/evidence/2026-10-06/seal.json", {"forecastId": forecast["forecastId"], "issuedAt": issued.isoformat(), "dataCutoffAt": cutoff, "snapshotId": snapshot_id, "articleTitle": TITLE})
write("STATE.md", f"# KOSPI·KODEX 리서치 상태\n\n- 작성 {issued.isoformat()}, 데이터 최종 확인 {cutoff}, 한국 장전.\n- 직전 KOSPI {number(kospi['closePrice']):,.2f}({number(kospi['fluctuationsRatio']):+.2f}%), KODEX {kodex['closePrice']}원({kodex['fluctuationsRatio']}%), 9월 30일 정규장. KOSPI OHLC는 원시 응답 결측으로 채우지 않았다.\n- 핵심: Micron의 기록적 4분기 매출·강한 1분기 가이던스와 장전 메모리 NXT 상승이 하단을 받치지만, 미국 10년물 5.26%와 원/달러 1,358.00원이 상단을 제한한다. 미국 ETF의 한국장 후행 반영분은 중복 가산하지 않는다.\n- 대응 30/55/15. 기본 6750~6900(50%), 강세6900초과~7050(30%), 약세6550~6750미만(20%), 경로6500~7050(90%). KODEX 107500/109470/112000.\n- 보고서 reports/2026-10-02.md, 취재 research/notes/2026-10-02.md. 차트는 charts/us_yield_spreads_90d_2026-10-02.png 및 long_term.\n- 대시보드 assets/data/market-dashboard-{snapshot_id}.json 및 latest.json.\n- 다음: 10월 1일 21:30 KST 미국 주간 실업수당 청구, 10월 2일 21:30 KST 미국 고용보고서.\n- 직전 정산 research/evaluation/outcomes/2026-09-30-0812-same-close.json, 누적 research/evaluation/generated/latest.md. 수급 앵커는 원문 미확보로 추정하지 않는다.\n")
print(json.dumps({"forecastId": forecast["forecastId"], "issuedAt": issued.isoformat(), "dataCutoffAt": cutoff, "snapshotId": snapshot_id}, ensure_ascii=False))
