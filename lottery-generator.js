(function(){
  'use strict';

  var STORAGE_KEY = 'grind.lotto645.history.v1';
  var SAVED_SETS_STORAGE_KEY = 'grind.lotto645.manualSets.v1';
  var BUNDLED_URL = 'assets/data/lotto-645-history.json?v=20260629-1';
  var MIRROR_ALL_URL = 'https://smok95.github.io/lotto/results/all.json';
  var OFFICIAL_URL = 'https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo=';
  var DRAW_ONE_DATE = new Date(Date.UTC(2002, 11, 7, 12, 0, 0));
  var MS_PER_WEEK = 7 * 24 * 60 * 60 * 1000;
  var BAND_LABELS = ['1-10', '11-20', '21-30', '31-40', '41-45'];
  var BAND_CAPACITIES = [10, 10, 10, 10, 5];
  var DIFFUSION_STEPS = 12;
  var DIFFUSION_SURVIVAL_STEPS = 14;
  var DIFFUSION_ANIMATION_MS = 170;

  var state = {
    history: [],
    source: 'sourceBundled',
    updatedAt: '',
    generated: [],
    seed: 0,
    stats: null,
    isDrawing: false,
    pendingGenerated: [],
    pendingSeed: 0,
    drawSurvivors: [],
    drawRemovalOrder: [],
    drawAssignmentOrder: [],
    diffusionStep: 0,
    diffusionTotal: DIFFUSION_SURVIVAL_STEPS,
    manualSelected: [],
    savedSets: [],
    activeSavedId: '',
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

  function normalizeNumbers(raw){
    if (!Array.isArray(raw)) return [];
    var seen = {};
    var nums = [];
    raw.forEach(function(value){
      var n = Number(value);
      if (!Number.isFinite(n) || Math.floor(n) !== n || n < 1 || n > 45 || seen[n]) return;
      seen[n] = true;
      nums.push(n);
    });
    nums.sort(function(a, b){ return a - b; });
    return nums.length === 6 ? nums : [];
  }

  function keyForNumbers(nums){
    return normalizeNumbers(nums).join(',');
  }

  function makeSavedId(){
    var random = Math.floor(Math.random() * 0xFFFFFF).toString(36);
    return 'manual-' + Date.now().toString(36) + '-' + random;
  }

  function readSavedSets(){
    try {
      var text = localStorage.getItem(SAVED_SETS_STORAGE_KEY);
      if (!text) return [];
      var parsed = JSON.parse(text);
      var list = Array.isArray(parsed) ? parsed : (Array.isArray(parsed.sets) ? parsed.sets : []);
      var seen = {};
      return list.map(function(item){
        var nums = normalizeNumbers(item && item.numbers);
        if (nums.length !== 6) return null;
        var key = nums.join(',');
        if (seen[key]) return null;
        seen[key] = true;
        return {
          id: String((item && item.id) || makeSavedId()),
          numbers: nums,
          createdAt: (item && item.createdAt) || new Date().toISOString()
        };
      }).filter(Boolean);
    } catch (err) {
      return [];
    }
  }

  function saveManualSets(){
    try {
      localStorage.setItem(SAVED_SETS_STORAGE_KEY, JSON.stringify({
        version: 1,
        updatedAt: new Date().toISOString(),
        sets: state.savedSets
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

  function bandIndex(n){
    return Math.min(4, Math.floor((n - 1) / 10));
  }

  function bandProfile(nums){
    var profile = [0, 0, 0, 0, 0];
    nums.forEach(function(n){
      profile[bandIndex(n)] += 1;
    });
    return profile;
  }

  function profileKey(profile){
    return profile.join('-');
  }

  function profileFromKey(key){
    return String(key || '').split('-').map(function(value){ return Number(value) || 0; }).slice(0, 5);
  }

  function validProfile(profile){
    if (!Array.isArray(profile) || profile.length !== 5) return false;
    var total = 0;
    for (var i = 0; i < profile.length; i++) {
      if (profile[i] < 0 || profile[i] > BAND_CAPACITIES[i]) return false;
      total += profile[i];
    }
    return total === 6;
  }

  function profileDistance(a, b){
    var total = 0;
    for (var i = 0; i < 5; i++) total += Math.abs((a[i] || 0) - (b[i] || 0));
    return total;
  }

  function computeStats(history){
    var counts = Array(46).fill(0);
    var recentCounts = Array(46).fill(0);
    var lastSeen = Array(46).fill(0);
    var pairCounts = new Map();
    var profileCounts = new Map();
    var recentProfileCounts = new Map();
    var transitionCounts = new Map();
    var sums = [];
    var latestNo = history.length ? history[history.length - 1].drawNo : 0;
    var recentFloor = Math.max(1, latestNo - 51);
    var previousProfileKey = '';
    var latestProfileKey = '';

    history.forEach(function(draw){
      var nums = draw.numbers;
      var sum = nums.reduce(function(acc, n){ return acc + n; }, 0);
      var currentProfileKey = profileKey(bandProfile(nums));
      sums.push(sum);
      profileCounts.set(currentProfileKey, (profileCounts.get(currentProfileKey) || 0) + 1);
      if (draw.drawNo >= recentFloor) {
        recentProfileCounts.set(currentProfileKey, (recentProfileCounts.get(currentProfileKey) || 0) + 1);
      }
      if (previousProfileKey) {
        var transitionKey = previousProfileKey + '>' + currentProfileKey;
        transitionCounts.set(transitionKey, (transitionCounts.get(transitionKey) || 0) + 1);
      }
      previousProfileKey = currentProfileKey;
      latestProfileKey = currentProfileKey;
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
    var pairValues = Array.from(pairCounts.values());
    var profileValues = Array.from(profileCounts.values());
    return {
      counts: counts,
      recentCounts: recentCounts,
      lastSeen: lastSeen,
      pairCounts: pairCounts,
      profileCounts: profileCounts,
      recentProfileCounts: recentProfileCounts,
      transitionCounts: transitionCounts,
      latestProfileKey: latestProfileKey,
      latestNo: latestNo,
      sumAvg: avg,
      sumLow: percentile(sums, 0.1) || 90,
      sumHigh: percentile(sums, 0.9) || 190,
      maxCount: Math.max.apply(null, counts) || 1,
      maxRecent: Math.max.apply(null, recentCounts) || 1,
      maxPair: pairValues.length ? Math.max.apply(null, pairValues) : 1,
      maxProfile: profileValues.length ? Math.max.apply(null, profileValues) : 1,
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

  function topProfile(stats){
    var bestKey = '';
    var bestScore = -Infinity;
    stats.profileCounts.forEach(function(count, key){
      var recent = stats.recentProfileCounts.get(key) || 0;
      var transition = stats.transitionCounts.get((stats.latestProfileKey || '') + '>' + key) || 0;
      var score = count + recent * 1.15 + transition * 1.35;
      if (score > bestScore) {
        bestScore = score;
        bestKey = key;
      }
    });
    return bestKey ? profileFromKey(bestKey) : [1, 1, 2, 1, 1];
  }

  function pickTargetProfile(stats, rng){
    var entries = [];
    stats.profileCounts.forEach(function(count, key){
      var profile = profileFromKey(key);
      if (!validProfile(profile)) return;
      var recent = stats.recentProfileCounts.get(key) || 0;
      var transition = stats.transitionCounts.get((stats.latestProfileKey || '') + '>' + key) || 0;
      var occupied = profile.filter(function(n){ return n > 0; }).length;
      var spread = occupied >= 4 ? 1.08 : 0.92;
      entries.push({
        profile: profile,
        weight: Math.max(0.05, (count / stats.maxProfile) * 1.15 + recent * 0.38 + transition * 0.5 + spread)
      });
    });
    if (!entries.length) return [1, 1, 2, 1, 1];
    var index = weightedPick(entries, entries.map(function(entry){ return entry.weight; }), rng);
    return entries[index].profile.slice();
  }

  function bandCount(nums, bandNo){
    return nums.filter(function(n){ return bandIndex(n) === bandNo; }).length;
  }

  function numberDenoiseWeight(n, selected, targetProfile, stats, temperature){
    var b = bandIndex(n);
    var inBand = bandCount(selected, b);
    var need = Math.max(0, (targetProfile[b] || 0) - inBand);
    var frequency = stats.counts[n] / stats.maxCount;
    var recent = stats.recentCounts[n] / stats.maxRecent;
    var gap = stats.latestNo && stats.lastSeen[n] ? (stats.latestNo - stats.lastSeen[n]) / stats.maxGap : 0.5;
    var pair = 0;

    selected.forEach(function(other){
      if (other !== n) {
        pair += stats.pairCounts.get(Math.min(n, other) + '-' + Math.max(n, other)) || 0;
      }
    });
    pair = pair / Math.max(1, stats.maxPair * Math.max(1, selected.length - 1));

    var profileFit = need > 0 ? 1.55 : (inBand < (targetProfile[b] || 0) + 1 ? 0.92 : 0.34);
    var centerBias = 1 - Math.abs(n - 23) / 44;
    var noise = Math.max(0, temperature || 0) * 0.32;
    return Math.max(0.03, profileFit + frequency * 0.44 + recent * 0.22 + gap * 0.16 + pair * 0.28 + centerBias * 0.05 + noise);
  }

  function pickRemovalIndex(nums, targetProfile, stats, rng, temperature){
    var weights = nums.map(function(n){
      var b = bandIndex(n);
      var overTarget = bandCount(nums, b) > (targetProfile[b] || 0);
      var keep = numberDenoiseWeight(n, nums.filter(function(x){ return x !== n; }), targetProfile, stats, 0);
      return (overTarget ? 1.8 : 0.42) + (1 / Math.max(0.08, keep)) + rng() * Math.max(0.05, temperature || 0);
    });
    return weightedPick(nums, weights, rng);
  }

  function pickAddition(pool, current, targetProfile, stats, rng, temperature){
    var counts = bandProfile(current);
    var neededBands = [];
    for (var b = 0; b < 5; b++) {
      if (counts[b] < (targetProfile[b] || 0)) neededBands.push(b);
    }
    var scoped = neededBands.length ? pool.filter(function(n){ return neededBands.indexOf(bandIndex(n)) >= 0; }) : pool.slice();
    if (!scoped.length) scoped = pool.slice();
    var weights = scoped.map(function(n){
      return numberDenoiseWeight(n, current, targetProfile, stats, temperature) * (0.72 + rng() * 0.56);
    });
    return scoped[weightedPick(scoped, weights, rng)];
  }

  function denoiseStep(nums, targetProfile, stats, rng, temperature){
    var current = nums.slice().sort(function(a, b){ return a - b; });
    var replacements = temperature > 0.62 ? 2 : 1;
    for (var i = 0; i < replacements; i++) {
      if (!current.length) break;
      var removeIndex = pickRemovalIndex(current, targetProfile, stats, rng, temperature);
      current.splice(removeIndex, 1);
      var pool = [];
      for (var n = 1; n <= 45; n++) {
        if (current.indexOf(n) < 0) pool.push(n);
      }
      var added = pickAddition(pool, current, targetProfile, stats, rng, temperature);
      if (added) current.push(added);
      current.sort(function(a, b){ return a - b; });
    }
    return current;
  }

  function weakestNumber(nums, targetProfile, stats, rng, predicate){
    var scoped = nums.filter(predicate || function(){ return true; });
    if (!scoped.length) scoped = nums.slice();
    scoped.sort(function(a, b){
      var aw = numberDenoiseWeight(a, nums.filter(function(x){ return x !== a; }), targetProfile, stats, 0);
      var bw = numberDenoiseWeight(b, nums.filter(function(x){ return x !== b; }), targetProfile, stats, 0);
      return aw - bw || rng() - 0.5;
    });
    return scoped[0];
  }

  function enforceProfile(nums, targetProfile, stats, rng){
    var current = nums.slice().sort(function(a, b){ return a - b; });
    var counts = bandProfile(current);

    for (var b = 0; b < 5; b++) {
      while (counts[b] > (targetProfile[b] || 0)) {
        var remove = weakestNumber(current, targetProfile, stats, rng, function(n){ return bandIndex(n) === b; });
        current.splice(current.indexOf(remove), 1);
        counts = bandProfile(current);
      }
    }

    for (var bandNo = 0; bandNo < 5; bandNo++) {
      while (counts[bandNo] < (targetProfile[bandNo] || 0)) {
        var pool = [];
        for (var n = 1; n <= 45; n++) {
          if (bandIndex(n) === bandNo && current.indexOf(n) < 0) pool.push(n);
        }
        var added = pickAddition(pool, current, targetProfile, stats, rng, 0);
        if (!added) break;
        current.push(added);
        current.sort(function(a, b){ return a - b; });
        counts = bandProfile(current);
      }
    }

    while (current.length > 6) {
      var weak = weakestNumber(current, targetProfile, stats, rng);
      current.splice(current.indexOf(weak), 1);
    }
    while (current.length < 6) {
      var allPool = [];
      for (var x = 1; x <= 45; x++) {
        if (current.indexOf(x) < 0) allPool.push(x);
      }
      current.push(pickAddition(allPool, current, targetProfile, stats, rng, 0));
      current.sort(function(a, b){ return a - b; });
    }

    return current;
  }

  function diffusionSetScore(nums, targetProfile, stats){
    var profile = bandProfile(nums);
    var key = profileKey(profile);
    var profileMatch = 1 - profileDistance(profile, targetProfile) / 12;
    var profilePrior = (stats.profileCounts.get(key) || 0) / stats.maxProfile;
    var recentPrior = (stats.recentProfileCounts.get(key) || 0) / 52;
    return profileMatch * 0.74 + profilePrior * 0.42 + recentPrior * 0.3;
  }

  function generateDiffusionCandidate(stats, rng){
    var targetProfile = pickTargetProfile(stats, rng);
    var nums = makeRollingNumbers(rng);

    for (var step = DIFFUSION_STEPS; step >= 1; step--) {
      nums = denoiseStep(nums, targetProfile, stats, rng, step / DIFFUSION_STEPS);
    }

    nums = enforceProfile(nums, targetProfile, stats, rng);

    return {
      numbers: nums,
      profile: targetProfile
    };
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

  function buildGeneratedSets(seed){
    if (!state.history.length) return;
    var stats = state.stats || computeStats(state.history);
    stats.historyLength = state.history.length;
    var rng = createRng(seed);
    var candidates = [];
    var seen = new Set();

    for (var i = 0; i < 1400; i++) {
      var result = generateDiffusionCandidate(stats, rng);
      var key = keyFor(result.numbers);
      if (seen.has(key)) continue;
      seen.add(key);
      if (!passesBalance(result.numbers, stats)) continue;
      candidates.push({
        numbers: result.numbers,
        score: scoreSet(result.numbers, stats) * 0.72 + diffusionSetScore(result.numbers, result.profile, stats) * 1.28,
        profile: result.profile
      });
    }

    candidates.sort(function(a, b){ return b.score - a.score; });
    var selected = selectSets(candidates);
    while (selected.length < 5) {
      var fallback = generateDiffusionCandidate(stats, rng);
      selected.push({
        numbers: fallback.numbers,
        score: scoreSet(fallback.numbers, stats) * 0.72 + diffusionSetScore(fallback.numbers, fallback.profile, stats) * 1.28,
        profile: fallback.profile
      });
    }

    return {
      seed: seed,
      sets: selected.slice(0, 5)
    };
  }

  function generateSets(seed){
    var result = buildGeneratedSets(seed || makeSeed());
    if (!result) return;
    state.seed = result.seed;
    state.generated = result.sets;
    setStatus('lottery.status.generated', { count: state.generated.length, draws: state.history.length }, 'ok');
    renderAll();
  }

  function makeRollingNumbers(rng){
    var pool = [];
    for (var n = 1; n <= 45; n++) pool.push(n);
    var nums = [];
    while (nums.length < 6) {
      var roll = typeof rng === 'function' ? rng() : Math.random();
      var index = Math.floor(roll * pool.length);
      nums.push(pool[index]);
      pool.splice(index, 1);
    }
    return nums.sort(function(a, b){ return a - b; });
  }

  function shuffleList(list, rng){
    var items = list.slice();
    for (var i = items.length - 1; i > 0; i--) {
      var j = Math.floor(rng() * (i + 1));
      var tmp = items[i];
      items[i] = items[j];
      items[j] = tmp;
    }
    return items;
  }

  function uniqueNumbersFromSets(sets){
    var seen = {};
    var nums = [];
    (sets || []).forEach(function(item){
      (item.numbers || []).forEach(function(n){
        if (seen[n]) return;
        seen[n] = true;
        nums.push(n);
      });
    });
    return nums.sort(function(a, b){ return a - b; });
  }

  function makeRemovalOrder(survivors, rng){
    var alive = new Set(survivors);
    var removed = [];
    for (var n = 1; n <= 45; n++) {
      if (!alive.has(n)) removed.push(n);
    }
    return shuffleList(removed, rng);
  }

  function makeAssignmentOrder(sets){
    var order = [];
    (sets || []).forEach(function(item, setIndex){
      (item.numbers || []).forEach(function(n, numberIndex){
        order.push({
          setIndex: setIndex,
          numberIndex: numberIndex,
          number: n
        });
      });
    });
    return order;
  }

  function removedCountForStep(){
    if (state.diffusionStep >= DIFFUSION_SURVIVAL_STEPS) return state.drawRemovalOrder.length;
    var progress = Math.max(0, Math.min(1, state.diffusionStep / DIFFUSION_SURVIVAL_STEPS));
    var eased = 1 - Math.pow(1 - progress, 2);
    return Math.floor(state.drawRemovalOrder.length * eased);
  }

  function assignedCountForStep(){
    return Math.max(0, Math.min(state.drawAssignmentOrder.length, state.diffusionStep - DIFFUSION_SURVIVAL_STEPS));
  }

  function startDraw(){
    if (!state.history.length) {
      setStatus('lottery.status.loading', {}, '');
      return;
    }
    if (state.isDrawing) return;

    var seed = makeSeed();
    var result = buildGeneratedSets(seed);
    if (!result || !result.sets.length) {
      setStatus('lottery.status.refreshFailed', {}, 'error');
      return;
    }
    var traceRng = createRng((seed ^ 0x9E3779B9) >>> 0);
    var survivors = uniqueNumbersFromSets(result.sets);

    state.isDrawing = true;
    state.generated = [];
    state.seed = seed;
    state.pendingGenerated = result.sets;
    state.pendingSeed = seed;
    state.drawSurvivors = survivors;
    state.drawRemovalOrder = makeRemovalOrder(survivors, traceRng);
    state.drawAssignmentOrder = makeAssignmentOrder(result.sets);
    state.diffusionStep = 0;
    state.diffusionTotal = DIFFUSION_SURVIVAL_STEPS + state.drawAssignmentOrder.length;
    setStatus('lottery.status.drawing', { step: 0, total: state.diffusionTotal }, '');
    setControlsBusy(true);
    renderAll();

    var index = 0;
    var interval = window.setInterval(function(){
      index += 1;
      state.diffusionStep = Math.min(index, state.diffusionTotal);
      renderResults();
      if (index >= state.diffusionTotal) {
        window.clearInterval(interval);
        state.isDrawing = false;
        setControlsBusy(false);
        state.generated = state.pendingGenerated.slice();
        state.seed = state.pendingSeed;
        state.pendingGenerated = [];
        state.drawSurvivors = [];
        state.drawRemovalOrder = [];
        state.drawAssignmentOrder = [];
        setStatus('lottery.status.generated', { count: state.generated.length, draws: state.history.length }, 'ok');
        renderAll();
      }
    }, DIFFUSION_ANIMATION_MS);
  }

  function band(n){
    return String(bandIndex(n) + 1);
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
    if (el.manualSave) el.manualSave.disabled = state.manualSelected.length !== 6;
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
      renderSavedSets();
    }
  }

  function toggleManualNumber(n){
    if (!Number.isFinite(n) || n < 1 || n > 45) return;
    state.activeSavedId = '';
    var index = state.manualSelected.indexOf(n);
    if (index >= 0) {
      state.manualSelected.splice(index, 1);
    } else if (state.manualSelected.length < 6) {
      state.manualSelected.push(n);
    }
    state.manualSelected.sort(function(a, b){ return a - b; });
    renderManualSelection();
    renderSavedSets();
  }

  function setManualSelection(nums){
    state.manualSelected = normalizeNumbers(nums);
    renderManualSelection();
  }

  function renderSavedSetBalls(container, nums){
    container.textContent = '';
    nums.forEach(function(n){
      container.appendChild(createBall(n, 'lottery-saved-ball'));
    });
  }

  function renderSavedSets(){
    if (!el.manualList) return;
    el.manualList.textContent = '';

    if (!state.savedSets.length) {
      var empty = document.createElement('div');
      empty.className = 'lottery-saved-empty';
      empty.textContent = t('lottery.savedEmpty');
      el.manualList.appendChild(empty);
      return;
    }

    state.savedSets.forEach(function(item){
      var row = document.createElement('div');
      row.className = 'lottery-saved-set';
      row.dataset.setId = item.id;
      row.classList.toggle('is-active', item.id === state.activeSavedId);

      var pick = document.createElement('button');
      pick.type = 'button';
      pick.className = 'lottery-saved-pick';
      pick.dataset.setId = item.id;

      var balls = document.createElement('span');
      balls.className = 'lottery-saved-balls';
      renderSavedSetBalls(balls, item.numbers);
      pick.appendChild(balls);

      var visualize = document.createElement('button');
      visualize.type = 'button';
      visualize.className = 'lottery-secret-btn lottery-saved-visualize';
      visualize.dataset.setId = item.id;
      visualize.textContent = t('lottery.secretSend');
      visualize.hidden = item.id !== state.activeSavedId;

      var remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'lottery-saved-delete';
      remove.dataset.setId = item.id;
      remove.setAttribute('aria-label', t('lottery.deleteSavedAria'));
      remove.title = t('lottery.deleteSavedAria');
      remove.textContent = '×';

      row.appendChild(pick);
      row.appendChild(visualize);
      row.appendChild(remove);
      el.manualList.appendChild(row);
    });
  }

  function saveManualSelection(){
    var nums = normalizeNumbers(state.manualSelected);
    if (nums.length !== 6) {
      setStatus('lottery.status.saveNeedSix', {}, 'error');
      return;
    }

    var key = keyForNumbers(nums);
    var existing = state.savedSets.find(function(item){ return keyForNumbers(item.numbers) === key; });
    if (existing) {
      state.activeSavedId = existing.id;
      setManualSelection(existing.numbers);
      renderSavedSets();
      setStatus('lottery.status.manualDuplicate', {}, 'ok');
      return;
    }

    var saved = {
      id: makeSavedId(),
      numbers: nums,
      createdAt: new Date().toISOString()
    };
    state.savedSets.unshift(saved);
    state.activeSavedId = saved.id;
    saveManualSets();
    renderManualSelection();
    renderSavedSets();
    setStatus('lottery.status.manualSaved', {}, 'ok');
  }

  function activateSavedSet(id){
    var item = state.savedSets.find(function(set){ return set.id === id; });
    if (!item) return;
    state.activeSavedId = item.id;
    setManualSelection(item.numbers);
    renderSavedSets();
  }

  function deleteSavedSet(id){
    var before = state.savedSets.length;
    state.savedSets = state.savedSets.filter(function(item){ return item.id !== id; });
    if (before === state.savedSets.length) return;
    if (state.activeSavedId === id) state.activeSavedId = '';
    saveManualSets();
    renderSavedSets();
    renderManualSelection();
    setStatus('lottery.status.manualDeleted', {}, 'ok');
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
    var item = state.savedSets.find(function(set){ return set.id === state.activeSavedId; });
    if (!item) return;
    var nums = item.numbers.slice();
    activateBreathingTab();
    document.dispatchEvent(new CustomEvent('lottery:vision', { detail: { numbers: nums } }));
    setStatus('lottery.status.secretSent', {}, 'ok');
  }

  function renderDiffusionPool(container){
    var survivors = new Set(state.drawSurvivors);
    var removed = new Set(state.drawRemovalOrder.slice(0, removedCountForStep()));
    for (var n = 1; n <= 45; n++) {
      var ball = createBall(n, 'lottery-pool-ball');
      ball.classList.toggle('is-survivor', survivors.has(n));
      ball.classList.toggle('is-gone', removed.has(n));
      ball.classList.toggle('is-noise', !survivors.has(n) && !removed.has(n));
      ball.classList.toggle('is-locked', survivors.has(n) && state.diffusionStep >= DIFFUSION_SURVIVAL_STEPS);
      container.appendChild(ball);
    }
  }

  function renderDiffusionSets(container){
    var assigned = assignedCountForStep();
    var revealed = new Set();
    state.drawAssignmentOrder.slice(0, assigned).forEach(function(item){
      revealed.add(item.setIndex + '-' + item.numberIndex);
    });

    state.pendingGenerated.forEach(function(item, setIndex){
      var row = document.createElement('div');
      row.className = 'lottery-diffusion-set';

      var label = document.createElement('span');
      label.className = 'lottery-diffusion-set-label';
      label.textContent = String.fromCharCode(65 + setIndex);

      var slots = document.createElement('div');
      slots.className = 'lottery-diffusion-slots';
      item.numbers.forEach(function(n, numberIndex){
        if (revealed.has(setIndex + '-' + numberIndex)) {
          slots.appendChild(createBall(n, 'lottery-diffusion-set-ball'));
        } else {
          var slot = document.createElement('span');
          slot.className = 'lottery-diffusion-slot';
          slot.textContent = '·';
          slots.appendChild(slot);
        }
      });

      row.appendChild(label);
      row.appendChild(slots);
      container.appendChild(row);
    });
  }

  function renderResults(){
    if (!el.results) return;
    el.results.textContent = '';
    if (state.isDrawing) {
      var drawing = document.createElement('div');
      drawing.className = 'lottery-draw-machine lottery-diffusion-machine';

      var stage = document.createElement('div');
      stage.className = 'lottery-diffusion-stage';

      var poolHead = document.createElement('div');
      poolHead.className = 'lottery-diffusion-caption';
      poolHead.textContent = t('lottery.diffusionPool', {
        count: 45 - removedCountForStep()
      });

      var pool = document.createElement('div');
      pool.className = 'lottery-diffusion-pool';
      renderDiffusionPool(pool);

      var sets = document.createElement('div');
      sets.className = 'lottery-diffusion-sets';
      renderDiffusionSets(sets);

      var label = document.createElement('div');
      label.className = 'lottery-diffusion-label';
      label.textContent = t('lottery.diffusionStep', {
        step: state.diffusionStep,
        total: state.diffusionTotal
      });

      var meter = document.createElement('div');
      meter.className = 'lottery-diffusion-meter';
      var fill = document.createElement('span');
      fill.style.width = Math.min(100, Math.max(0, (state.diffusionStep / Math.max(1, state.diffusionTotal)) * 100)) + '%';
      meter.appendChild(fill);

      stage.appendChild(poolHead);
      stage.appendChild(pool);
      stage.appendChild(sets);
      drawing.appendChild(stage);
      drawing.appendChild(meter);
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
    if (el.diffusionProfile) {
      el.diffusionProfile.textContent = '';
      topProfile(state.stats).forEach(function(count, index){
        var segment = document.createElement('span');
        segment.className = 'lottery-diffusion-segment';
        segment.dataset.band = String(index + 1);
        segment.textContent = BAND_LABELS[index] + ' ' + count;
        el.diffusionProfile.appendChild(segment);
      });
    }
    if (el.diffusionMeta) {
      el.diffusionMeta.textContent = t('lottery.diffusionMeta', {
        patterns: state.stats.profileCounts.size,
        steps: DIFFUSION_STEPS
      });
    }
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
    el.manualSave = get('lotteryManualSave');
    el.manualList = get('lotteryManualList');
    el.results = get('lotteryResults');
    el.seedLabel = get('lotterySeedLabel');
    el.dataSource = get('lotteryDataSource');
    el.metricDraws = get('lotteryMetricDraws');
    el.metricLatest = get('lotteryMetricLatest');
    el.metricUpdated = get('lotteryMetricUpdated');
    el.latestDraw = get('lotteryLatestDraw');
    el.hotNumbers = get('lotteryHotNumbers');
    el.recentNumbers = get('lotteryRecentNumbers');
    el.diffusionProfile = get('lotteryDiffusionProfile');
    el.diffusionMeta = get('lotteryDiffusionMeta');
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
    if (el.manualSave) el.manualSave.addEventListener('click', saveManualSelection);
    if (el.manualList) {
      el.manualList.addEventListener('click', function(event){
        var deleteButton = event.target && event.target.closest ? event.target.closest('.lottery-saved-delete') : null;
        if (deleteButton && el.manualList.contains(deleteButton)) {
          deleteSavedSet(deleteButton.dataset.setId);
          return;
        }

        var visualizeButton = event.target && event.target.closest ? event.target.closest('.lottery-saved-visualize') : null;
        if (visualizeButton && el.manualList.contains(visualizeButton)) {
          state.activeSavedId = visualizeButton.dataset.setId || '';
          sendManualVision();
          return;
        }

        var row = event.target && event.target.closest ? event.target.closest('.lottery-saved-set') : null;
        if (row && el.manualList.contains(row)) activateSavedSet(row.dataset.setId);
      });
    }

    state.savedSets = readSavedSets();
    buildManualGrid();
    renderManualSelection();
    renderSavedSets();

    document.addEventListener('app:lang', function(){
      renderAll();
      renderManualSelection();
      renderSavedSets();
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
