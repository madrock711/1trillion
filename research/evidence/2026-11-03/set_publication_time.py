from pathlib import Path
import json,re
p=Path('research/evidence/2026-11-03');z=json.loads((p/'sealed.json').read_text(encoding='utf-8'));job=json.loads((p/'amplify-content.json').read_text(encoding='utf-8-sig'));at=job['endTime']
for fn in ['articles/market-2026-11-03.html','index.html','articles/index.html','articles/market.html']:
 q=Path(fn);s=q.read_text(encoding='utf-8')
 if fn.endswith('market-2026-11-03.html'):
  s=s.replace('데이터 최종 확인 '+z['cutoff']+'.','데이터 최종 확인 '+z['cutoff']+' · 발행 '+at+'.').replace(' · 작성 08:03 KST',' · 작성 08:03 · 발행 '+at[11:16]+' KST')
  s=re.sub(r'(<meta property="article:(?:published_time|modified_time)" content=")[^"]+',lambda m:m[1]+at,s)
 else:
  def card(m):return re.sub(r'2026\.11\.03 · [^<]+','2026.11.03 · 발행 '+at[11:16]+' KST',m[0]) if 'market-2026-11-03.html' in m[0] else m[0]
  s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,s,flags=re.S)
 def ld(m):
  j=json.loads(m[1])
  if j.get('@type')=='Article':j.update(datePublished=at,dateModified=at)
  for n in j.get('@graph',[j]):
   for x in n.get('mainEntity',{}).get('itemListElement',[]):
    if x.get('url','').endswith('market-2026-11-03.html'):x.update(datePublished=at,dateModified=at)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,s,flags=re.S);q.write_text(s,encoding='utf-8',newline='\n')
p=Path('STATE.md');s=p.read_text(encoding='utf-8');p.write_text(s+f'- 최초 공개 Amplify718 성공 {at}, 콘텐츠 {job["commitId"]}. 양 도메인10자산 일치 확인.\n',encoding='utf-8',newline='\n')
