import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).parent
forecast_path = sorted((ROOT / "research/evaluation/forecasts").glob("2026-10-02-*-same-close.json"))[-1]
forecast = json.loads(forecast_path.read_text(encoding="utf-8"))
issued = forecast["issuedAt"]
cutoff = forecast["dataCutoffAt"]

forecast["scenarios"] = {
    "bull": {"low": 7000, "high": 7150, "probability": 0.35},
    "base": {"low": 6850, "high": 7000, "probability": 0.45},
    "bear": {"low": 6700, "high": 6850, "probability": 0.20},
}
forecast["pathEnvelope"] = {"low": 6600, "high": 7200, "coverage": 0.9}
forecast["drivers"] = [
    {"id": "us-chip-strength", "rank": 1, "claim": "미국 SOXX·Micron 강세가 KOSPI 6,850선 하단을 지지한다.", "validationMetric": "SOXX·Micron·삼성전자·SK하이닉스"},
    {"id": "yield-fx-ceiling", "rank": 2, "claim": "5%대 미국 10년물과 원/달러 상승이 7,000선 위 추격을 제한한다.", "validationMetric": "미국 10년물·USD/KRW·KOSPI"},
    {"id": "domestic-flow", "rank": 3, "claim": "7,000선 안착은 외국인과 프로그램 수급의 동행이 필요하다.", "validationMetric": "외국인·프로그램·KOSPI"},
]
forecast["scenarioTriggers"] = {
    "bull": {"logic": "AND", "observeBy": "2026-10-02T15:20:00+09:00", "conditions": [
        {"id": "bull-price", "metricId": "kospi_price", "operator": "gt", "threshold": 7000, "source": "Naver Finance KOSPI"},
        {"id": "bull-foreign", "metricId": "foreign_cash", "operator": "gt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"},
        {"id": "bull-program", "metricId": "program_total", "operator": "gt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"},
    ]},
    "base": {"logic": "AND", "observeBy": "2026-10-02T15:20:00+09:00", "conditions": [
        {"id": "base-floor", "metricId": "kospi_price", "operator": "gte", "threshold": 6850, "source": "Naver Finance KOSPI"},
        {"id": "base-cap", "metricId": "kospi_price", "operator": "lte", "threshold": 7000, "source": "Naver Finance KOSPI"},
        {"id": "base-foreign", "metricId": "foreign_cash", "operator": "gte", "threshold": -10000, "source": "Naver Finance KOSPI 수급 (억원)"},
    ]},
    "bear": {"logic": "AND", "observeBy": "2026-10-02T15:20:00+09:00", "conditions": [
        {"id": "bear-price", "metricId": "kospi_price", "operator": "lt", "threshold": 6850, "source": "Naver Finance KOSPI"},
        {"id": "bear-foreign", "metricId": "foreign_cash", "operator": "lt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"},
        {"id": "bear-program", "metricId": "program_total", "operator": "lt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"},
    ]},
}
forecast["posture"] = {"attack": 35, "wait": 45, "defense": 20}
forecast["reportSha256"] = hashlib.sha256((ROOT / "reports/2026-10-02.md").read_bytes()).hexdigest()
sealed = dict(forecast)
sealed.pop("contentHash", None)
forecast["contentHash"] = hashlib.sha256(json.dumps(sealed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
forecast_path.write_text(json.dumps(forecast, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

snapshot_path = ROOT / "assets/data/market-dashboard-20261002-0811.json"
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
snapshot["changes"] = [
    {"label": "KOSPI", "before": "6,838.04", "after": "6,971.35", "meaning": "10월 1일 반도체주 강세 속 1.95% 상승으로 마감했습니다."},
    {"label": "미국 10년물", "before": "5.26%", "after": "5.29%", "meaning": "장기금리 부담이 7,000선 위 추격을 제한합니다."},
]
for market in snapshot["markets"]:
    if market["id"] == "KOSPI":
        market.update(open=6814.49, high=6971.36, low=6765.06)
    if market["id"] == "KOSDAQ":
        market.update(value=None, changePercent=None, asOf="2026-10-01T15:30:00+09:00", asOfLabel="10월 1일 OHLC 미확인", stateLabel="정규장 종가", open=None, high=None, low=None, previousClose=None, flows=[])
snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
(ROOT / "assets/data/market-dashboard-latest.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

actual_path = ROOT / "research/evaluation/actuals/2026-10-01.json"
actual = json.loads(actual_path.read_text(encoding="utf-8"))
actual["kospi"].update(open=6814.49, high=6971.36, low=6765.06, source="https://marketin.edaily.co.kr/News/ReadE?newsId=04805206645608656")
actual_path.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

(ROOT / "STATE.md").write_text(f"""# KOSPI·KODEX 리서치 상태

- 작성 {issued}, 데이터 최종 확인 {cutoff}, 한국 장전.
- 직전 KOSPI 6,971.35(+1.95%, 시가 6,814.49·고가 6,971.36·저가 6,765.06), KODEX 113,255원(+3.46%), 10월 1일 정규장.
- 핵심: 미국 SOXX +1.35%·Micron +3.03%가 메모리주의 하단을 지지하지만, 미국 10년물 5.29%·원/달러 1,359.50원과 고용지표 대기가 7,000선 위를 제한한다. 10월 1일 국내 급등은 오늘 충격으로 중복 가산하지 않는다.
- 대응 35/45/20. 기본 6850~7000(45%), 강세7000초과~7150(35%), 약세6700~6850미만(20%), 경로6600~7200(90%). KODEX 110000/113255/116000.
- 보고서 reports/2026-10-02.md, 취재 research/notes/2026-10-02.md. 차트는 charts/us_yield_spreads_90d_2026-10-02.png 및 long_term.
- 대시보드 assets/data/market-dashboard-{issued[0:4]}{issued[5:7]}{issued[8:10]}-{issued[11:13]}{issued[14:16]}.json 및 latest.json.
- 다음: 10월 2일 21:30 KST 미국 9월 고용보고서, 추석 연휴 중 미국 반도체·금리 흐름.
- 직전 정산 research/evaluation/outcomes/2026-10-01-0816-same-close.json, 누적 research/evaluation/generated/latest.md. 수급 앵커는 원문 미확보로 추정하지 않는다.
""", encoding="utf-8", newline="\n")
print(json.dumps({"forecastId": forecast["forecastId"], "contentHash": forecast["contentHash"]}, ensure_ascii=False))
