"""2026-09-10 KOSPI·KODEX 장전 발행본 조립. --seal 전에는 원장을 만들지 않는다."""
import datetime
import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
E = pathlib.Path(__file__).parent
TITLE = "유가 100달러의 압력 속, KOSPI 7,000선의 변수는 SK하이닉스"
SUMMARY = "유가와 장기금리가 지수 상단을 누르는 가운데, 장전 NXT에서는 SK하이닉스만 강세를 유지해 반도체 내부의 온도차가 더 선명해졌습니다."
IMAGE = "market-2026-09-10-oil-memory-balance-1200x630.webp"
ALT = "서울 아침빛 속 메모리 칩과 유리 저울 위의 호박색 원유"
PREVIOUS_SUMMARY = "미국 반도체 ETF는 올랐지만 Nvidia와 Micron은 하락했습니다. 유가 부담 속에서 국내 메모리주 반등이 지수 전반으로 이어지는지가 관건입니다."
OLD_DATE = "2026-09-09"
NEW_DATE = "2026-09-10"

def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).replace(microsecond=0)

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def write(path, content):
    (ROOT / path).write_text(content, encoding="utf-8", newline="\n")

def dump(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")

def base(path):
    return subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT).decode("utf-8")

def ev(name):
    return json.loads((E / f"{name}.json").read_text(encoding="utf-8"))

def number(value):
    return float(str(value).replace(",", ""))

def find_daily(name, date):
    return next(x for x in ev(name)["data"] if x["localTradedAt"] == date)

def markdown_html(markdown):
    def inline(text):
        escaped = html.escape(text)
        escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', escaped)
        return re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escaped)
    blocks = []
    for block in markdown.strip().split("\n\n"):
        lines = block.strip().splitlines()
        if not lines:
            continue
        if lines[0].startswith("## "):
            blocks.append("<h2>" + inline(lines[0][3:]) + "</h2>" + ("" if len(lines) == 1 else "<p>" + inline(" ".join(lines[1:])) + "</p>"))
        elif lines[0].startswith("|"):
            rows = [line for line in lines if not re.fullmatch(r"\|[\s:|\-]+\|", line)]
            parsed = [[cell.strip() for cell in row.strip().strip("|").split("|")] for row in rows]
            header = "".join("<th>" + inline(cell) + "</th>" for cell in parsed[0])
            body = "".join("<tr>" + "".join("<td>" + inline(cell) + "</td>" for cell in row) + "</tr>" for row in parsed[1:])
            blocks.append('<div class="table-scroll"><table><thead><tr>' + header + "</tr></thead><tbody>" + body + "</tbody></table></div>")
        elif lines[0].startswith("- "):
            blocks.append("<ul>" + "".join("<li>" + inline(line[2:]) + "</li>" for line in lines) + "</ul>")
        else:
            blocks.append("<p>" + inline(" ".join(lines)) + "</p>")
    return "\n".join(blocks)

def add_card(path, css_class, old_title, stamp):
    text = base(path)
    match = re.search(r'<article class="' + re.escape(css_class) + r'"[^>]*>.*?</article>', text, re.S)
    assert match, path
    old_card = match.group(0)
    new_card = old_card.replace(old_title, TITLE).replace(PREVIOUS_SUMMARY, SUMMARY).replace("market-2026-09-09-chips-oil-1200x630.webp", IMAGE).replace(OLD_DATE, NEW_DATE).replace("market-2026-09-09.html", "market-2026-09-10.html").replace("2026.09.09 · 08:16 KST", f"2026.09.10 · {stamp.strftime('%H:%M')} KST")
    text = text[:match.start()] + new_card + "\n" + old_card.replace('loading="eager"', 'loading="lazy"').replace(' fetchpriority="high"', "") + text[match.end():]
    def schema(repl):
        obj = json.loads(repl.group(1))
        def walk(value):
            if isinstance(value, dict):
                if value.get("@type") == "ItemList" and value.get("itemListElement"):
                    item = json.loads(json.dumps(value["itemListElement"][0], ensure_ascii=False).replace(old_title, TITLE).replace(OLD_DATE, NEW_DATE).replace("market-2026-09-09.html", "market-2026-09-10.html").replace("market-2026-09-09-chips-oil-1200x630.webp", IMAGE))
                    value["itemListElement"].insert(0, item)
                    for index, element in enumerate(value["itemListElement"], start=1):
                        element["position"] = index
                    value["numberOfItems"] = len(value["itemListElement"])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(obj)
        return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, indent=2) + "</script>"
    text = re.sub(r'<script type="application/ld\+json">(.*?)</script>', schema, text, flags=re.S)
    write(path, text)

