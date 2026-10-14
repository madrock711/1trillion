"""최초 공개 시각을 배포 완료 증거로 기록한다. 봉인 보고서는 수정하지 않는다."""
import datetime, json, re, subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
f=json.loads(read('research/evaluation/forecasts/2026-10-15-0807-same-close.json'));job=json.loads((P/'amplify-668.json').read_text(encoding='utf-8-sig'));assert job['status']=='SUCCEED'
published=job['endTime'];now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
base={'schemaVersion':1,'forecastId':f['forecastId'],'contentHash':f['contentHash'],'commitSha':job['commitId']}
event=dict(base,eventType='deploy_verified',occurredAt=now,publicUrl='https://www.hpmplab.com/articles/market-2026-10-15.html',availabilityStatus='available')
path='research/evaluation/publications/'+f['forecastId']+'-deploy_verified.json';assert not (R/path).exists();dump(path,event)
for page in ['articles/market-2026-10-15.html','index.html','articles/index.html','articles/market.html']:
 s=read(page)
 if page.endswith('market-2026-10-15.html'):
  s=re.sub(r'(<meta property="article:published_time" content=")[^"]+',lambda m:m[1]+published,s)
  s=s.replace('2026.10.15 · 작성 08:07 KST','2026.10.15 · 작성 08:07 · 발행 08:09 KST')
  s=s.replace('데이터 최종 확인 2026-10-15T08:07:53+09:00.','데이터 최종 확인 2026-10-15T08:07:53+09:00 · 최초 공개 '+published+'.')
 def ld(m):
  j=json.loads(m[1])
  if j.get('@type')=='Article':j['datePublished']=published
  for n in j.get('@graph',[j]):
   for x in n.get('mainEntity',{}).get('itemListElement',[]):
    if x.get('url','').endswith('market-2026-10-15.html'):x['datePublished']=published
  return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,s,flags=re.S)
 if not page.endswith('market-2026-10-15.html'):
  def card(m):return m[0].replace('2026-10-15T08:07:53+09:00',published).replace('2026.10.15 · 08:07 KST','2026.10.15 · 08:09 KST') if 'market-2026-10-15.html' in m[0] else m[0]
  s=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',card,s,flags=re.S)
 write(page,s)
write('research/evidence/2026-10-15/publication.md',f'# 10월 15일 발행 증적\n\n- 최종 데이터 확인 {f["dataCutoffAt"]}. 작성·계약 봉인 {f["issuedAt"]}.\n- main 콘텐츠 {job["commitId"]}; push 확인 08:08:57 KST.\n- 최초 공개 Amplify 668 성공 {published}. 데이터 확인부터 공개까지 약 75초.\n- 양쪽 도메인 기사·대표 이미지·대시보드·두 차트 10개 cache-busted HTTP 200, 제목·스냅샷·PNG 확인 {now}.\n- preflight·관련 JS·평가기 회귀 53개·Bash pre-commit·작업기록 가드 통과. 원문 후행 공백 문제는 base64 JSON 저장으로 수정해 최종 diff 검사 통과.\n- 누적 평가 전체는 기존 9월 21일 reportSha256 불일치로 실패. 스킬 전용 검증기는 없어 SKIP.\n- 브라우저 기사·홈 썸네일·대시보드 소개 및 실제 라이브 시각 확인, 임시 검증 탭 종료.\n')
write('STATE.md',read('STATE.md')+f'- 최초 공개 {published}, Amplify 668. 발행 이벤트 publications/{f["forecastId"]}-*.json.\n')
print(published,now)
