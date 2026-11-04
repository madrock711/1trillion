# 연마 전용 AWS 권한 설정 안내

이 문서는 AWS 관리자 계정으로 **직접** 진행하는 1회 설정이다. 템플릿을 업로드하면 연마 전용 리소스와 권한이 만들어진다. 아직 이 템플릿을 실제 AWS에 적용하거나 서비스 권한을 실환경에서 검증하지 않았다. 작업 전에 계정과 리전을 확인하고, 검토 화면에서 내용이 예상과 다르면 생성하지 않는다.

## 만들 항목과 비용

- AWS 계정 `514670561185`, 리전 **미국 동부(버지니아 북부), us-east-1**에 `yeonma-nh-bootstrap` 스택을 만든다.
- `yeonma-nh-runtime`은 Lambda가 NH 키 한 개와 전용 토큰 테이블에 접근하도록 한다. `yeonma-nh-cfn`은 운영 스택이 지정된 함수, 테이블, 로그와 전용 HTTP API만 관리하도록 한다. `codex-amplify-manager` 사용자에게는 전용 운영 스택의 변경 세트와 전용 역할 전달, 전용 파일 경로 등을 허용하는 고객 관리형 IAM 정책 `yeonma-nh-deployment`를 연결한다. 기존 권한을 지우지는 않는다. 사용자의 관리형 정책 연결 한도에 도달했으면 생성이 실패할 수 있다.
- 전용 HTTP API 하나와 `yeonma-nh-artifacts-514670561185-us-east-1` 버킷 하나를 만든다. 버킷은 공개 차단·서버 측 암호화·버전 관리가 적용되며 배포 파일은 `deploy/` 아래에 둔다. 기존 버킷은 변경하지 않는다. API에는 이 설정만으로 시세 데이터나 Lambda 경로가 연결되지 않는다.
- 별도 월 고정 요금이 붙는 고객 관리형 KMS 키는 만들지 않는다. NH 앱키는 이후 SSM SecureString의 AWS 관리형 `aws/ssm` 키로 저장하고, 토큰 테이블은 DynamoDB의 기본 저장 암호화를 사용한다. AWS 관리형 키 저장에 대한 별도 요금은 없지만, KMS·API Gateway·S3 요청 및 이후 생성할 Lambda·DynamoDB·로그 등은 사용량과 무료 제공량에 따라 비용이 생길 수 있다. [KMS 요금 안내](https://aws.amazon.com/kms/pricing/)
- 버킷·API는 실수로 스택을 지워도 보존되도록 설정했다. 따라서 **스택을 삭제해도 버킷 등의 비용이 자동으로 끝나지 않을 수 있다.** 삭제는 데이터와 다른 리소스의 의존 관계를 확인한 뒤 별도 처리한다.

## AWS 콘솔에서 직접 설정하기

1. Chrome에서 AWS 콘솔 오른쪽 위의 계정 번호가 `514670561185`인지, 리전이 `미국 동부(버지니아 북부)`인지 확인한다.
2. 콘솔 검색창에서 **CloudFormation**을 열고 **스택 생성 → 새 리소스 사용(표준)**을 선택한다.
3. **템플릿이 준비됨**과 **템플릿 파일 업로드**를 고른 다음 `D:\Projects\1trillion\server\nh_infra\iam-bootstrap.json` 파일을 선택한다. 업로드 단계의 검사 오류가 나타나면 진행하지 말고 오류를 알려준다.
4. 스택 이름에 정확히 `yeonma-nh-bootstrap`을 입력한다. 나머지 선택 사항은 변경하지 않고 다음으로 진행한다.
5. 검토 화면에서 위의 전용 S3 버킷·HTTP API와 IAM 역할 및 사용자 정책이 생성됨을 확인한다. 고객 관리형 KMS 키가 생성 항목에 없어야 한다. 표시된 IAM 확인란에서 **사용자 지정 이름을 가진 IAM 리소스를 생성할 수 있음을 확인**한다는 항목을 선택한 후 **제출/스택 생성**을 누른다.
6. 스택의 상태가 **CREATE_COMPLETE**가 될 때까지 기다린다. 실패하면 삭제·재시도하지 말고 상태와 이벤트의 오류 문구를 알려준다. 완료되면 채팅에 **‘설정 완료’**라고만 알려주면 된다. 키나 인증정보를 채팅에 붙여 넣지 않는다.

설정 완료 후 운영 스택의 변경 세트는 검토한 뒤 별도로 실행해야 한다. 이 bootstrap만으로 구글 로그인이나 NH 시세가 작동하는 것은 아니다. NH 앱키·시크릿 이전, Google 본인 계정 식별자 검증, 기존 PC 토큰과의 전환, 구글 본인/타인 인증 테스트와 실제 배포 검증이 남아 있다.

## 기존 bootstrap의 API 단계 태그 권한 보완

운영 스택에서 HTTP API 단계를 만들 때 전용 CloudFormation 역할에 태그 권한이 부족하다는 오류가 확인돼, `iam-bootstrap.json`에 전용 API의 단계 및 태그 경로로 제한한 권한을 추가했다. **이미 생성된 bootstrap 스택에는 파일 수정만으로 이 권한이 반영되지 않는다.** 아래 절차로 관리자가 기존 bootstrap 스택의 변경 세트를 직접 검토·적용해야 한다.

1. AWS 콘솔에서 계정 `514670561185`, 리전 `us-east-1`을 확인하고 CloudFormation → 스택 → `yeonma-nh-bootstrap`을 연다.
2. **업데이트 → 현재 템플릿 바꾸기 → 템플릿 파일 업로드**를 선택하고 `D:\Projects\1trillion\server\nh_infra\iam-bootstrap.json`의 수정본을 업로드한다. 기존 bootstrap을 새로 만들거나 삭제하지 않는다.
3. 나머지 설정을 유지하고 검토 화면에서 변경 사항을 확인한다. `yeonma-nh-cfn` 역할의 정책만 수정되어야 하며, 전용 API·S3 버킷·기존 역할의 교체나 삭제가 표시되면 적용하지 말고 알려준다.
4. IAM 변경 확인란을 선택하고 업데이트를 제출한다. `UPDATE_COMPLETE`를 확인한 뒤 상태만 알려준다. 실패하면 이벤트의 오류를 보존하고 임의로 스택을 삭제하거나 반복하지 않는다.

AWS 공식 서비스 권한표는 태그 API 작업을 HTTP 동사 권한으로 매핑하지만, 동일한 단계 생성 오류를 `apigateway:TagResource`를 stages 컬렉션에 명시해 해결했다는 [AWS re:Post 실험 보고](https://repost.aws/questions/QUMw9zvPe8RQ6SiE7YDEKmRQ/http-api-createstage-denies-tagresource-but-iam-access-analyzer-says-the-action-is-invalid)가 있다. 이 수정은 해당 명시적 권한과 전용 API의 URL 인코딩 태그 경로용 HTTP 동사 권한을 함께 포함한다. AWS IAM Access Analyzer가 명시적 action을 `INVALID_ACTION`으로 경고할 수 있으며, **이 계정에서 템플릿 업데이트와 실제 단계 생성이 성공하는지는 아직 확인되지 않았다.** 경고나 실패가 나오면 그대로 알려준다.

별개로 운영 스택의 실패·롤백 이벤트와 남은 자원 상태는 보존·확인해야 한다. 화면의 `DELETE_SKIPPED`만으로 테이블이 실제 남아 있다고 단정하지 않고, 실제 DynamoDB 조회 결과를 확인한 후에만 복구 방법을 결정한다.

## 권한 범위와 한계

- CLI 사용자의 CloudFormation 권한은 `yeonma-nh-private` 스택의 변경 세트 생성·조회·실행·삭제 등으로 제한한다. 생성 시 전용 CloudFormation 서비스 역할을 지정해야 한다. CLI는 전용 역할 하나만 CloudFormation에 전달할 수 있다. CloudFormation 공식 [서비스 역할 안내](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html)처럼 스택에 연결된 서비스 역할은 이후 스택 변경 권한자에게도 사용된다.
- 전용 API ID를 bootstrap 단계에서 먼저 만들기 때문에 운영 서비스 역할의 API Gateway 변경 권한은 **그 API와 하위 경로**에 한정한다. API Gateway의 `/apis/*` 전체에 대한 변경 권한은 부여하지 않는다. 전용 API 자체도 변경·삭제할 수 있으므로 운영 템플릿 변경은 검토가 필요하다.
- `codex-amplify-manager`는 배포 코드를 수정할 수 있고, 해당 코드가 실행 역할의 권한으로 NH 비밀에 접근할 수 있다. 따라서 직접 `ssm:GetParameter --with-decryption` 권한을 막더라도 **배포 권한은 사실상 NH 비밀을 간접 사용할 수 있는 민감한 권한**이다. 배포할 코드와 변경 세트, 사용자 계정을 신뢰할 수 있을 때만 적용한다.
- NH 키에 사용하는 AWS 관리형 `aws/ssm` 키는 고객 관리형 키보다 계정 내 접근을 세밀하게 구분하기 어렵다. 기존 IAM 사용자·역할에 해당 SSM 파라미터 또는 상위 경로의 읽기 권한이 있으면 복호화해 볼 수 있으므로 별도로 점검해야 한다. [AWS의 SSM 복호화 제한 안내](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-restrict-decryption.html)
- DynamoDB는 디스크 저장 시 암호화하지만, 토큰을 애플리케이션에서 추가 암호화하지 않는다. 따라서 테이블의 항목 읽기 권한이 있는 주체는 접근토큰 값을 읽을 수 있다. 이 bootstrap은 Lambda와 CLI에 전용 테이블 권한을 주며, **기존 다른 IAM 권한을 제거하거나 점검하지 않는다**. DynamoDB 전체 읽기나 관리자 권한이 이미 있는 다른 주체도 확인해야 한다.
- 최초 토큰 상태를 안전하게 초기화할 수 있도록 CLI에 전용 DynamoDB 행을 수정할 수 있는 권한을 둔다. 행을 임의로 수정하면 중복 토큰 발급을 초래할 수 있으므로 검증된 절차 외에 수정하지 않는다. 클라우드에 저장될 NH 자격증명은 이후 별도의 안전한 경로로 입력하며 저장소·명령줄·채팅에 넣지 않는다.
- IAM 정책은 고정 이름과 리전에 제한하지만, 실제 CloudFormation 동작·권한 경계·조직 정책에 따라 추가 권한이 필요하거나 일부가 실패할 수 있다. AWS의 템플릿 사전 검증은 기존 CLI 사용자에게 `cloudformation:ValidateTemplate` 권한이 없어 실행하지 못했다. 오류가 나면 범위를 확인한 뒤 필요한 권한만 수정해야 한다.
