import datetime, json, re, subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3]
def read(p): return (R/p).read_text(encoding='utf-8')
def write(p,s): (R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v): write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
f=json.loads(read('research/evaluation/forecasts/2026-10-14-0815-same-close.json'))
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
published='2026-10-14T08:14:06.869000+09:00'
base={'schemaVersion':1,'forecastId':f['forecastId'],'contentHash':f['contentHash'],'commitSha':commit}
# 발행 이벤트는 최종 정정 커밋의 실제 push와 배포 확인 뒤 별도 보존한다.
for page in ['articles/market-2026-10-14.html','index.html','articles/index.html','articles/market.html']:
 s=read(page)
 if page.endswith('market-2026-10-14.html'):
  s=re.sub(r'(<meta property="article:published_time" content=")[^"]+',lambda m:m[1]+published,s)
  s=s.replace('公開','공개').replace('공개 시각은 아래 발행 기록 기준입니다.','최초 공개 '+published+'.').replace('2026.10.14 · 작성 08:09 KST','2026.10.14 · 작성 08:13 · 발행 08:14 KST')
 def ld(m):
  j=json.loads(m[1])
  if j.get('@type')=='Article': j['datePublished']=published
  for n in j.get('@graph',[]):
   for item in n.get('mainEntity',{}).get('itemListElement',[]):
    if item.get('url','').endswith('market-2026-10-14.html'): item['datePublished']=published
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,s,flags=re.S); write(page,s)
write('research/evidence/2026-10-14/publication.md',f'# 발행 증적\n\n- 최종 시세 확인 {f["dataCutoffAt"]}.\n- main 푸시 08:13:14 KST, 콘텐츠 {commit}.\n- Amplify 663 성공 {published}.\n- 라이브 확인 {now}, cache-busted custom·Amplify 기사/PNG/대시보드 확인.\n- 관련 회귀 및 평가기 53개 테스트 통과. 누적 평가 전체는 기존 9월 21일 보고서 해시 불일치로 실패.\n')
print(now,published)
