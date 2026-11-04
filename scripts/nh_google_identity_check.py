"""연마 소유자의 Google subject 확인. ID 토큰은 메모리에서만 검증한다.

사용자가 직접 Google 로그인 버튼과 계정 선택을 완료해야 한다. Google OAuth
클라이언트에 http://localhost 및 http://localhost:52710 출처가 필요하다.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import http.server
import json
import os
from pathlib import Path
import re
import secrets
import socket
import time
import urllib.request

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from nh_private_server import dpapi_transform

CLIENT_ID = "343043233969-95mv3utlrbafcj1673dpl33ont9mh2j9.apps.googleusercontent.com"
OWNER_EMAIL = "madrock711@gmail.com"
PORT = 52710
ORIGIN = f"http://localhost:{PORT}"
SUB_FILE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Yeonma" / "google-owner-sub.dpapi"
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
REMOTE_SESSION_URL = "https://dfx1foieoh.execute-api.us-east-1.amazonaws.com/api/private/nh/session"
MAX_TOKEN = 16384


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _decode(value: str) -> bytes:
    if not isinstance(value, str) or not value or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("invalid encoding")
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _fetch_keys() -> dict:
    # Fixed official endpoint; proxies and redirects are not used for this request.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(JWKS_URL, timeout=10) as response:
        raw = response.read(256_001)
        if response.status != 200 or len(raw) > 256_000:
            raise ValueError("key retrieval failed")
    result = json.loads(raw)
    if not isinstance(result, dict) or not isinstance(result.get("keys"), list):
        raise ValueError("invalid key set")
    return result


def verify_token(token: str, expected_nonce: str, *, keys: dict | None = None, now: int | None = None) -> str:
    """Google 서명과 계정·클라이언트·nonce를 검증한 subject만 반환한다."""
    if not isinstance(token, str) or len(token) > MAX_TOKEN or token.count(".") != 2:
        raise ValueError("invalid credential")
    encoded_header, encoded_claims, encoded_signature = token.split(".")
    header = json.loads(_decode(encoded_header))
    claims = json.loads(_decode(encoded_claims))
    if not isinstance(header, dict) or not isinstance(claims, dict):
        raise ValueError("invalid credential")
    kid = header.get("kid")
    if header.get("alg") != "RS256" or not isinstance(kid, str) or len(kid) > 200:
        raise ValueError("invalid credential")
    matches = [item for item in (keys or _fetch_keys()).get("keys", [])
               if isinstance(item, dict) and item.get("kid") == kid and item.get("kty") == "RSA"
               and item.get("alg", "RS256") == "RS256" and item.get("use", "sig") == "sig"]
    if len(matches) != 1:
        raise ValueError("invalid signing key")
    selected = matches[0]
    n, e = int.from_bytes(_decode(selected["n"]), "big"), int.from_bytes(_decode(selected["e"]), "big")
    if n.bit_length() < 2048 or e < 3 or not e & 1:
        raise ValueError("invalid signing key")
    public_key = rsa.RSAPublicNumbers(e, n).public_key()
    public_key.verify(_decode(encoded_signature), (encoded_header + "." + encoded_claims).encode("ascii"),
                      padding.PKCS1v15(), hashes.SHA256())
    current = int(time.time()) if now is None else now
    exp, iat = claims.get("exp"), claims.get("iat")
    if (claims.get("iss") not in ("https://accounts.google.com", "accounts.google.com")
            or claims.get("aud") != CLIENT_ID
            or (claims.get("azp") is not None and claims.get("azp") != CLIENT_ID)
            or not isinstance(exp, int) or isinstance(exp, bool) or exp <= current
            or not isinstance(iat, int) or isinstance(iat, bool) or iat > current + 60
            or claims.get("email_verified") is not True
            or not isinstance(claims.get("email"), str) or claims["email"].lower() != OWNER_EMAIL
            or not isinstance(claims.get("nonce"), str)
            or not hmac.compare_digest(claims["nonce"], expected_nonce)
            or not isinstance(claims.get("sub"), str)
            or not re.fullmatch(r"[0-9]{1,64}", claims["sub"])):
        raise ValueError("account or credential rejected")
    return claims["sub"]


def verify_remote_session(token: str, *, opener=None) -> bool:
    """고정 AWS 경로에만 인증 헤더를 보내고 성공 여부만 반환한다."""
    if not isinstance(token, str) or not token or len(token) > MAX_TOKEN:
        return False
    try:
        client = opener if opener is not None else urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect())
        request = urllib.request.Request(REMOTE_SESSION_URL, method="GET", headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "Cache-Control": "no-store",
        })
        with client.open(request, timeout=10) as response:
            raw = response.read(4097)
            if response.status != 200 or len(raw) > 4096:
                return False
        value = json.loads(raw)
        return (isinstance(value, dict) and set(value) == {"authenticated"}
                and value["authenticated"] is True)
    except Exception:
        # Provider exceptions may include private headers or response data.
        return False


def save_subject(sub: str) -> None:
    """기존 다른 subject는 덮어쓰지 않고 현재 Windows 계정으로 암호화한다."""
    if not re.fullmatch(r"[0-9]{1,64}", sub):
        raise ValueError("invalid subject")
    if SUB_FILE.exists():
        previous = dpapi_transform(SUB_FILE.read_bytes(), decrypt=True).decode("ascii")
        if not hmac.compare_digest(previous, sub):
            raise ValueError("existing subject differs")
        return
    encrypted = dpapi_transform(sub.encode("ascii"))
    SUB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SUB_FILE.open("xb") as stream:
        stream.write(encrypted)


def valid_request(headers, session: str, csrf: str, received_csrf: object) -> bool:
    cookie = headers.get("Cookie", "")
    values = [part.strip() for part in cookie.split(";") if part.strip().startswith("yeonma_identity=")]
    return (headers.get("Host") == f"localhost:{PORT}"
            and headers.get("Origin") == ORIGIN
            and headers.get("Sec-Fetch-Site") == "same-origin"
            and len(values) == 1 and hmac.compare_digest(values[0], "yeonma_identity=" + session)
            and isinstance(received_csrf, str) and hmac.compare_digest(received_csrf, csrf))


def _page(csrf: str, nonce: str) -> bytes:
    # The credential is sent in the request body only; it is never put in the DOM or URL.
    js_client, js_csrf, js_nonce = map(json.dumps, (CLIENT_ID, csrf, nonce))
    return ("""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>연마 계정 확인</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:36rem;margin:12vh auto;padding:0 1.5rem;color:#18231d}button{font:inherit;padding:.7rem 1rem}#status{margin-top:1rem}</style>
