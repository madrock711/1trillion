# KOSPI 리서치 누적 평가 규칙

## 목적

이 문서는 공개 시황과 분리된 내부 평가 계약이다. 매일의 전망을 장 마감 뒤 실제 흐름과 같은 기준으로 대조하고, 반복해서 확인된 판단만 다음 리서치의 규칙으로 승격한다. 하루의 적중이나 실패를 근거로 새 법칙을 만들지 않는다.

## 기존 리서치 비판적 감사

2026년 7월 29일부터 8월 7일까지 저장된 보고서를 날짜별 마지막 판본 기준으로 대조했다. 기본 시나리오의 종가 범위에 들어간 날은 8개 중 3개, 강세·기본·약세 중 어느 범위에든 들어간 날은 8개 중 6개였다. 그러나 이 수치는 성과로 해석하지 않는다.

- 개장 전 전망, 개장 직후 전망, 10시대 수정판, 14시 30분 전망이 같은 표본에 섞여 있다.
- 같은 날짜의 수정판이 독립된 예측처럼 남아 있다.
- 강세·기본·약세 범위가 겹치거나 세 범위가 지나치게 넓어 어느 쪽이든 적중하기 쉬운 날이 있다.
- 종가가 범위에 들어왔어도 장중에는 반대 시나리오를 통과한 날이 있다.
- 7월 31일처럼 방향은 맞았지만 상단을 크게 벗어난 날과 7월 29일처럼 수정판도 하단 꼬리를 놓친 날이 있다.
- 8월 7일에는 개장 초 외국인·프로그램 매수가 장 마감까지 유지되지 않았는데 초기 절대값을 지속적인 수급으로 읽었다.
- KOSPI 확정 OHLC와 최종 수급이 날짜별 정본으로 보존되지 않아 일부 과거 결과는 다음 보고서의 반올림 문장으로만 남았다.

따라서 과거의 `3/8`, `6/8`은 오류 분류를 위한 참고값일 뿐 적중률·예측력·투자 우위가 아니다. 과거 판정은 `research/evaluation/legacy-audit.jsonl`에 별도로 보존하고 새 누적 성과에 합치지 않는다.

## 반복된 실패 유형

1. **수급 지속성 오판**: 개장 직후 외국인·프로그램 절대값을 종가까지 이어질 흐름으로 간주했다.
2. **장중 경로 누락**: 종가 범위만 평가해 장중 최대 불리 움직임과 급반전을 숨겼다.
3. **외부 신호 과대평가**: 미국 반도체 상승을 국내 기관 리밸런싱과 가격 반응보다 앞세운 날이 있었다.
4. **범위 설계 문제**: 범위 중첩, 지나치게 넓은 전체 포락, 수치 하단·상단의 반복적인 꼬리 실패가 있었다.
5. **판본·시간축 혼합**: 같은 날 수정판과 서로 다른 남은 시간을 한 적중률로 셌다.
6. **사후 원인 교체 가능성**: 핵심 원인 순위와 관측값을 발행 전에 고정하지 않아 회고 때 다른 설명을 선택할 수 있었다.

## 내부 원장 구조

```text
research/evaluation/
├─ forecasts/            # 장 마감 전에 봉인한 전망 계약
├─ actuals/              # 거래일별 공통 확정값
├─ outcomes/             # 전망별 판정과 오류 코드
├─ publications/         # 실제 push·배포 확인 시각
├─ trading-sessions.json # KRX 거래일 순서 정본
├─ hypotheses.jsonl      # 누적 가설과 승격 상태
├─ legacy-audit.jsonl    # 과거 보고서의 비정규 감사
└─ generated/            # 평가기가 만든 최신 요약
```

전망과 실제값, 판정을 한 파일에 섞지 않는다. 전망 파일은 사후 수정하지 않으며, 정정판은 새 `forecastId`를 발급하고 `supersedes`로 연결한다.

## 전망 계약

목표 거래일의 종가 범위를 제시하는 공개·내부 리서치 판본은 같은 시각에 `research/evaluation/forecasts/<forecastId>.json`을 만든다.

