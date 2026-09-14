# 2026-09-15 밤사이 취재 노트

- 추가 원시 시세 대조 08:08 KST: 저장한 Yahoo chart 정규장 meta가 QQQ 709.18(-0.797%), SOXX 497.40(-5.629%)를 지지한다. 공개값은 이 정규장 시각 meta와 StockAnalysis 상단이 일치하는 값을 채택한다. historical 행의 차이는 원천 차이로 보존한다. 다른 6개 자산도 Yahoo meta와 위 표 종가가 일치한다.
- FRED CSV 실행 결과의 9/14 T10Y2Y +0.32%p, T10Y3M +0.86%p를 오늘 차트로 생성했다. 아래 DGS 개별 시리즈 9/11 값은 관측일 지연 설명이며 최신 Treasury 9/14 행으로 공개 금리표를 대체한다.

- 조사 시각: 2026-09-15 08:01~08:06 KST. 공개 원고가 아닌 집필용 근거.
- 미국 9월 14일 정규장 종료, 시간외 진행. 한국 9월 15일 정규장 개장 전. 아래 시간외 시세는 각 원문 표시 시각이며 발행 직전 시세가 아니다.
- RESEARCH_SPEC.md, DATA_SOURCES.md, STATE.md, issue-radar.md 확인. 전날 STATE 숫자는 현재값으로 재사용하지 않았다.

## 이슈 후보와 선택

점수 순서: 국내 노출/가격 확인/새로움/출처/속도, 최대 13. 점수는 내부 우선순위이며 투자확률이 아니다.

|후보|점수|처리와 전달 경로|
|---|---|---|
|AI 개발 속도조절 논쟁 이후 미국 반도체 집중 매도|3/3/1/3/2=12|상위. 주말 발언은 한국 9/14에 이미 공개되어 있었다. 새로운 미국 가격 반응과 한국장 마감 이후의 정책 논쟁만 추가 정보. 국내 메모리 밸류에이션·외국인 수급 경로.|
|사우디 송유관 차질 장기화 우려와 유가 급등 후 상승폭 축소|3/3/2/2/2=12|상위. AP의 수리 3~5주 전망은 익명 지역 당국자 2명 발언이지 확정 복구 일정이 아니다. Reuters 정산 Brent 105.68달러, WTI 101.39달러. 국내 수입물가·달러 수요·마진 경로.|
|미 10년물 장중 5% 돌파, FOMC 임박|3/3/2/2/2=12|상위. 주가 할인율과 AI 인프라 자금조달 비용. 5% 돌파는 장중, FRED 최신 확정 일별값은 9/11로 시계열 분리.|
|미국 지수 낙폭 회복 및 반도체 시간외 소폭 반등|3/3/2/2/2=12|상위 반대 신호. Nasdaq -0.56%에 비해 반도체 약세가 훨씬 큼. 소폭 시간외 반등은 정규장 손실 만회가 아니다.|
|DDR5 현물 보합, DDR4 품목별 엇갈림|3/1/1/3/1=9|보조. 당일 HBM 계약 취소나 메모리 수요 붕괴의 증거로 확대하지 않는다.|
|Oracle 9/10 실적·AI 계약과 Broadcom 9/2 가이던스|3/1/0/3/1=8|배경. 기존 계약·실적과 주식 재평가를 분리. 오늘 새 실적처럼 쓰지 않는다.|
|60개국 강제노동 관세가 오늘 반도체 매도를 유발했다는 웹 기사|3/1/0/3/1=8|제외. USTR 원문 발표는 7/23. 9/14 신규 관세 발표로 재포장하지 않는다.|
|강제청산·마진콜·블록딜·신규 대형 증자|2/0/0/0/1=3|제외. 날짜 포함 탐색에서 오늘 주도 사건을 뒷받침하는 새 공시 미확인. 비사건을 공개 원고에 쓰지 않는다.|

## AI 원문과 사실 경계

