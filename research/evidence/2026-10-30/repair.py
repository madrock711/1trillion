import json,re,datetime
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
TITLE='Intel 전망 부진에 반도체 급락…AI 투자 부담 속 5,900선 시험'
SUMMARY='Intel의 실적 전망과 Amazon의 현금 지출 부담에 반도체 시간외 매도가 확대됐습니다. KOSPI는 5,900선 지지와 외국인 매수 복귀를 시험합니다.'
old='Amazon 성장에도 커진 AI 투자 부담…5,900선 지지 시험';os='Amazon의 클라우드 성장에도 현금 지출 부담이 커졌고 미국 반도체주가 하락했습니다. KOSPI는 5,900선 지지와 외국인 매수 복귀를 시험합니다.'
for p in ['articles/market-2026-10-30.html','index.html','articles/index.html','articles/market.html']:
 s=read(p).replace(old,TITLE).replace(os,SUMMARY)
 s=s.replace('2026.10.20 · 작성','2026.10.30 · 작성')
 if p.endswith('2026-10-30.html'):s=s.replace('<h2>반도체 약세와 물가 부담</h2>','<h2>Intel 전망 부진에 커진 반도체 매도</h2><p>Intel은 4분기 매출을 150억~160억달러, 조정 주당순이익을 0.25달러로 제시했습니다. 서버용 Xeon 수요가 견조하다는 설명에도 PC 업계의 역풍이 부담으로 남았습니다. 시간외 매도는 AMD와 Nvidia, Micron 등으로 번졌습니다. <a href="https://www.intc.com/news-events/press-releases">Intel 실적 발표</a></p><h2>반도체 약세와 물가 부담</h2>')
 write(p,s)
p='research/evidence/2026-10-30/prepared-dashboard.json';s=json.loads(read(p));s.update(headline=TITLE,summary=SUMMARY,sourceLabel='미국 10월 29일 정규장·시간외 · 국내 10월 29일 종가 · 10월 30일 장전');s['latestArticle']['title']=TITLE
s['stance']={'label':'반도체 매도와 지지력 확인','attack':5,'wait':40,'defense':55,'note':'Intel 전망과 AI 투자 현금 부담 속에서 반도체 매수 복귀를 확인합니다.'}
s['changes']=[{'label':'KOSPI','before':'6,012.44','after':'5,937.66','meaning':'전일 1.24% 하락하며 6,000선 아래로 내려왔습니다.'}]
s['factors']=[{'label':'Intel 전망','metric':'Q4 조정 EPS $0.25','detail':'10월 29일 실적 발표','tone':'warning'},{'label':'Amazon 현금흐름','metric':'TTM FCF -424억달러','detail':'AWS 성장과 인프라 지출 부담','tone':'warning'}]
s['memory']=[{'label':'DDR5 16Gb · 10/29','value':'$61.333','change':'보합'},{'label':'DDR4 16Gb · 10/29','value':'$82.92','change':'보합'}]
s['events']=[{'time':'10월 30일 21:30 KST','name':'미국 고용비용지수','path':'임금·금리 기대'}]
for x in s['scenarios']:
 k=x['id'];x.update(label={'bull':'강세 · 15%','base':'기본 · 45%','bear':'약세 · 40%'}[k],range={'bull':'KOSPI 5,950 초과~6,100','base':'KOSPI 5,750~5,950','bear':'KOSPI 5,550~5,750 미만'}[k],summary='반도체 매도와 외국인 수급 동행 확인')
write(p,json.dumps(s,ensure_ascii=False,indent=2)+'\n')
write('STATE.md','# KOSPI·KODEX 리서치 상태\n\n- 작성 PREPARED, 데이터 최종 확인 PREPARED, 한국 장전.\n- 전일 KOSPI 5937.66(-1.24%), KODEX 78550(-2.15%).\n- Intel 전망 부진·Amazon 현금 부담·PCE 상승. 전일 국내 반영 Alphabet 우려 중복 제외.\n- 다음 미국 ECI 10/30 21:30 KST.\n- 기본5750~5950(45%), 강세5950초과~6100(15%), 약세5550~5750미만(40%), 대응5/40/55.\n- reports/2026-10-30.md, research/notes/2026-10-30.md.\n- 수급 최종묶음과 정확시각 앵커 미정산.\n')
p='assets/images/articles/market-2026-10-30-cloud-capex-1200x630.png';im=Image.open(R/p);im.resize((1200,630)).save(R/p)
s=read('research/evidence/2026-10-29/finalize.py')
for a,b in [('2026-10-29','2026-10-30'),('2026-10-28','2026-10-29'),('20261029','20261030'),('2026.10.29','2026.10.30'),('2026.10.28','2026.10.29'),('6012.44','5937.66'),("'low':6100,'high':6250,'probability':.20","'low':5950,'high':6100,'probability':.15"),("'low':5900,'high':6100,'probability':.50","'low':5750,'high':5950,'probability':.45"),("'low':5700,'high':5900,'probability':.30","'low':5550,'high':5750,'probability':.40"),("'low':5500,'high':6400","'low':5350,'high':6250"),("'attack':15,'wait':50,'defense':35","'attack':5,'wait':40,'defense':55"),('=6100 if','=5950 if'),('else 5900','else 5750'),('10/29 NXT','10/30 NXT')]:s=s.replace(a,b)
s=s.replace('미국 반도체 추가상승과 국내 실적 검증','Intel 전망 부진과 반도체 시간외 약세')
write('research/evidence/2026-10-30/finalize.py',s)
for f in ['publication.py','verify_live.py','settle.py']:
 s=read('research/evidence/2026-10-29/'+f)
 if f=='settle.py':s=s.replace('2026-10-28-0833','2026-10-29-0852').replace('2026-10-28','2026-10-29').replace('20261028','20261029').replace("'realizedScenario':'bull'","'realizedScenario':'base'")
 else:s=s.replace('2026-10-29','2026-10-30').replace('2026.10.29','2026.10.30').replace('cloud-crossroads','cloud-capex')
 write('research/evidence/2026-10-30/'+f,s)
write('docs/현재작업중.md',read('docs/현재작업중.md')+'\n## 2026-10-30 KOSPI 장전 발행\n\n- 기사·목록·대시보드·STATE·보고서·취재 노트·공식 원문·전망 계약·신규 썸네일·금리차 차트 갱신.\n- Intel 전망 부진과 Amazon 현금 지출, PCE를 반영하고 전일 국내 반영분 중복 제외.\n- 회귀·Bash 훅·작업일지 가드와 최종 조회 후 배포·라이브 검증.\n')
p=P/'run-status.json';s=json.loads(p.read_text(encoding='utf-8-sig'));now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat();s['status']='검증';s['stages'].update(조사={'completedAt':now,'path':'research/notes/2026-10-30.md'},집필={'completedAt':now,'path':'articles/market-2026-10-30.html'},이미지={'completedAt':now,'path':'assets/images/articles/market-2026-10-30-cloud-capex-1200x630.png'});p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
