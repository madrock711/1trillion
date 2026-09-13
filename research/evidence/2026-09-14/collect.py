import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).parent
URLS = {
    "KOSPI": "https://m.stock.naver.com/api/index/KOSPI/price?pageSize=10&page=1",
    "KOSDAQ": "https://m.stock.naver.com/api/index/KOSDAQ/price?pageSize=10&page=1",
    "KOSPI-basic": "https://m.stock.naver.com/api/index/KOSPI/basic",
    "KOSPI-integration": "https://m.stock.naver.com/api/index/KOSPI/integration",
    "FX": "https://api.stock.naver.com/marketindex/exchange/FX_USDKRW",
    "NXT": "https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660",
}
for code in ("122630", "005930", "000660"):
    URLS[code] = f"https://m.stock.naver.com/api/stock/{code}/price?pageSize=10&page=1"
for symbol in ("QQQ", "TQQQ", "SOXX", "SMH", "NVDA", "AMD", "MU", "AVGO", "NQ=F", "ES=F", "BZ=F", "CL=F"):
    URLS[f"yahoo-{symbol.replace('=', '')}"] = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d&includePrePost=true"

def fetch(item):
    key, url = item
    try:
        raw = urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=25
        ).read()
        record = {
            "url": url,
            "fetchedAt": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds"),
            "rawHash": hashlib.sha256(raw).hexdigest(),
            "data": json.loads(raw),
        }
        (ROOT / f"{key}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        return key, "OK"
    except Exception as exc:
        return key, repr(exc)

if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        for result in pool.map(fetch, URLS.items()):
            print(result)
