# 전망 원본

목표 거래일 장 마감 전에 확정한 전망 계약 JSON만 둔다. 파일은 `forecastId.json`으로 저장하고, 결과·오류 코드·push·배포 시각·사후 해석을 넣지 않는다. 공개·내부 구분, 당일 또는 다음 거래일 목표, 고정 시장 국면과 기준값 종류·시각을 함께 봉인한다. 계약 전체는 `contentHash` 자신을 제외한 정렬 JSON의 SHA-256으로 봉인한다. 같은 평가 구간의 수정판은 `supersedes`로 한 줄의 계보를 만든다. 공개판이 있으면 실제 push가 가장 빠른 최초 공개판, 공개되지 않은 내부 실험만 마지막 leaf를 누적 대표로 쓴다. 적격 가설은 모든 선택 대표에 같은 `predictorVersion`의 후보·기준 예측값을 `hypothesisTrials`로 봉인한다.

두 수급 가설의 trial은 정의가 요구한 앵커의 외국인 현물·프로그램 비차익·전체 누적값, 시각, 출처, 원문 해시를 `predictorInputs`에 넣고 `canonicalHash`로 봉인한다. 입력 기준 시각은 `dataCutoffAt`을 넘을 수 없다. 입력이 없더라도 trial을 삭제하지 않고 `inputStatus: missing`과 누락 증거를 남겨 적격 분모를 보존한다.

필수 필드와 검증 규칙은 `docs/KOSPI_RESEARCH_EVALUATION.md`를 따른다.
