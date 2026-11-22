"""Plot the daily Bank of Korea news sentiment observations used for publication."""

import datetime as dt
import html
import io
import math
import re
import textwrap

from PIL import Image, ImageDraw

from market_research_indicators import BOK_PAGE, BOK_SERIES
from update_yield_spreads import load_font


WIDTH, HEIGHT = 860, 440
PANEL_START = '<!-- market-news-sentiment:start -->'
PANEL_END = '<!-- market-news-sentiment:end -->'


def news_sentiment_points(evidence, indicator_rows):
    """Use only dates from the source record behind the validated headline value."""
    if not any(row['source'] == BOK_PAGE for row in indicator_rows):
        return []
    record = evidence['nsi']
    if record.get('seriesId') != BOK_SERIES:
        return []
    end = dt.date.fromisoformat(record['period'])
    start = end - dt.timedelta(days=89)
    points = {}
    try:
        for row in record.get('observations', []):
            day = dt.date.fromisoformat(row['period'])
            value = row['value']
            if day > end or day in points or isinstance(value, bool) or not math.isfinite(value):
                return []
            if day >= start:
                points[day] = value
    except (KeyError, ValueError, TypeError):
        return []
    if len(points) < 2 or points.get(end) != record['value']:
        return []
    return sorted(points.items())


def render_news_sentiment_chart(points):
    """Return a PNG with a calendar-date x axis and unfilled observation gaps."""
    dates, values = zip(*points)
    first, last = dates[0], dates[-1]
    days = (last - first).days
    low, high = min(100, *values), max(100, *values)
    step = max(5, 5 * math.ceil((high - low) / 25))
    lower = step * math.floor((low - 1) / step)
    upper = step * math.ceil((high + 1) / step)
    left, right, top, bottom = 87, 812, 48, 361

    def x(day):
        return left + (day - first).days * (right - left) / days

    def y(value):
        return bottom - (value - lower) * (bottom - top) / (upper - lower)

    image = Image.new('RGB', (WIDTH, HEIGHT), '#F8FAFC')
    draw = ImageDraw.Draw(image)
    font = load_font(25)
    blue, ink, muted = '#2358C6', '#17253D', '#455770'

    for value in sorted(set(range(lower, upper + 1, step)) | {100}):
        if value != 100 and abs(y(value) - y(100)) < 29:
            continue
        is_base = value == 100
        draw.line((left, y(value), right, y(value)), fill='#8292AA' if is_base else '#D6DFEB',
                  width=2 if is_base else 1)
        draw.text((left - 13, y(value)), str(value), fill=ink if is_base else muted,
                  font=font, anchor='rm')

    for before, after in zip(points, points[1:]):
        if (after[0] - before[0]).days == 1:
            draw.line((x(before[0]), y(before[1]), x(after[0]), y(after[1])), fill=blue, width=5)
    for day, value in points:
        px, py = x(day), y(value)
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=blue)

    for offset in sorted({round(days * fraction / 3) for fraction in range(4)}):
        day = first + dt.timedelta(days=offset)
        draw.text((x(day), bottom + 18), day.strftime('%m.%d'), fill=muted, font=font, anchor='mt')

    px, py = x(last), y(values[-1])
    draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill=blue, outline='white', width=2)
    output = io.BytesIO()
    image.save(output, format='PNG', optimize=True)
    return output.getvalue()


def news_sentiment_figure(chart_path, points):
    first, last = points[0][0], points[-1][0]
    latest = f'{points[-1][1]:.2f}'
    return (
        '<figure class="market-news-sentiment-figure" style="margin: 1rem 0 0">\n'
        f'    <img src="../{html.escape(chart_path)}" width="{WIDTH}" height="{HEIGHT}" '
        'style="display: block; width: 100%; height: auto" loading="lazy" decoding="async" '
        'alt="한국은행 뉴스심리지수 일별 추이 선 차트. 가로축은 관측일이며 세로축은 지수입니다.">\n'
        f'    <figcaption>{first:%Y.%m.%d}~{last:%Y.%m.%d} 일별 추이 · 마지막 관측값 <strong>{latest}</strong>'
        f' · <a href="{BOK_PAGE}">한국은행</a></figcaption>\n'
        '</figure>'
    )


def update_news_sentiment_panel(page, figure):
    panel = (
        '\n                <section class="market-dashboard-card" aria-labelledby="market-news-sentiment-title">\n'
        '                    <h3 id="market-news-sentiment-title">한국은행 뉴스심리지수</h3>\n'
        f'{textwrap.indent(figure, " " * 20)}\n'
        '                </section>'
    ) if figure else ''
    block = f'{PANEL_START}{panel}\n                {PANEL_END}'
    page, count = re.subn(f'{re.escape(PANEL_START)}.*?{re.escape(PANEL_END)}',
                         lambda _: block, page, count=1, flags=re.S)
    if count != 1:
        raise ValueError('뉴스심리지수 차트 영역을 찾을 수 없습니다.')
    return page
