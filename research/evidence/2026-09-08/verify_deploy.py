"""동일 커밋의 양 도메인 cache-busted 배포 바이트 및 발행 이벤트 보존."""
import concurrent.futures,datetime,hashlib,json,pathlib,subprocess,urllib.request
root=pathlib.Path(__file__).resolve().parents[3];e=pathlib.Path(__file__).parent
seal=json.loads((e/'seal.json').read_text(encoding='utf-8'));fid=seal['forecastId']
forecast=json.loads((root/'research/evaluation/forecasts'/f'{fid}.json').read_text(encoding='utf-8'))
commit='922ee3575b6dfe22c3cc32bea56cd930111ad06a'
def check(pair):
 domain,path=pair;url=domain+'/'+path+'?v='+commit[:12]
 raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'}),timeout=25).read()
 expected=subprocess.check_output(['git','show',commit+':'+path],cwd=root)
 return {'url':url,'status':200,'matchesCommit':raw==expected,'sha256':hashlib.sha256(raw).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
 checks=list(pool.map(check,[(d,p) for d in ['https://www.hpmplab.com','https://main.d2pg7r2qjjb9u9.amplifyapp.com'] for p in seal['files']]))
assert all(c['matchesCommit'] for c in checks),[c for c in checks if not c['matchesCommit']]
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
dump(e/'deployment-verification.json',{'commitSha':commit,'jobId':'573','verifiedAt':now,'checks':checks})
common={'schemaVersion':1,'forecastId':fid,'contentHash':forecast['contentHash'],'commitSha':commit}
dump(root/'research/evaluation/publications'/f'{fid}-pushed.json',dict(common,eventType='pushed',occurredAt='2026-09-08T08:15:23+09:00'))
dump(root/'research/evaluation/publications'/f'{fid}-deploy_verified.json',dict(common,eventType='deploy_verified',occurredAt=now,publicUrl='https://www.hpmplab.com/articles/market-2026-09-08.html',availabilityStatus='available'))
print(now,'verified',len(checks),'files against',commit)
