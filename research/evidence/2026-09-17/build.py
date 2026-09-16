"""9월 17일 취재 원고와 최종 시세를 정적 사이트에 반영한다."""
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

R = pathlib.Path(__file__).resolve().parents[3]
E = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location('previous_build', E.parent/'2026-09-16'/'build.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
TITLE = '연준 금리 인상 뒤 원화 약세, 반도체 반등의 다음 시험'
SUMMARY = '연준의 추가 긴축 신호와 원화 약세가 전날 반도체 반등을 시험합니다. KOSPI 6,600선과 외국인 수급이 오늘의 기준입니다.'
IMAGE = 'market-2026-09-17-fed-rate-memory-1200x630.webp'
OLD_TITLE = previous.TITLE
OLD_SUMMARY = previous.SUMMARY
OLD_IMAGE = previous.IMAGE
URL = 'https://www.hpmplab.com/articles/market-2026-09-17.html'
TZ = dt.timezone(dt.timedelta(hours=9))

def read(path): return (R/path).read_text(encoding='utf-8')
def write(path, value): (R/path).write_text(value, encoding='utf-8', newline='\n')
def dump(path, value): write(path, json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def ev(key): return json.loads((E/(key+'.json')).read_text(encoding='utf-8'))
def num(value): return float(str(value).replace(',', ''))
def meta(key): return ev('yahoo-'+key)['data']['chart']['result'][0]['meta']
def day(key): return next(x for x in ev(key)['data'] if x['localTradedAt']=='2026-09-16')

def main(seal):
    if seal and (E/'seal.json').exists(): raise RuntimeError('이미 봉인됨')
    now = dt.datetime.now(TZ).replace(microsecond=0)
    if not 8 <= now.hour < 9: raise RuntimeError('장전 발행 구간을 벗어남')
    issued = now.isoformat(); sid = now.strftime('%Y%m%d-%H%M'); fid = '2026-09-17-'+now.strftime('%H%M')+'-same-close'
    cutoff = max(ev(x)['fetchedAt'] for x in ('NXT','FX','yahoo-NQF','yahoo-ESF'))
    if seal and (now-dt.datetime.fromisoformat(cutoff)).total_seconds()>300: raise RuntimeError('핵심 시세가 5분보다 오래됨')
    fx=ev('FX')['data']['exchangeInfo']; nxt={x['itemCode']:x for x in ev('NXT')['data']['datas']}
    assert all(x['localTradedAt'].startswith('2026-09-17') for x in nxt.values())
    assert ev('KOSPI-basic')['data']['marketStatus']=='PREOPEN'
    body=read('research/evidence/2026-09-17/manuscript.md').split('\n',1)[1].strip()
    table='\n\n## 장전 가격\n\n|항목|가격·변화|출처 시각|\n|---|---:|---|\n'
    table+='|KOSPI 전일 종가|6,717.97 · +1.37%|2026-09-16 정규장 종가|\n'
    table+='|KODEX 레버리지 전일 종가|103,580원 · +3.90%|2026-09-16 정규장 종가|\n'
    for code,label in [('005930','삼성전자 NXT'),('000660','SK하이닉스 NXT')]:
        x=nxt[code]; table+=f"|{label}|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|\n"
    table+=f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|\n"
    for key,label in [('NQF','Nasdaq100 선물'),('ESF','S&P500 선물'),('BZF','브렌트 선물'),('CLF','WTI 선물')]:
        m=meta(key); t=dt.datetime.fromtimestamp(m['regularMarketTime'],TZ).isoformat()
        table+=f"|{label}|{m['regularMarketPrice']:,.2f} · {m['regularMarketChangePercent']:+.3f}%|{t} · 지연 시세|\n"
    table+='\n[NXT](https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660) · [환율](https://api.stock.naver.com/marketindex/exchange/FX_USDKRW) · [Nasdaq100 선물](https://finance.yahoo.com/quote/NQ=F/) · [S&P500 선물](https://finance.yahoo.com/quote/ES=F/)\n\nNXT는 대체거래소 장전 거래, 미국 선물은 지연 시세다.'
    body+=table
    old=read('articles/market-2026-09-16.html')
    prefix=old.split('<article class="editorial-article reading-article">')[0]
    prefix=prefix.replace(OLD_IMAGE,IMAGE).replace('market-2026-09-16','market-2026-09-17').replace(OLD_TITLE,TITLE).replace(OLD_SUMMARY,SUMMARY)
    prefix=re.sub(r'2026-09-16T09:11:24\+09:00',issued,prefix)
    prefix=prefix.replace('밝은 서울 아침의 메모리 칩과 웨이퍼, 유가와 금리 압력을 나타낸 금빛 곡선','밝은 서울 아침의 메모리 웨이퍼와 금리 상승선')
    schema=re.search(r'<script type="application/ld\+json">(.*?)</script>',prefix,re.S)
    if schema:
        obj=json.loads(schema[1]); obj['headline']=TITLE; obj['description']=SUMMARY; obj['image']['url']='https://www.hpmplab.com/assets/images/articles/'+IMAGE; obj['datePublished']=issued;obj['dateModified']=issued;obj['mainEntityOfPage']=URL
        prefix=prefix[:schema.start()]+f'<script type="application/ld+json">{json.dumps(obj,ensure_ascii=False)}</script>'+prefix[schema.end():]
    charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{kind}_2026-09-17.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {label}"><figcaption>9월 16일 FRED: 10년-2년 +0.27%p · 10년-3개월 +0.87%p.</figcaption></figure>' for kind,label in [('90d','최근 90일'),('long_term','최근 2년')])
    closing=old[old.index('</div></article></main>'):]
    article=prefix+f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{issued}">2026.09.17 · {now:%H:%M} KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 {now:%H:%M} KST · 데이터 최종 확인 {cutoff}. 미국 정규장은 9월 16일, 국내 NXT·환율·미국 선물은 장전 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="밝은 서울 아침의 메모리 웨이퍼와 금리 상승선"></figure></header><div class="article-body" id="article-body">'+previous.prior.prior.prior.prior.markdown_html(body).replace('table-scroll','article-table-wrap').replace('<table>','<table class="article-data-table">')+charts+closing
    write('articles/market-2026-09-17.html',article)
    report=f'# 2026-09-17 KOSPI·KODEX 일일 리서치\n\n작성 {issued} / 데이터 최종 확인 {cutoff} / 한국 장전.\n\n확정 사실은 출처 시각 기준, 시나리오와 확률은 조건부 전망이다. 9/16 KOSPI 6,717.97은 직전 강세 구간에 들어갔다.\n\n'+body+'\n\n## 직전 전망 정산\n\n'+read('research/evidence/2026-09-17/settlement-note.md')+'\n\n## 취재 근거와 확인 시각\n\n'+read('research/evidence/2026-09-17/overnight-notes.md')+'\n\n![최근 90일](../charts/us_yield_spreads_90d_2026-09-17.png)\n\n![최근 2년](../charts/us_yield_spreads_long_term_2026-09-17.png)\n'
    report+='\n## 미국 정규장 종목별 확인\n\n|종목|9/16 종가|전일 대비|고가|저가|\n|---|---:|---:|---:|---:|\n'
    for ticker in ('QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'):
        x=ev('yahoo-'+ticker)['data']['chart']['result'][0]; closes=x['indicators']['quote'][0]['close']; a,b=closes[-2:]
        report+=f"|{ticker}|{b:.2f}|{(b/a-1)*100:+.2f}%|{x['meta']['regularMarketDayHigh']:.2f}|{x['meta']['regularMarketDayLow']:.2f}|\n"
    write('reports/2026-09-17.md',report)
    d=json.loads(read('assets/data/market-dashboard-20260916-0911.json'))
    d.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff,marketState='한국 장전',sourceLabel='미국 9월 16일 정규장 · 국내 9월 16일 종가 · 9월 17일 장전',latestArticle={'title':TITLE,'href':'market-2026-09-17.html'},headline=TITLE,summary=SUMMARY)
    for market in d['markets']:
        if market['id']=='KOSPI':market.update(value=6717.97,changePercent=1.37,open=6611.24,high=6717.97,low=6598.87,previousClose=6627.26,asOf='2026-09-16T15:30:00+09:00',asOfLabel='9월 16일 종가',stateLabel='정규장 종가',flows=[]);market.pop('breadth',None)
        else:market.update(value=815.98,changePercent=.44,open=808.37,high=815.98,low=801.12,previousClose=812.41,asOf='2026-09-16T15:30:00+09:00',asOfLabel='9월 16일 종가',stateLabel='정규장 종가',flows=[])
    d['stance']={'label':'환율 확인 속 관망','attack':20,'wait':45,'defense':35,'note':'6,600선과 외국인 수급이 전날 반등을 지키는지 봅니다.'}
    d['checkpoints']=[{'label':'Nasdaq100 선물','value':f"{meta('NQF')['regularMarketPrice']:,.2f} · {meta('NQF')['regularMarketChangePercent']:+.2f}%",'detail':dt.datetime.fromtimestamp(meta('NQF')['regularMarketTime'],TZ).isoformat()+' · 지연','tone':'info'},{'label':'원/달러','value':fx['closePrice']+'원','detail':fx['localTradedAt']+' 고시','tone':'warning'},{'label':'삼성전자 NXT','value':nxt['005930']['closePrice']+'원','detail':nxt['005930']['localTradedAt'],'tone':'info'},{'label':'SK하이닉스 NXT','value':nxt['000660']['closePrice']+'원','detail':nxt['000660']['localTradedAt'],'tone':'info'}]
    d['changes']=[{'label':'KOSPI','before':'6,627.26','after':'6,717.97','meaning':'9월 16일 1.37% 반등했습니다.'},{'label':'미국 정책금리','before':'3.50~3.75%','after':'3.75~4.00%','meaning':'연준이 0.25%포인트 올렸습니다.'}]
    d['factors']=[{'label':'연준','metric':'기준금리 3.75~4.00%','detail':'9월 16일 FOMC 만장일치','tone':'warning'},{'label':'반도체','metric':'SOXX +0.64% · SMH +0.64%','detail':'9월 16일 미국 정규장','tone':'info'},{'label':'금리차','metric':'10년-2년 +0.27%p','detail':'FRED 9월 16일 · 10년-3개월 +0.87%p','tone':'info'}]
    d['flows']={'program':None,'kospi200FuturesForeign':None,'futuresUnit':'계약','futuresAsOfLabel':'장전 미개시'}
    d['memory']=[{'label':'DDR5 16Gb · 9/16 19:10 KST','value':'$54.833','change':'+0.80% 일간'},{'label':'DDR4 16Gb · 9/16 19:10 KST','value':'$87.625','change':'-1.68% 일간'},{'label':'DDR4 8Gb · 9/16 19:10 KST','value':'$45.786','change':'+0.55% 일간'}]
    d['scenarios']=[{'id':'base','label':'기본 · 50%','range':'KOSPI 6,600~6,750','summary':'전날 반등을 유지하며 환율 상승을 소화합니다.','conditions':['6,600 이상','6,750 이하','외국인 매도 축소'],'invalidation':'6,600 이탈 또는 6,750 돌파'},{'id':'bull','label':'강세 · 20%','range':'KOSPI 6,750 초과~6,900','summary':'외국인과 프로그램 매수로 반도체 반등을 이어 갑니다.','conditions':['6,750 초과','외국인 현물 순매수','프로그램 전체 순매수'],'invalidation':'6,750 아래 재진입'},{'id':'bear','label':'약세 · 30%','range':'KOSPI 6,400~6,600 미만','summary':'환율 상승과 외국인 매도에 6,600선이 밀립니다.','conditions':['6,600 미만','외국인 현물 순매도','프로그램 전체 순매도'],'invalidation':'6,600 회복'}]
    d['strategyLevels']=[{'asset':'KOSPI','support':'6,600 / 6,400','pivot':'6,750','resistance':'6,900'},{'asset':'KODEX 레버리지','support':'99,115원','pivot':'103,580원','resistance':'103,615원'}]
    d['events']=[{'time':'9월 17일 09:00 KST','name':'한국 정규장 개장','path':'환율과 외국인 수급'},{'time':'9월 17일 21:30 KST','name':'미국 신규 실업수당 청구','path':'노동시장과 금리 기대'}]
    d['checklist']=[{'id':'support','label':'KOSPI 6,600 방어'},{'id':'rebound','label':'6,750 회복과 메모리 동반 강세'},{'id':'flows','label':'외국인·프로그램 수급 동행 여부'}]
    d['technical']['note']='9월 16일 확정 일봉과 9월 17일 분석 기준선입니다.'
    for x in d['technical']['instruments']:
        levels=[6600,6750,6900] if x['id']=='KOSPI' else [99115,103580,103615]
        x.update(asOf='2026-09-16T15:30:00+09:00',asOfLabel='9월 16일 정규장 종가',levels=[{'label':label,'value':value} for label,value in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=f'1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}')
        if x['id']=='KOSPI':x['points']=[{'label':a,'value':b} for a,b in [('시가',6611.24),('고가',6717.97),('저가',6598.87),('종가',6717.97)]]
        else:x['points']=[{'label':a,'value':num(day('122630')[b])} for a,b in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]]
    d['sources']=[{'label':'연준 FOMC','href':'https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm'},{'label':'미국 정규장 SOXX','href':'https://finance.yahoo.com/quote/SOXX/'},{'label':'KOSPI 종가','href':'https://kr.investing.com/indices/kospi-historical-data'},{'label':'FRED','href':'https://fred.stlouisfed.org/series/T10Y2Y'},{'label':'TrendForce 현물','href':'https://www.trendforce.com/price/dram/dram_spot'}]
    dump('assets/data/market-dashboard-latest.json',d)
    if seal:dump('assets/data/market-dashboard-'+sid+'.json',d)
    def change(t):
        return t.replace(OLD_IMAGE,IMAGE).replace('market-2026-09-16','market-2026-09-17').replace(OLD_TITLE,TITLE).replace(OLD_SUMMARY,SUMMARY).replace('2026-09-16T09:11:24+09:00',issued).replace('2026.09.16 · 09:11','2026.09.17 · '+now.strftime('%H:%M')).replace('9월 16일 KOSPI 개장 직후','9월 17일 KOSPI 장전')
    for path,cls in [('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')]:
        t=read(path);m=re.search('<article class="'+re.escape(cls)+'"[^>]*>.*?</article>',t,re.S)
        if not m: raise RuntimeError('목록 카드 없음: '+path)
        card=m[0];t=t[:m.start()]+change(card)+'\n'+card.replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')+t[m.end():]
        def schema_change(match):
            obj=json.loads(match[1]);
            def walk(v):
                if isinstance(v,dict):
                    if v.get('@type')=='ItemList' and v.get('itemListElement'):
                        v['itemListElement'].insert(0,json.loads(change(json.dumps(v['itemListElement'][0],ensure_ascii=False))))
                        for i,item in enumerate(v['itemListElement'],1):item['position']=i
                        v['numberOfItems']=len(v['itemListElement'])
                    for value in v.values():walk(value)
                elif isinstance(v,list):
                    for value in v:walk(value)
            walk(obj);return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,indent=2)+'</script>'
        t=re.sub(r'<script type="application/ld\+json">(.*?)</script>',schema_change,t,flags=re.S)
        head,rest=t.split('</head>',1);t=head.replace(OLD_IMAGE,IMAGE)+'</head>'+rest
        if path=='articles/market.html':
            t=re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+',r'\g<1>market-2026-09-17.html',t)
            t=t.replace('KOSPI 6,500선과 외국인·프로그램 매도의 완화 여부를 함께 봅니다.','KOSPI 6,600선과 외국인·프로그램 수급의 방향을 함께 봅니다.')
            count=t.count('<article class="market-article-item"');t=re.sub(r'(일일시황 <span class="article-category-count">)\d+',r'\g<1>'+str(count),t);t=re.sub(r'최신순 · \d+편',f'최신순 · {count}편',t)
        write(path,t)
    for path in ('index.html','articles/index.html'):
        t=read(path);cats=re.findall(r'<article class="[^"]*" data-category="([^"]+)"',t)
        for cat in ('all','market','essay','health'):
            count=len(cats) if cat=='all' else cats.count(cat)
            t=re.sub(r'(data-category-count="'+cat+r'">)\d+',lambda m:m[1]+str(count),t)
        write(path,t)
    sm=read('sitemap.xml').replace('</urlset>','<url><loc>'+URL+'</loc><lastmod>2026-09-17</lastmod></url>\n</urlset>')
    for url in ('https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html'):
        sm=re.sub(r'(<loc>'+re.escape(url)+r'</loc>\s*<lastmod>)[^<]+',r'\g<1>2026-09-17',sm)
    write('sitemap.xml',sm)
    write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 {issued}, 데이터 최종 확인 {cutoff}, 한국 장전.\n- 직전 KOSPI 6,717.97(+1.37%), KODEX 103,580원(+3.90%), 9월 16일 정규장.\n- 핵심: 연준 25bp 인상과 올해 말 정책금리 전망 4.1%, 원/달러 상승. 미국 반도체 소폭 강세와 전날 한국장 반등의 후행 효과를 중복 계산하지 않는다.\n- 대응 20/45/35. 기본 6600~6750(50%), 강세 6750초과~6900(20%), 약세 6400~6600미만(30%), 경로 6300~7000(90%). KODEX 99115/103580/103615.\n- 보고서 reports/2026-09-17.md, 취재 research/evidence/2026-09-17/overnight-notes.md. 차트 charts/us_yield_spreads_90d_2026-09-17.png 및 long_term.\n- 대시보드 assets/data/market-dashboard-{sid}.json 및 latest.json. 직전 정산 research/evidence/2026-09-17/settlement-note.md.\n- 다음: 9/17 09:00 한국장 개장, 21:30 미국 신규 실업수당 청구.\n- 상위 사건과 제외 근거는 취재 노트에 보존.\n')
    if seal:
        f=json.loads(read('research/evaluation/forecasts/2026-09-16-0911-same-close.json'))
        f.update(forecastId=fid,reportPath='reports/2026-09-17.md',reportSha256=hashlib.sha256((R/'reports/2026-09-17.md').read_bytes()).hexdigest(),issuedAt=issued,dataCutoffAt=cutoff,marketState='preopen',evaluationBucket='preopen',marketRegime='risk_off',target={'sessionDate':'2026-09-17','horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-09-16'},reference={'price':6717.97,'asOf':'2026-09-16T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':6750,'high':6900,'probability':.2},'base':{'low':6600,'high':6750,'probability':.5},'bear':{'low':6400,'high':6600,'probability':.3}},pathEnvelope={'low':6300,'high':7000,'coverage':.9},posture={'attack':20,'wait':45,'defense':35},supersedes=None,drivers=[{'id':'fed-rate-fx','rank':1,'claim':'연준 인상과 원화 약세가 국내 반도체 반등의 지속성을 시험한다.','validationMetric':'USD/KRW·KOSPI·외국인 수급'},{'id':'chip-resilience','rank':2,'claim':'미국 반도체의 소폭 강세가 국내 반도체 하방을 일부 완충한다.','validationMetric':'SOXX·SMH·삼성전자·SK하이닉스'},{'id':'foreign-flow','rank':3,'claim':'6,600선과 외국인 현물·프로그램 수급이 종가 방향을 가른다.','validationMetric':'KOSPI·외국인·프로그램'}])
        for group in f['scenarioTriggers'].values():
            group['observeBy']='2026-09-17T15:20:00+09:00'
            for c in group['conditions']:
                if c['metricId']=='kospi_price':
                    c['threshold']={6650:6750,6500:6600}.get(c['threshold'],c['threshold']);c['description']='KOSPI '+str(c['threshold'])+' '+c['operator']
        f.pop('contentHash',None);f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();dump('research/evaluation/forecasts/'+fid+'.json',f)
        dump('research/evidence/2026-09-17/seal.json',{'forecastId':fid,'issuedAt':issued,'dataCutoffAt':cutoff,'snapshotId':sid})
    print('SEALED' if seal else 'DRAFT',issued,cutoff)

if __name__=='__main__': main('--seal' in sys.argv)
