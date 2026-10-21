"""검증 일봉 정산과 복구 불가 수급 증거를 보존한다."""
import base64,importlib.util,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def dump(p,v):(R/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
day='2026-10-21';integ=ev('KOSPI-integration');at=integ['fetchedAt']
a={'schemaVersion':1,'sessionDate':day,'bizdate':'20261021','fetchedAt':at,'marketStatus':'CLOSE'}
for name,key in [('KOSPI','kospi'),('KODEX','kodex')]:
 e=ev(name+'-fchart.raw');row=re.search(rb'20261021\|([^"\s]+)',base64.b64decode(e['raw'])).group(1).decode().split('|');a[key]=dict(zip(['open','high','low','close'],map(float,row[:4])));a[key].update(asOf=day+'T15:30:00+09:00',source=f'https://fchart.stock.naver.com/sise.nhn?symbol={"KOSPI" if key=="kospi" else "122630"}&timeframe=day&count=5&requestType=0',rawHash=e['rawHash'])
 if key=='kodex':a[key]['volume']=int(row[4])
a['closeSnapshotMissingReason']='10/21 integration 최종 묶음과 정확시각 수급앵커 미확보. 원문 evidence 보존, 15:20 앵커 미확보.'
a['flowTrajectoryMissingEvidence']={'sourceStatus':'unavailable','source':integ['url'],'asOf':day+'T15:30:00+09:00','fetchedAt':at,'missingReason':a['closeSnapshotMissingReason'],'rawHash':integ['rawHash']}
spec=importlib.util.spec_from_file_location('evaluation',R/'scripts/evaluate_market_research.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.validate_actual(a,R/'research/evaluation/actuals'/f'{day}.json');dump('research/evaluation/actuals/'+day+'.json',a)
out={'schemaVersion':1,'forecastId':'2026-10-21-0804-same-close','recordedAt':at,'actualRef':day,'realizedScenario':'bull','errorCodes':['cause_unverifiable'],'triggerResults':[{'id':'base-foreign','status':'unavailable','reason':'15:20 정확 수급 앵커 미확보'}],'driverAssessment':[],'hypothesisTests':[]}
fpath=R/'research/evaluation/forecasts'/f"{out['forecastId']}.json";f=m.validate_forecast(json.loads(fpath.read_text(encoding='utf-8')),fpath,R);out['triggerResults']=[{'id':c['id'],'status':'unavailable','reason':'정확 시각 앵커 미확보'} for t in json.loads(fpath.read_text(encoding='utf-8'))['scenarioTriggers'].values() for c in t['conditions']];out['driverAssessment']=[{'id':d['id'],'status':'unverifiable'} for d in json.loads(fpath.read_text(encoding='utf-8'))['drivers']];actual=m.validate_actual(a,R/'research/evaluation/actuals'/f'{day}.json');m.validate_outcome(out,R/'research/evaluation/outcomes'/f"{out['forecastId']}.json",f,actual);dump('research/evaluation/outcomes/'+out['forecastId']+'.json',out)
print('actual validated')
