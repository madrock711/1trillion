# 개인 NH 수급 API

이 코드는 AWS HTTP API Gateway의 JWT authorizer 뒤에서만 사용한다. 아직 배포되거나 실 서비스로 검증된 구현이 아니다. 주문 API는 호출하지 않는다.

**안전 조치: 실제 NH 자격증명으로 배포·호출하지 않는다.** [NH 공식 안내](https://www.nhplug.com/apiservice)는 토큰 유효기간이 24시간이며 만료 전에 재발급받지 않도록 주의할 것을 안내한다. SDK 메모리 캐시만 사용하면 Lambda 콜드 스타트마다 재발급해 이 안내에 어긋날 수 있다. 코드의 `TOKEN_CACHE_READY`는 고정 `False`로, 개인 시세 API가 실제로 호출되지 않게 차단한다. 환경변수로 해제할 수 없다. 안전한 공유 토큰 캐시 및 발급 조정, 장애 복구, 기존 PC 프로세스와의 동시 사용 방지에 대한 구현과 실제 검증이 선행되어야 한다. Lambda 예약 동시성 1만으로는 환경 교체나 PC 서버와의 중복을 막을 수 없다.

배포 전 `python server/nh_private/deployment_guard.py`를 실행한다. 현재는 항상 실패하도록 되어 있으며 배포 자동화에 아직 연결되지 않았다. 안전한 구현과 검증을 마친 뒤 검증 조건을 새로 설계해야 한다.

## 필수 보안 조건

- HTTP API payload format 2.0, `GET /api/private/nh/flow`에 Google OIDC issuer `https://accounts.google.com`과 Google OAuth 웹 클라이언트 ID를 audience로 지정한 JWT authorizer를 반드시 설정한다. Lambda는 **JWT 서명을 직접 검증하지 않으며**, 게이트웨이가 검증해 전달한 claims를 신뢰한다. 인증되지 않은 Lambda Function URL, 공개 invoke 권한, 검증 없는 다른 경로를 만들면 안 된다. 권한이 있는 IAM 주체가 Lambda를 직접 호출할 수 있으므로 invoke 권한도 최소화한다.
- Lambda는 authorizer가 검증한 `sub`, `email`, `email_verified`, `iss`, `aud`를 추가 검사한다. `OWNER_GOOGLE_SUB`은 실제 소유자의 Google 계정에서 검증된 ID 토큰으로 확인한 불변 식별자여야 한다. 프런트에서 보낸 이메일 문자열은 신뢰하지 않는다.
- `OPTIONS /api/private/nh/flow`만 사전 요청에 한해 무인증으로 허용한다. CORS는 `https://www.hpmplab.com` 한 곳만 허용하며 인증을 대체하지 않는다. Lambda 응답은 모두 no-store이고 API Gateway/CDN에도 캐시를 설정하지 않는다.
- `SSM_PARAMETER_NAME`이 가리키는 표준 SecureString에 `{"key":"...","secret":"..."}`을 별도 안전한 경로로 보관한다. 기본 AWS 관리형 `aws/ssm` 키를 사용하며 값은 Git, 브라우저, 배포 로그, 명령행 인자에 넣지 않는다. Lambda 역할에는 해당 파라미터에 대한 `ssm:GetParameter`만 허용한다. 이 기본 키는 계정 내 IAM 주체의 복호화 통제를 고객관리형 키처럼 세분화하지 못한다. 파라미터 및 상위 경로에 대한 모든 읽기·이력 권한을 면밀히 제한해야 한다. 기존 Windows DPAPI 비밀은 클라우드에서 복호화할 수 없다.
- `GOOGLE_CLIENT_ID`, `OWNER_GOOGLE_SUB`, `OWNER_EMAIL`, `SSM_PARAMETER_NAME`, `ALLOWED_ORIGIN` 환경변수를 설정한다. 마지막 값은 `https://www.hpmplab.com`이어야 한다. 개인 계정의 `sub`를 추측하거나 인터넷에 노출된 검증되지 않은 응답으로 설정하지 않는다.
- API Gateway 액세스 로그에 Authorization 헤더나 응답 본문을 기록하지 않는다. Lambda 예외는 일반 오류로 반환하며 공급자 원문과 시세, 비밀을 로깅하지 않는다. 운영 환경에서 SDK와 API Gateway의 실제 로깅 설정도 별도로 검증해야 한다.
- 검증 전에는 NH SDK의 프로세스 메모리 캐시만으로 배포하지 않는다. 공유 캐시 설계에는 제한된 IAM 권한, 만료 판정, 발급 잠금, 발급 후 저장 실패·락 만료 등 장애 처리, 키 갱신, 기존 PC에서 발급한 토큰과의 조정 및 비밀 미노출 테스트가 필요하다. 발급 성공과 캐시 기록 사이의 실패가 중복 발급을 초래할 수 있으므로 단순한 저장만으로 안전을 보장할 수 없다. 서버의 30초 시세 캐시는 실행 환경별로만 적용된다. 동시 호출 제한 및 비용·API 사용량도 설정한다.
- 확인한 SDK 0.4.1은 토큰 발급 요청의 네트워크 예외 시 재시도하고, 시세 요청의 토큰 무효 응답 시 강제 재발급한다. 공유 저장소를 붙이는 것만으로는 발급을 통제할 수 없다. 모든 발급 경로와 재시도를 통제하고 검증해야 한다.
- 설계 후보는 조건부 쓰기가 가능한 영속 저장소에 `발급 중`, `유효`, `확인 필요` 상태와 토큰을 함께 관리하는 것이다. 발급 응답이 불명이거나 발급 후 저장 전에 장애가 나면 잠금 만료만으로 자동 재발급하지 않고 `확인 필요` 상태를 유지해야 한다. 공급자가 중복 방지 키나 기존 발급 확인 기능을 지원하는지는 확인되지 않았으므로 외부 발급과 저장을 완전 원자적으로 처리한다고 가정하지 않는다. 로컬 서버도 같은 토큰 관리 체계를 사용하지 않으면 상호 충돌을 막을 수 없다.

## 공유 토큰 관리 실험 코드

`token_store.py`는 DynamoDB의 강한 일관성 읽기 및 조건부 갱신으로 발급 경합을 제어한다. 첫 상태가 없으면 발급을 막으며, 발급 중 프로세스가 중단되거나 발급 결과를 알 수 없으면 `ISSUING` 또는 `UNCERTAIN`에 머문다. 시간 경과만으로 이 상태를 자동 해제하지 않는다. 성공 응답 시간과 요청 시작 시간을 분리해 사용 중단 시점과 다음 발급 허용 시점 사이에 여유 구간을 둔다.

고정 월 키 요금을 피하기 위해 토큰은 애플리케이션 수준에서 별도로 암호화하지 않는다. DynamoDB는 기본 AWS 소유 키로 저장 시 암호화하고 전송에는 HTTPS를 사용하지만, **테이블에서 항목을 읽을 수 있는 IAM 주체는 토큰을 평문으로 볼 수 있다.** Lambda 역할과 운영자의 DynamoDB 읽기·조회·백업 권한을 최소화하고 로그에 값을 남기지 않아야 한다. 기본 AWS 소유 키에는 별도 키 요금이 없지만 다른 AWS 요청과 사용량에 따른 비용은 발생할 수 있다. [DynamoDB 기본 암호화](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/encryption.tutorial.html), [SSM 기본 키 권한](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-restrict-decryption.html).

실제 통합 전 필수: SDK의 자동 재발급·네트워크 재시도 경로를 거치지 않아야 한다. `nh_transport.py`에 단일 요청 발급기와 시세 조회기의 실험 구현을 작성하고 `flow_service.py`를 통해 공유 토큰 관리자와 연결할 수 있게 했다. 인증된 핸들러를 포함한 전체 연결은 가짜 HTTP·DynamoDB를 주입한 로컬 테스트에서만 검증했다. 운영 핸들러는 기본 차단 상태다. 발급기는 NH 공식 OpenAPI 명세 및 동작을 확인한 SDK와 같이 인증 매개변수를 HTTPS URL의 쿼리로 전달한다. 따라서 URL이나 원본 HTTP 예외를 로그·추적·모니터링에 기록하지 않아야 한다. 전용 전송기의 실제 NH 호출은 아직 검증하지 않았다. 401·타임아웃·리디렉션에서도 자동 재발급이나 재시도를 하지 않는다. 로컬 서버를 포함해 동일 NH 키로 독립 발급하는 모든 경로를 중단·전환하고, 기존 토큰의 상태와 마지막 발급 시각을 근거 있게 확인해야 한다. 정상 최초 상태를 만드는 관리자 절차도 아직 없다. DynamoDB 레코드는 자격증명의 HMAC 식별자와 연결돼 키 교체 시 과거 토큰을 잘못 재사용하지 않도록 한다. 안정적이고 신뢰할 수 있는 서버 시계가 필요하며 시계의 큰 전진을 감지하지 못하면 발급 안전시점을 보장할 수 없다.

DynamoDB 테이블과 최소한의 읽기·조건부 쓰기, 장애 복구 권한 분리가 추가로 필요하고 사용량에 따라 비용이 발생할 수 있다. 현재 테스트는 가짜 DynamoDB를 이용한 로컬 단위 테스트일 뿐, AWS 조건식·기본 저장 암호화 설정·NH 응답을 실환경에서 검증한 결과가 아니다. 배포 차단은 유지한다.

현재 실험 모듈은 SDK를 호출하지 않는다. `runtime_service.py`는 주입된 AWS 클라이언트로 SSM 비밀과 공유 토큰 관리자·전송기를 조립하는 준비 코드다. `SSM_PARAMETER_NAME`, `TOKEN_TABLE_NAME`이 필요하며 조립 시 NH에는 요청하지 않는다. 자격증명이 바뀌면 HMAC 기반 토큰 레코드 식별자도 바뀌고, 새 레코드가 없으므로 발급을 차단한다. 핸들러의 지연 초기화 경로는 작성했지만 고정된 배포 차단 때문에 실제 요청에서는 실행되지 않는다. `boto3`는 Lambda Python 런타임에 포함된 것을 사용하거나 호환 버전과 함께 패키징해야 한다. 로컬 테스트: `python -m unittest discover -s server/nh_private -p 'test_*.py'`.
