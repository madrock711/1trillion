import json,datetime as dt,sys,re,html
from pathlib import Path
from PIL import Image
R=Path.cwd();P=Path(__file__).parent;D='2026-11-12';PREV='2026-11-11';E=P/'collections/075858-945125';at=dt.datetime.now().astimezone().isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,t):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(t,encoding='utf-8',newline='\n')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ev(k):return load(E/(k+'.json'))
def rel(p):return str(p.relative_to(R)).replace('\\','/')
sys.path.insert(0,str(R/'scripts'));import publish_market_research as runner
prev=runner.previous_session({k:ev(k) for k in ['KOSPI','KOSPI-history','KOSPI-basic']},PREV)
title='미국 반도체주 동반 반등…코스피는 5,400 안착을 시험한다'
summary='Micron과 AMD가 크게 오르고 달러/원 고시환율은 낮아졌습니다. 이틀 연속 오른 코스피가 5,400 위에 안착하려면 외국인·프로그램 매수가 이어져야 합니다.'
sources=[('미국 정규장·시간외','https://finance.yahoo.com/quote/SMH/'),('CoreWeave 실적','https://investors.coreweave.com/news/news-details/2026/CoreWeave-Reports-Strong-Third-Quarter-2026-Results/default.aspx'),('TSMC 이사회 결의','https://pr.tsmc.com/chinese/news/3352'),('BLS 일정','https://www.bls.gov/schedule/2026/11_sched.htm'),('DRAM','https://www.trendforce.com/price/dram/dram_spot'),('NAND','https://www.trendforce.com/price/flash/flash_spot'),('국내 일봉','https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle'),('달러/원 고시','https://m.stock.naver.com/marketindex/exchange/FX_USDKRW'),('FRED','https://fred.stlouisfed.org/series/T10Y2Y')]
notes='''# 2026-11-12 취재 노트
조사 시작 07:58:19 KST. 공식 IR·BLS·TSMC 원문은 웹 도구로 재조회. 시세 21종 수집 07:58:58 이후, 원천별 requestedAt 보존.
후보 순위(직접노출/가격/새로움/신뢰/전달)
1. 미국 반도체 동반반등 3/3/2/2/2=12. SOXX+6.01, SMH+4.824, MU+11.886, AMD+7.315. 한국장 종료 후 가격변화. 국내 매수 동참이 무효화 조건.
2. 원화강세 3/2/2/2/2=11. 하나 고시1337.50,07:04:04,-7원. 현물환 체결가 아님.
3. CoreWeave 실적 재평가 3/2/1/3/2=11. 11/10 미국마감후 발표는 전일 한국장에 알려짐. 오늘은 이후 미국 정규장 가격 반응만 새 신호. 매출3661m,영업207m,이자846m,순손실709m. 예상 고객자금9bn은 실제 현금 아님.
4. DRAM 차별화 3/1/2/3/1=10. 11/11 18:10 GMT+8 DDR5 60.233 +0.11%,DDR4 79.867 -0.15%. NAND11/2 지연.
5. TSMC 이사회 3/1/0/3/1=8. 11/10 발표, Anthropic·OpenAI 각최대500m, 승인이지집행아님. 전일 국내 접할 수 있어 새 충격 중복 제외.
6. PPI 2/0/1/3/1=7. 11/13 08:30 ET=22:30KST. 오늘 발표 아님.
7. Nvidia 규제/경영진 조사 2/1/0/2/1=6. 새 공식결론없음, 기존보도반복 제외.
8. Meta-Nvidia/AMD 투자4bn 2/1/0/1/1=5. 검색에서오늘문맥이지만10/27발표. 제외.
9. 강제청산·공급계약·증자·지정학: 신규 확정1차자료 부족. 비사건 본문 미포함.
중심명제: 외부반등여건 개선과 전일국내연속상승의 중복을 분리. 반론: 높은 금융비용, 범용메모리 약세, 국내매수 부재.
전일 종가5375.36은 직전 기본5100~5300 초과, 강세범위. 수급은 최종원천부족으로 조건판정불가. 활성가설없음, 후보가중치미적용.
'''
write(R/f'research/notes/{D}.md',notes+'\n원문 확인 '+at+'\n'+'\n'.join(s+' '+u for s,u in sources))
paragraphs=[
('', '미국 반도체주가 함께 반등하면서 코스피의 추가 상승 여건이 좋아졌습니다. Micron과 AMD의 상승 폭이 컸고 원화도 강해졌습니다. 다만 코스피는 이미 이틀 연속 올랐습니다. 오늘은 갭 상승의 크기보다 5,400 위에서 외국인·프로그램 매수가 이어지는지가 중요합니다.'),
('Nvidia를 넘어 메모리와 경쟁사로 번진 반등','11일 미국 정규장에서 SOXX는 6.01%, SMH는 4.82% 올랐습니다. Micron은 11.89%, AMD는 7.32%, Broadcom은 3.99%, Nvidia는 2.92% 상승했습니다. QQQ와 TQQQ도 각각 2.32%, 6.86% 올랐습니다. 전날 업종 내 혼조에서 동반 반등으로 바뀐 점이 국내 반도체주에 유리합니다. 이 가격 변화는 수요일 한국장 마감 뒤의 새 신호입니다. <a href="https://finance.yahoo.com/quote/SMH/">미국 시세</a>'),
('AI 인프라 수요와 금융비용은 함께 커진다','CoreWeave의 3분기 매출은 36억6,100만달러, 영업이익은 2억700만달러였습니다. 반면 순이자비용은 8억4,600만달러, 순손실은 7억900만달러였습니다. 회사는 향후 3개월 고객 선급금·예치금 약 90억달러를 예상했습니다. 수요 확대를 뒷받침하는 실적이지만 자금 조달 부담도 큽니다. <a href="https://investors.coreweave.com/news/news-details/2026/CoreWeave-Reports-Strong-Third-Quarter-2026-Results/default.aspx">회사 발표</a>'),
('', '이 실적은 10일 미국장 마감 후 나와 전날 한국장에서도 접할 수 있었습니다. 오늘 새로 더해진 것은 그 뒤 미국 정규장에서 나타난 반도체 매수의 폭입니다. 같은 실적을 이틀의 독립 호재로 더하기보다 미국 매수세가 삼성전자·SK하이닉스로 이어지는지를 봐야 합니다.'),
('투자 승인과 실제 주문을 구분해야 한다','TSMC 이사회는 10일 Anthropic 보통주와 OpenAI 우선주에 각각 최대 5억달러를 투자하는 안을 승인했습니다. Anthropic 주식의 인수가격은 기업공개 가격에 따릅니다. 승인 한도가 실제 투자 완료나 메모리 주문액을 뜻하지는 않습니다. AI 고객과 공급자의 자본 연결은 수요 기반을 넓힐 수 있지만 현금 회수와 설비 집행을 함께 봐야 합니다. <a href="https://pr.tsmc.com/chinese/news/3352">TSMC</a>'),
('메모리 현물은 품목마다 다르다','TrendForce의 11일 18:10 대만시간 DRAM 현물표에서 DDR5 16Gb 평균은 60.233달러로 0.11% 올랐고 DDR4 16Gb는 79.867달러로 0.15% 내렸습니다. Micron 주가 급등을 범용 메모리 전 품목의 가격 상승으로 읽을 수는 없습니다. HBM·서버 DRAM의 장기 주문과 범용 DDR4 재고 흐름은 별도로 판단해야 합니다. <a href="https://www.trendforce.com/price/dram/dram_spot">DRAM</a>'),
('', '공개 NAND 웨이퍼 현물표의 기준일은 11월 2일이며 512Gb TLC 평균은 16.152달러입니다. SLC·MLC·TLC는 수요처와 공급 여건이 다릅니다. 이 가격을 오늘의 eSSD 계약가격이나 국내 업체의 수율 변화로 바꿔 읽기에는 시차와 품목 차이가 큽니다. <a href="https://www.trendforce.com/price/flash/flash_spot">NAND</a>'),
('전일 고가를 넘은 뒤 지킬 수 있는가','11일 코스피는 5,209.71에 출발해 5,207.44~5,377.99 사이에서 움직인 뒤 5,375.36으로 2.60% 상승 마감했습니다. KODEX 레버리지는 58,175원에 출발해 57,660~62,150원을 오간 뒤 61,995원으로 6.09% 올랐습니다. 코스피가 고가 부근에 마감한 만큼 오늘은 5,377.99 돌파 뒤 지지가 첫 관문입니다. <a href="https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=dayCandle">국내 일봉</a>'),
('', '직전 기본 전망 5,100~5,300은 상단을 넘어섰습니다. 미국 물가 부담보다 국내 반등의 힘이 강했던 결과입니다. 오늘은 그 상승을 되돌리는 위험과 미국 반도체 강세의 추가 전달을 함께 반영합니다. 외국인 현물과 KOSPI200 선물의 방향, 프로그램 비차익 매수, 반도체 밖으로의 상승 확산을 확인할 필요가 있습니다.'),
('환율은 완충, 유가는 보합권','12일 07:04:04 KST 하나은행 달러/원 고시환율은 1,337.50원으로 전회보다 7원 낮았습니다. 서울 현물환 개장 체결가와는 다릅니다. 브렌트 선물은 06:58:42 KST 92.63달러(-0.14%), WTI는 06:59:55 KST 86.42달러(-0.13%)였습니다. 원화 강세는 외국인 매수 여건을 돕지만 주식 매수 지속까지 보장하지는 않습니다. <a href="https://m.stock.naver.com/marketindex/exchange/FX_USDKRW">환율</a> · <a href="https://finance.yahoo.com/quote/BZ=F/">유가</a>'),
('세 종가 시나리오와 KODEX 기준선','기본 종가 범위는 5,300~5,500(50%)입니다. 지수가 이 범위에 머물고 외국인 현물이 순매도하지 않는 경우를 가정합니다. 5,500 초과와 외국인·프로그램 동반 순매수가 겹치면 강세 5,500 초과~5,700(30%), 5,300 미만과 두 수급의 동반 순매도가 겹치면 약세 5,050~5,300 미만(20%)입니다. 경계값은 기본 범위에 배정합니다. 범위 이탈이나 해당 수급의 반전은 각 시나리오의 무효화 기준입니다. 별도의 장중 저가·고가 포락은 4,950~5,800입니다.'),
('', '대응 점수는 공격 25·관망 50·방어 25입니다. KODEX의 1차 지지는 전일 저가 57,660원, 반등 기준은 전일 종가 61,995원, 저항은 전일 고가 62,150원입니다. 종가와 고가의 간격이 좁아 62,150원 돌파 자체보다 돌파 후 매수 지속이 중요합니다. 61,995원 아래로 되밀리면서 외국인·프로그램 매도가 커지면 추격 근거가 약해집니다.'),
('다음 확인 시점','09:30 외국인·프로그램 첫 수급, 10:30 삼성전자·SK하이닉스 저점 유지, 14:00 이후 수급 지속을 봅니다. 시나리오 조건 관측 시한은 15:20입니다. 미국 10월 PPI는 13일 08:30 ET, 한국시간 22:30 발표 예정입니다. 오늘의 반도체 반등이 물가·금리 부담을 없앴다는 뜻은 아닙니다. <a href="https://www.bls.gov/schedule/2026/11_sched.htm">BLS 일정</a>')]
old=(R/'research/evidence/2026-11-10/prepare_inputs.py').read_text(encoding='utf-8')
# 표 렌더 함수와 원장 스키마만 재사용하며 숫자는 오늘 수집 원천에서 읽는다.
tables=old[old.index('def table('):old.index('# 전일 actual')].replace('미국 11월 9일 정규장','미국 11월 11일 정규장').replace('11월 9일 미국 시간외','11월 11일 미국 시간외')
exec(tables)
actual=old[old.index('m=runner.evaluation()'):old.index("image=f'assets")].replace("'20261109'","'20261111'").replace("'realizedScenario':'base'","'realizedScenario':'bull'")
exec(actual)
image=f'assets/images/articles/market-{D}-chip-bridge-1200x630.png'
Image.open('C:/Users/madro/.codex/generated_images/01a1ccd5-29cd-78c2-8e7d-9742ad44892d/exec-d9cbe880-3dc4-420e-aa8e-f56573bbd527.png').resize((1200,630),Image.Resampling.LANCZOS).save(R/image)
scenarios={'bull':{'low':5500,'high':5700,'probability':.3},'base':{'low':5300,'high':5500,'probability':.5},'bear':{'low':5050,'high':5300,'probability':.2}};posture={'attack':25,'wait':50,'defense':25};triggers={}
for kind in scenarios:
 cs=[('floor','kospi_price','gte',5300),('cap','kospi_price','lte',5500),('foreign','foreign_cash','gte',0)] if kind=='base' else [('price','kospi_price','gt' if kind=='bull' else 'lt',5500 if kind=='bull' else 5300),('foreign','foreign_cash','gt' if kind=='bull' else 'lt',0),('program','program_total','gt' if kind=='bull' else 'lt',0)]
 triggers[kind]={'logic':'AND','observeBy':D+'T15:20:00+09:00','conditions':[{'id':kind+'-'+i,'metricId':met,'operator':oper,'threshold':v,'source':'Naver Finance KOSPI','description':kind+'-'+i} for i,met,oper,v in cs]}
