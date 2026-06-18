(function(init){
      if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
      else init();
    })(function(){
      // --- scope 탐지 ---
      const scriptEl = document.currentScript;
      const root = (scriptEl && scriptEl.closest('.sw-embed')) || document.querySelector('.sw-embed') || document;
      const t = (key)=> (window.appI18n && typeof window.appI18n.t === 'function') ? window.appI18n.t(key) : key;

      // --- DOM (scoped) ---
      const elTime   = root.querySelector('#sw-time');
      const btnStart = root.querySelector('#sw-start');
      const btnLap   = root.querySelector('#sw-lap');
      const btnReset = root.querySelector('#sw-reset');
      const holdInput = root.querySelector('#sw-hold-sec');
      const restInput = root.querySelector('#sw-rest-sec');
      const adjustButtons = Array.from(root.querySelectorAll('[data-sw-adjust]'));
      const tableEl  = root.querySelector('#sw-table');
      let tblBody = null;
      if (tableEl) {
        tblBody = (tableEl.tBodies && tableEl.tBodies[0]) ? tableEl.tBodies[0] : null;
        if (!tblBody) { tblBody = document.createElement('tbody'); tableEl.appendChild(tblBody); }
      }
      function ensureTbody(){
        if (tblBody && tblBody.parentNode) return tblBody;
        if (!tableEl) return null;
        let tb = (tableEl.tBodies && tableEl.tBodies[0]) ? tableEl.tBodies[0] : null;
        if (!tb) { tb = document.createElement('tbody'); tableEl.appendChild(tb); }
        tblBody = tb; return tb;
      }
      function ensureRowForSet(n){
        const b = ensureTbody(); if(!b) return null;
        let tr = b.querySelector('tr[data-set="'+n+'"]');
        if(!tr){
          tr = document.createElement('tr');
          tr.setAttribute('data-set', String(n));
          tr.innerHTML = '<td style="text-align:left">'+n+'</td><td class="lap">—</td><td class="rest">—</td>';
          b.appendChild(tr);
        }
        return tr;
      }
      function formatSecHTML(sec){
        const val = isFinite(sec) ? Number(sec).toFixed(2) : '0.00';
        const parts = val.split('.');
        const i = parts[0]; const d = parts[1] ?? '00';
        return '<span class="sw-sec"><span class="int">'+i+'</span><span class="dec">.'+d+'</span></span>';
      }

      const canvas = root.querySelector('#sw-chart');
      const ctx = canvas.getContext('2d');

      const btnCSV  = root.querySelector('#sw-export-csv');
      const btnJSON = root.querySelector('#sw-export-json');
      const btnPNG  = root.querySelector('#sw-export-png');
      const btnCopy = root.querySelector('#sw-copy');

      // 색상 상수: Hold=빨간색, Rest=파란색
      const COLOR_LAP  = '#ef4444'; // red-500
      const COLOR_REST = '#3b82f6'; // blue-500

      // --- 포맷터 ---
      const fmt = (ms) => {
        const sign = ms < 0 ? '-' : '';
        ms = Math.abs(ms);
        const h = Math.floor(ms / 3600000);
        const m = Math.floor((ms % 3600000) / 60000);
        const s = Math.floor((ms % 60000) / 1000);
        const msR = Math.floor(ms % 1000);
        const pad = (n, z=2) => String(n).padStart(z, '0');
        return `${sign}${pad(h)}:${pad(m)}:${pad(s)}.${pad(msR,3)}`
      };

      // --- State ---
      let running   = false;      // 타이머 동작 여부
      let startTs   = 0;          // 현재 구간 시작 시각
      let nextType  = 'LAP';      // 현재 측정 타입: 'LAP' 또는 'REST'
      let currentSet= 1;          // 현재 # 인덱스
      let sets = [];              // [{n, lapMs:null|number, restMs:null|number}]
      let tickRaf   = null;
      let autoMode  = false;
      let autoTimer = null;
      let autoIdx   = 0;
      let autoSegments = [];
      const DEFAULT_HOLD_SEC = 120;
      const DEFAULT_REST_SEC = 120;
      const HOLD_MIN_SEC = 5;
      const REST_MIN_SEC = 15;
      const INPUT_STEP_SEC = 5;
      const REST_DROP_PER_ROUND_SEC = 15;

      function normalizeSeconds(value, min, fallback){
        const parsed = (typeof value === 'string' && value.trim() === '') ? NaN : Number(value);
        const base = Number.isFinite(parsed) ? parsed : fallback;
        return Math.max(min, Math.round(base / INPUT_STEP_SEC) * INPUT_STEP_SEC);
      }
      function setInputSeconds(input, value, min, fallback){
        if(!input) return normalizeSeconds(value, min, fallback);
        const next = normalizeSeconds(value, min, fallback);
        input.value = String(next);
        return next;
      }
      function syncRoutineInputs(){
        const holdSec = setInputSeconds(holdInput, holdInput ? holdInput.value : DEFAULT_HOLD_SEC, HOLD_MIN_SEC, DEFAULT_HOLD_SEC);
        const restSec = setInputSeconds(restInput, restInput ? restInput.value : DEFAULT_REST_SEC, REST_MIN_SEC, DEFAULT_REST_SEC);
        return { holdSec, restSec };
      }
      function setRoutineControlsDisabled(disabled){
        [holdInput, restInput, ...adjustButtons].forEach(el=>{ if(el) el.disabled = disabled; });
      }
      function buildAutoSegments(){
        const cfg = syncRoutineInputs();
        const segments = [];
        let restSec = cfg.restSec;
        while(true){
          segments.push(cfg.holdSec * 1000);
          segments.push(restSec * 1000);
          if(restSec <= REST_MIN_SEC) break;
          restSec = Math.max(REST_MIN_SEC, restSec - REST_DROP_PER_ROUND_SEC);
        }
        return segments;
      }

      // --- 하이라이트 유틸 ---
      function clearActive(){
        if(!tblBody) return;
        tblBody.querySelectorAll('td.lap.active, td.rest.active').forEach(td=> td.classList.remove('active'));
      }
      function setActiveHighlight(){
        clearActive();
        if(!running) return;
        const tr = ensureRowForSet(currentSet);
        if(!tr) return;
        const cell = tr.querySelector(nextType==='LAP' ? 'td.lap' : 'td.rest');
        if(cell) cell.classList.add('active');
      }
      function flashSaved(cell){
        if(!cell) return;
        cell.classList.add('saved');
        setTimeout(()=>cell.classList.remove('saved'), 650);
      }
      function clearAutoTimer(){
        if(autoTimer){ clearTimeout(autoTimer); autoTimer = null; }
      }
      function stopAuto(){
        autoMode = false;
        autoIdx = 0;
        autoSegments = [];
        clearAutoTimer();
        setRoutineControlsDisabled(false);
      }

      // --- Chart ---
      function drawChart(live){
        const W = canvas.width, H = canvas.height;
        ctx.clearRect(0,0,W,H);
        ctx.fillStyle = '#0f1115'; ctx.fillRect(0,0,W,H);
        const nowTs = performance.now();
        const pulseMaxRadius = 46;
        const pulseMaxLineW = 10;
        const pulsePad = Math.ceil(pulseMaxRadius + pulseMaxLineW / 2 + 2);
        const pad = {l:40 + pulsePad, r:12 + pulsePad, t:12 + pulsePad, b:28 + pulsePad};
        ctx.strokeStyle = '#2a2f38'; ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(pad.l, H - pad.b); ctx.lineTo(W - pad.r, H - pad.b);
        ctx.moveTo(pad.l, H - pad.b); ctx.lineTo(pad.l, pad.t);
        ctx.stroke();

        const hasLive = live && typeof live.ms === 'number';
        if(sets.length === 0 && !hasLive){
          ctx.fillStyle = '#9ca3af';
          ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
          ctx.fillText(t('sw.chartEmpty'), pad.l + 8, H/2);
          return;
        }

        const lapsS  = sets.map(s=> typeof s.lapMs  === 'number' ? s.lapMs/1000  : null);
        const restsS = sets.map(s=> typeof s.restMs === 'number' ? s.restMs/1000 : null);
        let seriesCount = Math.max(lapsS.length, restsS.length);
        if(hasLive){
          const idx = Math.max(0, (live.setIndex || currentSet) - 1);
          seriesCount = Math.max(seriesCount, idx + 1);
          while(lapsS.length < seriesCount) lapsS.push(null);
          while(restsS.length < seriesCount) restsS.push(null);
          const sec = live.ms / 1000;
          if(live.type === 'LAP') lapsS[idx] = sec;
          if(live.type === 'REST') restsS[idx] = sec;
        }
        const values = [...lapsS, ...restsS].filter(v=>v!=null);
        if(values.length === 0){
          ctx.fillStyle = '#9ca3af';
          ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
          ctx.fillText(t('sw.chartNoRecords'), pad.l + 8, H/2);
          return;
        }
        const maxV = Math.max(...values);
        const minV = 0;
        const range = Math.max(0.01, maxV - minV);
        const xStep = (W - pad.l - pad.r) / Math.max(1, seriesCount - 1);
        const yScale= (H - pad.t - pad.b) / range;

        // grid labels
        ctx.strokeStyle = '#242a33';
        ctx.fillStyle = '#cbd5e1';
        ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
        const steps = 4;
        for(let i=0;i<=steps;i++){
          const v = minV + (range/steps)*i;
          const y = (H - pad.b) - (v - minV) * yScale;
          ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
          ctx.fillText(v.toFixed(2) + t('unit.secondsShort'), 4, y+4);
        }

        function drawSeries(arr, stroke, pointFill, seriesType){
          ctx.beginPath();
          let started=false;
          arr.forEach((val,i)=>{
            if(val==null) return;
            const x = pad.l + xStep * i;
            const y = (H - pad.b) - (val - minV) * yScale;
            if(!started){ ctx.strokeStyle = stroke; ctx.lineWidth = 2; ctx.moveTo(x,y); started=true; }
            else ctx.lineTo(x,y);
          });
          if(started) ctx.stroke();
          arr.forEach((val,i)=>{
            if(val==null) return;
            const x = pad.l + xStep * i;
            const y = (H - pad.b) - (val - minV) * yScale;
            ctx.beginPath(); ctx.fillStyle = pointFill; ctx.arc(x,y,3,0,Math.PI*2); ctx.fill();
            if(live && live.type === seriesType && (live.setIndex - 1) === i){
              const phase = (nowTs % 2000) / 2000;
              const easeOut = 1 - Math.pow(1 - phase, 3);
              const radius = 6 + easeOut * 40;
              const fade = 1 - phase;
              const lineW = 10 * fade;
              ctx.save();
              ctx.beginPath();
              ctx.rect(0, 0, W, H);
              ctx.clip();
              ctx.beginPath();
              ctx.strokeStyle = pointFill;
              ctx.globalAlpha = 0.9 * fade;
              ctx.lineWidth = lineW;
              ctx.arc(x, y, radius, 0, Math.PI*2);
              ctx.stroke();
              ctx.restore();
            }
          });
        }
        drawSeries(lapsS,  COLOR_LAP, COLOR_LAP, 'LAP');
        drawSeries(restsS, COLOR_REST, COLOR_REST, 'REST');

        ctx.fillStyle = '#6b7280';
        for(let i=0;i<seriesCount;i++){ const x = pad.l + xStep * i; ctx.fillText(String(i+1), x-3, H-8); }
      }

      // --- View ---
      function tick(){
        if(!running) return;
        const now = performance.now();
        const elapsed = now - startTs; // 현재 구간만 표기
        elTime.textContent = fmt(elapsed);
        drawChart({ms: elapsed, type: nextType, setIndex: currentSet});
        if(autoMode && autoIdx < autoSegments.length){
          const tr = ensureRowForSet(currentSet);
          if(tr){
            const cell = tr.querySelector(nextType==='LAP' ? 'td.lap' : 'td.rest');
            if(cell){
              const remaining = Math.max(0, autoSegments[autoIdx] - elapsed);
              cell.innerHTML = formatSecHTML(remaining/1000);
            }
          }
        }
        tickRaf = requestAnimationFrame(tick);
      }

      function recordCurrent(ms){
        const sec = ms/1000;
        if(!sets[currentSet-1]) sets[currentSet-1] = {n: currentSet, lapMs: null, restMs: null};
        const set = sets[currentSet-1];
        const tr = ensureRowForSet(currentSet);

        if(nextType === 'LAP'){
          set.lapMs = Math.max(0, Math.round(ms));
          if(tr){ const cell = tr.querySelector('td.lap'); if(cell){ cell.innerHTML = formatSecHTML(sec); flashSaved(cell); } }
          nextType = 'REST';
        }else{ // REST
          set.restMs = Math.max(0, Math.round(ms));
          if(tr){ const cell = tr.querySelector('td.rest'); if(cell){ cell.innerHTML = formatSecHTML(sec); flashSaved(cell); } }
          nextType = 'LAP';
          currentSet += 1;
        }
        drawChart();
      }

      function clearAll(){
        sets = []; currentSet = 1; nextType = 'LAP';
        const b = ensureTbody(); if(b) b.innerHTML = '';
        drawChart();
      }

      // --- Controls ---
      const stopBubble = (e)=>{ e.stopPropagation(); };
      [btnStart, btnLap, btnReset, ...adjustButtons].forEach(el=>{ if(el){ el.addEventListener('click', stopBubble); el.addEventListener('touchstart', stopBubble, {passive:false}); }});

      adjustButtons.forEach(function(btn){
        btn.addEventListener('click', function(){
          if(running) return;
          const target = btn.getAttribute('data-sw-adjust');
          const delta = Number(btn.getAttribute('data-delta')) || 0;
          if(target === 'hold') setInputSeconds(holdInput, Number(holdInput ? holdInput.value : DEFAULT_HOLD_SEC) + delta, HOLD_MIN_SEC, DEFAULT_HOLD_SEC);
          if(target === 'rest') setInputSeconds(restInput, Number(restInput ? restInput.value : DEFAULT_REST_SEC) + delta, REST_MIN_SEC, DEFAULT_REST_SEC);
        });
      });
      [holdInput, restInput].forEach(function(input){
        if(!input) return;
        input.addEventListener('change', function(){
          if(input === holdInput) setInputSeconds(input, input.value, HOLD_MIN_SEC, DEFAULT_HOLD_SEC);
          if(input === restInput) setInputSeconds(input, input.value, REST_MIN_SEC, DEFAULT_REST_SEC);
        });
      });

      btnStart.addEventListener('click', function(){
        if(running){
          // Stop: 현재 구간 기록 후 정지
          running = false;
          cancelAnimationFrame(tickRaf);
          clearAutoTimer();
          const seg = performance.now() - startTs;
          recordCurrent(seg);
          btnStart.textContent = t('sw.start');
          if(btnLap) btnLap.disabled = true;
          stopAuto();
          if(window.appWakeLock) window.appWakeLock.release('co2-timer');
          elTime.textContent = '00:00:00.000';
          // 정지 시 하이라이트 제거
          clearActive();
          return;
        }
        clearAll();
        autoSegments = buildAutoSegments();
        autoMode = true;
        autoIdx = 0;
        setRoutineControlsDisabled(true);
        nextType = 'LAP';
        currentSet = 1;
        startTs = performance.now();
        running = true;
        if(window.appWakeLock) window.appWakeLock.request('co2-timer');
        btnStart.textContent = t('sw.stop');
        if(btnLap) btnLap.disabled = true;
        // 어떤 칸이 채워질지 미리 강조
        setActiveHighlight();
        tickRaf = requestAnimationFrame(tick);
        function advance(){
          if(!running || !autoMode) return;
          const seg = performance.now() - startTs;
          recordCurrent(seg);
          autoIdx += 1;
          if(autoIdx >= autoSegments.length){
            running = false;
            cancelAnimationFrame(tickRaf);
            btnStart.textContent = t('sw.start');
            if(btnLap) btnLap.disabled = true;
            elTime.textContent = '00:00:00.000';
            clearActive();
            stopAuto();
            if(window.appWakeLock) window.appWakeLock.release('co2-timer');
            return;
          }
          startTs = performance.now();
          elTime.textContent = '00:00:00.000';
          setActiveHighlight();
          clearAutoTimer();
          autoTimer = setTimeout(advance, autoSegments[autoIdx]);
        }
        clearAutoTimer();
        autoTimer = setTimeout(advance, autoSegments[autoIdx]);
      });

      btnLap && btnLap.addEventListener('click', function(){
        if(!running || autoMode) return;
        const seg = performance.now() - startTs; // 현재 구간 기록
        recordCurrent(seg);
        // 랩 이후 다음 구간을 0부터 측정
        startTs = performance.now();
        elTime.textContent = '00:00:00.000';
        // 다음에 채워질 칸 강조
        setActiveHighlight();
      });

      btnReset.addEventListener('click', function(){
        running = false; cancelAnimationFrame(tickRaf);
        clearAutoTimer(); stopAuto();
        if(window.appWakeLock) window.appWakeLock.release('co2-timer');
        clearAll(); elTime.textContent = '00:00:00.000';
        btnStart.textContent = t('sw.start');
        if(btnLap) btnLap.disabled = true;
        clearActive();
      });

      // --- Export ---
      function toCSV(){
        const header = ['no','hold_s','hold_ms','rest_s','rest_ms'];
        const rows = sets.map(s=>[
          s.n,
          (typeof s.lapMs==='number') ? (s.lapMs/1000).toFixed(2) : '',
          (typeof s.lapMs==='number') ? s.lapMs : '',
          (typeof s.restMs==='number') ? (s.restMs/1000).toFixed(2) : '',
          (typeof s.restMs==='number') ? s.restMs : ''
        ]);
        const lines = [header.join(','), ...rows.map(r=>r.join(','))];
        return lines.join(String.fromCharCode(10));
      }
      function toJSON(){ return JSON.stringify({sets}, null, 2); }
      function download(name, mime, data){
        const blob = new Blob([data], {type: mime});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
        setTimeout(()=>URL.revokeObjectURL(url), 1000);
      }
      btnCSV && btnCSV.addEventListener('click', ()=> download('stopwatch_sets.csv', 'text/csv', toCSV()));
      btnJSON&& btnJSON.addEventListener('click', ()=> download('stopwatch_sets.json', 'application/json', toJSON()));
      btnPNG && btnPNG.addEventListener('click', ()=> { const dataUrl = canvas.toDataURL('image/png'); const a=document.createElement('a'); a.href=dataUrl; a.download='stopwatch_chart.png'; document.body.appendChild(a); a.click(); a.remove(); });
      btnCopy&& btnCopy.addEventListener('click', async ()=>{ try { await navigator.clipboard.writeText(toCSV()); btnCopy.textContent = t('sw.copied'); setTimeout(()=>{ btnCopy.textContent = t('sw.copy'); }, 1200);} catch(e){ alert(t('sw.copyFail') + e.message);} });

      function applyLanguageState(){
        if(btnStart) btnStart.textContent = running ? t('sw.stop') : t('sw.start');
        drawChart();
      }

      document.addEventListener('app:lang', function(){ applyLanguageState(); }, false);
      applyLanguageState();
      syncRoutineInputs();

      // --- 런타임 에러 표시 ---
      window.addEventListener('error', function(ev){
        const box = root.querySelector('#sw-error');
        if(!box) return;
        box.style.display = 'block';
        box.innerHTML = '<pre style="white-space:pre-wrap;background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;padding:8px;border-radius:8px;font-size:12px">Script Error: '+ (ev.message || ev.error) +'</pre>';
      });

      // --- 초기 렌더 ---
      drawChart();
    });
