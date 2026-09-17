"""9월 18일 장전 원고·시세를 정적 사이트와 전망 계약에 반영한다."""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

R=Path(__file__).resolve().parents[3]
E=Path(__file__).parent
spec=importlib.util.spec_from_file_location('previous_build',E.parent/'2026-09-17'/'build.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
TITLE='미국 반도체 반등, KOSPI는 외국인 매도를 넘을까'
SUMMARY='미국 반도체주가 유가·금리 하락에 반등했습니다. KOSPI 6,850선 돌파는 국내 외국인 수급이 가릅니다.'
IMAGE='market-2026-09-18-chip-rebound-foreign-flow-1200x630.webp'
ALT='밝은 서울 아침의 메모리 칩과 웨이퍼, 건물 사이로 이동하는 금빛 자금의 흐름'
URL='https://www.hpmplab.com/articles/market-2026-09-18.html'
TZ=dt.timezone(dt.timedelta(hours=9))
OLD_TITLE='연준 금리 인상 뒤 원화 약세, 반도체 반등의 다음 시험'
OLD_SUMMARY='연준의 추가 긴축 신호와 원화 약세가 전날 반도체 반등을 시험합니다. KOSPI 6,600선과 외국인 수급이 오늘의 기준입니다.'
OLD_IMAGE='market-2026-09-17-fed-rate-memory-1200x630.webp'
OLD_ALT='밝은 서울 아침의 메모리 웨이퍼와 금리 상승선'

def read(path): return (R/path).read_text(encoding='utf-8')
def write(path,value): (R/path).write_text(value,encoding='utf-8',newline='\n')
def dump(path,value): write(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def ev(key): return json.loads((E/(key+'.json')).read_text(encoding='utf-8'))
def number(value): return float(str(value).replace(',',''))
def market(key): return ev('yahoo-'+key)['data']['chart']['result'][0]['meta']
def fmt_market(key):
    m=market(key)
    return f"{m['regularMarketPrice']:,.2f} · {m['regularMarketChangePercent']:+.2f}%"
def stamp_market(key): return dt.datetime.fromtimestamp(market(key)['regularMarketTime'],TZ).isoformat()
def change(t,issued,hhmm):
    return (t.replace(OLD_IMAGE,IMAGE).replace('market-2026-09-17','market-2026-09-18')
      .replace(OLD_TITLE,TITLE).replace(OLD_SUMMARY,SUMMARY).replace(OLD_ALT,ALT)
      .replace('9월 17일 KOSPI 장전 시황 읽기','9월 18일 KOSPI 장전 시황 읽기')
      .replace('아침빛을 받는 메모리 칩 스택과 금빛 유리 문턱',ALT)
      .replace('2026-09-17T08:13:28+09:00',issued).replace('2026-09-17T08:19:59+09:00',issued)
      .replace('2026.09.17 · 08:13','2026.09.18 · '+hhmm)
      .replace('연준의 금리 인상과 원화 약세가 전날 반도체 반등을 시험합니다.','유가·금리 하락에 미국 반도체가 반등했습니다. 국내 외국인 수급이 상승의 지속성을 가릅니다.'))

def main(seal=False):
    if seal and (E/'seal.json').exists(): raise RuntimeError('이미 봉인됨')
    now=dt.datetime.now(TZ).replace(microsecond=0)
    if not 8<=now.hour<9: raise RuntimeError('장전 발행 구간을 벗어남')
    issued=now.isoformat();sid=now.strftime('%Y%m%d-%H%M');hhmm=now.strftime('%H:%M')
    fid='2026-09-18-'+now.strftime('%H%M')+'-same-close'
    cutoff=max(ev(x)['fetchedAt'] for x in ('NXT','FX','yahoo-NQF','yahoo-ESF'))
    if seal and (now-dt.datetime.fromisoformat(cutoff)).total_seconds()>300: raise RuntimeError('핵심 시세 5분 초과')
    assert ev('KOSPI-basic')['data']['marketStatus']=='PREOPEN'
    assert ev('KOSPI-basic')['data']['closePrice']=='6,715.41'
    fx=ev('FX')['data']['exchangeInfo']
    nxt={x['itemCode']:x for x in ev('NXT')['data']['datas']}
    assert all(x['localTradedAt'].startswith('2026-09-18') and x['marketSessionType']=='preMarket' for x in nxt.values())
    manuscript=read('research/evidence/2026-09-18/manuscript.md')
    body=manuscript.split('\n',1)[1].strip()
    table='\n\n## 장전 가격\n\n|항목|가격·변화|출처 시각|\n|---|---:|---|\n'
    table+='|KOSPI 전일 종가|6,715.41 · -0.04%|2026-09-17 정규장 종가|\n'
    table+='|KODEX 레버리지 전일 종가|103,490원 · -0.09%|2026-09-17 정규장 종가|\n'
    for code,label in [('005930','삼성전자 NXT'),('000660','SK하이닉스 NXT')]:
        x=nxt[code];table+=f"|{label}|{x['closePrice']}원 · {x['fluctuationsRatio']}%|{x['localTradedAt']}|\n"
    table+=f"|달러/원 하나은행 고시|{fx['closePrice']}원 · {fx['fluctuationsRatio']}%|{fx['localTradedAt']}|\n"
    for key,label in [('NQF','Nasdaq100 선물'),('ESF','S&P500 선물'),('BZF','브렌트 선물'),('CLF','WTI 선물')]:
        table+=f"|{label}|{fmt_market(key)}|{stamp_market(key)} · 지연 시세|\n"
    table+='\n[NXT](https://stock.naver.com/api/polling/domestic/NXT/stock?itemCodes=005930,000660) · [환율](https://api.stock.naver.com/marketindex/exchange/FX_USDKRW) · [Nasdaq100 선물](https://finance.yahoo.com/quote/NQ=F/) · [S&P500 선물](https://finance.yahoo.com/quote/ES=F/)\n\nNXT는 대체거래소 장전 거래, 미국 선물은 지연 시세다.'
    body+=table
    old=read('articles/market-2026-09-17.html')
    prefix=change(old.split('<article class="editorial-article reading-article">')[0],issued,hhmm)
    schema=re.search(r'<script type="application/ld\+json">(.*?)</script>',prefix,re.S)
    if schema:
        obj=json.loads(schema[1]);obj.update(headline=TITLE,description=SUMMARY,datePublished=issued,dateModified=issued,mainEntityOfPage=URL)
        obj['image']['url']='https://www.hpmplab.com/assets/images/articles/'+IMAGE
        prefix=prefix[:schema.start()]+'<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False)+'</script>'+prefix[schema.end():]
    charts=''.join(f'<figure class="article-chart article-inline-media"><img src="../charts/us_yield_spreads_{kind}_2026-09-18.png" width="1600" height="900" loading="lazy" alt="미국 장단기 금리차 {label}"><figcaption>9월 17일 FRED: 10년-2년 +0.27%p · 10년-3개월 +0.82%p.</figcaption></figure>' for kind,label in [('90d','최근 90일'),('long_term','최근 2년')])
    closing=old[old.index('</div></article></main>'):]
    markdown_html=previous.previous.prior.prior.prior.prior.markdown_html
    article=prefix+f'<article class="editorial-article reading-article"><header class="article-hero"><h1>{TITLE}</h1><p class="article-dek">{SUMMARY}</p><div class="article-meta"><strong><a href="../about.html">HPMPLab</a></strong><time datetime="{issued}">2026.09.18 · {hhmm} KST</time><span>장전 브리핑</span></div><p class="article-disclosure">작성 {hhmm} KST · 데이터 최종 확인 {cutoff}. 미국 정규장은 9월 17일, 국내 NXT·환율·미국 선물은 장전 표의 개별 시각 기준이다. 특정 상품의 매매 권유가 아닌 조건부 시장 분석이다.</p><figure class="article-hero-media"><img src="../assets/images/articles/{IMAGE}" width="1200" height="630" decoding="async" fetchpriority="high" alt="{ALT}"></figure></header><div class="article-body" id="article-body">'+markdown_html(body).replace('table-scroll','article-table-wrap').replace('<table>','<table class="article-data-table">')+charts+closing
    write('articles/market-2026-09-18.html',article)
    report='# 2026-09-18 KOSPI·KODEX 일일 리서치\n\n'+f'작성 {issued} / 데이터 최종 확인 {cutoff} / 한국 장전.\n\n확정 사실은 출처 시각 기준, 시나리오와 확률은 조건부 전망이다.\n\n'+body+'\n\n## 직전 전망 정산\n\n'+read('research/evidence/2026-09-18/settlement-note.md')+'\n\n## 취재 근거와 확인 시각\n\n'+read('research/evidence/2026-09-18/overnight-notes.md')+'\n\n![최근 90일](../charts/us_yield_spreads_90d_2026-09-18.png)\n\n![최근 2년](../charts/us_yield_spreads_long_term_2026-09-18.png)\n'
    report+='\n## 미국 정규장 종목별 확인\n\n|종목|9/17 종가|전일 대비|\n|---|---:|---:|\n'
    for ticker in ('QQQ','TQQQ','SOXX','SMH','NVDA','AMD','MU','AVGO'):
        m=market(ticker);report+=f"|{ticker}|{m['regularMarketPrice']:.2f}|{m['regularMarketChangePercent']:+.2f}%|\n"
    write('reports/2026-09-18.md',report)
    d=json.loads(read('assets/data/market-dashboard-20260917-0813.json'))
    d.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff,marketState='한국 장전',sourceLabel='미국 9월 17일 정규장 · 국내 9월 17일 종가 · 9월 18일 장전',latestArticle={'title':TITLE,'href':'market-2026-09-18.html'},headline=TITLE,summary=SUMMARY)
    for x in d['markets']:
        if x['id']=='KOSPI':x.update(value=6715.41,changePercent=-.04,open=6779.02,high=6795.53,low=6697.85,previousClose=6717.97,asOf='2026-09-17T15:30:00+09:00',asOfLabel='9월 17일 종가',stateLabel='정규장 종가',flows=[]);x.pop('breadth',None)
        else:x.update(value=822.18,changePercent=.76,open=820.16,high=826.22,low=814.98,previousClose=815.98,asOf='2026-09-17T15:30:00+09:00',asOfLabel='9월 17일 종가',stateLabel='정규장 종가',flows=[])
    d['stance']={'label':'수급 확인 속 관망','attack':25,'wait':50,'defense':25,'note':'미국 반도체 반등이 국내 외국인 매수로 이어지는지 봅니다.'}
    d['checkpoints']=[{'label':'Nasdaq100 선물','value':fmt_market('NQF'),'detail':stamp_market('NQF')+' · 지연','tone':'info'},{'label':'원/달러','value':fx['closePrice']+'원','detail':fx['localTradedAt']+' 고시','tone':'warning'},{'label':'삼성전자 NXT','value':nxt['005930']['closePrice']+'원','detail':nxt['005930']['localTradedAt'],'tone':'info'},{'label':'SK하이닉스 NXT','value':nxt['000660']['closePrice']+'원','detail':nxt['000660']['localTradedAt'],'tone':'info'}]
    d['changes']=[{'label':'KOSPI','before':'6,717.97','after':'6,715.41','meaning':'9월 17일 장중 상승분을 반납하고 약보합으로 마쳤습니다.'},{'label':'미국 10년물','before':'5.01%','after':'4.94%','meaning':'유가 하락과 함께 7bp 내려 반도체주 부담이 줄었습니다.'}]
    d['factors']=[{'label':'미국 반도체','metric':'SOXX +3.39% · MU +5.50%','detail':'9월 17일 미국 정규장','tone':'positive'},{'label':'국내 수급','metric':'외국인 약 2.46조원 순매도','detail':'9월 17일 KRX+NXT 누적 보도','tone':'warning'},{'label':'금리차','metric':'10년-2년 +0.27%p','detail':'FRED 9월 17일 · 10년-3개월 +0.82%p','tone':'info'}]
    d['flows']={'program':None,'kospi200FuturesForeign':None,'futuresUnit':'계약','futuresAsOfLabel':'장전 미개시'}
    d['memory']=[{'label':'DDR5 16Gb · 9/17 19:10 KST','value':'$55.233','change':'+0.73% 일간'},{'label':'DDR4 16Gb · 9/17 19:10 KST','value':'$86.000','change':'-1.85% 일간'},{'label':'DDR4 8Gb · 9/17 19:10 KST','value':'$46.143','change':'+0.78% 일간'}]
    d['scenarios']=[{'id':'base','label':'기본 · 50%','range':'KOSPI 6,650~6,850','summary':'반도체 반등을 받아들이되 외국인 매수 확인 전 상단이 제한됩니다.','conditions':['6,650 이상','6,850 이하','외국인 매도 축소'],'invalidation':'6,650 이탈 또는 6,850 돌파'},{'id':'bull','label':'강세 · 30%','range':'KOSPI 6,850 초과~7,000','summary':'메모리주 상승과 외국인·프로그램 순매수가 함께 이어집니다.','conditions':['6,850 초과','외국인 현물 순매수','프로그램 전체 순매수'],'invalidation':'6,850 아래 재진입'},{'id':'bear','label':'약세 · 20%','range':'KOSPI 6,450~6,650 미만','summary':'환율과 외국인 매도가 미국 반도체 반등을 압도합니다.','conditions':['6,650 미만','외국인 현물 순매도','프로그램 전체 순매도'],'invalidation':'6,650 회복'}]
    d['strategyLevels']=[{'asset':'KOSPI','support':'6,650 / 6,450','pivot':'6,850','resistance':'7,000'},{'asset':'KODEX 레버리지','support':'102,825원','pivot':'103,490원','resistance':'106,520원'}]
    d['events']=[{'time':'9월 18일 09:00 KST','name':'한국 정규장 개장','path':'반도체와 외국인 수급'},{'time':'9월 18일 23:00 KST','name':'미국 주별 고용 지표','path':'미 국채금리와 달러'}]
    d['checklist']=[{'id':'support','label':'KOSPI 6,650 방어'},{'id':'rebound','label':'6,850 돌파와 메모리 동반 강세'},{'id':'flows','label':'외국인·프로그램 수급 동행 여부'}]
    d['technical']['note']='9월 17일 확정 일봉과 9월 18일 분석 기준선입니다.'
    for x in d['technical']['instruments']:
        levels=[6650,6850,7000] if x['id']=='KOSPI' else [102825,103490,106520]
        x.update(asOf='2026-09-17T15:30:00+09:00',asOfLabel='9월 17일 정규장 종가',levels=[{'label':label,'value':value} for label,value in zip(['1차 지지','반등 기준','저항'],levels)],interpretation=f'1차 지지 {levels[0]:,} · 반등 기준 {levels[1]:,} · 저항 {levels[2]:,}')
        points=[6779.02,6795.53,6697.85,6715.41] if x['id']=='KOSPI' else [105785,106520,102825,103490]
        x['points']=[{'label':label,'value':value} for label,value in zip(['시가','고가','저가','종가'],points)]
    d['sources']=[{'label':'미 재무부 금리','href':'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=202609'},{'label':'미국 정규장 SOXX','href':'https://finance.yahoo.com/quote/SOXX/'},{'label':'KOSPI 종가','href':'https://www.newspim.com/news/view/20260917000942'},{'label':'FRED','href':'https://fred.stlouisfed.org/series/T10Y2Y'},{'label':'TrendForce 현물','href':'https://www.trendforce.com/price/dram/dram_spot'}]
    dump('assets/data/market-dashboard-latest.json',d)
    if seal:dump('assets/data/market-dashboard-'+sid+'.json',d)
    for path,cls in [('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')]:
        t=read(path);m=re.search('<article class="'+re.escape(cls)+'"[^>]*>.*?</article>',t,re.S)
        if not m:raise RuntimeError('목록 카드 없음: '+path)
        card=m[0];t=t[:m.start()]+change(card,issued,hhmm)+'\n'+card.replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')+t[m.end():]
        def schema_change(match):
            obj=json.loads(match[1]);obj['dateModified']=issued
            def walk(v):
                if isinstance(v,dict):
                    if v.get('@type')=='ItemList' and v.get('itemListElement'):
                        v['itemListElement'].insert(0,json.loads(change(json.dumps(v['itemListElement'][0],ensure_ascii=False),issued,hhmm)))
                        for i,item in enumerate(v['itemListElement'],1):item['position']=i
                        v['numberOfItems']=len(v['itemListElement'])
                    for value in v.values():walk(value)
                elif isinstance(v,list):
                    for value in v:walk(value)
            walk(obj);return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,indent=2)+'</script>'
        t=re.sub(r'<script type="application/ld\+json">(.*?)</script>',schema_change,t,flags=re.S)
        head,rest=t.split('</head>',1);t=head.replace(OLD_IMAGE,IMAGE)+'</head>'+rest
        if path=='articles/market.html':
            t=re.sub(r'(id="market-(?:latest-article-link|summary-article-link)" href=")[^"]+',r'\g<1>market-2026-09-18.html',t)
            t=t.replace('KOSPI 6,600선과 외국인·프로그램 수급의 방향을 함께 봅니다.','미국 반도체 반등이 외국인·프로그램 매수로 이어지는지 봅니다.')
            t=t.replace('연준의 금리 인상과 원화 약세가 전날 반도체 반등을 시험합니다.','유가·금리 하락에 미국 반도체가 반등했습니다. 국내 외국인 수급이 상승의 지속성을 가릅니다.')
            t=t.replace('원화 약세 속 반도체와 국내 수급','미국 반도체 반등과 국내 외국인 수급')
            count=t.count('<article class="market-article-item"');t=re.sub(r'(일일시황 <span class="article-category-count">)\d+',r'\g<1>'+str(count),t);t=re.sub(r'최신순 · \d+편',f'최신순 · {count}편',t)
        write(path,t)
    for path in ('index.html','articles/index.html'):
        t=read(path);cats=re.findall(r'<article class="[^"]*" data-category="([^"]+)"',t)
        for cat in ('all','market','essay','health'):
            count=len(cats) if cat=='all' else cats.count(cat)
            t=re.sub(r'(data-category-count="'+cat+r'">)\d+',lambda m:m[1]+str(count),t)
        write(path,t)
    sm=read('sitemap.xml').replace('</urlset>','<url><loc>'+URL+'</loc><lastmod>2026-09-18</lastmod></url>\n</urlset>')
    for url in ('https://www.hpmplab.com/','https://www.hpmplab.com/articles/','https://www.hpmplab.com/articles/market.html'):
        sm=re.sub(r'(<loc>'+re.escape(url)+r'</loc>\s*<lastmod>)[^<]+',r'\g<1>2026-09-18',sm)
    write('sitemap.xml',sm)
    write('STATE.md',f'# KOSPI·KODEX 리서치 상태\n\n- 작성 {issued}, 데이터 최종 확인 {cutoff}, 한국 장전.\n- 직전 KOSPI 6,715.41(-0.04%), KODEX 103,490원(-0.09%), 9월 17일 정규장.\n- 핵심: 유가·미 국채금리 하락에 미국 반도체가 반등했으나 전날 국내 외국인 약 2.46조원 순매도가 지속됐다. 미국 ETF의 전날 한국장 후행분을 중복 가산하지 않는다.\n- 대응 25/50/25. 기본 6650~6850(50%), 강세 6850초과~7000(30%), 약세 6450~6650미만(20%), 경로 6350~7050(90%). KODEX 102825/103490/106520.\n- 보고서 reports/2026-09-18.md, 취재 research/evidence/2026-09-18/overnight-notes.md. 차트 charts/us_yield_spreads_90d_2026-09-18.png 및 long_term.\n- 대시보드 assets/data/market-dashboard-{sid}.json 및 latest.json. 직전 정산 research/evidence/2026-09-18/settlement-note.md.\n- 다음: 9/18 09:00 한국장 개장, 23:00 미국 주별 고용 지표.\n- 상위 사건과 제외 근거는 취재 노트에 보존.\n')
    if seal:
        f=json.loads(read('research/evaluation/forecasts/2026-09-17-0813-same-close.json'))
        f.update(forecastId=fid,reportPath='reports/2026-09-18.md',reportSha256=hashlib.sha256((R/'reports/2026-09-18.md').read_bytes()).hexdigest(),issuedAt=issued,dataCutoffAt=cutoff,marketState='preopen',evaluationBucket='preopen',marketRegime='mixed',target={'sessionDate':'2026-09-18','horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':'2026-09-17'},reference={'price':6715.41,'asOf':'2026-09-17T15:30:00+09:00','kind':'previous_close'},scenarios={'bull':{'low':6850,'high':7000,'probability':.3},'base':{'low':6650,'high':6850,'probability':.5},'bear':{'low':6450,'high':6650,'probability':.2}},pathEnvelope={'low':6350,'high':7050,'coverage':.9},posture={'attack':25,'wait':50,'defense':25},supersedes=None,drivers=[{'id':'chip-rebound','rank':1,'claim':'미국 반도체 반등이 국내 메모리주의 장전 상승으로 전달된다.','validationMetric':'SOXX·MU·삼성전자·SK하이닉스'},{'id':'foreign-flow','rank':2,'claim':'전일 외국인 매도 이후 현물·프로그램 수급이 반등 지속성을 가른다.','validationMetric':'외국인·프로그램·KOSPI'},{'id':'oil-yield-relief','rank':3,'claim':'유가와 미 국채금리 하락이 성장주 부담을 일부 낮춘다.','validationMetric':'Brent·미국 10년물·KOSPI'}])
        thresholds={'bull-price':6850,'base-support':6650,'base-cap':6850,'bear-price':6650}
        for group in f['scenarioTriggers'].values():
            group['observeBy']='2026-09-18T15:20:00+09:00'
            for c in group['conditions']:
                if c['id'] in thresholds:c['threshold']=thresholds[c['id']];c['description']='KOSPI '+str(c['threshold'])+' '+c['operator']
        f.pop('contentHash',None);f['contentHash']=hashlib.sha256(json.dumps(f,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        dump('research/evaluation/forecasts/'+fid+'.json',f)
        dump('research/evidence/2026-09-18/seal.json',{'forecastId':fid,'issuedAt':issued,'dataCutoffAt':cutoff,'snapshotId':sid})
    print('SEALED' if seal else 'DRAFT',issued,cutoff)
if __name__=='__main__':main('--seal' in sys.argv)
