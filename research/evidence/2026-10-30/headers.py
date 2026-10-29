import base64,json,re
from pathlib import Path
p=Path('research/evidence/2026-10-30');s=base64.b64decode(json.loads((p/'Treasury.raw.json').read_text())['raw']).decode();rows=re.findall(r'<tr[^>]*>.*?</tr>',s,re.S)
for row in rows:
 if '10/29/2026' in row:
  cells=re.findall(r'<td[^>]*>(.*?)</td>',row,re.S)
  print([(re.search(r'headers="([^"]+)',c).group(1) if re.search(r'headers="([^"]+)',c) else '',re.sub('<[^>]+>',' ',c).strip()) for c in cells]);print(row[:3000])
s=(p/'TrendForce.txt').read_text(encoding='utf-8');print([s[m.start()-30:m.start()+90] for m in re.finditer('Last Update',s)][:4])