```json
{
  "schemaVersion": 1,
  "forecastId": "2026-08-07-0911-same-close",
  "visibility": "public",
  "reportPath": "reports/2026-08-07-0911.md",
  "reportSha256": "64자리 SHA-256",
  "contentHash": "contentHash 자신을 제외한 전망 계약 정렬 JSON의 64자리 SHA-256",
  "issuedAt": "2026-08-07T09:12:00+09:00",
  "dataCutoffAt": "2026-08-07T09:11:00+09:00",
  "marketState": "intraday",
  "marketRegime": "risk_off",
  "evaluationBucket": "open_0900_0930",
  "target": {
    "sessionDate": "2026-08-07",
    "horizon": "session_close",
    "instrument": "KOSPI",
    "leadSessions": 0,
    "previousSessionDate": "2026-08-06"
  },
  "reference": {
    "price": 6385.43,
    "asOf": "2026-08-07T09:11:00+09:00",
    "kind": "live"
  },
  "scenarios": {
    "bull": {"low": 6400, "high": 6500, "probability": 0.25},
    "base": {"low": 6300, "high": 6400, "probability": 0.55},
    "bear": {"low": 6220, "high": 6300, "probability": 0.20}
  },
  "closeEnvelopeCoverage": 0.90,
  "pathEnvelope": {"low": 6180, "high": 6550, "coverage": 0.90},
  "drivers": [
    {"id": "domestic-flow", "rank": 1, "claim": "외국인 현물 매수가 유지된다.", "validationMetric": "30분·60분·종가 누적값"},
    {"id": "semiconductor-price", "rank": 2, "claim": "반도체 대형주가 지수 하단을 지지한다.", "validationMetric": "삼성전자·SK하이닉스 종가 위치"}
  ],
  "scenarioTriggers": {
    "bull": {"logic": "AND", "observeBy": "2026-08-07T15:20:00+09:00", "conditions": [{"id": "bull-flow", "description": "외국인 현물 매수 유지", "metricId": "foreign_cash", "operator": "gt", "threshold": 0, "source": "Naver Finance KRX"}]},
    "base": {"logic": "AND", "observeBy": "2026-08-07T15:20:00+09:00", "conditions": [{"id": "base-support", "description": "기준선 종가 방어", "metricId": "kospi_price", "operator": "gte", "threshold": 6300, "source": "Naver Finance KRX"}]},
    "bear": {"logic": "OR", "observeBy": "2026-08-07T15:20:00+09:00", "conditions": [{"id": "bear-reversal", "description": "외국인 현물 매도 반전", "metricId": "foreign_cash", "operator": "lt", "threshold": 0, "source": "Naver Finance KRX"}]}
  },
  "hypothesisTrials": [
    {"hypothesisId": "domestic-flow-persistence", "regime": "risk_off", "candidatePrediction": 6260, "baselineId": "reference_carry", "predictorVersion": "domestic-flow-persistence-v1", "inputStatus": "available", "predictorInputs": {"asOf": "2026-08-07T10:00:00+09:00", "anchors": {"open30": {"asOf": "2026-08-07T09:30:00+09:00", "foreignCash": -820, "programNonArbitrage": -510, "programTotal": -545, "source": "Naver Finance KRX", "rawHash": "64자리 SHA-256"}, "open60": {"asOf": "2026-08-07T10:00:00+09:00", "foreignCash": -1050, "programNonArbitrage": -700, "programTotal": -760, "source": "Naver Finance KRX", "rawHash": "64자리 SHA-256"}}, "canonicalHash": "canonicalHash 자신을 제외한 정렬 JSON의 SHA-256"}}
  ],
  "posture": {"attack": 30, "wait": 50, "defense": 20},
  "supersedes": null
}
```

