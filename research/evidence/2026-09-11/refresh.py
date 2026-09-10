"""최종 시세만 병렬 갱신하고 최초 관측은 별도 보존한다."""
import concurrent.futures, pathlib, shutil
import collect
names=['NXT','FX','yahoo-NQF','yahoo-ESF','yahoo-BZF','yahoo-CLF']
for name in names:
    p=pathlib.Path(__file__).parent/(name+'.json')
    first=p.with_name(name+'-initial.json')
    if not first.exists():shutil.copyfile(p,first)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results=list(pool.map(collect.fetch,[(name,collect.URLS[name]) for name in names]))
print(results)
assert all(status=='OK' for _,status in results)
