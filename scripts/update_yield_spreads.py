#!/usr/bin/env python3
"""FRED의 미 국채 장단기 금리차를 장기·최근 PNG 차트로 생성한다."""

from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SERIES = {
    "T10Y2Y": {
        "label": "10Y - 2Y",
        "color": "#2563EB",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10Y2Y",
    },
    "T10Y3M": {
        "label": "10Y - 3M",
        "color": "#EA580C",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10Y3M",
    },
}
ABSOLUTE_YIELDS = {
    "DGS3MO": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO",
    "DGS2": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2",
    "DGS10": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",
}
WIDTH = 1600
HEIGHT = 900
PLOT = (120, 180, 1335, 765)


@dataclass(frozen=True)
class Observation:
    day: date
    value: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("charts"),
        help="PNG 출력 디렉터리 (기본값: charts)",
    )
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="파일명과 조회 상한 날짜 YYYY-MM-DD (기본값: 오늘)",
    )
    parser.add_argument(
        "--long-days",
        type=int,
        default=730,
        help="장기 차트 표시 일수 (기본값: 730)",
    )
    parser.add_argument(
        "--recent-days",
        type=int,
        default=90,
        help="최근 차트 표시 일수 (기본값: 90)",
    )
    return parser.parse_args()


def fetch_series(series_id: str, url: str, as_of: date) -> list[Observation]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "kospi-daily-research/1.0 (+FRED chart generator)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8-sig")

    rows: list[Observation] = []
    for row in csv.DictReader(io.StringIO(payload)):
        raw_day = row.get("observation_date") or row.get("DATE")
        raw_value = row.get(series_id)
        if not raw_day or not raw_value or raw_value == ".":
            continue
        observed_day = date.fromisoformat(raw_day)
        if observed_day <= as_of:
            rows.append(Observation(observed_day, float(raw_value)))

    if not rows:
        raise RuntimeError(f"{series_id}: {as_of.isoformat()} 이전 관측값이 없습니다.")
    return rows


def select_window(
    observations: list[Observation], as_of: date, days: int
) -> list[Observation]:
    start = as_of - timedelta(days=days)
    selected = [item for item in observations if item.day >= start]
    if not selected:
        raise RuntimeError(f"최근 {days}일 구간에 관측값이 없습니다.")
    return selected


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = (
        [Path("C:/Windows/Fonts/malgunbd.ttf"), Path("C:/Windows/Fonts/NotoSansKR-VF.ttf")]
        if bold
        else [Path("C:/Windows/Fonts/malgun.ttf"), Path("C:/Windows/Fonts/NotoSansKR-VF.ttf")]
    )
    for font_path in font_candidates:
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default(size=size)


def value_bounds(data: dict[str, list[Observation]]) -> tuple[float, float]:
    values = [item.value for observations in data.values() for item in observations]
    low = min(min(values), 0.0)
    high = max(max(values), 0.0)
    padding = max((high - low) * 0.12, 0.08)
    return low - padding, high + padding


def scale_x(day: date, start: date, end: date) -> float:
    left, _, right, _ = PLOT
    span = max((end - start).days, 1)
    return left + (day - start).days / span * (right - left)


def scale_y(value: float, low: float, high: float) -> float:
    _, top, _, bottom = PLOT
    return bottom - (value - low) / (high - low) * (bottom - top)


def text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str, **kwargs: object) -> None:
    draw.text((round(xy[0]), round(xy[1])), value, **kwargs)


def draw_axes(
    draw: ImageDraw.ImageDraw,
    start: date,
    end: date,
    low: float,
    high: float,
    recent: bool,
) -> None:
    left, top, right, bottom = PLOT
    axis_font = load_font(18)
    small_font = load_font(16)

    for step in range(6):
        value = low + (high - low) * step / 5
        y = scale_y(value, low, high)
        draw.line((left, y, right, y), fill="#E2E8F0", width=2)
        text(
            draw,
            (left - 18, y),
            f"{value:+.2f}",
            font=axis_font,
            fill="#475569",
            anchor="rm",
        )

    zero_y = scale_y(0.0, low, high)
    draw.line((left, zero_y, right, zero_y), fill="#64748B", width=3)
    draw.line((left, top, left, bottom), fill="#CBD5E1", width=2)
    draw.line((left, bottom, right, bottom), fill="#CBD5E1", width=2)

    tick_count = 7 if recent else 9
    span = max((end - start).days, 1)
    for step in range(tick_count):
        tick_day = start + timedelta(days=round(span * step / (tick_count - 1)))
        x = scale_x(tick_day, start, end)
        draw.line((x, bottom, x, bottom + 8), fill="#94A3B8", width=2)
        label = tick_day.strftime("%m-%d" if recent else "%Y-%m")
        text(
            draw,
            (x, bottom + 18),
            label,
            font=small_font,
            fill="#475569",
            anchor="ma",
        )

    text(
        draw,
        (left, top - 22),
        "Spread (%p)",
        font=small_font,
        fill="#475569",
        anchor="la",
    )


def draw_legend(draw: ImageDraw.ImageDraw) -> None:
    font = load_font(20, bold=True)
    x = PLOT[0]
    y = 148
    for meta in SERIES.values():
        draw.line((x, y, x + 40, y), fill=meta["color"], width=6)
        text(draw, (x + 53, y), meta["label"], font=font, fill="#334155", anchor="lm")
        x += 210


