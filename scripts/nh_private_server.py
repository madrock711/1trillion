"""개인 PC에서만 NH 수급을 읽는 연마 미리보기. 주문 API는 호출하지 않는다."""
from __future__ import annotations

import argparse
import ctypes
import getpass
import http.server
import json
import os
import re
import secrets
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SECRET_FILE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Yeonma" / "nhplug.dpapi"
API_PATH = "/krfuture/quote/v1/tradingStatus"
FIELDS = ("bsop_hour", "timez12", "prsn_val", "frgn_val", "orgn_val")
SDK_FALLBACK = Path.home() / ".codex/visualizations/2026/11/02/01a19cc3-e002-7f20-bf61-3af994da44ab/nhplug-packages"


def dpapi_transform(payload: bytes, decrypt: bool = False) -> bytes:
    if os.name != "nt":
        raise RuntimeError("Windows 사용자 계정 암호화가 필요합니다.")

    class Blob(ctypes.Structure):
        _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload)
    source = Blob(len(payload), buffer)
    destination = Blob()
    crypt = ctypes.windll.crypt32
    kernel = ctypes.windll.kernel32
    crypt.CryptProtectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(Blob)]
    crypt.CryptProtectData.restype = ctypes.c_int
    crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.restype = ctypes.c_int
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        ok = crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(destination))
    else:
        ok = crypt.CryptProtectData(ctypes.byref(source), "Yeonma NH PLUG", None, None, None, 1, ctypes.byref(destination))
    if not ok:
        raise OSError("Windows 암호화 처리에 실패했습니다.")
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel.LocalFree(destination.pbData)


def setup_credentials() -> None:
    if SECRET_FILE.exists():
        raise RuntimeError("이미 보관된 인증정보가 있습니다. 삭제하거나 교체하지 않았습니다.")
    print("NH 앱키와 시크릿을 입력하세요. 입력값은 화면에 표시하지 않습니다.")
    app_key = getpass.getpass("앱키: ").strip()
    app_secret = getpass.getpass("시크릿: ").strip()
    if not app_key or not app_secret:
        raise ValueError("인증정보가 비어 있습니다.")
    encrypted = dpapi_transform(json.dumps({"key": app_key, "secret": app_secret}).encode("utf-8"))
    SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 실패 시 기존 값을 덮어쓰지 않는다. 복호화는 같은 Windows 계정에서만 가능하다.
    with SECRET_FILE.open("xb") as output:
        output.write(encrypted)
    print("인증정보를 현재 Windows 계정으로 암호화해 보관했습니다.")


def load_sdk():
    if not SECRET_FILE.is_file():
        raise RuntimeError("먼저 setup을 실행해 NH 인증정보를 등록하세요.")
    credentials = json.loads(dpapi_transform(SECRET_FILE.read_bytes(), decrypt=True))
    if not isinstance(credentials, dict) or not credentials.get("key") or not credentials.get("secret"):
        raise RuntimeError("저장된 인증정보의 형식이 올바르지 않습니다.")
    os.environ["NHPLUG_APP_KEY"] = credentials["key"]
    os.environ["NHPLUG_APP_SECRET"] = credentials["secret"]
    os.environ["NHPLUG_BASE_URL"] = "https://api.nhplug.com:8443"
    os.environ["NHPLUG_AUTH_URL"] = "https://api.nhplug.com:8443"
    os.environ["NHPLUG_TOKEN_CACHE"] = "0"
    os.environ["NHPLUG_ALLOW_HOSTS"] = ""
    if SDK_FALLBACK.is_dir():
        sys.path.insert(0, str(SDK_FALLBACK))
    try:
        from nhplug import call
    except ImportError as exc:
        raise RuntimeError("NH PLUG SDK를 찾지 못했습니다. 기존 시세 확인 환경을 확인하세요.") from exc
    return call


def safe_rows(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("Output_0"), list):
        raise ValueError("NH 수급 응답을 확인하지 못했습니다.")
    result = []
    for row in payload["Output_0"]:
        if not isinstance(row, dict):
            continue
        item = {key: row.get(key) for key in FIELDS}
        if any(not (isinstance(item[key], int) and not isinstance(item[key], bool)
                        or isinstance(item[key], str) and re.fullmatch(r"[+-]?\d{1,18}", item[key].strip()))
               for key in ("prsn_val", "frgn_val", "orgn_val")):
            continue
        if any(not isinstance(item[key], (str, int)) or isinstance(item[key], bool) or len(str(item[key])) > 24
               for key in ("bsop_hour", "timez12")):
            continue
        result.append(item)
    return result


