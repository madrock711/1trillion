(function(){
      if(!window.requestAnimationFrame){
        window.requestAnimationFrame = function(cb){ return setTimeout(function(){ cb(Date.now()); }, 16); };
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
        var totalLbl = q('#br-total');
        var roundEl  = q('#br-round');
        var stepEl   = q('#br-step');
        var bubbleIn = q('.br-bubble-in');
        var bubbleEx = q('.br-bubble-ex');

        var RED  = '#ef4444';
        var BLUE = '#3b82f6';
        var R = 52, CIRC = 2*Math.PI*R;
        if(ringProg){ ringProg.style.strokeDasharray=String(CIRC); ringProg.style.strokeDashoffset=String(CIRC); }

        var syncOn = true;
        var phase = 'INHALE';
        var running = false;
        var round = 1;
        var phaseTargetMs = 4000;
        var phaseElapsedMs = 0;
        var lastTickTs = 0;
        var totalElapsedMs = 0; // 총 시간

        // Audio elements
        var inhaleAudio = document.getElementById('inhale-sound');
        var exhaleAudio = document.getElementById('exhale-sound');
        var volumeSlider = root.querySelector('#br-volume');

        if (inhaleAudio && exhaleAudio && volumeSlider) {
            function updateVolume() {
                inhaleAudio.volume = volumeSlider.value;
                exhaleAudio.volume = volumeSlider.value;
            }
            volumeSlider.addEventListener('input', updateVolume);
            updateVolume(); // Set initial volume
        }

        function stopAudio(audio){
          if(!audio) return;
          try{
            audio.pause();
            audio.currentTime = 0;
          }catch(e){ /* ignore */ }
        }

        function stopBreathAudio(){
          stopAudio(inhaleAudio);
          stopAudio(exhaleAudio);
        }

        function playPhaseAudio(){
          var current = (phase === 'INHALE') ? inhaleAudio : exhaleAudio;
          var other = (phase === 'INHALE') ? exhaleAudio : inhaleAudio;
          stopAudio(other);
          stopAudio(current);
          if(!current) return;
          if(typeof current.canPlayType === 'function' && !current.canPlayType('audio/mpeg')) return;
          current.play().catch(function(){ /* ignore */ });
        }

        function getInEl(){ return q('#br-in-sec'); }
        function getExEl(){ return q('#br-ex-sec'); }

        function clampSec(v){ v=String(v).replace(',', '.'); v=Number(v)||0; return Math.max(1, v); }
        function secToMs(v){ return clampSec(v)*1000; }
        function getInhale(){ var el=getInEl(); return el? clampSec(el.value) : 4; }
        function getExhale(){ var el=getExEl(); return el? clampSec(el.value) : 4; }

        function fmtDec(ms){ var sec = Math.max(0, ms)/1000; return sec.toFixed(2); }
        function fmtTotal(ms){
          var t = Math.max(0, Math.floor(ms/1000));
          var h = Math.floor(t/3600), m = Math.floor((t%3600)/60), s = t%60;
          var out = '';
          if(h>0) out += ('0'+h).slice(-2) + ':';
          out += ('0'+m).slice(-2) + ':' + ('0'+s).slice(-2);
          return out;
        }

        function applySyncUI(){
          var btn=q('#br-sync'), ex=getExEl(), inn=getInEl();
          if(!btn||!ex||!inn) return;
          btn.setAttribute('aria-pressed', syncOn?'true':'false');
          btn.textContent = syncOn ? '=' : '≠' ;
          ex.disabled = !!syncOn;
          if(syncOn){ ex.value = inn.value; }
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
          if(ringProg) ringProg.style.strokeDashoffset = String(CIRC);
          updateBubbles(0);
          if(running) playPhaseAudio();
          else stopBreathAudio();
        }

        function nextPhase(){
          if(phase==='INHALE') setPhase('EXHALE'); else setPhase('INHALE');
        }

        function start(){ if(running) return; running=true; var b=q('#br-start'); if(b) b.textContent = t('breath.pause'); lastTickTs=Date.now(); playPhaseAudio(); requestAnimationFrame(tick); }
        function pause(){ if(!running) return; running=false; var b=q('#br-start'); if(b) b.textContent = t('breath.start'); stopBreathAudio(); }
        function reset(){ running=false; var b=q('#br-start'); if(b) b.textContent = t('breath.start'); phaseElapsedMs=0; totalElapsedMs=0; round=1; if(roundEl) roundEl.textContent='1'; stopBreathAudio(); setPhase('INHALE'); if(totalLbl) totalLbl.textContent='00:00'; }

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
          var step = Number(el.step)||0.5;
          var next = clampSec((Number(el.value)||0) + (delta*step));
          el.value = next;
        }

        // 이벤트 위임
        document.addEventListener('click', function(e){
          var t = e.target; if(!t) return; if(!root.contains(t)) return;
          try{
            if(t.id==='br-start'){ running? pause(): start(); }
            else if(t.id==='br-reset'){ reset(); }
            else if(t.id==='br-sync'){ syncOn = !syncOn; applySyncUI(); }
            else if(t.id==='br-in-dec'){ var inn=getInEl(); adjustValue(inn, -1); if(syncOn){ var ex=getExEl(); if(ex) ex.value=inn.value; } if(phase==='INHALE'){ phaseTargetMs = secToMs(getInhale()); }
              if(timeLbl){ var remainNow = Math.max(0, phaseTargetMs - phaseElapsedMs); timeLbl.textContent = fmtDec(remainNow); } }
            else if(t.id==='br-in-inc'){ var inn2=getInEl(); adjustValue(inn2, +1); if(syncOn){ var ex2=getExEl(); if(ex2) ex2.value=inn2.value; } if(phase==='INHALE'){ phaseTargetMs = secToMs(getInhale()); }
              if(timeLbl){ var remainNow2 = Math.max(0, phaseTargetMs - phaseElapsedMs); timeLbl.textContent = fmtDec(remainNow2); } }
            else if(t.id==='br-ex-dec'){ var exn=getExEl(); adjustValue(exn, -1); if(!syncOn && phase==='EXHALE'){ phaseTargetMs = secToMs(getExhale()); }
              if(timeLbl){ var remainNow3 = Math.max(0, phaseTargetMs - phaseElapsedMs); timeLbl.textContent = fmtDec(remainNow3); } }
            else if(t.id==='br-ex-inc'){ var exn2=getExEl(); adjustValue(exn2, +1); if(!syncOn && phase==='EXHALE'){ phaseTargetMs = secToMs(getExhale()); }
              if(timeLbl){ var remainNow4 = Math.max(0, phaseTargetMs - phaseElapsedMs); timeLbl.textContent = fmtDec(remainNow4); } }
          }catch(err){ /* swallow */ }
        }, false);

        document.addEventListener('input', function(e){
          var t=e.target; if(!t) return; if(!root.contains(t)) return;
          try{
            if(t.id==='br-in-sec' || t.id==='br-ex-sec'){
              t.value = clampSec(t.value);
              if(syncOn && t.id==='br-in-sec'){ var ex=getExEl(); if(ex) ex.value = t.value; }
              if(phase==='INHALE' && t.id==='br-in-sec') phaseTargetMs = secToMs(getInhale());
              if(phase==='EXHALE' && t.id==='br-ex-sec') phaseTargetMs = secToMs(getExhale());
              if(timeLbl){ var remainNow = Math.max(0, phaseTargetMs - phaseElapsedMs); timeLbl.textContent = fmtDec(remainNow); }
            }
          }catch(err){ /* swallow */ }
        }, false);

        function applyLanguageState(){
          var b=q('#br-start');
          if(b) b.textContent = running ? t('breath.pause') : t('breath.start');
          if(phaseLbl) phaseLbl.textContent = (phase==='INHALE'? t('breath.inhale') : t('breath.exhale'));
          if(stepEl) stepEl.textContent = (phase==='INHALE'? t('breath.inhale') : t('breath.exhale'));
        }

        document.addEventListener('app:lang', function(){ applyLanguageState(); }, false);

        applySyncUI(); setPhase('INHALE'); if(totalLbl) totalLbl.textContent = '00:00';
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

      initSubscribeForm();
    })();
