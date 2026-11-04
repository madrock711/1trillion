from pathlib import Path
import json,re
P=Path('research/evidence/2026-11-04');D='2026-11-04'
s=json.loads((P/'prepared-dashboard.json').read_text(encoding='utf-8'));s['marketState']='한국 장중';s['changes']=[{'label':'KOSPI 전일','before':'5,859.08','after':'5,648.79','meaning':'11월 3일 3.59% 하락했습니다.'}];s['memory']=[{'label':'DDR5 16Gb','value':'$61.50','change':'11/3 보합'},{'label':'DDR4 16Gb','value':'$82.719','change':'11/3 보합'}];s['strategyLevels']=[{'asset':'KOSPI','support':'5,700','pivot':'5,800','resistance':'5,900'},{'asset':'KODEX 레버리지','support':'73,565원','pivot':'74,000원','resistance':'75,090원'}];s['technical']['note']='11월 4일 장중 분석 기준선입니다.'
for x in s['technical']['instruments']:
 if x['id']=='KODEX':x['levels']=[{'label':k,'value':v} for k,v in zip(['1차 지지','반등 기준','저항'],[73565,74000,75090])]
(P/'prepared-dashboard.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
Path('STATE.md').write_text('# KOSPI·KODEX 리서치 상태\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장중.\n- 전일 KOSPI5648.79(-3.59%), KODEX70095(-7.59%).\n- AMD 실적과 미국 반도체 반등. 기존 Intel 충격 중복 제외.\n- 기본5700~5900(50), 강세5900초과~6050(25), 약세5450~5700미만(25), 대응20/50/30.\n- 전일 기본범위 실패·약세범위 종가. 조건수급/발행후경로 미검증.\n- 다음 미국 고용11/6 22:30 KST. reports/2026-11-04.md.\n',encoding='utf-8')
q=Path('articles/market-2026-11-04.html');t=q.read_text(encoding='utf-8').replace('2026.11.03','2026.11.04').replace('장전 브리핑','장중 브리핑');q.write_text(t,encoding='utf-8')
# Adapt the sealer to current intraday data, with a fresh live reference.
t=Path('research/evidence/2026-11-03/seal_today.py').read_text(encoding='utf-8').replace('2026-11-03','2026-11-04').replace('2026-11-02','2026-11-03').replace('20261103-','20261104-').replace('2026.11.03','2026.11.04')
t=t.replace("le=next(x for x in ev['122630']['data'] if x['localTradedAt']=='2026-11-03')","le=ev['122630']['data'][0]")
t=t.replace("assert kp['localTradedAt']=='2026-11-03' and le['localTradedAt']=='2026-11-03'","assert kp['localTradedAt']==DATE and le['localTradedAt']==DATE and kb['marketStatus']=='OPEN'")
t=t.replace("'2026-11-03T15:30:00+09:00'","kb['localTradedAt']").replace('KOSPI 전일 종가','KOSPI 장중').replace('KODEX 레버리지 전일 종가','KODEX 레버리지 장중')
t=t.replace("marketState='preopen',evaluationBucket='preopen'","marketState='intraday',evaluationBucket=bucket").replace("'kind':'previous_close'","'kind':'live'")
t=t.replace("'probability':.20","'probability':.25").replace("'probability':.30","'probability':.25").replace("'low':5250,'high':6250","'low':5450,'high':6200").replace("'attack':10,'wait':45,'defense':45","'attack':20,'wait':50,'defense':30").replace('미국 반도체 추가 매도와 유가 하락','AMD 실적과 미국 반도체 반등')
t=t.replace("x.update(value=number(kb['closePrice'])","x.update(stateLabel='장중',asOfLabel=kb['localTradedAt'],value=number(kb['closePrice'])")
(P/'seal_today.py').write_text(t,encoding='utf-8')
for fn in ['verify_live.py','publication.py']:
 t=Path('research/evidence/2026-11-03',fn).read_text(encoding='utf-8').replace('2026-11-03','2026-11-04').replace('chip-oil-balance','earnings-springboard');(P/fn).write_text(t,encoding='utf-8')
