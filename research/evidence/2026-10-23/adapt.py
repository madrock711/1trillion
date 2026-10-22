from pathlib import Path
P=Path(__file__).parent;O=P.parent/'2026-10-22'
s=(O/'finalize.py').read_text(encoding='utf-8-sig')
for a,b in [('20261022','20261023'),('2026-10-22','2026-10-23'),('2026-10-21','2026-10-22'),('2026.10.20','2026.10.23'),('2026.10.22','2026.10.23'),('0804-same-close','0808-same-close'),('5735.66','5533.77')]:s=s.replace(a,b)
s=s.replace("'low':5800,'high':5950,'probability':.20","'low':5550,'high':5700,'probability':.15").replace("'low':5600,'high':5800,'probability':.50","'low':5350,'high':5550,'probability':.45").replace("'low':5350,'high':5600,'probability':.30","'low':5100,'high':5350,'probability':.40")
s=s.replace("'low':5250,'high':6100","'low':4950,'high':5850").replace("'attack':15,'wait':50,'defense':35","'attack':5,'wait':40,'defense':55").replace("5800 if k=='bull' or c['operator']=='lte' else 5600","5550 if k=='bull' or c['operator']=='lte' else 5350").replace('Nvidia 공급망 확대와 시간외 약세','Meta 투자비 부담과 반도체 급락').replace('금통위 뒤 국내 매수 지속','전일 저점 방어와 국내 매수 지속').replace('10/21 NXT OPEN','10/23 NXT OPEN')
(P/'finalize.py').write_text(s,encoding='utf-8',newline='\n')
s=(O/'settle.py').read_text(encoding='utf-8-sig').replace('20261021','20261022').replace('2026-10-22','2026-10-23').replace('2026-10-21','2026-10-22').replace('0804-same-close','0808-same-close').replace("realizedScenario':'bull","realizedScenario':'bear")
(P/'settle.py').write_text(s,encoding='utf-8',newline='\n')
for name in ['publication.py','verify_live.py']:
 s=(O/name).read_text(encoding='utf-8-sig').replace('2026-10-22','2026-10-23').replace('2026.10.22','2026.10.23').replace('ai-capacity-bok','ai-cash-oil')
 (P/name).write_text(s,encoding='utf-8',newline='\n')
