from pathlib import Path
import json,re
P=Path('research/evidence/2026-11-04');at=json.loads((P/'amplify-content.json').read_text(encoding='utf-8-sig'))['endTime']
for fn in ['articles/market-2026-11-04.html','index.html','articles/index.html','articles/market.html']:
 p=Path(fn);s=p.read_text(encoding='utf-8')
 if fn.endswith('market-2026-11-04.html'):
  s=s.replace('데이터 최종 확인 2026-11-04T09:16:08+09:00.','데이터 최종 확인 2026-11-04T09:16:08+09:00 · 발행 '+at+'.').replace(' · 작성 09:16 KST',' · 작성 09:16 · 발행 '+at[11:16]+' KST')
  s=re.sub(r'(<meta property="article:(?:published_time|modified_time)" content=")[^"]+',lambda m:m[1]+at,s)
 def ld(m):
  j=json.loads(m[1])
  if j.get('@type')=='Article':j.update(datePublished=at,dateModified=at)
  for n in j.get('@graph',[j]):
   for x in n.get('mainEntity',{}).get('itemListElement',[]):
    if x.get('url','').endswith('market-2026-11-04.html'):x.update(datePublished=at,dateModified=at)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,s,flags=re.S)
 def card(m):return re.sub(r'2026\.11\.04 · [^<]+','2026.11.04 · 발행 '+at[11:16]+' KST',m[0]) if 'market-2026-11-04.html' in m[0] else m[0]
 s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,s,flags=re.S);p.write_text(s,encoding='utf-8',newline='\n')
p=Path('research/evaluation/actuals/2026-11-03.json');j=json.loads(p.read_text(encoding='utf-8'));j['bizdate']='20261103';p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
p=Path('STATE.md');s=p.read_text(encoding='utf-8');p.write_text(s+'- 최초 공개 Amplify722 '+at+' · 콘텐츠 d8747c6. 양 도메인10자산 일치.\n',encoding='utf-8',newline='\n')
