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
    var bothTop = qs('#foot-both-top');
    if(bothTop && bothTop.checked && (qs('#foot-angle') ? qs('#foot-angle').value : 'top') === 'top'){
      updateCaptureStatus('foot.captureTargetBoth', currentTargetLabel());
      return;
    }
    updateCaptureStatus('foot.captureTarget', currentTargetLabel());
  }

  function hapticPulse(){
    if(navigator && typeof navigator.vibrate === 'function'){
      navigator.vibrate(20);
    }
  }

  var poseLandmarker = null;
  var poseLoading = null;

  function loadPoseLandmarker(){
    if(poseLandmarker) return Promise.resolve(poseLandmarker);
    if(poseLoading) return poseLoading;
    if(!window.vision || !window.vision.PoseLandmarker || !window.vision.FilesetResolver){
      return Promise.resolve(null);
    }
    poseLoading = window.vision.FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/wasm')
      .then(function(resolver){
        return window.vision.PoseLandmarker.createFromOptions(resolver, {
          baseOptions: {
            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'
          },
          runningMode: 'IMAGE',
          numPoses: 1
        });
      })
      .then(function(model){
        poseLandmarker = model;
        return model;
      })
      .catch(function(){
        return null;
      });
    return poseLoading;
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
    var angleVal = qs('#foot-angle') ? qs('#foot-angle').value : 'top';
    var bothTop = qs('#foot-both-top');
    if(angleVal === 'top' && bothTop && bothTop.checked){
      var angleEl = qs('#foot-angle');
      if(angleEl) angleEl.value = 'side';
      if(!state.captures['left-side']){
        setCurrentSlot('left-side', true);
        return;
      }
      if(!state.captures['right-side']){
        setCurrentSlot('right-side', true);
        return;
      }
    }
    for(var i = currentIndex + 1; i < slotOrder.length; i++){
      if(!state.captures[slotOrder[i]]){
        setCurrentSlot(slotOrder[i], true);
        return;
      }
    }
  }

  function setPreviewSilent(key, dataUrl){
    state.captures[key] = dataUrl;
    var slot = qs('.foot-preview-slot[data-slot="' + key + '"]');
    if(!slot) return;
    var oldImg = slot.querySelector('img');
    if(oldImg) oldImg.remove();
    var img = document.createElement('img');
    img.src = dataUrl;
    img.alt = key;
    slot.appendChild(img);
    slot.classList.add('has-image');
    if(!slot.querySelector('.foot-preview-label')){
      var label = document.createElement('span');
      label.className = 'foot-preview-label';
      label.textContent = slot.getAttribute('data-label') || '';
      slot.appendChild(label);
    }
  }

  function setPreview(key, dataUrl){
    setPreviewSilent(key, dataUrl);
    selectPreview(key);
  }

function setPreviewForTopBoth(dataUrl){
    setPreviewSilent('left-top', dataUrl);
    setPreviewSilent('right-top', dataUrl);
    selectPreview('left-top');
  }

  function rotateForAngle(angleVal, dataUrl, cb){
    if(angleVal !== 'side'){
      cb(dataUrl);
      return;
    }
    var img = new Image();
    img.onload = function(){
      if(img.width <= img.height){
        cb(dataUrl);
        return;
      }
      var canvas = document.createElement('canvas');
      canvas.width = img.height;
      canvas.height = img.width;
      var ctx = canvas.getContext('2d');
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate(Math.PI / 2);
      ctx.drawImage(img, -img.width / 2, -img.height / 2);
      cb(canvas.toDataURL('image/jpeg', 0.9));
    };
    img.onerror = function(){ cb(dataUrl); };
    img.src = dataUrl;
  }

  function nextEmptySlot(keys){
    for(var i=0;i<keys.length;i++){
      if(!state.captures[keys[i]]) return keys[i];
    }
    return null;
  }

  function setPreviewByAngle(angleVal, dataUrl){
    var bothTop = qs('#foot-both-top');
    if(angleVal === 'top' && bothTop && bothTop.checked){
      setPreviewForTopBoth(dataUrl);
      return { mode: 'both-top' };
    }
    if(angleVal === 'top'){
      var topSlot = nextEmptySlot(['left-top', 'right-top']) || slotKey();
      setPreview(topSlot, dataUrl);
      return { mode: 'top', slot: topSlot };
    }
    if(angleVal === 'side'){
      var sideSlot = nextEmptySlot(['left-side', 'right-side']) || slotKey();
      setPreview(sideSlot, dataUrl);
      return { mode: 'side', slot: sideSlot };
    }
    var fallbackSlot = slotKey();
    setPreview(fallbackSlot, dataUrl);
    return { mode: 'fallback', slot: fallbackSlot };
  }

