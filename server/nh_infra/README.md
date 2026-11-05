# 연마 개인 수급 API 배포 준비

이 디렉터리는 Google 로그인으로 본인을 확인한 뒤 NH 투자자별 수급을 조회하기 위한 AWS 설정을 담는다. 2026-11-05 현재 bootstrap과 운영 스택이 배포됐으며, 보안 쿠키 로그인 유지와 실제 NH 금액·수량 차트 표시를 확인했다. 현재 운영 구조와 토큰 발급·장애 대응은 [개인 NH API 설명](../nh_private/README.md), 세션 보안은 [세션 설명](../nh_private/SESSION_AUTH.md)을 따른다. 아래 최초 구축 절차와 [AWS IAM 설정 안내](AWS_IAM_설정_안내.md)는 재구축·복구 시 참고한다.

## 파일과 리소스

- `iam-bootstrap.json`: 관리자가 직접 적용하는 1회 설정. 전용 HTTP API와 공개 차단·버전 관리 S3 버킷, Lambda 실행 역할 `yeonma-nh-runtime`, CloudFormation 서비스 역할 `yeonma-nh-cfn`, CLI 사용자 `codex-amplify-manager`에 연결할 IAM 정책을 만든다. API ID는 이 스택에서 결정된다. 구체적인 방법과 비용·권한 위험은 [AWS IAM 설정 안내](AWS_IAM_설정_안내.md)를 따른다.
- `template.yaml`: 별도 운영 스택 `yeonma-nh-private`용 준비안. bootstrap이 만든 API와 실행 역할을 참조하며, DynamoDB 테이블 `yeonma-nh-token`, Lambda `yeonma-nh-private`, 로그 그룹, Google JWT 인증기, API 경로·스테이지를 만든다. IAM 역할을 직접 만들거나 기존 다른 API·버킷을 변경하지 않는다.
- `../nh_private/`: 인증 후에만 수급을 제공하는 서버 코드와 토큰 동시 발급 방지 코드. 자세한 조건과 테스트 상태는 [개인 NH 수급 API 안내](../nh_private/README.md)를 따른다.

bootstrap과 운영 스택은 서로 다른 작업이다. bootstrap만으로는 NH 시세 경로나 로그인 화면이 작동하지 않는다. 변경 세트와 배포 결과를 검토하고 실환경 인증·접근 통제·토큰 전환을 검증해야 한다. AWS `ValidateTemplate`도 마지막 확인 당시 CLI 사용자의 권한 부족으로 실행하지 못했으므로 실제 배포 전에 다시 확인한다.

## 인증과 비밀 보호

- HTTP API의 JWT authorizer는 Google issuer `https://accounts.google.com`, 지정된 OAuth 웹 클라이언트 ID를 검증한다. Lambda는 게이트웨이가 전달한 클레임에서 지정된 계정의 `sub`, 이메일과 이메일 검증 상태를 추가 확인한다. Lambda는 토큰 서명을 직접 검증하지 않으므로 authorizer를 우회하는 공개 Function URL이나 검증 없는 직접 호출 경로를 만들지 않는다.
- CORS는 `https://www.hpmplab.com`에 한정하지만 인증을 대신하지 않는다. 응답과 인증 정보는 캐시하지 않으며, API Gateway·HTTP 디버그 로그·추적에 ID 토큰, NH 키·시크릿, NH 토큰, 시세 본문을 남기지 않는다. NH 발급 명세는 키와 시크릿을 HTTPS URL의 쿼리로 요구하므로 요청 URL과 원본 예외도 기록하지 않는다.
- NH 자격증명은 표준 SSM SecureString `/yeonma/private/nhplug`에 기본 AWS 관리형 `aws/ssm` 키로 저장한다. 값은 별도 안전한 경로로 전달하고 Git·명령줄 인자·셸 기록·채팅·CloudFormation 매개변수에 넣지 않는다. Windows DPAPI로 보호된 기존 파일은 AWS에서 그대로 열 수 없다.
- 토큰은 DynamoDB의 기본 저장 시 암호화로 보호하며 애플리케이션 차원의 추가 암호화는 하지 않는다. **전용 테이블의 항목을 읽을 수 있는 IAM 주체는 토큰을 볼 수 있다.** AWS 관리형 `aws/ssm` 키는 고객 관리형 키만큼 복호화 권한을 분리하기 어렵다. 기존 사용자·역할의 SSM 해당 파라미터·상위 경로·이력 읽기 및 DynamoDB 테이블·백업 읽기 권한을 별도로 확인한다. [SSM 복호화 제한](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-restrict-decryption.html), [DynamoDB 기본 암호화](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/encryption.tutorial.html)
- CLI 사용자는 운영 스택 변경 세트를 만들고 실행할 수 있다. 수정한 Lambda 코드를 전용 실행 역할로 실행하면 NH 비밀을 간접적으로 사용할 수 있으므로 이 배포 권한은 민감하다. 검토된 패키지·변경 세트만 사용하고 권한 보유자를 제한한다. [CloudFormation 서비스 역할 안내](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html)

