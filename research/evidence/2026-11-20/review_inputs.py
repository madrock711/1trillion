import json,datetime
from pathlib import Path
P=Path(__file__).parent
def load(n):return json.loads((P/n).read_text(encoding='utf-8'))
def save(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paragraph='<h2>유가 반등과 원화 약세도 부담이다</h2><p>20일 06:59:57 KST WTI 선물은 배럴당 83.16달러로 0.87%, 06:57:04 KST Brent 선물은 90.05달러로 0.99% 상승했습니다. 같은 날 07:20:12 KST 하나은행 달러/원 고시는 1,335.50원으로 전회보다 1.50원 높았습니다. 은행 고시와 서울 현물환 체결가는 구분해야 합니다. 유가와 환율이 함께 오르면 국내 기업의 비용과 외국인 수급에 부담을 더할 수 있습니다. <a href="https://finance.yahoo.com/quote/CL=F/">WTI</a> · <a href="https://finance.yahoo.com/quote/BZ=F/">Brent</a> · <a href="https://m.stock.naver.com/marketindex/exchange/FX_USDKRW">달러/원</a></p>\n'
p=P/'article-body.html';p.write_text(p.read_text(encoding='utf-8').replace('<h2>발행 기준 시세</h2>',paragraph+'<h2>발행 기준 시세</h2>'),encoding='utf-8',newline='\n')
p=P/'report-template.md';p.write_text(p.read_text(encoding='utf-8')+'\n## 유가·환율\nWTI83.16(+0.873%) 11/20 06:59:57KST, Brent90.05(+0.987%)06:57:04KST, 은행고시1335.50 07:20:12KST. 원천 collections/075816-688069.\n',encoding='utf-8',newline='\n')
save('web-observations.json',{'checkedAt':datetime.datetime.now().astimezone().isoformat(),'DRAM':{'url':'https://www.trendforce.com/price/dram/dram_spot','sourceTime':'2026-11-19 18:10 GMT+8','DDR5_16Gb':60.667,'DDR5_change':0.28,'DDR4_16Gb':78.75,'DDR4_change':-0.25},'NAND':{'url':'https://www.trendforce.com/price/flash/flash_spot','sourceTime':'2026-11-09','TLC512':14.267,'change':-11.67},'BLS':{'url':'https://www.bls.gov/schedule/2026/home.htm','event':'State Employment and Unemployment (Monthly)','time':'2026-11-20T10:00:00-05:00'},'fallback':'Python TLS/403 failures supplemented by official pages via web tool'})
package=load('package.json');package['files']+=['research/evidence/2026-11-20/review_inputs.py','research/evidence/2026-11-20/web-observations.json'];save('package.json',package)
print('reviewed')
