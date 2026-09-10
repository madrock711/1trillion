"""검증된 취재 노트와 원시 시세로 9월 11일 공개판을 조립한다."""
import datetime, hashlib, importlib.util, json, pathlib, re, subprocess, sys
R=pathlib.Path(__file__).resolve().parents[3]; E=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('prior',E.parent/'2026-09-10/build.py'); prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
TITLE='유가와 물가가 누르는 반도체, KOSPI 7,000선 재시험'
SUMMARY='미국 반도체 하락과 원화 약세가 국내 메모리주 장전 매도로 이어졌습니다. 전일 낙폭을 되돌린 7,000선이 오늘도 버틸지가 관건입니다.'
IMAGE='market-2026-09-11-oil-chip-pressure-1200x630.webp'
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
    issued=stamp.isoformat(); sid=stamp.strftime('%Y%m%d-%H%M'); fid='2026-09-11-'+stamp.strftime('%H%M')+'-same-close'
    cutoff=max(ev(n)['fetchedAt'] for n in ('NXT','FX','yahoo-NQF','yahoo-ESF'))
    if seal: assert (stamp-datetime.datetime.fromisoformat(cutoff)).total_seconds()<180
    nxt={x['itemCode']:x for x in ev('NXT')['data']['datas']}; fx=ev('FX')['data']['exchangeInfo']
    for x in nxt.values():assert x['localTradedAt'].startswith('2026-09-11') and x['marketSessionType']=='preMarket'
    kospi=ev('KOSPI-fresh')['data'][0];kosdaq=ev('KOSDAQ-fresh')['data'][0]
    kodex=next(x for x in ev('122630')['data'] if x['localTradedAt']=='2026-09-10')
    assert kospi['localTradedAt']==kosdaq['localTradedAt']=='2026-09-10'
    body=read('research/evidence/2026-09-11/manuscript.md').split('\n',1)[1].strip()
    table='## 장전 가격\n\n|항목|가격·변화|출처 시각|\n|---|---:|---|\n'
    for code,label in [('005930','삼성전자 NXT'),('000660','SK하이닉스 NXT')]:
        x=nxt[code];table+=f"|{label}|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|\n"
    table+=f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|\n"
    for key,label in [('NQF','Nasdaq100 선물'),('ESF','S&P500 선물'),('BZF','브렌트 선물'),('CLF','WTI 선물')]:
        m=ev('yahoo-'+key)['data']['chart']['result'][0]['meta']; t=datetime.datetime.fromtimestamp(m['regularMarketTime'],stamp.tzinfo).isoformat()
        table+=f"|{label}|{m['regularMarketPrice']:,.2f} · {m['regularMarketChangePercent']:+.3f}%|{t} · 지연 시세|\n"
    table+='\n[NXT](https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660) · [환율](https://api.stock.naver.com/marketindex/exchange/FX_USDKRW) · [Nasdaq100 선물](https://finance.yahoo.com/quote/NQ=F/) · [S&P500 선물](https://finance.yahoo.com/quote/ES=F/) · [브렌트](https://finance.yahoo.com/quote/BZ=F/) · [WTI](https://finance.yahoo.com/quote/CL=F/)\n\nNXT는 국내 정규장과 별도 시장이다. 환율은 은행 고시이며 선물은 지연 시세다.'
    body+='\n\n'+table
    old=base('articles/market-2026-09-10.html'); oldtitle=re.search('<h1>(.*?)</h1>',old).group(1)
    oldimage='market-2026-09-10-oil-memory-balance-1200x630.webp'
    oldsummary=prior.SUMMARY
    def update(t):
        t=t.replace(oldtitle,TITLE).replace(oldsummary,SUMMARY).replace(oldimage,IMAGE).replace('2026-09-10','2026-09-11').replace('2026.09.10 · 08:28 KST','2026.09.11 · '+stamp.strftime('%H:%M')+' KST')
        t=re.sub(r'2026년 9월 \d+일 KOSPI 개장 전 시황', '2026년 9월 11일 KOSPI 개장 전 시황',t)
        t=t.replace(prior.ALT,'두 반도체 칩 위로 밀려드는 호박색 원유 파도')
        return t
    prefix=update(old.split('<article class="editorial-article reading-article">')[0])
    prefix=re.sub(r'(property="article:(?:published|modified)_time" content=")[^"]+',lambda m:m[1]+issued,prefix)
    prefix=re.sub(r'("date(?:Published|Modified)":\s*")[^"]+',lambda m:m[1]+issued,prefix)
    prefix=re.sub(r'(property="og:image:alt" content=")[^"]+',r'\g<1>두 반도체 칩 위로 밀려드는 호박색 원유 파도',prefix)
    prefix=prefix.replace('</head>','<style>.article-body .table-scroll{max-width:100%;overflow-x:auto}</style></head>')
    closing=old[old.index('</div></article></main>'):]
    charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{k}_2026-09-11.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {label}"><figcaption>9월 10일 FRED: 10년-2년 +0.39%p · 10년-3개월 +0.95%p.</figcaption></figure>' for k,label in [('90d','최근 90일'),('long_term','최근 2년')])
    article=prefix+f'<article class="editorial-article reading-article"><header class="article-hero"><a class="article-category-badge" href="market.html?view=analysis#research-archive">시황분석</a><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{issued}">2026.09.11 · {stamp.strftime("%H:%M")} KST</time><span>개장 전 브리핑</span></div><p class="article-disclosure">작성 {stamp.strftime("%H:%M")} KST · 데이터 최종 확인 {cutoff}. 국내·미국 정규장은 9월 10일 기준이며 장전 가격은 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="두 반도체 칩 위로 밀려드는 호박색 원유 파도"></figure></header><div class="article-body" id="article-body">'+prior.markdown_html(body).replace('table-scroll','article-table-wrap').replace('<table>','<table class="article-data-table">')+charts+closing
    write('articles/market-2026-09-11.html',article)
    report=f'# 2026-09-11 KOSPI·KODEX 일일 리서치\n\n작성 {issued} / 데이터 최종 확인 {cutoff} / 한국 개장 전.\n\n확정 수치는 출처 시각 기준이다. 시나리오·확률·대응점수는 조건부 분석이다. 전일 종가 7,033.92는 직전 기본 구간 안, 경로 6,898.45~7,072.79는 예상 경로 안이었다. 15:20 이전 트리거 원문은 없어 미확인으로 보존했다.\n\n'+body+'\n\n## 취재 근거와 확인 시각\n\n'+read('research/evidence/2026-09-11/overnight-notes.md')+'\n\n![최근 90일](../charts/us_yield_spreads_90d_2026-09-11.png)\n\n![최근 2년](../charts/us_yield_spreads_long_term_2026-09-11.png)\n'
    write('reports/2026-09-11.md',report)
    d=json.loads(base('assets/data/market-dashboard-latest.json'))
    d.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff,marketState='한국 개장 전',sourceLabel='국내·미국 9월 10일 정규장 · 장전 가격은 각 출처 시각',latestArticle={'title':TITLE,'href':'market-2026-09-11.html'},headline=TITLE,summary=SUMMARY)
    for m in d['markets']:
        x=kospi if m['id']=='KOSPI' else kosdaq
        m.update(value=num(x['closePrice']),changePercent=num(x['fluctuationsRatio']),open=num(x['openPrice']),high=num(x['highPrice']),low=num(x['lowPrice']),previousClose=num(x['closePrice'])-num(x['compareToPreviousClosePrice']),asOf='2026-09-10T15:30:00+09:00',asOfLabel='9월 10일 정규장 종가',stateLabel='전일 종가',flows=[]);m.pop('breadth',None)
    d['stance']={'label':'방어적 관망','attack':15,'wait':45,'defense':40,'note':'반도체 동반 약세와 원화 약세가 겹쳐 개장 뒤 수급 회복을 기다립니다.'}
    d['checkpoints']=[{'label':'미국 반도체','value':'SOXX -2.74%','detail':'9월 10일 미국 정규장','tone':'warning'},{'label':'원/달러','value':fx['closePrice']+'원','detail':fx['localTradedAt']+' 고시','tone':'warning'},{'label':'메모리 NXT','value':f"삼성 {nxt['005930']['fluctuationsRatio']}% · 하이닉스 {nxt['000660']['fluctuationsRatio']}%",'detail':nxt['005930']['localTradedAt'],'tone':'warning'}]
    d['changes']=[{'label':'KOSPI','before':'7,051.64','after':'7,033.92','meaning':'전일 장중 6,898.45에서 낙폭을 줄였습니다.'},{'label':'메모리 장전','before':'9/10 하이닉스 상대강세','after':'9/11 양사 동반 약세','meaning':'미국 반도체 매도가 국내 장전 가격에도 반영됐습니다.'}]
    d['factors']=[{'label':'물가·유가','metric':'물가 압력과 에너지 비용','detail':'미국 반도체 약세와 원화 약세가 겹쳤습니다.','tone':'warning'},{'label':'반도체','metric':'SOXX -2.74%','detail':'9월 10일 미국 정규장','tone':'warning'},{'label':'금리차','metric':'10년-2년 +0.39%p','detail':'FRED 9월 10일 · 10년-3개월 +0.95%p','tone':'info'}]
    d['flows']={'program':None,'kospi200FuturesForeign':None,'futuresUnit':'계약','futuresAsOfLabel':'9월 10일 확정 수급 전체 묶음 미확인'}
    d['memory']=[{'label':'DDR5 16Gb · 9/10 19:10 KST','value':'$54.333','change':'-0.31% 일간'},{'label':'DDR4 16Gb · 9/10 19:10 KST','value':'$90.50','change':'-0.55% 일간'},{'label':'512Gb TLC 웨이퍼 · 9/9 공개','value':'$20.146','change':'-2.71% 주간'}]
    d['scenarios']=[{'id':'base','label':'기본 · 50%','range':'KOSPI 6,800~7,000','summary':'갭 하락 뒤 전일 저점 주변에서 매도를 소화합니다.','conditions':['6,800 방어','7,000 이하','반도체 낙폭 축소'],'invalidation':'6,800 이탈 또는 7,000 돌파'}, {'id':'bull','label':'강세 · 20%','range':'KOSPI 7,000 초과~7,150','summary':'메모리주 반등과 외국인 매수로 7,000선을 회복합니다.','conditions':['7,000 초과','반도체 동반 반등','외국인·프로그램 순매수'],'invalidation':'7,000 아래 재진입'}, {'id':'bear','label':'약세 · 30%','range':'KOSPI 6,550~6,800 미만','summary':'환율 상승과 반도체 매도가 지수 하락을 키웁니다.','conditions':['6,800 미만','반도체 약세 지속','환율 상승'],'invalidation':'6,800 회복'}]
    d['strategyLevels']=[{'asset':'KOSPI','support':'6,800 / 6,550','pivot':'7,000','resistance':'7,150'},{'asset':'KODEX 레버리지','support':'109,815원','pivot':'112,500원','resistance':'115,000원'}]
    d['scenarios'][0]['conditions']=['6,800 이상','7,000 이하','외국인 순매도 1조원 이내']
    d['scenarios'][1]['conditions']=['7,000 초과','외국인 현물 순매수','프로그램 전체 순매수']
    d['scenarios'][2]['conditions']=['6,800 미만','외국인 현물 순매도','프로그램 전체 순매도']
    d['events']=[{'time':'9월 11일 21:30 KST','name':'미국 8월 CPI','path':'물가와 정책금리 기대'},{'time':'9월 17일 03:00 KST','name':'FOMC·경제전망','path':'정책금리와 장기금리'}]
    d['checklist']=[{'id':'support','label':'KOSPI 6,800 방어'},{'id':'rebound','label':'7,000 회복과 메모리 동반 반등'},{'id':'flows','label':'외국인·프로그램 순매수 동반 여부'}]
    d['technical']['note']='9월 10일 확정 일봉과 9월 11일 분석 기준선입니다.'
    for x in d['technical']['instruments']:
        row=kospi if x['id']=='KOSPI' else kodex; levels=[6800,7000,7150] if x['id']=='KOSPI' else [109815,112500,115000]
        x.update(asOf='2026-09-10T15:30:00+09:00',asOfLabel='9월 10일 정규장 종가',points=[{'label':l,'value':num(row[k])} for l,k in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('종가','closePrice')]],levels=[{'label':l,'value':v} for l,v in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=f'1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}')
    d['sources']=[{'label':'KOSPI 일봉','href':ev('KOSPI-fresh')['url']},{'label':'NXT','href':ev('NXT')['url']},{'label':'BLS CPI','href':'https://www.bls.gov/schedule/news_release/cpi.htm'},{'label':'FRED','href':'https://fred.stlouisfed.org/series/T10Y2Y'}]
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
            t=re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+',r'\g<1>market-2026-09-11.html',t)
            count=t.count('<article class="market-article-item"');t=re.sub(r'(일일시황 <span class="article-category-count">)\d+',r'\g<1>'+str(count),t);t=re.sub(r'최신순 · \d+편',f'최신순 · {count}편',t)
        write(path,t)
    for path in ['index.html','articles/index.html']:
        t=read(path); cats=re.findall(r'<article class="[^"]*" data-category="([^"]+)"',t)
        for cat in ['all','market','essay','health']:
            count=len(cats) if cat=='all' else cats.count(cat)
            t=re.sub(r'(data-category-count="'+cat+r'">)\d+',lambda m:m[1]+str(count),t)
        write(path,t)
    sm=base('sitemap.xml').replace('</urlset>','<url><loc>https://www.hpmplab.com/articles/market-2026-09-11.html</loc><lastmod>2026-09-11</lastmod></url>\n</urlset>')
    for url in ['https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html']:
        sm=re.sub(r'(<loc>'+re.escape(url)+r'</loc>\s*<lastmod>)[^<]+',r'\g<1>2026-09-11',sm)
    write('sitemap.xml',sm)
    write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 {issued}, 데이터 최종 확인 {cutoff}, 한국 개장 전.\n- 직전 KOSPI 7,033.92(-0.25%), KODEX 115,000원(-0.50%), 9월 10일 정규장.\n- 핵심: 유가·물가 압력, 미국 반도체 매도, 국내 메모리주 NXT 동반 약세.\n- 대응 15/45/40. 기본 6800~7000(50%), 강세 7000초과~7150(20%), 약세 6550~6800미만(30%), 경로 6450~7250(90%). KODEX 109815/112500/115000.\n- 다음: 9/11 CPI 21:30, 9/17 FOMC 03:00 KST.\n- 보고서 reports/2026-09-11.md, 취재 research/evidence/2026-09-11/overnight-notes.md. 차트 charts/us_yield_spreads_90d_2026-09-11.png 및 long_term.\n- 대시보드 assets/data/market-dashboard-{sid}.json 및 latest.json.\n- 직전 정산 research/evaluation/outcomes/2026-09-10-0828-same-close.json, 누적 research/evaluation/generated/latest.md. 트리거 원문은 미확인.\n')
    write('STATE.md',read('STATE.md')+f"- NXT 삼성 {nxt['005930']['closePrice']}원({nxt['005930']['fluctuationsRatio']}%), SK하이닉스 {nxt['000660']['closePrice']}원({nxt['000660']['fluctuationsRatio']}%); 원/달러 {fx['closePrice']}원({fx['localTradedAt']}).\n- 수급은 서울신문 KRX 마감 인용으로 외국인 -2조4,907억원, 프로그램 -2조5,358억원. 평가용 최종 원문 전체 묶음은 미확인.\n- Oracle·TSMC 수요는 반대 근거. NVIDIA 규제 조사는 공식 결정·독립 가격반응 부재로 보조, 강제청산 추정은 실현액이 아니므로 제외.\n")
    if seal:
        f=json.loads(read('research/evaluation/forecasts/2026-09-10-0828-same-close.json'))
        f.update(forecastId=fid,reportPath='reports/2026-09-11.md',reportSha256=sha('reports/2026-09-11.md'),issuedAt=issued,dataCutoffAt=cutoff,marketRegime='risk_off',target={'sessionDate':'2026-09-11','horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-09-10'},reference={'price':num(kospi['closePrice']),'asOf':'2026-09-10T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':7000,'high':7150,'probability':.2},'base':{'low':6800,'high':7000,'probability':.5},'bear':{'low':6550,'high':6800,'probability':.3}},pathEnvelope={'low':6450,'high':7250,'coverage':.9},posture={'attack':15,'wait':45,'defense':40},drivers=[{'id':'oil-inflation','rank':1,'claim':'유가·물가 압력이 반도체 밸류에이션을 누른다.','validationMetric':'브렌트·미국 금리'}, {'id':'domestic-chip-selling','rank':2,'claim':'국내 메모리주 동반 약세가 지수 하방 압력으로 이어진다.','validationMetric':'삼성전자·SK하이닉스·KOSPI'}, {'id':'fx-pressure','rank':3,'claim':'원화 약세가 외국인 매도 위험을 높인다.','validationMetric':'달러/원·외국인 현물'}])
        for group in f['scenarioTriggers'].values():
            group['observeBy']='2026-09-11T15:20:00+09:00'
            for c in group['conditions']:
                oldv=c['threshold'];c['threshold']={7150:7000,7000:6800}[oldv];c['description']=c['description'].replace(f'{oldv:,}',f"{c['threshold']:,}")
        for scenario,op in [('bull','gt'),('bear','lt')]:
            for metric,label in [('foreign_cash','외국인 현물'),('program_total','프로그램 전체')]:
                f['scenarioTriggers'][scenario]['conditions'].append({'id':scenario+'-'+metric,'description':label+(' 순매수' if op=='gt' else ' 순매도'),'metricId':metric,'operator':op,'threshold':0,'source':'Naver Finance KOSPI 수급 (억원)'})
        f['scenarioTriggers']['base']['conditions'].append({'id':'base-foreign','description':'외국인 현물 순매도가 1조원 이내','metricId':'foreign_cash','operator':'gte','threshold':-10000,'source':'Naver Finance KOSPI 수급 (억원)'})
        f.pop('contentHash',None);f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();dump('research/evaluation/forecasts/'+fid+'.json',f)
        files=['articles/market-2026-09-11.html','assets/data/market-dashboard-latest.json','assets/data/market-dashboard-'+sid+'.json','assets/images/articles/'+IMAGE,'charts/us_yield_spreads_90d_2026-09-11.png','charts/us_yield_spreads_long_term_2026-09-11.png','index.html','articles/index.html','articles/market.html','sitemap.xml']
        dump('research/evidence/2026-09-11/seal.json',{'forecastId':fid,'issuedAt':issued,'dataCutoffAt':cutoff,'snapshotId':sid,'files':files})
    print('SEALED' if seal else 'DRAFT',issued,cutoff)
if __name__=='__main__':main('--seal' in sys.argv)
