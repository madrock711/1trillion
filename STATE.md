# KOSPI·KODEX 리서치 상태

> 이 파일은 마지막 완료 실행을 가리키는 스냅샷이다. 현재 시세나 장 마감 확정값의 원천이 아니며, 새 실행에서는 모든 시장 수치를 다시 조회한다. 과거 전망과 회고는 `research/evaluation/`에서 관리한다.

## 마지막 완료 실행

- 기준일: 2026-08-07
- 데이터 기준 시각: 09:11 KST
- 시장 상태: 한국 정규장 개장 초반
- 최신 보고서: `reports/2026-08-07-0911.md`
- 최신 공개 글: `articles/market-2026-08-07.html`
- 시황 대시보드: `articles/market.html`
- 최신 대시보드 스냅샷: `assets/data/market-dashboard-20260807-0911.json`
- 최신 대시보드 포인터: `assets/data/market-dashboard-latest.json`
- 최신 장기 차트: `charts/us_yield_spreads_long_term_2026-08-07.png`
- 최신 90일 차트: `charts/us_yield_spreads_90d_2026-08-07.png`
- 다음 대형 이벤트: 미확정 — 다음 리서치 실행에서 공식 일정으로 새로 확인

## 당시 스냅샷

- KOSPI: 6,385.43, +1.41%; 시가 6,365.07 / 고가 6,415.60 / 저가 6,352.61 / 전일 6,296.38
- KOSDAQ: 810.50, +1.10%
- KODEX 레버리지: 94,845원, +2.87%; 시가 93,920원 / 고가 95,830원 / 저가 93,560원 / 전일 92,200원
- 삼성전자: 236,750원, +2.71%; SK하이닉스: 1,517,000원, +1.47%
- 달러/원: 1,424.40원(09:09 KST)
- 외국인 현물 +2,971억원, 기관 +30억원, 개인 -2,690억원
- 프로그램: 차익 +89억원, 비차익 +2,282억원, 전체 +2,371억원
- 시장 폭: 상승 596 · 보합 57 · 하락 231

## 당시 전망 계약 요약

- 대응 점수: 공격 30 / 관망 50 / 방어 20
- 기본 범위: 6,300~6,400
- 강세 범위: 6,400~6,500
- 약세 범위: 6,220~6,300
- 기준선: KOSPI 6,365.07 회복·6,296.38 방어; KODEX 93,920원 회복·92,200원 방어

이 전망은 새 정형 원장이 도입되기 전의 과거 판본이다. 저장소에 8월 7일 KOSPI 확정 종가·최종 수급 정본이 없어 새 누적 점수에는 포함하지 않는다. 비정규 감사 기록은 `research/evaluation/legacy-audit.jsonl`에 있다.

## 누적 평가 포인터

- 평가 규칙: `docs/KOSPI_RESEARCH_EVALUATION.md`
- 전망 원본: `research/evaluation/forecasts/`
- 거래일 확정값: `research/evaluation/actuals/`
- 전망별 판정: `research/evaluation/outcomes/`
- 실제 발행 시각: `research/evaluation/publications/`
- KRX 거래일 순서: `research/evaluation/trading-sessions.json`
- 가설 원장: `research/evaluation/hypotheses.jsonl`
- 과거 감사: `research/evaluation/legacy-audit.jsonl`
- 최신 자동 요약: `research/evaluation/generated/latest.md`

현재 등록된 가설은 모두 `candidate`다. 두 수급 가설만 `promotionBlockedUntil: flow_trajectory_v1`이며, 09:30·10:00·14:00·종가 앵커와 봉인 입력을 대조한 최근 적격 20거래일의 증거 커버리지가 100%가 될 때까지 활성 규칙이나 성과 주장에 사용하지 않는다. 수급 지속성은 10시 이후 morning 판본, 장 후반 가속은 14시 이후 판본만 적격으로 센다. 미국 반도체 신호 가설은 수급 궤적 계약의 차단 대상이 아니다.

## 다음 실행 규칙

1. 현재 시각·시장 상태·시세·수급·일정을 새로 조회한다.
2. 전 거래일 확정값이 있으면 미정산 전망을 먼저 정산한다.
3. 목표일과 직전 거래일을 KRX 거래일 순서에서 확인하고, 공개판은 계약 해시·commit SHA·실제 공개 URL 가용성이 연결된 push·배포 이벤트가 시간 제한 안에 모두 있는지 검사한다.
4. 공개판은 최초 push 판본, 내부 실험은 마지막 leaf만 대표로 삼아 거래일 동일 가중으로 누적 집계한다.
5. `active` 가설만 판단 체크리스트에 반영한다. 적격 선택 판본은 모두 같은 predictor 판본을 시험한다.
6. 새 전망은 보고서 해시·데이터 기준 시각·기준값 신선도를 봉인하고, 정정판은 새 ID로 보존한다.
