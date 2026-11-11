import re,html
from pathlib import Path
for k in ['DRAM','NAND']:
 s=html.unescape(re.sub('<[^>]*>',' ',Path('research/evidence/2026-11-12/'+k+'.raw').read_text(encoding='utf-8')));s=re.sub(r'\s+',' ',s);i=s.find('Last Update');print(k,s[i:i+2400])
