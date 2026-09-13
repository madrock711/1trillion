"""검증된 취재 노트와 원시 시세로 9월 14일 공개판을 조립한다."""
import datetime, hashlib, importlib.util, json, pathlib, re, subprocess, sys
R=pathlib.Path(__file__).resolve().parents[3]; E=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('prior',E.parent/'2026-09-11/build.py'); prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
TITLE='다시 오르는 유가, 미국 반등을 따라가지 못한 메모리주'
SUMMARY='금요일 미국 증시는 반등했지만 월요일 아침 유가가 다시 오르고 지수선물과 국내 메모리주는 하락했습니다. KOSPI 6,800선 방어와 외국인 매도 완화가 관건입니다.'
IMAGE='market-2026-09-14-shipping-memory-1200x630.webp'
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
    issued=stamp.isoformat(); sid=stamp.strftime('%Y%m%d-%H%M'); fid='2026-09-14-'+stamp.strftime('%H%M')+'-same-close'
    cutoff=max(ev(n)['fetchedAt'] for n in ('NXT','FX','yahoo-NQF','yahoo-ESF','yahoo-BZF','yahoo-CLF'))
    if seal:
        assert (stamp-datetime.datetime.fromisoformat(cutoff)).total_seconds()<180
        assert (E/'settlement-note.md').exists()
    nxt={x['itemCode']:x for x in ev('NXT')['data']['datas']}; fx=ev('FX')['data']['exchangeInfo']
    for x in nxt.values():assert x['localTradedAt'].startswith('2026-09-14') and x['marketSessionType']=='preMarket'
    kospi=next(x for x in ev('KOSPI-fresh')['data'] if x['localTradedAt']=='2026-09-11');kosdaq=next(x for x in ev('KOSDAQ-fresh')['data'] if x['localTradedAt']=='2026-09-11')
    kodex=next(x for x in ev('122630')['data'] if x['localTradedAt']=='2026-09-11')
    assert kospi['localTradedAt']==kosdaq['localTradedAt']=='2026-09-11'
    body=read('research/evidence/2026-09-14/manuscript.md').split('\n',1)[1].strip()
    table='## 장전 가격\n\n|항목|가격·변화|출처 시각|\n|---|---:|---|\n'
    for code,label in [('005930','삼성전자 NXT'),('000660','SK하이닉스 NXT')]:
        x=nxt[code];table+=f"|{label}|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|\n"
    table+=f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|\n"
    for key,label in [('NQF','Nasdaq100 선물'),('ESF','S&P500 선물'),('BZF','브렌트 선물'),('CLF','WTI 선물')]:
        m=ev('yahoo-'+key)['data']['chart']['result'][0]['meta']; t=datetime.datetime.fromtimestamp(m['regularMarketTime'],stamp.tzinfo).isoformat()
        table+=f"|{label}|{m['regularMarketPrice']:,.2f} · {m['regularMarketChangePercent']:+.3f}%|{t} · 지연 시세|\n"
    table+='\n[NXT](https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660) · [환율](https://api.stock.naver.com/marketindex/exchange/FX_USDKRW) · [Nasdaq100 선물](https://finance.yahoo.com/quote/NQ=F/) · [S&P500 선물](https://finance.yahoo.com/quote/ES=F/) · [브렌트](https://finance.yahoo.com/quote/BZ=F/) · [WTI](https://finance.yahoo.com/quote/CL=F/)\n\nNXT는 국내 정규장과 별도 시장이다. 환율은 은행 고시이며 선물은 지연 시세다.'
    body+='\n\n'+table
    old=base('articles/market-2026-09-11.html'); oldtitle=re.search('<h1>(.*?)</h1>',old).group(1)
    oldimage='market-2026-09-11-oil-chip-pressure-1200x630.webp'
    oldsummary=prior.SUMMARY
    def update(t):
        t=re.sub(r'2026-09-11T08:[0-9:]+\+09:00',issued,t)
        t=t.replace(oldtitle,TITLE).replace(oldsummary,SUMMARY).replace(oldimage,IMAGE).replace('2026-09-11','2026-09-14').replace('2026.09.11 · 08:21 KST','2026.09.14 · '+stamp.strftime('%H:%M')+' KST')
        t=re.sub(r'2026년 9월 \d+일 KOSPI 개장 전 시황', '2026년 9월 14일 KOSPI 개장 전 시황',t)
        t=t.replace('두 반도체 칩 위로 밀려드는 호박색 원유 파도','밝은 해협의 유조선과 부두 위 반도체 웨이퍼')
        return t
    prefix=update(old.split('<article class="editorial-article reading-article">')[0])
    prefix=re.sub(r'(property="article:(?:published|modified)_time" content=")[^"]+',lambda m:m[1]+issued,prefix)
    prefix=re.sub(r'("date(?:Published|Modified)":\s*")[^"]+',lambda m:m[1]+issued,prefix)
    prefix=re.sub(r'(property="og:image:alt" content=")[^"]+',r'\g<1>밝은 해협의 유조선과 부두 위 반도체 웨이퍼',prefix)
    prefix=prefix.replace('</head>','<style>.article-body .table-scroll{max-width:100%;overflow-x:auto}</style></head>')
    closing=old[old.index('</div></article></main>'):]
    charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{k}_2026-09-14.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {label}"><figcaption>9월 11일 FRED: 10년-2년 +0.33%p · 10년-3개월 +0.89%p.</figcaption></figure>' for k,label in [('90d','최근 90일'),('long_term','최근 2년')])
    article=prefix+f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{issued}">2026.09.14 · {stamp.strftime("%H:%M")} KST</time><span>개장 전 브리핑</span></div><p class="article-disclosure">작성 {stamp.strftime("%H:%M")} KST · 데이터 최종 확인 {cutoff}. 국내·미국 정규장은 9월 11일 기준이며 장전 가격은 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="밝은 해협의 유조선과 부두 위 반도체 웨이퍼"></figure></header><div class="article-body" id="article-body">'+prior.prior.markdown_html(body).replace('table-scroll','article-table-wrap').replace('<table>','<table class="article-data-table">')+charts+closing
    write('articles/market-2026-09-14.html',article)
    report=f'# 2026-09-14 KOSPI·KODEX 일일 리서치\n\n작성 {issued} / 데이터 최종 확인 {cutoff} / 한국 개장 전.\n\n확정 수치는 출처 시각 기준이다. 시나리오·확률·대응점수는 조건부 분석이다. 전일 종가 6,909.91은 직전 기본 구간 안이었다. 확정 일봉과 수급 원문 대조는 아래 정산 기록에 보존한다.\n\n'+body+'\n\n## 직전 전망 정산\n\n'+(read('research/evidence/2026-09-14/settlement-note.md') if (E/'settlement-note.md').exists() else '정산 진행 중: 공개 봉인 전에 확정한다.')+'\n\n## 취재 근거와 확인 시각\n\n'+read('research/evidence/2026-09-14/overnight-notes.md')+'\n\n![최근 90일](../charts/us_yield_spreads_90d_2026-09-14.png)\n\n![최근 2년](../charts/us_yield_spreads_long_term_2026-09-14.png)\n'
    report+='\n## 미국 정규장 고저·시간외 원천\n\n|종목|종가|고가|저가|고가 대비 종가|\n|---|---:|---:|---:|---:|\n'
    for ticker in ('QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'):
        m=ev('yahoo-'+ticker)['data']['chart']['result'][0]['meta']
        report+=f"|{ticker}|{m['regularMarketPrice']}|{m['regularMarketDayHigh']}|{m['regularMarketDayLow']}|{(m['regularMarketPrice']/m['regularMarketDayHigh']-1)*100:.2f}%|\n"
    report+='\n미국 9월 11일 정규장 기준. 각 yahoo-*.json에 조회 시각·URL·원문 해시를 보존했다. 시간외는 us-prices.json의 마지막 관측 시각과 가격을 따로 사용한다.\n'
    write('reports/2026-09-14.md',report)
    d=json.loads(base('assets/data/market-dashboard-latest.json'))
    d.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff,marketState='한국 개장 전',sourceLabel='국내·미국 9월 11일 정규장 · 장전 가격은 각 출처 시각',latestArticle={'title':TITLE,'href':'market-2026-09-14.html'},headline=TITLE,summary=SUMMARY)
    for m in d['markets']:
        x=kospi if m['id']=='KOSPI' else kosdaq
        m.update(value=num(x['closePrice']),changePercent=num(x['fluctuationsRatio']),open=num(x['openPrice']),high=num(x['highPrice']),low=num(x['lowPrice']),previousClose=num(x['closePrice'])-num(x['compareToPreviousClosePrice']),asOf='2026-09-11T15:30:00+09:00',asOfLabel='9월 11일 정규장 종가',stateLabel='전일 종가',flows=[]);m.pop('breadth',None)
    d['markets'][0]['flows']=[{'label':'개인','value':18191,'unit':'억원'},{'label':'외국인','value':-23556,'unit':'억원'},{'label':'기관','value':-11123,'unit':'억원'}]
    d['markets'][0]['asOfLabel']='9월 11일 종가 · 수급 15:30'
    d['stance']={'label':'방어적 관망','attack':15,'wait':45,'defense':40,'note':'유가 재상승과 메모리주 장전 약세 속 개장 뒤 수급 회복을 기다립니다.'}
    d['checkpoints']=[]
    for key,label in [('BZF','브렌트 선물'),('NQF','Nasdaq100 선물')]:
        m=ev('yahoo-'+key)['data']['chart']['result'][0]['meta']
        d['checkpoints'].append({'label':label,'value':f"{m['regularMarketPrice']:,.2f} · {m['regularMarketChangePercent']:+.2f}%",'detail':datetime.datetime.fromtimestamp(m['regularMarketTime'],stamp.tzinfo).isoformat()+' · 지연','tone':'warning'})
    d['checkpoints'] += [{'label':'원/달러','value':fx['closePrice']+'원','detail':fx['localTradedAt']+' 고시','tone':'info'},{'label':'메모리 NXT','value':f"삼성 {nxt['005930']['fluctuationsRatio']}% · 하이닉스 {nxt['000660']['fluctuationsRatio']}%",'detail':nxt['005930']['localTradedAt'],'tone':'warning'}]

    d['changes']=[{'label':'KOSPI','before':'7,033.92','after':'6,909.91','meaning':'금요일 1.76% 하락해 7,000선 아래에서 마감했습니다.'},{'label':'메모리 장전','before':'금요일 미국 반도체 ETF 반등','after':'월요일 국내 메모리 장전 약세','meaning':'유가 재상승과 선물 약세 속 국내 메모리주가 동반 하락했습니다.'}]
    d['factors']=[{'label':'물가·유가','metric':'유가 재상승과 FOMC 경계','detail':'금요일 미국 반등 뒤 월요일 아침 유가와 주가지수 선물이 엇갈렸습니다.','tone':'warning'},{'label':'반도체','metric':'SOXX +1.86%','detail':'9월 11일 미국 정규장','tone':'warning'},{'label':'금리차','metric':'10년-2년 +0.33%p','detail':'FRED 9월 11일 · 10년-3개월 +0.89%p','tone':'info'}]
    d['flows']={'program':{'arbitrage':-543,'nonArbitrage':-17656,'total':-18199,'unit':'억원'},'kospi200FuturesForeign':None,'futuresUnit':'계약','futuresAsOfLabel':'9월 11일 15:30 수급'}
    d['memory']=[{'label':'DDR5 16Gb · 9/11 19:10 KST','value':'$54.333','change':'보합 일간'},{'label':'DDR4 8Gb · 9/11 19:10 KST','value':'$45.214','change':'-0.14% 일간'}]
    d['scenarios']=[{'id':'base','label':'기본 · 50%','range':'KOSPI 6,800~7,000','summary':'갭 하락 뒤 전일 저점 주변에서 매도를 소화합니다.','conditions':['6,800 방어','7,000 이하','반도체 낙폭 축소'],'invalidation':'6,800 이탈 또는 7,000 돌파'}, {'id':'bull','label':'강세 · 20%','range':'KOSPI 7,000 초과~7,150','summary':'메모리주 반등과 외국인 매수로 7,000선을 회복합니다.','conditions':['7,000 초과','반도체 동반 회복','외국인·프로그램 순매수'],'invalidation':'7,000 아래 재진입'}, {'id':'bear','label':'약세 · 30%','range':'KOSPI 6,550~6,800 미만','summary':'유가 재상승과 반도체 매도가 지수 하락을 키웁니다.','conditions':['6,800 미만','반도체 약세 지속','환율 상승'],'invalidation':'6,800 회복'}]
    d['strategyLevels']=[{'asset':'KOSPI','support':'6,800 / 6,550','pivot':'7,000','resistance':'7,150'},{'asset':'KODEX 레버리지','support':'106,200원','pivot':'110,000원','resistance':'111,545원'}]
    d['scenarios'][0]['conditions']=['6,800 이상','7,000 이하','외국인 순매도 1조원 이내']
    d['scenarios'][1]['conditions']=['7,000 초과','외국인 현물 순매수','프로그램 전체 순매수']
    d['scenarios'][2]['conditions']=['6,800 미만','외국인 현물 순매도','프로그램 전체 순매도']
    d['events']=[{'time':'9월 16일 21:30 KST','name':'미국 8월 소매판매','path':'소비와 금리 기대'},{'time':'9월 17일 03:00 KST','name':'FOMC·경제전망','path':'정책금리와 장기금리'}]
    d['checklist']=[{'id':'support','label':'KOSPI 6,800 방어'},{'id':'rebound','label':'7,000 회복과 메모리 동반 반등'},{'id':'flows','label':'외국인·프로그램 순매수 동반 여부'}]
    d['technical']['note']='9월 11일 확정 일봉과 9월 14일 분석 기준선입니다.'
    for x in d['technical']['instruments']:
        row=kospi if x['id']=='KOSPI' else kodex; levels=[6800,7000,7150] if x['id']=='KOSPI' else [106200,110000,111545]
        x.update(asOf='2026-09-11T15:30:00+09:00',asOfLabel='9월 11일 정규장 종가',points=[{'label':l,'value':num(row[k])} for l,k in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]],levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=f'1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}')
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
            t=t.replace('대형 반도체와 코스닥의 온도차, 투자 주체별 수급과 메모리 실물 가격을 한 화면에서 비교합니다.','주말 송유관·해운 위험 뒤 유가가 다시 오르고 미국 선물과 국내 메모리주가 약세입니다.')
            t=t.replace('반등의 질을 가르는 네 가지','미국 반등 뒤 달라진 장전 흐름')
            t=t.replace('가격이 많이 빠졌다는 이유가 아니라, 수급과 기준선이 함께 바뀌는지로 대응 강도를 정합니다.','KOSPI 6,800선 방어와 외국인·프로그램 매도의 완화 여부를 함께 봅니다.')
            t=re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+',r'\g<1>market-2026-09-14.html',t)
            count=t.count('<article class="market-article-item"');t=re.sub(r'(일일시황 <span class="article-category-count">)\d+',r'\g<1>'+str(count),t);t=re.sub(r'최신순 · \d+편',f'최신순 · {count}편',t)
        write(path,t)
    for path in ['index.html','articles/index.html']:
        t=read(path); cats=re.findall(r'<article class="[^"]*" data-category="([^"]+)"',t)
        for cat in ['all','market','essay','health']:
            count=len(cats) if cat=='all' else cats.count(cat)
            t=re.sub(r'(data-category-count="'+cat+r'">)\d+',lambda m:m[1]+str(count),t)
        write(path,t)
    sm=base('sitemap.xml').replace('</urlset>','<url><loc>https://www.hpmplab.com/articles/market-2026-09-14.html</loc><lastmod>2026-09-14</lastmod></url>\n</urlset>')
    for url in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:
        sm=re.sub(r'(<loc>'+re.escape(url)+r'</loc>\s*<lastmod>)[^<]+',r'\g<1>2026-09-14',sm)
    write('sitemap.xml',sm)
    write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 {issued}, 데이터 최종 확인 {cutoff}, 한국 개장 전.\n- 직전 KOSPI 6,909.91(-1.76%), KODEX 109,995원(-4.35%), 9월 11일 정규장.\n- 핵심: 사우디 송유관·해운 위험으로 유가 재상승, 미국 선물 약세, 국내 메모리주 NXT 동반 약세.\n- 대응 15/45/40. 기본 6800~7000(50%), 강세 7000초과~7150(20%), 약세 6550~6800미만(30%), 경로 6450~7250(90%). KODEX 106200/110000/111545.\n- 다음: 9/16 소매판매 21:30, 9/17 FOMC 03:00 KST.\n- 보고서 reports/2026-09-14.md, 취재 research/evidence/2026-09-14/overnight-notes.md. 차트 charts/us_yield_spreads_90d_2026-09-14.png 및 long_term.\n- 대시보드 assets/data/market-dashboard-{sid}.json 및 latest.json.\n- 직전 정산 research/evaluation/outcomes/2026-09-11-0821-same-close.json, 누적 research/evaluation/generated/latest.md. 15:20 가격 조건은 충족했으나 외국인 매도가 1조원을 넘어 기본 AND 조건은 불성립했다.\n')
    write('STATE.md',read('STATE.md')+f"- NXT 삼성 {nxt['005930']['closePrice']}원({nxt['005930']['fluctuationsRatio']}%), SK하이닉스 {nxt['000660']['closePrice']}원({nxt['000660']['fluctuationsRatio']}%); 원/달러 {fx['closePrice']}원({fx['localTradedAt']}).\n- 상위 이슈: 송유관·해운 위험, CPI 이후 FOMC, 금요일 반도체 내부 분화. 원유 운송량 추정은 확정 공급손실로 사용하지 않는다.\n- 직전 정산 및 수급 원문: research/evidence/2026-09-14/settlement-note.md. 미확인 강제청산은 주도 사건에서 제외.\n")
    if seal:
        f=json.loads(read('research/evaluation/forecasts/2026-09-11-0821-same-close.json'))
        f.update(forecastId=fid,reportPath='reports/2026-09-14.md',reportSha256=sha('reports/2026-09-14.md'),issuedAt=issued,dataCutoffAt=cutoff,marketRegime='risk_off',target={'sessionDate':'2026-09-14','horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-09-11'},reference={'price':num(kospi['closePrice']),'asOf':'2026-09-11T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':7000,'high':7150,'probability':.2},'base':{'low':6800,'high':7000,'probability':.5},'bear':{'low':6550,'high':6800,'probability':.3}},pathEnvelope={'low':6450,'high':7250,'coverage':.9},posture={'attack':15,'wait':45,'defense':40},drivers=[{'id':'oil-inflation','rank':1,'claim':'유가·물가 압력이 반도체 밸류에이션을 누른다.','validationMetric':'브렌트·미국 금리'}, {'id':'domestic-chip-selling','rank':2,'claim':'국내 메모리주 동반 약세가 지수 하방 압력으로 이어진다.','validationMetric':'삼성전자·SK하이닉스·KOSPI'}, {'id':'futures-pressure','rank':3,'claim':'미국 지수선물 약세가 금요일 반등의 지속성을 제한한다.','validationMetric':'Nasdaq100 선물·외국인 현물'}])
        for group in f['scenarioTriggers'].values():
            group['observeBy']='2026-09-14T15:20:00+09:00'
        f.pop('contentHash',None);f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();dump('research/evaluation/forecasts/'+fid+'.json',f)
        files=['articles/market-2026-09-14.html','assets/data/market-dashboard-latest.json','assets/data/market-dashboard-'+sid+'.json','assets/images/articles/'+IMAGE,'charts/us_yield_spreads_90d_2026-09-14.png','charts/us_yield_spreads_long_term_2026-09-14.png','index.html','articles/index.html','articles/market.html','sitemap.xml']
        dump('research/evidence/2026-09-14/seal.json',{'forecastId':fid,'issuedAt':issued,'dataCutoffAt':cutoff,'snapshotId':sid,'files':files})
    print('SEALED' if seal else 'DRAFT',issued,cutoff)
if __name__=='__main__':main('--seal' in sys.argv)
