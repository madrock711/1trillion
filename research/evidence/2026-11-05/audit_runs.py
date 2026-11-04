"""최근 예약 실행과 후속 대화의 관측값만 추출한다. 비밀값/전체 도구 출력은 저장하지 않는다."""
import collections
import datetime
import json
from pathlib import Path

home = Path('C:/Users/madro/.codex')
ids = ['01a184c0-ac10-7e32-be3d-bbb438d71442', '01a189e3-8597-7be1-8db2-dd9396ce3ff9',
       '01a19958-a4c6-70f3-b81d-26bd5d3ccd56', '01a19e7b-41c4-74b0-ae65-a70c55f42cfd',
       '01a1a8ce-cedd-77a1-964f-9db2ba5f6bcc', '01a1a3a5-4967-72d3-bde3-c431e3f305af']
paths = list((home/'archived_sessions').glob('*.jsonl'))
for day in ['2026/11/04', '2026/11/05']:
    paths.extend((home/'sessions'/day).glob('*.jsonl'))
chosen = [p for p in paths if any(i in p.name for i in ids)]
result = []
markers = ['getaddrinfo failed', 'Permission denied', 'AccessDenied', 'cannot rebase',
           'reportSha256', 'SyntaxError', 'AssertionError', 'SUCCEED']
for p in chosen:
    turns = []; current = None; effort = None
    for line in p.open(encoding='utf-8'):
        row = json.loads(line); data = row.get('payload', {}); kind = data.get('type')
        if row['type'] == 'turn_context':
            effort = data.get('effort')
            if current: current['effort'] = effort
        if row['type'] == 'event_msg' and kind == 'task_started':
            current = {'start': row['timestamp'], 'tools': collections.Counter(), 'errors': collections.Counter()}
            turns.append(current)
        if current and row['type'] == 'response_item':
            if kind in ['function_call', 'custom_tool_call']:
                current['tools'][data.get('name')] += 1
            if kind in ['function_call_output', 'custom_tool_call_output']:
                txt = str(data.get('output', ''))
                for marker in markers:
                    if marker in txt: current['errors'][marker] += 1
            if kind == 'message' and data.get('role') == 'assistant' and data.get('channel') == 'final':
                current['final'] = ''.join(x.get('text', '') for x in data.get('content', []))[:1600]
        if current and row['type'] == 'event_msg' and kind in ['task_complete', 'task_completed', 'turn_aborted']:
            current['final'] = data.get('last_agent_message', current.get('final', ''))[:1800]
            current['end'] = row['timestamp']; current['endType'] = kind
            current['elapsedSeconds'] = (datetime.datetime.fromisoformat(current['end'].replace('Z','+00:00')) - datetime.datetime.fromisoformat(current['start'].replace('Z','+00:00'))).total_seconds()
            current = None
    result.append({'log': str(p), 'turns': [t for t in turns if 'end' in t]})
out = {'auditedAt': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(), 'runs': result}
Path(__file__).with_name('audit-runs.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for run in result:
    print(Path(run['log']).name)
    for t in run['turns'][:4]:
        print(t.get('start'), t.get('effort'), t.get('elapsedSeconds'), dict(t['errors']))
        print(t.get('final','')[:450])
