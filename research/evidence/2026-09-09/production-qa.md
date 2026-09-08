# 2026-09-09 제작·검증 기록

- 집필: write-finished-manuscript 집필·퇴고 뒤 humanize-korean 국소 윤문. 추가 집필 모델은 동시 작업 한도 때문에 시작하지 못해 메인에서 같은 단계를 수행했다.
- 사실 보존: SOXX 상승과 NVDA·MU 하락을 구분하고, Qualcomm·Amazon 지급상한을 확정 매출로 쓰지 않았다. DRAM 품목별 가격과 주식 수급을 분리했다.
- 썸네일: 내장 image_gen 사용. 이전 이미지 참조 없이 새로 생성한 원본을 1200×630 WebP로 크롭·저장했다. 최종 파일은 `assets/images/articles/market-2026-09-09-chips-oil-1200x630.webp`다.
- 생성 프롬프트: Use case: stylized-concept. Create a new premium editorial financial article thumbnail, landscape 1200x630 composition. Topic September 9 Korea stock market: US AI semiconductor strength supported by a new cloud data center partnership, confronted by oil supply cost pressure. A luminous translucent turquoise data center connected to a crisp gold and teal semiconductor/memory stack at center-left, at right a large amber oil droplet with a gentle rising amber wave. Bright ivory and pale blue dawn background, subtle Seoul skyline far back. Physical polished glass and silicon, tasteful high-end 3D editorial illustration, crisp recognizable main objects, generous light and clear small-thumbnail readability. Mood cautious optimism. No lettering, no numbers, no logos, no watermark, no black background, no red crash arrows. Entirely new composition, no reference images. Save output for project use.
- 차트: FRED9/8 10Y-2Y +0.41%p, 10Y-3M +0.86%p. 최근90일·2년 차트 실물 확인. 절대금리는 Treasury9/8의3M3.94/2Y4.39/10Y4.80을 사용했다.
- 로컬 브라우저: 기사 제목·1200×630 썸네일·전략30/50/20·시나리오50/30/20·KODEX112000/115000/120000 확인. 390px와 기본 데스크톱 가로 넘침 없음. 로컬 서버의 최신 시세 프록시는 제공되지 않으므로 공개 사이트에서 최종 확인한다.
- 회귀: Python평가기53개; Node 게시목록·대시보드·KODEX기준선·최신기사링크·장전보존·홈검색·읽기·플로팅내비 통과.
- 최종조회 08:16:55 KST, 작성08:16:56, push08:17:40. NXT 서버 시계는08:16:56으로 조회 클라이언트와1초 차이. 보고서 LF 해시와 스테이징 원시바이트 일치. 미공개 커밋의 settle.py 끝 빈줄을 수정한 뒤 전체커밋 diff 검사 통과.
- 전일 정산: basic의CLOSE·18:59를 확인했고, 원격분봉에서15:20지수6952.65·15:19외국인4556억원 복구. 프로그램 세 시점 자료와15:30종가앵커는 결측. 원문보다 이른 시각으로 수급을 소급하지 않는다.
- 라이브 브라우저: 최신 기사·08:16작성/08:16:55데이터·1200×630이미지·콘솔오류0 확인. 대시보드 기술 차트 SVG6개에 실제 path/rect가 렌더됐고 로딩실패 문구 없음. 가로넘침없음. 검증 탭을 닫았다.
