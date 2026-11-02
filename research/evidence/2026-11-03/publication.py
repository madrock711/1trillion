"""실제 push·배포 검증 이벤트를 정확한 계약 필드로 추가한다."""
import datetime,importlib.util,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sealed=json.loads((P/'sealed.json').read_text(encoding='utf-8'));fid=sealed['forecastId'];fp=R/'research/evaluation/forecasts'/f'{fid}.json';f=json.loads(fp.read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('evaluation',R/'scripts/evaluate_market_research.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);parsed=m.validate_forecast(f,fp,R)
kind=sys.argv[1];now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
if kind=='pushed':sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
else:
 job=json.loads((P/'amplify-content.json').read_text(encoding='utf-8-sig'));assert job['status']=='SUCCEED';sha=job['commitId']
v={'schemaVersion':1,'forecastId':fid,'contentHash':f['contentHash'],'commitSha':sha,'eventType':kind,'occurredAt':now}
if kind=='deploy_verified':
 rows=json.loads((P/'live-check.json').read_text(encoding='utf-8'));assert len(rows)==10 and all(x['status']==200 for x in rows);v.update(publicUrl=sealed['article'],availabilityStatus='available')
path=R/'research/evaluation/publications'/f'{fid}-{kind}.json';assert not path.exists();m.validate_publication_event(v,path,parsed);dump(str(path.relative_to(R)),v)