def draw_series(
    draw: ImageDraw.ImageDraw,
    data: dict[str, list[Observation]],
    start: date,
    end: date,
    low: float,
    high: float,
) -> None:
    for series_id, observations in data.items():
        points = [
            (scale_x(item.day, start, end), scale_y(item.value, low, high))
            for item in observations
        ]
        if len(points) > 1:
            draw.line(points, fill=SERIES[series_id]["color"], width=5, joint="curve")


def label_positions(latest_values: list[float], low: float, high: float) -> list[float]:
    raw = [scale_y(value, low, high) for value in latest_values]
    order = sorted(range(len(raw)), key=raw.__getitem__)
    minimum_gap = 72
    for upper, lower in zip(order, order[1:]):
        if raw[lower] - raw[upper] < minimum_gap:
            midpoint = (raw[lower] + raw[upper]) / 2
            raw[upper] = midpoint - minimum_gap / 2
            raw[lower] = midpoint + minimum_gap / 2
    return raw


def create_chart(
    data: dict[str, list[Observation]],
    output_path: Path,
    title: str,
    subtitle: str,
    recent: bool,
) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#F8FAFC")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((45, 35, 1555, 845), radius=28, fill="#FFFFFF", outline="#E2E8F0", width=2)

    title_font = load_font(34, bold=True)
    subtitle_font = load_font(19)
    source_font = load_font(15)
    text(draw, (90, 64), title, font=title_font, fill="#0F172A", anchor="la")
    text(draw, (90, 102), subtitle, font=subtitle_font, fill="#64748B", anchor="la")
    draw_legend(draw)

    start = min(values[0].day for values in data.values())
    end = max(values[-1].day for values in data.values())
    low, high = value_bounds(data)
    draw_axes(draw, start, end, low, high, recent)
    draw_series(draw, data, start, end, low, high)

    if recent:
        latest = [(series_id, values[-1]) for series_id, values in data.items()]
        positions = label_positions([item.value for _, item in latest], low, high)
        label_font = load_font(19, bold=True)
        date_font = load_font(16)
        label_x = 1375
        for (series_id, item), label_y in zip(latest, positions):
            meta = SERIES[series_id]
            point_x = scale_x(item.day, start, end)
            point_y = scale_y(item.value, low, high)
            draw.ellipse(
                (point_x - 8, point_y - 8, point_x + 8, point_y + 8),
                fill=meta["color"],
                outline="#FFFFFF",
                width=3,
            )
            draw.line((point_x + 9, point_y, label_x - 12, label_y), fill=meta["color"], width=2)
            text(
                draw,
                (label_x, label_y - 11),
                f"{meta['label']}  {item.value:+.2f}%p",
                font=label_font,
                fill=meta["color"],
                anchor="lm",
            )
            text(
                draw,
                (label_x, label_y + 17),
                item.day.isoformat(),
                font=date_font,
                fill="#64748B",
                anchor="lm",
            )

    latest_day = max(values[-1].day for values in data.values())
    text(
        draw,
        (90, 817),
        f"Source: Federal Reserve Bank of St. Louis (FRED), T10Y2Y and T10Y3M · latest {latest_day.isoformat()}",
        font=source_font,
        fill="#64748B",
        anchor="la",
    )
    image.save(output_path, "PNG", optimize=True)


def main() -> int:
    args = parse_args()
    if args.long_days <= 0 or args.recent_days <= 0:
        raise ValueError("표시 일수는 1 이상이어야 합니다.")

    kst = timezone(timedelta(hours=9))
    as_of = args.as_of or datetime.now(kst).date()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_data = {
        series_id: fetch_series(series_id, meta["url"], as_of)
        for series_id, meta in SERIES.items()
    }
    absolute_yields = {
        series_id: fetch_series(series_id, url, as_of)
        for series_id, url in ABSOLUTE_YIELDS.items()
    }
    long_data = {
        series_id: select_window(values, as_of, args.long_days)
        for series_id, values in all_data.items()
    }
    recent_data = {
        series_id: select_window(values, as_of, args.recent_days)
        for series_id, values in all_data.items()
    }

    stamp = as_of.isoformat()
    long_path = args.output_dir / f"us_yield_spreads_long_term_{stamp}.png"
    recent_path = args.output_dir / f"us_yield_spreads_90d_{stamp}.png"
    latest_day = max(values[-1].day for values in all_data.values())
    create_chart(
        long_data,
        long_path,
        "미국 국채 장단기 금리차 — 2년 추세",
        f"{latest_day.isoformat()}까지의 일별 관측치 · 0%p 아래는 장단기 금리 역전 구간",
        recent=False,
    )
    create_chart(
        recent_data,
        recent_path,
        "미국 국채 장단기 금리차 — 최근 90일",
        "단기금리와 장기금리의 간극이 보여주는 정책·경기 기대의 변화",
        recent=True,
    )

    for series_id, observations in all_data.items():
        latest = observations[-1]
        print(f"{series_id}: {latest.day.isoformat()} {latest.value:+.2f}%p")
    for series_id, observations in absolute_yields.items():
        latest = observations[-1]
        print(f"{series_id}: {latest.day.isoformat()} {latest.value:.2f}%")
    print(f"long_term_chart: {long_path.resolve()}")
    print(f"recent_90d_chart: {recent_path.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
