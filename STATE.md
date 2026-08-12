# KOSPI·KODEX 리서치 상태

## 최신 기준 · 2026-08-13 08:14 KST

- 최신 보고서: `reports/2026-08-13.md`
- 시장 상태: 한국 정규장 개장 전
- KOSPI 직전 종가 6,579.04(+3.68%), KODEX 레버리지 100,300원(+8.34%)
- 8월 12일 현물 수급: 외국인 +27,377억원, 기관 +6,157억원, 개인 -31,782억원
- 달러/원 1,419원대
- 오늘 판단: 공격 30 / 관망 50 / 방어 20
- 기본 6,550~6,699, 강세 6,700~6,820, 약세 6,400~6,549
- 다음 이벤트: 8월 13일 21:30 KST 미국 7월 PPI·신규 실업수당
- 새 변수: 미국 CPI 예상 부합, SOXX +2.32%·Micron +4.92%, Nebius AI 클라우드 수요 확인
- 유지 변수: DDR5·DDR4 현물 강세와 서버 DRAM 공급 제약은 중기 메모리 수요를 지지
- 직전 전망 평가: 8월 12일 KOSPI는 강세 종가 상단 6,550과 장중 경로 상단을 모두 넘어 외국인 수급의 크기와 반도체 동반 상승을 과소평가했다.

> 이 파일은 마지막 완료 실행을 가리키는 스냅샷이다. 현재 시세나 장 마감 확정값의 원천이 아니며, 새 실행에서는 모든 시장 수치를 다시 조회한다. 과거 전망과 회고는 `research/evaluation/`에서 관리한다.

## 마지막 완료 실행

- 기준일: 2026-08-13
- 데이터 기준 시각: 08:11 KST
- 시장 상태: 한국 정규장 개장 전
- 최신 보고서: `reports/2026-08-13.md`
- 최신 공개 글: `articles/market-2026-08-13.html`
- 시황 대시보드: `articles/market.html`
- 최신 대시보드 스냅샷: `assets/data/market-dashboard-20260813-0814.json`
- 최신 대시보드 포인터: `assets/data/market-dashboard-latest.json`
- 최신 장기 차트: `charts/us_yield_spreads_long_term_2026-08-13.png`
- 최신 90일 차트: `charts/us_yield_spreads_90d_2026-08-13.png`
- 다음 대형 이벤트: 8월 13일 21:30 PPI·신규 실업수당, 8월 14일 21:30 소매판매

## 당시 스냅샷

- KOSPI 직전 종가 6,579.04, KOSDAQ 858.91, KODEX 레버리지 100,300원
- 삼성전자 255,500원(+6.68%), SK하이닉스 1,504,000원(+5.54%)
- 8월 12일 현물 수급: 외국인 +27,377억원, 기관 +6,157억원, 개인 -31,782억원
- 미국장은 S&P500 +0.26%, Nasdaq +0.54%, SOXX +2.32%, Micron +4.92%였다.

## 당시 전망 계약 요약

- 대응 점수: 공격 30 / 관망 50 / 방어 20
- 기본 범위: 6,550~6,699
- 강세 범위: 6,700~6,820
- 약세 범위: 6,400~6,549
- 기준선: KOSPI 6,550 방어·6,668.43 돌파, KODEX 98,000원 방어·100,300원 유지·103,500원 돌파

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
