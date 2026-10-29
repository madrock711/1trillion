import base64,json,re
from pathlib import Path
p=Path('research/evidence/2026-10-30');s=base64.b64decode(json.loads((p/'Treasury.raw.json').read_text())['raw']).decode()
for row in re.findall(r'<tr[^>]*>.*?</tr>',s,re.S):
 if '10/29/2026' in row:
  for attr,v in re.findall(r'<td([^>]*)>(.*?)</td>',row,re.S):print(re.search('class="([^"]+)',attr)[1],re.sub('<[^>]+>',' ',v).strip())