</head><body><h1>연마 계정 확인</h1><p>연마에서 사용할 본인 Google 계정을 확인합니다.</p>
<button id="load" type="button">구글 로그인 불러오기</button><div id="google"></div>
<button id="server-check" type="button" hidden>서버 로그인 확인</button><p id="status" role="status"></p>
<script>
const clientId=CLIENT_ID_VALUE, csrf=CSRF_VALUE, nonce=NONCE_VALUE;
const status=document.getElementById('status'), serverCheck=document.getElementById('server-check');
let verifiedCredential='';
document.getElementById('load').addEventListener('click',function(){
  this.disabled=true;const script=document.createElement('script');
  script.src='https://accounts.google.com/gsi/client';script.async=true;
  script.onerror=()=>{status.textContent='구글 로그인을 불러오지 못했습니다.';this.disabled=false};
  script.onload=()=>{google.accounts.id.initialize({client_id:clientId,nonce:nonce,auto_select:false,callback:async result=>{
    verifiedCredential='';serverCheck.hidden=true;
    try{const response=await fetch('/verify',{method:'POST',headers:{'Content-Type':'application/json'},
      credentials:'same-origin',cache:'no-store',body:JSON.stringify({csrf:csrf,credential:result.credential})});
      if(response.ok){verifiedCredential=result.credential;serverCheck.hidden=false;
        status.textContent='본인 계정을 확인했습니다. 서버 로그인도 확인해 주세요.'}
      else{status.textContent='계정을 확인하지 못했습니다.'}
    }catch(_){status.textContent='계정을 확인하지 못했습니다.'}
  }});google.accounts.id.renderButton(document.getElementById('google'),{theme:'outline',size:'large',locale:'ko'});this.hidden=true};
  document.head.appendChild(script)
});
serverCheck.addEventListener('click',async function(){
  if(!verifiedCredential)return;this.disabled=true;
  try{const response=await fetch('/server-verify',{method:'POST',headers:{'Content-Type':'application/json'},
    credentials:'same-origin',cache:'no-store',body:JSON.stringify({csrf:csrf,credential:verifiedCredential})});
    if(response.ok){verifiedCredential='';this.hidden=true;status.textContent='서버 로그인을 확인했습니다.'}
    else{status.textContent='서버 로그인을 확인하지 못했습니다.'}
  }catch(_){status.textContent='서버 로그인을 확인하지 못했습니다.'}finally{this.disabled=false}
});
</script></body></html>""".replace("CLIENT_ID_VALUE", js_client).replace("CSRF_VALUE", js_csrf)
            .replace("NONCE_VALUE", js_nonce)).encode("utf-8")


def make_handler(entry: str, session: str, csrf: str, nonce: str):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def _send(self, status, body=b"", *, content_type="text/plain; charset=utf-8", cookie=False, redirect=False):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer" if redirect else "no-referrer-when-downgrade")
            self.send_header("Cross-Origin-Opener-Policy", "same-origin-allow-popups")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            if redirect:
                self.send_header("Location", "/")
            if cookie:
                self.send_header("Set-Cookie", f"yeonma_identity={session}; HttpOnly; SameSite=Strict; Path=/")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.headers.get("Host") != f"localhost:{PORT}":
                return self._send(404)
            if self.path == "/private-entry/" + entry and not self.server.entry_used:
                self.server.entry_used = True
                return self._send(303, cookie=True, redirect=True)
            cookies = [part.strip() for part in self.headers.get("Cookie", "").split(";")
                       if part.strip().startswith("yeonma_identity=")]
            if (self.path != "/" or len(cookies) != 1
                    or not hmac.compare_digest(cookies[0], "yeonma_identity=" + session)):
                return self._send(404)
            self._send(200, _page(csrf, nonce), content_type="text/html; charset=utf-8")

        def do_POST(self):
            if (self.path not in ("/verify", "/server-verify")
                    or (self.path == "/verify" and self.server.verified)
                    or (self.path == "/server-verify" and (not self.server.verified or self.server.remote_verified))):
                return self._send(403)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if (length < 1 or length > MAX_TOKEN + 512
                        or self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json"):
                    return self._send(400)
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict) or not valid_request(self.headers, session, csrf, payload.get("csrf")):
                    return self._send(403)
                credential = payload.get("credential")
                if not isinstance(credential, str) or len(credential) > MAX_TOKEN:
                    return self._send(403)
                if self.path == "/verify":
                    sub = verify_token(credential, nonce)
                    save_subject(sub)
                    self.server.verified_token_hash = hashlib.sha256(credential.encode("ascii")).digest()
                    self.server.verified = True
                    return self._send(200, b"OK")
                fingerprint = hashlib.sha256(credential.encode("ascii")).digest()
                if not hmac.compare_digest(fingerprint, self.server.verified_token_hash):
                    return self._send(403)
                if not verify_remote_session(credential):
                    return self._send(403, b"verification failed")
                self.server.remote_verified = True
                self.server.verified_token_hash = None
                self._send(200, b"OK")
            except Exception:
                # Never include provider responses, token material, or claims in logs/responses.
                self._send(403, b"verification failed")
    return Handler


class IdentityServer(http.server.HTTPServer):
    allow_reuse_address = False
    entry_used = False
    verified = False
    remote_verified = False
    verified_token_hash = None

    def server_bind(self):
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main():
    if os.name != "nt":
        raise RuntimeError("Windows 사용자 계정 암호화가 필요합니다.")
    entry, session, csrf, nonce = (secrets.token_urlsafe(32) for _ in range(4))
    server = IdentityServer(("127.0.0.1", PORT), make_handler(entry, session, csrf, nonce))
    print(f"{ORIGIN}/private-entry/{entry}", flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
