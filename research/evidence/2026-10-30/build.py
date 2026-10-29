import json,re,datetime,base64
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent
def read(p):return (R/p).read_text(encoding='utf-8-sig')
def write(p,s):(R/p).write_text(s,encoding='utf-8',newline='\n')
s=read('research/evidence/2026-10-29/prepare.py')
for a,b in [('2026-10-29','2026-10-30'),('2026-10-28','2026-10-29'),('20261028','20261029'),('2026.10.29','2026.10.30'),('2026.10.28','2026.10.29'),('6012.44','5937.66'),('80280','78550'),('6.63','-1.24'),('14.76','-2.15'),('5638.34','6012.44'),('cloud-crossroads','cloud-capex'),('earnings-curtain','cloud-crossroads')]:s=s.replace(a,b)
s=re.sub(r"TITLE=.*", "TITLE='Amazon 성장에도 커진 AI 투자 부담…5,900선 지지 시험'",s,count=1)
s=re.sub(r"SUMMARY=.*", "SUMMARY='Amazon의 클라우드 성장에도 현금 지출 부담이 커졌고 미국 반도체주가 하락했습니다. KOSPI는 5,900선 지지와 외국인 매수 복귀를 시험합니다.'",s,count=1)
s=re.sub(r"ALT=.*", "ALT='밝은 책상 위 메모리 칩이 받치는 청록색 구름과 무거운 호박색 유리 추'",s,count=1) if s.startswith('ALT=') else s
start=s.index("notes='''");end=s.index("body='''",start);s=s[:start]+s[end:]
start=s.index("body='''");end=s.index("write('research/evidence/",start)
body='''<p>KOSPI가 5,937.66으로 1.24% 하락한 뒤 미국 기술주도 밀렸습니다. Amazon은 클라우드 매출을 크게 늘렸지만 AI 인프라 지출이 현금흐름을 압박했습니다. 오늘은 성장률보다 그 성장을 뒷받침하는 비용과 국내 반도체 매수세가 관건입니다.</p><h2>클라우드 성장과 현금 지출의 간격</h2><p>Amazon의 3분기 AWS 매출은 460억달러로 전년보다 39.3% 증가했습니다. 최근 12개월 잉여현금흐름은 마이너스 424억달러였습니다. 연간 현금 설비투자 계획 2,200억달러는 유지됐습니다. 지출 확대를 이미 예상했어도 현금 회수까지의 시간이 길어지면 주가에는 부담이 됩니다. <a href="https://ir.aboutamazon.com/quarterly-results/default.aspx">Amazon 실적</a></p><h2>반도체 약세와 물가 부담</h2><p>미국 정규장에서 SOXX는 1.55%, SMH는 1.06% 내렸고 Micron은 4.98% 하락했습니다. 미국 3분기 GDP는 연율 3.4% 성장했고 9월 PCE 물가는 전월보다 0.5%, 전년보다 3.6% 올랐습니다. 견조한 성장과 높은 물가가 함께 나타나면서 금리 부담도 이어집니다. <a href="https://www.bea.gov/">BEA 발표</a></p><p>전일 한국장에 반영된 Alphabet 실적 우려와 미국장의 후행 반응을 다시 같은 크기의 충격으로 더할 수는 없습니다. 한국장 마감 뒤 나온 Amazon 실적과 시간외 반도체 약세가 오늘 새로 소화할 변수입니다. 메모리 현물 가격과 주식의 투자비·할인율 부담은 별도로 봐야 합니다.</p><h2>5,900선과 외국인 매수 복귀</h2><p>기본 종가 범위는 5,750~5,950(45%)입니다. 5,950선을 넘고 외국인·프로그램이 함께 순매수하면 5,950 초과~6,100(15%)을 봅니다. 5,750선 아래에서 매도가 동행하면 5,550~5,750 미만(40%)으로 낮춰 봅니다. 기본 범위를 이탈하면 해당 판단은 무효이며 다음 확인은 09:30, 10:00, 14:00입니다.</p><p>KODEX 레버리지는 75,200원을 첫 지지, 78,550원을 반등 기준, 80,595원을 저항으로 봅니다. 75,200원을 이탈한 뒤 회복하지 못하면 지지 판단을 접습니다. 공격 5·관망 40·방어 55로 두고, 환율 상승과 미국 선물 약세가 국내 반도체 매도로 이어지는지 확인합니다. 오늘 21:30 KST 미국 고용비용지수도 금리 기대에 영향을 줄 일정입니다.</p>'''
s=s[:start]+'body='+repr(body)+'\n'+s[end:]
start=s.index("report=f'''");end=s.index("write('reports/",start)
s=s[:start]+'''report=f"# {DATE} KOSPI·KODEX 장전 리서치\\n작성 PREPARED / 데이터 최종 확인 PREPARED\\n\\n"+read('research/notes/'+DATE+'.md')+'\\n## 미국 정규장\\n|종목|종가 USD|등락|\\n|---|---:|---:|\\n'+ustable+'\\n## 시간외\\n'+aftertable+'\\n## 발행 직전 조회\\nFAST_TABLE\\n## 조건부 전망\\n기본5750~5950(45%), 강세5950초과~6100(15%), 약세5550~5750미만(40%). 강세: 지수>5950 AND 외국인>0 AND 프로그램>0. 기본: 지수>=5750 AND <=5950 AND 외국인>=-8000억원. 약세: 지수<5750 AND 외국인<0 AND 프로그램<0. 관측15:20, 범위재진입/이탈시무효. 다음09:30/10:00/14:00. 경로90%포락5350~6250. 대응5/40/55. KODEX75200/78550/80595. 수급확정묶음과앵커미확인.\\n'+f'![90일](../charts/us_yield_spreads_90d_{DATE}.png)\\n![2년](../charts/us_yield_spreads_long_term_{DATE}.png)\\n'
'''+s[end:]
for a,b in [('5900','5750'),('6100','5950'),('6250','6100'),('5700','5550'),('78000','75200'),('81010','80595')]:s=s.replace(a,b)
s=s.replace("'attack':15,'wait':50,'defense':35","'attack':5,'wait':40,'defense':55")
s=s.replace("dump('research/evidence/", "dump('research/evidence/",1)
write('research/evidence/2026-10-30/prepared-script.py',s)
exec(compile(s,str(P/'prepared-script.py'),'exec'))
