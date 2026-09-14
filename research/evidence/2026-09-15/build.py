"""검증된 취재 노트와 원시 시세로 9월 15일 공개판을 조립한다."""
import datetime, hashlib, importlib.util, json, pathlib, re, subprocess, sys
R=pathlib.Path(__file__).resolve().parents[3]; E=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('prior',E.parent/'2026-09-14/build.py'); prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
TITLE='미국 반도체 급락, KOSPI는 전일 저점을 지킬까'
SUMMARY='미국 반도체 ETF가 5% 안팎 하락했습니다. 이미 급락한 한국장에서는 같은 뉴스를 두 번 세기보다 메모리주 장전 가격과 외국인 매도 완화를 살펴야 합니다.'
IMAGE='market-2026-09-15-ai-braking-1200x630.webp'
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
    assert stamp.hour<9,'09:00 이후에는 장중판으로 새로 작성해야 한다.'
    issued=stamp.isoformat(); sid=stamp.strftime('%Y%m%d-%H%M'); fid='2026-09-15-'+stamp.strftime('%H%M')+'-same-close'
    cutoff=max(ev(n)['fetchedAt'] for n in ('NXT','FX','yahoo-NQF','yahoo-ESF','yahoo-BZF','yahoo-CLF'))
    if seal:
        assert (stamp-datetime.datetime.fromisoformat(cutoff)).total_seconds()<180
        assert (E/'settlement-note.md').exists()
    nxt={x['itemCode']:x for x in ev('NXT')['data']['datas']}; fx=ev('FX')['data']['exchangeInfo']
    for x in nxt.values():assert x['localTradedAt'].startswith('2026-09-15') and x['marketSessionType']=='preMarket'
    kospi=next(x for x in ev('KOSPI-fresh')['data'] if x['localTradedAt']=='2026-09-14');kosdaq=next(x for x in ev('KOSDAQ-fresh')['data'] if x['localTradedAt']=='2026-09-14')
    kodex=next(x for x in ev('122630')['data'] if x['localTradedAt']=='2026-09-14')
    assert kospi['localTradedAt']==kosdaq['localTradedAt']=='2026-09-14'
    body=read('research/evidence/2026-09-15/manuscript.md').split('\n',1)[1].strip()
    table='## 장전 가격\n\n|항목|가격·변화|출처 시각|\n|---|---:|---|\n'
    for code,label in [('005930','삼성전자 NXT'),('000660','SK하이닉스 NXT')]:
        x=nxt[code];table+=f"|{label}|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|\n"
    table+=f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|\n"
    for key,label in [('NQF','Nasdaq100 선물'),('ESF','S&P500 선물'),('BZF','브렌트 선물'),('CLF','WTI 선물')]:
        m=ev('yahoo-'+key)['data']['chart']['result'][0]['meta']; t=datetime.datetime.fromtimestamp(m['regularMarketTime'],stamp.tzinfo).isoformat()
        table+=f"|{label}|{m['regularMarketPrice']:,.2f} · {m['regularMarketChangePercent']:+.3f}%|{t} · 지연 시세|\n"
    table+='\n[NXT](https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660) · [환율](https://api.stock.naver.com/marketindex/exchange/FX_USDKRW) · [Nasdaq100 선물](https://finance.yahoo.com/quote/NQ=F/) · [S&P500 선물](https://finance.yahoo.com/quote/ES=F/) · [브렌트](https://finance.yahoo.com/quote/BZ=F/) · [WTI](https://finance.yahoo.com/quote/CL=F/)\n\nNXT는 국내 정규장과 별도 시장이다. 환율은 은행 고시이며 선물은 지연 시세다.'
    body+='\n\n'+table
    old=base('articles/market-2026-09-14.html'); oldtitle=re.search('<h1>(.*?)</h1>',old).group(1)
    oldimage='market-2026-09-14-shipping-memory-1200x630.webp'
    oldsummary=prior.SUMMARY
    def update(t):
        t=re.sub(r'2026-09-14T08:[0-9:]+\+09:00',issued,t)
        t=t.replace(oldtitle,TITLE).replace(oldsummary,SUMMARY).replace(oldimage,IMAGE).replace('2026-09-14','2026-09-15').replace('2026.09.14 · 08:15 KST','2026.09.15 · '+stamp.strftime('%H:%M')+' KST')
        t=re.sub(r'2026년 9월 \d+일 KOSPI 개장 전 시황', '2026년 9월 15일 KOSPI 개장 전 시황',t)
        t=re.sub(r'9월 \d+일 KOSPI 개장 전 시황 읽기','9월 15일 KOSPI 개장 전 시황 읽기',t)
        t=t.replace('두 반도체 칩 위로 밀려드는 호박색 원유 파도','AI 서버와 메모리 칩 사이의 빛을 늦추는 호박색 장벽')
        return t
    prefix=update(old.split('<article class="editorial-article reading-article">')[0])
    prefix=re.sub(r'(property="article:(?:published|modified)_time" content=")[^"]+',lambda m:m[1]+issued,prefix)
    prefix=re.sub(r'("date(?:Published|Modified)":\s*")[^"]+',lambda m:m[1]+issued,prefix)
    prefix=re.sub(r'(property="og:image:alt" content=")[^"]+',r'\g<1>AI 서버와 메모리 칩 사이의 빛을 늦추는 호박색 장벽',prefix)
    prefix=prefix.replace('</head>','<style>.article-body .table-scroll{max-width:100%;overflow-x:auto}</style></head>')
    closing=old[old.index('</div></article></main>'):]
    charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{k}_2026-09-15.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {label}"><figcaption>9월 14일 FRED: 10년-2년 +0.32%p · 10년-3개월 +0.86%p.</figcaption></figure>' for k,label in [('90d','최근 90일'),('long_term','최근 2년')])
    article=prefix+f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{issued}">2026.09.15 · {stamp.strftime("%H:%M")} KST</time><span>개장 전 브리핑</span></div><p class="article-disclosure">작성 {stamp.strftime("%H:%M")} KST · 데이터 최종 확인 {cutoff}. 국내·미국 정규장은 9월 14일 기준이며 장전 가격은 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="AI 서버와 메모리 칩 사이의 빛을 늦추는 호박색 장벽"></figure></header><div class="article-body" id="article-body">'+prior.prior.prior.markdown_html(body).replace('table-scroll','article-table-wrap').replace('<table>','<table class="article-data-table">')+charts+closing
    write('articles/market-2026-09-15.html',article)
    report=f'# 2026-09-15 KOSPI·KODEX 일일 리서치\n\n작성 {issued} / 데이터 최종 확인 {cutoff} / 한국 개장 전.\n\n확정 수치는 출처 시각 기준이다. 시나리오·확률·대응점수는 조건부 분석이다. 전일 종가 6,684.37은 직전 약세 구간에 들어갔다. 확정 일봉과 수급 원문 대조는 아래 정산 기록에 보존한다.\n\n'+body+'\n\n## 직전 전망 정산\n\n'+(read('research/evidence/2026-09-15/settlement-note.md') if (E/'settlement-note.md').exists() else '정산 진행 중: 공개 봉인 전에 확정한다.')+'\n\n## 취재 근거와 확인 시각\n\n'+read('research/evidence/2026-09-15/overnight-notes.md')+'\n\n![최근 90일](../charts/us_yield_spreads_90d_2026-09-15.png)\n\n![최근 2년](../charts/us_yield_spreads_long_term_2026-09-15.png)\n'
    report+='\n## 미국 정규장 고저·시간외 원천\n\n|종목|종가|고가|저가|고가 대비 종가|\n|---|---:|---:|---:|---:|\n'
    for ticker in ('QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'):
        m=ev('yahoo-'+ticker)['data']['chart']['result'][0]['meta']
        report+=f"|{ticker}|{m['regularMarketPrice']}|{m['regularMarketDayHigh']}|{m['regularMarketDayLow']}|{(m['regularMarketPrice']/m['regularMarketDayHigh']-1)*100:.2f}%|\n"
    report+='\n미국 9월 14일 정규장 기준. 각 yahoo-*.json에 조회 시각·URL·원문 해시를 보존했다. 시간외는 취재 노트의 별도 시각·가격을 사용한다.\n'
    write('reports/2026-09-15.md',report)
    d=json.loads(base('assets/data/market-dashboard-latest.json'))
    d.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff,marketState='한국 개장 전',sourceLabel='국내·미국 9월 14일 정규장 · 장전 가격은 각 출처 시각',latestArticle={'title':TITLE,'href':'market-2026-09-15.html'},headline=TITLE,summary=SUMMARY)
    for m in d['markets']:
        x=kospi if m['id']=='KOSPI' else kosdaq
        m.update(value=num(x['closePrice']),changePercent=num(x['fluctuationsRatio']),open=num(x['openPrice']),high=num(x['highPrice']),low=num(x['lowPrice']),previousClose=num(x['closePrice'])-num(x['compareToPreviousClosePrice']),asOf='2026-09-14T15:30:00+09:00',asOfLabel='9월 14일 정규장 종가',stateLabel='전일 종가',flows=[]);m.pop('breadth',None)
    d['markets'][0]['flows']=[]
    d['markets'][0]['asOfLabel']='9월 14일 정규장 종가'
    d['stance']={'label':'방어적 관망','attack':15,'wait':40,'defense':45,'note':'미국 반도체 급락 뒤 국내 전일 저점 방어와 매도 완화를 기다립니다.'}
    d['checkpoints']=[]
    for key,label in [('BZF','브렌트 선물'),('NQF','Nasdaq100 선물')]:
        m=ev('yahoo-'+key)['data']['chart']['result'][0]['meta']
        d['checkpoints'].append({'label':label,'value':f"{m['regularMarketPrice']:,.2f} · {m['regularMarketChangePercent']:+.2f}%",'detail':datetime.datetime.fromtimestamp(m['regularMarketTime'],stamp.tzinfo).isoformat()+' · 지연','tone':'warning'})
    d['checkpoints'] += [{'label':'원/달러','value':fx['closePrice']+'원','detail':fx['localTradedAt']+' 고시','tone':'info'},{'label':'메모리 NXT','value':f"삼성 {nxt['005930']['fluctuationsRatio']}% · 하이닉스 {nxt['000660']['fluctuationsRatio']}%",'detail':nxt['005930']['localTradedAt'],'tone':'warning'}]

    d['changes']=[{'label':'KOSPI','before':'6,909.91','after':'6,684.37','meaning':'9월 14일 3.26% 하락했습니다.'},{'label':'미국 반도체','before':'한국장 급락','after':'SOXX -5.63%','meaning':'미국 시장에서도 AI 성장 기대를 둘러싼 매도가 이어졌습니다.'}]
    d['factors']=[{'label':'반도체','metric':'SOXX -5.63% · SMH -4.75%','detail':'9월 14일 미국 정규장','tone':'warning'},{'label':'물가·금리','metric':'FOMC 앞둔 금리 부담','detail':'높은 유가와 장기금리가 기술주 반등을 제약합니다.','tone':'warning'},{'label':'금리차','metric':'10년-2년 +0.32%p','detail':'FRED 9월 14일 · 10년-3개월 +0.86%p','tone':'info'}]
    d['flows']={'program':{'arbitrage':None,'nonArbitrage':None,'total':None,'unit':'억원'},'kospi200FuturesForeign':None,'futuresUnit':'계약','futuresAsOfLabel':'전일 확정 수급은 별도 출처 시각 기준'}
    d['memory']=[{'label':'DDR5 16Gb · 9/14 19:10 KST','value':'$54.333','change':'보합 일간'},{'label':'DDR4 16Gb · 9/14 19:10 KST','value':'$89.250','change':'-0.56% 일간'},{'label':'DDR4 8Gb · 9/14 19:10 KST','value':'$45.571','change':'+0.79% 일간'}]
    d['scenarios']=[{'id':'base','label':'기본 · 45%','range':'KOSPI 6,650~6,800','summary':'전일 저점 부근에서 매도를 소화하며 반등을 시도합니다.','conditions':['6,650 방어','6,800 이하','반도체 낙폭 축소'],'invalidation':'6,650 이탈 또는 6,800 돌파'}, {'id':'bull','label':'강세 · 20%','range':'KOSPI 6,800 초과~6,950','summary':'메모리주 반등과 외국인 매수로 6,800선을 회복합니다.','conditions':['6,800 초과','반도체 동반 회복','외국인·프로그램 순매수'],'invalidation':'6,800 아래 재진입'}, {'id':'bear','label':'약세 · 35%','range':'KOSPI 6,400~6,650 미만','summary':'반도체 매도가 이어지며 전일 저점 아래로 밀립니다.','conditions':['6,650 미만','반도체 약세 지속','환율 상승'],'invalidation':'6,650 회복'}]
    d['strategyLevels']=[{'asset':'KOSPI','support':'6,650 / 6,400','pivot':'6,800','resistance':'6,950'},{'asset':'KODEX 레버리지','support':'100,885원','pivot':'102,500원','resistance':'105,215원'}]
    d['scenarios'][0]['conditions']=['6,650 이상','6,800 이하','외국인 순매도 1조원 이내']
    d['scenarios'][1]['conditions']=['6,800 초과','외국인 현물 순매수','프로그램 전체 순매수']
    d['scenarios'][2]['conditions']=['6,650 미만','외국인 현물 순매도','프로그램 전체 순매도']
    d['events']=[{'time':'9월 16일 21:30 KST','name':'미국 8월 소매판매','path':'소비와 금리 기대'},{'time':'9월 17일 03:00 KST','name':'FOMC·경제전망','path':'정책금리와 장기금리'}]
    d['checklist']=[{'id':'support','label':'KOSPI 6,650 방어'},{'id':'rebound','label':'6,800 회복과 메모리 동반 반등'},{'id':'flows','label':'외국인·프로그램 순매수 동반 여부'}]
    d['technical']['note']='9월 14일 확정 일봉과 9월 15일 분석 기준선입니다.'
    for x in d['technical']['instruments']:
        row=kospi if x['id']=='KOSPI' else kodex; levels=[6650,6800,6950] if x['id']=='KOSPI' else [100885,102500,105215]
        x.update(asOf='2026-09-14T15:30:00+09:00',asOfLabel='9월 14일 정규장 종가',points=[{'label':l,'value':num(row[k])} for l,k in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]],levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=f'1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}')
    d['sources']=[{'label':'KOSPI 일봉','href':ev('KOSPI-fresh')['url']},{'label':'NXT','href':ev('NXT')['url']},{'label':'연준 FOMC','href':'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'},{'label':'FRED','href':'https://fred.stlouisfed.org/series/T10Y2Y'}]
    d['sources'].append({'label':'TrendForce 현물','href':'https://www.trendforce.com/price/dram/lpddr_spot'})
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
            t=t.replace('주말 송유관·해운 위험 뒤 유가가 다시 오르고 미국 선물과 국내 메모리주가 약세입니다.','미국 반도체 급락 뒤 국내 메모리주와 외국인 매도 흐름이 지수 방향을 가릅니다.')
            t=t.replace('KOSPI 6,800선 방어와 외국인·프로그램 매도의 완화 여부를 함께 봅니다.','KOSPI 6,650선 방어와 외국인·프로그램 매도의 완화 여부를 함께 봅니다.')
            t=t.replace('대형 반도체와 코스닥의 온도차, 투자 주체별 수급과 메모리 실물 가격을 한 화면에서 비교합니다.','미국 반도체 급락 뒤 국내 메모리주와 외국인 매도 흐름이 지수 방향을 가릅니다.')
            t=t.replace('미국 반등 뒤 달라진 장전 흐름','반도체 급락 뒤 확인할 국내 수급')
            t=t.replace('가격이 많이 빠졌다는 이유가 아니라, 수급과 기준선이 함께 바뀌는지로 대응 강도를 정합니다.','KOSPI 6,650선 방어와 외국인·프로그램 매도의 완화 여부를 함께 봅니다.')
            t=re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+',r'\g<1>market-2026-09-15.html',t)
            count=t.count('<article class="market-article-item"');t=re.sub(r'(일일시황 <span class="article-category-count">)\d+',r'\g<1>'+str(count),t);t=re.sub(r'최신순 · \d+편',f'최신순 · {count}편',t)
        write(path,t)
    for path in ['index.html','articles/index.html']:
        t=read(path); cats=re.findall(r'<article class="[^"]*" data-category="([^"]+)"',t)
        for cat in ['all','market','essay','health']:
            count=len(cats) if cat=='all' else cats.count(cat)
            t=re.sub(r'(data-category-count="'+cat+r'">)\d+',lambda m:m[1]+str(count),t)
        write(path,t)
    sm=base('sitemap.xml').replace('</urlset>','<url><loc>https://www.hpmplab.com/articles/market-2026-09-15.html</loc><lastmod>2026-09-15</lastmod></url>\n</urlset>')
    for url in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:
        sm=re.sub(r'(<loc>'+re.escape(url)+r'</loc>\s*<lastmod>)[^<]+',r'\g<1>2026-09-15',sm)
    write('sitemap.xml',sm)
    write('STATE.md',f"# KOSPI·KODEX 리서치 상태\n\n- 작성 {issued}, 데이터 최종 확인 {cutoff}, 한국 개장 전.\n- 직전 KOSPI 6,684.37(-3.26%), KODEX 102,095원(-7.18%), 9월 14일 정규장.\n- 핵심: 미국 반도체 급락과 국내 NXT 약세. 주말 AI 속도조절 논쟁은 한국장 선반영분을 중복 계산하지 않는다.\n- 대응 15/40/45. 기본 6650~6800(45%), 강세 6800초과~6950(20%), 약세 6400~6650미만(35%), 경로 6300~7050(90%). KODEX 100885/102500/105215.\n- 다음: 9/16 소매판매 21:30, 9/17 FOMC 03:00 KST.\n- 보고서 reports/2026-09-15.md, 취재 research/evidence/2026-09-15/overnight-notes.md. 차트 charts/us_yield_spreads_90d_2026-09-15.png 및 long_term.\n- 대시보드 assets/data/market-dashboard-{sid}.json 및 latest.json.\n- 직전 정산 research/evidence/2026-09-15/settlement-note.md, 누적 research/evaluation/generated/latest.md.\n- NXT 삼성 {nxt['005930']['closePrice']}원({nxt['005930']['fluctuationsRatio']}%), SK하이닉스 {nxt['000660']['closePrice']}원({nxt['000660']['fluctuationsRatio']}%); 원/달러 {fx['closePrice']}원({fx['localTradedAt']}).\n- 상위 사건과 제외 근거는 overnight-notes.md에 보존.\n")
    if seal:
        f=json.loads(read('research/evaluation/forecasts/2026-09-14-0815-same-close.json'))
        f.update(forecastId=fid,reportPath='reports/2026-09-15.md',reportSha256=sha('reports/2026-09-15.md'),issuedAt=issued,dataCutoffAt=cutoff,marketRegime='risk_off',target={'sessionDate':'2026-09-15','horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-09-14'},reference={'price':num(kospi['closePrice']),'asOf':'2026-09-14T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':6800,'high':6950,'probability':.2},'base':{'low':6650,'high':6800,'probability':.45},'bear':{'low':6400,'high':6650,'probability':.35}},pathEnvelope={'low':6300,'high':7050,'coverage':.9},posture={'attack':15,'wait':40,'defense':45},drivers=[{'id':'ai-growth-repricing','rank':1,'claim':'AI 성장 기대 둔화와 미국 반도체 매도가 국내 메모리주를 압박한다.','validationMetric':'SOXX·삼성전자·SK하이닉스'}, {'id':'domestic-chip-selling','rank':2,'claim':'국내 메모리주 동반 약세가 지수 하방 압력으로 이어진다.','validationMetric':'삼성전자·SK하이닉스·KOSPI'}, {'id':'rates-oil-pressure','rank':3,'claim':'높은 유가와 미국 장기금리가 기술주 반등을 제약한다.','validationMetric':'미국 10년물·브렌트·외국인 현물'}])
        for group in f['scenarioTriggers'].values():
            group['observeBy']='2026-09-15T15:20:00+09:00'
            for c in group['conditions']:
                if c['metricId']=='kospi_price':
                    c['threshold']={6800:6650,7000:6800}.get(c['threshold'],c['threshold'])
                    c['description']='KOSPI '+str(c['threshold'])+' '+c['operator']
        f.pop('contentHash',None);f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();dump('research/evaluation/forecasts/'+fid+'.json',f)
        files=['articles/market-2026-09-15.html','assets/data/market-dashboard-latest.json','assets/data/market-dashboard-'+sid+'.json','assets/images/articles/'+IMAGE,'charts/us_yield_spreads_90d_2026-09-15.png','charts/us_yield_spreads_long_term_2026-09-15.png','index.html','articles/index.html','articles/market.html','sitemap.xml']
        dump('research/evidence/2026-09-15/seal.json',{'forecastId':fid,'issuedAt':issued,'dataCutoffAt':cutoff,'snapshotId':sid,'files':files})
    print('SEALED' if seal else 'DRAFT',issued,cutoff)
if __name__=='__main__':main('--seal' in sys.argv)