dash=load(R/'research/evidence/2026-11-11/dashboard-input.json')
dash.update(headline=title,summary=summary,stance=dict(label='반도체 반등과 국내 매수 지속',note='5,400 안착과 외국인·프로그램 매수를 봅니다.',**posture),changes=[{'label':'KOSPI 전일','before':'5,239.13','after':'5,375.36','meaning':'2.60% 상승·고가 부근 마감'}],factors=[{'label':'미국 반도체','metric':'SOXX +6.01% · Micron +11.89%','detail':'11월 11일 정규장 동반 반등','tone':'positive'},{'label':'달러/원 고시','metric':'1,337.50원 · -7원','detail':'11월 12일 07:04:04 KST 하나은행','tone':'positive'}],memory=[{'label':'DDR5 16Gb','value':'$60.233','change':'11/11 +0.11%'},{'label':'DDR4 16Gb','value':'$79.867','change':'11/11 -0.15%'}],events=[{'time':'11월 13일 22:30 KST','name':'미국 10월 PPI','path':'생산비용·물가·금리'}],sources=[{'label':s,'href':u} for s,u in sources],scenarios=[])
for market in dash['markets']:market['asOf']=PREV+'T15:30:00+09:00'
for k,label,ran,cond,invalid in [('bull','강세 · 30%','5,500 초과~5,700',['5,500 초과','외국인 순매수','프로그램 순매수'],'5,500 재이탈 또는 수급 반전'),('base','기본 · 50%','5,300~5,500',['5,300 이상','5,500 이하','외국인 현물 0 이상'],'범위 이탈 또는 외국인 순매도'),('bear','약세 · 20%','5,050~5,300 미만',['5,300 미만','외국인 순매도','프로그램 순매도'],'5,300 회복 또는 수급 반전')]:dash['scenarios'].append({'id':k,'label':label,'range':'KOSPI '+ran,'summary':'09:30·10:30·14:00 확인, 15:20 관측 마감','conditions':cond,'invalidation':invalid})
dash['strategyLevels']=[{'asset':'KOSPI','support':'5,300','pivot':'5,400','resistance':'5,500'},{'asset':'KODEX 레버리지','support':'57,660원','pivot':'61,995원','resistance':'62,150원'}]
for ins,values in zip(dash['technical']['instruments'],[[5300,5400,5500],[57660,61995,62150]]):ins.update(asOf=PREV+'T15:30:00+09:00',levels=[{'label':label,'value':v} for label,v in zip(['1차 지지','반등 기준','저항'],values)],interpretation='전일 고가 돌파 뒤 국내 매수 지속을 봅니다.')
dump(P/'dashboard-input.json',dash)
state=f'# KOSPI·KODEX 리서치 상태\n- 최신 {D}. 전일KOSPI5375.36(+2.60%),KODEX61995(+6.09%).\n- 미국반도체동반반등·고시환율하락. 전일최종수급미확보.\n- 기본5300~5500(50),강세5500초과~5700(30),약세5050~5300미만(20),대응25/50/25.\n- 직전기본상단초과·강세범위, 수급조건미검증. 평가 {rel(op)}.\n- 다음11/13 22:30PPI. TSMC·CoreWeave발표자체 중복제외. 취재 research/notes/{D}.md.'
files=[image,rel(ap),rel(op),f'research/notes/{D}.md','docs/현재작업중.md']+charts+[rel(p) for p in P.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.html','.md','.raw'] and p.name not in ['run-status.json','pipeline-state.json'] and '075844-299749' not in str(p)]
package=dict(date=D,previousSessionDate=PREV,title=title,summary=summary,image=image,imageAlt='밝은 라벤더색 다리 위 은빛 웨이퍼와 두 개의 호박색 반도체 블록',bodyPath=rel(P/'article-body.html'),reportTemplate=rel(P/'report-template.md'),dashboardPath=rel(P/'dashboard-input.json'),notesPath=f'research/notes/{D}.md',scenarios=scenarios,posture=posture,pathEnvelope={'low':4950,'high':5800,'coverage':.9},marketRegime='risk_on',scenarioTriggers=triggers,drivers=[{'id':'semiconductor','rank':1,'claim':'미국 반도체 동반반등','validationMetric':'국내반도체·KOSPI·외국인'},{'id':'fx','rank':2,'claim':'원화강세 완충','validationMetric':'USD/KRW·프로그램'}],stateText=state,charts=charts,files=list(dict.fromkeys(files+[rel(P/'package.json')])));dump(P/'package.json',package)
log=R/'docs/현재작업중.md';write(log,log.read_text(encoding='utf-8')+f'\n## {D} KOSPI 장전 발행\n\n- reports/{D}.md, articles/market-{D}.html, STATE.md, 홈·목록·대시보드·사이트맵 오늘 자료 반영.\n- research/evidence/{D}/ 입력·원천·보조스크립트·package, research/notes/{D}.md, 전일 actual/outcome, 신규 chip-bridge 썸네일, charts/us_yield_spreads_*_{D}.png 보존.\n- 미국반도체동반반등과 환율완충, 기본5300~5500·대응25/50/25. 공통발행기로 검증·선별커밋·배포·양도메인 확인.\n')
status=load(P/'run-status.json');status['stages'].update(research=at,writing=at,image=at);status['artifacts']={'package':rel(P/'package.json'),'report':f'reports/{D}.md','article':f'articles/market-{D}.html'};dump(P/'run-status.json',status)
print('package ready',at)
