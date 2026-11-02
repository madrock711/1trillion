from pathlib import Path
import re
for fn in ['index.html','articles/index.html','articles/market.html']:
 p=Path(fn);s=p.read_text(encoding='utf-8')
 def fix(m):return re.sub(r'aria-label="[^"]+"','aria-label="11월 3일 KOSPI 장전 시황 읽기"',m[0]) if 'market-2026-11-03.html' in m[0] else m[0]
 s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',fix,s,flags=re.S)
 if fn=='articles/market.html':s=s.replace('반도체 매도와 지지력','반도체 추가 매도와 유가 하락')
 p.write_text(s,encoding='utf-8',newline='\n')
