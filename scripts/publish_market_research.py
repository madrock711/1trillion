"""준비된 일별 원고를 재개 가능한 발행 트랜잭션으로 실행한다. 매매 기능 없음."""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.request

from collect_market_evidence import collect, sources, TZ

ROOT = Path(__file__).resolve().parents[1]
BASES = ['https://www.hpmplab.com', 'https://main.d2pg7r2qjjb9u9.amplifyapp.com']


def now(): return dt.datetime.now(TZ).isoformat(timespec='microseconds')
def read(path): return (ROOT / path).read_text(encoding='utf-8-sig')
def load(path): return json.loads(read(path))
def write(path, value):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding='utf-8', newline='\n')
def dump(path, value): write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def digest(raw): return hashlib.sha256(raw).hexdigest()
def num(value): return float(str(value).replace(',', ''))


def evaluation():
    spec = importlib.util.spec_from_file_location('market_evaluation', ROOT/'scripts/evaluate_market_research.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def insert_card(page, card, date, kind):
    """오늘 카드만 교체/삽입. 과거 카드의 href/image/body는 바꾸지 않는다."""
    pattern = r'<article class="' + kind + r'"[^>]*>.*?</article>'
    matches = list(re.finditer(pattern, page, re.S))
    for match in matches:
        if f'market-{date}.html' in match[0]:
            return page[:match.start()] + card + page[match.end():]
    if not matches:
        raise ValueError('기사 카드 삽입 위치 없음')
    return page[:matches[0].start()] + card + '\n' + page[matches[0].start():]


def update_ld(page, item):
    def replace(match):
        data = json.loads(match[1])
        for node in data.get('@graph', [data]):
            main = node.get('mainEntity', {})
            if isinstance(main, dict) and 'itemListElement' in main:
                items = [x for x in main['itemListElement'] if x.get('url') != item['url']]
                items.insert(0, item.copy())
                for position, entry in enumerate(items, 1): entry['position'] = position
                main['itemListElement'] = items
                main['numberOfItems'] = len(items)
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, indent=2) + '</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', replace, page, flags=re.S)


def valid_nxt(row, date, fetched):
    try:
        at = dt.datetime.fromisoformat(row['localTradedAt'])
        end = dt.datetime.fromisoformat(fetched)
        price, low, high = [num(row[k]) for k in ['closePrice', 'lowPrice', 'highPrice']]
        return (row['itemCode'] in {'005930','000660'} and row['marketStatus'] == 'OPEN'
                and at.astimezone(TZ).date().isoformat() == date
                and 0 <= (end-at).total_seconds() <= 300 and low <= price <= high)
    except (KeyError, ValueError, TypeError): return False


