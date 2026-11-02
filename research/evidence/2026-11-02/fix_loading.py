import re
from pathlib import Path
for fn in ['index.html','articles/index.html','articles/market.html']:
 p=Path(fn);s=p.read_text(encoding='utf-8')
 def fix(m):
  return m[0] if 'market-2026-11-02.html' in m[0] else m[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
 s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',fix,s,flags=re.S);p.write_text(s,encoding='utf-8',newline='\n')