- `evaluationBucket`은 `preopen`, `open_0900_0930`, `morning_0931_1130`, `afternoon_1131_1500`, `closing_1501_1529`, `postclose` 중 하나다.
- `visibility`는 `public` 또는 `internal`이다. 공개 전망은 5분 이내 `pushed`와 `issuedAt`부터 10분 이내 `deploy_verified` 이벤트가 모두 있어야 정산할 수 있고, 내부 전망에는 publication 이벤트를 만들지 않는다. 두 이벤트는 발행과 같은 평가 구간·목표일 종가 전에 있어야 한다.
- `target.leadSessions`는 당일판 0, 바로 다음 거래일판 1만 허용한다. `previousSessionDate`는 `trading-sessions.json`에서 목표일 바로 앞 거래일과 일치해야 한다. 며칠 뒤 목표를 다음 거래일판으로 가장할 수 없다.
- 장중 `reference`는 `kind: live`이며 `dataCutoffAt`보다 5분 이상 낡을 수 없다. 개장 전·전일 장마감판은 `kind: previous_close`와 직전 거래일 15시 30분 이후 확정값을 사용한다.
- `scenarios.*.probability` 합계는 1이다. 이것은 전망 확률이다.
- `posture` 합계는 100이다. 이것은 사용자의 대응 성격이며 전망 확률이 아니다.
- 세 종가 범위는 서로 겹치지 않는다. 경계값을 공유할 수 있지만 같은 종가가 두 시나리오에 동시에 포함되지는 않게 판정 규칙을 고정한다.
- 종가 전체 포락과 `pathEnvelope`의 신뢰수준은 모두 90%로 고정한다. 판본마다 신뢰수준을 바꿔 구간 점수를 유리하게 만들 수 없다.
- `pathEnvelope`는 종가 범위가 아니라 발행 뒤 남은 장중 고가·저가의 예상 포락이다. 종가 적중과 장중 위험을 따로 평가한다.
- `reportSha256`으로 원고를, `contentHash`로 전망 계약 전체를 봉인한다. `contentHash`는 그 필드 자신만 제외한 정렬 JSON으로 다시 계산한다.
- 같은 거래일·목표·평가 구간의 수정판은 `supersedes`로 한 줄의 계보를 만든다. 공개판이 하나라도 있으면 실제 `pushed`가 가장 빨랐던 최초 공개판을 누적 대표로 고정해 뒤의 정정판이 최초 실패를 지우지 못하게 한다. 공개판이 없는 내부 실험만 마지막 leaf 판본을 대표로 선택한다.
- 발행이 늦어져 평가 구간 자체가 바뀌면 이전 판본을 `supersedes`하지 않고 새 평가 구간의 독립 판본으로 남긴다.
- 평가 구간은 데이터 시각이 아니라 실제 `issuedAt`으로 정한다. `dataCutoffAt → issuedAt`은 개장 전·장중 20분, 전일 장마감 뒤 다음 거래일 전망은 30분을 넘길 수 없다. 공개판은 같은 평가 구간 안에서 5분 이내 push해야 한다.
- 발행 전 핵심 원인 순위와 시나리오별 조건을 고정된 `metricId`, 비교 연산자, 임계값, 단위, 출처, 관측 마감 시각으로 봉인한다. 평가기는 조건별 참·거짓을 다시 계산한 뒤 시나리오의 `AND`·`OR`까지 합성한다. 실제가 아닌 시나리오가 성립하면 `trigger_false_positive`, 실제 시나리오가 불성립하면 `trigger_missed`를 자동 부여한다.
- 가설을 시험할 때는 후보 규칙의 종가 예측값, `reference_carry` 기준, `predictorVersion`을 `hypothesisTrials`에 미리 봉인한다. 수급 가설은 정의가 요구한 앵커의 세 지표·시각·출처·원문 해시를 `predictorInputs`에 넣고, `canonicalHash` 자신을 제외한 정렬 JSON의 SHA-256으로 다시 봉인한다. 입력의 최신 `asOf`는 포함 앵커의 마지막 시각과 같고 `dataCutoffAt`을 넘을 수 없다. 입력을 확보하지 못해도 trial을 빼지 않고 `inputStatus: missing`과 원천 상태·시각·해시를 남긴다. 전망의 `marketRegime`은 `risk_on`, `risk_off`, `mixed`, `event_shock` 중 하나만 사용한다. 가설 정의의 평가 구간·허용 국면에 해당하는 모든 선택 대표는 같은 predictor 판본을 반드시 시험하므로 좋은 날만 표본에 넣을 수 없다.

`trading-sessions.json`에는 오름차순 KRX 거래일, 원천 기준 시각, 출처와 원문 해시를 둔다.

