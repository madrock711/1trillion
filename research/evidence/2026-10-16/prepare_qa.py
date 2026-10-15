"""대표 이미지를 발행 크기로 맞추고 과거 카드를 보존한다."""
import json,re,subprocess
from pathlib import Path
from PIL import Image,ImageOps
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
im=Image.open(r'C:\Users\madro\.codex\generated_images\01a141cb-79ee-7d22-95dd-327c83e0fc76\exec-c2013ffd-ce4f-4316-b15b-a3cc0eb1c759.png')
ImageOps.fit(im,(1200,630),method=Image.Resampling.LANCZOS).save(R/'assets/images/articles/market-2026-10-16-chip-demand-funding-1200x630.png')
prepared=json.loads((P/'prepared.json').read_text(encoding='utf-8'))
for page in ['index.html','articles/index.html','articles/market.html']:
 path=R/page;s=path.read_text(encoding='utf-8');old=subprocess.check_output(['git','show','HEAD:'+page],cwd=R).decode('utf-8')
 pat=r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>'
 oldcard=next(m[0] for m in re.finditer(pat,old,re.S) if 'market-2026-10-15.html' in m[0])
 s=re.sub(pat,lambda m:oldcard if 'market-2026-10-15.html' in m[0] else m[0],s,flags=re.S)
 if page=='articles/market.html':s=s.replace('미국 CPI가 3.7%로 높아지고 반도체주가 동반 하락했습니다. 오늘은 KOSPI 6,000선 방어와 오후 3시 TSMC 실적이 관건입니다.',prepared['summary'])
 path.write_text(s,encoding='utf-8',newline='\n')
s=json.loads((P/'prepared-dashboard.json').read_text(encoding='utf-8'));s['snapshotId']='20261016-prepared';(R/'assets/data/market-dashboard-latest.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('thumbnail 1200x630, prior cards preserved')
