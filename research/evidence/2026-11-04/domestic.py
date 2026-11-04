from pathlib import Path
import json
P=Path('research/evidence/2026-11-04')
for k in ['KOSPI','122630']: print(k,json.loads((P/f'{k}.json').read_text(encoding='utf-8'))['data'][:2])
