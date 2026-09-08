import json,pathlib,datetime
R=pathlib.Path(__file__).resolve().parents[3]; E=pathlib.Path(__file__).parent
def ev(k):return json.loads((E/(k+'.json')).read_text(encoding='utf-8'))
def dump(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def num(v):return float(str(v).replace(',',''))
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
k=ev('KOSPI');i=ev('KOSPI-integration');b=ev('KOSPI-basic');q=ev('122630');x=next(r for r in k['data'] if r['localTradedAt']=='2026-09-08');z=next(r for r in q['data'] if r['localTradedAt']=='2026-09-08')
assert b['data']['marketStatus']=='CLOSE' and b['data']['localTradedAt'].startswith('2026-09-08')
data=i['data'];assert data['dealTrendInfo']['bizdate']==data['programTrendInfo']['bizdate']=='20260908'
def meta(o,unit):return dict(asOf=b['data']['localTradedAt'],source=o['url'],rawHash=o['rawHash'],unit=unit)
snap={'kodex':dict({f:num(z[f+'Price']) for f in ['open','high','low','close']},volume=z['accumulatedTradingVolume'],**dict(meta(q,'원'),asOf='2026-09-08T15:30:00+09:00')),
'cashFlow':dict({f:num(data['dealTrendInfo'][key]) for f,key in [('foreign','foreignValue'),('institution','institutionalValue'),('personal','personalValue')]},**meta(i,'억원')),
'program':dict({f:num(data['programTrendInfo'][key]) for f,key in [('arbitrage','indexDifferenceReal'),('nonArbitrage','indexBiDifferenceReal'),('total','indexTotalReal')]},**meta(i,'억원')),
'breadth':dict({f:int(data['upDownStockInfo'][key]) for f,key in [('up','riseCount'),('flat','steadyCount'),('down','fallCount')]},**meta(i,'종목'))}
a=dict(schemaVersion=1,sessionDate='2026-09-08',bizdate='20260908',fetchedAt=stamp,marketStatus='CLOSE',kospi=dict({f:num(x[f+'Price']) for f in ['open','high','low','close']},asOf='2026-09-08T15:30:00+09:00',source=k['url'],rawHash=k['rawHash']),closeSnapshot=snap,closeSnapshotMissingReason=None,flowTrajectory=None,flowTrajectoryMissingEvidence=dict(sourceStatus='incomplete',source=i['url'],asOf=b['data']['localTradedAt'],fetchedAt=stamp,missingReason='전일 마감 자료는 남아 있으나 09:30·10:00·14:00·15:30 세 지표 원문 앵커가 없으며 18:59 종가 후 응답을 15:30으로 소급하지 않는다.',rawHash=i['rawHash']))
a['closeSnapshot']=None
a['flowTrajectoryMissingEvidence']['asOf']='2026-09-08T15:30:00+09:00'
a['closeSnapshotMissingReason']='18:59 마감 후 응답의 수급·시장폭과 확정 KODEX 일봉은 settlement-note.json에 보존했다. 15:30 수급 앵커가 없어 평가 계약의 완결 묶음으로 봉인하지 않는다.'
dump('research/evaluation/actuals/2026-09-08.json',a)
f=json.loads((R/'research/evaluation/forecasts/2026-09-08-0814-same-close.json').read_text(encoding='utf-8'))
out=dict(schemaVersion=1,forecastId=f['forecastId'],recordedAt=stamp,actualRef='2026-09-08',realizedScenario='base',errorCodes=['cause_unverifiable'],triggerResults=[dict(id=c['id'],status='unavailable',reason='15:20 이전 시각의 원문 앵커를 확보하지 못했다. 18:59 마감 응답은 조건 관측시각을 넘으므로 대신 쓰지 않는다.') for r in f['scenarioTriggers'].values() for c in r['conditions']],driverAssessment=[dict(id=d['id'],status='partial' if d['id']=='domestic-demand' else 'unverifiable') for d in f['drivers']],hypothesisTests=[])
archive=json.loads((R/'assets/data/kospi-intraday/2026-09-08.json').read_text(encoding='utf-8'))
bar=next(v for v in archive['bars'] if v['time']=='15:20')
for result in out['triggerResults']:
 c=next(c for r in f['scenarioTriggers'].values() for c in r['conditions'] if c['id']==result['id'])
 value=bar['close'] if c['metricId']=='kospi_price' else bar.get('foreign') if c['metricId']=='foreign_cash' else None
 if value is not None:
  ok={'gt':value>c['threshold'],'gte':value>=c['threshold'],'lt':value<c['threshold'],'lte':value<=c['threshold']}[c['operator']]
  observed='2026-09-08T15:20:00+09:00' if c['metricId']=='kospi_price' else bar['flowObservedAt']
  if observed and len(observed)==5:observed='2026-09-08T'+observed+':00+09:00'
  result.clear();result.update(id=c['id'],status='observed' if ok else 'not_observed',observedAt=observed,observedValue=value,source=c['source'])
dump('research/evaluation/outcomes/'+f['forecastId']+'.json',out)
s=json.loads((R/'research/evaluation/trading-sessions.json').read_text(encoding='utf-8'));s.update(asOf=stamp,source='Naver Finance KOSPI 확정 일봉 및 122630 2026-09-09 PREOPEN 거래일',rawHash=q['rawHash']);s['sessions']=sorted(set(s['sessions']+['2026-09-09']));dump('research/evaluation/trading-sessions.json',s)
dump('research/evidence/2026-09-09/settlement-note.json',dict(recordedAt=stamp,closeSnapshot=snap,assessment='기본 종가 범위 적중, 전체 장중 경로 포락. 고점 7171.52에서 6954.52로 반납; 외국인과 프로그램 순매수만으로 상승 지속을 보장하지 않았다. 마감 전 트리거는 미확인.'))
print(json.dumps(snap,ensure_ascii=False))
