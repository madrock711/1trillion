import base64,json,datetime,re,html
from pathlib import Path
R=Path('.'); p=R/'research/evidence/2026-11-02';article=R/'articles/market-2026-11-02.html';s=article.read_text(encoding='utf-8');rows=[]
for k in ['NVDA','AMD','MU','AVGO']:
 d=json.loads(base64.b64decode(json.loads((p/f'after-{k}.raw.json').read_text())['raw']))['chart']['result'][0];post=d['meta']['currentTradingPeriod']['post'];pairs=[(t,c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c and post['start']<=t<post['end']];t,c=pairs[-1];dt=datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=9)));rows.append([k,f'{c:.2f}',f"{(c/d['meta']['regularMarketPrice']-1)*100:+.2f}%",dt.strftime('%m-%d %H:%M KST')])
table='<h2>미국 시간외 최근 거래</h2><div class="article-table-wrap"><table class="article-data-table"><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in row)+'</tr>' for row in [['종목','USD','종가 대비','원천 시각']]+rows)+'</tbody></table></div><h2>미국 정규장</h2>'
s=re.sub(r'<h2>미국 시간외 최근 거래</h2>.*?<h2>미국 정규장</h2>',lambda m:table,s,flags=re.S)
s=s.replace('<h2>5,600선 지지와 반등의 조건</h2>', '<p>미국 국채 금리차는 10월 30일 기준 10년물과 2년물 사이 0.38%포인트, 10년물과 3개월물 사이 0.78%포인트였습니다. <a href="https://fred.stlouisfed.org/series/T10Y2Y">FRED 금리차</a></p><h2>5,600선 지지와 반등의 조건</h2>')
article.write_text(s,encoding='utf-8',newline='\n')
for name in ['index.html','articles/index.html','articles/market.html']:
 path=R/name;s=path.read_text(encoding='utf-8')
 def fix(m):
  d=json.loads(m[1])
  for n in d.get('@graph',[d]):
   for item in n.get('mainEntity',{}).get('itemListElement',[]):
    u=item.get('url','');mo=re.search(r'/articles/(market-[\d-]+\.html)$',u)
    if not mo:continue
    ap=R/'articles'/mo.group(1)
    if not ap.exists():continue
    body=ap.read_text(encoding='utf-8');img=re.search(r'<meta property="og:image" content="([^"]+)',body)
    if img and 'image' in item and isinstance(item['image'],dict):item['image']['url']=img.group(1)
  return '<script type="application/ld+json">'+json.dumps(d,ensure_ascii=False,indent=2)+'</script>'
 s=re.sub(r'<script type="application/ld\+json">(.*?)</script>',fix,s,flags=re.S);path.write_text(s,encoding='utf-8',newline='\n')
