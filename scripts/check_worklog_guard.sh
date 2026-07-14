#!/bin/sh
set -eu

worklog='docs/현재작업중.md'
requires_worklog=0
worklog_staged=0

while IFS= read -r path; do
  [ -n "$path" ] || continue

  if [ "$path" = "$worklog" ]; then
    worklog_staged=1
    continue
  fi

  case "$path" in
    docs/screenshot/*)
      ;;
    *.html|*.css|*.js|*.json|*.yml|*.yaml|*.xml|*.sh|.githooks/*)
      requires_worklog=1
      ;;
  esac
done <<EOF
$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR)
EOF

if [ "$requires_worklog" -eq 1 ] && [ "$worklog_staged" -ne 1 ]; then
  echo "오류: 코드/설정 변경과 함께 $worklog 를 갱신해 스테이징해야 합니다." >&2
  exit 1
fi

exit 0
