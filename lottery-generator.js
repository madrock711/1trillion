(function(){
  'use strict';

  var STORAGE_KEY = 'grind.lotto645.history.v1';
  var VISION_STORAGE_KEY = 'grind.lotto645.vision.v1';
  var BUNDLED_URL = 'assets/data/lotto-645-history.json?v=20260629-1';
  var MIRROR_ALL_URL = 'https://smok95.github.io/lotto/results/all.json';
  var OFFICIAL_URL = 'https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo=';
  var DRAW_ONE_DATE = new Date(Date.UTC(2002, 11, 7, 12, 0, 0));
  var MS_PER_WEEK = 7 * 24 * 60 * 60 * 1000;

  var state = {
    history: [],
    source: 'sourceBundled',
    updatedAt: '',
    generated: [],
    seed: 0,
    stats: null,
    isDrawing: false,
    drawNumbers: [],
    manualSelected: [],
    statusKey: 'lottery.status.loading',
    statusParams: {},
    statusKind: ''
  };

  var el = {};

  function t(key, params){
    var value = window.appI18n && typeof window.appI18n.t === 'function' ? window.appI18n.t(key) : key;
    if (params) {
      Object.keys(params).forEach(function(name){
        value = value.replace(new RegExp('\\{' + name + '\\}', 'g'), String(params[name]));
      });
    }
    return value;
  }

  function get(id){
    return document.getElementById(id);
  }

  function setStatus(key, params, kind){
    state.statusKey = key;
    state.statusParams = params || {};
    state.statusKind = kind || '';
    renderStatus();
  }

  function setControlsBusy(isBusy){
    [el.generate, el.refresh, el.copy].forEach(function(button){
      if (button) button.disabled = !!isBusy;
    });
  }

  function renderStatus(){
    if (!el.status) return;
    el.status.textContent = t(state.statusKey, state.statusParams);
    el.status.classList.toggle('is-error', state.statusKind === 'error');
    el.status.classList.toggle('is-ok', state.statusKind === 'ok');
  }

  function sourceLabel(source){
    return t('lottery.' + (source || 'sourceBundled'));
  }

  function normalizeDraw(raw){
    if (!raw || typeof raw !== 'object') return null;

    var drawNo = Number(raw.draw_no || raw.drwNo || raw.drawNo);
    var numbers = Array.isArray(raw.numbers) ? raw.numbers.slice() : [
      raw.drwtNo1, raw.drwtNo2, raw.drwtNo3, raw.drwtNo4, raw.drwtNo5, raw.drwtNo6
    ];
    numbers = numbers.map(Number).filter(function(n){ return Number.isFinite(n); }).sort(function(a, b){ return a - b; });
    var unique = numbers.filter(function(n, idx){ return numbers.indexOf(n) === idx; });
    if (!Number.isFinite(drawNo) || drawNo < 1 || unique.length !== 6) return null;
    if (unique.some(function(n){ return n < 1 || n > 45; })) return null;

    return {
      drawNo: drawNo,
      numbers: unique,
      bonusNo: Number(raw.bonus_no || raw.bnusNo || raw.bonusNo || 0) || 0,
      date: raw.date || raw.drwNoDate || ''
    };
  }

  function normalizeList(payload){
    if (!payload) return [];
    var list = Array.isArray(payload) ? payload : (Array.isArray(payload.draws) ? payload.draws : []);
    return list.map(normalizeDraw).filter(Boolean).sort(function(a, b){ return a.drawNo - b.drawNo; });
  }

  function mergeHistory(){
    var map = new Map();
    for (var i = 0; i < arguments.length; i++) {
      var list = arguments[i] || [];
      list.forEach(function(draw){
        if (draw && draw.drawNo) map.set(draw.drawNo, draw);
      });
    }
    return Array.from(map.values()).sort(function(a, b){ return a.drawNo - b.drawNo; });
  }

  function readCache(){
    try {
      var text = localStorage.getItem(STORAGE_KEY);
      if (!text) return null;
      var parsed = JSON.parse(text);
      return {
        history: normalizeList(parsed.draws || parsed.history || []),
        updatedAt: parsed.updatedAt || '',
        source: parsed.source || 'sourceCache'
      };
    } catch (err) {
      return null;
    }
  }

  function saveCache(source){
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        version: 1,
        source: source || state.source,
        updatedAt: state.updatedAt,
        draws: state.history
      }));
    } catch (err) {
      /* ignore storage failures */
    }
  }

  function fetchJson(url){
    return fetch(url, { cache: 'no-store' }).then(function(response){
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    });
  }

  function estimateCurrentDrawNo(now){
    var current = now || new Date();
    var utcNoon = Date.UTC(current.getFullYear(), current.getMonth(), current.getDate(), 12, 0, 0);
    var drawNo = Math.floor((utcNoon - DRAW_ONE_DATE.getTime()) / MS_PER_WEEK) + 1;
    return Math.max(1, drawNo);
  }

  function fetchOfficialDraw(drawNo){
    return fetchJson(OFFICIAL_URL + encodeURIComponent(drawNo)).then(function(data){
      if (data.returnValue && data.returnValue !== 'success') throw new Error('Draw not found');
      var draw = normalizeDraw(data);
      if (!draw) throw new Error('Invalid official draw');
      return draw;
    });
  }

  function findOfficialLatest(){
    var expected = estimateCurrentDrawNo(new Date());
    var chain = Promise.reject(new Error('start'));
    [expected + 1, expected, expected - 1, expected - 2, expected - 3].forEach(function(drawNo){
      chain = chain.catch(function(){
        if (drawNo < 1) throw new Error('Invalid draw');
        return fetchOfficialDraw(drawNo);
      });
    });
    return chain;
  }

  function refreshFromOfficial(){
    return findOfficialLatest().then(function(latest){
      var newest = state.history.length ? state.history[state.history.length - 1].drawNo : 0;
      var missing = [];
      for (var drawNo = newest + 1; drawNo <= latest.drawNo; drawNo++) {
        missing.push(drawNo);
      }
      if (!missing.length) return [latest];
      if (missing.length > 24) return [latest];
      return Promise.all(missing.map(fetchOfficialDraw)).then(function(list){
        return mergeHistory([latest], list);
      });
    });
  }

  function refreshFromMirror(){
    return fetchJson(MIRROR_ALL_URL).then(normalizeList);
  }

  function loadBundled(){
    return fetchJson(BUNDLED_URL).then(normalizeList).catch(function(){
      return [];
    });
  }

  function applyHistory(list, source, updatedAt){
    state.history = mergeHistory(state.history, list);
    state.source = source || state.source;
    state.updatedAt = updatedAt || new Date().toISOString();
    state.stats = computeStats(state.history);
    saveCache(state.source);
    renderAll();
  }

  function computeStats(history){
    var counts = Array(46).fill(0);
    var recentCounts = Array(46).fill(0);
    var lastSeen = Array(46).fill(0);
    var pairCounts = new Map();
    var sums = [];
    var latestNo = history.length ? history[history.length - 1].drawNo : 0;
    var recentFloor = Math.max(1, latestNo - 51);

    history.forEach(function(draw){
      var nums = draw.numbers;
      var sum = nums.reduce(function(acc, n){ return acc + n; }, 0);
      sums.push(sum);
      nums.forEach(function(n){
        counts[n] += 1;
        lastSeen[n] = draw.drawNo;
        if (draw.drawNo >= recentFloor) recentCounts[n] += 1;
      });
      for (var i = 0; i < nums.length; i++) {
        for (var j = i + 1; j < nums.length; j++) {
          var key = nums[i] + '-' + nums[j];
          pairCounts.set(key, (pairCounts.get(key) || 0) + 1);
        }
      }
    });

    sums.sort(function(a, b){ return a - b; });
    var avg = sums.length ? sums.reduce(function(acc, n){ return acc + n; }, 0) / sums.length : 138;
    return {
      counts: counts,
      recentCounts: recentCounts,
      lastSeen: lastSeen,
      pairCounts: pairCounts,
      latestNo: latestNo,
      sumAvg: avg,
      sumLow: percentile(sums, 0.1) || 90,
      sumHigh: percentile(sums, 0.9) || 190,
      maxCount: Math.max.apply(null, counts) || 1,
      maxRecent: Math.max.apply(null, recentCounts) || 1,
      maxGap: Math.max(1, latestNo)
    };
  }

  function percentile(sorted, p){
    if (!sorted.length) return 0;
    var index = Math.min(sorted.length - 1, Math.max(0, Math.round((sorted.length - 1) * p)));
    return sorted[index];
  }

  function makeSeed(){
    var array = new Uint32Array(1);
    if (window.crypto && window.crypto.getRandomValues) {
      window.crypto.getRandomValues(array);
      return array[0] || Date.now();
    }
    return Math.floor(Math.random() * 4294967295) || Date.now();
  }

  function createRng(seed){
    var value = seed >>> 0;
    return function(){
      value ^= value << 13;
      value ^= value >>> 17;
      value ^= value << 5;
      return ((value >>> 0) / 4294967296);
    };
  }

  function numberWeight(n, stats){
    var frequency = stats.counts[n] / stats.maxCount;
    var recent = stats.recentCounts[n] / stats.maxRecent;
    var gap = stats.latestNo && stats.lastSeen[n] ? (stats.latestNo - stats.lastSeen[n]) / stats.maxGap : 0.5;
    var centerBias = 1 - Math.abs(n - 23) / 44;
    return 1 + frequency * 0.48 + recent * 0.22 + gap * 0.18 + centerBias * 0.08;
  }

  function weightedPick(pool, weights, rng){
    var total = weights.reduce(function(acc, n){ return acc + n; }, 0);
    var target = rng() * total;
    for (var i = 0; i < pool.length; i++) {
      target -= weights[i];
      if (target <= 0) return i;
    }
    return pool.length - 1;
  }

  function generateCandidate(stats, rng){
    var pool = [];
    for (var n = 1; n <= 45; n++) pool.push(n);
    var picked = [];
    while (picked.length < 6 && pool.length) {
      var weights = pool.map(function(n){ return numberWeight(n, stats); });
      var index = weightedPick(pool, weights, rng);
      picked.push(pool[index]);
      pool.splice(index, 1);
    }
    return picked.sort(function(a, b){ return a - b; });
  }

  function countOdd(nums){
    return nums.filter(function(n){ return n % 2 === 1; }).length;
  }

  function countLow(nums){
    return nums.filter(function(n){ return n <= 22; }).length;
  }

  function maxBucket(nums){
    var buckets = {};
    nums.forEach(function(n){
      var b = Math.floor((n - 1) / 10);
      buckets[b] = (buckets[b] || 0) + 1;
    });
    return Math.max.apply(null, Object.keys(buckets).map(function(k){ return buckets[k]; }));
  }

  function maxRun(nums){
    var best = 1;
    var run = 1;
    for (var i = 1; i < nums.length; i++) {
      if (nums[i] === nums[i - 1] + 1) run += 1;
      else run = 1;
      if (run > best) best = run;
    }
    return best;
  }

  function pairScore(nums, stats){
    var total = 0;
    for (var i = 0; i < nums.length; i++) {
      for (var j = i + 1; j < nums.length; j++) {
        total += stats.pairCounts.get(nums[i] + '-' + nums[j]) || 0;
      }
    }
    return total / Math.max(1, stats.historyLength || 1);
  }

  function scoreSet(nums, stats){
    var sum = nums.reduce(function(acc, n){ return acc + n; }, 0);
    var odd = countOdd(nums);
    var low = countLow(nums);
    var score = 0;

    nums.forEach(function(n){
      score += (stats.counts[n] / stats.maxCount) * 0.38;
      score += (stats.recentCounts[n] / stats.maxRecent) * 0.16;
      var gap = stats.latestNo && stats.lastSeen[n] ? (stats.latestNo - stats.lastSeen[n]) / stats.maxGap : 0.5;
      score += gap * 0.12;
    });

    score += odd === 3 ? 0.38 : (odd === 2 || odd === 4 ? 0.22 : -0.32);
    score += low === 3 ? 0.32 : (low === 2 || low === 4 ? 0.18 : -0.28);
    score += maxBucket(nums) <= 3 ? 0.2 : -0.2;
    score += maxRun(nums) <= 2 ? 0.16 : -0.24;
    score += Math.max(0, 1 - Math.abs(sum - stats.sumAvg) / Math.max(1, stats.sumHigh - stats.sumLow)) * 0.48;
    score += pairScore(nums, stats) * 0.08;

    return score;
  }

  function passesBalance(nums, stats){
    var sum = nums.reduce(function(acc, n){ return acc + n; }, 0);
    var odd = countOdd(nums);
    var low = countLow(nums);
    return odd >= 2 && odd <= 4 &&
      low >= 2 && low <= 4 &&
      sum >= stats.sumLow && sum <= stats.sumHigh &&
      maxBucket(nums) <= 3 &&
      maxRun(nums) <= 3;
  }

  function keyFor(nums){
    return nums.join(',');
  }

  function overlap(a, b){
    var set = new Set(a);
    return b.filter(function(n){ return set.has(n); }).length;
  }

  function selectSets(candidates){
    var selected = [];
    var seen = new Set();
    candidates.forEach(function(candidate){
      if (selected.length >= 5) return;
      var key = keyFor(candidate.numbers);
      if (seen.has(key)) return;
      var similar = selected.some(function(item){ return overlap(item.numbers, candidate.numbers) > 3; });
      if (similar) return;
      seen.add(key);
      selected.push(candidate);
    });
    return selected;
  }

  function generateSets(){
    if (!state.history.length) return;
    var stats = state.stats || computeStats(state.history);
    stats.historyLength = state.history.length;
    var seed = makeSeed();
    var rng = createRng(seed);
    var candidates = [];
    var seen = new Set();

    for (var i = 0; i < 5000; i++) {
      var nums = generateCandidate(stats, rng);
      var key = keyFor(nums);
      if (seen.has(key)) continue;
      seen.add(key);
      if (!passesBalance(nums, stats)) continue;
      candidates.push({
        numbers: nums,
        score: scoreSet(nums, stats)
      });
    }

    candidates.sort(function(a, b){ return b.score - a.score; });
    var selected = selectSets(candidates);
    while (selected.length < 5) {
      var fallback = generateCandidate(stats, rng);
      selected.push({
        numbers: fallback,
        score: scoreSet(fallback, stats)
      });
    }

    state.seed = seed;
    state.generated = selected.slice(0, 5);
    setStatus('lottery.status.generated', { count: state.generated.length, draws: state.history.length }, 'ok');
    renderAll();
  }

  function makeRollingNumbers(){
    var pool = [];
    for (var n = 1; n <= 45; n++) pool.push(n);
    var nums = [];
    while (nums.length < 6) {
      var index = Math.floor(Math.random() * pool.length);
      nums.push(pool[index]);
      pool.splice(index, 1);
    }
    return nums;
  }

  function startDraw(){
    if (!state.history.length) {
      setStatus('lottery.status.loading', {}, '');
      return;
    }
    if (state.isDrawing) return;

    state.isDrawing = true;
    state.generated = [];
    state.seed = 0;
    state.drawNumbers = makeRollingNumbers();
    setStatus('lottery.status.drawing', {}, '');
    setControlsBusy(true);
    renderAll();

    var elapsed = 0;
    var interval = window.setInterval(function(){
      elapsed += 90;
      state.drawNumbers = makeRollingNumbers();
      renderResults();
      if (elapsed >= 1350) {
        window.clearInterval(interval);
        state.isDrawing = false;
        setControlsBusy(false);
        generateSets();
      }
    }, 90);
  }

  function band(n){
    return String(Math.min(5, Math.floor((n - 1) / 10) + 1));
  }

  function createBall(n, className){
    var span = document.createElement('span');
    span.className = className || 'lottery-ball';
    span.dataset.band = band(n);
    span.textContent = String(n);
    return span;
  }

  function renderBalls(container, nums, className){
    if (!container) return;
    container.textContent = '';
    nums.forEach(function(n){
      container.appendChild(createBall(n, className));
    });
  }

  function renderManualSelection(){
    if (el.manualCount) el.manualCount.textContent = state.manualSelected.length + '/6';
    if (el.secretSend) {
      var ready = state.manualSelected.length === 6;
      el.secretSend.hidden = !ready;
      el.secretSend.disabled = !ready;
    }
    if (!el.manualGrid) return;
    var selected = new Set(state.manualSelected);
    el.manualGrid.querySelectorAll('.lottery-manual-number').forEach(function(button){
      var n = Number(button.dataset.number);
      var active = selected.has(n);
      button.classList.toggle('is-selected', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  function buildManualGrid(){
    if (!el.manualGrid || el.manualGrid.children.length) return;
    for (var n = 1; n <= 45; n++) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'lottery-manual-number';
      button.dataset.number = String(n);
      button.dataset.band = band(n);
      button.setAttribute('aria-pressed', 'false');
      button.textContent = String(n);
      el.manualGrid.appendChild(button);
    }
  }

  function setManualOpen(isOpen){
    if (!el.manualPanel) return;
    el.manualPanel.hidden = !isOpen;
    if (el.manualToggle) el.manualToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    if (isOpen) {
      buildManualGrid();
      renderManualSelection();
    }
  }

  function toggleManualNumber(n){
    if (!Number.isFinite(n) || n < 1 || n > 45) return;
    var index = state.manualSelected.indexOf(n);
    if (index >= 0) {
      state.manualSelected.splice(index, 1);
    } else if (state.manualSelected.length < 6) {
      state.manualSelected.push(n);
    }
    state.manualSelected.sort(function(a, b){ return a - b; });
    renderManualSelection();
  }

  function clearManualSelection(){
    state.manualSelected = [];
    renderManualSelection();
  }

  function saveVisionNumbers(nums){
    try {
      localStorage.setItem(VISION_STORAGE_KEY, JSON.stringify({
        version: 1,
        numbers: nums,
        updatedAt: new Date().toISOString()
      }));
    } catch (err) {
      /* ignore storage failures */
    }
  }

  function activateBreathingTab(){
    var tab = document.querySelector('.tab-link[data-tab="breathing"]');
    if (tab && typeof tab.click === 'function') {
      tab.click();
      return;
    }
    var breathing = document.getElementById('breathing');
    if (breathing) {
      document.querySelectorAll('.tab-content').forEach(function(node){ node.classList.remove('active'); });
      breathing.classList.add('active');
    }
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, '', window.location.pathname + '?tab=breathing#breathing');
    }
  }

  function sendManualVision(){
    if (state.manualSelected.length !== 6) return;
    var nums = state.manualSelected.slice().sort(function(a, b){ return a - b; });
    saveVisionNumbers(nums);
    document.dispatchEvent(new CustomEvent('lottery:vision', { detail: { numbers: nums } }));
    setStatus('lottery.status.secretSent', {}, 'ok');
    activateBreathingTab();
  }

  function renderResults(){
    if (!el.results) return;
    el.results.textContent = '';
    if (state.isDrawing) {
      var drawing = document.createElement('div');
      drawing.className = 'lottery-draw-machine';

      var balls = document.createElement('div');
      balls.className = 'lottery-draw-balls';
      (state.drawNumbers.length ? state.drawNumbers : makeRollingNumbers()).forEach(function(n){
        balls.appendChild(createBall(n, 'lottery-draw-ball'));
      });

      var label = document.createElement('div');
      label.textContent = t('lottery.status.drawing');

      drawing.appendChild(balls);
      drawing.appendChild(label);
      el.results.appendChild(drawing);
      if (el.seedLabel) el.seedLabel.textContent = '-';
      return;
    }
    if (!state.generated.length) {
      var empty = document.createElement('div');
      empty.className = 'lottery-empty';
      empty.textContent = t('lottery.empty');
      el.results.appendChild(empty);
      if (el.seedLabel) el.seedLabel.textContent = '-';
      return;
    }
    state.generated.forEach(function(item, index){
      var row = document.createElement('div');
      row.className = 'lottery-set';

      var label = document.createElement('span');
      label.className = 'lottery-set-index';
      label.textContent = String.fromCharCode(65 + index);

      var balls = document.createElement('div');
      balls.className = 'lottery-balls';
      renderBalls(balls, item.numbers, 'lottery-ball');

      var score = document.createElement('span');
      score.className = 'lottery-set-score';
      score.textContent = t('lottery.scoreLabel', { score: item.score.toFixed(2) });

      row.appendChild(label);
      row.appendChild(balls);
      row.appendChild(score);
      el.results.appendChild(row);
    });
    if (el.seedLabel) {
      el.seedLabel.textContent = state.seed ? t('lottery.seedLabel', { seed: state.seed }) : '-';
    }
  }

  function formatDate(value){
    if (!value) return '-';
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 10);
    return date.toLocaleDateString(document.documentElement.lang || 'ko', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  }

  function formatDateTime(value){
    if (!value) return '-';
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleString(document.documentElement.lang || 'ko', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function renderData(){
    var latest = state.history.length ? state.history[state.history.length - 1] : null;
    if (el.metricDraws) el.metricDraws.textContent = state.history.length ? String(state.history.length) : '-';
    if (el.metricLatest) el.metricLatest.textContent = latest ? ('#' + latest.drawNo) : '-';
    if (el.metricUpdated) el.metricUpdated.textContent = formatDateTime(state.updatedAt);
    if (el.dataSource) el.dataSource.textContent = sourceLabel(state.source);

    if (el.latestDraw) {
      el.latestDraw.textContent = '';
      if (latest) {
        var text = document.createElement('div');
        text.textContent = t('lottery.latestPrefix') + ' #' + latest.drawNo + ' (' + formatDate(latest.date) + ')';
        var balls = document.createElement('div');
        balls.className = 'lottery-balls';
        renderBalls(balls, latest.numbers, 'lottery-ball');
        el.latestDraw.appendChild(text);
        el.latestDraw.appendChild(balls);
      }
    }
  }

  function topNumbers(counts, limit){
    var list = [];
    for (var n = 1; n <= 45; n++) list.push({ number: n, count: counts[n] || 0 });
    list.sort(function(a, b){ return b.count - a.count || a.number - b.number; });
    return list.slice(0, limit).map(function(item){ return item.number; });
  }

  function renderAnalysis(){
    if (!state.stats) return;
    renderBalls(el.hotNumbers, topNumbers(state.stats.counts, 8), 'lottery-chip');
    renderBalls(el.recentNumbers, topNumbers(state.stats.recentCounts, 8), 'lottery-chip');
  }

  function renderAll(){
    renderStatus();
    renderResults();
    renderData();
    renderAnalysis();
  }

  function copyResults(){
    if (!state.generated.length) {
      setStatus('lottery.status.copyEmpty', {}, 'error');
      return;
    }
    var text = state.generated.map(function(item, index){
      return String.fromCharCode(65 + index) + ': ' + item.numbers.join(', ');
    }).join('\n');

    function done(ok){
      setStatus(ok ? 'lottery.status.copyDone' : 'share.toast.error', {}, ok ? 'ok' : 'error');
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function(){ done(true); }).catch(function(){ done(false); });
      return;
    }

    var textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      done(document.execCommand('copy'));
    } catch (err) {
      done(false);
    }
    document.body.removeChild(textarea);
  }

  function refreshHistory(){
    setStatus('lottery.status.refreshing', {}, '');
    if (el.refresh) el.refresh.disabled = true;

    refreshFromOfficial()
      .then(function(list){
        applyHistory(list, 'sourceOfficial', new Date().toISOString());
        var latest = state.history[state.history.length - 1];
        setStatus('lottery.status.refreshed', { draw: latest.drawNo, draws: state.history.length }, 'ok');
      })
      .catch(function(){
        return refreshFromMirror().then(function(list){
          applyHistory(list, 'sourceMirror', new Date().toISOString());
          var latest = state.history[state.history.length - 1];
          setStatus('lottery.status.refreshed', { draw: latest.drawNo, draws: state.history.length }, 'ok');
        });
      })
      .catch(function(){
        setStatus('lottery.status.refreshFailed', {}, 'error');
      })
      .finally(function(){
        if (el.refresh) el.refresh.disabled = false;
      });
  }

  function initElements(){
    el.status = get('lotteryStatus');
    el.generate = get('lotteryGenerate');
    el.refresh = get('lotteryRefresh');
    el.copy = get('lotteryCopy');
    el.manualToggle = get('lotteryManualToggle');
    el.manualPanel = get('lotteryManual');
    el.manualGrid = get('lotteryManualGrid');
    el.manualCount = get('lotteryManualCount');
    el.manualClear = get('lotteryManualClear');
    el.secretSend = get('lotterySecretSend');
    el.results = get('lotteryResults');
    el.seedLabel = get('lotterySeedLabel');
    el.dataSource = get('lotteryDataSource');
    el.metricDraws = get('lotteryMetricDraws');
    el.metricLatest = get('lotteryMetricLatest');
    el.metricUpdated = get('lotteryMetricUpdated');
    el.latestDraw = get('lotteryLatestDraw');
    el.hotNumbers = get('lotteryHotNumbers');
    el.recentNumbers = get('lotteryRecentNumbers');
  }

  function init(){
    if (!get('lottery')) return;
    initElements();

    if (el.generate) el.generate.addEventListener('click', startDraw);
    if (el.refresh) el.refresh.addEventListener('click', refreshHistory);
    if (el.copy) el.copy.addEventListener('click', copyResults);
    if (el.manualToggle) {
      el.manualToggle.addEventListener('click', function(){
        setManualOpen(el.manualPanel ? el.manualPanel.hidden : false);
      });
    }
    if (el.manualGrid) {
      el.manualGrid.addEventListener('click', function(event){
        var button = event.target && event.target.closest ? event.target.closest('.lottery-manual-number') : null;
        if (!button || !el.manualGrid.contains(button)) return;
        toggleManualNumber(Number(button.dataset.number));
      });
    }
    if (el.manualClear) el.manualClear.addEventListener('click', clearManualSelection);
    if (el.secretSend) el.secretSend.addEventListener('click', sendManualVision);

    buildManualGrid();
    renderManualSelection();

    document.addEventListener('app:lang', function(){
      renderAll();
      renderManualSelection();
    });

    var cache = readCache();
    if (cache && cache.history.length) {
      applyHistory(cache.history, 'sourceCache', cache.updatedAt || new Date().toISOString());
      setStatus('lottery.status.ready', { source: sourceLabel('sourceCache') }, 'ok');
    }

    loadBundled().then(function(list){
      if (!list.length && state.history.length) return;
      if (list.length) {
        var source = state.history.length ? state.source : 'sourceBundled';
        applyHistory(list, source, state.updatedAt || new Date().toISOString());
        setStatus('lottery.status.ready', { source: sourceLabel(source) }, 'ok');
      }
    }).catch(function(){
      if (!state.history.length) setStatus('lottery.status.refreshFailed', {}, 'error');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
