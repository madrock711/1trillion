#!/usr/bin/env python3
"""Accumulate KODEX Leveraged daily and one-minute volume-pressure estimates.

The public minute feed has a short retention window. Each completed session is
therefore archived once in a date-scoped JSON file, while the compact daily
aggregate remains available for the three-month chart.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


SYMBOL = "122630"
DISPLAY_NAME = "KODEX 레버리지"
METHOD_ID = "bvc-normal-1m-v1"
try:
    SEOUL = ZoneInfo("Asia/Seoul")
except ZoneInfoNotFoundError:
    SEOUL = timezone(timedelta(hours=9), name="KST")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "assets" / "data" / "kodex-volume-pressure.json"
DEFAULT_INTRADAY_DIR = ROOT / "assets" / "data" / "kodex-intraday"
DEFAULT_INTRADAY_INDEX = ROOT / "assets" / "data" / "kodex-intraday-index.json"
DAILY_URL = (
    "https://m.stock.naver.com/front-api/stock/domestic/price/list"
    "?code=122630&page=1&pageSize=50"
)
MINUTE_URL = "https://api.stock.naver.com/chart/domestic/item/122630/minute"
MINIMUM_BARS = 300
MINIMUM_COVERAGE = 0.95
MAXIMUM_COVERAGE = 1.005


@dataclass(frozen=True)
class MinuteBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


def parse_number(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    if isinstance(value, str):
        normalized = "".join(character for character in value if character in "+-0123456789.")
        if normalized:
            number = float(normalized)
            if math.isfinite(number):
                return number
    raise ValueError(f"invalid number: {value!r}")


def fetch_json(url: str, timeout: float = 20.0) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; hpmplab-volume-pressure/1.0)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return json.loads(response.read().decode("utf-8"))


def normalize_daily_volumes(payload: object) -> dict[str, int]:
    if not isinstance(payload, dict) or payload.get("isSuccess") is not True:
        raise ValueError("daily response is invalid")
    rows = payload.get("result")
    if not isinstance(rows, list):
        raise ValueError("daily rows are missing")
    result: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        date = str(row.get("localTradedAt") or "")
        if len(date) != 10:
            continue
        try:
            datetime.strptime(date, "%Y-%m-%d")
            volume = int(parse_number(row.get("accumulatedTradingVolume")))
        except (TypeError, ValueError):
            continue
        if volume > 0:
            result[date] = max(volume, result.get(date, 0))
    if not result:
        raise ValueError("daily volumes are empty")
    return result


def minute_request_url(date: str) -> str:
    compact = date.replace("-", "")
    query = urllib.parse.urlencode(
        {
            "startDateTime": compact + "0900",
            "endDateTime": compact + "1530",
        }
    )
    return f"{MINUTE_URL}?{query}"


def normalize_minute_bars(payload: object, expected_date: str) -> list[MinuteBar]:
    if not isinstance(payload, list):
        raise ValueError(f"{expected_date}: minute response is invalid")
    bars: list[MinuteBar] = []
    seen: set[datetime] = set()
    for row in payload:
        if not isinstance(row, dict):
            raise ValueError(f"{expected_date}: minute row is invalid")
        raw_timestamp = str(row.get("localDateTime") or "")
        try:
            timestamp = datetime.strptime(raw_timestamp, "%Y%m%d%H%M%S").replace(tzinfo=SEOUL)
            open_price = parse_number(row.get("openPrice"))
            high = parse_number(row.get("highPrice"))
            low = parse_number(row.get("lowPrice"))
            close = parse_number(row.get("currentPrice"))
            volume = int(parse_number(row.get("accumulatedTradingVolume")))
        except (TypeError, ValueError) as error:
            raise ValueError(f"{expected_date}: malformed minute row") from error
        if timestamp.strftime("%Y-%m-%d") != expected_date:
            raise ValueError(f"{expected_date}: mixed trading dates")
        if (
            timestamp in seen
            or volume < 0
            or high < max(open_price, close)
            or low > min(open_price, close)
        ):
            raise ValueError(f"{expected_date}: duplicate time or negative volume")
        seen.add(timestamp)
        bars.append(
            MinuteBar(
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
        )
    bars.sort(key=lambda bar: bar.timestamp)
    if any(left.timestamp >= right.timestamp for left, right in zip(bars, bars[1:])):
        raise ValueError(f"{expected_date}: timestamps are not increasing")
    return bars


def is_complete_session(bars: Sequence[MinuteBar]) -> bool:
    first_time = bars[0].timestamp.strftime("%H%M") if bars else ""
    return (
        len(bars) >= MINIMUM_BARS
        and "0900" <= first_time <= "0905"
        and bars[-1].timestamp.strftime("%H%M") == "1530"
    )


def estimate_sigma(sessions: Iterable[Sequence[MinuteBar]]) -> tuple[float, int]:
    changes: list[float] = []
    for bars in sessions:
        changes.extend(current.close - previous.close for previous, current in zip(bars, bars[1:]))
    if len(changes) < 2:
        raise ValueError("not enough minute changes for volatility")
    sigma = statistics.stdev(changes)
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError("minute volatility is invalid")
    return sigma, len(changes)


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def estimate_minute_rows(bars: Sequence[MinuteBar], sigma: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    cumulative_delta = 0
    for index, bar in enumerate(bars):
        neutral = index == 0 or bar.timestamp.strftime("%H%M") >= "1520"
        if neutral:
            buy_share = 0.5
        else:
            change = bar.close - bars[index - 1].close
            buy_share = normal_cdf(change / sigma)
        estimated_buy = max(0, min(bar.volume, int(round(bar.volume * buy_share))))
        estimated_sell = bar.volume - estimated_buy
        delta = estimated_buy - estimated_sell
        cumulative_delta += delta
        rows.append(
            {
                "time": bar.timestamp.strftime("%H:%M"),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "estimatedBuyVolume": estimated_buy,
                "estimatedSellVolume": estimated_sell,
                "delta": delta,
                "cumulativeDelta": cumulative_delta,
                "neutral": neutral,
            }
        )
    return rows


def estimate_day(
    date: str,
    bars: Sequence[MinuteBar],
    daily_volume: int,
    sigma: float,
    sigma_sample_size: int,
    collected_at: datetime,
) -> dict[str, object]:
    if not is_complete_session(bars):
        raise ValueError(f"{date}: session is incomplete")
    minute_volume = sum(bar.volume for bar in bars)
    if daily_volume <= 0 or minute_volume <= 0:
        raise ValueError(f"{date}: volume is missing")
    coverage = minute_volume / daily_volume
    if coverage < MINIMUM_COVERAGE or coverage > MAXIMUM_COVERAGE:
        raise ValueError(f"{date}: minute coverage {coverage:.4f} is outside the accepted range")

    estimated_buy = 0.0
    estimated_sell = 0.0
    neutral_volume = 0
    for index, bar in enumerate(bars):
        is_auction = index == 0 or bar.timestamp.strftime("%H%M") >= "1520"
        if is_auction:
            buy_share = 0.5
            neutral_volume += bar.volume
        else:
            change = bar.close - bars[index - 1].close
            buy_share = normal_cdf(change / sigma)
        estimated_buy += bar.volume * buy_share
        estimated_sell += bar.volume * (1.0 - buy_share)

    uncovered_volume = daily_volume - minute_volume
    if uncovered_volume < 0:
        raise ValueError(f"{date}: minute volume exceeds daily volume")
    neutral_volume += uncovered_volume
    estimated_buy += uncovered_volume / 2.0
    estimated_sell += uncovered_volume / 2.0

    rounded_buy = int(round(estimated_buy))
    rounded_buy = max(0, min(daily_volume, rounded_buy))
    rounded_sell = daily_volume - rounded_buy
    if rounded_buy + rounded_sell != daily_volume:
        raise AssertionError("estimated volumes do not conserve the daily total")

    return {
        "date": date,
        "dailyVolume": daily_volume,
        "minuteVolume": minute_volume,
        "estimatedBuyVolume": rounded_buy,
        "estimatedSellVolume": rounded_sell,
        "buyShare": round(rounded_buy / daily_volume, 6),
        "sellShare": round(rounded_sell / daily_volume, 6),
        "minuteBars": len(bars),
        "coverageRatio": round(coverage, 6),
        "neutralVolume": neutral_volume,
        "sourceLastAt": bars[-1].timestamp.isoformat(),
        "method": METHOD_ID,
        "sigma": round(sigma, 6),
        "sigmaSampleSize": sigma_sample_size,
        "collectedAt": collected_at.astimezone(SEOUL).isoformat(timespec="seconds"),
    }


def build_intraday_day(
    date: str,
    bars: Sequence[MinuteBar],
    daily_volume: int,
    sigma: float,
    sigma_sample_size: int,
    collected_at: datetime,
) -> dict[str, object]:
    if not is_complete_session(bars):
        raise ValueError(f"{date}: session is incomplete")
    minute_volume = sum(bar.volume for bar in bars)
    coverage = minute_volume / daily_volume
    if coverage < MINIMUM_COVERAGE or coverage > MAXIMUM_COVERAGE:
        raise ValueError(f"{date}: minute coverage {coverage:.4f} is outside the accepted range")
    return {
        "schemaVersion": 1,
        "symbol": SYMBOL,
        "displayName": DISPLAY_NAME,
        "date": date,
        "interval": "1m",
        "method": METHOD_ID,
        "dailyVolume": daily_volume,
        "minuteVolume": minute_volume,
        "coverageRatio": round(coverage, 6),
        "minuteBars": len(bars),
        "sourceLastAt": bars[-1].timestamp.isoformat(),
        "sigma": round(sigma, 6),
        "sigmaSampleSize": sigma_sample_size,
        "collectedAt": collected_at.astimezone(SEOUL).isoformat(timespec="seconds"),
        "bars": estimate_minute_rows(bars, sigma),
    }


def empty_archive() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "symbol": SYMBOL,
        "displayName": DISPLAY_NAME,
        "method": {
            "id": METHOD_ID,
            "interval": "1m",
            "label": "분봉 기반 추정 매수·매도 압력",
            "buyColor": "#ff4f5e",
            "sellColor": "#4f8dff",
        },
        "updatedAt": None,
        "days": [],
    }


def load_archive(path: Path) -> dict[str, object]:
    if not path.exists():
        return empty_archive()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(payload, dict)
        or payload.get("schemaVersion") != 1
        or payload.get("symbol") != SYMBOL
        or not isinstance(payload.get("days"), list)
    ):
        raise ValueError("existing volume-pressure archive has an unsupported schema")
    return payload


def merge_days(
    archive: dict[str, object],
    incoming: Sequence[dict[str, object]],
    collected_at: datetime,
    replace_dates: set[str] | None = None,
) -> tuple[dict[str, object], list[str]]:
    replacements = replace_dates or set()
    existing_days = archive.get("days")
    if not isinstance(existing_days, list):
        raise ValueError("archive days are invalid")
    by_date: dict[str, dict[str, object]] = {}
    for row in existing_days:
        if not isinstance(row, dict) or not isinstance(row.get("date"), str):
            raise ValueError("archive day is invalid")
        by_date[str(row["date"])] = row

    added: list[str] = []
    for row in incoming:
        date = str(row.get("date") or "")
        if date in by_date and date not in replacements:
            continue
        by_date[date] = row
        added.append(date)
    if not added:
        return archive, []

    merged = dict(archive)
    merged["method"] = empty_archive()["method"]
    merged["updatedAt"] = collected_at.astimezone(SEOUL).isoformat(timespec="seconds")
    merged["days"] = [by_date[date] for date in sorted(by_date)]
    return merged, sorted(added)


def serialize_archive(archive: dict[str, object]) -> str:
    return json.dumps(archive, ensure_ascii=False, indent=2) + "\n"


def empty_intraday_index() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "symbol": SYMBOL,
        "displayName": DISPLAY_NAME,
        "method": empty_archive()["method"],
        "updatedAt": None,
        "days": [],
    }


def load_intraday_index(path: Path) -> dict[str, object]:
    if not path.exists():
        return empty_intraday_index()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(payload, dict)
        or payload.get("schemaVersion") != 1
        or payload.get("symbol") != SYMBOL
        or not isinstance(payload.get("days"), list)
    ):
        raise ValueError("existing intraday index has an unsupported schema")
    return payload


def merge_intraday_index(
    index: dict[str, object],
    incoming: Sequence[dict[str, object]],
    collected_at: datetime,
) -> dict[str, object]:
    rows = index.get("days")
    if not isinstance(rows, list):
        raise ValueError("intraday index days are invalid")
    by_date: dict[str, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("date"), str):
            raise ValueError("intraday index day is invalid")
        by_date[str(row["date"])] = row
    for row in incoming:
        by_date[str(row["date"])] = row
    merged = dict(index)
    merged["method"] = empty_archive()["method"]
    merged["updatedAt"] = collected_at.astimezone(SEOUL).isoformat(timespec="seconds")
    merged["days"] = [by_date[date] for date in sorted(by_date)]
    return merged


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def collect_sessions(
    daily_volumes: dict[str, int],
    requested_dates: Sequence[str],
    recent: int,
) -> dict[str, list[MinuteBar]]:
    candidates = list(requested_dates) if requested_dates else sorted(daily_volumes, reverse=True)
    sessions: dict[str, list[MinuteBar]] = {}
    for date in candidates:
        if date not in daily_volumes:
            if requested_dates:
                raise ValueError(f"{date}: daily volume was not found")
            continue
        bars = normalize_minute_bars(fetch_json(minute_request_url(date)), date)
        if not is_complete_session(bars):
            if requested_dates:
                raise ValueError(f"{date}: completed minute session was not found")
            continue
        sessions[date] = bars
        if not requested_dates and len(sessions) >= recent:
            break
    if not sessions:
        raise ValueError("no completed minute sessions were found")

    return sessions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recent", type=int, default=6, help="number of recent completed sessions to inspect")
    parser.add_argument("--date", action="append", default=[], help="specific YYYY-MM-DD session (repeatable)")
    parser.add_argument("--replace-date", action="append", default=[], help="explicitly replace an archived date")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--intraday-index", type=Path, default=DEFAULT_INTRADAY_INDEX)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.recent < 1:
        raise ValueError("--recent must be positive")
    for date in args.date + args.replace_date:
        datetime.strptime(date, "%Y-%m-%d")

    collected_at = datetime.now(timezone.utc)
    archive = load_archive(args.output)
    intraday_index = load_intraday_index(args.intraday_index)
    daily_volumes = normalize_daily_volumes(fetch_json(DAILY_URL))
    sessions = collect_sessions(daily_volumes, args.date, args.recent)
    sigma, sample_size = estimate_sigma(sessions.values())
    estimates = [
        estimate_day(
            date,
            sessions[date],
            daily_volumes[date],
            sigma,
            sample_size,
            collected_at,
        )
        for date in sorted(sessions)
    ]
    merged, changed_dates = merge_days(archive, estimates, collected_at, set(args.replace_date))
    replace_dates = set(args.replace_date)
    intraday_days: list[dict[str, object]] = []
    intraday_entries: list[dict[str, object]] = []
    for date in sorted(sessions):
        output_path = args.intraday_dir / f"{date}.json"
        if output_path.exists() and date not in replace_dates:
            continue
        day = build_intraday_day(
            date,
            sessions[date],
            daily_volumes[date],
            sigma,
            sample_size,
            collected_at,
        )
        intraday_days.append(day)
        intraday_entries.append(
            {
                "date": date,
                "path": f"kodex-intraday/{date}.json",
                "minuteBars": day["minuteBars"],
                "coverageRatio": day["coverageRatio"],
                "sourceLastAt": day["sourceLastAt"],
                "collectedAt": day["collectedAt"],
            }
        )

    if not changed_dates and not intraday_days:
        print("No new completed trading days.")
        return 0

    if changed_dates:
        print("Added volume-pressure estimates: " + ", ".join(changed_dates))
    if intraday_days:
        print("Archived one-minute sessions: " + ", ".join(str(day["date"]) for day in intraday_days))
    if args.dry_run:
        return 0
    if changed_dates:
        write_atomic(args.output, serialize_archive(merged))
    for day in intraday_days:
        write_atomic(args.intraday_dir / f"{day['date']}.json", serialize_archive(day))
    if intraday_entries:
        updated_index = merge_intraday_index(intraday_index, intraday_entries, collected_at)
        write_atomic(args.intraday_index, serialize_archive(updated_index))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
