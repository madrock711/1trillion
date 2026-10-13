import datetime, json
from pathlib import Path
R=Path(__file__).resolve().parents[3]
f=json.loads((R/'research/evaluation/forecasts/2026-10-14-0815-same-close.json').read_text(encoding='utf-8'))
base={'schemaVersion':1,'forecastId':f['forecastId'],'contentHash':f['contentHash'],'commitSha':'55398972a0a296bdfa21b54cb3b13041d7fe79ec'}
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
for event,extra in [('pushed',{'occurredAt':'2026-10-14T08:17:12+09:00'}),('deploy_verified',{'occurredAt':now,'publicUrl':'https://www.hpmplab.com/articles/market-2026-10-14.html','availabilityStatus':'available','deployment':{'amplifyJobId':'664','commitSha':base['commitSha'],'completedAt':'2026-10-14T08:17:12.927000+09:00'}})]:
 p=R/'research/evaluation/publications'/f'{f["forecastId"]}-{event}.json'; assert not p.exists(); p.write_text(json.dumps(dict(base,eventType=event,**extra),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(now)
