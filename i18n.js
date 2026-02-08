(function(){
  var MESSAGES = {
    en: {
      'page.title': 'Timer App',
      'header.title': 'Grind',
      'nav.blog': 'App Guide',
      'nav.subscribe': 'Subscribe',
      'tabs.breathing': 'Breathing Timer',
      'tabs.co2': 'CO2 Table Timer',
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
      'blog.post2.title': 'Push Your Limits with CO2 Table Training',
      'blog.post2.p1': 'For athletes looking to gain a serious competitive edge, CO2 Table Training is a game-changer. This advanced technique involves a series of timed breath holds and recoveries, designed to improve your body\'s tolerance to carbon dioxide and the efficiency of your oxygen utilization.',
      'blog.post2.p2': 'Our CO2 Table Timer guides you through these challenging workouts with precision. By systematically increasing the duration of your breath holds, you train your body to perform better under the demanding conditions of high-intensity exercise. The benefits include increased endurance, delayed onset of fatigue, and a stronger dive reflex. Use our CO2 Table Timer to unlock new levels of performance and redefine your limits.',
      'blog.backToTimers': 'Back to Timers',
      'footer.rights': '© 2026 Timer.app. All rights reserved.'
    },
    ko: {
      'page.title': '타이머 앱',
      'header.title': '연마',
      'nav.blog': '앱 가이드',
      'nav.subscribe': '구독',
      'tabs.breathing': '호흡 타이머',
      'tabs.co2': 'CO2 테이블 타이머',
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
      'blog.post2.title': 'CO2 테이블 훈련으로 한계 돌파',
      'blog.post2.p1': '경쟁력을 크게 끌어올리고 싶은 선수에게 CO2 테이블 훈련은 게임 체인저입니다. 이 고급 훈련은 숨참기와 회복을 시간 단위로 반복하며, 이산화탄소 내성과 산소 활용 효율을 높이도록 설계되었습니다.',
      'blog.post2.p2': 'CO2 테이블 타이머는 도전적인 세션을 정밀하게 안내합니다. 숨참기 시간을 단계적으로 늘려 고강도 환경에서도 더 잘 버틸 수 있도록 훈련하며, 지구력 향상, 피로 지연, 강한 다이빙 반사 같은 효과를 기대할 수 있습니다. CO2 테이블 타이머로 새로운 퍼포먼스 레벨을 열어보세요.',
      'blog.backToTimers': '타이머로 돌아가기',
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