class Publisher:
    def __init__(self, package):
        self.package_path = Path(package).resolve()
        self.p = json.loads(self.package_path.read_text(encoding='utf-8-sig'))
        self.date = self.p['date']
        self.dir = Path('research/evidence') / self.date
        self.state_path = self.dir/'pipeline-state.json'
        self.status_path = self.dir/'run-status.json'
        self.s = load(self.state_path) if (ROOT/self.state_path).exists() else {'packageHash':digest(self.package_path.read_bytes()), 'startedAt':now()}
        if self.s['packageHash'] != digest(self.package_path.read_bytes()):
            raise ValueError('실행 중인 package 변경 금지: 기존 발행 상태와 대조 필요')
        self.save()

    def save(self):
        self.s['updatedAt'] = now()
        target = ROOT/self.state_path
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix('.tmp')
        temp.write_text(json.dumps(self.s, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        temp.replace(target)

    def stage(self, name, **evidence):
        self.s.setdefault('stages', {})[name] = {'completedAt':now(), **evidence}
        self.save()
        status = load(self.status_path) if (ROOT/self.status_path).exists() else {'startedAt':self.s['startedAt'], 'stages':{}}
        status['status'] = 'publishing'
        status.setdefault('stages', {})[name] = now()
        status.update(updatedAt=now(), pipeline=str(self.state_path).replace('\\','/'))
        dump(self.status_path, status)
        print(name, json.dumps(evidence, ensure_ascii=False), flush=True)

    def run(self, command, check=True):
        env = dict(os.environ, PYTHONUTF8='1', TEMP=str(ROOT/'.tmp-market-tests'), TMP=str(ROOT/'.tmp-market-tests'))
        (ROOT/'.tmp-market-tests').mkdir(exist_ok=True)
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
        self.s.setdefault('commands', []).append({'at':now(), 'command':command, 'exitCode':result.returncode,
                                                  'output':result.stdout[-2000:], 'error':result.stderr[-1500:]})
        self.save()
        if result.returncode and check:
            raise RuntimeError(f'명령 exit {result.returncode}: {command}\n{result.stdout[-1500:]}\n{result.stderr[-1500:]}')
        return result

    def preflight(self):
        if dt.datetime.now(TZ).date().isoformat() != self.date:
            raise ValueError('오늘 날짜와 package 날짜 불일치')
        if self.run(['git','branch','--show-current']).stdout.strip() != 'main':
            raise ValueError('main에서만 발행')
        if 'madrock711/1trillion' not in self.run(['git','remote','get-url','origin']).stdout:
            raise ValueError('원격 불일치')
        staged = self.run(['git','diff','--cached','--name-only']).stdout.strip()
        if staged: raise ValueError('기존 스테이징 변경 보존: 발행 시작 전 별도 처리 필요')
        for key in ['bodyPath','reportTemplate','dashboardPath','image','notesPath']:
            if not (ROOT/self.p[key]).is_file(): raise ValueError('필수 입력 없음: '+key)
        if sum(self.p['posture'].values()) != 100: raise ValueError('대응 합계 오류')
        if abs(sum(v['probability'] for v in self.p['scenarios'].values())-1) > 1e-9:
            raise ValueError('시나리오 확률 합계 오류')
        from PIL import Image
        if Image.open(ROOT/self.p['image']).size != (1200,630): raise ValueError('썸네일 크기 오류')
        for name in ['test_market_publication_pipeline.py','test_market_evidence_collection.py','test_market_run_gate.py','test_market_research_evaluation.py']:
            self.run([sys.executable,'-m','unittest','discover','-s','tests','-p',name])
        self.stage('validation', tests='publication pipeline + collection + run gate + evaluation')

    def final_query(self):
        output = ROOT/self.dir/'collections'/dt.datetime.now(TZ).strftime('final-%H%M%S-%f')
        output.mkdir(parents=True)
        manifest = collect(sources(final=True), output)
        if manifest['failed']: raise RuntimeError('최종조회 실패: '+','.join(manifest['failed']))
        ev = {key:json.loads((output/(key+'.json')).read_text(encoding='utf-8')) for key in manifest['sources']}
        self.s['quoteDir'] = str(output.relative_to(ROOT)).replace('\\','/')
        self.s['cutoff'] = max(x['fetchedAt'] for x in ev.values())
        self.stage('finalQuery', path=self.s['quoteDir'], cutoff=self.s['cutoff'])
        return ev

    def artifact(self, path, value):
        if (ROOT/path).exists(): raise ValueError('기존 불변 산출물 덮어쓰기 금지: '+str(path))
        # 의도부터 기록해 쓰기 직후 프로세스가 끊겨도 이번 실행의 미공개 파일만 복구한다.
        self.s.setdefault('draftArtifacts',{})[str(path)] = digest(value.encode('utf-8'))
        self.save();write(path,value)

    def recover_draft(self):
        if self.s.get('sealed') or self.s.get('contentCommit'): return
        for path, expected in self.s.get('draftArtifacts',{}).items():
            source=(ROOT/path).resolve()
            if not source.is_relative_to(ROOT.resolve()): raise ValueError('복구 경로 범위 오류')
            if source.exists():
                if digest(source.read_bytes()) != expected: raise ValueError('사용자 변경 가능성: 복구 중단 '+path)
                target=(ROOT/self.dir/'failed-build'/self.s.get('buildAttempt','unknown')/path).resolve()
                if not target.is_relative_to((ROOT/self.dir).resolve()): raise ValueError('보존 경로 범위 오류')
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.move(str(source),str(target))
        self.s['draftArtifacts']={};self.save()

    def build(self, ev):
        p = self.p; date = self.date; issued = now(); cutoff = self.s['cutoff']
        self.s['buildAttempt']=issued[11:].replace(':','').replace('.','').replace('+','-');self.save()
        prev = next(x for x in ev['KOSPI']['data'] if x['localTradedAt'] == p['previousSessionDate'])
        kb = ev['KOSPI-basic']['data']; current = kb['marketStatus'] == 'OPEN'
        if current:
            if not kb['localTradedAt'].startswith(date) or (dt.datetime.fromisoformat(cutoff)-dt.datetime.fromisoformat(kb['localTradedAt'])).total_seconds() > 300:
                raise ValueError('장중 기준값 시각 불일치/지연')
            kp = next(x for x in ev['KOSPI']['data'] if x['localTradedAt'] == date)
        else:
            if kb['marketStatus'] != 'PREOPEN': raise ValueError('현재 발행 가능한 시장상태 아님')
            kp = prev
        label = '장중' if current else '장전'
        rows = [['KOSPI '+('장중' if current else '전일 종가'), kp['closePrice'], kb['localTradedAt'] if current else p['previousSessionDate']+'T15:30:00+09:00']]
        le = next(x for x in ev['122630']['data'] if x['localTradedAt'] == (date if current else p['previousSessionDate']))
        rows.append(['KODEX '+('장중' if current else '전일 종가'), le['closePrice']+'원', cutoff if current else p['previousSessionDate']+'T15:30:00+09:00'])
        nxt = [r for r in ev['NXT']['data'].get('datas',[]) if valid_nxt(r,date,ev['NXT']['fetchedAt'])]
        rows += [[r['stockName']+' NXT', r['closePrice']+'원',r['localTradedAt']] for r in nxt]
        fx = ev['FX']['data']['exchangeInfo']
        if not fx['localTradedAt'].startswith(date): raise ValueError('환율 거래일 불일치')
        rows.append(['USD/KRW 하나은행 고시',fx['closePrice']+'원',fx['localTradedAt']])
        for symbol in ['NQF','ESF','BZF','CLF']:
            meta = ev['yahoo-'+symbol]['data']['chart']['result'][0]['meta']
            source_at = dt.datetime.fromtimestamp(meta['regularMarketTime'],TZ).isoformat(timespec='seconds')
            rows.append([symbol+' 최근 거래', f"{meta['regularMarketPrice']:,.2f}", source_at])
        table = '<div class="article-table-wrap"><table class="article-data-table"><thead><tr><th>항목</th><th>값</th><th>원천 기준 시각</th></tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
        markdown = '|항목|값|원천 기준 시각|\n|---|---:|---|\n'+'\n'.join('|'+ '|'.join(row)+'|' for row in rows)
        report = read(p['reportTemplate']).replace('{{issuedAt}}',issued).replace('{{cutoff}}',cutoff).replace('{{marketLabel}}',label).replace('{{fastTable}}',markdown)
        rp = f'reports/{date}.md'; ap = f'articles/market-{date}.html'
        if (ROOT/rp).exists() and not self.s.get('sealed'): raise ValueError('기존 일별 보고서 덮어쓰기 금지')
        self.artifact(rp,report)
        body = read(p['bodyPath']).replace('{{fastTable}}',table)
        article = self.render_article(body,issued,cutoff,label)
        self.artifact(ap,article)
        self.update_indexes(issued)
        dash = load(p['dashboardPath'])
        sid = date.replace('-','')+'-'+issued[11:16].replace(':','')
        dash.update(snapshotId=sid,generatedAt=issued,asOf=cutoff,asOfDisplay=cutoff,marketState='한국 '+label,sourceLabel=f'미국 {p["previousSessionDate"]} 정규장 · 한국 {date} '+label,
                    headline=p['title'],summary=p['summary'],latestArticle={'title':p['title'],'href':Path(ap).name})
        kospi = next(x for x in dash['markets'] if x['id']=='KOSPI')
        kospi.update(value=num(kp['closePrice']),changePercent=num(kp['fluctuationsRatio']),previousClose=num(prev['closePrice']) if current else num(prev['closePrice'])-num(prev['compareToPreviousClosePrice']),
                     open=num(kp['openPrice']),high=num(kp['highPrice']),low=num(kp['lowPrice']),asOf=rows[0][2],asOfLabel=rows[0][2],stateLabel='장중' if current else '전일 종가')
        dash['checkpoints']=[{'label':r[0],'value':r[1],'detail':r[2],'tone':'neutral'} for r in rows[2:]]
        if not nxt: dash['checkpoints'].insert(0,{'label':'NXT','value':'유효 가격 없음','detail':'원천 시각·상태 검증 실패','tone':'neutral'})
        for instrument in dash['technical']['instruments']:
            if instrument['id'] in ['KOSPI','KODEX']:
                value = kp if instrument['id']=='KOSPI' else le
                instrument.update(asOf=rows[0 if instrument['id']=='KOSPI' else 1][2],asOfLabel=label+' 기준',points=[{'label':a,'value':num(value[b])} for a,b in [('시가','openPrice'),('고가','highPrice'),('저가','lowPrice'),('현재' if current else '종가','closePrice')]])
        sp = f'assets/data/market-dashboard-{sid}.json'
        if (ROOT/sp).exists(): raise ValueError('불변 스냅샷 중복')
        self.artifact(sp,json.dumps(dash,ensure_ascii=False,indent=2)+'\n'); dump('assets/data/market-dashboard-latest.json',dash)
        module = evaluation(); bucket, market = module.expected_bucket(dt.datetime.fromisoformat(issued),dt.date.fromisoformat(date))
        fid = date+'-'+issued[11:19].replace(':','')+'-same-close'
        reference = {'price':num(kb['closePrice']) if current else num(prev['closePrice']), 'asOf':kb['localTradedAt'] if current else p['previousSessionDate']+'T15:30:00+09:00','kind':'live' if current else 'previous_close'}
        forecast = {'schemaVersion':1,'forecastId':fid,'visibility':'public','reportPath':rp,'reportSha256':digest((ROOT/rp).read_bytes()),'issuedAt':issued,'dataCutoffAt':cutoff,'marketState':market,'marketRegime':p['marketRegime'],'evaluationBucket':bucket,
                    'target':{'sessionDate':date,'horizon':'session_close','instrument':'KOSPI','leadSessions':0,'previousSessionDate':p['previousSessionDate']},'reference':reference,
                    'scenarios':p['scenarios'],'closeEnvelopeCoverage':0.9,'pathEnvelope':p['pathEnvelope'],'drivers':p['drivers'],'scenarioTriggers':p['scenarioTriggers'],'hypothesisTrials':[],'posture':p['posture'],'supersedes':None}
        forecast['contentHash'] = digest(json.dumps(forecast,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
        fp=f'research/evaluation/forecasts/{fid}.json'; self.artifact(fp,json.dumps(forecast,ensure_ascii=False,indent=2)+'\n')
        sessions=load('research/evaluation/trading-sessions.json'); sessions['sessions']=sorted(set(sessions['sessions']+[date]));sessions.update(asOf=cutoff,source=ev['KOSPI']['url']+' (전일 확정 일봉 및 오늘 시장상태)',rawHash=ev['KOSPI']['rawHash']);dump('research/evaluation/trading-sessions.json',sessions)
        module.validate_forecast(forecast,ROOT/fp,ROOT)
        write('STATE.md',p['stateText']+f'\n- 작성 {issued}, 데이터 최종 확인 {cutoff}, 한국 {label}.\n- reports/{date}.md · {sp} · {fp}.\n')
        self.s.update(sealed={'forecastId':fid,'forecastPath':fp,'snapshot':sp,'article':ap,'issuedAt':issued,'cutoff':cutoff},
                      files=list(dict.fromkeys(p['files']+[str(path.relative_to(ROOT)).replace('\\','/') for path in (ROOT/self.s['quoteDir']).glob('*.json')]+[rp,ap,sp,fp,'assets/data/market-dashboard-latest.json','research/evaluation/trading-sessions.json','STATE.md','index.html','articles/index.html','articles/market.html','sitemap.xml'])))
        self.stage('sealed', forecastId=fid)

    def render_article(self, body, issued, cutoff, label, published=None):
        p=self.p; e=html.escape; url=BASES[0]+f'/articles/market-{self.date}.html'; image=BASES[0]+'/'+p['image']
        ld={'@context':'https://schema.org','@type':'Article','headline':p['title'],'description':p['summary'],'image':{'@type':'ImageObject','url':image,'width':1200,'height':630},'datePublished':published or issued,'dateModified':published or issued,'articleSection':'시황분석','inLanguage':'ko-KR','mainEntityOfPage':url,'author':{'@type':'Organization','name':'HPMPLab','url':BASES[0]+'/about.html'},'publisher':{'@type':'Organization','name':'HPMPLab','url':BASES[0]+'/'}}
        pub = ' · 발행 '+published if published else ' · 발행 준비'
        return f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{e(p['title'])} | 연마</title><meta name="description" content="{e(p['summary'])}"><meta name="robots" content="index,follow,max-image-preview:large"><meta name="author" content="HPMPLab"><link rel="canonical" href="{url}">
<meta property="og:title" content="{e(p['title'])}"><meta property="og:description" content="{e(p['summary'])}"><meta property="og:type" content="article"><meta property="og:url" content="{url}"><meta property="og:site_name" content="연마 · HPMPLab"><meta property="og:locale" content="ko_KR"><meta property="og:image" content="{image}"><meta property="og:image:secure_url" content="{image}"><meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{e(p['imageAlt'])}">
<meta property="article:published_time" content="{published or issued}"><meta property="article:modified_time" content="{published or issued}"><meta property="article:section" content="시황분석"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(p['title'])}"><meta name="twitter:description" content="{e(p['summary'])}"><meta name="twitter:image" content="{image}">
<link rel="icon" href="../assets/icons/favicon.ico"><link rel="stylesheet" href="../style.css?v=20260913-1"><script defer src="../analytics.js?v=20260731-1"></script><script defer src="../assets/market-article-nav.js?v=20260826-1"></script><script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script></head>
<body><a class="skip-link" href="#article-body">본문으로 건너뛰기</a><header><div class="container"><div class="header-left"><a class="home-link" href="../" aria-label="연마 홈으로 이동"><img class="home-link-icon" src="../assets/icons/favicon-32x32.png" alt=""></a><p class="header-title"><a href="../">연마</a></p><nav aria-label="주요 이동"><a href="../">아티클</a><a href="../app.html">도구</a><a href="market.html" aria-current="page">시황</a></nav></div></div></header>
<main class="content-page article-page reading-shell"><nav class="content-page-nav market-article-view-tabs" aria-label="시장 대시보드 기능"><a href="market.html?view=analysis" aria-current="page">시황분석</a><a href="market.html?view=strategy">투자전략</a><a href="market.html?view=technical">기술적 분석</a></nav><article class="editorial-article reading-article"><header class="article-hero"><h1>{e(p['title'])}</h1><p class="article-dek">{e(p['summary'])}</p><div class="article-meta"><strong>HPMPLab</strong><time datetime="{issued}">{self.date.replace('-','.')} · 작성 {issued[11:16]}{(' · 발행 '+published[11:16]) if published else ''} KST</time><span>{label} 브리핑</span></div><p class="article-disclosure">작성 {issued} · 데이터 최종 확인 {cutoff}{pub}. 특정 상품의 매매 권유가 아닌 조건부 시장 분석입니다.</p><figure class="article-hero-media"><img src="../{p['image']}" width="1200" height="630" alt="{e(p['imageAlt'])}" fetchpriority="high"></figure></header><div class="article-body" id="article-body">{body}</div></article></main><footer><div class="container"><p>&copy; 2026 HPMPLab.</p><p><a href="../about.html">소개</a> · <a href="../privacy.html">개인정보처리방침</a> · <a href="../terms.html">이용약관</a> · <a href="../contact.html">문의</a></p></div></footer></body></html>'''

    def update_indexes(self, timestamp):
        p=self.p; date=self.date; e=html.escape; url=BASES[0]+f'/articles/market-{date}.html';image=BASES[0]+'/'+p['image']
        for page,kind in [('index.html','article-card home-article-card'),('articles/index.html','article-card'),('articles/market.html','market-article-item')]:
            prefix='' if page=='index.html' else '../';href=('articles/' if page=='index.html' else '')+f'market-{date}.html'
            priority='loading="eager" fetchpriority="high"' if page=='index.html' else 'loading="lazy"'
            img=f'<img class="article-card-image" src="{prefix+p["image"]}" width="1200" height="630" {priority} decoding="async" alt="{e(p["imageAlt"])}">'
            time_html=f'<time datetime="{timestamp}">{date.replace("-",".")} · {timestamp[11:16]} KST</time>'
            if page=='index.html':
                card=f'<article class="{kind}" data-category="market" data-published="{timestamp}"><a class="home-article-link" href="{href}"><span class="article-card-media">{img}</span><div class="home-article-copy"><span class="article-card-meta"><span class="article-category-badge">시황분석</span>{time_html}</span><h3 class="home-article-title">{e(p["title"])}</h3><p class="home-article-summary">{e(p["summary"])}</p></div></a></article>'
            elif page=='articles/market.html':
                card=f'<article class="{kind}"><a class="market-article-media" href="{href}" aria-label="{e(p["title"])}">{img}</a><div>{time_html}<h3><a href="{href}">{e(p["title"])}</a></h3><p>{e(p["summary"])}</p></div></article>'
            else:
                card=f'<article class="{kind}" data-category="market" data-published="{timestamp}"><a class="article-card-media" href="{href}" aria-label="{e(p["title"])}">{img}</a><span class="article-category-badge">시황분석</span>{time_html}<h3><a href="{href}">{e(p["title"])}</a></h3><p>{e(p["summary"])}</p></article>'
            text=insert_card(read(page),card,date,kind)
            if page=='index.html':
                def demote(match):
                    return match[0] if href in match[0] else match[0].replace('loading="eager"','loading="lazy"').replace(' fetchpriority="high"','')
                text=re.sub(r'<article class="article-card home-article-card"[^>]*>.*?</article>',demote,text,flags=re.S)
            if page!='articles/market.html':
                counts={k:len(re.findall(r'<article class="'+kind+r'" data-category="'+k+r'"',text)) for k in ['essay','market','health']}
                counts['all']=sum(counts.values())
                for category,count in counts.items():
                    text=re.sub(r'(data-category-count="'+category+r'">)\d+',lambda m:m[1]+str(count),text)
            if page=='articles/market.html':
                count=len(re.findall(r'<article class="market-article-item"',text))
                text=re.sub(r'(일일시황 <span class="article-category-count">)\d+',lambda m:m[1]+str(count),text)
                for ident in ['market-latest-article-link','market-summary-article-link']:
                    text=re.sub(r'(id="'+ident+r'" href=")[^"]+',lambda m:m[1]+href,text)
            if page=='index.html':
                text=re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")[^"]+',lambda m:m[1]+image,text)
            item={'@type':'ListItem','position':1,'url':url,'name':p['title'],'description':p['summary'],'datePublished':timestamp,'dateModified':timestamp,'image':{'@type':'ImageObject','url':image}}
            write(page,update_ld(text,item))
        sitemap=read('sitemap.xml')
        if url not in sitemap: sitemap=sitemap.replace('</urlset>',f'<url><loc>{url}</loc><lastmod>{date}</lastmod></url>\n</urlset>')
        for path in ['', 'articles/', 'articles/market.html']:
            sitemap=re.sub(r'(<loc>https://www\.hpmplab\.com/'+re.escape(path)+r'</loc>\s*<lastmod>)[^<]+',lambda m:m[1]+date,sitemap)
        write('sitemap.xml',sitemap)

    def commit(self, files, phase):
        allowed=set(files)
        staged=self.run(['git','-c','core.quotePath=false','diff','--cached','--name-only']).stdout.splitlines()
        if set(staged)-allowed: raise ValueError('다른 작업의 스테이징 변경 있음')
        self.run(['git','add','--']+files)
        self.run(['git','diff','--cached','--check'])
        bash=shutil.which('bash')
        if not bash: raise RuntimeError('Git Bash 없음')
        self.run([bash,'.githooks/pre-commit']); self.run([bash,'scripts/check_worklog_guard.sh'])
        if self.run(['git','diff','--cached','--quiet'],check=False).returncode != 0:
            self.run(['git','commit','-m',f'Publish market {self.date} {phase}'])
        sha=self.run(['git','rev-parse','HEAD']).stdout.strip()
        self.s[phase+'Commit']=sha;self.save()
        return sha

    def push(self, sha, phase):
        if self.run(['git','rev-parse','HEAD']).stdout.strip() != sha: raise ValueError('HEAD가 실행 체크포인트와 다름')
        self.run(['git','push','origin','main'])
        remote=self.run(['git','ls-remote','origin','refs/heads/main']).stdout.split()[0]
        if remote != sha: raise ValueError('원격 main 커밋 불일치')
        self.stage('push', phase=phase, commit=sha)

    def await_deploy(self, sha):
        deadline=time.monotonic()+600
        while time.monotonic()<deadline:
            jobs=json.loads(self.run(['aws','amplify','list-jobs','--app-id','d2pg7r2qjjb9u9','--branch-name','main','--region','us-east-1','--max-results','10','--output','json']).stdout)['jobSummaries']
            matches=[j for j in jobs if j.get('commitId')==sha]
            if matches:
                job=matches[0]
                if job['status']=='SUCCEED': return job
                if job['status'] in ['FAILED','CANCELLED']: raise RuntimeError('Amplify 최종 배포 실패: '+job['jobId'])
            print('Amplify waiting',sha[:8],flush=True);time.sleep(10)
        raise TimeoutError('Amplify 대기시간 초과; 체크포인트에서 재개 가능')

    def verify_live(self, sha):
        paths=[self.s['sealed']['article'],self.p['image'],self.s['sealed']['snapshot'],'assets/data/market-dashboard-latest.json','index.html','articles/index.html','articles/market.html']+self.p['charts']
        expected={p:subprocess.check_output(['git','show',sha+':'+p],cwd=ROOT) for p in paths}
        def check(pair):
            base,path=pair;url=base+'/'+path+'?verify='+sha+'-'+str(time.time_ns())
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'}),timeout=25) as response:
                raw=response.read()
                if response.status!=200 or raw!=expected[path]: raise ValueError('라이브 불일치: '+url)
                return {'url':url,'status':200,'sha256':digest(raw),'commitSha':sha,'checkedAt':now()}
        last=None
        for attempt in range(3):
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool: rows=list(pool.map(check,[(b,p) for b in BASES for p in paths]))
                dump(self.dir/'live-check.json',rows);return rows
            except Exception as error: last=error;time.sleep(5)
        raise last

    def publication(self, kind, sha):
        sealed=self.s['sealed'];f=load(sealed['forecastPath']);module=evaluation();parsed=module.validate_forecast(f,ROOT/sealed['forecastPath'],ROOT)
        path=Path('research/evaluation/publications')/(f['forecastId']+'-'+kind+'.json')
        if (ROOT/path).exists():
            event=load(path)
            if event['commitSha']!=sha: raise ValueError('발행 이벤트 중복/커밋 충돌')
            module.validate_publication_event(event,ROOT/path,parsed);return str(path).replace('\\','/')
        event={'schemaVersion':1,'forecastId':f['forecastId'],'contentHash':f['contentHash'],'commitSha':sha,'eventType':kind,'occurredAt':now()}
        if kind=='deploy_verified':event.update(publicUrl=BASES[0]+'/'+sealed['article'],availabilityStatus='available')
        module.validate_publication_event(event,ROOT/path,parsed);dump(path,event)
        return str(path).replace('\\','/')

    def publish(self, stop_after=None):
        if not self.s.get('contentCommit'):
            if not self.s.get('sealed'):
                self.preflight()
            else:
                # 봉인 전 통과한 누적 회귀를 무조건 반복하지 않는다. 실행기 수정은 관련 회귀로 확인한다.
                self.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_market_publication_pipeline.py'])
            if not self.s.get('sealed'):
                self.recover_draft();self.build(self.final_query())
            if (dt.datetime.now(TZ)-dt.datetime.fromisoformat(self.s['sealed']['cutoff'])).total_seconds()>300:
                raise ValueError('봉인 후 5분 초과. 미공개 판본/현재 시각 대조 후 새 판본 준비 필요')
            self.run(['node','scripts/preflight_deploy.js'])
            self.commit(self.s['files'],'content')
        sha=self.s['contentCommit']
        if not self.s.get('contentPushed'):
            self.push(sha,'content');self.s['contentPushed']=now();self.save()
        pushed=self.publication('pushed',sha)
        if stop_after=='content_push':
            print('checkpoint saved: immediately resume same command without --stop-after',flush=True);return 75
        if not self.s.get('contentDeploy'):
            job=self.await_deploy(sha);self.s['contentDeploy']=job;self.save()
        if not self.s.get('contentVerified'):
            self.verify_live(sha);self.s['contentVerified']=now();self.save()
        verified=self.publication('deploy_verified',sha)
        if not self.s.get('finalCommit'):
            at=self.s['contentDeploy']['endTime'];sealed=self.s['sealed'];text=read(sealed['article'])
            text=text.replace(' · 발행 준비', ' · 발행 '+at)
            text=re.sub(r'(<meta property="article:(?:published_time|modified_time)" content=")[^"]+',lambda m:m[1]+at,text)
            def ld(match):
                j=json.loads(match[1]);j.update(datePublished=at,dateModified=at)
                return '<script type="application/ld+json">'+json.dumps(j,ensure_ascii=False,indent=2)+'</script>'
            text=re.sub(r'<script type="application/ld\+json">(.*?)</script>',ld,text,flags=re.S)
            text=text.replace(' · 작성 '+sealed['issuedAt'][11:16]+' KST',' · 작성 '+sealed['issuedAt'][11:16]+' · 발행 '+at[11:16]+' KST')
            write(sealed['article'],text);self.update_indexes(at)
            state=read('STATE.md')+'- 최초 공개 '+at+' · 콘텐츠 '+sha+' · Amplify '+self.s['contentDeploy']['jobId']+'.\n';write('STATE.md',state)
            self.commit([sealed['article'],'index.html','articles/index.html','articles/market.html','sitemap.xml','STATE.md',pushed,verified,'docs/현재작업중.md'],'final')
        final=self.s['finalCommit']
        self.push(final,'final');job=self.await_deploy(final);rows=self.verify_live(final)
        self.s.update(finalDeploy=job,status='live_verified');self.stage('deploy',commit=final,job=job['jobId']);self.stage('live',assets=len(rows),commit=final)
        status=load(self.status_path);status.update(status='awaiting_browser',contentCommit=sha,finalCommit=final,deploymentJob=job['jobId'],verification=f'{len(rows)} cache-busted assets match final Git commit');dump(self.status_path,status)
        print(json.dumps({'status':'live_verified','article':BASES[0]+'/'+self.s['sealed']['article'],'finalCommit':final,'job':job['jobId'],'cutoff':self.s['sealed']['cutoff'],'browser':'required'},ensure_ascii=False),flush=True)
        return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',required=True)
    parser.add_argument('--stop-after',choices=['content_push'],help='실제 재개 검증용 체크포인트: exit75 뒤 동일 package 재실행')
    args=parser.parse_args()
    publisher=Publisher(args.package)
    try: return publisher.publish(args.stop_after)
    except Exception as error:
        publisher.s['lastError']={'at':now(),'error':str(error)};publisher.save();raise


if __name__=='__main__': raise SystemExit(main())
