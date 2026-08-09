# 발행·배포 이벤트

전망 원본을 다시 수정하지 않고 실제 push와 배포 확인을 각각 새 JSON 이벤트로 추가한다. 파일명은 `<forecastId>-pushed.json`, `<forecastId>-deploy_verified.json`을 사용한다. 두 이벤트는 전망 계약과 같은 `contentHash`, 서로 동일한 `commitSha`를 가져야 한다. 해당 commit에는 전망 JSON뿐 아니라 `reportPath` 원문도 있어야 하고 그 SHA-256이 `reportSha256`과 일치해야 한다. `deploy_verified`는 `availabilityStatus: available`과 독자가 실제로 접근한 `publicUrl`도 기록한다. push는 `issuedAt`부터 5분, 배포 확인은 10분 안이고 둘 다 같은 평가 구간·목표일 종가 전이어야 한다. 기존 이벤트를 수정해 나중 시각을 덧붙이지 않는다. `visibility: public` 전망은 두 이벤트가 모두 있어야 정산되며, `visibility: internal` 전망에는 이벤트를 만들지 않는다.