```json
{
  "schemaVersion": 1,
  "asOf": "2026-08-10T07:30:00+09:00",
  "source": "KRX 거래일 원천",
  "rawHash": "64자리 SHA-256",
  "sessions": ["2026-08-06", "2026-08-07", "2026-08-10"]
}
```

평가기는 목표일과 바로 앞 거래일을 이 순서로 다시 확인한다. 목표 거래일이 없는 주간 회고는 전망 계약 대상이 아니며, 특정 거래일을 목표로 삼은 판본은 주간 글 안에 있어도 같은 검증을 받는다.

## 거래일 확정값

정규장 종료 뒤 `research/evaluation/actuals/YYYY-MM-DD.json`을 한 번만 만든다. `bizdate`, `fetchedAt`, `marketStatus: CLOSE`를 필수로 두고 다음 보고서의 회고 문장이나 장중 대시보드 스냅샷을 정답으로 쓰지 않는다.

필수값은 KOSPI 최종 OHLC, `marketStatus: CLOSE`, 거래일, 원천 기준 시각, 수집 시각, 출처와 원문 해시다. KODEX 최종 OHLCV, 외국인·기관·개인 현물, 프로그램 차익·비차익·전체, 상승·보합·하락 종목 수는 `closeSnapshot`의 `kodex`, `cashFlow`, `program`, `breadth`에 나눠 보존한다. 네 묶음은 각각 15시 30분 이후 원천 시각, 출처, 원문 해시와 단위를 가져야 한다. 최종 수급 스냅샷을 확인하지 못하면 일부 값에 0을 채우지 않고 전체를 `null`로 둔 뒤 `closeSnapshotMissingReason`을 기록한다.

`flowTrajectory`는 `flow_trajectory_v1` 계약으로 09시 30분 `open30`, 10시 `open60`, 14시 `at1400`, 15시 30분 `close` 네 앵커를 모두 가진다. 각 앵커의 단위는 억원이며 `foreignCash`, `programNonArbitrage`, `programTotal`, 정확한 `asOf`, 출처와 원문 해시를 저장한다. 특정 앵커가 없으면 값을 0으로 채우지 않고 `status: missing`, 예정 시각, 확인 시각, 원천 상태·출처·누락 사유·원문 해시를 남긴다. `closeSnapshot`이 있으면 `close` 앵커도 반드시 있어야 하며 세 값이 정확히 일치해야 한다. 반대로 `closeSnapshot`이 없으면 임의의 종가 수급으로 커버리지를 채우지 못하도록 `close` 앵커도 누락 증거로만 기록한다. 궤적 전체를 확보하지 못한 날은 `flowTrajectory: null`과 종가 기준 누락 증거를 남기되, `closeSnapshot`이 존재하는데 궤적 전체를 누락 처리할 수는 없다.

평가기는 앵커의 모든 선행→후행 조합에 대해 `<metric>.delta.<from>.<to>`와 `<metric>.persistence.<from>.<to>`를 계산한다. 지속성은 `strengthening`, `weakening`, `reversal`, `flat`, `unavailable`로 고정하며 사후 결과 파일에서 임의로 작성하지 않는다.

## 결과 판정

`research/evaluation/outcomes/<forecastId>.json`은 공통 실제값을 `actualRef`로 참조한다. 다음을 기록한다.

