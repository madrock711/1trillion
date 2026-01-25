(function(init){
      if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
      else init();
    })(function(){
      // --- scope 탐지 ---
      const scriptEl = document.currentScript;
      const root = (scriptEl && scriptEl.closest('.sw-embed')) || document.querySelector('.sw-embed') || document;

      // --- DOM (scoped) ---
      const elTime   = root.querySelector('#sw-time');
      const btnStart = root.querySelector('#sw-start');
      const btnLap   = root.querySelector('#sw-lap');
      const btnReset = root.querySelector('#sw-reset');
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

      // 색상 상수: Lap=빨간색, Rest=파란색
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

      // --- Chart ---
      function drawChart(){
        const W = canvas.width, H = canvas.height;
        ctx.clearRect(0,0,W,H);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(0,0,W,H);
        const pad = {l:40, r:12, t:12, b:28};
        ctx.strokeStyle = '#e5e7eb'; ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(pad.l, H - pad.b); ctx.lineTo(W - pad.r, H - pad.b);
        ctx.moveTo(pad.l, H - pad.b); ctx.lineTo(pad.l, pad.t);
        ctx.stroke();

        if(sets.length === 0){
          ctx.fillStyle = '#9ca3af';
          ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
          ctx.fillText('Lap → Lap, Rest가 교대로 기록됩니다. Start(Stop)으로 현재 구간을 종료/기록합니다.', pad.l + 8, H/2);
          return;
        }

        const lapsS  = sets.map(s=> typeof s.lapMs  === 'number' ? s.lapMs/1000  : null);
        const restsS = sets.map(s=> typeof s.restMs === 'number' ? s.restMs/1000 : null);
        const values = [...lapsS, ...restsS].filter(v=>v!=null);
        if(values.length === 0){
          ctx.fillStyle = '#9ca3af';
          ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
          ctx.fillText('아직 기록이 없습니다. Lap을 눌러 기록을 시작하세요.', pad.l + 8, H/2);
          return;
        }
        const maxV = Math.max(...values);
        const minV = Math.min(...values);
        const range = Math.max(0.01, maxV - Math.min(minV, maxV-0.01));
        const xStep = (W - pad.l - pad.r) / Math.max(1, sets.length - 1);
        const yScale= (H - pad.t - pad.b) / range;

        // grid labels
        ctx.strokeStyle = '#f3f4f6';
        ctx.fillStyle = '#6b7280';
        ctx.font = '11px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
        const steps = 4;
        for(let i=0;i<=steps;i++){
          const v = minV + (range/steps)*i;
          const y = (H - pad.b) - (v - minV) * yScale;
          ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
          ctx.fillText(v.toFixed(2)+'s', 4, y+4);
        }

        function drawSeries(arr, stroke, pointFill){
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
          });
        }
        drawSeries(lapsS,  COLOR_LAP, COLOR_LAP);
        drawSeries(restsS, COLOR_REST, COLOR_REST);

        ctx.fillStyle = '#6b7280';
        sets.forEach((_,i)=>{ const x = pad.l + xStep * i; ctx.fillText(String(i+1), x-3, H-8); });
      }

      // --- View ---
      function tick(){
        if(!running) return;
        const now = performance.now();
        const elapsed = now - startTs; // 현재 구간만 표기
        elTime.textContent = fmt(elapsed);
        requestAnimationFrame(tick);
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
      [btnStart, btnLap, btnReset].forEach(el=>{ if(el){ el.addEventListener('click', stopBubble); el.addEventListener('touchstart', stopBubble, {passive:false}); }});

      btnStart.addEventListener('click', function(){
        if(running){
          // Stop: 현재 구간 기록 후 정지
          running = false;
          cancelAnimationFrame(tickRaf);
          const seg = performance.now() - startTs;
          recordCurrent(seg);
          btnStart.textContent = 'Start';
          btnLap.disabled = true;
          elTime.textContent = '00:00:00.000';
          // 정지 시 하이라이트 제거
          clearActive();
          return;
        }
        // Start: 현재 기대 타입(nextType) 구간 측정 시작
        startTs = performance.now();
        running = true;
        btnStart.textContent = 'Stop';
        btnLap.disabled = false;
        // 어떤 칸이 채워질지 미리 강조
        setActiveHighlight();
        requestAnimationFrame(tick);
      });

      btnLap.addEventListener('click', function(){
        if(!running) return;
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
        clearAll(); elTime.textContent = '00:00:00.000';
        btnStart.textContent = 'Start';
        btnLap.disabled = true;
        clearActive();
      });

      // --- Export ---
      function toCSV(){
        const header = ['no','lap_s','lap_ms','rest_s','rest_ms'];
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
      btnCopy&& btnCopy.addEventListener('click', async ()=>{ try { await navigator.clipboard.writeText(toCSV()); btnCopy.textContent='Copied!'; setTimeout(()=>btnCopy.textContent='Copy as Text', 1200);} catch(e){ alert('복사 실패: '+e.message);} });

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
  </script>