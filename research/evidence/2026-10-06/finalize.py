import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
forecast_path = sorted((ROOT / "research/evaluation/forecasts").glob("2026-10-06-*-same-close.json"))[-1]
forecast = json.loads(forecast_path.read_text(encoding="utf-8"))
forecast["scenarios"] = {
    "bull": {"low": 7080, "high": 7220, "probability": 0.30},
    "base": {"low": 6950, "high": 7080, "probability": 0.50},
    "bear": {"low": 6780, "high": 6950, "probability": 0.20},
}
forecast["pathEnvelope"] = {"low": 6700, "high": 7260, "coverage": 0.9}
forecast["drivers"] = [
    {"id": "us-tech-strength", "rank": 1, "claim": "나스닥·Nvidia 강세와 원화 강세가 6,950선 하단을 지지한다.", "validationMetric": "QQQ·Nvidia·USD/KRW·삼성전자·SK하이닉스"},
    {"id": "selective-chip-signal", "rank": 2, "claim": "SOXX 제한 상승과 Micron 하락은 7,080선 위 추격을 제한한다.", "validationMetric": "SOXX·SMH·Micron·KOSPI"},
    {"id": "domestic-flow", "rank": 3, "claim": "7,080선 안착은 외국인과 프로그램 수급의 동행이 필요하다.", "validationMetric": "외국인·프로그램·KOSPI"},
]
forecast["scenarioTriggers"] = {
    "bull": {"logic": "AND", "observeBy": "2026-10-06T15:20:00+09:00", "conditions": [{"id": "bull-price", "metricId": "kospi_price", "operator": "gt", "threshold": 7080, "source": "Naver Finance KOSPI"}, {"id": "bull-foreign", "metricId": "foreign_cash", "operator": "gt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"}, {"id": "bull-program", "metricId": "program_total", "operator": "gt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"}]},
    "base": {"logic": "AND", "observeBy": "2026-10-06T15:20:00+09:00", "conditions": [{"id": "base-floor", "metricId": "kospi_price", "operator": "gte", "threshold": 6950, "source": "Naver Finance KOSPI"}, {"id": "base-cap", "metricId": "kospi_price", "operator": "lte", "threshold": 7080, "source": "Naver Finance KOSPI"}, {"id": "base-foreign", "metricId": "foreign_cash", "operator": "gte", "threshold": -10000, "source": "Naver Finance KOSPI 수급 (억원)"}]},
    "bear": {"logic": "AND", "observeBy": "2026-10-06T15:20:00+09:00", "conditions": [{"id": "bear-price", "metricId": "kospi_price", "operator": "lt", "threshold": 6950, "source": "Naver Finance KOSPI"}, {"id": "bear-foreign", "metricId": "foreign_cash", "operator": "lt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"}, {"id": "bear-program", "metricId": "program_total", "operator": "lt", "threshold": 0, "source": "Naver Finance KOSPI 수급 (억원)"}]},
}
trigger_descriptions = {
    "bull-price": "KOSPI가 7,080을 웃도는지 확인한다.",
    "bull-foreign": "외국인 현물이 순매수인지 확인한다.",
    "bull-program": "프로그램 매매가 순매수인지 확인한다.",
    "base-floor": "KOSPI가 6,950 이상인지 확인한다.",
    "base-cap": "KOSPI가 7,080 이하인지 확인한다.",
    "base-foreign": "외국인 현물 매도가 급격히 확대되지 않았는지 확인한다.",
    "bear-price": "KOSPI가 6,950 아래로 내려갔는지 확인한다.",
    "bear-foreign": "외국인 현물이 순매도인지 확인한다.",
    "bear-program": "프로그램 매매가 순매도인지 확인한다.",
}
for scenario in forecast["scenarioTriggers"].values():
    for condition in scenario["conditions"]:
        condition["description"] = trigger_descriptions[condition["id"]]
forecast["posture"] = {"attack": 30, "wait": 50, "defense": 20}
forecast["reportSha256"] = hashlib.sha256((ROOT / "reports/2026-10-06.md").read_bytes()).hexdigest()
sealed = dict(forecast)
sealed.pop("contentHash", None)
forecast["contentHash"] = hashlib.sha256(json.dumps(sealed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
forecast_path.write_text(json.dumps(forecast, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

snapshot_path = ROOT / "assets/data/market-dashboard-latest.json"
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
snapshot["stance"] = {"label": "원화 강세와 7,000선 수급", "attack": 30, "wait": 50, "defense": 20, "note": "원화 강세와 장전 메모리주 상승이 7,000선 위 수급으로 이어지는지 본다."}
snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
dated_snapshot = ROOT / "assets/data" / f"market-dashboard-{snapshot['snapshotId']}.json"
dated_snapshot.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

old_image = "market-2026-10-06-memory-yield-holiday-1200x630.png"
new_image = "market-2026-10-06-nasdaq-memory-won-1200x630.png"
for relative in ("index.html", "articles/index.html", "articles/market.html"):
    path = ROOT / relative
    path.write_text(path.read_text(encoding="utf-8").replace(old_image, new_image), encoding="utf-8", newline="\n")

issued = forecast["issuedAt"]
(ROOT / "STATE.md").write_text(f"""# KOSPI·KODEX 리서치 상태

- 작성 {issued}, 데이터 최종 확인 {forecast['dataCutoffAt']}, 한국 장전.
- 직전 KOSPI 7,003.74(+0.46%), KODEX 114,395원(+1.01%), 10월 2일 정규장.
- 핵심: 나스닥·Nvidia 강세와 원/달러 1,342.50원이 하단을 지지하지만 SOXX 제한 상승·Micron 하락으로 7,080선 위는 국내 수급 확인이 필요하다. 10월 2일 국내 상승은 중복 가산하지 않는다.
- 대응 30/50/20. 기본 6950~7080(50%), 강세7080초과~7220(30%), 약세6780~6950미만(20%), 경로6700~7260(90%). KODEX 111500/114395/117500.
- 보고서 reports/2026-10-06.md, 취재 research/notes/2026-10-06.md. 차트는 charts/us_yield_spreads_90d_2026-10-06.png 및 long_term.
- 대시보드 assets/data/market-dashboard-{snapshot['snapshotId']}.json 및 latest.json.
- 다음: 10월 14일 21:30 KST 미국 9월 CPI.
- 직전 정산 research/evaluation/outcomes/2026-10-02-0811-same-close.json, 누적 research/evaluation/generated/latest.md. 수급 앵커는 원문 미확보로 추정하지 않는다.
""", encoding="utf-8", newline="\n")
print(json.dumps({"forecastId": forecast["forecastId"], "contentHash": forecast["contentHash"]}, ensure_ascii=False))
