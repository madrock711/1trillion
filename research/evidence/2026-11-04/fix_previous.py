from pathlib import Path
import json
p=Path('research/evaluation/outcomes/2026-11-03-0803-same-close.json');j=json.loads(p.read_text(encoding='utf-8'));j={k:v for k,v in j.items() if not k.startswith('postForecastPath')};p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