- 기본 종가 범위·전체 포락 적중 여부와 이탈 거리
- 발행 기준값 대비 종가 방향
- 장중판은 `postForecastPathStatus`를 `available` 또는 `missing`으로 반드시 기록한다. `available`이면 발행 이후 첫 봉부터 15시 30분까지 집계한 `postForecastPath`의 고가·저가와 최대 유리·불리 움직임, 봉 간격, 수집 시각, 출처와 원문 해시를 함께 기록하고 종가 포함 여부를 검증한다. `missing`이면 경로를 넣지 않고 `postForecastPathMissingReason`과 `postForecastPathMissingEvidence`를 남긴다. 누락 증거는 `sourceStatus`, `source`, 확정 종가 시각과 같은 `asOf`, 그 이후 결과 기록 전의 `fetchedAt`, 원문 해시를 가져야 한다. 누락 표본은 없애지 않고 경로 적중의 최선값과 `누락=실패` 하한을 함께 계산한다. 장중 경로 자료 충족률이 90% 미만이면 하한 적중률·구간점수·최대 유리·불리 움직임을 활성 인사이트로 쓰지 않는다. 개장 전·전일 장마감판은 거래일 전체가 발행 뒤이므로 확정 일봉 고가·저가를 사용한다.
- 개장 후 30분, 60분, 14시, 종가의 외국인·프로그램 수급은 공통 실제값의 `flowTrajectory`와 파생 feature를 사용한다. 평가기는 전망에 봉인한 입력의 시각·세 지표·출처·원문 해시를 같은 실제 앵커와 대조해 `verified`, `missing_actual`, `input_mismatch`, `missing_input`으로 판정한다. 필수 결과 feature가 없으면 `missing_outcome_feature`로 남긴다.
- 사전에 봉인한 조건의 관측 시각·값·출처 또는 관측 불가 사유. `observed`·`not_observed`는 평가기가 연산자와 임계값으로 다시 계산한다.
- 핵심 원인별 `확인`, `부분 확인`, `기각`, `판정 불가`
- 고정 오류 코드. 트리거 오탐·미탐은 수동 판정하지 않고 봉인된 시나리오 논리에서 평가기가 만든다.
- 검증 중인 가설은 결과 파일에 `hypothesisId`와 `result`만 기록한다. 후보·기준 예측값과 시장 국면은 전망 계약에 미리 봉인한 `hypothesisTrials`를 사용하며, 지지·기각과 기준 대비 개선 bp는 평가기가 실제 종가로 다시 계산한다.

핵심 원인 판정은 회고 감사용이며 그 상태값만으로 가설을 승격하지 않는다. 다음 리서치의 활성 규칙은 사전에 봉인한 후보 예측과 고정 기준선의 수치 오차 비교만으로 결정한다.

발행·배포 시각은 전망 원본에 사후 기입하지 않는다. 공개된 판본만 `research/evaluation/publications/`에 `pushed`와 `deploy_verified` 이벤트를 별도 JSON으로 한 번씩 추가한다. 두 이벤트는 전망과 같은 `contentHash` 및 서로 동일한 40자리 `commitSha`를 가지며, `deploy_verified`에는 `availabilityStatus: available`과 독자가 실제로 연 URL인 `publicUrl`을 추가한다. 평가기는 Git 저장소에서 해당 commit의 전망 JSON을 다시 읽어 같은 `contentHash`인지 확인하고, 같은 commit의 `reportPath` 원문 SHA-256도 봉인된 `reportSha256`과 대조한다. 기존 이벤트 파일을 수정하지 않는다.

```json
{"schemaVersion":1,"forecastId":"2026-08-07-0911-same-close","eventType":"pushed","occurredAt":"2026-08-07T09:14:00+09:00","contentHash":"전망 계약과 같은 SHA-256","commitSha":"40자리 Git SHA"}
```

```json
{"schemaVersion":1,"forecastId":"2026-08-07-0911-same-close","eventType":"deploy_verified","occurredAt":"2026-08-07T09:16:00+09:00","contentHash":"전망 계약과 같은 SHA-256","commitSha":"pushed와 같은 Git SHA","availabilityStatus":"available","publicUrl":"https://www.hpmplab.com/articles/market-2026-08-07.html"}
```

고정 오류 코드는 다음을 사용한다.

```text
range_too_narrow_up
range_too_narrow_down
direction_wrong
trigger_false_positive
trigger_missed
domestic_flow_underweighted
external_signal_overweighted
late_session_reversal_missed
data_stale
nonindependent_revision
cause_unverifiable
```

## 평가 지표

`scripts/evaluate_market_research.py`는 같은 평가 구간의 대표판만 집계한다.

