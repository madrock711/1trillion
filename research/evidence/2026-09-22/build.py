"""9월 21일 장전판을 검증된 전일 조립 계약으로 생성한다."""
from pathlib import Path
import json

HERE = Path(__file__).parent
SOURCE = (HERE.parent / '2026-09-18' / 'build.py').read_text(encoding='utf-8')

# 전일 조립기는 카드·대시보드·평가 계약의 공통 구조를 보존한다. 오늘의 원고와
# 원시 시세를 읽도록 날짜와 핵심 기준선을 바꾼 뒤 메모리에서만 실행한다.
REPLACEMENTS = {
    '2026-09-18': '2026-09-22',
    '미국 반도체 반등, KOSPI는 외국인 매도를 넘을까': 'AI 반도체 급등과 원화 강세, KOSPI 7,000선은 지킬까',
    '유가·금리 하락에 미국 반도체가 반등했습니다. 국내 외국인 수급이 상승의 지속성을 가릅니다.': 'AI 반도체의 급등과 원화 강세가 장전 기대를 높였습니다. 7,000선 위 수급의 지속성이 관건입니다.',
    'market-2026-09-18-chip-rebound-foreign-flow-1200x630.webp': 'market-2026-09-22-ai-rally-won-relief-1200x630.webp',
    '밝은 서울 아침의 메모리 칩과 웨이퍼, 건물 사이로 이동하는 금빛 자금의 흐름': '서울의 아침 빛 속 웨이퍼와 메모리 모듈, 푸른 반등과 흰 원화 흐름',
    "'6,715.41'": "'7,007.72'",
    '6,715.41': '7,007.72',
    '6715.41': '7007.72',
    '6,717.97': '6,715.41',
    '103,490': '114,060',
    '103490': '114060',
    '102,825': '110,635',
    '106,520': '114,925',
    '6,650~6,850': '7,000~7,200',
    '6,850 초과~7,000': '7,200 초과~7,350',
    '6,450~6,650 미만': '6,800~7,000 미만',
    '[6650,6850,7000]': '[7000,7200,7350]',
    '[102825,103490,106520]': '[110635,114060,114925]',
    "low=6850,high=7000,probability=.3": "low=7200,high=7350,probability=.3",
    "low=6650,high=6850,probability=.5": "low=7000,high=7200,probability=.5",
    "low=6450,high=6650,probability=.2": "low=6800,high=7000,probability=.2",
    "'attack':25,'wait':50,'defense':25": "'attack':35,'wait':50,'defense':15",
    "'attack':25,'wait':50,'defense':25": "'attack':30,'wait':50,'defense':20",
    '대응 25/50/25': '대응 35/50/15',
    '기본 6650~6850(50%), 강세 6850초과~7000(30%), 약세 6450~6650미만(20%), 경로 6350~7050(90%). KODEX 102825/103490/106520.': '기본 6850~7050(50%), 강세 7050초과~7200(30%), 약세 6650~6850미만(20%), 경로 6550~7250(90%). KODEX 107310/109265/110435.',
    '직전 KOSPI 6,894.23(-0.04%), KODEX 109,265원(-0.09%), 9월 17일 정규장.': '직전 KOSPI 6,894.23(+2.66%), KODEX 109,265원(+5.58%), 9월 18일 정규장.',
    '유가·미 국채금리 하락에 미국 반도체가 반등했으나 전날 국내 외국인 약 2.46조원 순매도가 지속됐다. 미국 ETF의 전날 한국장 후행분을 중복 가산하지 않는다.': '미국 반도체 반등과 장전 메모리주 강세가 이어졌지만, 10년물 5% 부근과 유가 변동이 상단을 제한한다. 끝난 한국장의 상승은 중복 가산하지 않는다.',
    '다음: 9/18 09:00 한국장 개장, 23:00 미국 주별 고용 지표.': '다음: 9/21 09:00 한국장 개장, 중국 LPR과 시카고 연은 8월 국가활동지수.',
    "'low':6850,'high':7000,'probability':.3": "'low':7050,'high':7200,'probability':.3",
    "'low':6650,'high':6850,'probability':.5": "'low':6850,'high':7050,'probability':.5",
    "'low':6450,'high':6650,'probability':.2": "'low':6650,'high':6850,'probability':.2",
    "'low':6350,'high':7050": "'low':6550,'high':7250",
    "'bull-price':6850,'base-support':6650,'base-cap':6850,'bear-price':6650": "'bull-price':7050,'base-support':6850,'base-cap':7050,'bear-price':6850",
    "'previousSessionDate':'2026-09-17'": "'previousSessionDate':'2026-09-21'",
    "'asOf':'2026-09-17T15:30:00+09:00'": "'asOf':'2026-09-21T15:30:00+09:00'",
}

