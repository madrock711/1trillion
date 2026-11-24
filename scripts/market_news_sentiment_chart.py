"""Render daily levels and aligned weekly changes and correlations."""

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


WIDTH, HEIGHT = 900, 1322
PANEL_START = '<!-- market-news-sentiment:start -->'
PANEL_END = '<!-- market-news-sentiment:end -->'
WEEK = dt.timedelta(days=7)
CORRELATION_WEEKS = 12
STYLES = {
    'nsi': ('뉴스심리', '#2458C6'),
    'nasdaq': ('나스닥 종합', '#B64C17'),
    'kospi': ('코스피', '#087E69'),
}
CORRELATION_PAIRS = (
    ('nsi', 'nasdaq', '뉴스심리·나스닥', '#B64C17'),
    ('nsi', 'kospi', '뉴스심리·코스피', '#087E69'),
    ('nasdaq', 'kospi', '나스닥·코스피', '#6B50A0'),
)


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
    # A daily bar is usable only if its session had closed when it was fetched.
    close_time = dt.time(21 if index == 'nasdaq' else 6, 0 if index == 'nasdaq' else 30, tzinfo=dt.timezone.utc)
    return {
        day: value for day, value in observations(record).items()
        if dt.datetime.combine(day, close_time) <= fetched
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


def rolling_weekly_correlations(moves, weeks):
    correlations = {(first, second): {} for first, second, _, _ in CORRELATION_PAIRS}
    for end in weeks:
        window = [end - WEEK * offset for offset in reversed(range(CORRELATION_WEEKS))]
        dates = set(window)
        if not all(dates <= values.keys() for values in moves.values()):
            continue
        for (first, second), values in correlations.items():
            try:
                values[end] = statistics.correlation(
                    [moves[first][date] for date in window],
                    [moves[second][date] for date in window],
                )
            except statistics.StatisticsError:
                continue
    return correlations


def news_market_comparison(evidence, indicator_rows, cutoff, *, verified_kospi_close=None):
    sentiment = news_sentiment_points(evidence, indicator_rows)
    closes = {index: market_closes(evidence, index, cutoff) for index in MARKET_INDEXES}
    supplemented = False
    if verified_kospi_close is not None:
        session, value = verified_kospi_close
        if session < cutoff.astimezone(TZ).date() and math.isfinite(value) and value > 0:
            supplemented = closes['kospi'].get(session) != value
            closes['kospi'][session] = value
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
    # Share actual weekly dates. The daily plot may include a later partial week.
    last_week = end - dt.timedelta(days=(end.weekday() + 1) % 7)
    moves = {'nsi': weekly_moves(sentiment)}
    moves.update({
        index: weekly_moves({day: value for day, value in values.items() if day <= last_week}, market=True)
        for index, values in closes.items()
    })
    weekly_lines = {
        index: {day: value for day, value in values.items() if base <= day <= last_week}
        for index, values in moves.items()
    }
    weeks = sorted({day for values in weekly_lines.values() for day in values})
    if len(weeks) < 2 or any(not values for values in weekly_lines.values()):
        return None
    return {
        'lines': lines, 'base': base, 'end': max(end, *(max(values) for values in closes.values())),
        'latest': {index: (max(values), values[max(values)]) for index, values in levels.items()},
        'weekly_lines': weekly_lines,
        'weekly_correlations': rolling_weekly_correlations(moves, weeks),
        'weeks': weeks,
        'kospi_close_supplemented': supplemented,
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
    draw.text((left, 492), '주간 변화와 상관계수', fill=ink, font=title)
    draw.text((left, 535), '같은 세로선은 같은 주를 가리킵니다.', fill=muted, font=font)
    weeks = comparison['weeks']
    weekly = comparison['weekly_lines']
    week_span = (weeks[-1] - weeks[0]).days
    tick_intervals = min(4, len(weeks) - 1)
    date_ticks = [weeks[round((len(weeks) - 1) * step / tick_intervals)]
                  for step in range(tick_intervals + 1)]

    def x_week(day):
        return left + (day - weeks[0]).days * (right - left) / week_span

    for week in date_ticks:
        x = x_week(week)
        draw.line((x, 627, x, 1237), fill=grid, width=1)
        draw.text((x, 1255), f'{week:%m.%d}', fill=muted, font=font, anchor='mt')

    def draw_week_panel(top, bottom, bound, series):
        def y(value):
            return (top + bottom) / 2 - value / bound * (bottom - top) / 2

        for level in (-bound, 0, bound):
            draw.line((left, y(level), right, y(level)), fill=axis if level == 0 else grid,
                      width=2 if level == 0 else 1)
            draw.text((left - 12, y(level)), f'{level:g}', fill=muted, font=font, anchor='rm')
        for values, color in series:
            points = [(x_week(day), y(value)) for day, value in sorted(values.items())]
            draw_line(draw, points, color, max_gap=(right - left) * 7.01 / week_span, markers=True)

    equity_bound = 5 * max(1, math.ceil(max(abs(value) for key in MARKET_INDEXES
                                             for value in weekly[key].values()) / 5))
    sentiment_bound = 5 * max(1, math.ceil(max(abs(value) for value in weekly['nsi'].values()) / 5))
    for (index, (name, color)), top in zip(STYLES.items(), (627, 777, 927)):
        is_sentiment = index == 'nsi'
        unit = 'p' if is_sentiment else '%'
        draw.text((left + 8, top - 31), f'{name} ({unit})', fill=color, font=strong, anchor='lm')
        draw_week_panel(top, top + 102, sentiment_bound if is_sentiment else equity_bound,
                        [(weekly[index], color)])

    draw.text((left + 8, 1074), f'최근 {CORRELATION_WEEKS}주 상관계수', fill=ink, font=strong, anchor='lm')
    legend_font = load_font(22)
    for x, (_, _, label, color) in zip((left, 339, 597), CORRELATION_PAIRS):
        draw.line((x + 8, 1113, x + 32, 1113), fill=color, width=4)
        draw.text((x + 41, 1113), label, fill=ink, font=legend_font, anchor='lm')
    correlations = comparison['weekly_correlations']
    draw_week_panel(1138, 1237, 1, [(correlations[first, second], color)
                                  for first, second, _, color in CORRELATION_PAIRS])
    draw.text(((left + right) / 2, 1290), '각 주의 일요일 날짜', fill=ink, font=font, anchor='mt')

    output = io.BytesIO()
    image.save(output, format='PNG', optimize=True)
    return output.getvalue()


def news_sentiment_figure(chart_path, comparison):
    nsi_date, nsi_value = comparison['latest']['nsi']
    nasdaq_date, nasdaq_close = comparison['latest']['nasdaq']
    kospi_date, kospi_close = comparison['latest']['kospi']
    weeks = comparison['weeks']
    weekly = comparison['weekly_lines']
    correlations = comparison['weekly_correlations']
    columns = [(weekly[index], unit) for index, unit in (('nsi', 'p'), ('nasdaq', '%'), ('kospi', '%'))]
    columns.extend((correlations[first, second], '') for first, second, _, _ in CORRELATION_PAIRS)
    headings = ('주 종료일', '뉴스심리 변화', '나스닥 수익률', '코스피 수익률',
                *(label for _, _, label, _ in CORRELATION_PAIRS))
    table_head = ''.join(f'<th scope="col">{label}</th>' for label in headings)
    table_rows = []
    for week in reversed(weeks):
        cells = [
            f'{values[week]:+.2f}{unit}' if week in values else '—'
            for values, unit in columns
        ]
        table_rows.append(f'<tr><th scope="row">{week:%Y.%m.%d}</th>'
                          + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>')
    kospi_daily = (
        ' · <a href="https://finance.naver.com/sise/sise_index_day.naver?code=KOSPI">코스피 전일 종가</a>'
        if comparison['kospi_close_supplemented'] else ''
    )
    return (
        '<figure class="market-news-sentiment-figure" style="margin: 1rem 0 0">\n'
        f'    <img src="../{html.escape(chart_path)}" width="{WIDTH}" height="{HEIGHT}" '
        'style="display: block; width: 100%; height: auto" loading="lazy" decoding="async" '
        'alt="뉴스심리·나스닥 종합·코스피의 일별 추이와 실제 날짜에 맞춘 주간 변화 및 상관계수.">\n'
        '    <figcaption>'
        f'<p>세 지표는 {comparison["base"]:%Y.%m.%d} 기준으로 100에서 시작합니다. '
        f'뉴스심리 최신 관측치는 {nsi_date:%m.%d} <strong>{nsi_value:.2f}</strong>입니다. '
        f'최신 정규장 종가는 나스닥 종합 {nasdaq_date:%m.%d} {nasdaq_close:,.2f}, '
        f'코스피 {kospi_date:%m.%d} {kospi_close:,.2f}입니다.</p>'
        '<p>한 주는 월요일부터 일요일까지입니다. 뉴스심리는 일요일 지수에서 전주 일요일 지수를 뺀 값, '
        '주가는 그 주 마지막 거래일 종가의 전주 대비 수익률을 씁니다.</p>'
        f'<p>각 날짜의 피어슨 상관계수는 그 주까지의 최근 {CORRELATION_WEEKS}주를 같은 주끼리 '
        f'짝지어 계산했습니다. 아래 표의 한 행에서 세 지표의 주간 변화와 세 쌍의 상관계수를 함께 읽을 수 있습니다.</p>'
        f'<p><a href="{BOK_PAGE}">한국은행</a> · '
        '<a href="https://finance.yahoo.com/quote/%5EIXIC/history/">나스닥 종합 종가</a> · '
        '<a href="https://finance.yahoo.com/quote/%5EKS11/history/">코스피 종가</a>'
        f'{kospi_daily}</p></figcaption>\n'
        '</figure>\n'
        '<details open style="margin-top: 1rem"><summary>날짜별 주간 변화와 상관계수</summary>'
        '<div class="article-table-wrap" role="region" aria-label="날짜별 주간 변화와 상관계수" '
        'tabindex="0" style="overflow-x: auto">'
        f'<table class="article-data-table"><thead><tr>{table_head}</tr></thead>'
        f'<tbody>{"".join(table_rows)}</tbody></table></div></details>'
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
