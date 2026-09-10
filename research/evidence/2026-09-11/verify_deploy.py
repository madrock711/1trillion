"""동일 커밋의 양 도메인 자산 바이트와 실제 발행 시각 보존. 원장 덮어쓰기 금지."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.request

root = pathlib.Path(__file__).resolve().parents[3]
e = pathlib.Path(__file__).parent
seal = json.loads((e / "seal.json").read_text(encoding="utf-8"))
fid = seal["forecastId"]
forecast = json.loads((root / "research/evaluation/forecasts" / f"{fid}.json").read_text(encoding="utf-8"))
commit, job, pushed = sys.argv[1:4]

def check(pair):
    domain, path = pair
    url = domain + "/" + path + "?v=" + commit[:12]
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}), timeout=25).read()
    expected = subprocess.check_output(["git", "show", commit + ":" + path], cwd=root)
    return {"url": url, "status": 200, "matchesCommit": raw == expected, "sha256": hashlib.sha256(raw).hexdigest()}

with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    checks = list(pool.map(check, [(domain, path) for domain in ("https://www.hpmplab.com", "https://main.d2pg7r2qjjb9u9.amplifyapp.com") for path in seal["files"]]))
assert all(item["matchesCommit"] for item in checks), [item for item in checks if not item["matchesCommit"]]
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")

def dump(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

dump(e / "deployment-verification.json", {"commitSha": commit, "jobId": job, "verifiedAt": now, "checks": checks})
common = {"schemaVersion": 1, "forecastId": fid, "contentHash": forecast["contentHash"], "commitSha": commit}
dump(root / "research/evaluation/publications" / f"{fid}-pushed.json", dict(common, eventType="pushed", occurredAt=pushed))
dump(root / "research/evaluation/publications" / f"{fid}-deploy_verified.json", dict(common, eventType="deploy_verified", occurredAt=now, publicUrl="https://www.hpmplab.com/articles/market-2026-09-11.html", availabilityStatus="available"))
print(now, "verified", len(checks), "files against", commit)
