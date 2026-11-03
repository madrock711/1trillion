"""사용자가 승인한 전일 평가 누락 필드만 보완한다. 기존 판단은 고정한다."""
import hashlib
import importlib.util
import json
from pathlib import Path

R = Path(__file__).resolve().parents[3]
P = Path(__file__).parent
target = R / 'research/evaluation/outcomes/2026-11-02-0917-same-close.json'
backup = P / 'outcome-2026-11-02-before-path-metadata.json'
original = target.read_bytes()
assert not backup.exists(), '원본 증거를 덮어쓰지 않는다'
backup.write_bytes(original)
outcome = json.loads(original)
source = json.loads((P / 'KOSPI.json').read_text(encoding='utf-8'))
assert source['data'][0]['localTradedAt'] == '2026-11-02'
outcome.update(
    postForecastPathStatus='missing',
    postForecastPathMissingReason='보존된 원천은 일별 OHLC로 발행 이후 분봉 경로를 입증하지 못함. 전일 전체 고저를 발행후 경로로 대체하지 않음.',
    postForecastPathMissingEvidence={
        'sourceStatus': 'incomplete',
        'source': source['url'],
        'asOf': '2026-11-02T15:30:00+09:00',
        'fetchedAt': source['fetchedAt'],
        'rawHash': source['rawHash'],
    },
)
before = json.loads(original)
assert {k: v for k, v in outcome.items() if k in before} == before
spec = importlib.util.spec_from_file_location('evaluation', R / 'scripts/evaluate_market_research.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fp = R / 'research/evaluation/forecasts/2026-11-02-0917-same-close.json'
ap = R / 'research/evaluation/actuals/2026-11-02.json'
forecast = module.validate_forecast(json.loads(fp.read_text(encoding='utf-8')), fp, None)
actual = module.validate_actual(json.loads(ap.read_text(encoding='utf-8')), ap)
module.validate_outcome(outcome, target, forecast, actual)
target.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print('원본 SHA256:', hashlib.sha256(original).hexdigest())
print('기존 필드 불변, 추가 필드 3개, outcome 계약 검증 통과')