## 배포 및 검증 순서

1. 관리자의 bootstrap 스택이 **CREATE_COMPLETE**인지 확인하고 출력의 `PrivateApiId`, `RuntimeRoleArn`, `CloudFormationRoleArn`, `ArtifactBucketName`과 실제 권한을 확인한다. 오류가 있으면 임의로 삭제하거나 재생성하지 않고 원인을 점검한다.
2. 연마 전용 Google OAuth 클라이언트 `343043233969-95mv3utlrbafcj1673dpl33ont9mh2j9.apps.googleusercontent.com`과 허용 출처 `https://www.hpmplab.com`을 사용한다. `all-begins` 프로젝트는 테스트 상태이고 `madrock711@gmail.com`이 테스트 사용자로 등록돼 있다. 기존 게임용 클라이언트를 변경하지 않았다. 실제 로그인은 아직 검증되지 않았다.
3. 본인 계정의 Google ID 토큰을 신뢰할 수 있는 방식으로 서명·issuer·audience·만료·이메일 검증 상태까지 확인한 뒤 안정적인 `sub`를 얻는다. 이메일 자체를 `sub`로 쓰거나 검증하지 않은 값으로 추측하지 않는다. 토큰 원문은 공개·기록하지 않는다.
4. NH 키를 안전하게 전용 SSM 파라미터에 저장하고, 기존 PC에서 동일 키로 독립 발급하는 경로를 중지·전환한다. 이전 발급 시점과 만료를 확인한 뒤 조건부 토큰 상태를 초기화한다. 실패 후 결과가 불명확할 때는 자동 재발급하지 않는다. [NH 공식 토큰 안내](https://www.nhplug.com/apiservice)
5. 검토한 Lambda 코드와 의존성을 패키징해 bootstrap의 `yeonma-nh-artifacts-514670561185-us-east-1` 버킷 `deploy/` 아래에 저장한다. 정확한 객체 버전 ID를 지정하고 패키지에 자격증명이 없는지 확인한다. 운영 템플릿의 입력은 `GoogleClientId`, `OwnerGoogleSub`, `ApiId`, `RuntimeRoleArn`, `CodeBucket`, `CodeKey`, `CodeObjectVersion`이다. `OwnerGoogleSub`는 `NoEcho`로 설정돼 있지만 템플릿이나 로그에 임의로 기재하지 않는다.
6. `yeonma-nh-cfn` 역할을 지정해 운영 스택의 변경 세트를 만들고, 대상 API·함수·테이블·권한과 보존 정책을 검토한 뒤 실행한다. 운영 API는 지정된 ID 하나에만 연결한다. 부트스트랩 정책의 허용 범위와 CloudFormation의 실제 호출이 일치하는지는 현 계정에서 검증이 필요하다.
7. 본인 계정 성공과 다른 Google 계정·무토큰·만료·잘못된 토큰 거부를 실제로 확인한다. 거부 요청에서 SSM·NH 호출이 일어나지 않는지도 확인한다. 금액·수량 전환, 조회 시각·30초 갱신, 모바일 UI와 NH 원본 값을 대조한다. 모의 테스트만으로 실서비스 성공을 주장하지 않는다.

## 비용과 운영

고객 관리형 KMS 키를 만들지 않아 별도의 월 키 보관료는 없지만, API Gateway·Lambda·DynamoDB·S3·KMS 요청과 로그는 사용량 및 계정의 다른 사용량에 따라 과금될 수 있다. 버킷은 버전 관리가 켜져 있고 삭제 시 보존되며 DynamoDB 테이블도 운영 스택 삭제 시 보존된다. 비용은 자동으로 중단되지 않는다. 운영 API의 초당 0.2건·순간 4건 제한과 Lambda 예약 동시성 1은 요청량을 줄이기 위한 값이지 요금의 절대 상한이 아니다. [SSM 요금](https://aws.amazon.com/systems-manager/pricing/), [Lambda 요금](https://aws.amazon.com/lambda/pricing/), [API Gateway 요금](https://aws.amazon.com/api-gateway/pricing/)