- 기본 범위 적중률과 전체 포락 적중률
- 기본 범위와 전체 종가 포락의 너비·이탈을 명목 확률로 함께 벌점 처리한 구간 점수
- 방향 적중률
- 다중 시나리오 Brier 점수
- 발행 기준값 그대로를 종가로 보는 단순 기준 대비 중심값 오차 개선
- 발행 이후 실제 고가·저가에 대한 최대 유리·불리 움직임과 경로 포락 구간 점수. 누락 경로는 모두 적중했다고 놓은 최선값과 모두 실패했다고 놓은 하한을 함께 보여주고, 활성 판단에는 자료 충족률 90%를 넘긴 하한만 사용한다.
- `dataCutoffAt → issuedAt`, `issuedAt → pushAt`, 이후에는 `pushAt → deployVerifiedAt` 시차
- 평가 구간별 성과와 반복 오류 코드. 전체 점수는 하루에 여러 평가 구간이 있어도 거래일마다 같은 가중치를 주며, 전체·평가 구간별 오류 코드 횟수도 같은 거래일의 중복을 한 번만 센다. `latest.md`의 시간대별 표에는 해당 구간의 반복 오류를 함께 표시한다.

평가기에는 우선 `발행 시점 현재가 유지` 기준을 내장한다. 다음 기준은 필요한 입력을 발행 전에 함께 봉인한 표본에서만 추가 비교하며, 비교하지 못한 판단은 인사이트로 승격하지 않는다.

1. 발행 시점 현재가 유지
2. 전일 종가 유지
3. 최근 20거래일 변동폭 기반 기계적 밴드
4. 미국 반도체 종가 방향만 반영한 단순 방향

## 가설의 승격과 퇴역

`hypotheses.jsonl`에는 가설의 정의와 `predictorVersion`, 적용 평가 구간·시장 국면을 둔다. 해당 조건에 맞는 모든 선택 leaf가 같은 predictor 판본의 `hypothesisTrials`를 갖는지 먼저 검사한다. 독립 거래일 수, 기준 대비 개선, 시장 국면 수와 최근 악화 여부는 그 전체 적격 표본과 `outcomes`를 결합해 평가기가 다시 계산한다. 원장의 선언 상태가 계산 상태와 다르면 평가를 실패시켜 임의 승격을 막는다.

- 10개 미만: `candidate`, 관찰 메모
- 10~19개: `monitoring`, 잠정 가설
- 20개 이상이며 단순 기준보다 개선: `checklist_candidate`
- 20개 이상, 평균 10bp 이상 개선, 60% 이상 표본 지지, 각 5거래일 이상 쌓인 서로 다른 고정 시장 국면 두 개 이상에서 개선 유지: `active`
- 최근 표본에서 성능 악화: `watch`
- 재현되지 않거나 기준보다 나쁨: `retired`

다음 리서치는 `active` 규칙만 판단 체크리스트에 반영한다. `candidate`와 `monitoring`은 확인할 항목일 뿐 공격·관망·방어 점수나 시나리오 확률을 직접 바꾸지 않는다.

두 수급 후보는 `promotionBlockedUntil: flow_trajectory_v1`을 유지한다. `domestic-flow-persistence`는 10시 이후 `morning_0931_1130`, `late-session-flow-acceleration`은 14시 이후 평가판만 적격으로 센다. 평가기는 두 가설의 `predictorVersion`, 평가 구간, 최소 입력 시각, `requiredInputAnchors`, 세 `requiredInputMetrics`, `requiredOutcomeFeatures`를 코드의 정본 계약과 정확히 대조해 정의 파일에서 기준을 낮출 수 없게 한다. 적격 판본은 입력·실제 궤적이 없어도 분모에서 빠지지 않으며, 평가 요약은 `eligibleSessionCount`, `verifiedInputSessionCount`, `outcomeFeatureSessionCount`, `evaluableSessionCount`, `evidenceCoverageRate`를 따로 보여준다.

`flow_trajectory_v1` 승격 차단은 문자열을 사람이 지우는 방식으로 풀지 않는다. 최근 적격 거래일이 20개이고 그 20개 모두 봉인 입력 검증과 필수 결과 feature를 충족해 최근 커버리지가 100%일 때만 자동으로 해제된다. 한 거래일이라도 `missing_input`, `missing_actual`, `input_mismatch`, `missing_outcome_feature`이면 적격 분모에는 남지만 `active` 승격은 차단된다. 미국 반도체 신호 가설은 이 수급 계약의 대상이 아니므로 이 차단을 적용하지 않는다.

