from pathlib import Path
import json,re
for fn in ['index.html','articles/index.html','articles/market.html']:
 p=Path(fn);s=p.read_text(encoding='utf-8')
 def fix(m):
  j=json.loads(m[1])
  for n in j.get('@graph',[j]):
   for x in n.get('mainEntity',{}).get('itemListElement',[]):
    z=re.search(r'/articles/(market-[\d-]+\.html)$',x.get('url',''))
    if not z:continue
    a=Path('articles')/z[1]
    if not a.exists():continue
    q=a.read_text(encoding='utf-8'); title=re.search(r'<h1>(.*?)</h1>',q);desc=re.search(r'<meta name="description" content="([^"]+)',q);img=re.search(r'<meta property="og:image" content="([^"]+)',q)
    if title:x['name']=re.sub(r'<[^>]+>',' ',title[1])
    if desc:x['description']=desc[1]
    if img and isinstance(x.get('image'),dict):x['image']['url']=img[1]
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',fix,s,flags=re.S);p.write_text(s,encoding='utf-8',newline='\n')
p=Path('research/evidence/2026-11-03/seal_today.py');s=p.read_text(encoding='utf-8').replace(r'2026\.11\.02',r'2026\.11\.03');s=s.replace("nxt=[x for x in nxt if x['localTradedAt'].startswith(DATE) and x['marketStatus']=='OPEN']","nxt=[x for x in nxt if x['localTradedAt'].startswith(DATE) and x['marketStatus']=='OPEN' and x['localTradedAt'] <= cutoff]")
p.write_text(s,encoding='utf-8',newline='\n')
