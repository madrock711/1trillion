import datetime,json,hashlib,importlib.util
from pathlib import Path
r=Path.cwd();p=r/'research/evidence/2026-11-03';now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
def ev(k):return json.loads((p/(k+'.json')).read_text(encoding='utf-8'))
def n(v):return float(str(v).replace(',',''))
a=json.loads((r/'research/evaluation/actuals/2026-10-29.json').read_text(encoding='utf-8'));a.update(sessionDate='2026-11-02',bizdate='20261102',fetchedAt=now)
for key,k in [('kospi','KOSPI'),('kodex','122630')]:
 d=ev(k);v=d['data'][0];a[key]={x:n(v[y]) for x,y in [('open','openPrice'),('high','highPrice'),('low','lowPrice'),('close','closePrice')]};a[key].update(asOf='2026-11-02T15:30:00+09:00',source=d['url'],rawHash=d['rawHash'])
 if key=='kodex':a[key]['volume']=v['accumulatedTradingVolume']
reason='정확15:20 수급앵커·발행후 분봉경로 미확보; 투자자 합계와 원천 간 차이로 최종 묶음 보류'
a['closeSnapshotMissingReason']=reason;a['flowTrajectoryMissingEvidence'].update(asOf='2026-11-02T15:30:00+09:00',fetchedAt=now,missingReason=reason,rawHash=ev('KOSPI-integration')['rawHash'])
(r/'research/evaluation/actuals/2026-11-02.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
fid='2026-11-02-0917-same-close';f=json.loads((r/f'research/evaluation/forecasts/{fid}.json').read_text(encoding='utf-8'));o={'schemaVersion':1,'forecastId':fid,'recordedAt':now,'actualRef':'2026-11-02','realizedScenario':'bull','errorCodes':['cause_unverifiable'],'triggerResults':[{'id':c['id'],'status':'unavailable','reason':reason} for t in f['scenarioTriggers'].values() for c in t['conditions']],'driverAssessment':[{'id':d['id'],'status':'unverifiable'} for d in f['drivers']],'hypothesisTests':[]}
(r/f'research/evaluation/outcomes/{fid}.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
s=json.loads((p/'run-status.json').read_text(encoding='utf-8-sig'));s['stage']='검증';s['stages'].update(조사=now,집필=now,이미지=now);s['knownLimitation']='누적 평가기 기존9/21 reportSha256 불일치, 오늘과 분리';(p/'run-status.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
