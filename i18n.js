(function(){
  var MESSAGES = {
    en: {
      'page.title': 'Timer App',
      'meta.description': 'Breathing and CO2 table timers with guided training and detailed records.',
      'og.title': 'Timer App',
      'og.description': 'Breathing and CO2 table timers with guided training and detailed records.',
      'twitter.title': 'Timer App',
      'twitter.description': 'Breathing and CO2 table timers with guided training and detailed records.',
      'header.title': 'Grind',
      'nav.blog': 'App Guide',
      'nav.subscribe': 'Subscribe',
      'tabs.breathing': 'Breathing Timer',
      'tabs.co2': 'CO2 Table Timer',
      'site.intro': 'Focused timers for breath training and CO2 table practice, with clear guidance and exportable records.',
      'breath.embed': 'Breath Timer Section',
      'breath.wrapper': 'Inhale–Exhale Breath Trainer',
      'breath.title': '🫁 Breath Trainer — Inhale (red) / Exhale (blue)',
      'breath.inhale': 'Inhale',
      'breath.exhale': 'Exhale',
      'breath.start': 'Start',
      'breath.pause': 'Pause',
      'breath.skip': 'Skip',
      'breath.skipTitle': 'Skip to the next phase',
      'breath.reset': 'Reset',
      'breath.note': 'Default is 1:1 sync. Use <b>=</b> (sync) / <b>≠</b> (separate) to switch.',
      'breath.syncTitle': 'Sync inhale & exhale',
      'breath.volume': 'Volume',
      'breath.roundLabel': 'Round',
      'breath.stepLabel': 'Step',
      'breath.totalLabel': 'Total Time',
      'breath.nudgeInhale': 'Inhale adjust buttons',
      'breath.nudgeExhale': 'Exhale adjust buttons',
      'breath.inhaleDec': 'Decrease inhale',
      'breath.inhaleInc': 'Increase inhale',
      'breath.exhaleDec': 'Decrease exhale',
      'breath.exhaleInc': 'Increase exhale',
      'unit.seconds': '(s)',
      'unit.secondsShort': 's',
      'sw.embed': 'Stopwatch Section',
      'sw.wrapper': 'Stopwatch',
      'sw.title': '⏱ Stopwatch (Start / Lap / Stop / Reset — Alternates recording Lap and Rest)',
      'sw.start': 'Start',
      'sw.stop': 'Stop',
      'sw.lap': 'Lap',
      'sw.reset': 'Reset',
      'sw.records': 'Records',
      'sw.lapSec': 'Lap (s)',
      'sw.restSec': 'Rest (s)',
      'sw.note': 'While timing, the next cell to be recorded is highlighted. (Lap=red, Rest=blue)',
      'sw.chartTitle': 'Lap/Rest Chart (s)',
      'sw.legendLap': 'Lap',
      'sw.legendRest': 'Rest',
      'sw.chartAria': 'Lap/Rest chart',
      'sw.exportCsv': 'Export CSV',
      'sw.exportJson': 'Export JSON',
      'sw.exportPng': 'Export Chart PNG',
      'sw.copy': 'Copy as Text',
      'sw.copied': 'Copied!',
      'sw.copyFail': 'Copy failed: ',
      'sw.chartEmpty': 'Lap → Lap and Rest are recorded alternately. Use Start(Stop) to end and record the current segment.',
      'sw.chartNoRecords': 'No records yet. Press Lap to start recording.',
      'blog.title': 'App Guide',
      'blog.post1.title': 'Master Your Breath: A Guide to Breathing Training',
      'blog.post1.p1': 'Proper breathing is the foundation of performance, focus, and stress management. Our Breathing Timer is designed to help you cultivate a powerful and efficient breathing practice. By guiding you through controlled inhale and exhale cycles, you can improve your respiratory muscle strength, increase your lung capacity, and learn to control your physiological response to stress.',
      'blog.post1.p2': 'Regular practice with the Breathing Timer can lead to a lower resting heart rate, improved cardiovascular health, and a heightened sense of calm and focus. Whether you are an athlete looking to optimize your performance or simply seeking a way to manage daily stress, our Breathing Timer is an essential tool for your wellness journey.',
      'blog.post2.title': 'CO2 Table Training, Explained Simply',
      'blog.post2.p1': 'CO2 table training builds tolerance to the urge to breathe. You keep the breath-hold time the same, while rest time gets shorter each round. This trains both body and mind to stay calm under rising CO2.',
      'blog.post2.p2': 'The timer handles the rhythm for you so you can focus on form and safety. It guides each round with clear transitions and consistent timing.',
      'blog.post2.p3': 'How to use it: press Start to begin. Press Lap to record the current segment and switch between breath-hold and rest. Press Stop to end and save. Press Reset to clear. Records are stored as Lap → Rest pairs.',
      'blog.post2.p4': 'The chart makes progress easy to see (Lap=red, Rest=blue). Export CSV or JSON for analysis, or save a PNG chart for your log. Train 2–3 times per week, start on dry land, and never train alone.',
      'blog.post2.chartTitle': 'Typical CO2 Table Shape (Sample)',
      'blog.post2.chartCaption': 'Flat red line = fixed breath-hold. Blue line steps down = shorter rest each round.',
      'blog.post2.readMoreTitle': 'Read more',
      'blog.post2.readMoreHtml': '<h4>프리다이빙 CO₂ 테이블 완벽 가이드: 초보자도 쉽게 따라하는 숨참기 훈련법</h4>\n<p>⏱ <strong>훈련용 스톱워치</strong> (Start / Lap / Stop / Reset)</p>\n<ul>\n<li>Lap과 Rest를 번갈아 측정하세요</li>\n<li>측정 중인 구간은 색상으로 표시됩니다 (숨참기=빨강, 휴식=파랑)</li>\n</ul>\n<hr>\n<h5>프리다이빙, 왜 숨참기 훈련이 필요할까요?</h5>\n<p>프리다이빙은 산소통 없이 한 번의 호흡만으로 물속에 들어가는 특별한 수중 스포츠입니다. 물속에서 가장 힘든 순간은 숨이 막히는 느낌이 들 때인데요, 이때 우리 몸에는 이산화탄소(CO₂)가 쌓이고 있습니다.</p>\n<p><strong>CO₂ 테이블 훈련</strong>은 이런 불편한 느낌에 천천히 익숙해지는 연습 방법입니다. 마치 매운 음식을 조금씩 먹으면서 매운맛에 적응하는 것처럼, 우리 몸도 CO₂에 점점 익숙해질 수 있답니다.</p>\n<hr>\n<h5>안전이 최우선! 반드시 지켜야 할 규칙</h5>\n<p>프리다이빙 훈련은 효과적이지만, 잘못하면 위험할 수 있어요. 다음 규칙을 꼭 기억하세요.</p>\n<h6>필수 안전 수칙 4가지</h6>\n<ol>\n<li><strong>절대 혼자 하지 마세요</strong><br>옆에서 지켜봐 줄 사람이 꼭 필요합니다. 친구나 가족에게 부탁하세요.</li>\n<li><strong>과호흡은 금물</strong><br>숨을 빨리 많이 쉬는 것은 오히려 위험합니다. 기절할 수도 있어요.</li>\n<li><strong>육지에서부터 시작하세요</strong><br>소파나 바닥에서 먼저 충분히 연습한 후, 나중에 물속으로 가세요.</li>\n<li><strong>몸이 이상하면 바로 멈추세요</strong><br>머리가 아프거나 어지러우면 그날 훈련은 여기까지입니다.</li>\n</ol>\n<hr>\n<h5>CO₂ 테이블과 O₂ 테이블, 무엇이 다를까?</h5>\n<p>프리다이빙에는 두 가지 대표적인 훈련 방법이 있습니다.</p>\n<table>\n<thead>\n<tr><th>구분</th><th>CO₂ 테이블</th><th>O₂ 테이블</th></tr>\n</thead>\n<tbody>\n<tr><td><strong>특징</strong></td><td>숨참기 시간은 같게, 휴식은 점점 짧게</td><td>휴식은 같게, 숨참기는 점점 길게</td></tr>\n<tr><td><strong>효과</strong></td><td>CO₂ 쌓이는 느낌에 익숙해짐</td><td>산소 부족 상황에 적응</td></tr>\n<tr><td><strong>추천 대상</strong></td><td>초보자, 중급자</td><td>중급자, 상급자</td></tr>\n</tbody>\n</table>\n<p><strong>CO₂ 테이블</strong>은 특히 \"숨이 막히는 느낌\"과 \"빨리 숨 쉬고 싶은 충동\"을 조절하는 데 탁월합니다.</p>\n<hr>\n<h5>스톱워치 사용 설명서</h5>\n<p>위에 있는 스톱워치로 훈련을 기록할 수 있어요.</p>\n<h6>버튼 기능</h6>\n<ul>\n<li><strong>Start</strong>: 타이머 시작</li>\n<li><strong>Lap</strong>: 구간 기록 (숨참기 ↔ 휴식 자동 전환)</li>\n<li><strong>Stop</strong>: 훈련 종료 및 저장</li>\n<li><strong>Reset</strong>: 모든 기록 지우기</li>\n</ul>\n<h6>기록 방식</h6>\n<ul>\n<li>한 줄에 \"숨참기 시간 + 휴식 시간\"이 함께 저장됩니다</li>\n<li>그래프로 보면 빨간색(숨참기), 파란색(휴식)으로 표시돼요</li>\n<li>CSV, JSON, PNG 파일로 내보내기 가능</li>\n</ul>\n<hr>\n<h5>실전 훈련 방법: 단계별 프로토콜</h5>\n<p>초보자를 위한 기본 CO₂ 테이블 예시입니다. 본인 실력에 맞춰 시간을 조절하세요.</p>\n<table>\n<thead>\n<tr><th>세트</th><th>숨참기 시간</th><th>휴식 시간</th><th>특징</th></tr>\n</thead>\n<tbody>\n<tr><td>1회</td><td>2분</td><td>1분 45초</td><td>편안하게 시작</td></tr>\n<tr><td>2회</td><td>2분</td><td>1분 30초</td><td>휴식이 조금 줄어듦</td></tr>\n<tr><td>3회</td><td>2분</td><td>1분 15초</td><td>점점 힘들어짐</td></tr>\n<tr><td>4회</td><td>2분</td><td>1분</td><td>본격적인 도전</td></tr>\n<tr><td>5회</td><td>2분</td><td>45초</td><td>거의 끝!</td></tr>\n<tr><td>6회</td><td>2분</td><td>30초</td><td>마지막 세트</td></tr>\n</tbody>\n</table>\n<h6>핵심 포인트</h6>\n<ul>\n<li>숨참기 시간(2분)은 모든 세트에서 똑같이 유지</li>\n<li>휴식 시간만 점점 짧아집니다</li>\n<li>이렇게 하면 CO₂가 쌓이는 느낌에 점차 익숙해져요</li>\n</ul>\n<hr>\n<h5>훈련 기록, 이렇게 활용하세요</h5>\n<h6>Lap 버튼 활용법</h6>\n<ol>\n<li>숨참기 시작 → Start 버튼</li>\n<li>숨참기 끝 → Lap 버튼 (자동으로 휴식 측정 시작)</li>\n<li>휴식 끝 → Lap 버튼 (다음 세트 숨참기 측정 시작)</li>\n<li>전체 종료 → Stop 버튼</li>\n</ol>\n<h6>그래프 해석 팁</h6>\n<ul>\n<li>빨간 막대(숨참기)가 일정한지 확인하세요</li>\n<li>파란 막대(휴식)가 점점 낮아지는지 체크하세요</li>\n<li>패턴이 불규칙하다면 훈련 강도를 조절할 필요가 있어요</li>\n</ul>\n<h6>데이터 저장하기</h6>\n<ul>\n<li><strong>CSV/JSON</strong>: 엑셀이나 구글 시트에서 분석</li>\n<li><strong>PNG</strong>: 그래프 이미지로 보관, SNS 공유 가능</li>\n</ul>\n<hr>\n<h5>훈련 스케줄 추천</h5>\n<h6>이상적인 빈도</h6>\n<ul>\n<li><strong>주 2~3회</strong>: 매일 하면 오히려 피곤해요</li>\n<li><strong>격일 훈련</strong>: 월·수·금 또는 화·목·토</li>\n<li><strong>휴식일 준수</strong>: 몸이 회복할 시간이 필요합니다</li>\n</ul>\n<h6>점진적 발전 전략</h6>\n<ol>\n<li><strong>첫 달</strong>: 기본 프로토콜 완성 (위 표 참고)</li>\n<li><strong>둘째 달</strong>: 휴식 시간 15초씩 추가로 단축</li>\n<li><strong>셋째 달</strong>: 숨참기 시간 15초씩 증가</li>\n</ol>\n<hr>\n<h5>초보자가 흔히 하는 실수들</h5>\n<table>\n<thead>\n<tr><th>실수</th><th>왜 위험한가요?</th><th>올바른 방법</th></tr>\n</thead>\n<tbody>\n<tr><td>과호흡으로 시작</td><td>기절 위험</td><td>편안한 호흡 유지</td></tr>\n<tr><td>혼자 훈련</td><td>사고 시 대처 불가</td><td>반드시 감시자 동반</td></tr>\n<tr><td>휴식 무리하게 단축</td><td>멘탈·체력 소진</td><td>점진적 감소 원칙</td></tr>\n<tr><td>바로 수중 훈련</td><td>익수 사고 위험</td><td>육지 숙련 후 진행</td></tr>\n</tbody>\n</table>\n<hr>\n<h5>자주 묻는 질문 TOP 3</h5>\n<p><strong>Q1. CO₂ 테이블만 해도 기록이 늘어나나요?</strong><br>어느 정도 효과가 있지만, 킥 기술, 이퀄라이징(귀 압력 조절), 멘탈 트레이닝을 함께 해야 진짜 실력이 늘어요.</p>\n<p><strong>Q2. 집에서도 가능한가요?</strong><br>네! 소파나 침대에서 안전하게 연습할 수 있어요. 이걸 \'건식 훈련\'이라고 부릅니다.</p>\n<p><strong>Q3. 수중에서 해도 되나요?</strong><br>반드시 버디(짝)와 안전 장비를 갖춘 상태에서만 가능합니다. 절대 혼자 하지 마세요.</p>\n<hr>\n<h5>정리하며</h5>\n<p>이 가이드는 CO₂ 테이블의 원리부터 실전 적용, 안전 수칙, 기록 분석까지 모든 것을 담았습니다.</p>\n<h6>시작하기 전 체크리스트</h6>\n<ul class=\"checklist\">\n<li>안전 감시자 확보</li>\n<li>건강 상태 양호</li>\n<li>스톱워치 준비</li>\n<li>편안한 환경 조성</li>\n<li>안전 수칙 숙지</li>\n</ul>\n<p>이제 위에 제공된 스톱워치를 활용해 직접 훈련을 시작해 보세요. 매주 기록을 확인하면서 본인의 발전을 느껴보는 것, 정말 뿌듯할 거예요!</p>\n<p><strong>안전한 프리다이빙, 즐거운 훈련 되세요!</strong></p>',
      'blog.backToTimers': 'Back to Timers',
      'subscribe.title': 'Contact',
      'subscribe.body': 'Have feedback or a feature request? Send a quick message.',
      'subscribe.note': 'We will reply within 1–2 business days.',
      'subscribe.cta': 'Send',
      'subscribe.emailLabel': 'Email',
      'subscribe.messageLabel': 'Message',
      'subscribe.emailPlaceholder': 'you@example.com',
      'subscribe.messagePlaceholder': 'Tell us what you need.',
      'footer.rights': '© 2026 Timer.app. All rights reserved.'
    },
    ko: {
      'page.title': '타이머 앱',
      'meta.description': '호흡 및 CO2 테이블 훈련을 위한 타이머와 상세 기록을 제공합니다.',
      'og.title': '타이머 앱',
      'og.description': '호흡 및 CO2 테이블 훈련을 위한 타이머와 상세 기록을 제공합니다.',
      'twitter.title': '타이머 앱',
      'twitter.description': '호흡 및 CO2 테이블 훈련을 위한 타이머와 상세 기록을 제공합니다.',
      'header.title': '연마',
      'nav.blog': '앱 가이드',
      'nav.subscribe': '구독',
      'tabs.breathing': '호흡 타이머',
      'tabs.co2': 'CO2 테이블 타이머',
      'site.intro': '호흡 훈련과 CO2 테이블 연습을 위한 집중 타이머로, 명확한 가이드와 내보내기 가능한 기록을 제공합니다.',
      'breath.embed': '호흡 타이머 영역',
      'breath.wrapper': '들숨-날숨 호흡 트레이너',
      'breath.title': '🫁 호흡 트레이너 — 들숨(빨강) / 날숨(파랑)',
      'breath.inhale': '들숨',
      'breath.exhale': '날숨',
      'breath.start': '시작',
      'breath.pause': '일시정지',
      'breath.skip': '다음',
      'breath.skipTitle': '다음 단계로 즉시 전환',
      'breath.reset': '초기화',
      'breath.note': '기본은 1:1 동기화. <b>=</b> (동기화) / <b>≠</b> (개별설정) 버튼으로 전환하세요.',
      'breath.syncTitle': '들숨/날숨 동기화',
      'breath.volume': '소리 크기',
      'breath.roundLabel': '라운드',
      'breath.stepLabel': '단계',
      'breath.totalLabel': '총 시간',
      'breath.nudgeInhale': '들숨 조절 버튼',
      'breath.nudgeExhale': '날숨 조절 버튼',
      'breath.inhaleDec': '들숨 감소',
      'breath.inhaleInc': '들숨 증가',
      'breath.exhaleDec': '날숨 감소',
      'breath.exhaleInc': '날숨 증가',
      'unit.seconds': '(초)',
      'unit.secondsShort': '초',
      'sw.embed': '스톱워치 영역',
      'sw.wrapper': '스톱워치',
      'sw.title': '⏱ 스톱워치 (시작 / 랩 / 정지 / 초기화 — 랩과 휴식을 교대로 기록)',
      'sw.start': '시작',
      'sw.stop': '정지',
      'sw.lap': '랩',
      'sw.reset': '초기화',
      'sw.records': '기록',
      'sw.lapSec': '랩 (초)',
      'sw.restSec': '휴식 (초)',
      'sw.note': '측정 중에는 다음에 기록될 칸이 색으로 표시됩니다. (Lap=빨강, Rest=파랑)',
      'sw.chartTitle': '랩/휴식 차트 (초)',
      'sw.legendLap': '랩',
      'sw.legendRest': '휴식',
      'sw.chartAria': '랩/휴식 차트',
      'sw.exportCsv': 'CSV 내보내기',
      'sw.exportJson': 'JSON 내보내기',
      'sw.exportPng': '차트 PNG 내보내기',
      'sw.copy': '텍스트로 복사',
      'sw.copied': '복사됨!',
      'sw.copyFail': '복사 실패: ',
      'sw.chartEmpty': '랩 → 랩/휴식이 번갈아 기록됩니다. 시작(정지)으로 현재 구간을 종료/기록합니다.',
      'sw.chartNoRecords': '아직 기록이 없습니다. 랩을 눌러 기록을 시작하세요.',
      'blog.title': '앱 가이드',
      'blog.post1.title': '호흡 마스터하기: 호흡 훈련 가이드',
      'blog.post1.p1': '올바른 호흡은 퍼포먼스, 집중, 스트레스 관리의 기본입니다. 호흡 타이머는 효율적이고 강력한 호흡 습관을 만들 수 있도록 설계되었습니다. 들숨과 날숨을 일정하게 안내해 호흡근을 강화하고 폐활량을 높이며, 스트레스에 대한 생리적 반응을 더 잘 통제하도록 돕습니다.',
      'blog.post1.p2': '호흡 타이머를 꾸준히 사용하면 안정 시 심박수가 낮아지고 심혈관 건강이 개선되며, 더 큰 평온함과 집중을 얻을 수 있습니다. 퍼포먼스를 최적화하려는 운동선수든, 일상 스트레스를 관리하고 싶은 누구든 호흡 타이머는 건강 여정을 위한 핵심 도구입니다.',
      'blog.post2.title': 'CO2 테이블 훈련, 쉽게 이해하기',
      'blog.post2.p1': 'CO2 테이블은 숨참기 시간은 그대로 두고, 휴식 시간을 라운드마다 조금씩 줄이는 훈련입니다. 몸은 CO2에 익숙해지고, 마음은 더 차분해집니다.',
      'blog.post2.p2': '타이머가 흐름을 정확히 안내해주니, 사용자는 자세와 안전에 집중하면 됩니다. 일정한 리듬을 유지하는 데 최적화되어 있습니다.',
      'blog.post2.p3': '사용법: `Start`로 시작합니다. `Lap`을 누르면 지금 구간이 기록되고 아프네아↔휴식이 교대됩니다. `Stop`은 세션 종료 및 저장, `Reset`은 초기화입니다. 기록은 Lap → Rest 순서로 저장됩니다.',
      'blog.post2.p4': '차트는 Lap=빨강, Rest=파랑으로 보여줘 진행을 쉽게 확인할 수 있습니다. CSV/JSON/PNG로 내보내 분석하거나 기록 보관에 쓰세요. 주 2~3회, 건식부터 시작하고 절대 혼자 하지 마세요.',
      'blog.post2.chartTitle': 'CO2 테이블 기본 그래프(예시)',
      'blog.post2.chartCaption': '빨간선은 숨참기 고정, 파란선은 휴식이 계단처럼 줄어드는 모습입니다.',
      'blog.post2.readMoreTitle': '더 읽기',
      'blog.post2.readMoreHtml': '<h4>프리다이빙 CO₂ 테이블 완벽 가이드: 초보자도 쉽게 따라하는 숨참기 훈련법</h4>\n<p>⏱ <strong>훈련용 스톱워치</strong> (Start / Lap / Stop / Reset)</p>\n<ul>\n<li>Lap과 Rest를 번갈아 측정하세요</li>\n<li>측정 중인 구간은 색상으로 표시됩니다 (숨참기=빨강, 휴식=파랑)</li>\n</ul>\n<hr>\n<h5>프리다이빙, 왜 숨참기 훈련이 필요할까요?</h5>\n<p>프리다이빙은 산소통 없이 한 번의 호흡만으로 물속에 들어가는 특별한 수중 스포츠입니다. 물속에서 가장 힘든 순간은 숨이 막히는 느낌이 들 때인데요, 이때 우리 몸에는 이산화탄소(CO₂)가 쌓이고 있습니다.</p>\n<p><strong>CO₂ 테이블 훈련</strong>은 이런 불편한 느낌에 천천히 익숙해지는 연습 방법입니다. 마치 매운 음식을 조금씩 먹으면서 매운맛에 적응하는 것처럼, 우리 몸도 CO₂에 점점 익숙해질 수 있답니다.</p>\n<hr>\n<h5>안전이 최우선! 반드시 지켜야 할 규칙</h5>\n<p>프리다이빙 훈련은 효과적이지만, 잘못하면 위험할 수 있어요. 다음 규칙을 꼭 기억하세요.</p>\n<h6>필수 안전 수칙 4가지</h6>\n<ol>\n<li><strong>절대 혼자 하지 마세요</strong><br>옆에서 지켜봐 줄 사람이 꼭 필요합니다. 친구나 가족에게 부탁하세요.</li>\n<li><strong>과호흡은 금물</strong><br>숨을 빨리 많이 쉬는 것은 오히려 위험합니다. 기절할 수도 있어요.</li>\n<li><strong>육지에서부터 시작하세요</strong><br>소파나 바닥에서 먼저 충분히 연습한 후, 나중에 물속으로 가세요.</li>\n<li><strong>몸이 이상하면 바로 멈추세요</strong><br>머리가 아프거나 어지러우면 그날 훈련은 여기까지입니다.</li>\n</ol>\n<hr>\n<h5>CO₂ 테이블과 O₂ 테이블, 무엇이 다를까?</h5>\n<p>프리다이빙에는 두 가지 대표적인 훈련 방법이 있습니다.</p>\n<table>\n<thead>\n<tr><th>구분</th><th>CO₂ 테이블</th><th>O₂ 테이블</th></tr>\n</thead>\n<tbody>\n<tr><td><strong>특징</strong></td><td>숨참기 시간은 같게, 휴식은 점점 짧게</td><td>휴식은 같게, 숨참기는 점점 길게</td></tr>\n<tr><td><strong>효과</strong></td><td>CO₂ 쌓이는 느낌에 익숙해짐</td><td>산소 부족 상황에 적응</td></tr>\n<tr><td><strong>추천 대상</strong></td><td>초보자, 중급자</td><td>중급자, 상급자</td></tr>\n</tbody>\n</table>\n<p><strong>CO₂ 테이블</strong>은 특히 \"숨이 막히는 느낌\"과 \"빨리 숨 쉬고 싶은 충동\"을 조절하는 데 탁월합니다.</p>\n<hr>\n<h5>스톱워치 사용 설명서</h5>\n<p>위에 있는 스톱워치로 훈련을 기록할 수 있어요.</p>\n<h6>버튼 기능</h6>\n<ul>\n<li><strong>Start</strong>: 타이머 시작</li>\n<li><strong>Lap</strong>: 구간 기록 (숨참기 ↔ 휴식 자동 전환)</li>\n<li><strong>Stop</strong>: 훈련 종료 및 저장</li>\n<li><strong>Reset</strong>: 모든 기록 지우기</li>\n</ul>\n<h6>기록 방식</h6>\n<ul>\n<li>한 줄에 \"숨참기 시간 + 휴식 시간\"이 함께 저장됩니다</li>\n<li>그래프로 보면 빨간색(숨참기), 파란색(휴식)으로 표시돼요</li>\n<li>CSV, JSON, PNG 파일로 내보내기 가능</li>\n</ul>\n<hr>\n<h5>실전 훈련 방법: 단계별 프로토콜</h5>\n<p>초보자를 위한 기본 CO₂ 테이블 예시입니다. 본인 실력에 맞춰 시간을 조절하세요.</p>\n<table>\n<thead>\n<tr><th>세트</th><th>숨참기 시간</th><th>휴식 시간</th><th>특징</th></tr>\n</thead>\n<tbody>\n<tr><td>1회</td><td>2분</td><td>1분 45초</td><td>편안하게 시작</td></tr>\n<tr><td>2회</td><td>2분</td><td>1분 30초</td><td>휴식이 조금 줄어듦</td></tr>\n<tr><td>3회</td><td>2분</td><td>1분 15초</td><td>점점 힘들어짐</td></tr>\n<tr><td>4회</td><td>2분</td><td>1분</td><td>본격적인 도전</td></tr>\n<tr><td>5회</td><td>2분</td><td>45초</td><td>거의 끝!</td></tr>\n<tr><td>6회</td><td>2분</td><td>30초</td><td>마지막 세트</td></tr>\n</tbody>\n</table>\n<h6>핵심 포인트</h6>\n<ul>\n<li>숨참기 시간(2분)은 모든 세트에서 똑같이 유지</li>\n<li>휴식 시간만 점점 짧아집니다</li>\n<li>이렇게 하면 CO₂가 쌓이는 느낌에 점차 익숙해져요</li>\n</ul>\n<hr>\n<h5>훈련 기록, 이렇게 활용하세요</h5>\n<h6>Lap 버튼 활용법</h6>\n<ol>\n<li>숨참기 시작 → Start 버튼</li>\n<li>숨참기 끝 → Lap 버튼 (자동으로 휴식 측정 시작)</li>\n<li>휴식 끝 → Lap 버튼 (다음 세트 숨참기 측정 시작)</li>\n<li>전체 종료 → Stop 버튼</li>\n</ol>\n<h6>그래프 해석 팁</h6>\n<ul>\n<li>빨간 막대(숨참기)가 일정한지 확인하세요</li>\n<li>파란 막대(휴식)가 점점 낮아지는지 체크하세요</li>\n<li>패턴이 불규칙하다면 훈련 강도를 조절할 필요가 있어요</li>\n</ul>\n<h6>데이터 저장하기</h6>\n<ul>\n<li><strong>CSV/JSON</strong>: 엑셀이나 구글 시트에서 분석</li>\n<li><strong>PNG</strong>: 그래프 이미지로 보관, SNS 공유 가능</li>\n</ul>\n<hr>\n<h5>훈련 스케줄 추천</h5>\n<h6>이상적인 빈도</h6>\n<ul>\n<li><strong>주 2~3회</strong>: 매일 하면 오히려 피곤해요</li>\n<li><strong>격일 훈련</strong>: 월·수·금 또는 화·목·토</li>\n<li><strong>휴식일 준수</strong>: 몸이 회복할 시간이 필요합니다</li>\n</ul>\n<h6>점진적 발전 전략</h6>\n<ol>\n<li><strong>첫 달</strong>: 기본 프로토콜 완성 (위 표 참고)</li>\n<li><strong>둘째 달</strong>: 휴식 시간 15초씩 추가로 단축</li>\n<li><strong>셋째 달</strong>: 숨참기 시간 15초씩 증가</li>\n</ol>\n<hr>\n<h5>초보자가 흔히 하는 실수들</h5>\n<table>\n<thead>\n<tr><th>실수</th><th>왜 위험한가요?</th><th>올바른 방법</th></tr>\n</thead>\n<tbody>\n<tr><td>과호흡으로 시작</td><td>기절 위험</td><td>편안한 호흡 유지</td></tr>\n<tr><td>혼자 훈련</td><td>사고 시 대처 불가</td><td>반드시 감시자 동반</td></tr>\n<tr><td>휴식 무리하게 단축</td><td>멘탈·체력 소진</td><td>점진적 감소 원칙</td></tr>\n<tr><td>바로 수중 훈련</td><td>익수 사고 위험</td><td>육지 숙련 후 진행</td></tr>\n</tbody>\n</table>\n<hr>\n<h5>자주 묻는 질문 TOP 3</h5>\n<p><strong>Q1. CO₂ 테이블만 해도 기록이 늘어나나요?</strong><br>어느 정도 효과가 있지만, 킥 기술, 이퀄라이징(귀 압력 조절), 멘탈 트레이닝을 함께 해야 진짜 실력이 늘어요.</p>\n<p><strong>Q2. 집에서도 가능한가요?</strong><br>네! 소파나 침대에서 안전하게 연습할 수 있어요. 이걸 \'건식 훈련\'이라고 부릅니다.</p>\n<p><strong>Q3. 수중에서 해도 되나요?</strong><br>반드시 버디(짝)와 안전 장비를 갖춘 상태에서만 가능합니다. 절대 혼자 하지 마세요.</p>\n<hr>\n<h5>정리하며</h5>\n<p>이 가이드는 CO₂ 테이블의 원리부터 실전 적용, 안전 수칙, 기록 분석까지 모든 것을 담았습니다.</p>\n<h6>시작하기 전 체크리스트</h6>\n<ul class=\"checklist\">\n<li>안전 감시자 확보</li>\n<li>건강 상태 양호</li>\n<li>스톱워치 준비</li>\n<li>편안한 환경 조성</li>\n<li>안전 수칙 숙지</li>\n</ul>\n<p>이제 위에 제공된 스톱워치를 활용해 직접 훈련을 시작해 보세요. 매주 기록을 확인하면서 본인의 발전을 느껴보는 것, 정말 뿌듯할 거예요!</p>\n<p><strong>안전한 프리다이빙, 즐거운 훈련 되세요!</strong></p>',
      'blog.backToTimers': '타이머로 돌아가기',
      'subscribe.title': '문의하기',
      'subscribe.body': '피드백이나 기능 요청이 있나요? 간단한 메시지를 보내주세요.',
      'subscribe.note': '1~2 영업일 내에 답변드립니다.',
      'subscribe.cta': '보내기',
      'subscribe.emailLabel': '이메일',
      'subscribe.messageLabel': '메시지',
      'subscribe.emailPlaceholder': 'you@example.com',
      'subscribe.messagePlaceholder': '필요한 내용을 알려주세요.',
      'footer.rights': '© 2026 Timer.app. 모든 권리 보유.'
    }
  };

  var current = 'ko';

  function t(key){
    if (MESSAGES[current] && MESSAGES[current][key]) return MESSAGES[current][key];
    if (MESSAGES.en && MESSAGES.en[key]) return MESSAGES.en[key];
    return key;
  }

  function apply(){
    var nodes = document.querySelectorAll('[data-i18n]');
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var key = el.getAttribute('data-i18n');
      var value = t(key);
      var attr = el.getAttribute('data-i18n-attr');
      if (attr) {
        el.setAttribute(attr, value);
        continue;
      }
      if (el.hasAttribute('data-i18n-html')) {
        el.innerHTML = value;
      } else {
        el.textContent = value;
      }
    }
  }

  function setLang(lang){
    if (!MESSAGES[lang]) lang = 'en';
    current = lang;
    document.documentElement.setAttribute('lang', lang);
    try { localStorage.setItem('lang', lang); } catch (e) { /* ignore */ }
    apply();
    try {
      document.dispatchEvent(new CustomEvent('app:lang', { detail: { lang: current } }));
    } catch (e) { /* ignore */ }
  }

  function init(){
    var stored = null;
    try { stored = localStorage.getItem('lang'); } catch (e) { /* ignore */ }
    var select = document.querySelector('.language-selector select');
    var initial = (stored || (select && select.value) || 'ko');
    if (select) select.value = initial;
    setLang(initial);
    if (select) {
      select.addEventListener('change', function(){
        setLang(select.value);
      });
    }
  }

  window.appI18n = { t: t, setLang: setLang, apply: apply };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
