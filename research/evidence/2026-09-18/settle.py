"""9월 17일 확정 종가를 전일 공개 전망에 대조한다."""
import datetime as dt
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[3]
E = Path(__file__).parent
tz = dt.timezone(dt.timedelta(hours=9))
now = dt.datetime.now(tz).isoformat(timespec='seconds')

def load(path): return json.loads((R/path).read_text(encoding='utf-8'))
def dump(path, data):
    (R/path).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

basic=load('research/evidence/2026-09-18/KOSPI-basic.json')
assert basic['data']['marketStatus']=='PREOPEN'
assert basic['data']['closePrice']=='6,715.41'
actual={
  'schemaVersion':1,'sessionDate':'2026-09-17','bizdate':'20260917',
  'fetchedAt':now,'marketStatus':'CLOSE',
  'kospi':{'open':6779.02,'high':6795.53,'low':6697.85,'close':6715.41,
    'asOf':'2026-09-17T15:30:00+09:00',
    'source':'https://en.sedaily.com/finance/2026/09/17/kospi-ends-flat-as-foreigners-dump-16-billion-on-hawkish-fed',
    'rawPath':'research/evidence/2026-09-18/kospi-ohlc-source.html.gz',
    'rawHash':hashlib.sha256(__import__('gzip').decompress((E/'kospi-ohlc-source.html.gz').read_bytes())).hexdigest()},
  'closeSnapshot':None,
  'closeSnapshotMissingReason':'15시 20분 정확 시각 외국인·프로그램·시장 폭 원문 부재. 15시 30분 누적 보도를 소급하지 않음',
  'flowTrajectory':None,
  'flowTrajectoryMissingEvidence':{'sourceStatus':'unavailable','source':'https://m.stock.naver.com/api/index/KOSPI/integration',
    'asOf':'2026-09-17T15:30:00+09:00','fetchedAt':now,
    'missingReason':'09:30·10:00·14:00·15:20 동일 시각 수급 앵커 원문 미확보',
    'rawHash':load('research/evidence/2026-09-18/KOSPI-integration.json')['rawHash']}
}
dump('research/evaluation/actuals/2026-09-17.json', actual)
fid='2026-09-17-0813-same-close'
f=load('research/evaluation/forecasts/'+fid+'.json')
outcome={'schemaVersion':1,'forecastId':fid,'recordedAt':now,'actualRef':'2026-09-17',
 'realizedScenario':'base','errorCodes':[],
 'triggerResults':[{'id':condition['id'],'status':'unavailable','reason':'15시 20분 정확 시각 원문 미확보'}
  for group in f['scenarioTriggers'].values() for condition in group['conditions']],
 'driverAssessment':[{'id':'fed-rate-fx','status':'confirmed'}, {'id':'chip-resilience','status':'rejected'}, {'id':'foreign-flow','status':'confirmed'}],
 'hypothesisTests':[]}
dump('research/evaluation/outcomes/'+fid+'.json',outcome)
sessions=load('research/evaluation/trading-sessions.json')
if sessions['sessions'][-1]=='2026-09-17': sessions['sessions'].append('2026-09-18')
assert sessions['sessions'][-1]=='2026-09-18'
sessions.update(asOf=now,source='Naver Finance KOSPI PREOPEN 2026-09-18; KRX 거래일',rawHash=basic['rawHash'])
dump('research/evaluation/trading-sessions.json',sessions)
(E/'settlement-note.md').write_text(
 '# 2026-09-17 종가 정산\n\n'
 f'- 정산 기록 {now}. KOSPI 6,715.41(-0.04%), 시가 6,779.02·고가 6,795.53·저가 6,697.85. KODEX 레버리지 103,490원(-0.09%), 고가 106,520원·저가 102,825원.\n'
 '- 직전 장전 전망의 기본 종가 범위 6,600~6,750에 들어갔고 당일 전체 고저는 6,300~7,000 경로 안이다. 종가 기본 적중과 별개로 외국인 매도 축소 조건은 15:20 원문 부재로 미확인.\n'
 '- KRX+NXT 누적 외국인 약 2조 4,606억원 순매도 보도와 KRX 단독 약 2조 2,771억원 보도는 집계 범위가 다르다. 15:20 값처럼 사용하지 않는다.\n'
 '- 미국 반도체 상승을 국내 지속 반등으로 기대했으나 삼성·하이닉스 정규장 약세와 외국인 매도 때문에 오전 상승을 반납했다. 수급 계측 없는 확률 설명으로 대체하지 않는다.\n'
 '- KOSPI `price` API는 9/16에서 멈췄다. 9/17 OHLC는 한국거래소 인용 마감 보도 두 곳과 `basic`의 6,715.41을 대조했다.\n',encoding='utf-8',newline='\n')
print(now)
