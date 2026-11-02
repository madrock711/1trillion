import datetime, importlib.util, json, re
from pathlib import Path
R=Path.cwd();P=R/'research/evidence/2026-11-02';sealed=json.loads((P/'sealed.json').read_text(encoding='utf-8'));fid=sealed['forecastId'];fp=R/'research/evaluation/forecasts'/f'{fid}.json';f=json.loads(fp.read_text(encoding='utf-8'));rows=json.loads((P/'live-check.json').read_text(encoding='utf-8'));assert len(rows)==10 and all(x['status']==200 for x in rows);now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds');spec=importlib.util.spec_from_file_location('evaluation',R/'scripts/evaluate_market_research.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);parsed=m.validate_forecast(f,fp,R);sha='78c55e1e6cbe7163b84481511dc434dfa40df05a';event={'schemaVersion':1,'forecastId':fid,'contentHash':f['contentHash'],'commitSha':sha,'eventType':'deploy_verified','occurredAt':now,'publicUrl':sealed['article'],'availabilityStatus':'available'};path=R/'research/evaluation/publications'/f'{fid}-deploy_verified.json';assert not path.exists();m.validate_publication_event(event,path,parsed);path.write_text(json.dumps(event,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
for page in ['articles/market-2026-11-02.html','index.html','articles/index.html','articles/market.html']:
 path=R/page;s=path.read_text(encoding='utf-8')
 if page.startswith('articles/market-2026-11-02'):
  s=re.sub(r'(<meta property="article:(?:published_time|modified_time)" content=")[^"]+',lambda m:m[1]+now,s);s=s.replace('데이터 최종 확인 '+sealed['cutoff']+'.','데이터 최종 확인 '+sealed['cutoff']+' · 공개 확인 '+now+'.');s=re.sub(r' · 작성 \d{2}:\d{2} KST',' · 작성 '+sealed['issuedAt'][11:16]+' · 공개 확인 '+now[11:16]+' KST',s);s=re.sub(r'(<time datetime=")[^"]+',lambda m:m[1]+now,s)
 else:
  def card(match):
   if 'market-2026-11-02.html' not in match[0]:return match[0]
   c=re.sub(r'(<time datetime=")[^"]+',lambda m:m[1]+now,match[0]);return re.sub(r'2026\.11\.02 · [^<]+','2026.11.02 · 공개 확인 '+now[11:16]+' KST',c)
  s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,s,flags=re.S)
 def ld(match):
  j=json.loads(match[1]);
  if j.get('@type')=='Article':j.update(datePublished=now,dateModified=now)
  for node in j.get('@graph',[j]):
   for x in node.get('mainEntity',{}).get('itemListElement',[]):
    if x.get('url','').endswith('market-2026-11-02.html'):x.update(datePublished=now,dateModified=now)
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,s,flags=re.S);path.write_text(s,encoding='utf-8',newline='\n')
p=R/'STATE.md';s=p.read_text(encoding='utf-8');p.write_text(s+f'- Amplify job 715 성공 2026-11-02T09:18:43.870+09:00, 두 도메인 공개 확인 {now}. 최초 공개 시각은 별도 관측하지 않아 공개 확인 시각을 사용.\n',encoding='utf-8',newline='\n');(P/'publication.json').write_text(json.dumps({'verifiedAt':now,'amplifyCompletedAt':'2026-11-02T09:18:43.870+09:00','commitSha':sha,'jobId':'715'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('deploy_verified',now)
