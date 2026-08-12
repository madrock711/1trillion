#!/usr/bin/env python3
"""Archive completed KOSPI one-minute prices and intraday investor flows.

Historical sessions are written once as compact JSON files. The browser can
therefore render a stable multi-session chart without repeatedly downloading
the paginated Naver investor-flow pages.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "assets" / "data" / "kospi-intraday"
DEFAULT_INDEX = ROOT / "assets" / "data" / "kospi-intraday-index.json"
DEFAULT_TRADING_DAYS = ROOT / "assets" / "data" / "kodex-intraday-index.json"
MINUTE_URL = "https://api.stock.naver.com/chart/domestic/index/KOSPI/minute"
FLOW_URL = "https://finance.naver.com/sise/investorDealTrendTime.naver"
USER_AGENT = "Mozilla/5.0 (compatible; hpmplab-kospi-archive/1.0)"
MINIMUM_BARS = 300
MINIMUM_FLOW_SNAPSHOTS = 150
try:
    SEOUL = ZoneInfo("Asia/Seoul")
except ZoneInfoNotFoundError:
    SEOUL = timezone(timedelta(hours=9), name="KST")


def fetch_bytes(url: str, timeout: float = 25.0) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return response.read(), response.headers.get_content_charset() or ""


def fetch_json(url: str) -> object:
    raw, _ = fetch_bytes(url)
    return json.loads(raw.decode("utf-8"))


def fetch_text(url: str) -> str:
    raw, charset = fetch_bytes(url)
    for encoding in [charset, "euc-kr", "cp949", "utf-8"]:
        if not encoding:
            continue
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            pass
    return raw.decode("utf-8", errors="replace")


def parse_number(value: object) -> float:
    cleaned = re.sub(r"[^0-9+.-]", "", str(value or ""))
    if not cleaned:
        raise ValueError(f"not numeric: {value!r}")
    return float(cleaned)


def minute_url(date: str) -> str:
    compact = date.replace("-", "")
    return MINUTE_URL + "?" + urllib.parse.urlencode(
        {"startDateTime": compact + "0900", "endDateTime": compact + "1530"}
    )


def flow_url(date: str, page: int) -> str:
    return FLOW_URL + "?" + urllib.parse.urlencode(
        {"bizdate": date.replace("-", ""), "sosok": "01", "page": page}
    )


def normalize_minute_rows(payload: object, date: str) -> list[dict[str, object]]:
    if not isinstance(payload, list):
        raise ValueError(f"{date}: invalid minute payload")
    rows: dict[str, dict[str, object]] = {}
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        timestamp = str(raw.get("localDateTime") or "")
        if not re.fullmatch(r"\d{14}", timestamp):
            continue
        row_date = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
        time = f"{timestamp[8:10]}:{timestamp[10:12]}"
        if row_date != date or not "09:00" <= time <= "15:30":
            continue
        try:
            row = {
                "time": time,
                "open": parse_number(raw.get("openPrice")),
                "high": parse_number(raw.get("highPrice")),
                "low": parse_number(raw.get("lowPrice")),
                "close": parse_number(raw.get("currentPrice")),
                "volume": int(parse_number(raw.get("accumulatedTradingVolume"))),
            }
        except ValueError:
            continue
        if row["volume"] < 0 or row["high"] < max(row["open"], row["close"]) or row["low"] > min(row["open"], row["close"]):
            continue
        rows[time] = row
    result = [rows[key] for key in sorted(rows)]
    if len(result) < MINIMUM_BARS or result[-1]["time"] != "15:30":
        raise ValueError(f"{date}: completed minute session unavailable ({len(result)} bars)")
    return result


def extract_page_count(payload: str) -> int:
    pages = [int(value) for value in re.findall(r"(?:[?&]|&amp;)page=(\d+)", payload, flags=re.I)]
    return max([1, *pages])


def strip_cell(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).replace("\xa0", " ").strip()


def parse_flow_rows(payload: str, date: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for match in re.finditer(r"<tr[^>]*>([\s\S]*?)</tr>", payload, flags=re.I):
        cells = [strip_cell(cell) for cell in re.findall(r"<td[^>]*>([\s\S]*?)</td>", match.group(1), flags=re.I)]
        time = cells[0] if cells else ""
        if len(cells) < 4 or not re.fullmatch(r"\d{2}:\d{2}", time) or not "09:00" <= time <= "15:30":
            continue
        try:
            rows.append(
                {
                    "date": date,
                    "time": time,
                    "personal": parse_number(cells[1]),
                    "foreign": parse_number(cells[2]),
                    "institution": parse_number(cells[3]),
                }
            )
        except ValueError:
            continue
    return rows


def collect_flow_rows(date: str) -> tuple[list[dict[str, object]], int]:
    first = fetch_text(flow_url(date, 1))
    page_count = extract_page_count(first)
    if page_count > 100:
        raise ValueError(f"{date}: unexpected flow page count {page_count}")
    by_time: dict[str, dict[str, object]] = {}
    for page, payload in [(1, first), *[(page, fetch_text(flow_url(date, page))) for page in range(2, page_count + 1)]]:
        del page
        for row in parse_flow_rows(payload, date):
            by_time[str(row["time"])] = row
    rows = [by_time[key] for key in sorted(by_time)]
    if not rows:
        raise ValueError(f"{date}: intraday investor flow unavailable")
    if (
        len(rows) < MINIMUM_FLOW_SNAPSHOTS
        or str(rows[0]["time"]) > "09:10"
        or str(rows[-1]["time"]) < "15:25"
    ):
        raise ValueError(
            f"{date}: incomplete investor flow "
            f"({len(rows)} snapshots, {rows[0]['time']}..{rows[-1]['time']})"
        )
    return rows, page_count


def merge_rows(
    minute_rows: Sequence[dict[str, object]], flow_rows: Sequence[dict[str, object]]
) -> list[dict[str, object]]:
    merged: list[dict[str, object]] = []
    flow_index = 0
    latest: dict[str, object] | None = None
    for minute in minute_rows:
        while flow_index < len(flow_rows) and str(flow_rows[flow_index]["time"]) <= str(minute["time"]):
            latest = dict(flow_rows[flow_index])
            flow_index += 1
        row = dict(minute)
        row.update(
            {
                "foreign": latest.get("foreign") if latest else None,
                "institution": latest.get("institution") if latest else None,
                "personal": latest.get("personal") if latest else None,
                "flowObservedAt": latest.get("time") if latest else None,
                "flowCarriedForward": bool(latest and latest.get("time") != minute.get("time")),
                "flowUnit": "억원",
            }
        )
        merged.append(row)
    return merged


def build_day(date: str, collected_at: datetime) -> dict[str, object]:
    minute_rows = normalize_minute_rows(fetch_json(minute_url(date)), date)
    try:
        flow_rows, page_count = collect_flow_rows(date)
    except ValueError:
        flow_rows, page_count = [], 0
    bars = merge_rows(minute_rows, flow_rows)
    return {
        "schemaVersion": 1,
        "symbol": "KOSPI",
        "displayName": "KOSPI",
        "date": date,
        "interval": "1m",
        "sourceLastAt": f"{date}T{minute_rows[-1]['time']}:00+09:00",
        "flowSourceLastAt": f"{date}T{flow_rows[-1]['time']}:00+09:00" if flow_rows else None,
        "flowPageCount": page_count,
        "flowSnapshotCount": len(flow_rows),
        "minuteBars": len(bars),
        "minuteVolume": sum(int(row["volume"]) for row in bars),
        "collectedAt": collected_at.astimezone(SEOUL).isoformat(timespec="seconds"),
        "bars": bars,
    }


def load_json(path: Path, fallback: object) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def write_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def candidate_dates(path: Path, requested: Sequence[str], recent: int) -> list[str]:
    if requested:
        dates = list(dict.fromkeys(requested))
    else:
        payload = load_json(path, {})
        days = payload.get("days") if isinstance(payload, dict) else None
        dates = [str(row.get("date") or "") for row in days or [] if isinstance(row, dict)]
        dates = dates[-recent:]
    for date in dates:
        datetime.strptime(date, "%Y-%m-%d")
    return dates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recent", type=int, default=6)
    parser.add_argument("--date", action="append", default=[])
    parser.add_argument("--replace-date", action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--trading-days", type=Path, default=DEFAULT_TRADING_DAYS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.recent < 1:
        raise ValueError("--recent must be positive")
    dates = candidate_dates(args.trading_days, args.date, args.recent)
    replacements = set(args.replace_date)
    for date in replacements:
        datetime.strptime(date, "%Y-%m-%d")
    collected_at = datetime.now(timezone.utc)
    existing = load_json(
        args.index,
        {"schemaVersion": 1, "symbol": "KOSPI", "displayName": "KOSPI", "updatedAt": None, "days": []},
    )
    if not isinstance(existing, dict) or existing.get("schemaVersion") != 1 or existing.get("symbol") != "KOSPI":
        raise ValueError("existing KOSPI intraday index is invalid")
    by_date = {str(row["date"]): row for row in existing.get("days", []) if isinstance(row, dict) and row.get("date")}
    written: list[str] = []
    for date in dates:
        output = args.output_dir / f"{date}.json"
        if output.exists() and date not in replacements:
            continue
        try:
            day = build_day(date, collected_at)
        except ValueError as error:
            if args.date:
                raise
            print(f"Skip {date}: {error}")
            continue
        entry = {
            "date": date,
            "path": f"kospi-intraday/{date}.json",
            "minuteBars": day["minuteBars"],
            "flowSnapshotCount": day["flowSnapshotCount"],
            "sourceLastAt": day["sourceLastAt"],
            "flowSourceLastAt": day["flowSourceLastAt"],
            "collectedAt": day["collectedAt"],
        }
        if not args.dry_run:
            write_atomic(output, day)
        by_date[date] = entry
        written.append(date)
    if not written:
        print("No new completed KOSPI sessions.")
        return 0
    merged = dict(existing)
    merged["updatedAt"] = collected_at.astimezone(SEOUL).isoformat(timespec="seconds")
    merged["days"] = [by_date[date] for date in sorted(by_date)]
    if not args.dry_run:
        write_atomic(args.index, merged)
    print("Archived KOSPI sessions: " + ", ".join(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
