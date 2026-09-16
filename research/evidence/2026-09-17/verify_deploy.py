"""양 도메인의 발행 자산이 지정 커밋과 바이트 단위로 같은지 검증한다."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.request

root = pathlib.Path(__file__).resolve().parents[3]
evidence_dir = pathlib.Path(__file__).parent
seal = json.loads((evidence_dir / "seal.json").read_text(encoding="utf-8"))
forecast_id = seal["forecastId"]
forecast = json.loads(
    (root / "research/evaluation/forecasts" / f"{forecast_id}.json").read_text(encoding="utf-8")
)
commit, job_id = sys.argv[1:3]


def check(pair):
    domain, path = pair
    url = f"{domain}/{path}?v={commit[:12]}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
    )
    raw = urllib.request.urlopen(request, timeout=25).read()
    expected = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root)
    return {
        "url": url,
        "status": 200,
        "matchesCommit": raw == expected,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


pairs = [
    (domain, path)
    for domain in (
        "https://www.hpmplab.com",
        "https://main.d2pg7r2qjjb9u9.amplifyapp.com",
    )
    for path in [
        "articles/market-2026-09-17.html",
        "assets/data/market-dashboard-latest.json",
        "assets/data/market-dashboard-20260917-0813.json",
        "assets/images/articles/market-2026-09-17-fed-rate-memory-1200x630.webp",
        "charts/us_yield_spreads_90d_2026-09-17.png",
        "charts/us_yield_spreads_long_term_2026-09-17.png",
        "index.html", "articles/index.html", "articles/market.html", "sitemap.xml",
    ]
]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    checks = list(pool.map(check, pairs))

assert all(item["matchesCommit"] for item in checks), [
    item for item in checks if not item["matchesCommit"]
]
now = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=9))
).isoformat(timespec="seconds")


def dump_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


dump_new(
    evidence_dir / "deployment-verification.json",
    {"commitSha": commit, "jobId": job_id, "verifiedAt": now, "checks": checks},
)
dump_new(
    root / "research/evaluation/publications" / f"{forecast_id}-deploy_verified.json",
    {
        "schemaVersion": 1,
        "forecastId": forecast_id,
        "contentHash": forecast["contentHash"],
        "commitSha": commit,
        "eventType": "deploy_verified",
        "occurredAt": now,
        "publicUrl": "https://www.hpmplab.com/articles/market-2026-09-17.html",
        "availabilityStatus": "available",
    },
)
print(now, "verified", len(checks), "files against", commit)