[Dario Amodei 원문](https://darioamodei.com/post/we-must-pace-the-frontier): 모델 능력 개선 속도조절을 제안. 원문은 모델 훈련이나 기술진보의 중단을 뜻하지 않는다고 명시한다. Anthropic이 당장 약속한 것은 외부 평가자 상주 접근이며, 산업 전체·국제 조율은 별도 단계다. 따라서 전 세계 AI 투자 중단, GPU 주문 취소, HBM 공급계약 취소로 쓰면 안 된다.

[AP 9/12 보도](https://apnews.com/article/d59552edcb27892d8ee4d98a48397706), [Reuters 9/14 장중 시장 보도](https://currently.att.yahoo.com/att/ai-warnings-knock-nasdaq-futures-092329455.html)와 날짜·시장반응 대조. [Axios 9/14 트럼프 반대 발언](https://www.axios.com/2026/09/14/trump-ai-safety-anthropic-dario-amodei) 17:59 UTC는 한국 9/15 02:59에 해당. 새 규제 시행 공시와 정치적 발언을 구분한다.

해석 후보: 당장 출하량보다 향후 투자 속도와 프리미엄에 대한 재평가가 주가를 압박. 무효화·완화 조건은 메모리주 가격 회복과 외국인 매도 둔화, 미국 선물 안정. 실제 CAPEX 하향·계약 취소가 나오면 펀더멘털 판단을 별도 갱신.

## 미국 정규장·시간외

StockAnalysis 각 상단의 9/14 16:00 EDT 종가 채택. KST 9/15 05:00. 시간외는 종가 대비.

|자산|종가 USD|정규장|시간외 USD / 변동|시간외 KST|출처|
|---|---:|---:|---|---|---|
|QQQ|709.18|-0.80%|709.84 / +0.09%|07:53|[StockAnalysis](https://stockanalysis.com/etf/qqq/history/), [CoinGlass](https://www.coinglass.com/stocks/QQQ)|
|TQQQ|69.27|-2.41%|69.35 / +0.12%|07:45|[원문](https://stockanalysis.com/etf/tqqq/history/)|
|SOXX|497.40|-5.63%|499.68 / +0.46%|07:51|[원문](https://stockanalysis.com/etf/soxx/history/)|
|SMH|541.50|-4.75%|543.50 / +0.37%|07:34|[원문](https://stockanalysis.com/etf/smh/history/)|
|Nvidia|210.96|-3.36%|212.26 / +0.62%|07:38|[원문](https://stockanalysis.com/stocks/nvda/history/)|
|AMD|493.41|-4.40%|493.80 / +0.08%|07:50|[원문](https://stockanalysis.com/stocks/amd/history/)|
|Micron|924.03|-5.25%|926.50 / +0.27%|07:50|[원문](https://stockanalysis.com/stocks/mu/history/)|
|Broadcom|344.72|-4.77%|346.40 / +0.49%|07:49|[원문](https://stockanalysis.com/stocks/avgo/history/)|

데이터 경계: QQQ 일봉 행은 709.26(-0.79%)로 상단과 다르나 CoinGlass 및 Investing ETF 표가 709.18(-0.80%)을 지지. SOXX 일봉 행은 497.70(-5.57%)로 상단과 상충하므로 공개 정밀값은 추가 직접 시세 교차 확인이 권장된다. Nasdaq 공식 historical 페이지를 열었으나 숫자 행을 추출하지 못했다. 공식 정밀 종가를 모두 확인했다고 표현하지 않는다. SOXX를 본문에서 약 5.6% 하락으로 표현하면 두 수치의 공통 방향·규모를 보존한다.

[AP 종가 요약](https://apnews.com/article/8f72a301be85728018018735163f4dad): Nasdaq 26,186.41(-146.62, -0.6%), Dow 52,421.20(-152.09, -0.3%), S&P500 7,619.98(-37.00, -0.5%). Reuters/Investing S&P 표시 7,619.96과 0.02 차이. Nasdaq 두 출처 일치하며 정확 등락률 -0.56%. 지수 전반과 반도체 ETF 하락을 혼동하지 않는다.

## 유가·금리

[Reuters 9/14 정산](https://www.investing.com/news/commodities-news/oil-prices-climb-over-2-after-strikes-on-saudi-pipeline-and-ships-in-middle-east-4900107): Brent +1.07달러(+1.0%) 105.68달러, WTI +1.34달러(+1.3%) 101.39달러. 장중 약 5% 급등 뒤 트럼프의 이란 협상 의향 발언으로 상승폭 축소. 협상 타결은 아니다. 송유관·홍해 위험은 한국 월요일에 이미 알려졌으므로 후속 차질 기간과 정산가만 새 정보로 다룬다.

[AP 후속](https://apnews.com/article/efa431e2fa771e34880c8453c62ffb92): 수리 3~5주 가능성은 익명 지역 당국자 2명 추정. 공식 확정 복구 일정 미확인. Reuters의 5~7일 항구 재고도 업계 관계자 추정이며 확정 공급손실과 다르다.

[Reuters 금리](https://www.investing.com/news/economy-news/us-10year-yields-reach-5-highest-since-2023-4899925): 9/14 장중 10년물이 5%를 넘음. 기사 속 마지막 값 5.01%, Investing 시세판 18:25:18 표시 4.991%, 고가 5.017%로 시각이 다르므로 5.01%를 확정 종가로 쓰지 않는다.

FRED 현재 재조회 최신 관측일 9/11: [10년 4.96%](https://fred.stlouisfed.org/series/DGS10), [2년 4.63%](https://fred.stlouisfed.org/series/DGS2), [3개월 4.07%](https://fred.stlouisfed.org/series/DGS3MO). 갱신 표시는 9/14 15:16 CDT지만 관측일은 9/11. 같은 날 차이는 10Y-2Y +0.33%p, 10Y-3M +0.89%p. 9/14 실시간 10년과 이 값들을 섞어 최신 스프레드를 만들지 않는다.

08:08 KST 추가 검증: [미 재무부 공식 일별 Par Yield 표](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2026) 9/14 행·열 제목을 직접 대조했다. **3개월 4.11%, 2년 4.65%, 10년 4.97%**. 10Y-2Y +0.32%p, 10Y-3M +0.86%p로 오늘 생성 차트와 일치. 공개 보고서의 최신 일별 금리는 이 재무부 9/14 값을 채택하고, FRED DGS 페이지의 하루 늦은 값과 혼합하지 않는다. 장중 5% 돌파와 일별 4.97%는 모순이 아니라 관측 기준 차이다.

## 메모리·기업

[TrendForce DRAM](https://www.trendforce.com/price/dram/dram_spot) 9/14 18:10 GMT+8(19:10 KST): DDR5 16Gb 4800/5600 session average 54.333달러, 0.00%; DDR4 16Gb 3200 89.25달러 -0.56%; DDR4 8Gb 3200 45.571달러 +0.79%. 현물 특정 품목 수치이며 HBM 계약가격이 아니다. [NAND](https://www.trendforce.com/price/flash/flash_spot) 최신 표시는 9/7 14:40 GMT+8로 낡아 오늘 변화 판단에서 제외.

[Oracle 9/10 공식 실적](https://investor.oracle.com/investor-news/news-details/2026/Oracle-Announces-Q1-Results-Driven-by-Triple-Digit-Growth-in-Cloud-Infrastructure-Revenues/default.aspx): FY27 Q1 매출 193억달러, 클라우드 인프라 매출 74억달러(+121%), RPO 6,640억달러, 분기 추가 AI 클라우드 계약 300억달러 초과. 회사는 이 신규 계약 구조에 따른 추가 자금조달 계획 영향이 없다고 설명. 이미 발표된 자료이며 이번 밤사이 실적이 아니다.

[Broadcom 9/2 공식 실적](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2026-financial): Q3 매출 296억달러(+86%), Q4 매출 가이던스 약 348억달러. 기존 전망이며 월요일 주가 하락을 가이던스 하향으로 쓰지 않는다.

[USTR 7/23 공식 발표](https://www.ustr.gov/about/policy-offices/press-office/press-releases/2026/july/ustr-takes-action-forced-labor-section-301-investigations): 60개국 관세 관련 9/14 재서술 웹 기사를 신규 사건에서 제외한 근거.

## 공식 일정

- [Fed FOMC](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm): 9/15~16, SEP 포함. 결정 9/16 14:00 ET = 9/17 03:00 KST, 기자회견 03:30 KST(표준 발표 시각; 발행 담당 최종 캘린더 확인).
- [Census 소매판매](https://www.census.gov/retail/release_schedule.html): 8월분 9/16 08:30 ET = 9/16 21:30 KST.
- [BLS 수출입물가](https://www.bls.gov/schedule/2026/): 8월분 9/16 08:30 ET = 9/16 21:30 KST. CPI 9/11, PPI 9/10은 이미 발표.
- [Fed 산업생산 G.17](https://www.federalreserve.gov/releases/g17/): 9/18 09:15 ET = 9/18 22:15 KST. 9/15로 오기 금지.
- [Micron 공식 IR](https://investors.micron.com/news/press-release/2026/Micron-Technology-to-Report-Fiscal-Fourth-Quarter-Results-on-September-30-2026/default.aspx): FY Q4 콜 9/30 14:30 Mountain = 10/1 05:30 KST. 9/23은 2025 일정이므로 사용 금지.

## 발행 담당자 재조회 항목

08:05 전후 웹판: [Nasdaq100 12월 선물](https://www.investing.com/indices/nq-100-futures) 29,461.50(+0.04%), 표시 18:33:10; 9/13에 12월물로 교체되었으므로 9월물 절대값과 비교 금지. [USD/KRW](https://www.investing.com/currencies/usd-krw) 1,347.32(+0.02%), 표시 18:06:05. 시세판 시간대가 원문에 명시되지 않아 이 표시를 임의로 KST로 변환하지 않는다. 국내 원천·미국 선물·NXT 최종 조회로 대체할 것. 이 노트 작성 시점의 값은 발행 최종 확인값이 아니다.
