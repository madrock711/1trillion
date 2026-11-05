# 브라우저 로그인 세션

- Google 서명·issuer·audience는 기존 API Gateway JWT authorizer에서 확인한다. 로그인 전용 POST 경로에서 Lambda가 sub·이메일·email_verified를 다시 확인한 뒤 7일 세션을 발급한다.
- 실제 브라우저는 `https://www.hpmplab.com/api/private/nh/session/*`만 사용한다. Amplify HTTPS 프록시는 기존 시세/리다이렉트 규칙을 보존해 추가한다. 제3자 쿠키에 의존하지 않는다.
- 세션 쿠키는 `__Host-yeonma_session`, `Path=/`, `Secure`, `HttpOnly`, `SameSite=Lax`이며 Domain 속성을 쓰지 않는다. 세션 ID는 32바이트 암호학적 난수다. 서버에는 SHA-256 해시만 저장한다.
- 기존 DynamoDB 테이블의 `session#` 접두사 레코드로 분리한다. NH 토큰 레코드는 읽거나 수정하지 않는다. 기존 GetItem/UpdateItem 권한만 사용한다. 만료는 매 요청 서버에서 검사하며 물리 삭제 시각에 의존하지 않는다. 만료·폐기된 해시 레코드는 남을 수 있다.
- `/state`는 세션 해시·소유자 해시·폐기 여부·서버 만료를 강한 일관성으로 확인한다. `/logout`은 정확한 Origin과 세션별 CSRF 헤더를 요구하고 서버에서 폐기한 뒤 쿠키를 지운다. 로그아웃 응답 손실 시에도 폐기된 쿠키는 재사용할 수 없다.
- 쿠키·Google ID 토큰·NH 키는 코드, 브라우저 저장소, 로그에 남기지 않는다. 응답은 `private, no-store`; `Vary: Origin, Cookie`다. 로그인 확인과 세션 복원은 NH 런타임을 초기화하지 않는다.
- 기존 Google JWT GET 경로는 로컬 계정 확인 도구 호환성을 위해 유지한다. 수급은 최초 공유 상태 초기화와 사용자 승인 후 활성화하며, 상태가 없거나 발급 결과가 불명확하면 자동 발급을 차단한다.

검증:

- `python -m unittest discover -s server/nh_private -p 'test_*.py'`
- `node tests/test_private_flow_auth.js`
- `node tests/test_market_header_auth_browser.cjs`: 외부 API/Google은 모의 처리하되 Chrome의 실제 HttpOnly 쿠키 저장·재전송으로 새로고침/로그아웃/만료를 검사한다.
- `python scripts/qa_live_browser_session.py --run`: 명시적으로만 실행하는 운영 세션 경로 검증. 별도의 짧은 소유자 테스트 세션을 만들고 격리된 headless Chrome에 stdin으로만 전달하며 finally에서 서버 폐기한다. Google OAuth 완료나 NH 토큰 발급 검증으로 해석하지 않는다.
