(function(){
  var STORAGE_KEY = 'abrahang:lastCompletedAt';
  var HISTORY_KEY = 'abrahang:trainingHistory';
  var HISTORY_MIGRATED_KEY = 'abrahang:trainingHistoryMigrated';
  var BODY_WEIGHT_KEY = 'abrahang:bodyWeightKg';
  var ONE_HAND_KEY = 'abrahang:oneHandMode';
  var SCALE_MODE_KEY = 'abrahang:scaleMode';
  var RECOVERY_MS = 6 * 60 * 60 * 1000;
  var HISTORY_LIMIT = 100;
  var DEFAULT_INTENSITY = {
    paper: 50,
    video: 70
  };
  var WEIGHT_SCALE_SERVICE = 0x181d;
  var WEIGHT_MEASUREMENT_CHARACTERISTIC = 0x2a9d;
  var POUND_TO_KG = 0.45359237;
  var WHC06_MANUFACTURER_ID = 0x0100;
  var WHC06_NAME_PREFIX = 'IF_B7';
  var WHC06_WEIGHT_OFFSET = 10;
  var WHC06_HANG_SILENCE_MS = 4000;
  var WHC06_FIRST_PACKET_MS = 12000;
  var WHC06_FOREGROUND_PACKET_MS = 15000;
  var WHC06_MANUAL_FIRST_PACKET_MS = 20000;
  var WHC06_RECOVERY_COOLDOWN_MS = 7000;
  var WHC06_STALE_MS = 90000;
  var WHC06_RESTART_GAP_MS = 250;
  var WHC06_UNWATCH_TIMEOUT_MS = 1500;
  var PRECOUNT_MS = 3000;
  var BEEP_GAIN = 1;

  var TEXT = {
    en: {
      hang: 'Load',
      rest: 'Rest',
      prestart: 'Starting',
      ready: 'Ready',
      done: 'Complete',
      start: 'Start',
      pause: 'Pause',
      resume: 'Resume',
      nextEmpty: 'No completed session yet',
      nextReady: 'Ready now',
      nextAt: 'After {time}',
      remaining: 'remaining',
      paperNote: 'Abrahangs mode: 18-22 mm edge, 10 s load / 20 s rest, 20 reps',
      videoNote: 'Emil mode: 10 s load / 50 s rest, 10 reps',
      baseTitle: '4-finger base hang',
      baseCue: 'Use an 18-22 mm edge. Keep both feet grounded and feel only light forearm strain.',
      front3Title: 'Front 3 open grip',
      front3Cue: 'Index, middle, and ring fingers. Open grip, low load, no pulling to failure.',
      front2OpenTitle: 'Front 2 open grip',
      front2OpenCue: 'Index and middle fingers. Keep shoulders quiet and unload with the feet.',
      middle2OpenTitle: 'Middle 2 open grip',
      middle2OpenCue: 'Middle and ring fingers. Keep the wrist neutral and the strain small.',
      front2CrimpTitle: 'Front 2 half crimp',
      front2CrimpCue: 'Index and middle fingers in a controlled half crimp. Stop on sharp pain.',
      middle2CrimpTitle: 'Middle 2 half crimp',
      middle2CrimpCue: 'Middle and ring fingers in a controlled half crimp. Keep the load conservative.',
      videoHalfTitle: 'Half crimp',
      videoHalfCue: 'Use a 15-20 mm edge and stand tall enough that the fingers are loaded, not punished.',
      videoFront3Cue: 'Use a 30-40 mm edge with the first pads set in an open grip.',
      restCue: 'Shake out, breathe normally, and keep the next load deliberately easy.',
      crimpRestCue: 'Shake out. During the last crimp rests, lightly loosen the little finger and forearm.',
      nextPreviewTitle: 'Next set preview',
      finalRestTitle: 'Final rest',
      finalRestCue: 'This is the last rest. The session will complete when the timer reaches zero.',
      prestartTitle: 'First set starts after the count.',
      prestartCue: 'Set your fingers and keep the load easy. Start loading after the beep.',
      readyTitle: 'Place your feet on the floor and your fingers on the edge.',
      readyCue: 'Begin only when the load feels easy and controlled.',
      doneTitle: 'Session complete.',
      doneCue: 'Keep at least six hours before the next finger-loading session or hard climbing.'
    },
    ko: {
      hang: '로딩',
      rest: '휴식',
      prestart: '카운트다운',
      ready: '준비',
      done: '완료',
      start: '시작',
      pause: '일시정지',
      resume: '재개',
      nextEmpty: '아직 완료 기록 없음',
      nextReady: '지금 가능',
      nextAt: '{time} 이후',
      remaining: '남음',
      paperNote: 'Abrahangs 모드: 18-22mm 엣지, 10초 로딩/20초 휴식, 총 20회',
      videoNote: 'Emil 모드: 10초 로딩/50초 휴식, 총 10회',
      baseTitle: '4손가락 기본 행',
      baseCue: '18-22mm 엣지를 사용합니다. 발은 바닥에 두고 전완에 약한 긴장만 느끼세요.',
      front3Title: '앞 3손가락 오픈 그립',
      front3Cue: '검지, 중지, 약지를 오픈 그립으로 겁니다. 실패 지점까지 당기지 않습니다.',
      front2OpenTitle: '앞 2손가락 오픈 그립',
      front2OpenCue: '검지와 중지를 사용합니다. 어깨를 조용히 두고 발로 하중을 덜어냅니다.',
      middle2OpenTitle: '중간 2손가락 오픈 그립',
      middle2OpenCue: '중지와 약지를 사용합니다. 손목을 중립에 두고 긴장은 작게 유지합니다.',
      front2CrimpTitle: '앞 2손가락 하프 크림프',
      front2CrimpCue: '검지와 중지를 하프 크림프로 겁니다. 날카로운 통증이 있으면 즉시 멈춥니다.',
      middle2CrimpTitle: '중간 2손가락 하프 크림프',
      middle2CrimpCue: '중지와 약지를 하프 크림프로 겁니다. 하중은 보수적으로 유지합니다.',
      videoHalfTitle: '하프 크림프',
      videoHalfCue: '15-20mm 엣지를 사용합니다. 손가락을 벌주는 느낌이 아니라 가볍게 싣는 느낌으로 서세요.',
      videoFront3Cue: '30-40mm 엣지에 첫 마디만 걸리는 오픈 그립으로 진행합니다.',
      restCue: '손을 털고 편하게 호흡합니다. 다음 로딩도 의도적으로 쉽게 유지하세요.',
      crimpRestCue: '손을 털어 주세요. 마지막 크림프 휴식 중에는 새끼손가락과 전완을 가볍게 풀어 줍니다.',
      nextPreviewTitle: '다음 세트 미리보기',
      finalRestTitle: '마지막 휴식',
      finalRestCue: '마지막 휴식입니다. 타이머가 끝나면 세션이 완료됩니다.',
      prestartTitle: '카운트 후 첫 세트를 시작합니다.',
      prestartCue: '손을 올리고 하중은 쉽게 유지하세요. 신호음 후 로딩을 시작합니다.',
      readyTitle: '발을 바닥에 두고 엣지에 손을 올리세요.',
      readyCue: '하중을 쉽게 통제 가능할 때만 시작합니다.',
      doneTitle: '세션 완료.',
      doneCue: '다음 손가락 로딩 세션 또는 강한 클라이밍까지 최소 6시간을 둡니다.'
    }
  };

  function lang(){
    return (document.documentElement.getAttribute('lang') || 'ko').indexOf('en') === 0 ? 'en' : 'ko';
  }

  function tt(key){
    var table = TEXT[lang()] || TEXT.ko;
    return table[key] || TEXT.en[key] || key;
  }

  function siteT(key, fallback){
    if(window.appI18n && typeof window.appI18n.t === 'function'){
      var value = window.appI18n.t(key);
      if(value && value !== key) return value;
    }
    return fallback || key;
  }

  function makeRepeated(count, titleKey, cueKey, options){
    var out = [];
    for(var i = 0; i < count; i++){
      out.push({
        titleKey: titleKey,
        cueKey: cueKey,
        restCueKey: options && options.restCueKey ? options.restCueKey : 'restCue',
        edge: options && options.edge ? options.edge : ''
      });
    }
    return out;
  }

  function buildProtocol(mode){
    if(mode === 'video'){
      return {
        mode: 'video',
        hangMs: 10000,
        restMs: 50000,
        noteKey: 'videoNote',
        steps: []
          .concat(makeRepeated(3, 'videoHalfTitle', 'videoHalfCue', { edge: '15-20 mm' }))
          .concat(makeRepeated(3, 'front3Title', 'videoFront3Cue', { edge: '30-40 mm' }))
          .concat(makeRepeated(1, 'front2OpenTitle', 'front2OpenCue', { edge: '30-40 mm' }))
          .concat(makeRepeated(1, 'middle2OpenTitle', 'middle2OpenCue', { edge: '30-40 mm' }))
          .concat(makeRepeated(1, 'middle2CrimpTitle', 'middle2CrimpCue', { edge: '15-20 mm', restCueKey: 'crimpRestCue' }))
          .concat(makeRepeated(1, 'front2CrimpTitle', 'front2CrimpCue', { edge: '15-20 mm', restCueKey: 'crimpRestCue' }))
      };
    }
    return {
      mode: 'paper',
      hangMs: 10000,
      restMs: 20000,
      noteKey: 'paperNote',
      steps: []
        .concat(makeRepeated(6, 'baseTitle', 'baseCue', { edge: '18-22 mm' }))
        .concat(makeRepeated(6, 'front3Title', 'front3Cue', { edge: '18-22 mm' }))
        .concat(makeRepeated(2, 'front2OpenTitle', 'front2OpenCue', { edge: '18-22 mm' }))
        .concat(makeRepeated(2, 'middle2OpenTitle', 'middle2OpenCue', { edge: '18-22 mm' }))
        .concat(makeRepeated(2, 'front2CrimpTitle', 'front2CrimpCue', { edge: '18-22 mm', restCueKey: 'crimpRestCue' }))
        .concat(makeRepeated(2, 'middle2CrimpTitle', 'middle2CrimpCue', { edge: '18-22 mm', restCueKey: 'crimpRestCue' }))
    };
  }

  function boot(){
    var roots = document.querySelectorAll('.abrahang-app');
    for(var i = 0; i < roots.length; i++){
      if(roots[i].getAttribute('data-ab-initialized') === '1') continue;
      init(roots[i]);
    }
  }

  function init(root){
    root.setAttribute('data-ab-initialized', '1');
    function q(sel){ return root.querySelector(sel); }
    var modeButtons = root.querySelectorAll('[data-ab-mode]');
    var startBtn = q('#abStart');
    var resetBtn = q('#abReset');
    var intensity = q('#abIntensity');
    var intensityValue = q('#abIntensityValue');
    var bodyWeight = q('#abBodyWeight');
    var oneHand = q('#abOneHand');
    var loadTarget = q('#abLoadTarget');
    var scaleConnect = q('#abScaleConnect');
    var scaleConnectWhc06 = q('#abScaleConnectWhc06');
    var scaleStatus = q('#abScaleStatus');
    var scaleSupport = q('#abScaleSupport');
    var scaleModeButtons = root.querySelectorAll('[data-ab-scale-mode]');
    var scaleMetrics = q('.abrahang-scale-metrics');
    var scaleReadingMetric = q('#abScaleReadingMetric');
    var scaleFingerLoadMetric = q('#abScaleFingerLoadMetric');
    var scaleReadingLabel = q('#abScaleReadingLabel');
    var scaleFingerLoadLabel = q('#abScaleFingerLoadLabel');
    var scaleTargetLabel = q('#abScaleTargetLabel');
    var scaleReading = q('#abScaleReading');
    var scaleFingerLoad = q('#abScaleFingerLoad');
    var scaleTargetReading = q('#abScaleTargetReading');
    var sound = q('#abSound');
    var autoLog = q('#abAutoLog');
    var phaseEl = q('#abPhase');
    var timeEl = q('#abTime');
    var countEl = q('#abStepCount');
    var moveTitle = q('#abMoveTitle');
    var moveCue = q('#abMoveCue');
    var totalBar = q('#abTotalBar');
    var totalRemaining = q('#abTotalRemaining');
    var ringFill = q('#abRingFill');
    var dial = q('.abrahang-dial');
    var stepsEl = q('#abSteps');
    var noteEl = q('#abProtocolNote');
    var nextEl = q('#abNextSession');
    var historyList = q('#abHistoryList');
    var historyClear = q('#abHistoryClear');
    var metricLoad = q('#abMetricLoad');
    var metricRest = q('#abMetricRest');
    var metricReps = q('#abMetricReps');

    var audioCtx = null;
    var rafId = 0;
    var lastTick = 0;
    var lastCountdownSecond = -1;
    var temporaryCueTimer = 0;
    var editingHistoryId = null;

    var state = {
      mode: 'paper',
      protocol: buildProtocol('paper'),
      running: false,
      phase: 'ready',
      stepIndex: 0,
      remainingMs: 10000,
      elapsedMs: 0,
      completedLogged: false,
      historyLogged: false,
      loadSampleCount: 0,
      maxMeasuredLoadKg: null,
      lastMeasuredLoadKg: null
    };
    var scaleDisplayMode = 'foot';
    var scaleState = {
      device: null,
      connectionType: null,
      characteristic: null,
      disconnectHandler: null,
      advertisementHandler: null,
      advertisementTimeout: 0,
      firstPacketTimeout: 0,
      firstPacketExpectedSince: 0,
      firstPacketStatusKey: '',
      firstPacketStatusFallback: '',
      advertisementRestarting: false,
      lastAdvertisementAt: 0,
      recoveryAttemptAt: 0,
      foregroundLossAt: 0,
      foregroundCheckAt: 0,
      foregroundNeedsFreshPacket: false,
      watchGeneration: 0,
      watchStale: false,
      connecting: false,
      connectingType: null,
      readingKg: null,
      peakLoadKg: null,
      statusKey: 'abrahang.scaleStatusIdle',
      statusFallback: 'Not connected',
      statusTone: 'idle'
    };

    function protocolTotalMs(protocol){
      return protocol.steps.length * (protocol.hangMs + protocol.restMs);
    }

    function phaseDuration(){
      if(state.phase === 'prestart') return PRECOUNT_MS;
      if(state.phase === 'hang') return state.protocol.hangMs;
      if(state.phase === 'rest') return state.protocol.restMs;
      return state.protocol.hangMs;
    }

    function formatSeconds(ms){
      var sec = Math.max(0, Math.ceil(ms / 1000));
      if(sec < 60) return String(sec);
      var m = Math.floor(sec / 60);
      var s = sec % 60;
      return String(m) + ':' + (s < 10 ? '0' : '') + String(s);
    }

    function formatMinuteSecond(ms){
      var sec = Math.max(0, Math.ceil(ms / 1000));
      var m = Math.floor(sec / 60);
      var s = sec % 60;
      return String(m) + ':' + (s < 10 ? '0' : '') + String(s);
    }

    function formatShort(sec){
      return lang() === 'en' ? sec + 's' : sec + '초';
    }

    function setDefaultIntensityForMode(mode){
      if(!intensity) return;
      var next = DEFAULT_INTENSITY[mode] || DEFAULT_INTENSITY.paper;
      intensity.value = String(next);
    }

    function parseBodyWeight(){
      if(!bodyWeight) return 0;
      var normalized = String(bodyWeight.value || '').replace(',', '.');
      var kg = Number(normalized);
      if(!isFinite(kg) || kg <= 0) return 0;
      return kg;
    }

    function formatKg(value){
      var rounded = Math.round(value * 10) / 10;
      return rounded.toFixed(rounded % 1 === 0 ? 0 : 1) + 'kg';
    }

    function isOneHandMode(){
      return !!(oneHand && oneHand.checked);
    }

    function targetLoadKg(bodyKg){
      var intensityValueNumber = intensity ? Number(intensity.value) || 0 : 0;
      var handFactor = isOneHandMode() ? 0.5 : 1;
      return bodyKg * intensityValueNumber / 100 * handFactor;
    }

    function measuredLoadFromScaleReading(readingKg){
      if(readingKg == null || !isFinite(readingKg)) return null;
      if(getScaleDisplayMode() === 'crane') return Math.max(0, readingKg);
      var bodyKg = parseBodyWeight();
      if(bodyKg <= 0) return null;
      return Math.max(0, bodyKg - readingKg);
    }

    function resetSessionMeasurements(){
      state.loadSampleCount = 0;
      state.maxMeasuredLoadKg = null;
      state.lastMeasuredLoadKg = null;
    }

    function resetScalePeakLoad(){
      scaleState.peakLoadKg = null;
    }

    function updateScalePeakLoad(readingKg){
      var loadKg = measuredLoadFromScaleReading(readingKg);
      if(loadKg == null) return;
      if(scaleState.peakLoadKg == null || loadKg > scaleState.peakLoadKg){
        scaleState.peakLoadKg = loadKg;
      }
      return loadKg;
    }

    function recordScaleLoadSample(readingKg){
      var loadKg = updateScalePeakLoad(readingKg);
      if(loadKg == null || !state.running || state.phase !== 'hang') return;
      state.loadSampleCount += 1;
      state.lastMeasuredLoadKg = loadKg;
      if(state.maxMeasuredLoadKg == null || loadKg > state.maxMeasuredLoadKg){
        state.maxMeasuredLoadKg = loadKg;
      }
    }

    function emptyScaleText(){
      return siteT('abrahang.scaleEmpty', '--');
    }

    function hasBluetoothScaleSupport(){
      return !!(navigator.bluetooth && typeof navigator.bluetooth.requestDevice === 'function');
    }

    function getWhc06Support(){
      if(typeof window.isSecureContext !== 'undefined' && !window.isSecureContext){
        return {
          ok: false,
          key: 'abrahang.scaleSupportNoSecure',
          fallback: lang() === 'en' ? 'Bluetooth requires HTTPS or localhost.' : 'Bluetooth는 HTTPS 또는 localhost에서만 동작합니다.'
        };
      }
      if(!hasBluetoothScaleSupport()){
        return {
          ok: false,
          key: 'abrahang.scaleSupportNoBluetooth',
          fallback: lang() === 'en' ? 'This browser cannot use Web Bluetooth.' : '이 브라우저는 Web Bluetooth를 사용할 수 없습니다.'
        };
      }
      if(!window.BluetoothDevice || !window.BluetoothDevice.prototype || typeof window.BluetoothDevice.prototype.watchAdvertisements !== 'function'){
        return {
          ok: false,
          key: 'abrahang.scaleSupportNoAdvertisements',
          fallback: lang() === 'en'
            ? 'WH-C06 live receiver: unavailable. Use Chrome with Experimental Web Platform features enabled, then restart Chrome.'
            : 'WH-C06 실시간 수신 불가: Chrome에서 Experimental Web Platform features를 켠 뒤 Chrome을 완전히 재시작해야 합니다.'
        };
      }
      return {
        ok: true,
        key: 'abrahang.scaleSupportReady',
        fallback: lang() === 'en' ? 'WH-C06 live receiver: available' : 'WH-C06 실시간 수신 가능'
      };
    }

    function renderWhc06Support(){
      if(!scaleSupport) return getWhc06Support();
      var support = getWhc06Support();
      scaleSupport.textContent = siteT(support.key, support.fallback);
      scaleSupport.classList.toggle('is-error', !support.ok);
      scaleSupport.classList.toggle('is-ok', support.ok);
      return support;
    }

    function setScaleStatus(key, fallback, tone){
      scaleState.statusKey = key;
      scaleState.statusFallback = fallback;
      scaleState.statusTone = tone || 'idle';
      renderScale();
    }

    function setScaleStatusSilently(key, fallback, tone){
      scaleState.statusKey = key;
      scaleState.statusFallback = fallback;
      scaleState.statusTone = tone || 'idle';
    }

    function parseWeightMeasurement(value){
      if(!value || value.byteLength < 3) return null;
      var flags = value.getUint8(0);
      var raw = value.getUint16(1, true);
      if(raw === 0xffff) return null;
      var isImperial = (flags & 0x01) === 0x01;
      var kg = isImperial ? raw * 0.01 * POUND_TO_KG : raw * 0.005;
      if(!isFinite(kg) || kg < 0) return null;
      return kg;
    }

    function parseWhc06Advertisement(event){
      if(!event || !event.manufacturerData || typeof event.manufacturerData.get !== 'function') return null;
      var data = event.manufacturerData.get(WHC06_MANUFACTURER_ID);
      if(!data || data.byteLength <= WHC06_WEIGHT_OFFSET + 1) return null;
      var raw = (data.getUint8(WHC06_WEIGHT_OFFSET) << 8) | data.getUint8(WHC06_WEIGHT_OFFSET + 1);
      var kg = raw / 100;
      if(!isFinite(kg) || kg < 0) return null;
      return kg;
    }

    function clearWhc06PacketTimers(){
      if(scaleState.advertisementTimeout){
        clearTimeout(scaleState.advertisementTimeout);
        scaleState.advertisementTimeout = 0;
      }
      if(scaleState.firstPacketTimeout){
        clearTimeout(scaleState.firstPacketTimeout);
        scaleState.firstPacketTimeout = 0;
      }
      scaleState.firstPacketExpectedSince = 0;
      scaleState.firstPacketStatusKey = '';
      scaleState.firstPacketStatusFallback = '';
    }

    function resetWhc06PacketTimeout(){
      clearWhc06PacketTimers();
      if(scaleState.connectionType !== 'whc06') return;
      scaleState.watchStale = false;
      scaleState.advertisementTimeout = setTimeout(function(){
        if(scaleState.connectionType !== 'whc06') return;
        if(scaleState.foregroundLossAt || document.visibilityState === 'hidden'){
          scaleState.foregroundNeedsFreshPacket = true;
          scaleState.advertisementTimeout = 0;
          return;
        }
        markWhc06Stale();
      }, WHC06_STALE_MS);
    }

    function nudgeWhc06WatchForLoad(){
      if(scaleState.connectionType !== 'whc06' || !scaleState.device || scaleState.watchStale) return;
      restartWhc06AdvertisementWatch(false);
    }

    function markWhc06Stale(){
      clearWhc06PacketTimers();
      scaleState.watchStale = true;
      setScaleStatus(
        'abrahang.scaleStatusWhc06Stale',
        lang() === 'en' ? 'WH-C06 stream stopped. Use WH-C06 rescan.' : 'WH-C06 수신이 멈췄습니다. WH-C06 새로 스캔을 누르세요.',
        'error'
      );
    }

    function markWhc06NoFirstPacket(){
      if(scaleState.connectionType !== 'whc06') return;
      if(scaleState.firstPacketExpectedSince && scaleState.lastAdvertisementAt >= scaleState.firstPacketExpectedSince) return;
      if(!scaleState.firstPacketExpectedSince && scaleState.readingKg != null) return;
      var statusKey = scaleState.firstPacketStatusKey || 'abrahang.scaleStatusWhc06NoFirstPacket';
      var statusFallback = scaleState.firstPacketStatusFallback || (lang() === 'en' ? 'No WH-C06 packets from the paired device. Use WH-C06 rescan.' : '페어링된 WH-C06에서 값이 들어오지 않습니다. WH-C06 새로 스캔을 누르세요.');
      clearWhc06PacketTimers();
      scaleState.watchStale = true;
      setScaleStatus(
        statusKey,
        statusFallback,
        'error'
      );
    }

    function setWhc06FirstPacketTimeout(durationMs, statusKey, fallback){
      if(scaleState.firstPacketTimeout){
        clearTimeout(scaleState.firstPacketTimeout);
        scaleState.firstPacketTimeout = 0;
      }
      scaleState.firstPacketExpectedSince = 0;
      scaleState.firstPacketStatusKey = '';
      scaleState.firstPacketStatusFallback = '';
      if(!durationMs) return;
      scaleState.firstPacketExpectedSince = Date.now();
      scaleState.firstPacketStatusKey = statusKey || '';
      scaleState.firstPacketStatusFallback = fallback || '';
      scaleState.firstPacketTimeout = setTimeout(markWhc06NoFirstPacket, durationMs);
    }

    function handleScaleValue(value){
      var kg = parseWeightMeasurement(value);
      if(kg == null){
        setScaleStatus('abrahang.scaleStatusBadReading', lang() === 'en' ? 'The scale sent an unreadable value.' : '저울값을 읽을 수 없습니다.', 'error');
        return;
      }
      scaleState.readingKg = kg;
      recordScaleLoadSample(kg);
      setScaleStatus('abrahang.scaleStatusLive', lang() === 'en' ? 'Live weight is streaming.' : '실시간 저울값 표시 중', 'ok');
    }

    function handleScaleMeasurement(event){
      if(event && event.target) handleScaleValue(event.target.value);
    }

    function handleWhc06Advertisement(event){
      scaleState.lastAdvertisementAt = Date.now();
      scaleState.recoveryAttemptAt = 0;
      scaleState.watchStale = false;
      if(scaleState.firstPacketTimeout){
        clearTimeout(scaleState.firstPacketTimeout);
        scaleState.firstPacketTimeout = 0;
      }
      scaleState.firstPacketExpectedSince = 0;
      scaleState.firstPacketStatusKey = '';
      scaleState.firstPacketStatusFallback = '';
      resetWhc06PacketTimeout();
      var kg = parseWhc06Advertisement(event);
      if(kg == null){
        if(scaleState.readingKg == null){
          setScaleStatus(
            'abrahang.scaleStatusWhc06PacketNoWeight',
            lang() === 'en' ? 'WH-C06 packet received. Waiting for weight data.' : 'WH-C06 패킷 수신 중. 무게값 대기 중',
            'waiting'
          );
        }
        return;
      }
      scaleState.readingKg = kg;
      recordScaleLoadSample(kg);
      setScaleStatusSilently('abrahang.scaleStatusLive', lang() === 'en' ? 'Live weight is streaming.' : '실시간 저울값 표시 중', 'ok');
      renderScale();
    }

    function attachWhc06AdvertisementHandler(device){
      if(!device) return;
      if(scaleState.advertisementHandler){
        try{
          device.removeEventListener('advertisementreceived', scaleState.advertisementHandler);
        }catch(e){ /* ignore */ }
      }
      scaleState.advertisementHandler = handleWhc06Advertisement;
      device.addEventListener('advertisementreceived', scaleState.advertisementHandler);
    }

    function isAlreadyWatchingError(error){
      var text = String(error ? ((error.name || '') + ' ' + (error.message || '')) : '');
      return text.indexOf('InvalidStateError') !== -1 || text.toLowerCase().indexOf('already') !== -1;
    }

    function waitMs(ms){
      return new Promise(function(resolve){ setTimeout(resolve, ms); });
    }

    function stopWhc06AdvertisementWatch(device, timeoutMs){
      if(!device || typeof device.unwatchAdvertisements !== 'function') return Promise.resolve();
      try{
        var result = device.unwatchAdvertisements();
        if(result && typeof result.then === 'function'){
          if(timeoutMs){
            return Promise.race([
              result.catch(function(){}),
              waitMs(timeoutMs)
            ]);
          }
          return result.catch(function(){});
        }
      }catch(e){ /* ignore */ }
      return Promise.resolve();
    }

    function isWhc06Device(device){
      return !!(device && device.name && device.name.indexOf(WHC06_NAME_PREFIX) === 0);
    }

    async function findPermittedWhc06Device(){
      if(!navigator.bluetooth || typeof navigator.bluetooth.getDevices !== 'function') return null;
      var devices = await navigator.bluetooth.getDevices();
      var currentName = scaleState.device && scaleState.device.name;
      for(var i = 0; i < devices.length; i++){
        if(isWhc06Device(devices[i]) || (currentName && devices[i].name === currentName)) return devices[i];
      }
      return null;
    }

    async function startWhc06DeviceWatch(device, options){
      if(!device) throw new Error('No WH-C06 device selected');
      if(typeof device.watchAdvertisements !== 'function'){
        throw new Error('watchAdvertisements unsupported for WH-C06');
      }
      options = options || {};
      await cleanupScaleDevice({ skipWhc06Unwatch: !!options.skipWhc06Unwatch });
      var generation = scaleState.watchGeneration + 1;
      scaleState.watchGeneration = generation;
      if(options.clearReading !== false){
        scaleState.readingKg = null;
        resetScalePeakLoad();
      }
      scaleState.device = device;
      scaleState.connectionType = 'whc06';
      scaleState.watchStale = false;
      scaleState.lastAdvertisementAt = 0;
      attachWhc06AdvertisementHandler(device);
      if(options.forceRestart){
        await stopWhc06AdvertisementWatch(device, WHC06_UNWATCH_TIMEOUT_MS);
        if(scaleState.watchGeneration !== generation) return;
        await waitMs(WHC06_RESTART_GAP_MS);
      }
      if(scaleState.watchGeneration !== generation) return;
      try{
        await device.watchAdvertisements();
      }catch(e){
        if(!isAlreadyWatchingError(e)) throw e;
      }
      if(scaleState.watchGeneration !== generation) return;
      resetWhc06PacketTimeout();
      setWhc06FirstPacketTimeout(options.firstPacketTimeout || 0);
      setScaleStatus(
        options.statusKey || 'abrahang.scaleStatusWhc06Connected',
        options.statusFallback || (lang() === 'en' ? 'WH-C06 selected. Waiting for advertisement data.' : 'WH-C06 선택됨. 광고 데이터 수신 대기 중'),
        options.statusTone || 'waiting'
      );
    }

    async function recoverWhc06FromPermittedDevice(){
      if(scaleState.advertisementRestarting) return;
      var now = Date.now();
      if(scaleState.recoveryAttemptAt && now - scaleState.recoveryAttemptAt < WHC06_RECOVERY_COOLDOWN_MS) return;
      scaleState.recoveryAttemptAt = now;
      scaleState.advertisementRestarting = true;
      try{
        setScaleStatus(
          'abrahang.scaleStatusWhc06Recovering',
          lang() === 'en' ? 'WH-C06 stream paused. Rewatching paired device.' : 'WH-C06 수신이 멈춰 페어링된 장치를 다시 감시 중입니다.',
          'waiting'
        );
        var device = await findPermittedWhc06Device();
        if(device){
          await startWhc06DeviceWatch(device, {
            clearReading: false,
            statusKey: 'abrahang.scaleStatusWhc06PairedWatch',
            statusFallback: lang() === 'en' ? 'Trying paired WH-C06 recovery. If no value appears, use WH-C06 rescan.' : '페어링된 WH-C06 자동 복구를 시도 중입니다. 값이 안 뜨면 WH-C06 새로 스캔을 누르세요.',
            statusTone: 'waiting',
            firstPacketTimeout: WHC06_FIRST_PACKET_MS,
            skipWhc06Unwatch: true
          });
        }else{
          scaleState.advertisementRestarting = false;
          await restartWhc06AdvertisementWatch(false);
        }
      }catch(e){
        markWhc06Stale();
      }finally{
        scaleState.advertisementRestarting = false;
      }
    }

    async function restartWhc06AdvertisementWatch(showStatus, options){
      if(scaleState.connectionType !== 'whc06' || !scaleState.device) return;
      if(typeof scaleState.device.watchAdvertisements !== 'function') return;
      if(scaleState.advertisementRestarting) return;
      options = options || {};
      scaleState.advertisementRestarting = true;
      try{
        attachWhc06AdvertisementHandler(scaleState.device);
        if(showStatus !== false){
          setScaleStatus(
            'abrahang.scaleStatusWhc06Stale',
            lang() === 'en' ? 'Checking WH-C06 advertisement watch. Keep the scale awake.' : 'WH-C06 광고 감시를 확인 중입니다. 저울 전원을 유지하세요.',
            'waiting'
          );
        }
        if(options.stopFirst) await stopWhc06AdvertisementWatch(scaleState.device);
        await scaleState.device.watchAdvertisements();
        resetWhc06PacketTimeout();
        if(options.firstPacketTimeout){
          setWhc06FirstPacketTimeout(
            options.firstPacketTimeout,
            options.firstPacketStatusKey,
            options.firstPacketStatusFallback
          );
        }
      }catch(e){
        if(isAlreadyWatchingError(e)){
          resetWhc06PacketTimeout();
          if(options.firstPacketTimeout){
            setWhc06FirstPacketTimeout(
              options.firstPacketTimeout,
              options.firstPacketStatusKey,
              options.firstPacketStatusFallback
            );
          }
        }else{
          setScaleStatus(
            'abrahang.scaleStatusWhc06WatchError',
            lang() === 'en' ? 'WH-C06 advertisement watch could not start. Turn the scale off and on, then reconnect.' : 'WH-C06 광고 감시를 시작하지 못했습니다. 저울 전원을 껐다 켠 뒤 다시 연결하세요.',
            'error'
          );
        }
      }finally{
        scaleState.advertisementRestarting = false;
      }
    }

    function monitorWhc06DuringHang(){
      if(!state.running || state.phase !== 'hang') return;
      if(scaleState.connectionType !== 'whc06' || !scaleState.device || scaleState.watchStale) return;
      if(!scaleState.lastAdvertisementAt) return;
      if(scaleState.foregroundNeedsFreshPacket){
        scaleState.foregroundNeedsFreshPacket = false;
        setScaleStatus(
          'abrahang.scaleStatusWhc06ForegroundCheck',
          lang() === 'en' ? 'Chrome returned. Timer kept running; checking for a fresh WH-C06 packet.' : 'Chrome 복귀. 타이머는 계속 진행하며 WH-C06 새 패킷을 확인 중입니다.',
          'waiting'
        );
        restartWhc06AdvertisementWatch(false, {
          firstPacketTimeout: WHC06_FOREGROUND_PACKET_MS,
          firstPacketStatusKey: 'abrahang.scaleStatusWhc06ForegroundNoPacket',
          firstPacketStatusFallback: lang() === 'en'
            ? 'Timer kept running, but WH-C06 data did not resume after Chrome returned. Use WH-C06 rescan.'
            : '타이머는 계속 진행됐지만 Chrome 복귀 후 WH-C06 수신이 재개되지 않았습니다. WH-C06 새로 스캔을 누르세요.'
        });
        return;
      }
      if(Date.now() - scaleState.lastAdvertisementAt >= WHC06_HANG_SILENCE_MS){
        recoverWhc06FromPermittedDevice();
      }
    }

    function noteWhc06ForegroundLoss(){
      if(scaleState.connectionType === 'whc06' && scaleState.device && !scaleState.watchStale){
        scaleState.foregroundLossAt = Date.now();
        scaleState.foregroundNeedsFreshPacket = true;
      }
    }

    function checkWhc06AfterForeground(force){
      if(scaleState.connectionType !== 'whc06' || !scaleState.device) return;
      if(scaleState.connecting) return;
      if(!force && !scaleState.foregroundLossAt && !scaleState.foregroundNeedsFreshPacket) return;
      var now = Date.now();
      if(scaleState.foregroundCheckAt && now - scaleState.foregroundCheckAt < 5000) return;
      scaleState.foregroundCheckAt = now;
      scaleState.foregroundLossAt = 0;
      scaleState.foregroundNeedsFreshPacket = false;
      setScaleStatus(
        'abrahang.scaleStatusWhc06ForegroundCheck',
        lang() === 'en' ? 'Chrome returned. Timer kept running; checking for a fresh WH-C06 packet.' : 'Chrome 복귀. 타이머는 계속 진행하며 WH-C06 새 패킷을 확인 중입니다.',
        'waiting'
      );
      restartWhc06AdvertisementWatch(false, {
        firstPacketTimeout: WHC06_FOREGROUND_PACKET_MS,
        firstPacketStatusKey: 'abrahang.scaleStatusWhc06ForegroundNoPacket',
        firstPacketStatusFallback: lang() === 'en'
          ? 'Timer kept running, but WH-C06 data did not resume after Chrome returned. Use WH-C06 rescan.'
          : '타이머는 계속 진행됐지만 Chrome 복귀 후 WH-C06 수신이 재개되지 않았습니다. WH-C06 새로 스캔을 누르세요.'
      });
    }

    function handleScaleDisconnected(){
      scaleState.characteristic = null;
      scaleState.connectionType = null;
      setScaleStatus('abrahang.scaleStatusDisconnected', lang() === 'en' ? 'Disconnected' : '연결 해제됨', 'waiting');
    }

    function cleanupScaleDevice(options){
      options = options || {};
      clearWhc06PacketTimers();
      var unwatchPromise = Promise.resolve();
      if(scaleState.characteristic){
        try{
          scaleState.characteristic.removeEventListener('characteristicvaluechanged', handleScaleMeasurement);
        }catch(e){ /* ignore */ }
      }
      if(scaleState.device && scaleState.advertisementHandler){
        try{
          scaleState.device.removeEventListener('advertisementreceived', scaleState.advertisementHandler);
        }catch(e){ /* ignore */ }
      }
      if(!options.skipWhc06Unwatch && scaleState.device && scaleState.connectionType === 'whc06' && typeof scaleState.device.unwatchAdvertisements === 'function'){
        unwatchPromise = stopWhc06AdvertisementWatch(scaleState.device);
      }
      if(scaleState.device && scaleState.disconnectHandler){
        try{
          scaleState.device.removeEventListener('gattserverdisconnected', scaleState.disconnectHandler);
        }catch(e){ /* ignore */ }
      }
      scaleState.characteristic = null;
      scaleState.disconnectHandler = null;
      scaleState.advertisementHandler = null;
      scaleState.advertisementRestarting = false;
      scaleState.lastAdvertisementAt = 0;
      scaleState.foregroundLossAt = 0;
      scaleState.foregroundNeedsFreshPacket = false;
      if(!options.preserveWatchGeneration) scaleState.watchGeneration += 1;
      scaleState.watchStale = false;
      return unwatchPromise;
    }

    function disconnectCurrentScale(options){
      var device = scaleState.device;
      cleanupScaleDevice(options);
      if(device && device.gatt && device.gatt.connected){
        try { device.gatt.disconnect(); } catch(e){ /* ignore */ }
      }
      scaleState.device = null;
      scaleState.connectionType = null;
    }

    async function disconnectCurrentScaleAsync(options){
      var device = scaleState.device;
      await cleanupScaleDevice(options);
      if(device && device.gatt && device.gatt.connected){
        try { device.gatt.disconnect(); } catch(e){ /* ignore */ }
      }
      scaleState.device = null;
      scaleState.connectionType = null;
    }

    function getScaleDisplayMode(){
      return scaleDisplayMode === 'crane' ? 'crane' : 'foot';
    }

    function saveScaleDisplayMode(mode){
      try { localStorage.setItem(SCALE_MODE_KEY, mode); } catch(e){ /* ignore */ }
    }

    function setScaleDisplayMode(mode, save){
      var nextMode = mode === 'crane' ? 'crane' : 'foot';
      if(nextMode !== scaleDisplayMode) resetScalePeakLoad();
      scaleDisplayMode = nextMode;
      if(save !== false) saveScaleDisplayMode(scaleDisplayMode);
      renderScale();
    }

    function loadScaleDisplayMode(){
      try{
        var stored = localStorage.getItem(SCALE_MODE_KEY);
        if(stored === 'crane' || stored === 'foot') scaleDisplayMode = stored;
      }catch(e){ /* ignore */ }
    }

    function renderScale(){
      var bodyKg = parseBodyWeight();
      var hasReading = scaleState.readingKg != null;
      var hasBodyWeight = bodyKg > 0;
      var standardConnected = scaleState.connectionType === 'standard' && scaleState.device && scaleState.device.gatt && scaleState.device.gatt.connected;
      var whc06NeedsFreshScan = scaleState.connectionType === 'whc06' && !!scaleState.device && scaleState.watchStale;
      var whc06Connected = scaleState.connectionType === 'whc06' && !!scaleState.device && !scaleState.watchStale;
      var isCraneScale = getScaleDisplayMode() === 'crane';

      for(var i = 0; i < scaleModeButtons.length; i++){
        var activeMode = scaleModeButtons[i].getAttribute('data-ab-scale-mode') === getScaleDisplayMode();
        scaleModeButtons[i].classList.toggle('is-active', activeMode);
        scaleModeButtons[i].setAttribute('aria-pressed', activeMode ? 'true' : 'false');
      }

      if(scaleReadingLabel){
        scaleReadingLabel.textContent = siteT(
          isCraneScale ? 'abrahang.scaleCurrentLoadLabel' : 'abrahang.scaleReadingLabel',
          isCraneScale ? (lang() === 'en' ? 'Current load' : '현재 하중') : (lang() === 'en' ? 'Scale reading' : '저울값')
        );
      }
      if(scaleFingerLoadLabel){
        scaleFingerLoadLabel.textContent = siteT('abrahang.scaleFingerLoadLabel', lang() === 'en' ? 'Finger load' : '실제 하중');
      }
      if(scaleTargetLabel){
        scaleTargetLabel.textContent = siteT('abrahang.scalePeakLoadLabel', lang() === 'en' ? 'Peak load' : '피크 하중');
      }
      if(scaleFingerLoadMetric) scaleFingerLoadMetric.hidden = isCraneScale;
      if(scaleMetrics) scaleMetrics.classList.toggle('is-crane', isCraneScale);
      if(scaleReadingMetric) scaleReadingMetric.classList.toggle('is-wide', isCraneScale);

      if(scaleStatus){
        scaleStatus.textContent = siteT(scaleState.statusKey, scaleState.statusFallback);
        scaleStatus.classList.toggle('is-error', scaleState.statusTone === 'error');
        scaleStatus.classList.toggle('is-waiting', scaleState.statusTone === 'waiting' || scaleState.connecting);
      }
      if(scaleConnect){
        scaleConnect.disabled = scaleState.connecting;
        if(scaleState.connecting && scaleState.connectingType === 'standard'){
          scaleConnect.textContent = siteT('abrahang.scaleStatusSearching', lang() === 'en' ? 'Searching for a scale...' : '저울 검색 중...');
        }else if(standardConnected){
          scaleConnect.textContent = siteT('abrahang.scaleReconnectStandard', lang() === 'en' ? 'Reconnect standard scale' : '표준 저울 다시 연결');
        }else{
          scaleConnect.textContent = siteT('abrahang.scaleConnectStandard', lang() === 'en' ? 'Standard scale (beta)' : '표준 저울 연결(beta)');
        }
      }
      if(scaleConnectWhc06){
        scaleConnectWhc06.disabled = scaleState.connecting;
        if(scaleState.connecting && scaleState.connectingType === 'whc06'){
          scaleConnectWhc06.textContent = siteT('abrahang.scaleStatusWhc06Searching', lang() === 'en' ? 'Searching for WH-C06 / IF_B7...' : 'WH-C06 / IF_B7 검색 중...');
        }else if(whc06NeedsFreshScan){
          scaleConnectWhc06.textContent = siteT('abrahang.scaleReconnectWhc06', lang() === 'en' ? 'Rescan WH-C06' : 'WH-C06 새로 스캔');
        }else if(whc06Connected){
          scaleConnectWhc06.textContent = siteT('abrahang.scaleReconnectWhc06', lang() === 'en' ? 'Rescan WH-C06' : 'WH-C06 새로 스캔');
        }else{
          scaleConnectWhc06.textContent = siteT('abrahang.scaleConnectWhc06', lang() === 'en' ? 'WH-C06 / IF_B7 (beta)' : 'WH-C06 / IF_B7 연결(beta)');
        }
      }
      renderWhc06Support();
      if(scaleReading) scaleReading.textContent = hasReading ? formatKg(scaleState.readingKg) : emptyScaleText();
      if(scaleFingerLoad){
        if(isCraneScale) scaleFingerLoad.textContent = hasReading ? formatKg(scaleState.readingKg) : emptyScaleText();
        else if(hasReading && hasBodyWeight) scaleFingerLoad.textContent = formatKg(Math.max(0, bodyKg - scaleState.readingKg));
        else scaleFingerLoad.textContent = hasReading ? siteT('abrahang.scaleNeedBody', lang() === 'en' ? 'Enter body weight' : '체중 입력 필요') : emptyScaleText();
      }
      if(scaleTargetReading){
        scaleTargetReading.textContent = scaleState.peakLoadKg == null ? emptyScaleText() : formatKg(scaleState.peakLoadKg);
      }
    }

    async function connectScale(){
      if(!scaleConnect) return;
      if(!hasBluetoothScaleSupport()){
        setScaleStatus('abrahang.scaleStatusUnsupported', lang() === 'en' ? 'Web Bluetooth is not supported in this browser.' : '이 브라우저는 Web Bluetooth를 지원하지 않습니다.', 'error');
        return;
      }
      scaleState.connecting = true;
      scaleState.connectingType = 'standard';
      setScaleStatus('abrahang.scaleStatusSearching', lang() === 'en' ? 'Searching for a scale...' : '저울 검색 중...', 'waiting');
      try{
        await disconnectCurrentScaleAsync();
        scaleState.readingKg = null;
        resetScalePeakLoad();
        var device = await navigator.bluetooth.requestDevice({
          filters: [{ services: [WEIGHT_SCALE_SERVICE] }]
        });
        scaleState.device = device;
        scaleState.connectionType = 'standard';
        scaleState.disconnectHandler = handleScaleDisconnected;
        device.addEventListener('gattserverdisconnected', scaleState.disconnectHandler);
        setScaleStatus('abrahang.scaleStatusConnecting', lang() === 'en' ? 'Connecting...' : '연결 중...', 'waiting');
        var server = await device.gatt.connect();
        var service = await server.getPrimaryService(WEIGHT_SCALE_SERVICE);
        var characteristic = await service.getCharacteristic(WEIGHT_MEASUREMENT_CHARACTERISTIC);
        scaleState.characteristic = characteristic;
        characteristic.addEventListener('characteristicvaluechanged', handleScaleMeasurement);
        await characteristic.startNotifications();
        setScaleStatus('abrahang.scaleStatusConnected', lang() === 'en' ? 'Connected. Waiting for weight.' : '연결됨. 저울값 대기 중', 'waiting');
        if(characteristic.properties && characteristic.properties.read){
          try{
            handleScaleValue(await characteristic.readValue());
          }catch(e){ /* Most standard scales only indicate readings. */ }
        }
      }catch(e){
        await cleanupScaleDevice();
        scaleState.device = null;
        scaleState.connectionType = null;
        setScaleStatus('abrahang.scaleStatusError', lang() === 'en' ? 'Scale connection failed.' : '저울 연결에 실패했습니다.', 'error');
      }finally{
        scaleState.connecting = false;
        scaleState.connectingType = null;
        renderScale();
      }
    }

    async function requestWhc06Device(){
      var options = {
        filters: [
          { manufacturerData: [{ companyIdentifier: WHC06_MANUFACTURER_ID }] },
          { namePrefix: WHC06_NAME_PREFIX }
        ],
        optionalManufacturerData: [WHC06_MANUFACTURER_ID]
      };
      try{
        return await navigator.bluetooth.requestDevice(options);
      }catch(e){
        if(e && e.name === 'TypeError'){
          return await navigator.bluetooth.requestDevice({
            filters: [{ namePrefix: WHC06_NAME_PREFIX }],
            optionalManufacturerData: [WHC06_MANUFACTURER_ID]
          });
        }
        throw e;
      }
    }

    async function connectWhc06Scale(){
      if(!scaleConnectWhc06) return;
      if(!hasBluetoothScaleSupport()){
        setScaleStatus('abrahang.scaleStatusUnsupported', lang() === 'en' ? 'Web Bluetooth is not supported in this browser.' : '이 브라우저는 Web Bluetooth를 지원하지 않습니다.', 'error');
        return;
      }
      var whc06Support = renderWhc06Support();
      if(!whc06Support.ok){
        setScaleStatus('abrahang.scaleStatusWhc06Unsupported', lang() === 'en' ? 'WH-C06 advertisement scanning is unavailable.' : 'WH-C06 광고 수신 미지원', 'error');
        return;
      }
      setScaleDisplayMode('crane');
      scaleState.connecting = true;
      scaleState.connectingType = 'whc06';
      setScaleStatus('abrahang.scaleStatusWhc06Searching', lang() === 'en' ? 'Searching for WH-C06 / IF_B7...' : 'WH-C06 / IF_B7 검색 중...', 'waiting');
      try{
        var previousWhc06Device = scaleState.connectionType === 'whc06' ? scaleState.device : null;
        await disconnectCurrentScaleAsync({ skipWhc06Unwatch: true });
        scaleState.watchStale = false;
        var device = await requestWhc06Device();
        if(previousWhc06Device && previousWhc06Device !== device){
          await stopWhc06AdvertisementWatch(previousWhc06Device, WHC06_UNWATCH_TIMEOUT_MS);
          await waitMs(WHC06_RESTART_GAP_MS);
        }
        await startWhc06DeviceWatch(device, {
          clearReading: true,
          forceRestart: true,
          firstPacketTimeout: WHC06_MANUAL_FIRST_PACKET_MS,
          firstPacketStatusKey: 'abrahang.scaleStatusWhc06ManualNoPacket',
          firstPacketStatusFallback: lang() === 'en'
            ? 'WH-C06 was selected again, but no new packets arrived. Turn the scale off and on, then rescan.'
            : 'WH-C06를 다시 선택했지만 새 패킷이 들어오지 않습니다. 저울 전원을 껐다 켠 뒤 새로 스캔하세요.',
          statusKey: 'abrahang.scaleStatusWhc06ManualRestart',
          statusFallback: lang() === 'en' ? 'WH-C06 selected. Restarting advertisement watch.' : 'WH-C06 선택됨. 광고 감시를 새로 시작 중',
          statusTone: 'waiting'
        });
      }catch(e){
        await cleanupScaleDevice({ skipWhc06Unwatch: true });
        scaleState.device = null;
        scaleState.connectionType = null;
        if(e && e.message && e.message.indexOf('watchAdvertisements') !== -1){
          setScaleStatus(
            'abrahang.scaleStatusWhc06Unsupported',
            lang() === 'en'
              ? 'WH-C06 advertisement scanning is unavailable.'
              : 'WH-C06 광고 수신 미지원',
            'error'
          );
        }else{
          setScaleStatus('abrahang.scaleStatusError', lang() === 'en' ? 'Scale connection failed.' : '저울 연결에 실패했습니다.', 'error');
        }
      }finally{
        scaleState.connecting = false;
        scaleState.connectingType = null;
        renderScale();
      }
    }

    function makeHistoryId(){
      return 'ab-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
    }

    function normalizeNumber(value){
      if(value == null || value === '') return null;
      var number = Number(String(value).replace(',', '.'));
      return isFinite(number) ? number : null;
    }

    function readTrainingHistory(){
      var raw = '[]';
      try { raw = localStorage.getItem(HISTORY_KEY) || '[]'; } catch(e){ raw = '[]'; }
      var parsed = [];
      try { parsed = JSON.parse(raw); } catch(e){ parsed = []; }
      if(!Array.isArray(parsed)) parsed = [];
      var items = [];
      for(var i = 0; i < parsed.length; i++){
        var item = parsed[i] || {};
        var completedAt = Number(item.completedAt || 0);
        if(!isFinite(completedAt) || completedAt <= 0) continue;
        var mode = item.mode === 'video' ? 'video' : 'paper';
        var id = String(item.id || '');
        if(!/^[A-Za-z0-9_-]+$/.test(id)) id = makeHistoryId();
        items.push({
          id: id,
          mode: mode,
          completedAt: completedAt,
          intensityPct: normalizeNumber(item.intensityPct),
          targetLoadKg: normalizeNumber(item.targetLoadKg),
          maxLoadKg: normalizeNumber(item.maxLoadKg),
          legacy: !!item.legacy
        });
      }
      items.sort(function(a, b){ return b.completedAt - a.completedAt; });
      return items.slice(0, HISTORY_LIMIT);
    }

    function saveTrainingHistory(items){
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, HISTORY_LIMIT))); } catch(e){ /* ignore */ }
    }

    function migrateLegacyTrainingHistory(){
      try{
        if(localStorage.getItem(HISTORY_MIGRATED_KEY) === '1') return;
        var history = readTrainingHistory();
        var last = Number(localStorage.getItem(STORAGE_KEY) || 0);
        if(history.length === 0 && isFinite(last) && last > 0){
          history.push({
            id: 'legacy-' + String(Math.round(last)),
            mode: 'paper',
            completedAt: last,
            intensityPct: null,
            targetLoadKg: null,
            maxLoadKg: null,
            legacy: true
          });
          saveTrainingHistory(history);
        }
        localStorage.setItem(HISTORY_MIGRATED_KEY, '1');
      }catch(e){ /* ignore migration errors */ }
    }

    function protocolHistoryLabel(mode, legacy){
      var label = mode === 'video'
        ? siteT('abrahang.historyModeVideo', lang() === 'en' ? 'Emil' : 'Emil')
        : siteT('abrahang.historyModePaper', lang() === 'en' ? 'Abrahangs' : 'Abrahangs');
      if(legacy) label += lang() === 'en' ? ' · legacy log' : ' · 기존 로그';
      return label;
    }

    function formatDateTime(ms){
      try{
        return new Date(ms).toLocaleString(lang() === 'en' ? 'en-US' : 'ko-KR', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        });
      }catch(e){ return '-'; }
    }

    function pad2(value){
      return value < 10 ? '0' + value : String(value);
    }

    function toDateTimeLocalValue(ms){
      var d = new Date(ms);
      return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()) + 'T' + pad2(d.getHours()) + ':' + pad2(d.getMinutes());
    }

    function fromDateTimeLocalValue(value){
      var time = Date.parse(value);
      return isFinite(time) ? time : Date.now();
    }

    function formatHistoryKg(value, missingText){
      if(value == null || !isFinite(value)) return missingText || siteT('abrahang.historyMissing', lang() === 'en' ? 'Missing' : '측정누락');
      return formatKg(value);
    }

    function formatHistoryPercent(value, missingText){
      if(value == null || !isFinite(value)) return missingText || siteT('abrahang.historyMissing', lang() === 'en' ? 'Missing' : '측정누락');
      var rounded = Math.round(value * 10) / 10;
      return rounded.toFixed(rounded % 1 === 0 ? 0 : 1) + '%';
    }

    function formatTargetSetting(item, missingText){
      var parts = [];
      if(item && item.intensityPct != null && isFinite(item.intensityPct)) parts.push(formatHistoryPercent(item.intensityPct, missingText));
      if(item && item.targetLoadKg != null && isFinite(item.targetLoadKg)) parts.push(formatHistoryKg(item.targetLoadKg, missingText));
      return parts.length ? parts.join(' · ') : missingText;
    }

    function achievementPct(item){
      if(!item || !(item.targetLoadKg > 0) || !(item.maxLoadKg >= 0)) return null;
      return item.maxLoadKg / item.targetLoadKg * 100;
    }

    function makeTrainingHistoryRecord(completedAt){
      var bodyKg = parseBodyWeight();
      var targetKg = bodyKg > 0 ? targetLoadKg(bodyKg) : null;
      var maxLoad = state.loadSampleCount > 0 ? state.maxMeasuredLoadKg : null;
      return {
        id: makeHistoryId(),
        mode: state.mode === 'video' ? 'video' : 'paper',
        completedAt: completedAt,
        intensityPct: intensity ? Number(intensity.value) || null : null,
        targetLoadKg: targetKg,
        maxLoadKg: maxLoad,
        legacy: false
      };
    }

    function addTrainingHistoryRecord(record){
      var history = readTrainingHistory();
      history.unshift(record);
      saveTrainingHistory(history);
      renderHistory();
    }

    function logTrainingHistory(completedAt){
      if(state.historyLogged) return;
      state.historyLogged = true;
      addTrainingHistoryRecord(makeTrainingHistoryRecord(completedAt));
    }

    function renderHistory(){
      if(!historyList) return;
      var history = readTrainingHistory();
      if(history.length === 0){
        historyList.innerHTML = '<div class="abrahang-history-empty">' + siteT('abrahang.historyEmpty', lang() === 'en' ? 'No training history yet.' : '훈련 히스토리가 없습니다.') + '</div>';
        return;
      }
      var missingSetting = siteT('abrahang.historySettingMissing', lang() === 'en' ? 'Missing setting' : '설정누락');
      var missingMeasurement = siteT('abrahang.historyMissing', lang() === 'en' ? 'Missing measurement' : '측정누락');
      var html = '';
      for(var i = 0; i < history.length; i++){
        var item = history[i];
        var pct = achievementPct(item);
        var title = protocolHistoryLabel(item.mode, item.legacy);
        if(editingHistoryId === item.id){
          html += '<article class="abrahang-history-item is-editing" data-history-id="' + item.id + '">';
          html += '<div class="abrahang-history-edit-grid">';
          html += '<label>' + siteT('abrahang.historyProtocol', lang() === 'en' ? 'Protocol' : '프로토콜') + '<select data-history-field="mode"><option value="paper"' + (item.mode === 'paper' ? ' selected' : '') + '>Abrahangs</option><option value="video"' + (item.mode === 'video' ? ' selected' : '') + '>Emil</option></select></label>';
          html += '<label>' + siteT('abrahang.historyDate', lang() === 'en' ? 'Date and time' : '훈련 날짜와 시간') + '<input type="datetime-local" data-history-field="completedAt" value="' + toDateTimeLocalValue(item.completedAt) + '"></label>';
          html += '<label>' + siteT('abrahang.historyIntensity', lang() === 'en' ? 'Target intensity' : '목표 강도') + '<input type="number" min="30" max="80" step="1" data-history-field="intensityPct" value="' + (item.intensityPct == null ? '' : item.intensityPct) + '"></label>';
          html += '<label>' + siteT('abrahang.historyTargetLoad', lang() === 'en' ? 'Target load' : '목표 하중') + '<input type="number" min="0" step="0.1" data-history-field="targetLoadKg" value="' + (item.targetLoadKg == null ? '' : item.targetLoadKg) + '"></label>';
          html += '<label>' + siteT('abrahang.historyMaxLoad', lang() === 'en' ? 'Max measured load' : '최대 측정 하중') + '<input type="number" min="0" step="0.1" data-history-field="maxLoadKg" value="' + (item.maxLoadKg == null ? '' : item.maxLoadKg) + '"></label>';
          html += '</div>';
          html += '<div class="abrahang-history-actions"><button type="button" class="abrahang-btn ghost" data-history-action="save">' + siteT('abrahang.historySave', lang() === 'en' ? 'Save' : '저장') + '</button><button type="button" class="abrahang-btn ghost" data-history-action="cancel">' + siteT('abrahang.historyCancel', lang() === 'en' ? 'Cancel' : '취소') + '</button></div>';
          html += '</article>';
          continue;
        }
        html += '<article class="abrahang-history-item" data-history-id="' + item.id + '">';
        html += '<details class="abrahang-history-details">';
        html += '<summary class="abrahang-history-summary"><span class="abrahang-history-item-head"><strong>' + title + '</strong><span>' + formatDateTime(item.completedAt) + '</span></span></summary>';
        html += '<div class="abrahang-history-detail-body">';
        html += '<dl class="abrahang-history-stats">';
        html += '<div><dt>' + siteT('abrahang.historyTargetSetting', lang() === 'en' ? 'Target setting' : '목표 설정') + '</dt><dd>' + formatTargetSetting(item, missingSetting) + '</dd></div>';
        html += '<div><dt>' + siteT('abrahang.historyMaxLoad', lang() === 'en' ? 'Max measured load' : '최대 측정 하중') + '</dt><dd>' + formatHistoryKg(item.maxLoadKg, missingMeasurement) + '</dd></div>';
        html += '<div><dt>' + siteT('abrahang.historyAchievement', lang() === 'en' ? 'Load achievement' : '하중달성률') + '</dt><dd>' + formatHistoryPercent(pct, missingMeasurement) + '</dd></div>';
        html += '</dl>';
        html += '<div class="abrahang-history-actions"><button type="button" class="abrahang-btn ghost" data-history-action="edit">' + siteT('abrahang.historyEdit', lang() === 'en' ? 'Edit' : '편집') + '</button><button type="button" class="abrahang-btn ghost danger" data-history-action="delete">' + siteT('abrahang.historyDelete', lang() === 'en' ? 'Delete' : '삭제') + '</button></div>';
        html += '</div></details>';
        html += '</article>';
      }
      historyList.innerHTML = html;
    }

    function historyItemFromForm(container, original){
      function field(name){ return container.querySelector('[data-history-field="' + name + '"]'); }
      var maxLoad = normalizeNumber(field('maxLoadKg') && field('maxLoadKg').value);
      return {
        id: original.id,
        mode: field('mode') && field('mode').value === 'video' ? 'video' : 'paper',
        completedAt: fromDateTimeLocalValue(field('completedAt') && field('completedAt').value),
        intensityPct: normalizeNumber(field('intensityPct') && field('intensityPct').value),
        targetLoadKg: normalizeNumber(field('targetLoadKg') && field('targetLoadKg').value),
        maxLoadKg: maxLoad,
        legacy: !!original.legacy
      };
    }

    function handleHistoryClick(event){
      var actionEl = event.target && event.target.closest ? event.target.closest('[data-history-action]') : null;
      if(!actionEl) return;
      var itemEl = actionEl.closest('[data-history-id]');
      var action = actionEl.getAttribute('data-history-action');
      var id = itemEl && itemEl.getAttribute('data-history-id');
      var history = readTrainingHistory();
      var index = history.findIndex(function(item){ return item.id === id; });
      if(action === 'cancel'){
        editingHistoryId = null;
        renderHistory();
        return;
      }
      if(index < 0) return;
      if(action === 'edit'){
        editingHistoryId = id;
        renderHistory();
        return;
      }
      if(action === 'delete'){
        if(window.confirm(siteT('abrahang.historyDeleteConfirm', lang() === 'en' ? 'Delete this training history item?' : '이 훈련 히스토리를 삭제할까요?'))){
          history.splice(index, 1);
          saveTrainingHistory(history);
          if(editingHistoryId === id) editingHistoryId = null;
          renderHistory();
        }
        return;
      }
      if(action === 'save'){
        history[index] = historyItemFromForm(itemEl, history[index]);
        saveTrainingHistory(history);
        editingHistoryId = null;
        renderHistory();
      }
    }

    function clearTrainingHistory(){
      if(!window.confirm(siteT('abrahang.historyClearConfirm', lang() === 'en' ? 'Delete all training history?' : '훈련 히스토리를 모두 삭제할까요?'))) return;
      saveTrainingHistory([]);
      try { localStorage.setItem(HISTORY_MIGRATED_KEY, '1'); } catch(e){ /* ignore */ }
      editingHistoryId = null;
      renderHistory();
    }

    function saveBodyWeight(){
      if(!bodyWeight) return;
      var kg = parseBodyWeight();
      try{
        if(kg > 0) localStorage.setItem(BODY_WEIGHT_KEY, String(kg));
        else localStorage.removeItem(BODY_WEIGHT_KEY);
      }catch(e){ /* ignore */ }
    }

    function loadBodyWeight(){
      if(!bodyWeight) return;
      try{
        var stored = Number(localStorage.getItem(BODY_WEIGHT_KEY) || 0);
        if(isFinite(stored) && stored > 0) bodyWeight.value = String(stored);
      }catch(e){ /* ignore */ }
    }

    function saveOneHandMode(){
      if(!oneHand) return;
      try { localStorage.setItem(ONE_HAND_KEY, oneHand.checked ? '1' : '0'); } catch(e){ /* ignore */ }
    }

    function loadOneHandMode(){
      if(!oneHand) return;
      try { oneHand.checked = localStorage.getItem(ONE_HAND_KEY) === '1'; } catch(e){ /* ignore */ }
    }

    function stepText(step){
      return tt(step.titleKey);
    }

    function stepCue(step){
      return tt(step.cueKey);
    }

    function getCurrentStep(){
      return state.protocol.steps[state.stepIndex] || null;
    }

    function getNextStep(){
      return state.protocol.steps[state.stepIndex + 1] || null;
    }

    function getHighlightedStepIndex(){
      if(state.phase === 'prestart') return 0;
      if(state.phase === 'hang') return state.stepIndex;
      if(state.phase === 'rest') return getNextStep() ? state.stepIndex + 1 : -1;
      return -1;
    }

    function formatStepPreview(index, step){
      if(!step) return '';
      var prefix = String(index + 1) + ' / ' + state.protocol.steps.length;
      var edge = step.edge ? ' · ' + step.edge : '';
      return prefix + ' · ' + stepText(step) + edge + ' - ' + stepCue(step);
    }

    function remainingTotalMs(){
      if(state.phase === 'done') return 0;
      if(state.phase === 'ready') return protocolTotalMs(state.protocol);
      if(state.phase === 'prestart') return state.remainingMs + protocolTotalMs(state.protocol);
      var remaining = state.remainingMs;
      if(state.phase === 'hang') remaining += state.protocol.restMs;
      var remainingSteps = Math.max(0, state.protocol.steps.length - state.stepIndex - 1);
      return remaining + remainingSteps * (state.protocol.hangMs + state.protocol.restMs);
    }

    function setMode(mode){
      state.mode = mode === 'video' ? 'video' : 'paper';
      state.protocol = buildProtocol(state.mode);
      setDefaultIntensityForMode(state.mode);
      resetState(false);
      render();
    }

    function resetState(shouldRender){
      stopLoop();
      state.running = false;
      state.phase = 'ready';
      state.stepIndex = 0;
      state.remainingMs = state.protocol.hangMs;
      state.elapsedMs = 0;
      state.completedLogged = false;
      state.historyLogged = false;
      resetSessionMeasurements();
      resetScalePeakLoad();
      lastCountdownSecond = -1;
      if(window.appWakeLock) window.appWakeLock.release('abrahang');
      if(shouldRender !== false) render();
    }

    function ensureAudio(){
      if(audioCtx) return;
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if(!Ctx) return;
      try{
        audioCtx = new Ctx();
      }catch(e){
        audioCtx = null;
      }
    }

    function beep(kind){
      if(!sound || !sound.checked) return;
      ensureAudio();
      if(!audioCtx) return;
      try{
        if(audioCtx.state === 'suspended' && audioCtx.resume) audioCtx.resume();
        var osc = audioCtx.createOscillator();
        var gain = audioCtx.createGain();
        var now = audioCtx.currentTime;
        var freq = kind === 'done' ? 880 : (kind === 'countdown' ? 560 : 740);
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now);
        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.exponentialRampToValueAtTime(BEEP_GAIN, now + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + (kind === 'countdown' ? 0.12 : 0.24));
        osc.connect(gain).connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + (kind === 'countdown' ? 0.14 : 0.26));
      }catch(e){ /* ignore audio errors */ }
    }

    function start(){
      if(state.phase === 'done') resetState(false);
      if(state.phase === 'ready'){
        resetSessionMeasurements();
        resetScalePeakLoad();
        state.historyLogged = false;
        state.phase = 'prestart';
        state.stepIndex = 0;
        state.remainingMs = PRECOUNT_MS;
        lastCountdownSecond = -1;
      }
      state.running = true;
      lastTick = performance.now();
      if(window.appWakeLock) window.appWakeLock.request('abrahang');
      tick(lastTick);
      render();
    }

    function pause(){
      state.running = false;
      stopLoop();
      if(window.appWakeLock) window.appWakeLock.release('abrahang');
      render();
    }

    function stopLoop(){
      if(rafId){
        cancelAnimationFrame(rafId);
        rafId = 0;
      }
    }

    function finish(){
      state.phase = 'done';
      state.running = false;
      state.remainingMs = 0;
      stopLoop();
      if(window.appWakeLock) window.appWakeLock.release('abrahang');
      beep('done');
      var completedAt = Date.now();
      logTrainingHistory(completedAt);
      if(autoLog && autoLog.checked && !state.completedLogged){
        state.completedLogged = true;
        try { localStorage.setItem(STORAGE_KEY, String(completedAt)); } catch(e){ /* ignore */ }
      }
      render();
    }

    function advancePhase(){
      lastCountdownSecond = -1;
      if(state.phase === 'prestart'){
        state.phase = 'hang';
        state.remainingMs = state.protocol.hangMs;
        nudgeWhc06WatchForLoad();
        beep('phase');
        renderSteps();
        return;
      }
      if(state.phase === 'hang'){
        state.phase = 'rest';
        state.remainingMs = state.protocol.restMs;
        beep('phase');
        renderSteps();
        return;
      }
      if(state.phase === 'rest'){
        state.stepIndex += 1;
        if(state.stepIndex >= state.protocol.steps.length){
          finish();
          return;
        }
        state.phase = 'hang';
        state.remainingMs = state.protocol.hangMs;
        nudgeWhc06WatchForLoad();
        beep('phase');
        renderSteps();
      }
    }

    function tick(ts){
      if(!state.running) return;
      var delta = Math.max(0, ts - lastTick);
      lastTick = ts;
      state.remainingMs -= delta;
      state.elapsedMs += delta;
      while(state.running && state.remainingMs <= 0){
        var overshoot = state.remainingMs;
        advancePhase();
        if(state.running) state.remainingMs += overshoot;
      }
      if(state.running){
        monitorWhc06DuringHang();
        var sec = Math.ceil(state.remainingMs / 1000);
        if(sec > 0 && sec <= 3 && sec !== lastCountdownSecond){
          lastCountdownSecond = sec;
          beep('countdown');
        }
        renderLive();
        rafId = requestAnimationFrame(tick);
      }
    }

    function renderSteps(){
      stepsEl.innerHTML = '';
      var highlightedIndex = getHighlightedStepIndex();
      for(var i = 0; i < state.protocol.steps.length; i++){
        var step = state.protocol.steps[i];
        var li = document.createElement('li');
        li.className = 'abrahang-step';
        if(i === highlightedIndex){
          li.className += ' is-current';
          if(state.phase === 'hang' && state.running) li.className += ' is-loading';
          if(state.phase === 'rest' || state.phase === 'prestart') li.className += ' is-preview';
          li.setAttribute('aria-current', 'step');
        }
        if(state.phase === 'done' || i < state.stepIndex || (state.phase === 'rest' && i === state.stepIndex)) li.className += ' is-done';
        var num = document.createElement('span');
        num.className = 'abrahang-step-num';
        num.textContent = String(i + 1);
        var body = document.createElement('div');
        var title = document.createElement('strong');
        title.textContent = stepText(step);
        var cue = document.createElement('span');
        cue.textContent = step.edge ? step.edge + ' - ' + stepCue(step) : stepCue(step);
        body.appendChild(title);
        body.appendChild(cue);
        li.appendChild(num);
        li.appendChild(body);
        stepsEl.appendChild(li);
      }
    }

    function renderLive(){
      var total = protocolTotalMs(state.protocol) + (state.phase === 'prestart' ? PRECOUNT_MS : 0);
      var remaining = remainingTotalMs();
      var elapsed = Math.max(0, total - remaining);
      var progress = total > 0 ? Math.max(0, Math.min(1, elapsed / total)) : 0;
      var phaseProgress = state.phase === 'ready' || state.phase === 'done' ? (state.phase === 'done' ? 1 : 0) :
        Math.max(0, Math.min(1, 1 - (state.remainingMs / phaseDuration())));
      var current = getCurrentStep();
      var next = getNextStep();

      if(dial) dial.setAttribute('data-ab-phase', state.phase);
      if(ringFill) ringFill.style.setProperty('--ab-ring-deg', Math.round(phaseProgress * 360) + 'deg');
      if(totalBar) totalBar.style.width = Math.round(progress * 1000) / 10 + '%';
      if(totalRemaining) totalRemaining.textContent = formatMinuteSecond(remaining);

      if(state.phase === 'done'){
        phaseEl.textContent = tt('done');
        timeEl.textContent = '0';
        countEl.textContent = state.protocol.steps.length + ' / ' + state.protocol.steps.length;
        moveTitle.textContent = tt('doneTitle');
        moveCue.textContent = tt('doneCue');
      }else if(state.phase === 'ready'){
        phaseEl.textContent = tt('ready');
        timeEl.textContent = formatSeconds(state.protocol.hangMs);
        countEl.textContent = '0 / ' + state.protocol.steps.length;
        moveTitle.textContent = tt('readyTitle');
        moveCue.textContent = tt('readyCue');
      }else if(state.phase === 'prestart'){
        phaseEl.textContent = tt('prestart');
        timeEl.textContent = formatSeconds(state.remainingMs);
        countEl.textContent = '0 / ' + state.protocol.steps.length;
        moveTitle.textContent = tt('prestartTitle');
        moveCue.textContent = tt('prestartCue');
      }else{
        phaseEl.textContent = state.phase === 'hang' ? tt('hang') : tt('rest');
        timeEl.textContent = formatSeconds(state.remainingMs);
        countEl.textContent = (state.stepIndex + 1) + ' / ' + state.protocol.steps.length;
        if(current){
          if(state.phase === 'hang'){
            moveTitle.textContent = stepText(current);
            moveCue.textContent = stepCue(current);
          }else if(next){
            moveTitle.textContent = tt('nextPreviewTitle');
            moveCue.textContent = formatStepPreview(state.stepIndex + 1, next);
          }else{
            moveTitle.textContent = tt('finalRestTitle');
            moveCue.textContent = tt('finalRestCue');
          }
        }
      }
    }

    function renderNextSession(){
      var last = 0;
      try { last = Number(localStorage.getItem(STORAGE_KEY) || 0); } catch(e){ last = 0; }
      if(!last){
        nextEl.textContent = tt('nextEmpty');
        return;
      }
      var next = last + RECOVERY_MS;
      if(Date.now() >= next){
        nextEl.textContent = tt('nextReady');
        nextEl.classList.add('is-ready');
        return;
      }
      nextEl.classList.remove('is-ready');
      var formatter = new Intl.DateTimeFormat(lang() === 'en' ? 'en-US' : 'ko-KR', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      nextEl.textContent = tt('nextAt').replace('{time}', formatter.format(new Date(next)));
    }

    function render(){
      for(var i = 0; i < modeButtons.length; i++){
        var active = modeButtons[i].getAttribute('data-ab-mode') === state.mode;
        modeButtons[i].classList.toggle('is-active', active);
        modeButtons[i].setAttribute('aria-pressed', active ? 'true' : 'false');
      }
      if(metricLoad) metricLoad.textContent = formatShort(state.protocol.hangMs / 1000);
      if(metricRest) metricRest.textContent = formatShort(state.protocol.restMs / 1000);
      if(metricReps) metricReps.textContent = lang() === 'en' ? state.protocol.steps.length + ' reps' : state.protocol.steps.length + '회';
      if(noteEl) noteEl.textContent = tt(state.protocol.noteKey);
      if(intensityValue && intensity) intensityValue.textContent = intensity.value + '%';
      if(loadTarget && intensity){
        var kg = parseBodyWeight();
        if(kg > 0){
          loadTarget.textContent = formatKg(targetLoadKg(kg));
        }else{
          loadTarget.textContent = siteT('abrahang.loadTargetEmpty', lang() === 'en' ? 'Enter body weight' : '체중 입력 필요');
        }
      }
      renderScale();
      if(startBtn){
        if(state.running) startBtn.textContent = siteT('abrahang.pause', tt('pause'));
        else if(state.phase === 'prestart' || state.phase === 'hang' || state.phase === 'rest') startBtn.textContent = siteT('abrahang.resume', tt('resume'));
        else startBtn.textContent = siteT('abrahang.start', tt('start'));
      }
      renderLive();
      renderSteps();
      renderNextSession();
    }

    function temporaryCue(text){
      clearTimeout(temporaryCueTimer);
      var current = getCurrentStep();
      var original = state.phase === 'hang' && current ? stepCue(current) : moveCue.textContent;
      moveCue.textContent = text;
      temporaryCueTimer = setTimeout(function(){
        moveCue.textContent = original;
        renderLive();
      }, 1600);
    }

    for(var i = 0; i < modeButtons.length; i++){
      modeButtons[i].addEventListener('click', function(){
        setMode(this.getAttribute('data-ab-mode'));
      });
    }
    for(var j = 0; j < scaleModeButtons.length; j++){
      scaleModeButtons[j].addEventListener('click', function(){
        setScaleDisplayMode(this.getAttribute('data-ab-scale-mode'));
      });
    }

    if(startBtn){
      startBtn.addEventListener('click', function(){
        ensureAudio();
        if(state.running) pause();
        else start();
      });
    }
    if(resetBtn) resetBtn.addEventListener('click', function(){ resetState(true); });
    if(scaleConnect) scaleConnect.addEventListener('click', connectScale);
    if(scaleConnectWhc06) scaleConnectWhc06.addEventListener('click', connectWhc06Scale);
    if(historyList) historyList.addEventListener('click', handleHistoryClick);
    if(historyClear) historyClear.addEventListener('click', clearTrainingHistory);
    if(intensity) intensity.addEventListener('input', render);
    if(oneHand){
      oneHand.addEventListener('change', function(){
        saveOneHandMode();
        render();
      });
      loadOneHandMode();
    }
    if(bodyWeight){
      bodyWeight.addEventListener('input', function(){
        saveBodyWeight();
        resetScalePeakLoad();
        render();
      });
      bodyWeight.addEventListener('change', function(){
        saveBodyWeight();
        resetScalePeakLoad();
        render();
      });
      loadBodyWeight();
    }

    loadScaleDisplayMode();
    setDefaultIntensityForMode(state.mode);
    migrateLegacyTrainingHistory();
    document.addEventListener('app:lang', function(){ render(); renderHistory(); });
    document.addEventListener('visibilitychange', function(){
      if(document.visibilityState === 'visible'){
        renderNextSession();
        checkWhc06AfterForeground(true);
      }else{
        noteWhc06ForegroundLoss();
      }
    });
    window.addEventListener('blur', noteWhc06ForegroundLoss);
    window.addEventListener('focus', function(){
      renderNextSession();
      checkWhc06AfterForeground(true);
    });
    window.addEventListener('pageshow', function(){
      renderNextSession();
      checkWhc06AfterForeground(true);
    });
    window.addEventListener('pagehide', noteWhc06ForegroundLoss);

    render();
    renderHistory();
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', boot);
  }else{
    boot();
  }
})();
