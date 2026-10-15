"""실제 push·배포 검증 이벤트를 정확한 계약 필드로 추가한다."""
import datetime,importlib.util,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sealed=json.loads((P/'sealed.json').read_text(encoding='utf-8'));fid=sealed['forecastId'];fp=R/'research/evaluation/forecasts'/f'{fid}.json';f=json.loads(fp.read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('evaluation',R/'scripts/evaluate_market_research.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);parsed=m.validate_forecast(f,fp,R)
kind=sys.argv[1];now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
if kind=='pushed':sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
else:
 job=json.loads((P/'amplify-content.json').read_text(encoding='utf-8-sig'));assert job['status']=='SUCCEED';sha=job['commitId']
v={'schemaVersion':1,'forecastId':fid,'contentHash':f['contentHash'],'commitSha':sha,'eventType':kind,'occurredAt':now}
if kind=='deploy_verified':
 rows=json.loads((P/'live-check.json').read_text(encoding='utf-8'));assert len(rows)==10 and all(x['status']==200 for x in rows);v.update(publicUrl=sealed['article'],availabilityStatus='available')
path=R/'research/evaluation/publications'/f'{fid}-{kind}.json';assert not path.exists();m.validate_publication_event(v,path,parsed);dump(str(path.relative_to(R)),v)
if kind=='deploy_verified':
 published=job['endTime']
 for page in ['articles/market-2026-10-16.html','index.html','articles/index.html','articles/market.html']:
  s=read(page)
  if page.endswith('market-2026-10-16.html'):
   s=re.sub(r'(<meta property="article:published_time" content=")[^"]+',lambda m:m[1]+published,s);s=s.replace('데이터 최종 확인 '+sealed['cutoff']+'.','데이터 최종 확인 '+sealed['cutoff']+' · 최초 공개 '+published+'.');s=s.replace(' · 작성 '+sealed['issuedAt'][11:16]+' KST',' · 작성 '+sealed['issuedAt'][11:16]+' · 발행 '+published[11:16]+' KST');s=re.sub(r'(<time datetime=")[^"]+',lambda m:m[1]+published,s)
  else:
   def card(match):
    if 'market-2026-10-16.html' not in match[0]:return match[0]
    c=re.sub(r'(<time datetime=")[^"]+',lambda m:m[1]+published,match[0]);c=re.sub(r'2026\.10\.16 · [^<]+','2026.10.16 · '+published[11:16]+' KST',c);return c.replace('밝은 자연광 속 반도체 칩과 금빛 고리, 실리콘 웨이퍼','밝은 하늘 아래 웨이퍼 다리와 호박색 압력 아치')
   s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,s,flags=re.S)
  def ld(match):
   j=json.loads(match[1])
   if j.get('@type')=='Article':j['datePublished']=published
   for n in j.get('@graph',[j]):
    for x in n.get('mainEntity',{}).get('itemListElement',[]):
     if x.get('url','').endswith('market-2026-10-16.html'):x['datePublished']=published
   return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
  s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,s,flags=re.S);write(page,s)
 write('STATE.md',read('STATE.md')+f'- 최초 공개 {published}, Amplify {job["jobId"]}. pushed/deploy_verified 계약 검증 통과.\n')
 dump('research/evidence/2026-10-16/publication.json',{'publishedAt':published,'checkedAt':now,'commitSha':sha,'jobId':job['jobId']})
print(kind,sha,now)
