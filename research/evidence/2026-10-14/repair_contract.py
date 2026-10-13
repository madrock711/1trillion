import datetime, hashlib, importlib.util, json
from pathlib import Path
R=Path(__file__).resolve().parents[3]; P=Path(__file__).parent
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
f=json.loads((R/'research/evaluation/forecasts/2026-10-14-0813-same-close.json').read_text(encoding='utf-8'))
for name in ['2026-10-14-0809-same-close','2026-10-14-0813-same-close']:
 source=R/'research/evaluation/forecasts'/f'{name}.json'
 source.rename(P/f'{name}-invalid-preparation.json')
f.update(forecastId='2026-10-14-'+now[11:16].replace(':','')+'-same-close',issuedAt=now,marketRegime='risk_off',supersedes=None)
f.pop('contentHash'); f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
path=R/'research/evaluation/forecasts'/f'{f["forecastId"]}.json'; path.write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=importlib.util.spec_from_file_location('evaluator',R/'scripts/evaluate_market_research.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.validate_forecast(f,path,R)
(P/'contract-correction.md').write_text(f'# 전망 계약 정정\n\n- {now}: 원본 조립 코드가 예전 계약의 risk-off 표기를 복사해 고정 분류 risk_off 검증에 실패했다.\n- 검증 실패한 두 준비 계약의 바이트를 이 증거 폴더에 그대로 보존하고, 평가 대상 폴더에는 검증을 통과한 새 독립 공개 계약만 둔다. 초기 준비 보고서는 최종값 치환으로 해시가 바뀌었으므로 초기 계약을 성과 표본으로 사용하지 않는다.\n- 새 공개 계약 {f["forecastId"]}. 최종 시세 확인 08:13:01, 조건과 수치 및 보고서 해시는 동일.\n',encoding='utf-8')
print('validated',f['forecastId'],now)