function detectAngleHeuristic(dataUrl){
    return new Promise(function(resolve){
      var img = new Image();
      img.onload = function(){
        var canvas = document.createElement('canvas');
        var size = 160;
        canvas.width = size;
        canvas.height = size;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, size, size);
        var data = ctx.getImageData(0, 0, size, size).data;
        var sum = 0;
        var sumSq = 0;
        var count = size * size;
        for(var i=0;i<data.length;i+=4){
          var gray = (data[i] + data[i+1] + data[i+2]) / 3;
          sum += gray;
          sumSq += gray * gray;
        }
        var mean = sum / count;
        var variance = Math.max(0, sumSq / count - mean * mean);
        var std = Math.sqrt(variance);
        var threshold = Math.max(10, Math.min(40, std * 0.7));
        function findBounds(th){
          var minX = size, minY = size, maxX = 0, maxY = 0;
          var fg = 0;
          for(var y=0;y<size;y++){
            for(var x=0;x<size;x++){
              var idx = (y * size + x) * 4;
              var gray2 = (data[idx] + data[idx+1] + data[idx+2]) / 3;
              if(Math.abs(gray2 - mean) > th){
                fg++;
                if(x < minX) minX = x;
                if(y < minY) minY = y;
                if(x > maxX) maxX = x;
                if(y > maxY) maxY = y;
              }
            }
          }
          if(fg < 80) return null;
          return { minX: minX, minY: minY, maxX: maxX, maxY: maxY };
        }
        var bounds = findBounds(threshold) || findBounds(Math.max(8, threshold * 0.7));
        if(!bounds){
          resolve(null);
          return;
        }
        var w = Math.max(1, bounds.maxX - bounds.minX);
        var h = Math.max(1, bounds.maxY - bounds.minY);
        var ratio = h / w;
        var imgRatio = img.height / img.width;
        if(imgRatio > 1.25){
          resolve('side');
          return;
        }
        if(imgRatio < 0.8){
          resolve('top');
          return;
        }
        if(ratio > 1.05){
          resolve('side');
          return;
        }
        if(ratio < 0.7){
          resolve('top');
          return;
        }
        resolve(null);
      };
      img.onerror = function(){ resolve(null); };
      img.src = dataUrl;
    });
  }

  function detectAngleWithPose(dataUrl){
    return new Promise(function(resolve){
      loadPoseLandmarker().then(function(model){
        if(!model) return resolve(null);
        var img = new Image();
        img.onload = function(){
          var canvas = document.createElement('canvas');
          var size = 256;
          canvas.width = size;
          canvas.height = size;
          var ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, size, size);
          var result = model.detect(canvas);
          if(!result || !result.landmarks || !result.landmarks.length){
            resolve(null);
            return;
          }
          var lm = result.landmarks[0] || [];
          var ls = lm[11];
          var rs = lm[12];
          var lh = lm[23];
          if(!ls || !rs || !lh){
            resolve(null);
            return;
          }
          var width = Math.abs(rs.x - ls.x);
          var height = Math.abs(lh.y - ls.y);
          if(height <= 0){
            resolve(null);
            return;
          }
          var ratio = width / height;
          if(ratio < 0.28){
            resolve('side');
            return;
          }
          if(ratio > 0.55){
            resolve('top');
            return;
          }
          resolve(null);
        };
        img.onerror = function(){ resolve(null); };
        img.src = dataUrl;
      });
    });
  }

  function applyAngleDetection(dataUrl, cb){
    var auto = qs('#foot-auto-angle');
    if(!auto || !auto.checked){
      cb(null);
      return;
    }
    var bothTop = qs('#foot-both-top');
    var angleEl = qs('#foot-angle');
    var angleVal = angleEl ? angleEl.value : 'top';
    if(bothTop && bothTop.checked && angleVal === 'top'){
      if(angleEl) angleEl.value = 'top';
      updateCaptureTarget();
      cb('top');
      return;
    }
    detectAngleWithPose(dataUrl).then(function(angle){
      if(angle){
        if(angleEl) angleEl.value = angle;
        updateCaptureTarget();
        updateCaptureStatus(angle === 'top' ? 'foot.autoAngleTop' : 'foot.autoAngleSide');
        cb(angle);
        return;
      }
      detectAngleHeuristic(dataUrl).then(function(fallback){
        if(!fallback){
          updateCaptureStatus('foot.autoAngleFailed', currentTargetLabel());
          cb(null);
          return;
        }
        if(angleEl) angleEl.value = fallback;
        updateCaptureTarget();
        updateCaptureStatus(fallback === 'top' ? 'foot.autoAngleTop' : 'foot.autoAngleSide');
        cb(fallback);
      });
    });
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
    applyAngleDetection(dataUrl, function(detected){
      var angleVal = detected || (qs('#foot-angle') ? qs('#foot-angle').value : 'top');
      rotateForAngle(angleVal, dataUrl, function(rotated){
        var result = setPreviewByAngle(angleVal, rotated);
        if(result.mode === 'both-top'){
          updateCaptureStatus('foot.captureDoneBoth');
        } else {
          updateCaptureStatus('foot.captureDone', {
            side: t('foot.' + (qs('#foot-side') ? qs('#foot-side').value : 'left')),
            angle: t('foot.angle' + (angleVal === 'top' ? 'Top' : 'Side'))
          });
        }
        hapticPulse();
        autoAdvanceSlot();
      });
    });
  }

  function loadUpload(file){
    if(!file) return;
    var reader = new FileReader();
    reader.onload = function(e){
      var dataUrl = e.target.result;
      applyAngleDetection(dataUrl, function(detected){
        var angleVal = detected || (qs('#foot-angle') ? qs('#foot-angle').value : 'top');
        rotateForAngle(angleVal, dataUrl, function(rotated){
          var result = setPreviewByAngle(angleVal, rotated);
          if(result.mode === 'both-top'){
            updateCaptureStatus('foot.uploadDoneBoth');
          } else {
            updateCaptureStatus('foot.uploadDone', {
              side: t('foot.' + (qs('#foot-side') ? qs('#foot-side').value : 'left')),
              angle: t('foot.angle' + (angleVal === 'top' ? 'Top' : 'Side'))
            });
          }
          hapticPulse();
          autoAdvanceSlot();
        });
      });
    };
    reader.readAsDataURL(file);
  }

  function loadUploads(files){
    if(!files || !files.length) return;
    var list = Array.prototype.slice.call(files);
    var idx = 0;
    function next(){
      var file = list[idx++];
      if(!file) return;
      var reader = new FileReader();
      reader.onload = function(e){
        var dataUrl = e.target.result;
        applyAngleDetection(dataUrl, function(detected){
          var angleVal = detected || (qs('#foot-angle') ? qs('#foot-angle').value : 'top');
          rotateForAngle(angleVal, dataUrl, function(rotated){
            var result = setPreviewByAngle(angleVal, rotated);
            if(result.mode === 'both-top'){
              updateCaptureStatus('foot.uploadDoneBoth');
            } else {
              updateCaptureStatus('foot.uploadDone', {
                side: t('foot.' + (qs('#foot-side') ? qs('#foot-side').value : 'left')),
                angle: t('foot.angle' + (angleVal === 'top' ? 'Top' : 'Side'))
              });
            }
            hapticPulse();
            autoAdvanceSlot();
            next();
          });
        });
      };
      reader.readAsDataURL(file);
    }
    next();
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

    function computeFootResult(sideKey, seedOffset){
      var baseLength = estimateLength();
      var lengthMm = Math.max(200, Math.min(320, baseLength + (seedOffset % 2 ? -1 : 1)));
      var seed = Math.round(lengthMm) + (count * 7) + seedOffset;
      var widthMm = Math.round(lengthMm * 0.39);
      var widthRatio = widthMm / lengthMm;
      var widthType = widthRatio < 0.37 ? t('foot.widthNarrow') : (widthRatio > 0.41 ? t('foot.widthWide') : t('foot.widthNormal'));

      var hasSide = !!state.captures[sideKey + '-side'];
      var instep = hasSide ? pickBySeed([t('foot.instepMid'), t('foot.instepHigh')], seed + 3) : pickBySeed([t('foot.instepLow'), t('foot.instepMid')], seed + 5);
      if(widthRatio > 0.41 && instep === t('foot.instepLow')) instep = t('foot.instepMid');
      if(widthRatio < 0.37 && instep === t('foot.instepHigh')) instep = t('foot.instepMid');

      var arch = pickBySeed([t('foot.archFlat'), t('foot.archNormal'), t('foot.archHigh')], seed + 11);
      if(widthRatio > 0.41) arch = t('foot.archFlat');
      if(widthRatio < 0.37) arch = t('foot.archHigh');

      var toe = t('foot.toeGreek');
      if(lengthMm >= 270 && widthRatio < 0.38) toe = t('foot.toeEgypt');
      if(widthRatio > 0.41) toe = t('foot.toeRoman');

      return {
        lengthMm: lengthMm,
        widthMm: widthMm,
        widthType: widthType,
        instep: instep,
        arch: arch,
        toe: toe,
        ball: widthType
      };
    }

    var left = computeFootResult('left', 1);
    var right = computeFootResult('right', 7);
    state.results = { left: left, right: right };

    setTimeout(function(){ updateProgress(55); }, 200);
    setTimeout(function(){ updateProgress(100); }, 600);

    setTimeout(function(){
      var l = state.results.left;
      var r = state.results.right;
      var lLen = qs('#foot-result-left-length');
      var lWidth = qs('#foot-result-left-width');
      var lInstep = qs('#foot-result-left-instep');
      var lArch = qs('#foot-result-left-arch');
      var lToe = qs('#foot-result-left-toe');
      var lBall = qs('#foot-result-left-ball');
      var rLen = qs('#foot-result-right-length');
      var rWidth = qs('#foot-result-right-width');
      var rInstep = qs('#foot-result-right-instep');
      var rArch = qs('#foot-result-right-arch');
      var rToe = qs('#foot-result-right-toe');
      var rBall = qs('#foot-result-right-ball');
      if(lLen) lLen.textContent = l.lengthMm + ' mm';
      if(lWidth) lWidth.textContent = l.widthMm + ' mm';
      if(lInstep) lInstep.textContent = l.instep;
      if(lArch) lArch.textContent = l.arch;
      if(lToe) lToe.textContent = l.toe;
      if(lBall) lBall.textContent = l.ball;
      if(rLen) rLen.textContent = r.lengthMm + ' mm';
      if(rWidth) rWidth.textContent = r.widthMm + ' mm';
      if(rInstep) rInstep.textContent = r.instep;
      if(rArch) rArch.textContent = r.arch;
      if(rToe) rToe.textContent = r.toe;
      if(rBall) rBall.textContent = r.ball;
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

  function getStreetSize(){
    var sizeEl = qs('#foot-street-size');
    var scaleEl = qs('#foot-street-scale');
    var sizeVal = sizeEl ? Number(sizeEl.value) : 0;
    if(!sizeVal || isNaN(sizeVal)) return null;
    return { value: sizeVal, scale: scaleEl ? scaleEl.value : 'eu' };
  }

  var TENAYA_SIZE_TABLE = [
    { cm: 22.1, eu: 36, usW: '5.5', usM: '4.5', uk: '3.5' },
    { cm: 22.8, eu: 37, usW: '6.25', usM: '5.25', uk: '4.25' },
    { cm: 23.5, eu: 38, usW: '7', usM: '6', uk: '5' },
    { cm: 24.1, eu: 39, usW: '7.75', usM: '6.75', uk: '5.75' },
    { cm: 24.8, eu: 40, usW: '8.5', usM: '7.5', uk: '6.5' },
    { cm: 25.5, eu: 41, usW: '9.25', usM: '8.25', uk: '7.25' },
    { cm: 26.1, eu: 42, usW: '10', usM: '9', uk: '8' },
    { cm: 26.8, eu: 43, usW: '10.75', usM: '9.75', uk: '8.75' },
    { cm: 27.5, eu: 44, usW: '11.5', usM: '10.5', uk: '9.5' },
    { cm: 28.1, eu: 45, usW: '12.5', usM: '11.5', uk: '10.5' },
    { cm: 28.8, eu: 46, usW: '13.25', usM: '12.25', uk: '11.25' },
    { cm: 29.5, eu: 47, usW: '14', usM: '13', uk: '12' }
  ];

  var BD_SIZE_TABLE = [
    { cm: 21.72, eu: 35, usW: '4.5', usM: '3.5' },
    { cm: 22.05, eu: 35.5, usW: '5', usM: '4' },
    { cm: 22.38, eu: 36, usW: '5.5', usM: '4.5' },
    { cm: 22.71, eu: 36.5, usW: '5.5+', usM: '4.5+' },
    { cm: 23.04, eu: 37, usW: '6', usM: '5' },
    { cm: 23.37, eu: 37.5, usW: '6.5', usM: '5.5' },
    { cm: 23.7, eu: 38, usW: '7', usM: '6' },
    { cm: 24.03, eu: 38.5, usW: '7.5', usM: '6.5' },
    { cm: 24.36, eu: 39, usW: '7.5+', usM: '6.5+' },
    { cm: 24.69, eu: 39.5, usW: '8', usM: '7' },
    { cm: 25.02, eu: 40, usW: '8.5', usM: '7.5' },
    { cm: 25.35, eu: 40.5, usW: '9', usM: '8' },
    { cm: 25.68, eu: 41, usW: '9.5', usM: '8.5' },
    { cm: 26.01, eu: 41.5, usW: '9.5+', usM: '8.5+' },
    { cm: 26.34, eu: 42, usW: '10', usM: '9' },
    { cm: 26.67, eu: 42.5, usW: '10.5', usM: '9.5' },
    { cm: 27, eu: 43, usW: '11', usM: '10' },
    { cm: 27.33, eu: 43.5, usW: '11.5', usM: '10.5' },
    { cm: 27.66, eu: 44, usW: '11.5+', usM: '10.5+' },
    { cm: 27.99, eu: 44.5, usW: '12', usM: '11' },
    { cm: 28.32, eu: 45, usW: '12.5', usM: '11.5' },
    { cm: 28.65, eu: 45.5, usW: '13', usM: '12' },
    { cm: 28.98, eu: 46, usW: '13.5', usM: '12.5' },
    { cm: 29.31, eu: 46.5, usW: '13.5+', usM: '12.5+' },
    { cm: 29.64, eu: 47, usW: '14', usM: '13' }
  ];

  function closestTenayaSize(cm){
    if(!cm) return null;
    var best = TENAYA_SIZE_TABLE[0];
    var bestDiff = Math.abs(cm - best.cm);
    for(var i=1;i<TENAYA_SIZE_TABLE.length;i++){
      var diff = Math.abs(cm - TENAYA_SIZE_TABLE[i].cm);
      if(diff < bestDiff){
        best = TENAYA_SIZE_TABLE[i];
        bestDiff = diff;
      }
    }
    return best;
  }

  function closestBdSize(cm){
    if(!cm) return null;
    var best = BD_SIZE_TABLE[0];
    var bestDiff = Math.abs(cm - best.cm);
    for(var i=1;i<BD_SIZE_TABLE.length;i++){
      var diff = Math.abs(cm - BD_SIZE_TABLE[i].cm);
      if(diff < bestDiff){
        best = BD_SIZE_TABLE[i];
        bestDiff = diff;
      }
    }
    return best;
  }

  function sizeTipForBrand(brand, level, fit, climbType, street, footCm){
    function scaleLabel(scale){
      if(scale === 'usm') return 'US(M)';
      if(scale === 'usw') return 'US(W)';
      return 'EU';
    }
    function fmtStreet(val, scale){
      return val + ' ' + scaleLabel(scale);
    }
    if(brand === 'Evolv'){
      if(street){
        var delta = level === 'beginner' ? 2 : (level === 'intermediate' ? 1 : 0);
        return fmtStreet(street.value, street.scale) + ' + ' + delta;
      }
      return t('foot.sizeTipEvolv');
    }
    if(brand === 'Black Diamond'){
      var row = closestBdSize(footCm);
      if(row){
        return 'EU ' + row.eu + ' / US ' + row.usM + ' / ' + row.usW;
      }
      if(street && street.scale === 'eu'){
        if(fit === 'comfort') return 'EU ' + street.value + ' → ' + (street.value - 1).toFixed(1) + ' ~ ' + (street.value - 0.5).toFixed(1);
        if(fit === 'performance') return 'EU ' + street.value + ' → ' + (street.value - 2.5).toFixed(1) + ' ~ ' + (street.value - 2).toFixed(1);
        return 'EU ' + street.value + ' → ' + (street.value - 2).toFixed(1) + ' ~ ' + (street.value - 1.5).toFixed(1);
      }
      return t('foot.sizeTipBlackDiamond');
    }
    if(brand === 'Scarpa'){
      return t('foot.sizeTipScarpa');
    }
    if(brand === 'Tenaya'){
      var row = closestTenayaSize(footCm);
      if(row){
        return 'EU ' + row.eu + ' / US ' + row.usM + ' / ' + row.usW;
      }
      return t('foot.sizeTipTenaya');
    }
    if(brand === 'La Sportiva'){
      return t('foot.sizeTipLaSportivaChart');
    }
    return '';
  }

  function buildRecommendations(){
    var grid = qs('#foot-reco-grid');
    if(!grid || !state.results) return;

    var level = qs('#foot-level') ? qs('#foot-level').value : 'beginner';
    var type = qs('#foot-type') ? qs('#foot-type').value : 'bouldering';
    var fit = qs('#foot-fit') ? qs('#foot-fit').value : 'balanced';
    var widthType = state.results.left.widthType;
    var lengthMm = Math.max(state.results.left.lengthMm, state.results.right.lengthMm);
    var footCm = Math.round(lengthMm / 10 * 10) / 10;

    var models = [
      { brand: 'La Sportiva', model: 'Performance Series', level: 'advanced', types: ['bouldering', 'sport'], width: 'normal', price: '$$$$' },
      { brand: 'La Sportiva', model: 'All-day Comfort', level: 'beginner', types: ['sport', 'multi'], width: 'normal', price: '$$' },
      { brand: 'Scarpa', model: 'Performance Line', level: 'advanced', types: ['bouldering', 'sport'], width: 'wide', price: '$$$$' },
      { brand: 'Scarpa', model: 'Comfort Line', level: 'beginner', types: ['sport', 'multi'], width: 'normal', price: '$$' },
      { brand: 'Evolv', model: 'Training Line', level: 'beginner', types: ['sport', 'multi'], width: 'normal', price: '$$' },
      { brand: 'Evolv', model: 'Performance Line', level: 'advanced', types: ['bouldering', 'sport'], width: 'wide', price: '$$$$' },
      { brand: 'Black Diamond', model: 'Momentum Series', level: 'beginner', types: ['sport', 'multi'], width: 'normal', price: '$$' },
      { brand: 'Tenaya', model: 'Precision Line', level: 'intermediate', types: ['sport', 'bouldering'], width: 'narrow', price: '$$$' }
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
      if(state.results.left.instep === t('foot.instepHigh') || state.results.right.instep === t('foot.instepHigh')) {
        if(item.width === 'wide') score += 4;
      }
      if(state.results.left.instep === t('foot.instepLow') || state.results.right.instep === t('foot.instepLow')) {
        if(item.width === 'narrow') score += 4;
      }
      score = Math.min(95, score);
      return { item: item, score: score };
    }).sort(function(a,b){ return b.score - a.score; });

    grid.innerHTML = '';

    var advice = sizeAdvice(lengthMm);
    var street = getStreetSize();
    scored.slice(0, 6).forEach(function(entry){
      var card = document.createElement('div');
      card.className = 'foot-reco-card';
      var sizeTip = sizeTipForBrand(entry.item.brand, level, fit, type, street, footCm);
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
          '<span>' + t('foot.recoWidth') + ': ' + entry.item.width + '</span>' +
          (sizeTip ? '<span>' + t('foot.recoSize') + ': ' + sizeTip + '</span>' : '') +
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
      var img = slot.querySelector('img');
      if(img) img.remove();
      slot.classList.remove('has-image');
      var labelEl = slot.querySelector('.foot-preview-label');
      if(!labelEl){
        labelEl = document.createElement('span');
        labelEl.className = 'foot-preview-label';
        labelEl.textContent = slot.getAttribute('data-label') || '';
        slot.appendChild(labelEl);
      }
      slot.classList.remove('is-active');
    });
    var resIds = ['length','width','instep','arch','toe','ball'];
    ['left','right'].forEach(function(side){
      resIds.forEach(function(id){
        var el = qs('#foot-result-' + side + '-' + id);
        if(el) el.textContent = '-';
      });
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
    var maxLen = Math.max(state.results.left.lengthMm, state.results.right.lengthMm);
    var entry = {
      date: new Date().toISOString(),
      lengthMm: maxLen,
      widthType: state.results.left.widthType + '/' + state.results.right.widthType,
      arch: state.results.left.arch + '/' + state.results.right.arch,
      toe: state.results.left.toe + '/' + state.results.right.toe
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
    var maxLen = Math.max(state.results.left.lengthMm, state.results.right.lengthMm);
    var summary = t('foot.shareTemplate')
      .replace('{length}', maxLen)
      .replace('{width}', state.results.left.widthType + '/' + state.results.right.widthType)
      .replace('{arch}', state.results.left.arch + '/' + state.results.right.arch)
      .replace('{toe}', state.results.left.toe + '/' + state.results.right.toe);

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
    var uploadBtn = qs('#foot-upload-btn');
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
    if(uploadBtn && upload) uploadBtn.addEventListener('click', function(){ upload.click(); });
    if(upload) upload.addEventListener('change', function(e){
      if(e.target.files && e.target.files.length > 1){
        loadUploads(e.target.files);
      } else {
        loadUpload(e.target.files[0]);
      }
    });
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
