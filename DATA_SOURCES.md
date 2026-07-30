# KOSPI·KODEX 리서치 데이터 소스

## 원칙

1. 공식 발표기관과 기업 IR을 1순위로 사용한다.
2. 거래소·지수·시세 원천 또는 이를 직접 재배포하는 페이지를 가격 확인에 사용한다.
3. Investing.com 경제 캘린더는 탐색용이며, 중요 일정은 공식 발표기관에서 재확인한다.
4. Reuters·AP 등 통신사는 사건의 맥락과 시장 반응을 교차 확인할 때 사용한다.
5. 검색 결과 요약만으로 핵심 수치를 확정하지 않고 가능한 한 원문을 연다.
6. 출처마다 갱신 시각과 시장 상태를 기록한다.
7. 고정 소스만 순회하지 말고 발행 전 최신 헤드라인과 가격 이상 움직임에서 새 사건을 역추적한다.

출처가 충돌하면 `정부·거래소·공시·기업 원문 > 직접 시세 원천 > Reuters·AP 등 통신사 > 경제 캘린더·검색 요약 > 소셜·커뮤니티` 순으로 판단한다. 확정 공시가 아닌 핵심 사건은 가능하면 서로 독립적인 신뢰 출처 두 곳으로 교차 확인한다.

## 개방형 이슈 발견 소스

| 발견 경로 | 우선 소스 | 사용 목적 | 확정 규칙 |
|---|---|---|---|
| 공시·규제 | DART·KIND·SEC EDGAR·거래소·정부기관 | 계약, 증자, 조사, 제재, 지분·포트폴리오 변화 | 원문 문구와 법적 형식을 그대로 구분 |
| 기업 원문 | IR, 실적콜, 뉴스룸, 프레젠테이션 | 공급계약, CAPEX, 고객 수요, 가이던스 | 고객명·금액·기간 비공개 여부까지 기록 |
| 주요 속보 | Reuters, AP, Axios, Bloomberg, FT, WSJ, CNBC | 강제청산, 블록딜, 정책·지정학, 시장 반응 | 가능하면 원문 1개와 독립 출처 1개 교차 확인 |
| 가격 이상 | KRX, Nasdaq·NYSE, CME, 공식 ETF·지수 시세 | 급등락, 거래량 급증, 장중 급반전의 원인 탐색 | 가격은 사건의 증거가 아니라 검증 신호로 사용 |
| 소셜·커뮤니티 | 공식 계정, 업계 게시물, 포럼 | 아직 색인되지 않은 사건의 탐색 단서 | 단독 근거로 공개하지 않고 원문을 찾지 못하면 제외 |

### 매일 확인할 비정형 검색군

- 강제청산·자금: `liquidation`, `forced selling`, `margin call`, `block trade`, `redemption`, `portfolio sale`
- 공급 부족: `long-term supply agreement`, `prepayment`, `capacity reservation`, `sold out`, `allocation`
- 정책·운영: `export control`, `sanction`, `investigation`, `outage`, `recall`, `strike`, `shipping disruption`
- 실적 변화: `guidance cut`, `capital raise`, `downgrade`, `order cancellation`, `customer concentration`

발견 후보는 `.agents/skills/kospi-daily-research/references/issue-radar.md`의 기준으로 순위를 매긴다. 검색량이나 소셜 반응만으로 중요도를 높이지 않는다.

## 소스 매트릭스

