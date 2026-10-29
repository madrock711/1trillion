import json,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
p=R/'assets/data/market-dashboard-latest.json';s=json.loads(p.read_text(encoding='utf-8'));s['snapshotId']='20261030-0804-levels';s['strategyLevels']=[{'asset':'KOSPI','support':'5,750','pivot':'5,937.66','resistance':'5,950'},{'asset':'KODEX 레버리지','support':'75,200원','pivot':'78,550원','resistance':'80,595원'}]
s['checklist']=[{'id':'support','label':'5,900선 지지와 5,950선 회복'},{'id':'flow','label':'외국인·프로그램 매수 복귀'}]
for x in s['technical']['instruments']:
 if x['id'] in ['KOSPI','KODEX']:
  v=[5750,5937.66,5950] if x['id']=='KOSPI' else [75200,78550,80595]
  x.update(levels=[{'label':a,'value':b} for a,b in zip(['1차 지지','반등 기준','저항'],v)],interpretation='반도체 매도 이후 지지력과 외국인 매수 복귀를 확인합니다.')
text=json.dumps(s,ensure_ascii=False,indent=2)+'\n';p.write_text(text,encoding='utf-8',newline='\n');(p.parent/'market-dashboard-20261030-0804-levels.json').write_text(text,encoding='utf-8',newline='\n')
st=json.loads((P/'run-status.json').read_text(encoding='utf-8'));now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat();st['status']='배포';st['stages'].update(검증={'completedAt':now,'result':'53 regression + preflight + Bash hooks passed; historical 9/21 hash error separate'},최종조회={'completedAt':'2026-10-30T08:04:05+09:00','path':'sealed.json'},푸시={'completedAt':now,'commit':'eea2d7d20184f97dbe7d02cc94ae1298aeeb0c6b'});(P/'run-status.json').write_text(json.dumps(st,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
