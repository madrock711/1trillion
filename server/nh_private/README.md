# 개인 NH 수급 API

연마의 본인 계정 전용 온라인 수급 서비스다. 주문·잔고·계좌 API는 호출하지 않는다. Google 로그인과 보안 쿠키 세션은 [SESSION_AUTH.md](SESSION_AUTH.md)를 따른다.

## 운영 경로

1. `POST /api/private/nh/session/login`: API Gateway가 Google JWT를 검증하고 Lambda가 지정된 sub·이메일·email_verified를 다시 확인한다.
2. `GET /api/private/nh/session/state`: 7일 보안 쿠키 세션을 서버에서 확인한다.
3. `GET /api/private/nh/session/flow`: 유효한 소유자 세션에만 NH 금액·수량 시계열을 반환한다. 비로그인은 401, 잘못된 Origin/계정은 거부한다.
4. `POST /api/private/nh/session/logout`: 정확한 Origin과 세션별 CSRF를 확인한 뒤 서버에서 폐기한다.

브라우저는 www.hpmplab.com의 같은 도메인 HTTPS 프록시를 사용한다. NH 키·시크릿·토큰은 프런트엔드나 응답에 포함하지 않는다. 모든 응답은 private/no-store다.

## NH 공유 토큰

- 자격증명은 `/yeonma/private/nhplug` 표준 SecureString에 보관한다. Lambda만 해당 파라미터를 읽는다.
- 자격증명 HMAC별 DynamoDB 레코드가 없으면 발급하지 않는다. 사용자 승인 뒤 `scripts/initialize_nh_online.py --initialize-approved-once`로 최초 READY 상태만 조건부 생성한다. 이미 있는 상태를 덮어쓰지 않는다.
- 토큰 발급은 Lambda의 `SharedTokenManager`만 담당한다. READY/기한이 지난 VALID → 조건부 ISSUING → VALID 순서이며, 경합에서 실패한 요청은 발급하지 않는다.
- 발급 응답이 불명확하거나 저장 전에 실패하면 ISSUING/UNCERTAIN에 머문다. 시간 경과나 일반 조회 오류만으로 이를 리셋하지 않는다.
- 유효 토큰은 Lambda 교체·재시작 후에도 재사용한다. 정상 만료보다 120초 앞서 사용을 멈추고, 마지막 가능 만료보다 120초 지난 뒤 다음 발급을 허용한다. 이 경계 구간은 일시 조회 불가일 수 있다.
- NH HTTP 전송은 6초 제한이며 자동 재시도·리디렉션·401 재발급을 하지 않는다. 두 시계열은 서버에서 30초 캐시한다.
- 발급 쿼리에는 NH 공식 명세에 따라 키가 포함된다. URL·공급자 원문 예외·Authorization·SSM 값·토큰을 로깅하지 않는다.
- DynamoDB는 저장 시 암호화되지만 항목 읽기 권한자는 토큰을 볼 수 있다. 기본 AWS 소유 키를 사용해 고객 관리형 키의 고정 월 요금을 추가하지 않았으며, 서비스 사용량 요금은 별도다.
- PC에는 온라인 전환 표시를 남긴다. 기존 임시 서버는 표시가 있으면 시작하지 않는다. 같은 앱키로 예전 시세 확인 스크립트를 따로 실행해 발급하지 않는다.

## 시계열 의미

NH 통합 시장의 투자자별 금액·수량 원본값이다. 현재 반환 자료에는 검증된 거래일·단위가 없어 이를 확정하지 않는다. 프런트는 당일 한국 정규장 시각에만 거래일을 제한적으로 연결하며, 10분 이상 어긋난 수급은 가격에 붙이지 않는다. 단위는 미확인 원본값으로 표시하고 가격과 별도 축을 사용한다.

## 검증과 장애 대응

`python server/nh_private/deployment_guard.py`는 외부 호출 없이 공유 상태·경합·응답 손실·저장 실패·재발급 금지 테스트를 수행한다. 이것은 실제 NH 가용성을 증명하지 않는다.

`qa_live_browser_session.py --run-nh-backend`는 실제 서버의 소유자 테스트 세션으로 금액·수량 응답과 30초 캐시를 확인한다. `--run-nh-chart`는 실제 페이지의 분봉에서 두 모드를 바꿔 렌더링을 확인한다. 테스트 세션은 finally에서 폐기한다.

현재 실제 검증 결과는 작업일지와 실행 출력에 구분해 남긴다. 토큰은 출력하지 않고 상태·버전·사용/다음발급 경계만 ProjectionExpression으로 점검한다. UNCERTAIN/ISSUING이 발생하면 먼저 마지막 발급 근거와 원천 장애를 확인하며, 무조건 삭제·재발급하지 않는다.
