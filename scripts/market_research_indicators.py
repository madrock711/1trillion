"""Collect official Korean news sentiment and the monthly leading cycle."""

import concurrent.futures
import datetime as dt
import hashlib
import html
import io
import json
import math
import re
import statistics
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from update_korea_leading_cycle import DETAIL_URL, SOURCE_URL, fetch_series

TZ = dt.timezone(dt.timedelta(hours=9))
BOK_PAGE = "https://snapshot.bok.or.kr/dashboard/C8"
BOK_META = "https://snapshot.bok.or.kr/api/chart/getChartInfo?chart_ids=956"
BOK_EXPORT = "https://snapshot.bok.or.kr/api/chart/exportChart?chart_id=956"
BOK_SERIES = "NECOS-523U001-D-A001"
FILENAME = "research-indicators.json"
MARKET_INDEXES = {"nasdaq": ("^IXIC", "America/New_York"), "kospi": ("^KS11", "Asia/Seoul")}
MARKET_HISTORY_DAYS = 730
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
MAX_RESPONSE = 2_000_000


def read_bok(url):
    request = urllib.request.Request(url, headers={"User-Agent": "HPMPLab market research"})
    with urllib.request.urlopen(request, timeout=8) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("Unexpected BOK response size")
    return raw


def parse_nsi_export(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as workbook:
        sheets = ["xl/sharedStrings.xml", "xl/worksheets/sheet1.xml"]
        if any(workbook.getinfo(path).file_size > 8_000_000 for path in sheets):
            raise ValueError("Unexpected BOK workbook size")
        strings = [
            "".join(node.text or "" for node in item.iter(NS + "t"))
            for item in ET.fromstring(workbook.read(sheets[0]))
        ]
        rows = ET.fromstring(workbook.read(sheets[1])).iter(NS + "row")

    metadata, points = {}, {}
    for row in rows:
        cells = {}
        for cell in row.findall(NS + "c"):
            value = cell.findtext(NS + "v")
            if value is not None:
                column = re.sub(r"\d+$", "", cell.attrib["r"])
                cells[column] = strings[int(value)] if cell.get("t") == "s" else value
        label, value = cells.get("A", ""), cells.get("B")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", label):
            metadata[label] = value
            continue
        day = dt.date.fromisoformat(label)
        if day in points:
            raise ValueError("Duplicate observation in BOK workbook")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Non-finite BOK value")
        points[day] = round(number, 2)
    if (
        metadata.get("출처") != "ECOS"
        or metadata.get("범례명") != "뉴스심리지수"
        or metadata.get("주기") != "일"
        or not points
    ):
        raise ValueError("Unexpected series in BOK workbook")
    return points


def month_before(day, offset):
    year, month = divmod(day.year * 12 + day.month - 1 - offset, 12)
    return dt.date(year, month + 1, 1)


def date_range(start, end):
    return (start + dt.timedelta(days=i) for i in range((end - start).days))


def summarize_nsi(points, as_of):
    latest = max(points)
    if not 1 <= (as_of - latest).days <= 14:
        raise ValueError("Latest BOK date is stale or outside the available window")
    weekly = latest - dt.timedelta(days=7)
    # A month's daily readings must all be present before it enters the average.
    end = latest.replace(day=1)
    if (latest + dt.timedelta(days=1)).month != latest.month:
        end = month_before(latest, -1)
    months = []
    for offset in (4, 3, 2, 1):
        first = month_before(end, offset)
        rows = [points.get(day) for day in date_range(first, month_before(first, -1))]
        months.append(statistics.mean(rows) if all(value is not None for value in rows) else None)
    moving = statistics.mean(months[1:]) if None not in months[1:] else None
    prior = statistics.mean(months[:3]) if None not in months[:3] else None
    history_start = min(month_before(end, 4), latest - dt.timedelta(days=MARKET_HISTORY_DAYS))
    return {
        "period": latest.isoformat(),
        "value": points[latest],
        "change7d": round(points[latest] - points[weekly], 2) if weekly in points else None,
        "average3m": round(moving, 2) if moving is not None else None,
        "average3mPeriod": month_before(end, 1).strftime("%Y-%m") if moving is not None else None,
        "average3mChange": round(moving - prior, 2) if moving is not None and prior is not None else None,
        "observations": [
            {"period": day.isoformat(), "value": value}
            for day, value in sorted(points.items())
            if day >= history_start
        ],
    }


def fetch_nsi(as_of):
    metadata = read_bok(BOK_META)
    response = json.loads(metadata)
    charts = {chart["chart_id"]: chart for chart in response["data"]}
    series = [row["series_id"] for row in json.loads(charts[956]["tmsrs_ids"])]
    if response["resultCd"] != 0 or series != [BOK_SERIES]:
        raise ValueError("Unexpected BOK chart series ID")
    raw = read_bok(BOK_EXPORT)
    return dict(
        summarize_nsi(parse_nsi_export(raw), as_of),
        seriesId=BOK_SERIES, rawHash=hashlib.sha256(raw).hexdigest(),
        metadataHash=hashlib.sha256(metadata).hexdigest(), dataUrl=BOK_EXPORT,
    )


def fetch_leading(as_of):
    response = fetch_series(timeout=9)
    observations = response["observations"][-2:]
    previous, latest = observations
    month = dt.date.fromisoformat(latest["period"] + "-01")
    if (
        not month_before(as_of, 3) <= month < as_of.replace(day=1)
        or previous["period"] != month_before(month, 1).strftime("%Y-%m")
        or not all(math.isfinite(row["value"]) for row in observations)
    ):
        raise ValueError("KOSIS months are stale, invalid or nonconsecutive")
    return dict(
        latest, change=round(latest["value"] - previous["value"], 1),
        observations=observations, tableId=response["tableId"],
        rawHash=response["rawHash"], dataUrl=DETAIL_URL,
    )


def market_history_url(index):
    symbol, _ = MARKET_INDEXES[index]
    return (f"https://query1.finance.yahoo.com/v8/finance/chart/%5E{symbol[1:]}"
            "?range=2y&interval=1d&includePrePost=false")


def fetch_market_history(index):
    symbol, zone = MARKET_INDEXES[index]
    url = market_history_url(index)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=8) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("Unexpected market history response size")
    result, = json.loads(raw)["chart"]["result"]
    metadata = result["meta"]
    if (metadata.get("symbol"), metadata.get("exchangeTimezoneName"), metadata.get("instrumentType")) != (symbol, zone, "INDEX"):
        raise ValueError("Unexpected index symbol or exchange")
    quotes = result["indicators"]["quote"][0]
    observations = []
    for stamp, close in zip(result["timestamp"], quotes["close"], strict=True):
        if close is None:
            continue
        if isinstance(close, bool) or not math.isfinite(close) or close <= 0:
            raise ValueError("Invalid closing level")
        # These equity sessions open and close within the same UTC calendar day.
        day = dt.datetime.fromtimestamp(stamp, dt.timezone.utc).date()
        observations.append({"period": day.isoformat(), "value": round(close, 2)})
    if not observations:
        raise ValueError("No closing levels")
    return dict(symbol=symbol, rawHash=hashlib.sha256(raw).hexdigest(), observations=observations)


