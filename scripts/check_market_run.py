"""일별 실행 증거 검사. 미완료(exit 2)는 종료 허가가 아니라 작업 계속 지시다."""
import argparse
import datetime as dt
import json
from pathlib import Path

STAGES = ("research", "writing", "image", "validation", "finalQuery", "push", "deploy", "live")
ALIASES = {"finalQuery": "finalQuote", "deploy": "deployment"}


def inspect(root, date):
    path = root / "research" / "evidence" / date / "run-status.json"
    if not path.exists():
        return ["run-status.json 없음: 실제 시작 시각을 기록하고 조사 시작"]
    state = json.loads(path.read_text(encoding="utf-8-sig"))
    problems = []
    stages = state.get("stages", {})
    for stage in STAGES:
        value = stages.get(stage, stages.get(ALIASES.get(stage)))
        try:
            stamp = dt.datetime.fromisoformat(value)
            if stamp.utcoffset() is None or stamp.astimezone(dt.timezone(dt.timedelta(hours=9))).date().isoformat() != date:
                raise ValueError()
        except (TypeError, ValueError):
            problems.append(f"{stage}: 완료 시각 없음")
    for name in (f"reports/{date}.md", f"articles/market-{date}.html"):
        if not (root / name).is_file():
            problems.append(f"산출물 없음: {name}")
    if state.get("status") != "complete":
        problems.append(f"실행 상태: {state.get('status', 'missing')}")
    if not state.get("finalCommit"):
        problems.append("최종 커밋 없음")
    if not state.get("deploymentJob"):
        problems.append("최종 배포 작업 ID 없음")
    live_path = path.with_name("live-check.json")
    if not live_path.exists():
        problems.append("최종 라이브 증거 없음")
    else:
        rows = json.loads(live_path.read_text(encoding="utf-8-sig"))
        if not isinstance(rows, list) or not rows or any(
            row.get("status") != 200 or not row.get("sha256") or not row.get("checkedAt")
            for row in rows
        ):
            problems.append("라이브 증거 형식/HTTP/hash/시각 미충족")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat())
    args = parser.parse_args()
    dt.date.fromisoformat(args.date)
    try:
        problems = inspect(Path(__file__).resolve().parents[1], args.date)
    except (ValueError, OSError, AttributeError) as error:
        problems = [f"상태/증거 읽기 실패: {error}"]
    print(json.dumps({"decision": "continue" if problems else "evidence_present",
                      "remaining": problems,
                      "note": "이 검사는 로컬 증거 점검이다. 완료 보고에는 원격 main·최종 Amplify commit·실제 URL 재대조가 별도로 필요하다."}, ensure_ascii=False, indent=2))
    return 2 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
