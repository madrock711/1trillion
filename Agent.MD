# Agent Instructions

- 세션 시작 시에만 `git pull --rebase --autostash`를 수행한다.
- 작업 완료 후 항상 `git push`까지 수행한다.
- 문서 작업은 기본으로 한글로 작성한다.

# 작업 가이드라인

이 문서는 앱 가이드/콘텐츠 수정 시 헷갈리지 않도록 만든 작업 기준입니다.

## 1) i18n 규칙
1. 번역 대상 요소는 반드시 `data-i18n`을 가진다.
2. HTML 삽입이 필요한 경우 `data-i18n-html`을 사용한다.
3. `data-i18n-html` 사용 시에도 `data-i18n`을 같이 넣어야 적용된다.
4. 긴 콘텐츠는 `i18n.js`의 `...Html` 키로 관리한다.
5. 한/영 전환은 모든 키에 대해 `en`과 `ko` 모두 정의한다.

## 2) 콘텐츠 구조
1. “더 읽기”는 `<details>` + `<summary>`로 구성한다.
2. 본문 HTML은 `data-i18n-html`로 주입한다.
3. 표/체크리스트/구분선은 공통 스타일 클래스로 처리한다.

## 3) 스타일 규칙
1. 장문 영역은 `.guide-details` / `.guide-details-body`를 사용한다.
2. 표는 `border-collapse`, 헤더 강조, 적당한 패딩을 유지한다.
3. 체크리스트는 `.checklist`로 통일한다.

## 4) 버전/캐시
1. i18n 변경 시 `index.html`의 `i18n.js?v=YYYYMMDD-N`을 증가시킨다.

## 5) 파일 관리
1. 외부 문서/참고 파일은 반영 후 삭제한다.
2. 불필요한 로그(`firebase-debug.log`)는 커밋에 포함하지 않는다.

## 5.1) 커밋/푸시 원칙
- 커밋과 푸시는 항상 함께 진행한다.

## 6) 시작 체크리스트
- `i18n.js`에 새 키 추가했는가?
- `data-i18n` + `data-i18n-html` 둘 다 넣었는가?
- `index.html`의 `i18n.js` 버전이 증가했는가?

## 7) 콘텐츠 삽입 규칙
- 장문은 `...Html` 키로만 관리한다.
- HTML은 single-quote 문자열로 넣고 `'`는 반드시 이스케이프한다.
- 표/체크리스트는 기존 스타일 클래스를 재사용한다.

## 8) 시퀀스 생성기/마스크 기능 작업 기록 (2026-02-18)
### 탭/앱 통합
1. 시퀀스 생성기를 앱 탭에 통합하고 `video-to-sprite-sheet.html`은 안내 배너만 유지.
2. 탭 구조는 기존 `.tabs`, `.tab-link`, `.tab-content` 패턴을 그대로 사용.
3. 새 탭의 공유 버튼은 `data-share-tab="sequence"`로 연결.

### 마스크 적용 기능
1. 마스킹 텍스처 업로드/드래그 앤 드롭 지원.
2. 마스크 반전 옵션 추가.
3. 알파가 없는 흑백 마스크는 **밝기→알파**로 변환해 적용.
4. 마스크는 항상 프레임 크기에 맞춰 **늘려 적용**.

### 마스크 생성기
1. 생성기 UI 내에서 직접 마스크 생성 가능.
2. 옵션 구성:
   - 노이즈 알고리즘: Perlin/Simplex, Worley/Voronoi, Ridged, White.
   - 형상: Radial/Linear/Diamond/Square, Edge Softness, Polar Coordinates.
   - 왜곡: UV Warp, Swirl/Twirl, Pixelate.
   - 후처리: Threshold, Contrast, Gamma.
   - Tiling: Seamless 반복.
   - Intensity(강도), Scale(스케일) 추가.
3. 슬라이더 조정 시 실시간 미리보기.
4. 폴라 코디네이트 심라인 완화 처리.
5. UV Warp로 인한 외곽 튐 방지(기본 좌표 기반 마스크 클램프).

### 프리셋/저장
1. 기본 프리셋 제공(Soft/Hard/Dissolve/Noise).
2. 저장 시 이름 입력 → 드롭다운에 추가.
3. 드롭다운 선택 시 즉시 불러오기(불러오기 버튼 제거).
4. 저장 상태 표시(저장됨/불러옴/실패).

### 입력/UI 개선
1. 입력 필드 오버플로우 방지(`min-width:0`, `box-sizing:border-box`).
2. 슬라이더 텍스트 선택 방지(`user-select:none`).
3. 슬라이더 값 실시간 표시.

### 관련 파일
- `index.html` (시퀀스 탭, 마스크 UI, 프리셋 드롭다운)
- `sequence-generator.js` (생성 로직, 마스크 합성, 저장/프리셋)
- `style.css` (시퀀스/마스크 스타일)
- `i18n.js` (시퀀스/마스크 키 추가)
