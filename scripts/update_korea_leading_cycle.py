#!/usr/bin/env python3
"""KOSIS 경기선행종합지수 순환변동치 월별 자료를 갱신한다."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "data" / "korea-leading-cycle.json"
DETAIL_URL = "https://kosis.kr/visual/economyBoard/selectDetailDataList.do?lang=ko"
SOURCE_URL = "https://kosis.kr/visual/economyBoard/economyJipyo.do?lang=ko&listId=130&unitySrvcId=641"


def fetch_series() -> dict:
    body = urllib.parse.urlencode(
        {
            "unitySrvcIdArr": "641",
            "stdIdctIdArr": "524",
            "clsfGroupCdArr": "",
            "clsfCdArr": "",
            "cyclSe": "M",
            "regionArr": "00",
            "spclBefore": "",
            "spclIncrease": "",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        DETAIL_URL,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "HPMPLab market dashboard data updater",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    observations = []
    for row in payload.get("data", []):
        period = str(row.get("wrtPnttm", ""))
        value = row.get("vl")
        if len(period) != 6 or not isinstance(value, (int, float)):
            continue
        observations.append(
            {
                "period": f"{period[:4]}-{period[4:]}",
                "value": round(float(value), 1),
            }
        )

    observations.sort(key=lambda row: row["period"])
    if len(observations) < 600:
        raise RuntimeError("KOSIS 선행지수 월별 시계열이 예상보다 짧습니다.")

    return {
        "schemaVersion": 1,
        "seriesId": "KOR_LEADING_COMPOSITE_CYCLICAL_COMPONENT",
        "label": "경기선행종합지수 순환변동치",
        "frequency": "monthly",
        "unit": "지수",
        "latestPeriod": observations[-1]["period"],
        "latestValue": observations[-1]["value"],
        "retrievedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "국가데이터처, 경기종합지수",
        "table": "경기종합지수(2020=100)(10차)",
        "tableId": "DT_1C8015",
        "sourceUrl": SOURCE_URL,
        "revisionNote": "순환변동치는 계절·불규칙 변동치 갱신에 따라 전체 시계열이 매월 수정될 수 있습니다.",
        "observations": observations,
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fetch_series(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
