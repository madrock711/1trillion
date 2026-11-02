from pathlib import Path
p=Path('STATE.md');s=p.read_text(encoding='utf-8');p.write_text(s.replace('미국 11월 고용보고서','미국 10월 고용보고서'),encoding='utf-8')
p=Path('reports/2026-11-02.md');s=p.read_text(encoding='utf-8');s=s.replace(' AND 외국인>=-8000억원','');s+='\n미국 FRED 10월 30일 10년-2년 금리차 +0.38%p, 10년-3개월 +0.78%p. 개별 금리와 날짜를 혼합하지 않음.\n';p.write_text(s,encoding='utf-8')
p=Path('research/evidence/2026-11-02/prepared-dashboard.json');s=p.read_text(encoding='utf-8');s=s.replace('      "외국인 순매도 8천억원 이하"\n','      "수급 변화 확인"\n');p.write_text(s,encoding='utf-8')
