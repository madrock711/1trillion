"""Render the daily market comparison and weekly news-sentiment cross-correlations."""

import datetime as dt
import html
import io
import math
import re
import statistics
import textwrap

from PIL import Image, ImageDraw

from market_research_indicators import BOK_PAGE, BOK_SERIES, MARKET_INDEXES, TZ, market_history_url
from update_yield_spreads import load_font


WIDTH, HEIGHT = 900, 836
PANEL_START = '<!-- market-news-sentiment:start -->'
PANEL_END = '<!-- market-news-sentiment:end -->'
WEEK = dt.timedelta(days=7)
LAGS = range(-4, 5)
STYLES = {
    'nsi': ('뉴스심리', '#2458C6'),
    'nasdaq': ('나스닥 종합', '#B64C17'),
    'kospi': ('코스피', '#087E69'),
}


def observations(record):
    points = {}
    try:
        for row in record.get('observations', []):
            day = dt.date.fromisoformat(row['period'])
            value = row['value']
            if day in points or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                return {}
            points[day] = value
    except (AttributeError, KeyError, TypeError, ValueError):
        return {}
    return points


def news_sentiment_points(evidence, indicator_rows):
    if not any(row['source'] == BOK_PAGE for row in indicator_rows):
        return {}
    record = evidence['nsi']
    points = observations(record)
    if not points or record.get('seriesId') != BOK_SERIES:
        return {}
    latest = max(points)
    return points if latest.isoformat() == record['period'] and points[latest] == record['value'] else {}


def market_closes(evidence, index, cutoff):
    history = evidence.get('marketHistory')
    if not isinstance(history, dict):
        return {}
    record = history.get(index)
    if (not isinstance(record, dict) or record.get('status') != 'verified'
            or record.get('symbol') != MARKET_INDEXES[index][0]
            or record.get('sourceUrl') != market_history_url(index)
            or not isinstance(record.get('rawHash'), str)
            or not re.fullmatch(r'[0-9a-f]{64}', record.get('rawHash', ''))):
        return {}
    try:
        fetched = dt.datetime.fromisoformat(record['fetchedAt'])
        if fetched.utcoffset() is None or fetched.astimezone(TZ).date() != cutoff.astimezone(TZ).date() or fetched > cutoff:
            return {}
    except (KeyError, TypeError, ValueError):
        return {}
    # At 08:00 KST both prior trading sessions have closed. Also exclude a
    # partially completed US session if this is run earlier in the morning.
    close_time = dt.time(21 if index == 'nasdaq' else 6, 0 if index == 'nasdaq' else 30, tzinfo=dt.timezone.utc)
    return {
        day: value for day, value in observations(record).items()
        if day < cutoff.astimezone(TZ).date() and dt.datetime.combine(day, close_time) <= cutoff
    }


def weekly_moves(points, *, market=False):
    levels = {}
    if market:
        for day, value in sorted(points.items()):
            levels[day + dt.timedelta(days=6 - day.weekday())] = value
    else:
        levels = {day: value for day, value in points.items() if day.weekday() == 6}
    return {
        day: (value / levels[day - WEEK] - 1) * 100 if market else value - levels[day - WEEK]
        for day, value in levels.items() if day - WEEK in levels
    }


