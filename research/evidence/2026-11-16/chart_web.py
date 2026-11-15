import sys,json,datetime
from pathlib import Path
sys.path.insert(0,'scripts');import update_yield_spreads as c
P=Path(__file__).parent
days=['2026-11-09','2026-11-10','2026-11-12','2026-11-13']
values={'T10Y2Y':[.32,.25,.24,.27],'T10Y3M':[.64,.68,.78,.83]}
data={k:[c.Observation(datetime.date.fromisoformat(d),v) for d,v in zip(days,vs)] for k,vs in values.items()}
evidence={'checkedAt':datetime.datetime.now().astimezone().isoformat(),'method':'FRED official pages after two failed CSV attempts; four displayed observations only','series':{k:{'url':'https://fred.stlouisfed.org/series/'+k,'observations':dict(zip(days,v))} for k,v in values.items()},'absolute':{'asOf':'2026-11-12','DGS10':5.10,'DGS2':4.86,'DGS3MO':4.32}}
(P/'fred-web-check.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for k in ['long_term','90d']:
 c.create_chart(data,Path(f'charts/us_yield_spreads_{k}_2026-11-16.png'),'미국 국채 금리차 — 최근 공개 관측','2026-11-09·10·12·13 네 관측 · 휴일 제외 · 단위 %p',recent=True)
p=P/'package.json';v=json.loads(p.read_text(encoding='utf-8'));v['files']+=['research/evidence/2026-11-16/chart_web.py','research/evidence/2026-11-16/fred-web-check.json'];p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('four observations charted')
