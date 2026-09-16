"""검증된 취재 노트와 원시 시세로 9월 16일 공개판을 조립한다."""
import datetime, hashlib, importlib.util, json, pathlib, re, subprocess, sys
R=pathlib.Path(__file__).resolve().parents[3]; E=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('prior',E.parent/'2026-09-15/build.py'); prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
TITLE='유가와 5% 금리의 압력, 반도체 반등은 약했다'
SUMMARY='유가 급등과 미 10년물 5% 돌파가 지수 상단을 누릅니다. 반도체의 제한적 반등보다 KOSPI 6,500선과 외국인 수급을 확인할 때입니다.'
IMAGE='market-2026-09-16-oil-yields-chip-stabilization-1200x630.webp'
OLD_PUBLIC_SUMMARY='미국 반도체 ETF가 5% 안팎 급락한 뒤 국내 메모리주는 장전부터 등락을 거듭하고 있습니다. KOSPI 6,650선 방어와 외국인 매도 완화가 반등의 지속성을 가릅니다.'
OLD_SCHEMA_SUMMARY='미국 반도체 ETF는 올랐지만 Nvidia와 Micron은 하락했습니다. 유가 부담 속에서 국내 메모리주 반등이 지수 전반으로 이어지는지가 관건입니다.'
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,t):(R/p).write_text(t,encoding='utf-8',newline='\n')
def dump(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ev(n):return json.loads((E/(n+'.json')).read_text(encoding='utf-8'))
def base(p):return subprocess.check_output(['git','show','HEAD:'+p],cwd=R).decode('utf-8')
def num(x):return float(str(x).replace(',',''))
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
def main(seal):
    assert not (E/'seal.json').exists(),'봉인 뒤에는 새 판본을 만든다.'
    stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).replace(microsecond=0)
    assert stamp.hour==9 and stamp.minute<=30,'09:30 이후에는 다음 장중 평가 구간으로 새로 작성해야 한다.'
    issued=stamp.isoformat(); sid=stamp.strftime('%Y%m%d-%H%M'); fid='2026-09-16-'+stamp.strftime('%H%M')+'-same-close'
    cutoff=max(ev(n)['fetchedAt'] for n in ('KOSPI-basic','KOSDAQ-basic','KOSPI-integration','122630','005930','000660','FX','yahoo-NQF','yahoo-ESF','yahoo-BZF','yahoo-CLF'))
    if seal:
        assert (stamp-datetime.datetime.fromisoformat(cutoff)).total_seconds()<180
        assert (E/'settlement-note.md').exists()
    nxt={x['itemCode']:x for x in ev('NXT')['data']['datas']}; fx=ev('FX')['data']['exchangeInfo']
    for x in nxt.values():assert x['localTradedAt'].startswith('2026-09-16') and x['marketSessionType']=='regularMarket'
    kospi=next(x for x in ev('KOSPI')['data'] if x['localTradedAt']=='2026-09-15');kosdaq=next(x for x in ev('KOSDAQ')['data'] if x['localTradedAt']=='2026-09-15')
    kodex=next(x for x in ev('122630')['data'] if x['localTradedAt']=='2026-09-15')
    assert kospi['localTradedAt']==kosdaq['localTradedAt']=='2026-09-15'
    live=ev('KOSPI-basic')['data']; liveq=ev('KOSDAQ-basic')['data']; flows=ev('KOSPI-integration')['data']
    live_day=next(x for x in ev('KOSPI')['data'] if x['localTradedAt']=='2026-09-16'); liveq_day=next(x for x in ev('KOSDAQ')['data'] if x['localTradedAt']=='2026-09-16')
    assert live['marketStatus']=='OPEN' and liveq['marketStatus']=='OPEN'
    body=read('research/evidence/2026-09-16/manuscript.md').split('\n',1)[1].strip()
    table='## 개장 직후 가격\n\n|항목|가격·변화|출처 시각|\n|---|---:|---|\n'
    table+=f"|KOSPI|{live['closePrice']} · {live['fluctuationsRatio']}%|{live['localTradedAt']}|\n"
    table+=f"|KOSDAQ|{liveq['closePrice']} · {liveq['fluctuationsRatio']}%|{liveq['localTradedAt']}|\n"
    for code,label in [('122630','KODEX 레버리지'),('005930','삼성전자'),('000660','SK하이닉스')]:
        x=ev(code)['data'][0];table+=f"|{label}|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{live['localTradedAt']}|\n"
    table+=f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|\n"
    for key,label in [('NQF','Nasdaq100 선물'),('ESF','S&P500 선물'),('BZF','브렌트 선물'),('CLF','WTI 선물')]:
        m=ev('yahoo-'+key)['data']['chart']['result'][0]['meta']; t=datetime.datetime.fromtimestamp(m['regularMarketTime'],stamp.tzinfo).isoformat()
        table+=f"|{label}|{m['regularMarketPrice']:,.2f} · {m['regularMarketChangePercent']:+.3f}%|{t} · 지연 시세|\n"
    table+='\n[KOSPI](https://m.stock.naver.com/api/index/KOSPI/basic) · [KODEX](https://m.stock.naver.com/api/stock/122630/price?pageSize=10&page=1) · [환율](https://api.stock.naver.com/marketindex/exchange/FX_USDKRW) · [Nasdaq100 선물](https://finance.yahoo.com/quote/NQ=F/) · [S&P500 선물](https://finance.yahoo.com/quote/ES=F/) · [브렌트](https://finance.yahoo.com/quote/BZ=F/) · [WTI](https://finance.yahoo.com/quote/CL=F/)\n\n국내 가격은 개장 직후 스냅샷, 환율은 은행 고시, 미국 선물은 지연 시세다.'
    body+='\n\n'+table
    old=base('articles/market-2026-09-15.html'); oldtitle=re.search('<h1>(.*?)</h1>',old).group(1)
    oldimage='market-2026-09-15-ai-braking-1200x630.webp'
    oldsummary=prior.SUMMARY
    def update(t):
        t=re.sub(r'2026-09-15T08:[0-9:]+\+09:00',issued,t)
        t=t.replace(oldtitle,TITLE).replace(oldsummary,SUMMARY).replace(OLD_PUBLIC_SUMMARY,SUMMARY).replace(OLD_SCHEMA_SUMMARY,SUMMARY).replace(oldimage,IMAGE).replace('2026-09-15','2026-09-16')
        t=re.sub(r'2026\.09\.15 · \d{2}:\d{2} KST','2026.09.16 · '+stamp.strftime('%H:%M')+' KST',t)
        t=re.sub(r'2026년 9월 \d+일 KOSPI 개장 전 시황', '2026년 9월 16일 KOSPI 개장 직후 시황',t)
        t=re.sub(r'9월 \d+일 KOSPI 개장 전 시황 읽기','9월 16일 KOSPI 개장 직후 시황 읽기',t)
        t=t.replace('AI 서버와 메모리 칩 사이의 빛을 늦추는 호박색 장벽','밝은 서울 아침의 메모리 칩과 웨이퍼, 유가와 금리 압력을 나타낸 금빛 곡선')
        return t
    prefix=update(old.split('<article class="editorial-article reading-article">')[0])
    prefix=re.sub(r'(<meta (?:name="description"|property="og:description"|name="twitter:description") content=")[^"]+',lambda m:m[1]+SUMMARY,prefix)
    prefix=re.sub(r'("description":\s*")[^"]+',lambda m:m[1]+SUMMARY,prefix)
    prefix=re.sub(r'(property="article:(?:published|modified)_time" content=")[^"]+',lambda m:m[1]+issued,prefix)
    prefix=re.sub(r'("date(?:Published|Modified)":\s*")[^"]+',lambda m:m[1]+issued,prefix)
    prefix=re.sub(r'(property="og:image:alt" content=")[^"]+',r'\g<1>밝은 서울 아침의 메모리 칩과 웨이퍼, 유가와 금리 압력을 나타낸 금빛 곡선',prefix)
    prefix=prefix.replace('</head>','<style>.article-body .table-scroll{max-width:100%;overflow-x:auto}</style></head>')
    closing=old[old.index('</div></article></main>'):]
    charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{k}_2026-09-16.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {label}"><figcaption>9월 15일 FRED: 10년-2년 +0.33%p · 10년-3개월 +0.89%p.</figcaption></figure>' for k,label in [('90d','최근 90일'),('long_term','최근 2년')])
    article=prefix+f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{issued}">2026.09.16 · {stamp.strftime("%H:%M")} KST</time><span>개장 직후 브리핑</span></div><p class="article-disclosure">작성 {stamp.strftime("%H:%M")} KST · 데이터 최종 확인 {cutoff}. 미국 정규장은 9월 15일, 국내 가격은 개장 직후 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="밝은 서울 아침의 메모리 칩과 웨이퍼, 유가와 금리 압력을 나타낸 금빛 곡선"></figure></header><div class="article-body" id="article-body">'+prior.prior.prior.prior.markdown_html(body).replace('table-scroll','article-table-wrap').replace('<table>','<table class="article-data-table">')+charts+closing
    write('articles/market-2026-09-16.html',article)
    report=f'# 2026-09-16 KOSPI·KODEX 일일 리서치\n\n작성 {issued} / 데이터 최종 확인 {cutoff} / 한국 개장 직후.\n\n확정 수치는 출처 시각 기준이다. 시나리오·확률·대응점수는 조건부 분석이다. 전일 종가 6,627.26은 직전 약세 구간에 들어갔다. 확정 일봉과 수급 원문 대조는 아래 정산 기록에 보존한다.\n\n'+body+'\n\n## 직전 전망 정산\n\n'+(read('research/evidence/2026-09-16/settlement-note.md') if (E/'settlement-note.md').exists() else '정산 진행 중: 공개 봉인 전에 확정한다.')+'\n\n## 취재 근거와 확인 시각\n\n'+read('research/evidence/2026-09-16/overnight-notes.md')+'\n\n![최근 90일](../charts/us_yield_spreads_90d_2026-09-16.png)\n\n![최근 2년](../charts/us_yield_spreads_long_term_2026-09-16.png)\n'
    report+='\n## 미국 정규장 고저·시간외 원천\n\n|종목|종가|고가|저가|고가 대비 종가|\n|---|---:|---:|---:|---:|\n'
    for ticker in ('QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'):
        m=ev('yahoo-'+ticker)['data']['chart']['result'][0]['meta']
        report+=f"|{ticker}|{m['regularMarketPrice']}|{m['regularMarketDayHigh']}|{m['regularMarketDayLow']}|{(m['regularMarketPrice']/m['regularMarketDayHigh']-1)*100:.2f}%|\n"
    report+='\n미국 9월 15일 정규장 기준. 각 yahoo-*.json에 조회 시각·URL·원문 해시를 보존했다. 시간외는 취재 노트의 별도 시각·가격을 사용한다.\n'
    write('reports/2026-09-16.md',report)
    d=json.loads(base('assets/data/market-dashboard-latest.json'))
    d.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff,marketState='한국 개장 직후',sourceLabel='미국 9월 15일 정규장 · 국내 9월 16일 개장 직후',latestArticle={'title':TITLE,'href':'market-2026-09-16.html'},headline=TITLE,summary=SUMMARY)
    for m in d['markets']:
        x=live if m['id']=='KOSPI' else liveq
        day=live_day if m['id']=='KOSPI' else liveq_day
        prev=kospi if m['id']=='KOSPI' else kosdaq
        m.update(value=num(x['closePrice']),changePercent=num(x['fluctuationsRatio']),open=num(day['openPrice']),high=num(day['highPrice']),low=num(day['lowPrice']),previousClose=num(prev['closePrice']),asOf=x['localTradedAt'],asOfLabel='9월 16일 개장 직후',stateLabel='장중',flows=[]);m.pop('breadth',None)
    d['markets'][0]['flows']=[{'label':'개인','value':num(flows['dealTrendInfo']['personalValue'])},{'label':'외국인','value':num(flows['dealTrendInfo']['foreignValue'])},{'label':'기관','value':num(flows['dealTrendInfo']['institutionalValue'])}]
    d['markets'][0]['breadth']={'rise':int(flows['upDownStockInfo']['riseCount']),'steady':int(flows['upDownStockInfo']['steadyCount']),'fall':int(flows['upDownStockInfo']['fallCount'])}
    d['stance']={'label':'방어적 관망','attack':15,'wait':40,'defense':45,'note':'유가·금리 부담 속 6,500선과 외국인 매도 완화를 확인합니다.'}
    d['checkpoints']=[]
    for key,label in [('BZF','브렌트 선물'),('NQF','Nasdaq100 선물')]:
        m=ev('yahoo-'+key)['data']['chart']['result'][0]['meta']
        d['checkpoints'].append({'label':label,'value':f"{m['regularMarketPrice']:,.2f} · {m['regularMarketChangePercent']:+.2f}%",'detail':datetime.datetime.fromtimestamp(m['regularMarketTime'],stamp.tzinfo).isoformat()+' · 지연','tone':'warning'})
    d['checkpoints'] += [{'label':'원/달러','value':fx['closePrice']+'원','detail':fx['localTradedAt']+' 고시','tone':'info'},{'label':'메모리 NXT','value':f"삼성 {nxt['005930']['fluctuationsRatio']}% · 하이닉스 {nxt['000660']['fluctuationsRatio']}%",'detail':nxt['005930']['localTradedAt'],'tone':'warning'}]

    d['changes']=[{'label':'KOSPI','before':'6,684.37','after':'6,627.26','meaning':'9월 15일 0.85% 하락했습니다.'},{'label':'미국 반도체','before':'전일 급락','after':'SOXX +0.29%','meaning':'소폭 반등했지만 전날 낙폭을 되돌리지 못했습니다.'}]
    d['factors']=[{'label':'유가·금리','metric':'WTI +4.4% · 10년물 5% 돌파','detail':'9월 15일 미국 정규장','tone':'warning'},{'label':'반도체','metric':'SOXX +0.29% · SMH +0.11%','detail':'급락 뒤 제한적 반등','tone':'info'},{'label':'금리차','metric':'10년-2년 +0.33%p','detail':'FRED 9월 15일 · 10년-3개월 +0.89%p','tone':'info'}]
    d['flows']={'program':{'arbitrage':num(flows['programTrendInfo']['indexDifferenceReal']),'nonArbitrage':num(flows['programTrendInfo']['indexBiDifferenceReal']),'total':num(flows['programTrendInfo']['indexTotalReal']),'unit':'억원'},'kospi200FuturesForeign':None,'futuresUnit':'계약','futuresAsOfLabel':live['localTradedAt']}
    d['memory']=[{'label':'DDR5 16Gb · 9/15 19:10 KST','value':'$54.400','change':'+0.12% 일간'},{'label':'DDR4 16Gb · 9/15 19:10 KST','value':'$89.125','change':'-0.14% 일간'},{'label':'DDR4 8Gb · 9/15 19:10 KST','value':'$45.536','change':'-0.08% 일간'}]
    d['scenarios']=[{'id':'base','label':'기본 · 45%','range':'KOSPI 6,500~6,650','summary':'6,500선을 지키며 유가·금리 부담을 소화합니다.','conditions':['6,500 이상','6,650 이하','외국인 순매도 1조원 이내'],'invalidation':'6,500 이탈 또는 6,650 돌파'}, {'id':'bull','label':'강세 · 20%','range':'KOSPI 6,650 초과~6,800','summary':'메모리주 반등과 외국인 매수로 6,650선을 회복합니다.','conditions':['6,650 초과','외국인 현물 순매수','프로그램 전체 순매수'],'invalidation':'6,650 아래 재진입'}, {'id':'bear','label':'약세 · 35%','range':'KOSPI 6,300~6,500 미만','summary':'유가·금리 부담과 매도가 겹치며 6,500 아래로 밀립니다.','conditions':['6,500 미만','외국인 현물 순매도','프로그램 전체 순매도'],'invalidation':'6,500 회복'}]
    d['strategyLevels']=[{'asset':'KOSPI','support':'6,500 / 6,300','pivot':'6,650','resistance':'6,800'},{'asset':'KODEX 레버리지','support':'98,695원','pivot':'99,690원','resistance':'103,230원'}]
    d['events']=[{'time':'9월 16일 21:30 KST','name':'미국 8월 소매판매','path':'소비와 금리 기대'},{'time':'9월 17일 03:00 KST','name':'FOMC·경제전망','path':'정책금리와 장기금리'}]
    d['checklist']=[{'id':'support','label':'KOSPI 6,500 방어'},{'id':'rebound','label':'6,650 회복과 메모리 동반 반등'},{'id':'flows','label':'외국인·프로그램 순매수 동반 여부'}]
    d['technical']['note']='9월 15일 확정 일봉과 9월 16일 분석 기준선입니다.'
    for x in d['technical']['instruments']:
        row=kospi if x['id']=='KOSPI' else kodex; levels=[6500,6650,6800] if x['id']=='KOSPI' else [98695,99690,103230]
        x.update(asOf='2026-09-15T15:30:00+09:00',asOfLabel='9월 15일 정규장 종가',points=[{'label':l,'value':num(row[k])} for l,k in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]],levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=f'1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}')
    d['sources']=[{'label':'KOSPI 장중','href':ev('KOSPI-basic')['url']},{'label':'Reuters 미국장','href':'https://www.reuters.com/business/wall-st-futures-slip-rising-oil-treasury-yields-compound-ai-anxiety-2026-09-15/'},{'label':'연준 FOMC','href':'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'},{'label':'FRED','href':'https://fred.stlouisfed.org/series/T10Y2Y'}]
    d['sources'].append({'label':'TrendForce 현물','href':'https://www.trendforce.com/price/dram/dram_spot'})
    dump('assets/data/market-dashboard-latest.json',d)
    if seal:dump('assets/data/market-dashboard-'+sid+'.json',d)
    for path,cls in [('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')]:
        t=base(path); m=re.search('<article class="'+re.escape(cls)+'"[^>]*>.*?</article>',t,re.S); assert m
        card=m.group();t=t[:m.start()]+update(card)+'\n'+card.replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')+t[m.end():]
        def schema(m):
            o=json.loads(m[1])
            def walk(v):
                if isinstance(v,dict):
                    if v.get('@type')=='ItemList' and v.get('itemListElement'):
                        v['itemListElement'].insert(0,json.loads(update(json.dumps(v['itemListElement'][0],ensure_ascii=False))))
                        for i,x in enumerate(v['itemListElement'],1):x['position']=i
                        v['numberOfItems']=len(v['itemListElement'])
                    for x in v.values():walk(x)
                elif isinstance(v,list):
                    for x in v:walk(x)
            walk(o);return '<script type="application/ld+json">'+json.dumps(o,ensure_ascii=False,indent=2)+'</script>'
        t=re.sub(r'<script type="application/ld\+json">(.*?)</script>',schema,t,flags=re.S)
        head,rest=t.split('</head>',1);t=head.replace(oldimage,IMAGE)+'</head>'+rest
        if path=='articles/market.html':
            t=t.replace('미국 반도체 급락 뒤 국내 메모리주와 외국인 매도 흐름이 지수 방향을 가릅니다.','유가 급등과 장기금리 5% 돌파가 지수 상단을 누릅니다.')
            t=t.replace('KOSPI 6,650선 방어와 외국인·프로그램 매도의 완화 여부를 함께 봅니다.','KOSPI 6,500선과 외국인·프로그램 매도의 완화 여부를 함께 봅니다.')
            t=t.replace('반도체 급락 뒤 확인할 국내 수급','유가·금리 압력 아래 확인할 국내 수급')
            t=re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+',r'\g<1>market-2026-09-16.html',t)
            count=t.count('<article class="market-article-item"');t=re.sub(r'(일일시황 <span class="article-category-count">)\d+',r'\g<1>'+str(count),t);t=re.sub(r'최신순 · \d+편',f'최신순 · {count}편',t)
        write(path,t)
    for path in ['index.html','articles/index.html']:
        t=read(path); cats=re.findall(r'<article class="[^"]*" data-category="([^"]+)"',t)
        for cat in ['all','market','essay','health']:
            count=len(cats) if cat=='all' else cats.count(cat)
            t=re.sub(r'(data-category-count="'+cat+r'">)\d+',lambda m:m[1]+str(count),t)
        write(path,t)
    sm=base('sitemap.xml').replace('</urlset>','<url><loc>https://www.hpmplab.com/articles/market-2026-09-16.html</loc><lastmod>2026-09-16</lastmod></url>\n</urlset>')
    for url in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:
        sm=re.sub(r'(<loc>'+re.escape(url)+r'</loc>\s*<lastmod>)[^<]+',r'\g<1>2026-09-16',sm)
    write('sitemap.xml',sm)
    write('STATE.md',f"# KOSPI·KODEX 리서치 상태\n\n- 작성 {issued}, 데이터 최종 확인 {cutoff}, 한국 개장 직후.\n- 직전 KOSPI 6,627.26(-0.85%), KODEX 99,690원(-2.36%), 9월 15일 정규장.\n- 핵심: WTI +4.4%, 미 10년물 5% 돌파와 FOMC 금리 인상 전망이 상단을 누른다. 미국 반도체의 전날 급락은 한국장 선반영분을 중복 계산하지 않는다.\n- 대응 15/40/45. 기본 6500~6650(45%), 강세 6650초과~6800(20%), 약세 6300~6500미만(35%), 경로 6200~6900(90%). KODEX 98695/99690/103230.\n- 다음: 9/16 소매판매·수출입물가 21:30, 9/17 FOMC 03:00 KST.\n- 보고서 reports/2026-09-16.md, 취재 research/evidence/2026-09-16/overnight-notes.md. 차트 charts/us_yield_spreads_90d_2026-09-16.png 및 long_term.\n- 대시보드 assets/data/market-dashboard-{sid}.json 및 latest.json.\n- 직전 정산 research/evidence/2026-09-16/settlement-note.md, 누적 research/evaluation/generated/latest.md.\n- 장중 KOSPI {live['closePrice']}({live['fluctuationsRatio']}%), KODEX {ev('122630')['data'][0]['closePrice']}원({ev('122630')['data'][0]['fluctuationsRatio']}%); 원/달러 {fx['closePrice']}원({fx['localTradedAt']}).\n- 상위 사건과 제외 근거는 overnight-notes.md에 보존.\n")
    if seal:
        f=json.loads(read('research/evaluation/forecasts/2026-09-15-0817-same-close.json'))
        f.update(forecastId=fid,reportPath='reports/2026-09-16.md',reportSha256=sha('reports/2026-09-16.md'),issuedAt=issued,dataCutoffAt=cutoff,marketState='intraday',evaluationBucket='open_0900_0930',marketRegime='risk_off',target={'sessionDate':'2026-09-16','horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-09-15'},reference={'price':num(live['closePrice']),'asOf':live['localTradedAt'],'kind':'live'},scenarios={'bull':{'low':6650,'high':6800,'probability':.2},'base':{'low':6500,'high':6650,'probability':.45},'bear':{'low':6300,'high':6500,'probability':.35}},pathEnvelope={'low':6200,'high':6900,'coverage':.9},posture={'attack':15,'wait':40,'defense':45},supersedes=None,drivers=[{'id':'oil-yield-pressure','rank':1,'claim':'유가 급등과 미국 10년물 5% 돌파가 국내 성장주와 반도체 상단을 제약한다.','validationMetric':'WTI·미 10년물·KOSPI'}, {'id':'limited-chip-rebound','rank':2,'claim':'미국 반도체의 제한적 반등이 전날 급락을 되돌리지 못했다.','validationMetric':'SOXX·SMH·삼성전자·SK하이닉스'}, {'id':'domestic-flow-confirmation','rank':3,'claim':'6,500선과 외국인·프로그램 수급이 종가 방향을 가른다.','validationMetric':'KOSPI·외국인 현물·프로그램 전체'}])
        for group in f['scenarioTriggers'].values():
            group['observeBy']='2026-09-16T15:20:00+09:00'
            for c in group['conditions']:
                if c['metricId']=='kospi_price':
                    c['threshold']={6800:6650,6650:6500}.get(c['threshold'],c['threshold'])
                    c['description']='KOSPI '+str(c['threshold'])+' '+c['operator']
        f.pop('contentHash',None);f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();dump('research/evaluation/forecasts/'+fid+'.json',f)
        files=['articles/market-2026-09-16.html','assets/data/market-dashboard-latest.json','assets/data/market-dashboard-'+sid+'.json','assets/images/articles/'+IMAGE,'charts/us_yield_spreads_90d_2026-09-16.png','charts/us_yield_spreads_long_term_2026-09-16.png','index.html','articles/index.html','articles/market.html','sitemap.xml']
        dump('research/evidence/2026-09-16/seal.json',{'forecastId':fid,'issuedAt':issued,'dataCutoffAt':cutoff,'snapshotId':sid,'files':files})
    print('SEALED' if seal else 'DRAFT',issued,cutoff)
if __name__=='__main__':main('--seal' in sys.argv)
