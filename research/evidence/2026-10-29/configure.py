from pathlib import Path
import re
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
s=(R/'research/evidence/2026-10-28/finalize.py').read_text(encoding='utf-8')
for a,b in [('2026-10-28','2026-10-29'),('20261028','20261029'),('2026.10.28','2026.10.29'),('2026-10-27','2026-10-28'),('5638.34','6012.44'),("'low':5800,'high':5950,'probability':.25","'low':6100,'high':6250,'probability':.20"),("'low':5600,'high':5800,'probability':.50","'low':5900,'high':6100,'probability':.50"),("'low':5400,'high':5600,'probability':.25","'low':5700,'high':5900,'probability':.30"),("'low':5250,'high':6100","'low':5500,'high':6400"),("'attack':25,'wait':50,'defense':25","'attack':15,'wait':50,'defense':35"),('=5800 if','=6100 if'),('else 5600','else 5900'),('10/28 NXT','10/29 NXT')]:s=s.replace(a,b)
(P/'finalize.py').write_text(s,encoding='utf-8',newline='\n')
s=(R/'research/evidence/2026-10-28/settle.py').read_text(encoding='utf-8').replace('2026-10-27','2026-10-28').replace('20261027','20261028').replace('2026-10-28-0803','2026-10-28-0833').replace("'realizedScenario':'bull'","'realizedScenario':'outside'").replace('10/27','10/28')
(P/'settle.py').write_text(s,encoding='utf-8',newline='\n')
for page in ['index.html','articles/index.html','articles/market.html']:
 p=R/page;t=p.read_text(encoding='utf-8')
 def repair(m):
  x=m[0]
  if 'market-2026-10-29.html' in x:return x
  q=re.search(r'market-(2026-\d\d-\d\d)\.html',x)
  if q:
   a=(R/'articles'/('market-'+q[1]+'.html')).read_text(encoding='utf-8');im=re.search(r'<meta property="og:image" content="[^"]*/([^/"]+)"',a)
   if im:x=re.sub(r'(src="[^" ]*/)[^/"]+\.png',lambda z:z[1]+im[1],x)
  return x
 t=re.sub(r'<article class="(?:article-card(?: home-article-card)?|market-article-item)"[^>]*>.*?</article>',repair,t,flags=re.S);p.write_text(t,encoding='utf-8',newline='\n')
p=R/'sitemap.xml';t=p.read_text(encoding='utf-8')
for u in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:t=re.sub(r'(<loc>'+re.escape(u)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+'2026-10-29',t)
p.write_text(t,encoding='utf-8',newline='\n')
p=R/'docs/현재작업중.md';t=p.read_text(encoding='utf-8');p.write_text(t+'\n## 2026-10-29 KOSPI 장전 리서치\n\n- reports/2026-10-29.md, research/notes/2026-10-29.md, research/evidence/2026-10-29/: 실제 시각 자료 수집·클라우드 실적/금리 결정 검증·공개 원고 준비와 발행 계약.\n- 기사·홈·목록·시장 대시보드·STATE.md·금리차 차트·신규 분기도로 썸네일 동기화.\n- 발행 전 핵심값 재조회 후 봉인·선별 커밋·Amplify 및 라이브 자산 확인.\n',encoding='utf-8',newline='\n')