def collect_indicators(output):
    as_of = dt.datetime.now(TZ).date()

    def capture(fetch, source, *args):
        try:
            record = dict(fetch(*args), status="verified")
        except Exception as error:
            record = {"status": "unavailable", "error": f"{type(error).__name__}: {error}"}
        return dict(record, sourceUrl=source, fetchedAt=dt.datetime.now(TZ).isoformat())

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        nsi = pool.submit(capture, fetch_nsi, BOK_PAGE, as_of)
        leading = pool.submit(capture, fetch_leading, SOURCE_URL, as_of)
        histories = {
            index: pool.submit(capture, fetch_market_history, market_history_url(index), index)
            for index in MARKET_INDEXES
        }
        data = {"schemaVersion": 1, "nsi": nsi.result(), "leading": leading.result(),
                "marketHistory": {index: pending.result() for index, pending in histories.items()}}
    path = output / FILENAME
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def indicator_rows(data, cutoff):
    """Return published observations from a traceable same-day collection."""
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        return []
    cutoff = cutoff.astimezone(TZ)
    rows = []
    for key, source, label, precision, delta_key in [
        ("nsi", BOK_PAGE, "한국은행 뉴스심리지수", 2, "change7d"),
        ("leading", SOURCE_URL, "경기선행종합지수 순환변동치", 1, "change"),
    ]:
        record = data.get(key, {})
        if not isinstance(record, dict) or record.get("status") != "verified" or record.get("sourceUrl") != source:
            continue
        try:
            fetched = dt.datetime.fromisoformat(record["fetchedAt"])
            if fetched.utcoffset() is None:
                continue
            fetched = fetched.astimezone(TZ)
            period = record["period"]
            value = record["value"]
            delta = record.get(delta_key)
            date = dt.date.fromisoformat(period if key == "nsi" else period + "-01")
            earliest = cutoff.date() - dt.timedelta(days=14) if key == "nsi" else month_before(cutoff.date(), 3)
            latest = cutoff.date() if key == "nsi" else cutoff.date().replace(day=1)
            if fetched.date() != cutoff.date() or fetched > cutoff or not earliest <= date < latest:
                continue
            if not math.isfinite(value) or (delta is not None and not math.isfinite(delta)):
                continue
            if not re.fullmatch(r"[0-9a-f]{64}", record.get("rawHash", "")):
                continue
        except (KeyError, ValueError, TypeError):
            continue
        comparison = "7일 전보다" if key == "nsi" else "전월보다"
        detail = f"{period} {'관측 · 주간 공표' if key == 'nsi' else '기준'}"
        detail += describe_change(delta, precision, comparison)
        rows.append({"label": label, "value": f"{value:.{precision}f}", "detail": detail, "source": source})
        if key == "nsi" and record.get("average3m") is not None:
            average = record["average3m"]
            average_period = record.get("average3mPeriod", "")
            if isinstance(average, (float, int)) and math.isfinite(average) and re.fullmatch(r"\d{4}-\d{2}", average_period):
                rows.append({
                    "label": "뉴스심리지수 3개월 평균", "value": f"{average:.2f}",
                    "detail": f"{average_period}까지 3개월 · 일별 지수의 월평균 사용"
                    + describe_change(record.get("average3mChange"), 2, "한 달 전 3개월 평균보다"),
                    "source": source,
                })
    return rows


def describe_change(delta, precision, comparison):
    if not isinstance(delta, (int, float)) or not math.isfinite(delta):
        return ""
    if delta == 0:
        return f" · {comparison} 변화 없음"
    direction = "상승" if delta > 0 else "하락"
    return f" · {comparison} {abs(delta):.{precision}f}포인트 {direction}"


def render_indicator_block(rows):
    if not rows:
        return "", ""
    title = "국내 뉴스심리와 경기선행지수"
    body = "".join(
        f'<li>{html.escape(row["label"])} {row["value"]} · {html.escape(row["detail"])} '
        f'<a href="{html.escape(row["source"], quote=True)}">출처</a></li>'
        for row in rows
    )
    markdown = "".join(
        f'- [{row["label"]}]({row["source"]}) {row["value"]} · {row["detail"]}\n' for row in rows
    )
    return f"<h2>{title}</h2><ul>{body}</ul>\n", f"\n\n## {title}\n\n{markdown}"