## 매일의 내부 순서

1. 새 조사 전에 전 거래일의 확정값과 미정산 대표 전망을 확인한다.
2. 장 마감 확정값이 있으면 `actuals`와 `outcomes`를 추가하고 평가 요약을 갱신한다.
3. 최신 누적 오류와 `active` 가설만 읽고 새 리서치의 확인 항목을 정한다.
4. 숫자 범위를 포함한 세션 종가 전망을 제시할 때만 리서치 본문과 함께 전망 계약을 만들고 보고서 해시·데이터 기준 시각·평가 구간을 봉인한다. 회고만 있는 장마감판과 목표 거래일이 없는 주간 정리는 계약 대상이 아니다.
5. 발행 직전 수치 교체가 있으면 `dataCutoffAt`과 보고서 해시를 함께 갱신한다. 발행 뒤 정정은 새 판본으로 남긴다.
6. push·배포 확인 시각은 각각 새 publication 이벤트 파일로 추가한다.
7. 장 마감 뒤 전망 파일을 수정하지 않고 공통 실제값과 결과 판정을 추가한다.

## 과적합 방지

- 하루의 성공이나 실패로 가중치·기준선을 바꾸지 않는다.
- 같은 거래일의 여러 수정판을 독립 표본으로 세지 않는다.
- 개장 전 전망과 14시 이후 전망을 같은 집단에서 비교하지 않는다.
- 표본 10개 미만의 적중률은 공개하거나 성과로 해석하지 않는다.
- 범위를 넓혀 적중률만 높이는 변화는 범위 손실과 단순 기준 비교에서 탈락시킨다.
- 원인 설명은 사전에 기록한 관측값으로만 판정하고 장 마감 뒤 새 원인을 소급 추가하지 않는다.

## 실행

```powershell
py -3 scripts/evaluate_market_research.py `
  --evaluation-root research/evaluation `
  --repo-root . `
  --output-json research/evaluation/generated/latest.json `
  --output-md research/evaluation/generated/latest.md
```

이 산출물은 내부 평가용이다. 공개 아티클과 대시보드에는 적중률, 내부 오류 코드, 후보 가설을 노출하지 않는다.

## 발행 보고서 해시 실패의 명시적 무효화

발행 후 발견된 원시 바이트 봉인 실패는 기존 전망·보고서·발행 이벤트를 수정해서 복구하지 않는다. `research/evaluation/invalidations/<forecastId>.json`을 한 번 추가해 실패를 보존하고 성과 집계에서 제외한다. 같은 전망의 무효화 파일을 덮어쓰거나 중복 작성하지 않는다. 방향 예측 실패나 데이터 부진을 무효화 사유로 쓰지 않는다.

무효화 레코드는 `schemaVersion: 1`, `forecastId`, 원본 `contentHash`, 원래 push의 `commitSha`, 실제 발견·기록 시각 `recordedAt`, `failureCode: pushed_report_hash_mismatch`, 원본 `sealedReportSha256`, Git 커밋에서 확인한 `committedReportSha256`, 구체적인 `reason`을 모두 포함한다. 별도 필드는 허용하지 않는다.

평가기에서 두 해시와 Git 원본을 재확인하고 기존 전망·발행 이벤트 검증을 그대로 실행한다. 원본 커밋의 전망 계약이 보존됐고 보고서 해시 실패가 실제 재현될 때만 무효화를 적용한다. 불일치하지 않는 해시, 다른 push, 공개 이전 기록시각, 변조된 전망, 근거 없는 무효화는 평가 전체를 실패시킨다. 작업 트리 보고서도 봉인 또는 확인된 커밋 해시에 해당해야 하며 제3의 내용은 허용하지 않는다.

무효 판본은 JSON의 `invalidatedForecasts`·`invalidatedForecastCount`와 Markdown 실패 목록에 남고 성과·미정산 표본·가설 승격 근거에서 제외된다. 원래 검증 실패를 유효 표본으로 바꾸거나 보고서 바이트를 정규화해 봉인을 통과시키지 않는다. 새 보고서는 LF 바이트로 저장하고 스테이징된 `git show :reports/...`의 SHA-256을 봉인 전에 대조한다.
