# KOSPI·KODEX 리서치 데이터 소스

## 원칙

1. 공식 발표기관과 기업 IR을 1순위로 사용한다.
2. 거래소·지수·시세 원천 또는 이를 직접 재배포하는 페이지를 가격 확인에 사용한다.
3. Investing.com 경제 캘린더는 탐색용이며, 중요 일정은 공식 발표기관에서 재확인한다.
4. Reuters·AP 등 통신사는 사건의 맥락과 시장 반응을 교차 확인할 때 사용한다.
5. 검색 결과 요약만으로 핵심 수치를 확정하지 않고 가능한 한 원문을 연다.
6. 출처마다 갱신 시각과 시장 상태를 기록한다.

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
