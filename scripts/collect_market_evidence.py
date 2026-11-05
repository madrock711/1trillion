"""날짜 고정 코드 복사 없이 공개 시세를 독립 수집한다. 수집 성공은 발행 성공이 아니다."""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request

TZ = dt.timezone(dt.timedelta(hours=9))


def sources(final=False):
    urls = {
        "KOSPI": "https://m.stock.naver.com/api/index/KOSPI/price?pageSize=50&page=1",
        "KOSPI-basic": "https://m.stock.naver.com/api/index/KOSPI/basic",
        "KOSPI-integration": "https://m.stock.naver.com/api/index/KOSPI/integration",
        "KOSPI-history": "https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle",
        "FX": "https://api.stock.naver.com/marketindex/exchange/FX_USDKRW",
        "NXT": "https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660",
    }
    for code in ("122630", "005930", "000660"):
        urls[code] = f"https://m.stock.naver.com/api/stock/{code}/price?pageSize=10&page=1"
    symbols = ("NQ=F", "ES=F", "BZ=F", "CL=F")
    if not final:
        symbols += ("QQQ", "TQQQ", "SOXX", "SMH", "NVDA", "AMD", "MU", "AVGO")
    interval = "5m" if final else "1d"
    for symbol in symbols:
        urls["yahoo-" + symbol.replace("=", "")] = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval={interval}&includePrePost=true"
    return urls


def fetch_one(item, output):
    key, url = item
    record = {"url": url, "requestedAt": dt.datetime.now(TZ).isoformat()}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=25) as response:
            raw = response.read()
            record.update(httpStatus=response.status, rawHash=hashlib.sha256(raw).hexdigest(), data=json.loads(raw))
        if record["data"] is None or (isinstance(record["data"], dict) and record["data"].get("chart", {}).get("error")):
            raise ValueError("원천이 빈 값 또는 오류 응답을 반환함")
        record["status"] = "collected"
    except Exception as error:
        record.update(status="failed", error=f"{type(error).__name__}: {error}")
    record["fetchedAt"] = dt.datetime.now(TZ).isoformat()
    (output / f"{key}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return key, {k: record[k] for k in ("status", "url", "fetchedAt", "error") if k in record}


def collect(urls, output):
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        rows = dict(pool.map(lambda item: fetch_one(item, output), urls.items()))
    failed = [key for key, value in rows.items() if value["status"] != "collected"]
    manifest = {"finishedAt": dt.datetime.now(TZ).isoformat(), "sources": rows, "failed": failed,
                "next": "실패 출처는 승인된 재시도/대체출처로 보완. 성공 자료는 거래일·시각·시장상태 검증 후 취재 단계 진행."}
    (output / "collection-status.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", action="store_true", help="발행 직전 국내값과 선물 수집")
    args = parser.parse_args()
    now = dt.datetime.now(TZ)
    output = Path(__file__).resolve().parents[1] / "research/evidence" / now.date().isoformat() / "collections" / now.strftime("%H%M%S-%f")
    output.mkdir(parents=True, exist_ok=False)
    manifest = collect(sources(args.final), output)
    print(json.dumps({"output": str(output), "collected": len(manifest["sources"]) - len(manifest["failed"]), "failed": manifest["failed"]}, ensure_ascii=False))
    return 1 if manifest["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
