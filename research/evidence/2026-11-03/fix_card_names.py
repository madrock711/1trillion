from pathlib import Path
import json,re
for fn in ['index.html','articles/index.html','articles/market.html']:
 p=Path(fn);s=p.read_text(encoding='utf-8');titles={}
 for card in re.findall(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',s,re.S):
  u=re.search(r'href="([^"]+)"',card);t=re.search(r'<h[23][^>]*>(.*?)</h[23]>',card,re.S)
  if u and t:titles[u[1].split('/')[-1]]=re.sub(r'<[^>]+>','',t[1]).strip()
 def fix(m):
  j=json.loads(m[1])
  for n in j.get('@graph',[j]):
   for x in n.get('mainEntity',{}).get('itemListElement',[]):
    name=x.get('url','').split('/')[-1]
    if name in titles:x['name']=titles[name]
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',fix,s,flags=re.S);p.write_text(s,encoding='utf-8',newline='\n')