class FlowReader:
    def __init__(self, call, ttl=30):
        self.call, self.ttl = call, ttl
        self.lock = threading.Lock()
        self.value, self.at = None, 0.0

    def get(self):
        with self.lock:
            if self.value is not None and time.monotonic() - self.at < self.ttl:
                return self.value
            series = {}
            for name, option in (("amount", "1"), ("quantity", "2")):
                payload = self.call(API_PATH, {"market_cd": "UNT", "mrkt_cls_code": "1", "cycle_cls_code": "4", "opt_cls_code": option, "cnt": "999"})
                series[name] = safe_rows(payload)
            self.value = {"source": "NH PLUG", "market": "UNT", "fetchedAt": datetime.now(timezone.utc).isoformat(), "tradeDate": None, "unitsVerified": False, **series}
            self.at = time.monotonic()
            return self.value


def make_handler(reader, session, port):
    allowed_host = f"127.0.0.1:{port}"
    origin = f"http://{allowed_host}"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)

        def log_message(self, *_args):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            super().end_headers()

        def is_authorized(self):
            cookies = dict(part.strip().split("=", 1) for part in self.headers.get("Cookie", "").split(";") if "=" in part)
            return (secrets.compare_digest(cookies.get("yeonma_private", ""), session)
                    and self.headers.get("Sec-Fetch-Site", "") in ("", "same-origin")
                    and self.headers.get("Origin", "") in ("", origin))

        def do_HEAD(self):
            self.send_error(405)

        def do_GET(self):
            if self.headers.get("Host") != allowed_host:
                self.send_error(403)
                return
            url = urllib.parse.urlsplit(self.path)
            if url.path == "/private-entry/" + session:
                self.send_response(303)
                self.send_header("Set-Cookie", f"yeonma_private={session}; HttpOnly; SameSite=Strict; Path=/")
                self.send_header("Location", "/articles/market.html?view=technical")
                self.end_headers()
                return
            if url.path == "/api/private/nh/flow":
                if not self.is_authorized():
                    self.send_error(403)
                    return
                try:
                    data = json.dumps(reader.get(), ensure_ascii=False).encode("utf-8")
                except Exception:
                    # 인증값이 포함될 수 있는 공급자 오류 전문은 반환·기록하지 않는다.
                    self.send_error(502, "NH request failed")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if url.path.startswith("/market-data/"):
                # 공급자 도메인과 경로를 고정하고 요청 헤더·쿠키를 전달하지 않는다.
                if not self.is_authorized() or ".." in urllib.parse.unquote(url.path) or "\\" in urllib.parse.unquote(url.path):
                    self.send_error(403)
                    return
                try:
                    target = "https://www.hpmplab.com" + url.path + ("?" + url.query if url.query else "")
                    request = urllib.request.Request(target, headers={"User-Agent": "Yeonma-private-preview/1.0"})
                    with urllib.request.urlopen(request, timeout=15) as response:
                        content = response.read(8_000_001)
                        if len(content) > 8_000_000:
                            raise ValueError("response too large")
                        content_type = response.headers.get("Content-Type", "application/octet-stream")
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                except Exception:
                    self.send_error(502, "Market data unavailable")
                return
            # 배포 대상 디렉터리와 확장자만 허용하고, 디렉터리 목록과 심볼릭 링크를 차단한다.
            decoded = urllib.parse.unquote(url.path)
            parts = PurePosixPath(decoded.lstrip("/")).parts
            if decoded == "/":
                parts = ("index.html",)
            if not parts or "\\" in decoded or any(part.startswith(".") for part in parts):
                self.send_error(404)
                return
            file = ROOT.joinpath(*parts)
            try:
                resolved = file.resolve(strict=True)
                allowed = (len(parts) == 1 and file.suffix in (".html", ".js", ".css", ".txt", ".xml")) or (
                    parts[0] in ("articles", "guides") and len(parts) == 2 and file.suffix == ".html") or (
                    parts[0] == "assets" and file.suffix in (".json", ".js", ".css", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico", ".woff2", ".mp3", ".wav")) or (
                    parts[0] == "charts" and len(parts) == 2 and file.suffix == ".png")
                if not allowed or not resolved.is_relative_to(ROOT) or not resolved.is_file() or any(ROOT.joinpath(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1)):
                    raise ValueError("not allowed")
            except (OSError, ValueError):
                self.send_error(404)
                return
            super().do_GET()

    return Handler


class PrivateServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def run_server():
    call = load_sdk()
    session = secrets.token_urlsafe(32)
    # 0은 OS가 다른 프로그램과 충돌하지 않는 빈 포트를 선택한다.
    server = PrivateServer(("127.0.0.1", 0), http.server.BaseHTTPRequestHandler, bind_and_activate=False)
    server.server_bind()
    port = server.server_address[1]
    server.RequestHandlerClass = make_handler(FlowReader(call), session, port)
    server.server_activate()
    print(f"개인 연마: http://127.0.0.1:{port}/private-entry/{session}", flush=True)
    print("이 주소는 현재 실행 중에만 사용하세요. 종료하려면 Ctrl+C를 누르세요.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="NH PLUG 개인 조회 (주문 기능 없음)")
    parser.add_argument("action", choices=("setup", "start"))
    action = parser.parse_args().action
    try:
        setup_credentials() if action == "setup" else run_server()
    except Exception as exc:
        print(str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "요청을 처리하지 못했습니다.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
