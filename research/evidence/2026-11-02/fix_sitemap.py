from pathlib import Path
import re
p=Path('sitemap.xml');s=p.read_text(encoding='utf-8')
for path in ['', 'articles/', 'articles/market.html']:
 pattern=r'(<loc>https://www\.hpmplab\.com/'+re.escape(path)+r'</loc>\s*<lastmod>)[^<]+'
 s,n=re.subn(pattern,lambda m:m[1]+'2026-11-02',s);assert n==1,(path,n)
p.write_text(s,encoding='utf-8',newline='\n')
