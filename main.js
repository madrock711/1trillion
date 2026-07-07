(function(){
      if(!window.requestAnimationFrame){
        window.requestAnimationFrame = function(cb){ return setTimeout(function(){ cb(Date.now()); }, 16); };
      }

      if(!window.appWakeLock){
        var wakeLockSentinel = null;
        var wakeLockPending = null;
        var wakeLockReleaseCheck = null;
        var wakeLockUsers = {};

        function hasWakeLockUsers(){
          for(var key in wakeLockUsers){
            if(Object.prototype.hasOwnProperty.call(wakeLockUsers, key)) return true;
          }
          return false;
        }

        function canUseWakeLock(){
          return !!(navigator.wakeLock && typeof navigator.wakeLock.request === 'function' && window.isSecureContext !== false);
        }

        function clearReleaseCheck(){
          if(wakeLockReleaseCheck){
            clearTimeout(wakeLockReleaseCheck);
            wakeLockReleaseCheck = null;
          }
        }

        function scheduleReleaseCheck(){
          clearReleaseCheck();
          wakeLockReleaseCheck = setTimeout(function(){
            wakeLockReleaseCheck = null;
            if(!hasWakeLockUsers()) releaseSentinel();
          }, 250);
        }

        function releaseSentinel(){
          if(!wakeLockSentinel) return;
          var sentinel = wakeLockSentinel;
          wakeLockSentinel = null;
          try{
            var released = sentinel.release();
            if(released && typeof released.catch === 'function') released.catch(function(){});
          }catch(e){ /* ignore */ }
        }

        function ensureWakeLock(){
          if(!hasWakeLockUsers() || document.visibilityState === 'hidden' || !canUseWakeLock()) return;
          clearReleaseCheck();
          if(wakeLockSentinel || wakeLockPending) return;
          try{
            wakeLockPending = navigator.wakeLock.request('screen')
              .then(function(sentinel){
                wakeLockSentinel = sentinel;
                wakeLockSentinel.addEventListener('release', function(){
                  wakeLockSentinel = null;
                  if(hasWakeLockUsers() && document.visibilityState !== 'hidden') ensureWakeLock();
                });
                if(!hasWakeLockUsers() || document.visibilityState === 'hidden'){
                  releaseSentinel();
                  if(!hasWakeLockUsers()) scheduleReleaseCheck();
                }
              })
              .catch(function(){})
              .finally(function(){ wakeLockPending = null; });
          }catch(e){
            wakeLockPending = null;
          }
        }

        window.appWakeLock = {
          request: function(key){
            wakeLockUsers[key || 'default'] = true;
            ensureWakeLock();
          },
          release: function(key){
            delete wakeLockUsers[key || 'default'];
            if(!hasWakeLockUsers()){
              releaseSentinel();
              scheduleReleaseCheck();
            }
          },
          isSupported: canUseWakeLock
        };

        document.addEventListener('visibilitychange', function(){
          if(document.visibilityState === 'hidden') releaseSentinel();
          else ensureWakeLock();
        }, false);
      }

      function boot(){
        try{
          var nodes = document.querySelectorAll('.br-embed');
          for(var i=0;i<nodes.length;i++){
            var root = nodes[i];
            if(root.getAttribute('data-br-initialized') === '1') continue;
            if(root.querySelector('#br-start')){ init(root); }
          }
        }catch(e){ /* ignore */ }
      }

      function init(root){
        root.setAttribute('data-br-initialized','1');
        function q(sel){ return root.querySelector(sel); }
        function t(key){
          return (window.appI18n && typeof window.appI18n.t === 'function') ? window.appI18n.t(key) : key;
        }

        var circle   = q('.br-circle');
        var ringProg = q('.br-progress');
        var phaseLbl = q('#br-phase-label');
        var timeLbl  = q('#br-time');
        var targetLbl = q('#br-target-time');
        var totalLbl = q('#br-total');
        var roundEl  = q('#br-round');
        var stepEl   = q('#br-step');
        var bubbleIn = q('.br-bubble-in');
        var bubbleEx = q('.br-bubble-ex');
        var lottoVision = q('#br-lotto-vision');
        var lottoVisionBalls = q('#br-lotto-vision-balls');

        var RED  = '#ef4444';
        var BLUE = '#3b82f6';
        var R = 52, CIRC = 2*Math.PI*R;
        var NUDGE_STEP_SEC = 0.5;
        var AUTO_GROW_MIN_SEC = 0.1;
        var AUTO_GROW_STEP_DELTA_SEC = 0.1;
        if(ringProg){ ringProg.style.strokeDasharray=String(CIRC); ringProg.style.strokeDashoffset=String(CIRC); }

        var syncOn = true;
        var autoGrowOn = false;
        var autoGrowStepSec = AUTO_GROW_MIN_SEC;
        var phase = 'INHALE';
        var running = false;
        var round = 1;
        var phaseTargetMs = 4000;
        var phaseElapsedMs = 0;
        var lastTickTs = 0;
        var totalElapsedMs = 0; // 총 시간

        // Synth audio
        var TONE_GAIN = 0.22;
        var TONE_ATTACK_SEC = 0.16;
        var TONE_RELEASE_SEC = 0.09;
        var TONE_DISCONNECT_PAD_SEC = 0.08;
        var TONE_PITCH_SWEEP_SEC = 1.4;
        var INHALE_PITCH_START_RATIO = 0.6875;
        var EXHALE_PITCH_START_RATIO = 1.7778;
        var volumeSlider = root.querySelector('#br-volume');
        var chakraFrequencyLabel = q('#br-chakra-frequency');
        var chakraButtons = root.querySelectorAll('.br-chakra-node');
        var selectedChakra = 'root';
        var audioUnlocked = false;
        var audioCtx = null;
        var masterGainNode = null;
        var fallbackOscillator = null;
        var fallbackOscillatorGain = null;

        function getBreathVolume(){
          var v = volumeSlider ? Number(volumeSlider.value) : 0.5;
          if(isNaN(v)) v = 0.5;
          return Math.max(0, Math.min(1, v));
        }

        function setGainValue(gainParam, value){
          if(!gainParam) return;
          try{
            if(audioCtx && typeof gainParam.setTargetAtTime === 'function'){
              var now = audioCtx.currentTime;
              if(typeof gainParam.cancelAndHoldAtTime === 'function') gainParam.cancelAndHoldAtTime(now);
              else if(typeof gainParam.cancelScheduledValues === 'function') gainParam.cancelScheduledValues(now);
              gainParam.setTargetAtTime(value, now, 0.03);
            }else if(audioCtx && typeof gainParam.setValueAtTime === 'function'){
              gainParam.setValueAtTime(value, audioCtx.currentTime);
            }else{
              gainParam.value = value;
            }
          }catch(e){ /* ignore */ }
        }

        function updateVolume() {
          if(masterGainNode){
            setGainValue(masterGainNode.gain, getBreathVolume());
          }
        }

        if (volumeSlider) {
          volumeSlider.addEventListener('input', updateVolume);
          volumeSlider.addEventListener('change', updateVolume);
          updateVolume();
        }

        function getSelectedChakraButton(){
          return root.querySelector('.br-chakra-node[data-chakra="' + selectedChakra + '"]') ||
            root.querySelector('.br-chakra-node[aria-pressed="true"]') ||
            root.querySelector('.br-chakra-node');
        }

        function getChakraFrequency(){
          var btn = getSelectedChakraButton();
          var hz = btn ? Number(btn.getAttribute('data-frequency')) : 396;
          if(!isFinite(hz) || hz <= 0) hz = 396;
          return hz;
        }

        function getBreathFrequency(isInhale){
          var baseHz = getChakraFrequency();
          return baseHz;
        }

        function getPitchSweepDuration(){
          var phaseSec = Math.max(0.2, phaseTargetMs / 1000);
          return Math.min(TONE_PITCH_SWEEP_SEC, Math.max(0.2, phaseSec * 0.45));
        }

        function getPitchStartFrequency(isInhale, targetFrequency){
          return isInhale ? targetFrequency * INHALE_PITCH_START_RATIO : targetFrequency * EXHALE_PITCH_START_RATIO;
        }

        function chakraButtonLabel(btn){
          if(!btn) return '';
          var key = btn.getAttribute('data-chakra-key');
          return key ? t(key) : btn.getAttribute('data-chakra') || '';
        }

        function formatChakraSelection(){
          var btn = getSelectedChakraButton();
          var baseHz = getChakraFrequency();
          return t('breath.chakraSelected')
            .replace('{chakra}', chakraButtonLabel(btn))
            .replace('{hz}', String(baseHz))
            .replace('{inhale}', String(baseHz));
        }

        function updateChakraUI(){
          var activeBtn = getSelectedChakraButton();
          for(var i=0;i<chakraButtons.length;i++){
            var btn = chakraButtons[i];
            var active = btn === activeBtn;
            var hz = Number(btn.getAttribute('data-frequency')) || 0;
            var label = chakraButtonLabel(btn);
            btn.setAttribute('aria-pressed', active ? 'true' : 'false');
            btn.setAttribute('aria-label', label + ' ' + hz + 'Hz');
            btn.title = label + ' ' + hz + 'Hz';
          }
          if(chakraFrequencyLabel) chakraFrequencyLabel.textContent = formatChakraSelection();
        }

        function setOscillatorFrequency(frequency){
          if(!fallbackOscillator || !fallbackOscillator.frequency || !audioCtx) return;
          try{
            var now = audioCtx.currentTime;
            var param = fallbackOscillator.frequency;
            if(typeof param.cancelAndHoldAtTime === 'function') param.cancelAndHoldAtTime(now);
            else if(typeof param.cancelScheduledValues === 'function') param.cancelScheduledValues(now);
            if(typeof param.setTargetAtTime === 'function'){
              param.setTargetAtTime(frequency, now, 0.035);
            }else if(typeof param.linearRampToValueAtTime === 'function'){
              param.setValueAtTime(param.value || frequency, now);
              param.linearRampToValueAtTime(frequency, now + 0.08);
            }else{
              param.value = frequency;
            }
          }catch(e){
            try{ fallbackOscillator.frequency.value = frequency; }catch(ignore){ /* ignore */ }
          }
        }

        function updateActiveToneFrequency(){
          if(running && fallbackOscillator){
            setOscillatorFrequency(getBreathFrequency(phase === 'INHALE'));
          }
        }

        function selectChakra(btn){
          if(!btn) return;
          selectedChakra = btn.getAttribute('data-chakra') || selectedChakra;
          updateChakraUI();
          updateActiveToneFrequency();
        }

        function ensureAudioContext(){
          var AC = window.AudioContext || window.webkitAudioContext;
          if(!AC) return false;
          try{
            audioCtx = audioCtx || new AC();
            masterGainNode = masterGainNode || audioCtx.createGain();
            if(!masterGainNode._connected){
              try{ masterGainNode.gain.value = getBreathVolume(); }catch(ignore){ /* ignore */ }
              masterGainNode.connect(audioCtx.destination);
              masterGainNode._connected = true;
            }
            updateVolume();
            return true;
          }catch(e){
            return false;
          }
        }

        function releaseTone(oscillator, gainNode, immediate){
          if(!oscillator && !gainNode) return;
          if(immediate || !audioCtx || !gainNode || !gainNode.gain){
            try{ if(oscillator) oscillator.stop(); }catch(e){ /* ignore */ }
            try{ if(oscillator) oscillator.disconnect(); }catch(e){ /* ignore */ }
            try{ if(gainNode) gainNode.disconnect(); }catch(e){ /* ignore */ }
            return;
          }

          var now = audioCtx.currentTime;
          try{
            var gain = gainNode.gain;
            if(typeof gain.cancelAndHoldAtTime === 'function') gain.cancelAndHoldAtTime(now);
            else if(typeof gain.cancelScheduledValues === 'function') gain.cancelScheduledValues(now);
            if(typeof gain.setTargetAtTime === 'function'){
              gain.setTargetAtTime(0.0001, now, TONE_RELEASE_SEC / 3);
            }else{
              gain.setValueAtTime(Math.max(0.0001, gain.value || 0.0001), now);
              gain.linearRampToValueAtTime(0.0001, now + TONE_RELEASE_SEC);
            }
          }catch(e){ /* ignore */ }

          try{ if(oscillator) oscillator.stop(now + TONE_RELEASE_SEC + TONE_DISCONNECT_PAD_SEC); }catch(e){ /* ignore */ }
          setTimeout(function(){
            try{ if(oscillator) oscillator.disconnect(); }catch(e){ /* ignore */ }
            try{ if(gainNode) gainNode.disconnect(); }catch(e){ /* ignore */ }
          }, Math.ceil((TONE_RELEASE_SEC + TONE_DISCONNECT_PAD_SEC + 0.04) * 1000));
        }

        function stopFallbackTone(immediate){
          var oscillator = fallbackOscillator;
          var gainNode = fallbackOscillatorGain;
          fallbackOscillator = null;
          fallbackOscillatorGain = null;
          releaseTone(oscillator, gainNode, !!immediate);
        }

        function stopBreathAudio(){
          stopFallbackTone();
        }

        function startFallbackTone(isInhale){
          if(!ensureAudioContext() || !audioCtx || !masterGainNode) return;
          try{
            if(audioCtx.state === 'suspended' && typeof audioCtx.resume === 'function'){
              audioCtx.resume();
            }
          }catch(e){ /* ignore */ }

          stopFallbackTone();
          var oscillator = audioCtx.createOscillator();
          var gainNode = audioCtx.createGain();
          var now = audioCtx.currentTime;
          fallbackOscillator = oscillator;
          fallbackOscillatorGain = gainNode;
          oscillator.type = 'sine';
          try{
            var targetFrequency = getBreathFrequency(isInhale);
            var startFrequency = getPitchStartFrequency(isInhale, targetFrequency);
            oscillator.frequency.setValueAtTime(startFrequency, now);
            oscillator.frequency.linearRampToValueAtTime(targetFrequency, now + getPitchSweepDuration());
          }catch(e){
            try{ oscillator.frequency.value = getBreathFrequency(isInhale); }catch(ignore){ /* ignore */ }
          }
          try{
            gainNode.gain.setValueAtTime(0.0001, now);
            gainNode.gain.exponentialRampToValueAtTime(TONE_GAIN, now + TONE_ATTACK_SEC);
          }catch(e){
            try{
              gainNode.gain.setValueAtTime(0, now);
              gainNode.gain.linearRampToValueAtTime(TONE_GAIN, now + TONE_ATTACK_SEC);
            }catch(ignore){
              try{ gainNode.gain.value = TONE_GAIN; }catch(ignore2){ /* ignore */ }
            }
          }
          oscillator.connect(gainNode);
          gainNode.connect(masterGainNode);
          oscillator.start();
        }

        function playPhaseAudio(){
          startFallbackTone(phase === 'INHALE');
        }

        function unlockAudioElements(){
          if(audioUnlocked) return;
          ensureAudioContext();
          if(audioCtx && typeof audioCtx.resume === 'function'){
            try{ audioCtx.resume(); }catch(e){ /* ignore */ }
          }
          updateVolume();
          audioUnlocked = true;
        }

        function getInEl(){ return q('#br-in-sec'); }
        function getExEl(){ return q('#br-ex-sec'); }

        function clampSec(v){ v=String(v).replace(',', '.'); v=Number(v)||0; return Math.max(1, v); }
        function secToMs(v){ return clampSec(v)*1000; }
        function getInhale(){ var el=getInEl(); return el? clampSec(el.value) : 4; }
        function getExhale(){ var el=getExEl(); return el? clampSec(el.value) : 4; }

        function formatSecInput(v){
          var rounded = Math.round(clampSec(v) * 10) / 10;
          return rounded.toFixed(1).replace(/\.0$/, '');
        }

        function setSecInput(el, value){
          if(el) el.value = formatSecInput(value);
        }

        function clampAutoGrowStep(v){
          v = Number(v);
          if(!isFinite(v)) v = AUTO_GROW_MIN_SEC;
          return Math.max(AUTO_GROW_MIN_SEC, Math.round(v * 10) / 10);
        }

        function formatAutoGrowStep(v){
          return clampAutoGrowStep(v).toFixed(1).replace(/\.0$/, '');
        }

        function autoGrowText(key){
          return t(key).replace('{step}', formatAutoGrowStep(autoGrowStepSec));
        }

        function fmtDec(ms){ var sec = Math.max(0, ms)/1000; return sec.toFixed(2); }
        function targetTimeText(){
          return t('breath.targetTime').replace('{seconds}', formatSecInput(phaseTargetMs / 1000));
        }
        function updateTargetTime(){
          if(targetLbl) targetLbl.textContent = targetTimeText();
        }
        function updatePhaseTimeLabels(){
          if(timeLbl){
            var remainNow = Math.max(0, phaseTargetMs - phaseElapsedMs);
            timeLbl.textContent = fmtDec(remainNow);
          }
          updateTargetTime();
        }
        function fmtTotal(ms){
          var t = Math.max(0, Math.floor(ms/1000));
          var h = Math.floor(t/3600), m = Math.floor((t%3600)/60), s = t%60;
          var out = '';
          if(h>0) out += ('0'+h).slice(-2) + ':';
          out += ('0'+m).slice(-2) + ':' + ('0'+s).slice(-2);
          return out;
        }

        function lottoBand(n){
          return String(Math.min(5, Math.floor((n - 1) / 10) + 1));
        }

        function normalizeVisionNumbers(value){
          var raw = Array.isArray(value) ? value : (value && Array.isArray(value.numbers) ? value.numbers : []);
          var seen = {};
          var nums = [];
          for(var i=0;i<raw.length;i++){
            var n = Number(raw[i]);
            if(!Number.isFinite(n) || Math.floor(n) !== n || n < 1 || n > 45 || seen[n]) continue;
            seen[n] = true;
            nums.push(n);
          }
          nums.sort(function(a,b){ return a-b; });
          return nums.length === 6 ? nums : [];
        }

        function renderLottoVision(numbers){
          if(!lottoVision || !lottoVisionBalls) return;
          var nums = normalizeVisionNumbers(numbers);
          lottoVisionBalls.textContent = '';
          if(nums.length !== 6){
            lottoVision.hidden = true;
            return;
          }
          nums.forEach(function(n){
            var ball = document.createElement('span');
            ball.className = 'br-lotto-vision-ball';
            ball.dataset.band = lottoBand(n);
            ball.textContent = String(n);
            lottoVisionBalls.appendChild(ball);
          });
          lottoVision.hidden = false;
        }

        function applySyncUI(){
          var btn=q('#br-sync'), ex=getExEl(), inn=getInEl();
          if(!btn||!ex||!inn) return;
          btn.setAttribute('aria-pressed', syncOn?'true':'false');
          btn.textContent = syncOn ? '=' : '≠' ;
          ex.disabled = !!syncOn;
          if(syncOn){ setSecInput(ex, inn.value); }
        }

        function applyAutoGrowUI(){
          var btn=q('#br-auto');
          var dec=q('#br-auto-dec');
          var inc=q('#br-auto-inc');
          var atMin = autoGrowStepSec <= AUTO_GROW_MIN_SEC + 0.0001;
          if(btn){
            btn.setAttribute('aria-pressed', autoGrowOn ? 'true' : 'false');
            btn.textContent = autoGrowText('breath.autoGrow');
            btn.title = autoGrowText('breath.autoGrowTitle');
          }
          if(dec){
            dec.disabled = atMin;
            dec.setAttribute('aria-disabled', atMin ? 'true' : 'false');
            dec.title = t('breath.autoGrowDec');
          }
          if(inc){
            inc.disabled = false;
            inc.setAttribute('aria-disabled', 'false');
            inc.title = t('breath.autoGrowInc');
          }
        }

        function growRoundDurations(){
          var inn = getInEl();
          var ex = getExEl();
          var nextInhale = getInhale() + autoGrowStepSec;
          setSecInput(inn, nextInhale);
          if(syncOn){
            setSecInput(ex, nextInhale);
          }else{
            setSecInput(ex, getExhale() + autoGrowStepSec);
          }
        }

        function adjustAutoGrowStep(delta){
          autoGrowStepSec = clampAutoGrowStep(autoGrowStepSec + (delta * AUTO_GROW_STEP_DELTA_SEC));
          applyAutoGrowUI();
        }

        function updateBubbles(ratio){
          if(!bubbleIn || !bubbleEx) return;
          if(phase==='INHALE'){
            var sIn = 0.2 + 0.8*ratio; bubbleIn.style.transform = 'scale(' + sIn + ')'; bubbleIn.style.opacity = '1';
            bubbleEx.style.transform = 'scale(0.2)'; bubbleEx.style.opacity = '0.25';
          } else {
            var sEx = 1.0 - 0.8*ratio; bubbleEx.style.transform = 'scale(' + sEx + ')'; bubbleEx.style.opacity = '1';
            bubbleIn.style.transform = 'scale(1)'; bubbleIn.style.opacity = '0.25';
          }
        }

        function setPhase(newPhase){
          phase = newPhase;
          if(circle) circle.setAttribute('data-phase', phase);
          if(phaseLbl) phaseLbl.textContent = (phase==='INHALE'? t('breath.inhale') : t('breath.exhale'));
          if(stepEl) stepEl.textContent = (phase==='INHALE'? t('breath.inhale') : t('breath.exhale'));
          if(ringProg) ringProg.style.stroke = (phase==='INHALE'? RED: BLUE);
          phaseTargetMs = secToMs(phase==='INHALE'? getInhale(): getExhale());
          phaseElapsedMs = 0; lastTickTs = Date.now();
          if(circle){ circle.className = circle.className.replace(/\bpulse\b/, ''); setTimeout(function(){ circle.className += ' pulse'; }, 0); }
          if(timeLbl) timeLbl.textContent = fmtDec(phaseTargetMs);
          updateTargetTime();
          if(ringProg) ringProg.style.strokeDashoffset = String(CIRC);
          updateBubbles(0);
          if(running) playPhaseAudio();
          else stopBreathAudio();
        }

        function nextPhase(){
          if(phase==='INHALE'){
            setPhase('EXHALE');
          }else{
            round += 1;
            if(roundEl) roundEl.textContent = String(round);
            if(autoGrowOn) growRoundDurations();
            setPhase('INHALE');
          }
        }

        function start(){ if(running) return; unlockAudioElements(); running=true; if(window.appWakeLock) window.appWakeLock.request('breath-timer'); var b=q('#br-start'); if(b) b.textContent = t('breath.pause'); lastTickTs=Date.now(); playPhaseAudio(); requestAnimationFrame(tick); }
        function pause(){ if(!running) return; running=false; if(window.appWakeLock) window.appWakeLock.release('breath-timer'); var b=q('#br-start'); if(b) b.textContent = t('breath.start'); stopBreathAudio(); }
        function reset(){ running=false; if(window.appWakeLock) window.appWakeLock.release('breath-timer'); var b=q('#br-start'); if(b) b.textContent = t('breath.start'); phaseElapsedMs=0; totalElapsedMs=0; round=1; if(roundEl) roundEl.textContent='1'; stopBreathAudio(); setPhase('INHALE'); if(totalLbl) totalLbl.textContent='00:00'; }

        function tick(ts){
          if(!running) return;
          var nowTs = (typeof ts==='number')? ts : Date.now();
          var dt = Math.max(0, nowTs - lastTickTs); lastTickTs = nowTs; phaseElapsedMs += dt; totalElapsedMs += dt;
          var remain = Math.max(0, phaseTargetMs - phaseElapsedMs);
          var ratio = Math.min(1, phaseElapsedMs/phaseTargetMs);
          if(ringProg) ringProg.style.strokeDashoffset = String((1-ratio)*CIRC);
          if(timeLbl) timeLbl.textContent = fmtDec(remain);
          if(totalLbl) totalLbl.textContent = fmtTotal(totalElapsedMs);
          updateBubbles(ratio);
          if(phaseElapsedMs >= phaseTargetMs){ nextPhase(); }
          requestAnimationFrame(tick);
        }

        // 공통 증감 로직
        function adjustValue(el, delta){
          if(!el) return;
          var next = clampSec((Number(el.value)||0) + (delta*NUDGE_STEP_SEC));
          setSecInput(el, next);
        }

        // 이벤트 위임
        document.addEventListener('click', function(e){
          var t = e.target; if(!t) return; if(!root.contains(t)) return;
          try{
            var chakraBtn = t.closest ? t.closest('.br-chakra-node') : null;
            if(chakraBtn && root.contains(chakraBtn)){ selectChakra(chakraBtn); }
            else if(t.id==='br-start'){ running? pause(): start(); }
            else if(t.id==='br-reset'){ reset(); }
            else if(t.id==='br-auto'){ autoGrowOn = !autoGrowOn; applyAutoGrowUI(); }
            else if(t.id==='br-auto-dec'){ adjustAutoGrowStep(-1); }
            else if(t.id==='br-auto-inc'){ adjustAutoGrowStep(+1); }
            else if(t.id==='br-sync'){ syncOn = !syncOn; applySyncUI(); if(phase==='EXHALE'){ phaseTargetMs = secToMs(getExhale()); } updatePhaseTimeLabels(); }
            else if(t.id==='br-in-dec'){ var inn=getInEl(); adjustValue(inn, -1); if(syncOn){ var ex=getExEl(); if(ex) ex.value=inn.value; } if(phase==='INHALE'){ phaseTargetMs = secToMs(getInhale()); }
              if(syncOn && phase==='EXHALE'){ phaseTargetMs = secToMs(getExhale()); }
              updatePhaseTimeLabels(); }
            else if(t.id==='br-in-inc'){ var inn2=getInEl(); adjustValue(inn2, +1); if(syncOn){ var ex2=getExEl(); if(ex2) ex2.value=inn2.value; } if(phase==='INHALE'){ phaseTargetMs = secToMs(getInhale()); }
              if(syncOn && phase==='EXHALE'){ phaseTargetMs = secToMs(getExhale()); }
              updatePhaseTimeLabels(); }
            else if(t.id==='br-ex-dec'){ var exn=getExEl(); adjustValue(exn, -1); if(!syncOn && phase==='EXHALE'){ phaseTargetMs = secToMs(getExhale()); }
              updatePhaseTimeLabels(); }
            else if(t.id==='br-ex-inc'){ var exn2=getExEl(); adjustValue(exn2, +1); if(!syncOn && phase==='EXHALE'){ phaseTargetMs = secToMs(getExhale()); }
              updatePhaseTimeLabels(); }
          }catch(err){ /* swallow */ }
        }, false);

        document.addEventListener('input', function(e){
          var t=e.target; if(!t) return; if(!root.contains(t)) return;
          try{
            if(t.id==='br-in-sec' || t.id==='br-ex-sec'){
              t.value = clampSec(t.value);
              if(syncOn && t.id==='br-in-sec'){ var ex=getExEl(); if(ex) ex.value = t.value; }
              if(phase==='INHALE' && t.id==='br-in-sec') phaseTargetMs = secToMs(getInhale());
              if(syncOn && phase==='EXHALE' && t.id==='br-in-sec') phaseTargetMs = secToMs(getExhale());
              if(phase==='EXHALE' && t.id==='br-ex-sec') phaseTargetMs = secToMs(getExhale());
              updatePhaseTimeLabels();
            }
          }catch(err){ /* swallow */ }
        }, false);

        function applyLanguageState(){
          var b=q('#br-start');
          if(b) b.textContent = running ? t('breath.pause') : t('breath.start');
          applyAutoGrowUI();
          updateChakraUI();
          if(phaseLbl) phaseLbl.textContent = (phase==='INHALE'? t('breath.inhale') : t('breath.exhale'));
          if(stepEl) stepEl.textContent = (phase==='INHALE'? t('breath.inhale') : t('breath.exhale'));
          updateTargetTime();
        }

        document.addEventListener('app:lang', function(){ applyLanguageState(); }, false);
        document.addEventListener('lottery:vision', function(e){
          renderLottoVision(e && e.detail ? e.detail.numbers : null);
        }, false);
        document.addEventListener('click', function(e){
          var t = e.target;
          var tab = t && t.closest ? t.closest('.tab-link[data-tab]') : null;
          if(tab && tab.getAttribute('data-tab') !== 'breathing') renderLottoVision(null);
        }, false);
        window.addEventListener('hashchange', function(){
          var active = document.querySelector('.tab-content.active');
          if(active && active.id !== 'breathing') renderLottoVision(null);
        }, false);

        applySyncUI(); applyAutoGrowUI(); updateChakraUI(); setPhase('INHALE'); if(totalLbl) totalLbl.textContent = '00:00';
        renderLottoVision(null);
        applyLanguageState();
      }

      function startWhenReady(){
        var tries = 0;
        (function check(){
          boot();
          var nodes = document.querySelectorAll('.br-embed:not([data-br-initialized])');
          if(nodes.length && tries++ < 600){ setTimeout(check, 50); }
        })();
      }

      if(document.readyState==='complete'){ startWhenReady(); }
      else {
        document.addEventListener('DOMContentLoaded', startWhenReady, false);
        window.addEventListener('load', startWhenReady, false);
        setTimeout(startWhenReady, 0);
      }

      function initSubscribeForm(){
        var form = document.querySelector('.subscribe-form');
        if(!form) return;
        var statusEl = document.querySelector('.subscribe-status');
        var submitBtn = form.querySelector('button[type="submit"]');
        var sending = false;

        function t(key){
          return (window.appI18n && typeof window.appI18n.t === 'function') ? window.appI18n.t(key) : key;
        }

        function setStatus(state, key){
          if(!statusEl) return;
          statusEl.dataset.state = state || '';
          statusEl.dataset.key = key || '';
          statusEl.textContent = key ? t(key) : '';
          if(!key){
            statusEl.classList.add('is-hidden');
          } else {
            statusEl.classList.remove('is-hidden');
          }
        }

        function updateStatusLanguage(){
          if(!statusEl) return;
          var key = statusEl.dataset.key;
          if(key){ statusEl.textContent = t(key); }
        }

        form.addEventListener('submit', function(e){
          e.preventDefault();
          if(sending) return;
          sending = true;
          if(submitBtn) submitBtn.disabled = true;
          setStatus('sending', 'subscribe.sending');

          var endpoint = form.getAttribute('action');
          var payload = new FormData(form);

          fetch(endpoint, {
            method: 'POST',
            body: payload,
            headers: { 'Accept': 'application/json' }
          }).then(function(res){
            if(res.ok){
              form.reset();
              setStatus('success', 'subscribe.success');
              return;
            }
            return res.json().catch(function(){ return null; }).then(function(){
              throw new Error('subscribe_failed');
            });
          }).catch(function(){
            setStatus('error', 'subscribe.error');
          }).finally(function(){
            sending = false;
            if(submitBtn) submitBtn.disabled = false;
          });
        }, false);

        document.addEventListener('app:lang', updateStatusLanguage, false);
      }

      function initShareButtons(){
        var buttons = document.querySelectorAll('[data-share-tab]');
        if(!buttons.length) return;
        var toast = document.getElementById('share-toast');

        function t(key){
          return (window.appI18n && typeof window.appI18n.t === 'function') ? window.appI18n.t(key) : key;
        }

        function buildUrl(tab){
          try{
            var u = new URL(window.location.origin + window.location.pathname);
            u.searchParams.set('tab', tab);
            return u.toString();
          }catch(e){
            return (window.location.origin + window.location.pathname + '?tab=' + encodeURIComponent(tab));
          }
        }

        function showToast(key){
          if(!toast) return;
          if(toast._toastTimer){ clearTimeout(toast._toastTimer); }
          toast.textContent = key ? t(key) : '';
          toast.classList.add('is-visible');
          toast._toastTimer = setTimeout(function(){
            toast.classList.remove('is-visible');
          }, 1600);
        }

        function restore(btn){
          btn.classList.remove('is-copied');
        }

        function flashState(btn, ok){
          if(btn._shareTimer){ clearTimeout(btn._shareTimer); }
          if(ok){
            btn.classList.add('is-copied');
            showToast('share.toast.copied');
          } else {
            showToast('share.toast.error');
          }
          btn._shareTimer = setTimeout(function(){ restore(btn); }, 1500);
        }

        function copyText(text, cb){
          if(navigator.clipboard && typeof navigator.clipboard.writeText === 'function'){
            navigator.clipboard.writeText(text).then(function(){ cb(true); }).catch(function(){ cb(false); });
            return;
          }
          var temp = document.createElement('textarea');
          temp.value = text;
          temp.setAttribute('readonly', '');
          temp.style.position = 'fixed';
          temp.style.left = '-9999px';
          document.body.appendChild(temp);
          temp.select();
          var ok = false;
          try{ ok = document.execCommand('copy'); }catch(e){ ok = false; }
          document.body.removeChild(temp);
          cb(ok);
        }

        buttons.forEach(function(btn){
          restore(btn);
          btn.addEventListener('click', function(){
            var tab = btn.getAttribute('data-share-tab') || 'breathing';
            var url = buildUrl(tab);
            copyText(url, function(ok){ flashState(btn, ok); });
          }, false);
        });

        document.addEventListener('app:lang', function(){
          buttons.forEach(function(btn){ restore(btn); });
        }, false);
      }

      initSubscribeForm();
      initShareButtons();
    })();
