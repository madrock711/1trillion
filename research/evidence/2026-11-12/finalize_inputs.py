import json,datetime
from pathlib import Path
P=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
text='FREDの最新公表値'.replace('FREDの最新公表値','FRED 최신 공개 관측에서 10년-2년 금리차는 11월 10일 0.25%포인트, 10년-3개월은 0.68%포인트입니다. 개별 만기는 11월 9일 기준 3개월 4.24%, 2년 4.56%, 10년 4.88%입니다. 관측일이 달라 같은 날의 곡선으로 합칠 수는 없습니다. 장기금리의 높은 절대 수준은 반도체 가치평가의 부담으로 남습니다.')
for file in ['article-body.html','report-template.md']:
 p=P/file;s=p.read_text(encoding='utf-8').replace('us_yield_spreads_long_term_2026-11-12','us_yield_spreads_long_term_2026-11-11').replace('us_yield_spreads_90d_2026-11-12','us_yield_spreads_90d_2026-11-11')
 s+= ('\n<h2>미 국채와 금리차</h2><p>'+text+' <a href="https://fred.stlouisfed.org/series/DGS10">FRED</a></p>\n') if file.endswith('html') else '\n## 미 국채와 금리차\n'+text+' [FRED](https://fred.stlouisfed.org/series/DGS10)\n'
 p.write_text(s,encoding='utf-8',newline='\n')
p=P/'package.json';v=load(p);v['charts']=[x.replace('2026-11-12','2026-11-11') for x in v['charts']];v['files']=[x for x in v['files'] if not x.startswith('charts/')];v['files']+=[str(x).replace('\\','/') for x in [P/'finalize_inputs.py']];dump(p,v)
note=Path('research/notes/2026-11-12.md');note.write_text(note.read_text(encoding='utf-8')+'\nFRED CSV 2回・期間限定CSV・公式TXT代替はread timeout。公式seriesページ5種を08:04 KSTに再閲覧し最新観測が前日図と同じ11/10(差)・11/9(個別)と確認。日付を偽らず11/11生成済み図を参照、新規生成成功とはしない。\n'.replace('代替','대체').replace('公式','공식').replace('前日図','전일 차트'),encoding='utf-8',newline='\n')
log=Path('docs/현재작업중.md');log.write_text(log.read_text(encoding='utf-8')+'\n- FRED 다운로드 시간초과 재시도 후 공식 웹 5개 시리즈 최신 관측 대조. 관측 갱신이 없어 기존 11/11 생성 차트를 원래 날짜로 참조한다. 새 차트 생성 성공으로 간주하지 않는다. finalize_inputs.py에 최종 입력 정리 기록.\n',encoding='utf-8',newline='\n')
dump(P/'fred-web-check.json',{'checkedAt':datetime.datetime.now().astimezone().isoformat(),'source':'FRED official series pages via web tool','latest':{'T10Y2Y':['2026-11-10',.25],'T10Y3M':['2026-11-10',.68],'DGS10':['2026-11-09',4.88],'DGS2':['2026-11-09',4.56],'DGS3MO':['2026-11-09',4.24]},'chartStatus':'prior chart retained with original filename and observation date after latest values reverified'})
v=load(p);v['files'].append(str(P/'fred-web-check.json').replace('\\','/'));dump(p,v)
