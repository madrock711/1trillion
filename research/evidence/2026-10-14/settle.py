import json
from pathlib import Path
R=Path(__file__).resolve().parents[3]; P=Path(__file__).parent
def ev(k): return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def dump(p,x): (R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a=json.loads((R/'research/evaluation/actuals/2026-10-12.json').read_text(encoding='utf-8'))
a.update(sessionDate='2026-10-13',bizdate='20261013',fetchedAt=ev('KOSPI')['fetchedAt'])
for code,key in [('KOSPI','kospi'),('122630','kodex')]:
 v=next(v for v in ev(code)['data'] if v['localTradedAt']=='2026-10-13')
 a[key]={k:float(v[f].replace(',','')) for k,f in [('open','openPrice'),('high','highPrice'),('low','lowPrice'),('close','closePrice')]}
 a[key].update(asOf='2026-10-13T15:30:00+09:00',source=ev(code)['url'],rawHash=ev(code)['rawHash'])
 if key=='kodex': a[key]['volume']=v['accumulatedTradingVolume']
a['flowTrajectoryMissingEvidence'].update(asOf='2026-10-13T15:30:00+09:00',fetchedAt=ev('KOSPI')['fetchedAt'],rawHash=ev('KOSPI-integration')['rawHash'])
dump('research/evaluation/actuals/2026-10-13.json',a)
dump('research/evaluation/outcomes/2026-10-13-0812-same-close.json',{'schemaVersion':1,'forecastId':'2026-10-13-0812-same-close','recordedAt':ev('KOSPI')['fetchedAt'],'actualRef':'2026-10-13','realizedScenario':'bear','errorCodes':['range_too_narrow_down'],'triggerResults':[{'id':'price','status':'confirmed','value':6035.35,'threshold':6250},{'id':'flows','status':'unavailable','reason':'15:20 수급 앵커 원문 미확보'}],'driverAssessment':[],'hypothesisTests':[]})
