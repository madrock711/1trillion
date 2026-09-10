"""9월 10일 확정 일봉과 관측 불가 조건을 분리 보존한다."""
import datetime, hashlib, json, pathlib
R = pathlib.Path(__file__).resolve().parents[3]
E = pathlib.Path(__file__).parent
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):
    with p.open('x',encoding='utf-8',newline='\n') as f: f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
ev=read(E/'KOSPI-fresh.json'); row=ev['data'][0]
assert row['localTradedAt']=='2026-09-10'
n=lambda x:float(str(x).replace(',',''))
a=read(R/'research/evaluation/actuals/2026-09-09.json')
a=json.loads(json.dumps(a,ensure_ascii=False).replace('2026-09-09','2026-09-10').replace('20260909','20260910').replace('9월 9일','9월 10일').replace('9월 10일 장전','9월 11일 장전'))
a['fetchedAt']=now
a['kospi']={k:n(row[k+'Price']) for k in ('open','high','low','close')}
a['kospi'].update(asOf='2026-09-10T15:30:00+09:00',source=ev['url'],rawHash=ev['rawHash'])
flow=read(E/'KOSPI-integration.json')
a['flowTrajectoryMissingEvidence'].update(fetchedAt=now,rawHash=flow['rawHash'])
save(R/'research/evaluation/actuals/2026-09-10.json',a)
prev=read(R/'research/evaluation/forecasts/2026-09-10-0828-same-close.json')
o={'schemaVersion':1,'forecastId':prev['forecastId'],'recordedAt':now,'actualRef':'2026-09-10','realizedScenario':'base','errorCodes':['cause_unverifiable'],'triggerResults':[], 'driverAssessment':[{'id':d['id'],'status':'unverifiable'} for d in prev['drivers']], 'hypothesisTests':[]}
for v in prev['scenarioTriggers'].values():
    for c in v['conditions']: o['triggerResults'].append({'id':c['id'],'status':'unavailable','reason':'9월 10일 15:20 이전 원문 앵커를 확보하지 못했다. 15:30 종가를 소급하지 않는다.'})
save(R/'research/evaluation/outcomes'/f"{prev['forecastId']}.json",o)
s=read(R/'research/evaluation/trading-sessions.json')
s.update(asOf=now,source='Naver Finance KOSPI 확정 일봉 및 2026-09-11 PREOPEN 응답',rawHash=ev['rawHash'],sessions=sorted(set(s['sessions']+['2026-09-10','2026-09-11'])))
(R/'research/evaluation/trading-sessions.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('9/10 actual/outcome saved',now)
