#!/usr/bin/env python3
"""Naver Finance의 KOSPI 월봉을 1990년부터 현재까지 갱신한다."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "data" / "kospi-monthly-history.json"
SOURCE_URL = "https://fchart.stock.naver.com/sise.nhn"
ITEM_PATTERN = re.compile(r'data="(\d{8})\|([^\"]+)"')


def fetch_page(request_type: int, start_time: str | None = None) -> list[dict]:
    params = {
        "symbol": "KOSPI",
        "timeframe": "month",
        "count": "120",
        "requestType": str(request_type),
    }
    if start_time:
        params["startTime"] = start_time
    request = urllib.request.Request(
        SOURCE_URL + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "HPMPLab market dashboard data updater"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode("euc-kr", errors="replace")

    rows = []
    for match in ITEM_PATTERN.finditer(text):
        values = match.group(2).split("|")
        if len(values) != 5:
            continue
        try:
            rows.append(
                {
                    "date": f"{match.group(1)[:4]}-{match.group(1)[4:6]}-{match.group(1)[6:]}",
                    "open": round(float(values[0]), 2),
                    "high": round(float(values[1]), 2),
                    "low": round(float(values[2]), 2),
                    "close": round(float(values[3]), 2),
                    "volume": int(float(values[4])),
                }
            )
        except ValueError:
            continue
    return rows


def fetch_series() -> dict:
    by_date = {row["date"]: row for row in fetch_page(0)}
    while by_date:
        earliest = min(by_date)
        older = fetch_page(2, earliest.replace("-", ""))
        added = 0
        for row in older:
            if row["date"] not in by_date:
                by_date[row["date"]] = row
                added += 1
        if not added:
            break

    observations = [by_date[key] for key in sorted(by_date)]
    if len(observations) < 400 or observations[0]["date"][:7] != "1990-01":
        raise RuntimeError("KOSPI 월봉 시계열이 예상보다 짧습니다.")

    return {
        "schemaVersion": 1,
        "seriesId": "KOSPI_MONTHLY_OHLCV",
        "label": "KOSPI 월봉",
        "frequency": "monthly",
        "unit": "지수",
        "firstPeriod": observations[0]["date"][:7],
        "latestPeriod": observations[-1]["date"][:7],
        "latestValue": observations[-1]["close"],
        "retrievedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "Naver Finance KOSPI 월봉",
        "sourceUrl": SOURCE_URL + "?symbol=KOSPI&timeframe=month&count=120&requestType=0",
        "observations": observations,
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fetch_series(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
