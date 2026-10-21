import json,base64,datetime,importlib.util,sys
from pathlib import Path
from bs4 import BeautifulSoup
R=Path.cwd();P=R/'research/evidence/2026-10-22'
s=BeautifulSoup(base64.b64decode(json.loads((P/'Treasury.raw.json').read_text(encoding='utf-8'))['raw']),'html.parser')
rows=[]
for tr in s.select('tbody tr'):
 cells=[x.get_text(' ',strip=True) for x in tr.select('td')]
 if len(cells)>=15:
  try:
   day=datetime.datetime.strptime(cells[0],'%m/%d/%Y').date();vals=list(map(float,cells[-14:]));rows.append((day,vals[3],vals[7],vals[11]))
  except ValueError:pass
assert rows and rows[-1][0].isoformat()=='2026-10-21';print(rows[-1])
src=(R/'scripts/update_yield_spreads.py').read_text(encoding='utf-8').replace('Source: Federal Reserve Bank of St. Louis (FRED), T10Y2Y and T10Y3M','Source: U.S. Treasury daily par yields; calculated 10Y-2Y / 10Y-3M')
import types
m=types.ModuleType('treasury_chart');sys.modules[m.__name__]=m;exec(compile(src,'treasury_chart','exec'),m.__dict__)
data={'T10Y2Y':[m.Observation(d,round(y-b,2)) for d,a,b,y in rows],'T10Y3M':[m.Observation(d,round(y-a,2)) for d,a,b,y in rows]}
for span,n,title in [('90d',90,'미국 국채 장단기 금리차 — 최근 90일'),('long_term',730,'미국 국채 장단기 금리차 — 2026년')]:
 m.create_chart({k:m.select_window(v,datetime.date(2026,10,22),n) for k,v in data.items()},R/f'charts/us_yield_spreads_{span}_2026-10-22.png',title,'2026-10-21 관측치 · 미 재무부 일별 금리',recent=span=='90d')
