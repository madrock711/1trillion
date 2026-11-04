"""계정 변경/배포 없이 발행 의존성을 현재 환경에서 점검한다."""
import argparse
import concurrent.futures
import datetime
import importlib.util
import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--label', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[3]
commands = {
    'git-remote': ['git', 'ls-remote', 'origin', 'refs/heads/main'],
    'node': ['node', '--version'],
    'bash': [shutil.which('bash') or 'bash', '--version'],
    'aws-auth': ['aws', 'sts', 'get-caller-identity', '--output', 'json'],
    'amplify': ['aws', 'amplify', 'list-jobs', '--app-id', 'd2pg7r2qjjb9u9', '--branch-name', 'main', '--region', 'us-east-1', '--max-results', '5', '--output', 'json'],
}
urls = {
    'naver': 'https://m.stock.naver.com/api/index/KOSPI/basic',
    'yahoo': 'https://query1.finance.yahoo.com/v8/finance/chart/QQQ?range=5d&interval=1d',
    'fred': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10Y2Y',
    'treasury': 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2026',
    'memory': 'https://www.trendforce.com/price/dram/dram_spot',
    'live-custom': 'https://www.hpmplab.com/articles/market.html',
    'live-amplify': 'https://main.d2pg7r2qjjb9u9.amplifyapp.com/articles/market.html',
}

def probe(item):
    key, value = item
    start = time.monotonic()
    try:
        if isinstance(value, list):
            r = subprocess.run(value, cwd=root, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
            out = r.stdout.strip()
            if key == 'aws-auth' and r.returncode == 0:
                out = json.dumps({'Account': json.loads(out).get('Account')})
            if key == 'amplify' and r.returncode == 0:
                out = json.dumps([{k: job.get(k) for k in ['jobId','commitId','status','endTime']} for job in json.loads(out).get('jobSummaries',[])])
            result = {'exitCode': r.returncode, 'output': out[:3500], 'error': r.stderr.strip()[:1200]}
        else:
            with urllib.request.urlopen(urllib.request.Request(value,headers={'User-Agent':'Mozilla/5.0'}), timeout=15) as r:
                raw = r.read()
                result = {'status': r.status, 'bytes': len(raw), 'url': value}
                if key == 'naver':
                    data=json.loads(raw)
                    result.update({k:data.get(k) for k in ['marketStatus','localTradedAt']})
        return key, dict(result, elapsed=round(time.monotonic()-start,2))
    except Exception as error:
        return key, {'error': str(error)[:1200], 'elapsed': round(time.monotonic()-start,2)}

with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    checks = dict(pool.map(probe, list(commands.items()) + list(urls.items())))
checks['python-modules'] = {m: importlib.util.find_spec(m) is not None for m in ['matplotlib','numpy','PIL','requests']}
out={'checkedAt': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(), 'label':args.label, 'checks':checks}
Path(__file__).with_name('environment-'+args.label+'.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
