import re
from pathlib import Path
root=Path('.')
for fn in ['index.html','articles/index.html','articles/market.html']:
 p=root/fn;s=p.read_text(encoding='utf-8')
 def fix(m):
  card=m[0];link=re.search(r'href="(?:articles/)?(market-\d{4}-\d{2}-\d{2}\.html)"',card)
  if not link or link[1]=='market-2026-11-02.html':return card
  article=root/'articles'/link[1]
  if not article.exists():return card
  a=article.read_text(encoding='utf-8');og=re.search(r'<meta property="og:image" content="[^"]*/([^/]+)"',a);alt=re.search(r'<figure class="article-hero-media"><img[^>]+alt="([^"]+)',a)
  if og:card=re.sub(r'(<img[^>]+src="(?:\.\./)?assets/images/articles/)[^"]+',lambda z:z[1]+og[1],card,count=1)
  if alt:card=re.sub(r'(<img[^>]+alt=")[^"]+',lambda z:z[1]+alt[1],card,count=1)
  return card
 s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',fix,s,flags=re.S);p.write_text(s,encoding='utf-8',newline='\n')
