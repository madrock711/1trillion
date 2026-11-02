import subprocess,hashlib,json
from pathlib import Path
p=Path('reports/2026-11-03.md');b=subprocess.check_output(['git','show','HEAD:'+p.as_posix()]);f=json.loads(Path('research/evaluation/forecasts/2026-11-03-0803-same-close.json').read_text());assert hashlib.sha256(b).hexdigest()==f['reportSha256'];p.write_bytes(b)