def news_market_comparison(evidence, indicator_rows, cutoff):
    sentiment = news_sentiment_points(evidence, indicator_rows)
    closes = {index: market_closes(evidence, index, cutoff) for index in MARKET_INDEXES}
    if not sentiment or any(not values for values in closes.values()):
        return None
    end = max(sentiment)
    if any((cutoff.astimezone(TZ).date() - max(values)).days > 7 for values in closes.values()):
        return None
    # Rebase all three series on one date when all three observed levels exist.
    shared = set(sentiment).intersection(*closes.values())
    candidates = [day for day in shared if end - dt.timedelta(days=89) <= day < end]
    if not candidates:
        return None
    base = min(candidates)
    levels = {'nsi': sentiment, **closes}
    lines = {
        index: [(day, 100 * value / values[base]) for day, value in sorted(values.items()) if day >= base]
        for index, values in levels.items()
    }
    nsi_moves = weekly_moves(sentiment)
    # Only use complete weeks in the comparison period. Markets can extend
    # beyond the last published sentiment observation in the daily plot.
    last_week = end - dt.timedelta(days=(end.weekday() + 1) % 7)
    prices = {index: weekly_moves({d: v for d, v in values.items() if d <= last_week}, market=True)
              for index, values in closes.items()}
    anchors = sorted(day for day in nsi_moves if all(
        day + lag * WEEK in moves for moves in prices.values() for lag in LAGS
    ))
    if len(anchors) < 20:
        return None
    changes = [nsi_moves[day] for day in anchors]
    try:
        correlations = {
            index: {lag: statistics.correlation(changes, [moves[day + lag * WEEK] for day in anchors])
                    for lag in LAGS}
            for index, moves in prices.items()
        }
        market_correlation = statistics.correlation(
            [prices['nasdaq'][day] for day in anchors], [prices['kospi'][day] for day in anchors]
        )
    except statistics.StatisticsError:
        return None
    return {
        'lines': lines, 'base': base, 'end': max(end, *(max(values) for values in closes.values())),
        'latest': {index: (max(values), values[max(values)]) for index, values in levels.items()},
        'correlations': correlations, 'market_correlation': market_correlation,
        'weeks': anchors,
    }


def draw_line(draw, points, color, *, max_gap=None, markers=False):
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if max_gap is None or x2 - x1 <= max_gap:
            draw.line((x1, y1, x2, y2), fill=color, width=4)
    for x, y in points if markers else points[-1:]:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color, outline='white', width=1)


def render_news_sentiment_chart(comparison):
    image = Image.new('RGB', (WIDTH, HEIGHT), '#F8FAFC')
    draw = ImageDraw.Draw(image)
    font, title, strong = load_font(26), load_font(32, True), load_font(26, True)
    ink, muted, grid, axis = '#152238', '#43556E', '#D6DFEB', '#8292AA'
    left, right = 82, 846

    draw.text((left, 24), '일별 추이', fill=ink, font=title)
    draw.text((right, 30), f'{comparison["base"]:%m.%d} = 100', fill=muted, font=font, anchor='ra')
    for x, (name, color) in zip((left, 309, 589), STYLES.values()):
        draw.line((x, 93, x + 33, 93), fill=color, width=5)
        draw.text((x + 44, 93), name, fill=ink, font=strong, anchor='lm')

    first, last = comparison['base'], comparison['end']
    days = (last - first).days
    values = [value for line in comparison['lines'].values() for _, value in line]
    step = max(5, 5 * math.ceil((max(values) - min(values)) / 25))
    lower = step * math.floor((min(values) - 1) / step)
    upper = step * math.ceil((max(values) + 1) / step)

    def x_day(day):
        return left + (day - first).days * (right - left) / days

    def y_level(value):
        return 411 - (value - lower) * 291 / (upper - lower)

    for value in range(lower, upper + 1, step):
        y = y_level(value)
        draw.line((left, y, right, y), fill=axis if value == 100 else grid, width=2 if value == 100 else 1)
        draw.text((left - 12, y), str(value), fill=muted, font=font, anchor='rm')
    for offset in [round(days * part / 3) for part in range(4)]:
        day = first + dt.timedelta(days=offset)
        draw.text((x_day(day), 432), f'{day:%m.%d}', fill=muted, font=font, anchor='mt')
    for index, points in comparison['lines'].items():
        draw_line(draw, [(x_day(day), y_level(value)) for day, value in points], STYLES[index][1],
                  max_gap=(right - left) / days * (1.01 if index == 'nsi' else 7.01))

    draw.line((left, 476, right, 476), fill=grid, width=2)
    draw.text((left, 492), '주간 변화의 시차별 상관계수', fill=ink, font=title)
    correlations = comparison['correlations']
    maximum = max(abs(r) for series in correlations.values() for r in series.values())
    bound = max(.4, min(1, math.ceil(maximum * 5) / 5))

    def x_lag(lag):
        return left + (lag + 4) * (right - left) / 8

    def y_r(value):
        return 643 - value * 98 / bound

    for value in (-bound, -bound / 2, 0, bound / 2, bound):
        y = y_r(value)
        draw.line((left, y, right, y), fill=axis if value == 0 else grid, width=2 if value == 0 else 1)
        draw.text((left - 12, y), f'{value:.1f}', fill=muted, font=font, anchor='rm')
    draw.line((x_lag(0), y_r(-bound), x_lag(0), y_r(bound)), fill=axis, width=2)
    for index, values in correlations.items():
        draw_line(draw, [(x_lag(lag), y_r(r)) for lag, r in values.items()], STYLES[index][1], markers=True)
    for lag in LAGS:
        draw.text((x_lag(lag), 753), f'{lag:+d}' if lag else '0', fill=muted, font=font, anchor='mt')
    draw.text((left, 796), '주가가 먼저', fill=muted, font=font)
    draw.text((right, 796), '뉴스심리가 먼저', fill=muted, font=font, anchor='ra')

    output = io.BytesIO()
    image.save(output, format='PNG', optimize=True)
    return output.getvalue()