| 영역 | 1차·공식 소스 | 보조 소스 | 확인 항목 |
|---|---|---|---|
| KOSPI·KOSPI200·종목 | [KRX](https://data.krx.co.kr/), KRX 기반 국내 시세 | [네이버 금융](https://finance.naver.com/) | 현재가, OHLC, 시장 폭, 투자자·프로그램 수급 |
| KODEX 레버리지 | [삼성자산운용](https://www.samsungfund.com/), KRX | 네이버 금융 | 현재가, NAV, 거래량, 투자자 수급 |
| USD/KRW | [한국은행 ECOS](https://ecos.bok.or.kr/), 서울외환시장 | [Investing.com USD/KRW](https://www.investing.com/currencies/usd-krw) | 현재가·종가·범위·확인 시각 |
| 한국 경제 | [한국은행](https://www.bok.or.kr/), [산업통상자원부](https://www.motie.go.kr/), [통계청](https://kostat.go.kr/) | Investing.com | 금통위, 경상수지, 수출입, 물가 |
| 미국 통화정책 | [Federal Reserve](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) | Investing.com | 회의·성명·의사록·기자회견 |
| 미국 물가·고용 | [BLS](https://www.bls.gov/schedule/), [DOL](https://www.dol.gov/) | Investing.com | CPI, PPI, 고용, 실업수당 |
| 미국 GDP·PCE | [BEA](https://www.bea.gov/news/schedule) | Investing.com | GDP, 소득·소비, PCE |
| 미국 국채 | [U.S. Treasury](https://home.treasury.gov/resource-center/data-chart-center/interest-rates), [FRED](https://fred.stlouisfed.org/) | Investing.com | 3M·2Y·10Y 절대금리, 장단기 금리차 |
| 메모리 가격 | [TrendForce DRAMeXchange](https://www.trendforce.com/price/dram/dram_spot) | 기업 실적자료 | DRAM·NAND 현물, 계약가격 전망 |
| 삼성전자 | [Samsung Electronics IR](https://www.samsung.com/global/ir/) | Reuters | 실적, HBM, DRAM, NAND, CAPEX |
| SK하이닉스 | [SK hynix IR](https://www.skhynix.com/ir/UI-FR-IR01/) | 뉴스룸·Reuters | 실적, HBM, 수율, CAPEX, 고객 수요 |
| Micron | [Micron IR](https://investors.micron.com/) | Reuters | 실적, 가격, CAPEX, HBM |
| 미국 빅테크 | 각 기업 IR | Reuters·AP | 실적, Cloud, AI CAPEX, 수익화 |
| 경제 일정 탐색 | 각 공식 캘린더 | [Investing.com 경제 캘린더](https://www.investing.com/economic-calendar/) | 실제·예상·이전, 중요도 |

## FRED 시리즈

| 시리즈 | 의미 | URL |
|---|---|---|
| `T10Y2Y` | 10년물 - 2년물 | https://fred.stlouisfed.org/series/T10Y2Y |
| `T10Y3M` | 10년물 - 3개월물 | https://fred.stlouisfed.org/series/T10Y3M |

차트 스크립트는 FRED CSV를 직접 내려받으며 결측치 `.`를 제외한다. 두 시리즈의 최신 관측일이 다르면 각 선의 최신 날짜를 따로 표기한다.

## 시각·단위 규칙

- 보고서 기준 시각: `YYYY-MM-DD HH:MM KST`
- 미국 일정: 원래 `ET` 또는 `PT`와 변환한 `KST`를 함께 기록
- 금리: `%`, 금리차: `%p`
- 국내 수급: `억원` 또는 `조원`, 단위를 표에 명시
- 가격: 통화 단위를 열 제목 또는 값에 포함
- 장중 데이터는 `실시간`이라고 단정하지 말고 출처의 표시 시각을 그대로 쓴다.

## 교차 검증 체크리스트

- 지수 등락률과 전일 종가가 산술적으로 일치하는가
- 종목 가격의 시가·고가·저가 범위 안에 현재가가 있는가
- 현물·선물 수급 단위가 계약수와 금액 중 무엇인지 구분했는가
- 미국 종가와 시간외 등락을 섞지 않았는가
- 경제 일정의 날짜가 KST 변환 후 하루 바뀌는지 확인했는가
- ADR·EWY가 한국장의 기존 움직임을 후행 반영했는지 확인했는가
- 기사 속 전망과 기업·기관의 확정 발표를 구분했는가
- 공개주식 매각을 펀드 폐쇄·파산으로 확대 해석하지 않았는가
- MOU·협상·장기공급계약·공시 매출액을 정확히 구분했는가
- 오늘의 제목과 첫 분석이 이슈 레이더 최상위 사건을 반영하는가
