(function(){
  'use strict';

  var state = {
    stream: null,
    activeSlot: null,
    currentSlot: null,
    captures: {
      'left-top': null,
      'left-side': null,
      'right-top': null,
      'right-side': null
    },
    results: null
  };

  function t(key){
    return (window.appI18n && typeof window.appI18n.t === 'function') ? window.appI18n.t(key) : key;
  }

  function qs(sel){ return document.querySelector(sel); }

  function setStep(step){
    var steps = document.querySelectorAll('.foot-step');
    steps.forEach(function(el){
      var num = Number(el.getAttribute('data-step'));
      if(num <= step){
        el.classList.add('is-active');
      } else {
        el.classList.remove('is-active');
      }
    });
  }

  function updateProgress(val){
    var el = qs('#foot-progress');
    if(!el) return;
    el.textContent = String(val) + '%';
  }

  function stopCamera(){
    if(state.stream){
      state.stream.getTracks().forEach(function(track){ track.stop(); });
      state.stream = null;
    }
    var video = qs('#foot-video');
    if(video){ video.srcObject = null; }
  }

  function updateCaptureStatus(messageKey, replacements, isError){
    var status = qs('#foot-capture-status');
    if(!status) return;
    var msg = t(messageKey);
    if(replacements){
      Object.keys(replacements).forEach(function(key){
        msg = msg.replace('{' + key + '}', replacements[key]);
      });
    }
    status.textContent = msg;
    if(isError){ status.classList.add('is-error'); }
    else { status.classList.remove('is-error'); }
  }

  var slotOrder = ['left-top', 'left-side', 'right-top', 'right-side'];

  function currentTargetLabel(){
    var sideEl = qs('#foot-side');
    var angleEl = qs('#foot-angle');
    var side = t('foot.' + (sideEl ? sideEl.value : 'left'));
    var angle = t('foot.angle' + ((angleEl ? angleEl.value : 'top') === 'top' ? 'Top' : 'Side'));
    return { side: side, angle: angle };
  }

  function updateCaptureTarget(){
    updateCaptureStatus('foot.captureTarget', currentTargetLabel());
  }

  function hapticPulse(){
    if(navigator && typeof navigator.vibrate === 'function'){
      navigator.vibrate(20);
    }
  }

  function startCamera(){
    var video = qs('#foot-video');
    if(!video || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
      updateCaptureStatus('foot.cameraUnsupported', null, true);
      alert(t('foot.cameraUnsupported'));
      return;
    }
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false })
      .then(function(stream){
        state.stream = stream;
        video.srcObject = stream;
        video.play().catch(function(){ /* ignore */ });
        updateCaptureStatus('foot.cameraReady');
      })
      .catch(function(){
        updateCaptureStatus('foot.cameraDenied', null, true);
        alert(t('foot.cameraDenied'));
      });
  }

  function computeSlotFromSelects(){
    var angle = qs('#foot-angle');
    var side = qs('#foot-side');
    var a = angle ? angle.value : 'top';
    var s = side ? side.value : 'left';
    return s + '-' + a;
  }
  
  function slotKey(){
    if(state.currentSlot) return state.currentSlot;
    state.currentSlot = computeSlotFromSelects();
    return state.currentSlot;
  }

  function setCurrentSlot(key, syncSelects){
    state.currentSlot = key;
    if(syncSelects) setSelectsForSlot(key);
    updateCaptureTarget();
  }

  function setSelectsForSlot(key){
    var parts = key.split('-');
    if(parts.length !== 2) return;
    var sideEl = qs('#foot-side');
    var angleEl = qs('#foot-angle');
    if(sideEl) sideEl.value = parts[0];
    if(angleEl) angleEl.value = parts[1];
  }

  function autoAdvanceSlot(){
    var current = slotKey();
    var currentIndex = slotOrder.indexOf(current);
    for(var i = currentIndex + 1; i < slotOrder.length; i++){
      if(!state.captures[slotOrder[i]]){
        setCurrentSlot(slotOrder[i], true);
        return;
      }
    }
  }

  function setPreview(key, dataUrl){
    state.captures[key] = dataUrl;
    var slot = qs('.foot-preview-slot[data-slot="' + key + '"]');
    if(!slot) return;
    slot.innerHTML = '';
    var img = document.createElement('img');
    img.src = dataUrl;
    img.alt = key;
    slot.appendChild(img);
    selectPreview(key);
  }

  function selectPreview(key){
    state.activeSlot = key;
    setCurrentSlot(key, true);
    var slots = document.querySelectorAll('.foot-preview-slot');
    slots.forEach(function(slot){
      if(slot.getAttribute('data-slot') === key){ slot.classList.add('is-active'); }
      else { slot.classList.remove('is-active'); }
    });
  }

  function captureFrame(){
    var video = qs('#foot-video');
    if(!video || !state.stream){
      updateCaptureStatus('foot.captureNoCamera', null, true);
      alert(t('foot.captureNoCamera'));
      return;
    }
    var canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    var dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setPreview(slotKey(), dataUrl);
    updateCaptureStatus('foot.captureDone', {
      side: t('foot.' + (qs('#foot-side') ? qs('#foot-side').value : 'left')),
      angle: t('foot.angle' + ((qs('#foot-angle') ? qs('#foot-angle').value : 'top') === 'top' ? 'Top' : 'Side'))
    });
    hapticPulse();
    autoAdvanceSlot();
  }

  function loadUpload(file){
    if(!file) return;
    var reader = new FileReader();
    reader.onload = function(e){
      setPreview(slotKey(), e.target.result);
      updateCaptureStatus('foot.uploadDone', {
        side: t('foot.' + (qs('#foot-side') ? qs('#foot-side').value : 'left')),
        angle: t('foot.angle' + ((qs('#foot-angle') ? qs('#foot-angle').value : 'top') === 'top' ? 'Top' : 'Side'))
      });
      hapticPulse();
      autoAdvanceSlot();
    };
    reader.readAsDataURL(file);
  }

  function countCaptures(){
    var count = 0;
    Object.keys(state.captures).forEach(function(key){
      if(state.captures[key]) count += 1;
    });
    return count;
  }

  function pickBySeed(list, seed){
    if(!list.length) return '';
    var idx = Math.abs(seed) % list.length;
    return list[idx];
  }

  function estimateLength(){
    var input = qs('#foot-length-input');
    var val = input ? Number(input.value) : 0;
    if(val && !isNaN(val)) return Math.max(200, Math.min(320, val));
    var scale = qs('#foot-scale');
    var scaleVal = scale ? scale.value : 'none';
    if(scaleVal === 'a4') return 255;
    if(scaleVal === 'card') return 250;
    return 260;
  }

  function analyze(){
    var count = countCaptures();
    updateProgress(10);
    setStep(2);

    var lengthMm = estimateLength();
    var seed = Math.round(lengthMm) + (count * 7);
    var widthMm = Math.round(lengthMm * 0.39);
    var widthRatio = widthMm / lengthMm;
    var widthType = widthRatio < 0.37 ? t('foot.widthNarrow') : (widthRatio > 0.41 ? t('foot.widthWide') : t('foot.widthNormal'));

    var hasSide = !!(state.captures['left-side'] || state.captures['right-side']);
    var instep = hasSide ? pickBySeed([t('foot.instepMid'), t('foot.instepHigh')], seed + 3) : pickBySeed([t('foot.instepLow'), t('foot.instepMid')], seed + 5);
    if(widthRatio > 0.41 && instep === t('foot.instepLow')) instep = t('foot.instepMid');
    if(widthRatio < 0.37 && instep === t('foot.instepHigh')) instep = t('foot.instepMid');

    var arch = pickBySeed([t('foot.archFlat'), t('foot.archNormal'), t('foot.archHigh')], seed + 11);
    if(widthRatio > 0.41) arch = t('foot.archFlat');
    if(widthRatio < 0.37) arch = t('foot.archHigh');

    var toe = t('foot.toeGreek');
    if(lengthMm >= 270 && widthRatio < 0.38) toe = t('foot.toeEgypt');
    if(widthRatio > 0.41) toe = t('foot.toeRoman');

    var ball = widthType;

    state.results = {
      lengthMm: lengthMm,
      widthMm: widthMm,
      widthType: widthType,
      instep: instep,
      arch: arch,
      toe: toe,
      ball: ball
    };

    setTimeout(function(){ updateProgress(55); }, 200);
    setTimeout(function(){ updateProgress(100); }, 600);

    setTimeout(function(){
      var l = qs('#foot-result-length');
      var w = qs('#foot-result-width');
      var i = qs('#foot-result-instep');
      var a = qs('#foot-result-arch');
      var tEl = qs('#foot-result-toe');
      var b = qs('#foot-result-ball');
      if(l) l.textContent = lengthMm + ' mm';
      if(w) w.textContent = widthMm + ' mm (' + widthType + ')';
      if(i) i.textContent = instep;
      if(a) a.textContent = arch;
      if(tEl) tEl.textContent = toe;
      if(b) b.textContent = ball;
      buildRecommendations();
      setStep(3);
    }, 650);
  }

  function sizeAdvice(lengthMm){
    var fit = qs('#foot-fit');
    var fitVal = fit ? fit.value : 'balanced';
    if(fitVal === 'comfort') return t('foot.sizeComfort').replace('{mm}', lengthMm);
    if(fitVal === 'performance') return t('foot.sizePerformance').replace('{mm}', lengthMm);
    return t('foot.sizeBalanced').replace('{mm}', lengthMm);
  }

  function buildRecommendations(){
    var grid = qs('#foot-reco-grid');
    if(!grid || !state.results) return;

    var level = qs('#foot-level') ? qs('#foot-level').value : 'beginner';
    var type = qs('#foot-type') ? qs('#foot-type').value : 'bouldering';
    var widthType = state.results.widthType;

    var models = [
      { brand: 'La Sportiva', model: 'Tarantula', level: 'beginner', types: ['sport', 'multi'], width: 'normal', last: 'neutral', volume: 'mid', price: '$$' },
      { brand: 'Scarpa', model: 'Origin', level: 'beginner', types: ['sport', 'multi'], width: 'wide', last: 'neutral', volume: 'high', price: '$$' },
      { brand: 'Evolv', model: 'Kronos', level: 'beginner', types: ['sport', 'multi'], width: 'normal', last: 'neutral', volume: 'mid', price: '$$' },
      { brand: 'Black Diamond', model: 'Momentum', level: 'beginner', types: ['sport', 'multi'], width: 'normal', last: 'neutral', volume: 'mid', price: '$$' },
      { brand: 'Tenaya', model: 'Tanta', level: 'intermediate', types: ['bouldering', 'sport'], width: 'normal', last: 'slightly downturned', volume: 'mid', price: '$$$' },
      { brand: 'La Sportiva', model: 'Katana Lace', level: 'intermediate', types: ['sport', 'multi'], width: 'narrow', last: 'slightly downturned', volume: 'low', price: '$$$' },
      { brand: 'Scarpa', model: 'Vapor V', level: 'intermediate', types: ['sport', 'bouldering'], width: 'normal', last: 'slightly downturned', volume: 'mid', price: '$$$' },
      { brand: 'Five Ten', model: 'Anasazi', level: 'intermediate', types: ['sport', 'multi'], width: 'narrow', last: 'neutral', volume: 'low', price: '$$$' },
      { brand: 'La Sportiva', model: 'Solution Comp', level: 'advanced', types: ['bouldering'], width: 'normal', last: 'aggressive', volume: 'mid', price: '$$$$' },
      { brand: 'Scarpa', model: 'Instinct VS', level: 'advanced', types: ['bouldering', 'sport'], width: 'wide', last: 'aggressive', volume: 'high', price: '$$$$' },
      { brand: 'Tenaya', model: 'Iati', level: 'advanced', types: ['sport', 'bouldering'], width: 'narrow', last: 'aggressive', volume: 'low', price: '$$$$' },
      { brand: 'Evolv', model: 'Shaman', level: 'advanced', types: ['bouldering', 'sport'], width: 'wide', last: 'aggressive', volume: 'high', price: '$$$$' }
    ];

    function widthMatch(){
      if(widthType === t('foot.widthWide')) return 'wide';
      if(widthType === t('foot.widthNarrow')) return 'narrow';
      return 'normal';
    }

    var targetWidth = widthMatch();
    var scored = models.map(function(item){
      var score = 60;
      if(item.level === level) score += 10;
      if(item.types.indexOf(type) > -1) score += 10;
      if(item.width === targetWidth) score += 12;
      if(state.results.instep === t('foot.instepHigh') && item.volume === 'high') score += 8;
      if(state.results.instep === t('foot.instepLow') && item.volume === 'low') score += 8;
      if(state.results.arch === t('foot.archHigh') && item.last === 'aggressive') score += 6;
      if(state.results.arch === t('foot.archFlat') && item.last === 'neutral') score += 6;
      if(state.results.instep === t('foot.instepHigh') && item.width === 'wide') score += 4;
      if(state.results.instep === t('foot.instepLow') && item.width === 'narrow') score += 4;
      score = Math.min(95, score);
      return { item: item, score: score };
    }).sort(function(a,b){ return b.score - a.score; });

    grid.innerHTML = '';

    var advice = sizeAdvice(state.results.lengthMm);
    scored.slice(0, 6).forEach(function(entry){
      var card = document.createElement('div');
      card.className = 'foot-reco-card';
      card.innerHTML = '' +
        '<div class="foot-reco-top">' +
          '<div>' +
            '<div class="foot-reco-brand">' + entry.item.brand + '</div>' +
            '<div class="foot-reco-model">' + entry.item.model + '</div>' +
          '</div>' +
          '<div class="foot-score">' + entry.score + '%</div>' +
        '</div>' +
        '<div class="foot-reco-meta">' +
          '<span>' + t('foot.recoLevel') + ': ' + t('foot.level.' + entry.item.level) + '</span>' +
          '<span>' + t('foot.recoType') + ': ' + t('foot.type.' + entry.item.types[0]) + '</span>' +
          '<span>' + t('foot.recoLast') + ': ' + entry.item.last + '</span>' +
          '<span>' + t('foot.recoWidth') + ': ' + entry.item.width + '</span>' +
          '<span>' + t('foot.recoVolume') + ': ' + entry.item.volume + '</span>' +
        '</div>' +
        '<div class="foot-reco-footer">' +
          '<span class="foot-reco-price">' + entry.item.price + '</span>' +
          '<span class="foot-reco-size">' + advice + '</span>' +
        '</div>';
      grid.appendChild(card);
    });
  }

  function resetAll(){
    state.captures = { 'left-top': null, 'left-side': null, 'right-top': null, 'right-side': null };
    state.activeSlot = null;
    state.results = null;
    var slots = document.querySelectorAll('.foot-preview-slot');
    slots.forEach(function(slot){
      var label = slot.getAttribute('data-slot') || '';
      slot.innerHTML = '<span>' + (t('foot.preview.' + label) || label) + '</span>';
      slot.classList.remove('is-active');
    });
    var resIds = ['length','width','instep','arch','toe','ball'];
    resIds.forEach(function(id){
      var el = qs('#foot-result-' + id);
      if(el) el.textContent = '-';
    });
    var grid = qs('#foot-reco-grid');
    if(grid) grid.innerHTML = '<div class="foot-reco-empty">' + t('foot.recoEmpty') + '</div>';
    updateProgress(0);
    setStep(1);
    updateCaptureStatus('foot.captureIdle');
    updateCaptureTarget();
    state.currentSlot = computeSlotFromSelects();
  }

  function saveHistory(){
    if(!state.results) return;
    var history = JSON.parse(localStorage.getItem('footAnalysisHistory') || '[]');
    var entry = {
      date: new Date().toISOString(),
      lengthMm: state.results.lengthMm,
      widthType: state.results.widthType,
      arch: state.results.arch,
      toe: state.results.toe
    };
    history.unshift(entry);
    history = history.slice(0, 8);
    localStorage.setItem('footAnalysisHistory', JSON.stringify(history));
    renderHistory();
  }

  function renderHistory(){
    var list = qs('#foot-history-list');
    if(!list) return;
    var history = JSON.parse(localStorage.getItem('footAnalysisHistory') || '[]');
    if(!history.length){
      list.innerHTML = '<div class="foot-history-empty">' + t('foot.historyEmpty') + '</div>';
      return;
    }
    list.innerHTML = '';
    history.forEach(function(item){
      var row = document.createElement('div');
      row.className = 'foot-history-item';
      var date = new Date(item.date);
      row.innerHTML = '<div class="foot-history-date">' + date.toLocaleDateString() + '</div>' +
        '<div class="foot-history-meta">' +
        item.lengthMm + 'mm · ' + item.widthType + ' · ' + item.arch + ' · ' + item.toe +
        '</div>';
      list.appendChild(row);
    });
  }

  function copySummary(){
    if(!state.results) return;
    var summary = t('foot.shareTemplate')
      .replace('{length}', state.results.lengthMm)
      .replace('{width}', state.results.widthType)
      .replace('{arch}', state.results.arch)
      .replace('{toe}', state.results.toe);

    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(summary).then(function(){
        alert(t('foot.shareDone'));
      }).catch(function(){
        alert(summary);
      });
    } else {
      alert(summary);
    }
  }

  function attachEvents(){
    var startBtn = qs('#foot-start-camera');
    var stopBtn = qs('#foot-stop-camera');
    var captureBtn = qs('#foot-capture-btn');
    var upload = qs('#foot-upload');
    var analyzeBtn = qs('#foot-analyze-btn');
    var resetBtn = qs('#foot-reset');
    var saveBtn = qs('#foot-save');
    var shareBtn = qs('#foot-share');
    var clearHistory = qs('#foot-clear-history');
    var scaleSel = qs('#foot-scale');
    var angleSel = qs('#foot-angle');
    var sideSel = qs('#foot-side');

    if(startBtn) startBtn.addEventListener('click', startCamera);
    if(stopBtn) stopBtn.addEventListener('click', stopCamera);
    if(captureBtn) captureBtn.addEventListener('click', captureFrame);
    if(upload) upload.addEventListener('change', function(e){ loadUpload(e.target.files[0]); });
    if(analyzeBtn) analyzeBtn.addEventListener('click', analyze);
    if(resetBtn) resetBtn.addEventListener('click', resetAll);
    if(saveBtn) saveBtn.addEventListener('click', saveHistory);
    if(shareBtn) shareBtn.addEventListener('click', copySummary);
    if(scaleSel) scaleSel.addEventListener('change', updateCaptureTarget);
    if(angleSel) angleSel.addEventListener('change', function(){
      setCurrentSlot(computeSlotFromSelects(), false);
    });
    if(sideSel) sideSel.addEventListener('change', function(){
      setCurrentSlot(computeSlotFromSelects(), false);
    });
    if(angleSel) angleSel.addEventListener('change', updateCaptureTarget);
    if(sideSel) sideSel.addEventListener('change', updateCaptureTarget);
    if(clearHistory) clearHistory.addEventListener('click', function(){
      localStorage.removeItem('footAnalysisHistory');
      renderHistory();
    });

    document.addEventListener('app:tab', function(e){
      if(e.detail && e.detail.tab !== 'foot'){
        stopCamera();
      }
    });
  }

  function init(){
    attachEvents();
    renderHistory();
    updateProgress(0);
    updateCaptureStatus('foot.captureIdle');
    updateCaptureTarget();
    state.currentSlot = computeSlotFromSelects();
    document.querySelectorAll('.foot-preview-slot').forEach(function(slot){
      slot.addEventListener('click', function(){
        var key = slot.getAttribute('data-slot');
        if(state.captures[key]){ selectPreview(key); }
      });
    });
  }

  if(document.readyState === 'complete' || document.readyState === 'interactive'){
    setTimeout(init, 0);
  } else {
    document.addEventListener('DOMContentLoaded', init, false);
  }
})();
