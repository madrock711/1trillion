import sys,json,datetime
from pathlib import Path
sys.path.insert(0,'scripts');import update_yield_spreads as c
P=Path(__file__).parent
days=['2026-11-10','2026-11-12','2026-11-13','2026-11-16']
values={'T10Y2Y':[.25,.24,.27,.29],'T10Y3M':[.68,.78,.83,.78]}
data={k:[c.Observation(datetime.date.fromisoformat(d),v) for d,v in zip(days,vs)] for k,vs in values.items()}
evidence={'checkedAt':datetime.datetime.now().astimezone().isoformat(),'method':'FRED official pages after CSV timeout; four displayed observations only','series':{k:{'url':'https://fred.stlouisfed.org/series/'+k,'observations':dict(zip(days,v))} for k,v in values.items()},'absolute':{'asOf':'2026-11-13','DGS10':5.15,'DGS2':4.88,'DGS3MO':4.32}}
(P/'fred-web-check.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for k in ['long_term','90d']:
 c.create_chart(data,Path(f'charts/us_yield_spreads_{k}_2026-11-17.png'),'미국 국채 금리차 — 최근 공개 관측','2026-11-10·12·13·16 네 관측 · 단위 %p',recent=True)
p=P/'package.json';v=json.loads(p.read_text(encoding='utf-8'));v['files']+=['research/evidence/2026-11-17/chart_web.py','research/evidence/2026-11-17/fred-web-check.json'];p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['article-body.html','report-template.md']:
 p=P/name;t=p.read_text(encoding='utf-8');t=t.replace('두 금리차의 방향도 서로 달랐습니다.','개별 만기의 최신 관측은 13일이며 10년 5.15%, 2년 4.88%, 3개월 4.32%입니다. 두 금리차의 방향도 서로 달랐습니다.');p.write_text(t,encoding='utf-8')
print('four official observations charted')