def update_card_counts():
    for path, card_class, market_href in (("index.html", "article-card home-article-card", "articles/market-"), ("articles/index.html", "article-card", "market-")):
        text = read(path)
        total = len(re.findall(r'<article class="' + re.escape(card_class) + r'"', text))
        market = len(re.findall(r'href="[^"]*' + re.escape(market_href) + r'\d{4}-\d{2}-\d{2}\.html"', text))
        text = re.sub(r'(data-category-count="all">)\d+', r'\g<1>' + str(total), text)
        text = re.sub(r'(data-category-count="market">)\d+', r'\g<1>' + str(market), text)
        write(path, text)

def main(seal):
    if seal:
        assert not (E / "seal.json").exists(), "이미 봉인했습니다."
    stamp = now()
    stamp_iso = stamp.isoformat()
    cutoff = max(ev(name)["fetchedAt"] for name in ("NXT", "FX", "yahoo-NQF", "yahoo-ESF", "yahoo-BZF", "yahoo-CLF"))
    kospi = find_daily("KOSPI", "2026-09-09")
    kosdaq = find_daily("KOSDAQ", "2026-09-09")
    kodex = find_daily("122630", "2026-09-09")
    samsung = find_daily("005930", "2026-09-09")
    hynix = find_daily("000660", "2026-09-09")
    nxt = ev("NXT")["data"]
    nxt_by_code = {item["itemCode"]: item for item in nxt["datas"]}
    fx = ev("FX")["data"]["exchangeInfo"]
    market_time = datetime.datetime.strptime(nxt["time"], "%Y%m%d%H%M%S").strftime("%H:%M:%S")
    futures = {name: ev("yahoo-" + name)["data"]["chart"]["result"][0]["meta"] for name in ("NQF", "ESF", "BZF", "CLF")}

    body = read("research/evidence/2026-09-10/manuscript.md").split("\n", 1)[1].strip()
    price_table = "## 장전 가격\n\n|항목|가격·변화|출처 기준 시각|\n|---|---:|---|\n"
    price_table += f"|삼성전자 NXT|{nxt_by_code['005930']['closePrice']}원 · {nxt_by_code['005930']['fluctuationsRatio']}%|9월 10일 {market_time} KST 조회|\n"
    price_table += f"|SK하이닉스 NXT|{nxt_by_code['000660']['closePrice']}원 · {nxt_by_code['000660']['fluctuationsRatio']}%|9월 10일 {market_time} KST 조회|\n"
    price_table += f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|\n"
    for key, label in (("NQF", "Nasdaq100 선물"), ("ESF", "S&P500 선물"), ("BZF", "브렌트 선물"), ("CLF", "WTI 선물")):
        value = futures[key]
        local_time = datetime.datetime.fromtimestamp(value["regularMarketTime"], stamp.tzinfo).isoformat()
        price_table += f"|{label}|{value['regularMarketPrice']:,.2f} · {value['regularMarketChangePercent']:+.3f}%|{local_time} 지연 시세|\n"
    price_table += "\n[NXT](https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660) · [환율](https://api.stock.naver.com/marketindex/exchange/FX_USDKRW) · [Nasdaq100 선물](https://finance.yahoo.com/quote/NQ=F/) · [S&P500 선물](https://finance.yahoo.com/quote/ES=F/) · [브렌트](https://finance.yahoo.com/quote/BZ=F/) · [WTI](https://finance.yahoo.com/quote/CL=F/)\n\nNXT는 정규장과 별도 시장이고 선물은 지연 시세다.\n"
    publication_body = body + "\n\n" + price_table

    old_article = base("articles/market-2026-09-09.html")
    old_title = re.search(r"<h1>(.*?)</h1>", old_article).group(1)
    prefix = old_article.split('<article class="editorial-article reading-article">')[0]
    prefix = prefix.replace(old_title, TITLE).replace(PREVIOUS_SUMMARY, SUMMARY).replace("market-2026-09-09.html", "market-2026-09-10.html").replace("market-2026-09-09-chips-oil-1200x630.webp", IMAGE)
    closing = old_article[old_article.index("</div></article></main>"):]
    charts = "\n".join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{kind}_2026-09-10.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {label}"><figcaption>9월 9일 10년-2년 +0.40%p · 10년-3개월 +0.88%p. FRED.</figcaption></figure>' for kind, label in (("90d", "최근 90일"), ("long_term", "최근 2년")))
    article = prefix + f'<article class="editorial-article reading-article"><header class="article-hero"><a class="article-category-badge" href="market.html?view=analysis#research-archive">시황분석</a><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{stamp_iso}">2026.09.10 · {stamp.strftime("%H:%M")} KST</time><span>개장 전 브리핑</span></div><p class="article-disclosure">작성 {stamp.strftime("%H:%M")} KST · 데이터 최종 확인 {cutoff}. 국내 정규장 일봉은 9월 9일, 미국 정규장은 9월 9일 기준이다. 장전 가격의 개별 시각은 표에 표시했다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="{ALT}"></figure></header><div class="article-body" id="article-body">' + markdown_html(publication_body) + charts + closing
    write("articles/market-2026-09-10.html", article)
    report = f"# {TITLE}\n\n- 작성: {stamp_iso}; 데이터 최종 확인: {cutoff}; 한국 개장 전.\n- 수치는 출처 관측값이며 시나리오·확률·대응점수는 조건부 분석이다.\n- 전일 KOSPI 7,051.64 종가는 직전 장전판 기본 구간 안, 일중 고가·저가는 전체 경로 안에 들어왔다. 확정 수급은 미확인으로 보존했다.\n\n" + publication_body + "\n\n## 취재 근거\n\n" + read("research/evidence/2026-09-10/overnight-notes.md") + "\n\n![금리차 90일](../charts/us_yield_spreads_90d_2026-09-10.png)\n\n![금리차 2년](../charts/us_yield_spreads_long_term_2026-09-10.png)\n"
    write("reports/2026-09-10.md", report)

    dashboard = json.loads(base("assets/data/market-dashboard-latest.json"))
    snapshot_id = stamp.strftime("%Y%m%d-%H%M")
    dashboard.update(snapshotId=snapshot_id, generatedAt=stamp_iso, asOf=cutoff, asOfDisplay=cutoff, marketState="한국 개장 전", sourceLabel="국내 9월 9일 정규장 종가 · 미국 9월 9일 정규장 · 장전 가격은 각 출처 시각", latestArticle={"title": TITLE, "href": "market-2026-09-10.html"}, headline="유가·금리 부담 속 SK하이닉스 장전 강세가 7,000선 하단으로 번지는지 봅니다.", summary=SUMMARY)
    daily = {"KOSPI": kospi, "KOSDAQ": kosdaq}
    for item in dashboard["markets"]:
        value = daily[item["id"]]
        item.update(value=number(value["closePrice"]), changePercent=number(value["fluctuationsRatio"]), open=number(value["openPrice"]), high=number(value["highPrice"]), low=number(value["lowPrice"]), previousClose=number(value["closePrice"]) - number(value["compareToPreviousClosePrice"]), asOf="2026-09-09T15:30:00+09:00", asOfLabel="9월 9일 정규장 종가", stateLabel="전일 종가", flows=[])
        if item["id"] == "KOSPI":
            item.pop("breadth", None)
    dashboard["stance"] = {"label": "관망 우세", "attack": 25, "wait": 55, "defense": 20, "note": "유가·금리 부담과 삼성·하이닉스 장전 엇갈림이 충돌하는 구간입니다."}
    dashboard["checkpoints"] = [{"label": "미국 반도체", "value": "SOXX +0.68% · Micron +2.75%", "detail": "9월 9일 미국 정규장 종가", "tone": "info"}, {"label": "원/달러", "value": f"{fx['closePrice']}원", "detail": fx["localTradedAt"] + " 고시", "tone": "info"}, {"label": "메모리 NXT", "value": f"삼성 {nxt_by_code['005930']['fluctuationsRatio']}% · 하이닉스 {nxt_by_code['000660']['fluctuationsRatio']}%", "detail": market_time + " KST 조회", "tone": "info"}, {"label": "브렌트 선물", "value": f"{futures['BZF']['regularMarketPrice']:.2f}달러", "detail": "지연 시세 · 개별 시각은 기사 표", "tone": "warning"}]
    dashboard["changes"] = [{"label": "KOSPI", "before": "6,954.52", "after": "7,051.64", "meaning": "9월 9일 7,000선을 회복했습니다."}, {"label": "메모리 대형주", "before": "삼성 0.00% · 하이닉스 +3.51%", "after": f"NXT 삼성 {nxt_by_code['005930']['fluctuationsRatio']}% · 하이닉스 {nxt_by_code['000660']['fluctuationsRatio']}%", "meaning": "장전에도 SK하이닉스가 상대강세를 유지했습니다."}]
    dashboard["factors"] = [{"label": "유가·금리", "metric": "브렌트 100달러대 · 미 10년물 4.84%", "detail": "9월 9일 미국장 · 물가와 장기금리 부담이 상단을 누릅니다.", "tone": "warning"}, {"label": "미국 반도체", "metric": "SOXX +0.68% · Micron +2.75%", "detail": "9월 9일 미국 정규장 · Nvidia와 Broadcom은 하락했습니다.", "tone": "info"}, {"label": "메모리 현물", "metric": "DDR4 1Gx8 주간 +1.78%", "detail": "TrendForce 9월 9일 · DDR5 조달과 NAND는 약합니다.", "tone": "info"}]
    dashboard["flows"] = {"program": None, "kospi200FuturesForeign": None, "futuresUnit": "계약", "futuresAsOfLabel": "9월 9일 확정 수급 미확인"}
    dashboard["memory"] = [{"label": "DDR4 1Gx8 3200 · 9/8", "value": "$45.36", "change": "+1.78% 주간"}, {"label": "DDR5 현물 · 9/9", "value": "조달 제한", "change": "수요 약함"}, {"label": "TLC 웨이퍼 · 9/9", "value": "현물", "change": "-2.71% 주간"}]
    dashboard["scenarios"] = [{"id": "base", "label": "기본 · 50%", "range": "KOSPI 7,000~7,150", "summary": "유가 부담을 소화하며 SK하이닉스의 상대강세가 하단으로 번지는지 봅니다.", "conditions": ["7,000 이상", "7,150 이하", "SK하이닉스 상대강세"], "invalidation": "7,000 이탈과 반도체 동반 약세"}, {"id": "bull", "label": "강세 · 25%", "range": "KOSPI 7,150 초과~7,350", "summary": "SK하이닉스 장전 강세에 삼성전자 반등이 합류합니다.", "conditions": ["7,150 초과", "삼성전자·SK하이닉스 동반 강세", "원/달러 안정"], "invalidation": "7,150 아래 재진입"}, {"id": "bear", "label": "약세 · 25%", "range": "KOSPI 6,800~7,000 미만", "summary": "유가와 금리 부담이 반도체 매도로 번집니다.", "conditions": ["7,000 미만", "반도체 동반 약세", "원/달러 상승"], "invalidation": "7,000 회복"}]
    dashboard["strategyLevels"] = [{"asset": "KOSPI", "support": "7,000 / 6,800", "pivot": "7,150", "resistance": "7,350"}, {"asset": "KODEX 레버리지", "support": "112,500원", "pivot": "115,000원", "resistance": "117,925원"}]
    dashboard["events"] = [{"time": "9월 10일 21:30 KST", "name": "미국 8월 PPI", "path": "유가·금리 기대"}, {"time": "9월 11일 21:30 KST", "name": "미국 8월 CPI", "path": "금리 기대와 밸류에이션"}, {"time": "9월 17일 03:00 KST", "name": "FOMC·경제전망", "path": "정책금리와 전망"}]
    dashboard["checklist"] = [{"id": "support", "label": "KOSPI 7,000을 지켰다"}, {"id": "breakout", "label": "KOSPI 7,150을 넘었다"}, {"id": "memory", "label": "삼성전자도 SK하이닉스 장전 강세에 합류한다"}]
    dashboard["technical"]["note"] = "9월 9일 확정 일봉과 9월 10일 분석 기준선입니다."
    for item in dashboard["technical"]["instruments"]:
        daily_item = kospi if item["id"] == "KOSPI" else kodex
        levels = [7000, 7150, 7350] if item["id"] == "KOSPI" else [112500, 115000, 117925]
        item.update(asOf="2026-09-09T15:30:00+09:00", asOfLabel="9월 9일 정규장 종가", points=[{"label": label, "value": number(daily_item[key])} for label, key in (("시가", "openPrice"), ("고가", "highPrice"), ("저가", "lowPrice"), ("종가", "closePrice"))], levels=[{"label": label, "value": value} for label, value in zip(("1차 지지", "반등 기준", "저항"), levels)], interpretation=f"1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}")
    dashboard["sources"] = [{"label": "TrendForce", "href": "https://www.trendforce.com/news/2026/09/09/insights-memory-spot-price-update-ddr4-mainstream-prices-rise-1-78-on-2gx8-orders-ddr5-demand-remains-limited/"}, {"label": "BLS", "href": "https://www.bls.gov/schedule/news_release/ppi.htm"}, {"label": "KOSPI", "href": ev("KOSPI")["url"]}, {"label": "NXT", "href": ev("NXT")["url"]}, {"label": "환율", "href": ev("FX")["url"]}]
    dump("assets/data/market-dashboard-latest.json", dashboard)
    if seal:
        dump(f"assets/data/market-dashboard-{snapshot_id}.json", dashboard)

    add_card("index.html", "article-card home-article-card", old_title, stamp)
    add_card("articles/index.html", "article-card", old_title, stamp)
    add_card("articles/market.html", "market-article-item", old_title, stamp)
    update_card_counts()
    market_index = read("articles/market.html")
    market_index = re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+', r'\g<1>market-2026-09-10.html', market_index)
    market_count = len(re.findall(r'<article class="market-article-item"', market_index))
    market_index = re.sub(r'(일일시황 <span class="article-category-count">)\d+', r'\g<1>' + str(market_count), market_index)
    market_index = re.sub(r'최신순 · \d+편', lambda m: f"최신순 · {market_count}편", market_index)
    write("articles/market.html", market_index)
    sitemap = base("sitemap.xml").replace("</urlset>", "<url><loc>https://www.hpmplab.com/articles/market-2026-09-10.html</loc><lastmod>2026-09-10</lastmod></url>\n</urlset>")
    for loc in ("https://www.hpmplab.com/", "https://www.hpmplab.com/articles/", "https://www.hpmplab.com/articles/market.html"):
        sitemap = re.sub(r"(<loc>" + re.escape(loc) + r"</loc>\s*<lastmod>)[^<]+", r"\g<1>2026-09-10", sitemap)
    write("sitemap.xml", sitemap)
    write("STATE.md", f"# KOSPI·KODEX 리서치 상태\n\n- 작성 {stamp_iso}, 데이터 최종 확인 {cutoff}, 한국 개장 전.\n- 직전 KOSPI 7,051.64(+1.40%), KODEX 115,580원(+3.06%), 9월 9일 정규장 종가.\n- NXT 삼성 {nxt_by_code['005930']['closePrice']}원({nxt_by_code['005930']['fluctuationsRatio']}%), 하이닉스 {nxt_by_code['000660']['closePrice']}원({nxt_by_code['000660']['fluctuationsRatio']}%), {market_time} KST 조회. 원/달러 {fx['closePrice']}원({fx['localTradedAt']}).\n- 핵심: 유가100달러대와 장기금리 상승, 국내 메모리주 장전 상대강세, 메모리 현물 품목별 분화. EWY·ADR 후행 반영은 중복 가산하지 않는다.\n- 수급: 9월 9일 확정 현물·프로그램·시장폭 수급 미확인. 0으로 대체하지 않으며 actuals/2026-09-09.json 참조.\n- 대응 공격25/관망55/방어20. 기본7000~7150(50%),강세7150초과~7350(25%),약세6800~7000미만(25%),장중6750~7400(90%). KODEX112500/115000/117925.\n- 다음: 9/10PPI·9/11CPI21:30, 9/15~16ET FOMC.\n- reports/2026-09-10.md; research/evidence/2026-09-10/overnight-notes.md; charts/us_yield_spreads_90d_2026-09-10.png 및 long_term.\n- assets/data/market-dashboard-{snapshot_id}.json; 최신 포인터 market-dashboard-latest.json.\n- 평가 research/evaluation/generated/latest.md, 직전 정산 outcomes/2026-09-09-0816-same-close.json.\n")

    actual = {"schemaVersion": 1, "sessionDate": "2026-09-09", "bizdate": "20260909", "fetchedAt": stamp_iso, "marketStatus": "CLOSE", "kospi": {key: number(kospi[key + "Price"]) for key in ("open", "high", "low", "close")} | {"asOf": "2026-09-09T15:30:00+09:00", "source": ev("KOSPI")["url"], "rawHash": ev("KOSPI")["rawHash"]}, "closeSnapshot": None, "closeSnapshotMissingReason": "확정 KODEX 일봉은 보존했으나 9월 9일 15:30 이후 동일 묶음의 현물·프로그램·시장폭 원문을 확보하지 못했다. 장전 0값이나 다른 시각 수급으로 대체하지 않는다.", "flowTrajectory": None, "flowTrajectoryMissingEvidence": {"sourceStatus": "incomplete", "source": ev("KOSPI-integration")["url"], "asOf": "2026-09-09T15:30:00+09:00", "fetchedAt": stamp_iso, "missingReason": "9월 10일 장전 integration 응답은 새 거래일 0으로 초기화되어 9월 9일 09:30·10:00·14:00·15:30 원문 앵커를 제공하지 않는다.", "rawHash": ev("KOSPI-integration")["rawHash"]}}
    dump("research/evaluation/actuals/2026-09-09.json", actual)
    previous = json.loads(read("research/evaluation/forecasts/2026-09-09-0816-same-close.json"))
    outcome = {"schemaVersion": 1, "forecastId": previous["forecastId"], "recordedAt": stamp_iso, "actualRef": "2026-09-09", "realizedScenario": "base", "errorCodes": ["cause_unverifiable"], "triggerResults": [{"id": "bull-price", "status": "not_observed", "observedAt": "2026-09-09T15:30:00+09:00", "observedValue": number(kospi["closePrice"]), "source": "Naver Finance KOSPI 일봉"}, {"id": "bull-foreign", "status": "unavailable", "reason": "9월 9일 15:20 이전 외국인 현물 원문 앵커를 확보하지 못했다."}, {"id": "bull-program", "status": "unavailable", "reason": "9월 9일 15:20 이전 프로그램 전체 원문 앵커를 확보하지 못했다."}, {"id": "base-support", "status": "observed", "observedAt": "2026-09-09T15:30:00+09:00", "observedValue": number(kospi["closePrice"]), "source": "Naver Finance KOSPI 일봉"}, {"id": "base-cap", "status": "observed", "observedAt": "2026-09-09T15:30:00+09:00", "observedValue": number(kospi["closePrice"]), "source": "Naver Finance KOSPI 일봉"}, {"id": "base-foreign", "status": "unavailable", "reason": "9월 9일 15:20 이전 외국인 현물 원문 앵커를 확보하지 못했다."}, {"id": "bear-price", "status": "not_observed", "observedAt": "2026-09-09T15:30:00+09:00", "observedValue": number(kospi["closePrice"]), "source": "Naver Finance KOSPI 일봉"}, {"id": "bear-foreign", "status": "unavailable", "reason": "9월 9일 15:20 이전 외국인 현물 원문 앵커를 확보하지 못했다."}, {"id": "bear-program", "status": "unavailable", "reason": "9월 9일 15:20 이전 프로그램 전체 원문 앵커를 확보하지 못했다."}], "driverAssessment": [{"id": "domestic-demand", "status": "partial"}, {"id": "oil-risk", "status": "unverifiable"}, {"id": "memory-differentiation", "status": "partial"}], "hypothesisTests": []}
    dump("research/evaluation/outcomes/2026-09-09-0816-same-close.json", outcome)
    sessions = json.loads(read("research/evaluation/trading-sessions.json"))
    sessions.update(asOf=stamp_iso, source="Naver Finance KOSPI 확정 일봉 및 2026-09-10 PREOPEN 거래일", rawHash=ev("KOSPI")["rawHash"], sessions=sorted(set(sessions["sessions"] + ["2026-09-10"])))
    dump("research/evaluation/trading-sessions.json", sessions)

    if seal:
        forecast = {"schemaVersion": 1, "forecastId": f"2026-09-10-{stamp.strftime('%H%M')}-same-close", "visibility": "public", "reportPath": "reports/2026-09-10.md", "reportSha256": hashlib.sha256((ROOT / "reports/2026-09-10.md").read_bytes()).hexdigest(), "issuedAt": stamp_iso, "dataCutoffAt": cutoff, "marketState": "preopen", "marketRegime": "mixed", "evaluationBucket": "preopen", "target": {"sessionDate": "2026-09-10", "horizon": "session_close", "instrument": "KOSPI", "leadSessions": 0, "previousSessionDate": "2026-09-09"}, "reference": {"price": number(kospi["closePrice"]), "asOf": "2026-09-09T15:30:00+09:00", "kind": "previous_close"}, "scenarios": {"bull": {"low": 7150, "high": 7350, "probability": 0.25}, "base": {"low": 7000, "high": 7150, "probability": 0.50}, "bear": {"low": 6800, "high": 7000, "probability": 0.25}}, "closeEnvelopeCoverage": 0.90, "pathEnvelope": {"low": 6750, "high": 7400, "coverage": 0.90}, "drivers": [{"id": "oil-rates", "rank": 1, "claim": "유가와 장기금리 상승이 지수 상단을 제한한다.", "validationMetric": "브렌트·원/달러·KOSPI 종가"}, {"id": "memory-relative-strength", "rank": 2, "claim": "장전 메모리 대형주 강세가 7,000선 하단을 지지한다.", "validationMetric": "삼성전자·SK하이닉스·KOSPI 종가"}, {"id": "semiconductor-differentiation", "rank": 3, "claim": "미국 반도체의 분화는 지수 전반 추세 확인을 늦춘다.", "validationMetric": "SOXX·삼성전자·SK하이닉스"}], "scenarioTriggers": {"bull": {"logic": "AND", "observeBy": "2026-09-10T15:20:00+09:00", "conditions": [{"id": "bull-price", "description": "KOSPI가 7,150을 넘는다.", "metricId": "kospi_price", "operator": "gt", "threshold": 7150, "source": "Naver Finance KOSPI"}]}, "base": {"logic": "AND", "observeBy": "2026-09-10T15:20:00+09:00", "conditions": [{"id": "base-support", "description": "KOSPI가 7,000을 지킨다.", "metricId": "kospi_price", "operator": "gte", "threshold": 7000, "source": "Naver Finance KOSPI"}, {"id": "base-cap", "description": "KOSPI가 7,150 이하에 머문다.", "metricId": "kospi_price", "operator": "lte", "threshold": 7150, "source": "Naver Finance KOSPI"}]}, "bear": {"logic": "AND", "observeBy": "2026-09-10T15:20:00+09:00", "conditions": [{"id": "bear-price", "description": "KOSPI가 7,000 아래로 내려간다.", "metricId": "kospi_price", "operator": "lt", "threshold": 7000, "source": "Naver Finance KOSPI"}]}}, "hypothesisTrials": [], "posture": {"attack": 25, "wait": 55, "defense": 20}, "supersedes": None}
        forecast["contentHash"] = hashlib.sha256(json.dumps(forecast, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        dump(f"research/evaluation/forecasts/{forecast['forecastId']}.json", forecast)
        dump("research/evidence/2026-09-10/seal.json", {"forecastId": forecast["forecastId"], "issuedAt": stamp_iso, "dataCutoffAt": cutoff, "snapshotId": snapshot_id, "articleTitle": TITLE, "files": ["articles/market-2026-09-10.html", "assets/data/market-dashboard-latest.json", f"assets/data/market-dashboard-{snapshot_id}.json", "assets/images/articles/" + IMAGE, "charts/us_yield_spreads_90d_2026-09-10.png", "charts/us_yield_spreads_long_term_2026-09-10.png", "articles/index.html", "articles/market.html", "index.html", "sitemap.xml"]})
    print(("SEALED" if seal else "DRAFT"), stamp_iso, cutoff)

if __name__ == "__main__":
    main("--seal" in sys.argv)