def news_sentiment_figure(chart_path, comparison):
    nsi_date, nsi_value = comparison['latest']['nsi']
    nasdaq_date, _ = comparison['latest']['nasdaq']
    kospi_date, _ = comparison['latest']['kospi']
    weeks = comparison['weeks']
    correlations = comparison['correlations']
    nasdaq = correlations['nasdaq'][0]
    kospi = correlations['kospi'][0]
    both = comparison['market_correlation']
    return (
        '<figure class="market-news-sentiment-figure" style="margin: 1rem 0 0">\n'
        f'    <img src="../{html.escape(chart_path)}" width="{WIDTH}" height="{HEIGHT}" '
        'style="display: block; width: 100%; height: auto" loading="lazy" decoding="async" '
        'alt="뉴스심리·나스닥 종합·코스피의 일별 비교와 주간 변화의 시차별 상관계수 차트. '
        '양의 시차는 뉴스심리 관측주가 먼저인 경우입니다.">\n'
        '    <figcaption>'
        f'<p>{comparison["base"]:%Y.%m.%d}을 100으로 맞췄습니다. '
        f'뉴스심리 마지막 관측은 {nsi_date:%m.%d} <strong>{nsi_value:.2f}</strong>이며 '
        f'나스닥 종합은 {nasdaq_date:%m.%d}, 코스피는 {kospi_date:%m.%d} 정규장 종가까지 표시했습니다.</p>'
        f'<p>동일 주 상관계수는 뉴스심리·나스닥 {nasdaq:+.2f}, 뉴스심리·코스피 {kospi:+.2f}, '
        f'나스닥·코스피 {both:+.2f}입니다. {weeks[0]:%Y.%m.%d}~{weeks[-1]:%Y.%m.%d} '
        f'공통 {len(weeks)}주에서 뉴스심리의 전주 대비 변화와 각 지수의 주간 수익률을 비교했습니다. '
        '시차는 뉴스심리 관측주 기준이며 공표 시각에 따른 예측력은 별도 검증이 필요합니다.</p>'
        f'<p><a href="{BOK_PAGE}">한국은행</a> · '
        '<a href="https://finance.yahoo.com/quote/%5EIXIC/history/">나스닥 종합 종가</a> · '
        '<a href="https://finance.yahoo.com/quote/%5EKS11/history/">코스피 종가</a></p></figcaption>\n'
        '</figure>'
    )


def update_news_sentiment_panel(page, figure):
    panel = (
        '\n                <section class="market-dashboard-card" aria-labelledby="market-news-sentiment-title">\n'
        '                    <h3 id="market-news-sentiment-title">뉴스심리·나스닥·코스피</h3>\n'
        f'{textwrap.indent(figure, " " * 20)}\n'
        '                </section>'
    ) if figure else ''
    block = f'{PANEL_START}{panel}\n                {PANEL_END}'
    page, count = re.subn(f'{re.escape(PANEL_START)}.*?{re.escape(PANEL_END)}',
                         lambda _: block, page, count=1, flags=re.S)
    if count != 1:
        raise ValueError('뉴스심리지수 차트 영역을 찾을 수 없습니다.')
    return page
