from pathlib import Path
p=Path('research/evidence/2026-11-04/seal_today.py');s=p.read_text(encoding='utf-8').replace(";kb=dict(kb,fluctuationsRatio=kp['fluctuationsRatio'])",'').replace('2026\\.11\\.03','2026\\.11\\.04');p.write_text(s,encoding='utf-8')
# Preserve prior session actuals and explicitly mark unavailable path evidence.
s=Path('research/evidence/2026-11-03/actuals_today.py').read_text(encoding='utf-8').replace('2026-11-03','2026-11-04').replace('2026-11-02','2026-11-03').replace("d['data'][0]","next(z for z in d['data'] if z['localTradedAt']=='2026-11-03')").replace('2026-11-03-0917-same-close','2026-11-03-0803-same-close').replace("'realizedScenario':'bull'","'realizedScenario':'bear'")
s=s[:s.index("s=json.loads((p/'run-status.json')")]
s += "\no.update(postForecastPathStatus='missing',postForecastPathMissingReason=reason,postForecastPathMissingEvidence={'sourceStatus':'incomplete','source':ev('KOSPI')['url'],'asOf':'2026-11-03T15:30:00+09:00','fetchedAt':now,'rawHash':ev('KOSPI')['rawHash']})\n(r/f'research/evaluation/outcomes/{fid}.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\\n',encoding='utf-8')\n"
Path('research/evidence/2026-11-04/actuals_today.py').write_text(s,encoding='utf-8')
