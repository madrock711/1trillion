"""9월 21일 장전판을 검증된 전일 조립 계약으로 생성한다."""
from pathlib import Path
import json

HERE = Path(__file__).parent
SOURCE = (HERE.parent / '2026-09-18' / 'build.py').read_text(encoding='utf-8')

# 전일 조립기는 카드·대시보드·평가 계약의 공통 구조를 보존한다. 오늘의 원고와
# 원시 시세를 읽도록 날짜와 핵심 기준선을 바꾼 뒤 메모리에서만 실행한다.
REPLACEMENTS = {
    '2026-09-18': '2026-09-21',
    '미국 반도체 반등, KOSPI는 외국인 매도를 넘을까': '반도체 반등 뒤의 월요일, KOSPI 7,000선은 수급이 결정한다',
    '유가·금리 하락에 미국 반도체가 반등했습니다. 국내 외국인 수급이 상승의 지속성을 가릅니다.': '미국 반도체 반등과 장전 메모리주 강세가 이어졌습니다. KOSPI 7,000선은 국내 수급이 가릅니다.',
    'market-2026-09-18-chip-rebound-foreign-flow-1200x630.webp': 'market-2026-09-21-chip-rebound-yield-ceiling-1200x630.webp',
    '밝은 서울 아침의 메모리 칩과 웨이퍼, 건물 사이로 이동하는 금빛 자금의 흐름': '서울 아침의 메모리 칩과 웨이퍼, 금리 곡선 아래 이어지는 푸른 반등선',
    "'6,715.41'": "'6,894.23'",
    '6,715.41': '6,894.23',
    '6715.41': '6894.23',
    '6,717.97': '6,715.41',
    '103,490': '109,265',
    '103490': '109265',
    '102,825': '107,310',
    '106,520': '110,435',
    '6,650~6,850': '6,850~7,050',
    '6,850 초과~7,000': '7,050 초과~7,200',
    '6,450~6,650 미만': '6,650~6,850 미만',
    '[6650,6850,7000]': '[6850,7050,7200]',
    '[102825,103490,106520]': '[107310,109265,110435]',
    "low=6850,high=7000,probability=.3": "low=7050,high=7200,probability=.3",
    "low=6650,high=6850,probability=.5": "low=6850,high=7050,probability=.5",
    "low=6450,high=6650,probability=.2": "low=6650,high=6850,probability=.2",
    "'attack':25,'wait':50,'defense':25": "'attack':30,'wait':50,'defense':20",
    "'attack':25,'wait':50,'defense':25": "'attack':30,'wait':50,'defense':20",
    '대응 25/50/25': '대응 30/50/20',
    '기본 6650~6850(50%), 강세 6850초과~7000(30%), 약세 6450~6650미만(20%), 경로 6350~7050(90%). KODEX 102825/103490/106520.': '기본 6850~7050(50%), 강세 7050초과~7200(30%), 약세 6650~6850미만(20%), 경로 6550~7250(90%). KODEX 107310/109265/110435.',
    '직전 KOSPI 6,894.23(-0.04%), KODEX 109,265원(-0.09%), 9월 17일 정규장.': '직전 KOSPI 6,894.23(+2.66%), KODEX 109,265원(+5.58%), 9월 18일 정규장.',
    '유가·미 국채금리 하락에 미국 반도체가 반등했으나 전날 국내 외국인 약 2.46조원 순매도가 지속됐다. 미국 ETF의 전날 한국장 후행분을 중복 가산하지 않는다.': '미국 반도체 반등과 장전 메모리주 강세가 이어졌지만, 10년물 5% 부근과 유가 변동이 상단을 제한한다. 끝난 한국장의 상승은 중복 가산하지 않는다.',
    '다음: 9/18 09:00 한국장 개장, 23:00 미국 주별 고용 지표.': '다음: 9/21 09:00 한국장 개장, 중국 LPR과 시카고 연은 8월 국가활동지수.',
    "'low':6850,'high':7000,'probability':.3": "'low':7050,'high':7200,'probability':.3",
    "'low':6650,'high':6850,'probability':.5": "'low':6850,'high':7050,'probability':.5",
    "'low':6450,'high':6650,'probability':.2": "'low':6650,'high':6850,'probability':.2",
    "'low':6350,'high':7050": "'low':6550,'high':7250",
    "'bull-price':6850,'base-support':6650,'base-cap':6850,'bear-price':6650": "'bull-price':7050,'base-support':6850,'base-cap':7050,'bear-price':6850",
    "'previousSessionDate':'2026-09-17'": "'previousSessionDate':'2026-09-18'",
    "'asOf':'2026-09-17T15:30:00+09:00'": "'asOf':'2026-09-18T15:30:00+09:00'",
}

for before, after in REPLACEMENTS.items():
    SOURCE = SOURCE.replace(before, after)

SOURCE = SOURCE.replace("E.parent/'2026-09-20'", "E.parent/'2026-09-18'")
namespace = {'__name__': 'market_build', '__file__': str(HERE / 'template-2026-09-18.py')}
exec(compile(SOURCE, str(HERE / 'template-2026-09-18.py'), 'exec'), namespace)


def number(value):
    return float(str(value).replace(',', ''))


def repair_kospi_snapshot(path):
    """Use the collected 9/18 bar as one atomic OHLC observation.

    The inherited template has editorial text substitutions, but a market bar
    must never be assembled field-by-field from different sessions.
    """
    raw = json.loads((HERE / 'KOSPI.json').read_text(encoding='utf-8'))['data']
    bar = next(row for row in raw if row['localTradedAt'] == '2026-09-18')
    close = number(bar['closePrice'])
    previous_close = close - number(bar['compareToPreviousClosePrice'])
    points = [
        ('시가', number(bar['openPrice'])),
        ('고가', number(bar['highPrice'])),
        ('저가', number(bar['lowPrice'])),
        ('종가', close),
    ]
    data = json.loads(path.read_text(encoding='utf-8'))
    market = next(item for item in data['markets'] if item['id'] == 'KOSPI')
    market.update(
        value=close,
        changePercent=number(bar['fluctuationsRatio']),
        open=number(bar['openPrice']),
        high=number(bar['highPrice']),
        low=number(bar['lowPrice']),
        previousClose=previous_close,
        asOf='2026-09-18T15:30:00+09:00',
        asOfLabel='9월 18일 종가',
        stateLabel='정규장 종가',
    )
    instrument = next(item for item in data['technical']['instruments'] if item['id'] == 'KOSPI')
    instrument.update(
        asOf='2026-09-18T15:30:00+09:00',
        asOfLabel='9월 18일 정규장 종가',
        points=[{'label': label, 'value': value} for label, value in points],
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    arguments = __import__('sys').argv
    if '--repair-dashboard' not in arguments:
        namespace['main'](seal='--seal' in arguments)
    repair_kospi_snapshot(Path('assets/data/market-dashboard-latest.json'))
    repair_kospi_snapshot(Path('assets/data/market-dashboard-20260921-0814.json'))
