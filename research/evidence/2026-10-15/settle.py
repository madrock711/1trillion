"""전일 확정값과 정확 시각 앵커 누락을 분리 보존한다."""
import hashlib, importlib.util, json, re
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
def ev(k):return json.loads((P/(k+'.json')).read_text(encoding='utf-8'))
def dump(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def n(x):return float(str(x).replace(',',''))
basic=ev('KOSPI-basic');integ=ev('KOSPI-integration');day='2026-10-14';at=basic['data']['localTradedAt'];fetched=integ['fetchedAt']
assert basic['data']['marketStatus']=='CLOSE' and at.startswith(day)
assert integ['data']['dealTrendInfo']['bizdate']=='20261014' and integ['data']['programTrendInfo']['bizdate']=='20261014'
a={'schemaVersion':1,'sessionDate':day,'bizdate':'20261014','fetchedAt':fetched,'marketStatus':'CLOSE'}
for code,key in [('KOSPI','kospi'),('122630','kodex')]:
 v=next(x for x in ev(code)['data'] if x['localTradedAt']==day)
 values={k:n(v[b]) for k,b in [('open','openPrice'),('high','highPrice'),('low','lowPrice'),('close','closePrice')]}
 # 독립 일봉 원문과 일치하는지 확인한다.
 raw=(P/('KOSPI-fchart.txt' if key=='kospi' else 'KODEX-fchart.txt')).read_bytes(); row=re.search(rb'20261014\|([^"\s]+)',raw).group(1).decode().split('|')
 assert [values[k] for k in ['open','high','low','close']]==list(map(float,row[:4]))
 values.update(asOf=day+'T15:30:00+09:00',source=ev(code)['url'],rawHash=ev(code)['rawHash'])
 if key=='kodex':values['volume']=v['accumulatedTradingVolume']
 a[key]=values
meta={'asOf':at,'source':integ['url'],'rawHash':integ['rawHash']}
d=integ['data'];flow=d['dealTrendInfo'];prog=d['programTrendInfo'];breadth=d['upDownStockInfo']
a['closeSnapshot']={'kodex':a['kodex'],'cashFlow':dict(foreign=n(flow['foreignValue']),institution=n(flow['institutionalValue']),personal=n(flow['personalValue']),unit='억원',**meta),'program':dict(arbitrage=n(prog['indexDifferenceReal']),nonArbitrage=n(prog['indexBiDifferenceReal']),total=n(prog['indexTotalReal']),unit='억원',**meta),'breadth':dict(up=int(breadth['riseCount'])+int(breadth['upperCount']),flat=int(breadth['steadyCount']),down=int(breadth['fallCount'])+int(breadth['lowerCount']),unit='종목',**meta)}
anchors={}
for name,time in [('open30','09:30:00'),('open60','10:00:00'),('at1400','14:00:00')]:
 anchors[name]={'status':'missing','expectedAsOf':day+'T'+time+'+09:00','attemptedAt':fetched,'sourceStatus':'unavailable','source':integ['url'],'missingReason':'최종 누적 응답만 확보. 해당 시각으로 소급하지 않음','rawHash':integ['rawHash']}
anchors['close']={'status':'available','asOf':day+'T15:30:00+09:00','foreignCash':n(flow['foreignValue']),'programNonArbitrage':n(prog['indexBiDifferenceReal']),'programTotal':n(prog['indexTotalReal']),'source':integ['url'],'rawHash':integ['rawHash']}
a['flowTrajectory']={'contract':'flow_trajectory_v1','unit':'억원','anchors':anchors}
spec=importlib.util.spec_from_file_location('evaluation',R/'scripts/evaluate_market_research.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.validate_actual(a,R/'research/evaluation/actuals'/f'{day}.json')
dump('research/evaluation/actuals/'+day+'.json',a)
out={'schemaVersion':1,'forecastId':'2026-10-14-0815-same-close','recordedAt':fetched,'actualRef':day,'realizedScenario':'base','errorCodes':['cause_unverifiable'],'triggerResults':[{'id':'base-price','status':'confirmed','value':6008.81,'threshold':5900},{'id':'flows','status':'unavailable','reason':'15:20 정확 시각 수급 앵커 미확보. 최종 외국인 -11,614억원은 -8천억원 조건 이탈'}],'driverAssessment':[],'hypothesisTests':[]}
dump('research/evaluation/outcomes/'+out['forecastId']+'.json',out)
print('전일 actual 검증 및 일봉 교차검증 통과')