for before, after in REPLACEMENTS.items():
    SOURCE = SOURCE.replace(before, after)

SOURCE = SOURCE.replace("E.parent/'2026-09-20'", "E.parent/'2026-09-18'")
namespace = {'__name__': 'market_build', '__file__': str(HERE / 'template-2026-09-18.py')}
exec(compile(SOURCE, str(HERE / 'template-2026-09-18.py'), 'exec'), namespace)


def number(value):
    return float(str(value).replace(',', ''))


def bar_points(bar):
    return [
        ('시가', number(bar['openPrice'])),
        ('고가', number(bar['highPrice'])),
        ('저가', number(bar['lowPrice'])),
        ('종가', number(bar['closePrice'])),
    ]


def repair_dashboard_snapshot(path):
    """Keep every published OHLC field and level tied to its source session."""
    kospi_bar = next(row for row in json.loads((HERE / 'KOSPI.json').read_text(encoding='utf-8'))['data'] if row['localTradedAt'] == '2026-09-21')
    kodex_bar = next(row for row in json.loads((HERE / '122630.json').read_text(encoding='utf-8'))['data'] if row['localTradedAt'] == '2026-09-21')
    close = number(kospi_bar['closePrice'])
    previous_close = round(close - number(kospi_bar['compareToPreviousClosePrice']), 2)
    data = json.loads(path.read_text(encoding='utf-8'))
    market = next(item for item in data['markets'] if item['id'] == 'KOSPI')
    market.update(
        value=close,
        changePercent=number(kospi_bar['fluctuationsRatio']),
        open=number(kospi_bar['openPrice']),
        high=number(kospi_bar['highPrice']),
        low=number(kospi_bar['lowPrice']),
        previousClose=previous_close,
        asOf='2026-09-21T15:30:00+09:00',
        asOfLabel='9월 21일 종가',
        stateLabel='정규장 종가',
    )
    instrument = next(item for item in data['technical']['instruments'] if item['id'] == 'KOSPI')
    instrument.update(
        asOf='2026-09-21T15:30:00+09:00',
        asOfLabel='9월 21일 정규장 종가',
        points=[{'label': label, 'value': value} for label, value in bar_points(kospi_bar)],
    )
    kodex = next(item for item in data['technical']['instruments'] if item['id'] == 'KODEX')
    kodex.update(
        asOf='2026-09-21T15:30:00+09:00',
        asOfLabel='9월 21일 정규장 종가',
        points=[{'label': label, 'value': value} for label, value in bar_points(kodex_bar)],
        levels=[
            {'label': '1차 지지', 'value': 110635},
            {'label': '반등 기준', 'value': 114060},
            {'label': '저항', 'value': 114925},
        ],
        interpretation='1차 지지 110,635 · 반등 기준 114,060 · 저항 114,925',
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    arguments = __import__('sys').argv
    if '--repair-dashboard' not in arguments:
        namespace['main'](seal='--seal' in arguments)
    repair_dashboard_snapshot(Path('assets/data/market-dashboard-latest.json'))
    repair_dashboard_snapshot(Path('assets/data/market-dashboard-20260922-0808.json'))
