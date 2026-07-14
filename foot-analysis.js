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
    return { mode: t('foot.captureAutoTarget') };
  }

  function updateCaptureTarget(){
    updateCaptureStatus('foot.captureAutoTarget');
  }

  function hapticPulse(){
    if(navigator && typeof navigator.vibrate === 'function'){
      navigator.vibrate(20);
    }
  }

  var poseLandmarker = null;
  var poseLoading = null;

  function loadVisionModule(){
    if(window._visionModule) return Promise.resolve(window._visionModule);
    return import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21/+esm')
      .then(function(mod){
        window._visionModule = mod;
        return mod;
      })
      .catch(function(){
        return null;
      });
  }

  function loadPoseLandmarker(){
    if(poseLandmarker) return Promise.resolve(poseLandmarker);
    if(poseLoading) return poseLoading;
    poseLoading = loadVisionModule().then(function(vision){
      if(!vision || !vision.PoseLandmarker || !vision.FilesetResolver){
        return null;
      }
      return vision.FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21/wasm')
        .then(function(resolver){
          return vision.PoseLandmarker.createFromOptions(resolver, {
            baseOptions: {
              modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'
            },
            runningMode: 'IMAGE',
            numPoses: 1
          });
        });
    }).then(function(model){
      if(!model) return null;
      poseLandmarker = model;
      return model;
    }).catch(function(){
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
    for(var i=0;i<slotOrder.length;i++){
      if(!state.captures[slotOrder[i]]) return slotOrder[i];
    }
    return 'left-top';
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
  }

  function setPreview(key, dataUrl){
    setPreviewSilent(key, dataUrl);
    selectPreview(key);
  }

  function normalizeAngleByMeta(angleVal, meta){
    if(meta && meta.bothFeet) return 'top';
    return angleVal;
  }

  function rotateForAngle(angleVal, dataUrl, meta, cb){
    cb(dataUrl);
  }

  function detectAngleByAspect(dataUrl){
    return new Promise(function(resolve){
      var img = new Image();
      img.onload = function(){
        resolve(null);
      };
      img.onerror = function(){ resolve(null); };
      img.src = dataUrl;
    });
  }

  function fileToDataUrl(file, cb){
    if(!file){
      cb(null);
      return;
    }
    if(window.createImageBitmap){
      createImageBitmap(file, { imageOrientation: 'none' }).then(function(bitmap){
        var canvas = document.createElement('canvas');
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(bitmap, 0, 0);
        cb(canvas.toDataURL('image/jpeg', 0.9));
      }).catch(function(){
        var reader = new FileReader();
        reader.onload = function(e){ cb(e.target.result); };
        reader.readAsDataURL(file);
      });
      return;
    }
    var reader = new FileReader();
    reader.onload = function(e){ cb(e.target.result); };
    reader.readAsDataURL(file);
  }

  function detectAngleOnly(dataUrl){
    return detectAngleHeuristic(dataUrl).then(function(result){
      if(result && result.angle) return result;
      return detectAngleByAspect(dataUrl).then(function(fallback){
        if(!fallback || !fallback.angle) return null;
        return fallback;
      });
    });
  }

  function detectSideFoot(dataUrl){
    return new Promise(function(resolve){
      var img = new Image();
      img.onload = function(){
        var size = 160;
        var canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, size, size);
        var data = ctx.getImageData(0, 0, size, size).data;
        var sum = 0;
        var count = size * size;
        for(var i=0;i<data.length;i+=4){
          sum += (data[i] + data[i+1] + data[i+2]) / 3;
        }
        var mean = sum / count;
        var threshold = 18;
        var minX = size, minY = size, maxX = 0, maxY = 0;
        for(var y=0;y<size;y++){
          for(var x=0;x<size;x++){
            var idx = (y * size + x) * 4;
            var g = (data[idx] + data[idx+1] + data[idx+2]) / 3;
            if(Math.abs(g - mean) > threshold){
              if(x < minX) minX = x;
              if(y < minY) minY = y;
              if(x > maxX) maxX = x;
              if(y > maxY) maxY = y;
            }
          }
        }
        if(maxX <= minX || maxY <= minY){
          resolve(null);
          return;
        }
        var h = Math.max(1, maxY - minY);
        var upperEnd = minY + Math.floor(h * 0.42);
        var lowerStart = maxY - Math.floor(h * 0.42);
        var upperX = 0, upperN = 0;
        var lowerX = 0, lowerN = 0;
        for(var y=minY;y<=maxY;y++){
          for(var x=minX;x<=maxX;x++){
            var idx2 = (y * size + x) * 4;
            var g2 = (data[idx2] + data[idx2+1] + data[idx2+2]) / 3;
            if(Math.abs(g2 - mean) <= threshold) continue;
            if(y <= upperEnd){
              upperX += x;
              upperN++;
            }
            if(y >= lowerStart){
              lowerX += x;
              lowerN++;
            }
          }
        }
        if(upperN < 25 || lowerN < 25){
          resolve(null);
          return;
        }
        var upperCx = upperX / upperN;
        var lowerCx = lowerX / lowerN;
        var delta = upperCx - lowerCx;
        if(Math.abs(delta) >= 2){
          // Toe mass shifts opposite to ankle direction in these side-shot captures.
          resolve(delta > 0 ? 'left' : 'right');
          return;
        }
        // Fallback: compare top-region mass on left/right halves.
        var topLimit = minY + Math.floor(h * 0.45);
        var midX = (minX + maxX) / 2;
        var leftCount = 0;
        var rightCount = 0;
        for(var yy=minY;yy<=topLimit;yy++){
          for(var xx=minX;xx<=maxX;xx++){
            var idx3 = (yy * size + xx) * 4;
            var g3 = (data[idx3] + data[idx3+1] + data[idx3+2]) / 3;
            if(Math.abs(g3 - mean) > threshold){
              if(xx < midX) leftCount++;
              else rightCount++;
            }
          }
        }
        if(leftCount === rightCount){
          resolve(null);
          return;
        }
        var toeSide = leftCount > rightCount ? 'left' : 'right';
        var footSide = toeSide === 'left' ? 'right' : 'left';
        resolve(footSide);
      };
      img.onerror = function(){ resolve(null); };
      img.src = dataUrl;
    });
  }

  function detectBothFeetTop(dataUrl){
    return new Promise(function(resolve){
      var img = new Image();
      img.onload = function(){
        var size = 180;
        var canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, size, size);
        var data = ctx.getImageData(0, 0, size, size).data;
        var count = size * size;
        var sum = 0;
        for(var i=0;i<data.length;i+=4){
          sum += (data[i] + data[i+1] + data[i+2]) / 3;
        }
        var mean = sum / count;
        var threshold = 16;
        var minX = size, minY = size, maxX = 0, maxY = 0;
        for(var y=0;y<size;y++){
          for(var x=0;x<size;x++){
            var idx = (y * size + x) * 4;
            var g = (data[idx] + data[idx+1] + data[idx+2]) / 3;
            if(Math.abs(g - mean) > threshold){
              if(x < minX) minX = x;
              if(y < minY) minY = y;
              if(x > maxX) maxX = x;
              if(y > maxY) maxY = y;
            }
          }
        }
        if(maxX <= minX || maxY <= minY){
          resolve(false);
          return;
        }
        var h = Math.max(1, maxY - minY);
        var yStart = minY + Math.floor(h * 0.35);
        var xStart = minX;
        var xEnd = maxX;
        var w = Math.max(1, xEnd - xStart);
        var leftMass = 0;
        var rightMass = 0;
        var centerMass = 0;
        var fgCount = 0;
        for(var yy=yStart;yy<=maxY;yy++){
          for(var xx=xStart;xx<=xEnd;xx++){
            var idx2 = (yy * size + xx) * 4;
            var g2 = (data[idx2] + data[idx2+1] + data[idx2+2]) / 3;
            if(Math.abs(g2 - mean) <= threshold) continue;
            fgCount++;
            var rel = (xx - xStart) / w;
            if(rel < 0.42){
              leftMass++;
            } else if(rel > 0.58){
              rightMass++;
            } else {
              centerMass++;
            }
          }
        }
        if(fgCount < 220){
          resolve(false);
          return;
        }
        var minSide = Math.min(leftMass, rightMass);
        var maxSide = Math.max(leftMass, rightMass);
        var spreadWide = w > size * 0.45;
        var bothSidesStrong = leftMass > fgCount * 0.28 && rightMass > fgCount * 0.28;
        var centerGap = centerMass < minSide * 0.70;
        var notTooBiased = maxSide === 0 ? false : (minSide / maxSide) > 0.55;
        resolve(spreadWide && bothSidesStrong && centerGap && notTooBiased);
      };
      img.onerror = function(){ resolve(false); };
      img.src = dataUrl;
    });
  }

  function resolveAutoPlacement(dataUrl, detected, info){
    return new Promise(function(resolve){
      var meta = info || {};
      var angleVal = normalizeAngleByMeta((meta.angle || detected || 'top'), meta);
      if(meta.bothFeet){
        resolve({ angle: 'top', meta: meta });
        return;
      }
      var sideLikely = angleVal === 'side' || (typeof meta.ratio === 'number' && meta.ratio >= 1.0);
      if(sideLikely){
        detectSideFoot(dataUrl).then(function(sideFoot){
          if(sideFoot){
            meta.footSide = sideFoot;
            resolve({ angle: 'side', meta: meta });
            return;
          }
          // If heuristic strongly says side, prefer side even when left/right is uncertain.
          if(angleVal === 'side' || (typeof meta.ratio === 'number' && meta.ratio > 1.08)){
            resolve({ angle: 'side', meta: meta });
            return;
          }
          resolve({ angle: 'top', meta: meta });
        });
        return;
      }
      detectBothFeetTop(dataUrl).then(function(isBothTop){
        if(isBothTop){
          meta.bothFeet = true;
          meta.footSide = null;
          resolve({ angle: 'top', meta: meta });
          return;
        }
        detectSideFoot(dataUrl).then(function(sideFoot){
          if(sideFoot){
            meta.footSide = sideFoot;
            resolve({ angle: 'side', meta: meta });
            return;
          }
          resolve({ angle: 'top', meta: meta });
        });
      });
    });
  }

  function nextEmptySlot(keys){
    for(var i=0;i<keys.length;i++){
      if(!state.captures[keys[i]]) return keys[i];
    }
    return null;
  }

  function setPreviewByAngle(angleVal, dataUrl, meta){
    if(angleVal === 'top'){
      var topSlot = nextEmptySlot(['left-top', 'right-top']) || 'left-top';
      setPreview(topSlot, dataUrl);
      return { mode: 'top', slot: topSlot };
    }
    if(angleVal === 'side'){
      var preferred = meta && meta.footSide ? (meta.footSide === 'right' ? 'right-side' : 'left-side') : null;
      var sideSlot = null;
      if(preferred && !state.captures[preferred]){
        sideSlot = preferred;
      } else {
        sideSlot = nextEmptySlot(['left-side', 'right-side']);
      }
      if(!sideSlot && preferred){
        sideSlot = preferred;
      }
      if(!sideSlot){
        sideSlot = preferred || 'left-side';
      }
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
        function countComponents(th){
          var mask = new Uint8Array(count);
          for(var p=0, idx=0;p<data.length;p+=4, idx++){
            var g = (data[p] + data[p+1] + data[p+2]) / 3;
            var y = Math.floor(idx / size);
            if(y < size * 0.18) continue;
            if(Math.abs(g - mean) > th) mask[idx] = 1;
          }
          var visited = new Uint8Array(count);
          var components = 0;
          var minArea = 520;
          var large = [];
          for(var y=0;y<size;y++){
            for(var x=0;x<size;x++){
              var pos = y * size + x;
              if(!mask[pos] || visited[pos]) continue;
              var stack = [pos];
              visited[pos] = 1;
              var area = 0;
              var sumX = 0;
              var sumY = 0;
              var minX = size;
              var maxX = 0;
              while(stack.length){
                var cur = stack.pop();
                area++;
                var cy = (cur / size) | 0;
                var cx = cur - cy * size;
                sumX += cx;
                sumY += cy;
                if(cx < minX) minX = cx;
                if(cx > maxX) maxX = cx;
                var cy = (cur / size) | 0;
                var cx = cur - cy * size;
                var n;
                if(cx > 0){ n = cur - 1; if(mask[n] && !visited[n]){ visited[n]=1; stack.push(n);} }
                if(cx < size - 1){ n = cur + 1; if(mask[n] && !visited[n]){ visited[n]=1; stack.push(n);} }
                if(cy > 0){ n = cur - size; if(mask[n] && !visited[n]){ visited[n]=1; stack.push(n);} }
                if(cy < size - 1){ n = cur + size; if(mask[n] && !visited[n]){ visited[n]=1; stack.push(n);} }
              }
              if(area >= minArea){
                components++;
                large.push({ area: area, cx: sumX / area, cy: sumY / area, minX: minX, maxX: maxX });
              }
            }
          }
          return { count: components, large: large };
        }
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
        var comp = countComponents(threshold);
        var components = comp.count;
        var bothFeet = false;
        if(components >= 2 && comp.large.length >= 2){
          var sorted = comp.large.slice().sort(function(a, b){ return b.area - a.area; });
          var a = sorted[0];
          var b = sorted[1];
          var dx = Math.abs(a.cx - b.cx);
          var bothLow = Math.min(a.cy, b.cy) > size * 0.25;
          var minPairX = Math.min(a.minX, b.minX);
          var maxPairX = Math.max(a.maxX, b.maxX);
          var pairWidth = Math.max(1, maxPairX - minPairX);
          var pairHeight = Math.max(1, Math.max(a.cy, b.cy) - Math.min(a.cy, b.cy) + Math.sqrt(Math.max(a.area, b.area)));
          var pairWide = (pairWidth / pairHeight) > 1.05;
          if(dx > size * 0.14 && bothLow && pairWide){
            bothFeet = true;
          }
        }
        if(bothFeet){
          resolve({ angle: 'top', conf: 0.9, components: components, imgRatio: img.height / img.width, ratio: 0.6, bothFeet: true });
          return;
        }
        var w = Math.max(1, bounds.maxX - bounds.minX);
        var h = Math.max(1, bounds.maxY - bounds.minY);
        var ratio = h / w;
        var imgRatio = img.height / img.width;
        if(components === 1 && imgRatio > 1.25){
          resolve({ angle: 'side', conf: 0.6, components: components, imgRatio: imgRatio, ratio: ratio, bothFeet: false });
          return;
        }
        if(components === 1 && imgRatio < 0.8){
          resolve({ angle: 'top', conf: 0.6, components: components, imgRatio: imgRatio, ratio: ratio, bothFeet: false });
          return;
        }
        if(components === 1 && ratio > 1.08){
          resolve({ angle: 'side', conf: 0.55, components: components, imgRatio: imgRatio, ratio: ratio, bothFeet: false });
          return;
        }
        if(components === 1 && ratio < 0.65){
          resolve({ angle: 'top', conf: 0.55, components: components, imgRatio: imgRatio, ratio: ratio, bothFeet: false });
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
          if(ratio < 0.22){
            resolve({ angle: 'side', conf: 0.75, ratio: ratio, bothFeet: false });
            return;
          }
          if(ratio > 0.62){
            resolve({ angle: 'top', conf: 0.75, ratio: ratio, bothFeet: false });
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
    detectAngleOnly(dataUrl).then(function(result){
      if(!result || !result.angle || result.conf < 0.55){
        updateCaptureStatus('foot.autoAngleFailed', currentTargetLabel());
        cb(null);
        return;
      }
      if(angleEl) angleEl.value = result.angle;
      updateCaptureTarget();
      updateCaptureStatus(result.angle === 'top' ? 'foot.autoAngleTop' : 'foot.autoAngleSide');
      cb(result.angle);
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
      detectAngleOnly(dataUrl).then(function(info){
        resolveAutoPlacement(dataUrl, detected, info).then(function(resolved){
          var meta = resolved.meta || {};
          var angleVal = resolved.angle || 'top';
          rotateForAngle(angleVal, dataUrl, meta, function(rotated){
            var result = setPreviewByAngle(angleVal, rotated, meta);
            if(result.mode === 'both-top'){
              updateCaptureStatus('foot.captureDoneBoth');
            } else {
              updateCaptureStatus('foot.captureDone', {
                side: t('foot.' + (meta.footSide || 'left')),
                angle: t('foot.angle' + (angleVal === 'top' ? 'Top' : 'Side'))
              });
            }
            hapticPulse();
            autoAdvanceSlot();
          });
        });
      });
    });
  }

  function loadUpload(file){
    if(!file) return;
    fileToDataUrl(file, function(dataUrl){
      if(!dataUrl) return;
      applyAngleDetection(dataUrl, function(detected){
        detectAngleOnly(dataUrl).then(function(info){
          resolveAutoPlacement(dataUrl, detected, info).then(function(resolved){
            var meta = resolved.meta || {};
            var angleVal = resolved.angle || 'top';
            rotateForAngle(angleVal, dataUrl, meta, function(rotated){
              var result = setPreviewByAngle(angleVal, rotated, meta);
              if(result.mode === 'both-top'){
                updateCaptureStatus('foot.uploadDoneBoth');
              } else {
                updateCaptureStatus('foot.uploadDone', {
                  side: t('foot.' + (meta.footSide || 'left')),
                  angle: t('foot.angle' + (angleVal === 'top' ? 'Top' : 'Side'))
                });
              }
              hapticPulse();
              autoAdvanceSlot();
            });
          });
        });
      });
    });
  }

  function loadUploads(files){
    if(!files || !files.length) return;
    var list = Array.prototype.slice.call(files);
    var auto = qs('#foot-auto-angle');
    if(!auto || !auto.checked){
      var idx = 0;
      function next(){
        var file = list[idx++];
        if(!file) return;
        fileToDataUrl(file, function(dataUrl){
          if(!dataUrl) return next();
          detectAngleOnly(dataUrl).then(function(info){
            resolveAutoPlacement(dataUrl, null, info).then(function(resolved){
              var angleVal = resolved.angle || 'top';
              var meta = resolved.meta || {};
              rotateForAngle(angleVal, dataUrl, meta, function(rotated){
                var result = setPreviewByAngle(angleVal, rotated, meta);
                if(result.mode === 'both-top'){
                  updateCaptureStatus('foot.uploadDoneBoth');
                } else {
                  updateCaptureStatus('foot.uploadDone', {
                    side: t('foot.' + (meta.footSide || 'left')),
                    angle: t('foot.angle' + (angleVal === 'top' ? 'Top' : 'Side'))
                  });
                }
                hapticPulse();
                autoAdvanceSlot();
                next();
              });
            });
          });
        });
      }
      next();
      return;
    }
    function scoreTopCandidate(item){
      if(!item) return -999;
      var info = item.info || {};
      var score = 0;
      if(info.bothFeet) score += 1000;
      if(typeof info.components === 'number' && info.components >= 2) score += 180;
      if(item.angle === 'top') score += 90;
      if(item.angle === 'side') score -= 120;
      if(info.footSide) score -= 140;
      if(typeof info.ratio === 'number'){
        if(info.ratio < 0.9){
          score += Math.round((0.9 - info.ratio) * 220);
        } else if(info.ratio > 1.08){
          score -= 120;
        }
      }
      return score;
    }

    Promise.all(list.map(function(file){
      return new Promise(function(resolve){
        fileToDataUrl(file, function(dataUrl){
          if(!dataUrl) return resolve(null);
          detectAngleOnly(dataUrl).then(function(info){
            resolveAutoPlacement(dataUrl, null, info).then(function(resolved){
              resolve({ dataUrl: dataUrl, angle: resolved.angle, info: resolved.meta || {} });
            });
          });
        });
      });
    })).then(function(items){
      var valid = items.filter(Boolean);
      var bothTop = qs('#foot-both-top');
      var used = new Set();
      var topFilled = state.captures['left-top'] && state.captures['right-top'];
      if(bothTop && bothTop.checked && !topFilled){
        var topIndex = -1;
        var bestScore = -999;
        for(var i=0;i<valid.length;i++){
          var s = scoreTopCandidate(valid[i]);
          if(s > bestScore){
            bestScore = s;
            topIndex = i;
          }
        }
        if(topIndex < 0 && valid.length){
          topIndex = 0;
          var bestRatio = 99;
          for(var k=0;k<valid.length;k++){
            var ratio = valid[k].info && typeof valid[k].info.ratio === 'number' ? valid[k].info.ratio : 99;
            if(ratio < bestRatio){
              bestRatio = ratio;
              topIndex = k;
            }
          }
        }
        if(topIndex >= 0){
          var preTopSlot = nextEmptySlot(['left-top', 'right-top']) || 'left-top';
          setPreview(preTopSlot, valid[topIndex].dataUrl);
          used.add(topIndex);
          topFilled = !!(state.captures['left-top'] && state.captures['right-top']);
        }
      }
      function placeByAngle(angle, url, info){
        var meta = info || {};
        var normalizedAngle = normalizeAngleByMeta(angle, meta);
        rotateForAngle(normalizedAngle, url, meta, function(rotated){
          setPreviewByAngle(normalizedAngle, rotated, meta);
        });
      }
      for(var i=0;i<valid.length;i++){
        if(used.has(i)) continue;
        var angle = valid[i].angle;
        if(topFilled && angle === 'top'){
          angle = 'side';
        }
        placeByAngle(angle, valid[i].dataUrl, valid[i].info);
      }
      updateCaptureStatus('foot.uploadDone', {
        side: t('foot.left'),
        angle: t('foot.angleTop')
      });
      hapticPulse();
      autoAdvanceSlot();
    });
  }

  function toeImageForLabel(label){
    if(!label) return null;
    var s = String(label).toLowerCase();
    if(s.indexOf('greek') > -1 || s.indexOf('그리스') > -1) return 'assets/images/FootType_Greek.png';
    if(s.indexOf('roman') > -1 || s.indexOf('로만') > -1) return 'assets/images/FootType_Roman.png';
    if(s.indexOf('egypt') > -1 || s.indexOf('이집트') > -1) return 'assets/images/FootType_Egypt.png';
    return null;
  }

  function setToeGuideImage(leftEl, rightEl, leftLabel, rightLabel){
    function render(el, label, mirror){
      if(!el) return;
      var old = el.querySelector('.foot-toe-inline');
      if(old) old.remove();
      var src = toeImageForLabel(label);
      if(!src) return;
      var box = document.createElement('span');
      box.className = 'foot-toe-inline';
      var img = document.createElement('img');
      img.className = 'foot-toe-guide' + (mirror ? ' mirror' : '');
      img.src = src;
      img.alt = label || 'toe type';
      box.appendChild(img);
      el.appendChild(box);
    }
    render(leftEl, leftLabel, true);
    render(rightEl, rightLabel, false);
  }

  function isKorean(){
    return String(document.documentElement.lang || 'ko').toLowerCase().indexOf('ko') === 0;
  }

  function translated(key, englishFallback, koreanFallback){
    var value = t(key);
    if(value && value !== key) return value;
    return isKorean() ? koreanFallback : englishFallback;
  }

  function formatText(template, replacements){
    var output = String(template || '');
    Object.keys(replacements || {}).forEach(function(key){
      output = output.split('{' + key + '}').join(String(replacements[key]));
    });
    return output;
  }

  var PROFILE_LABEL_KEYS = {
    width: { narrow: 'foot.widthNarrow', normal: 'foot.widthNormal', wide: 'foot.widthWide' },
    instep: { low: 'foot.instepLow', mid: 'foot.instepMid', high: 'foot.instepHigh' },
    arch: { flat: 'foot.archFlat', normal: 'foot.archNormal', high: 'foot.archHigh' },
    toe: { egypt: 'foot.toeEgypt', greek: 'foot.toeGreek', roman: 'foot.toeRoman' },
    fit: { comfort: 'foot.fitComfort', balanced: 'foot.fitBalanced', performance: 'foot.fitPerformance' },
    level: { beginner: 'foot.levelBeginner', intermediate: 'foot.levelIntermediate', advanced: 'foot.levelAdvanced' },
    type: { bouldering: 'foot.typeBouldering', sport: 'foot.typeSport', multi: 'foot.typeMulti' }
  };

  function profileLabel(group, value){
    var groupKeys = PROFILE_LABEL_KEYS[group] || {};
    var key = groupKeys[value];
    return key ? t(key) : String(value || '-');
  }

  function readLengthInput(selector){
    var input = qs(selector);
    var value = input && input.value !== '' ? Number(input.value) : NaN;
    if(!input || !Number.isFinite(value) || value < 200 || value > 320){
      var message = translated(
        'foot.lengthInputError',
        'Enter both measured foot lengths between 200 and 320 mm.',
        '왼발과 오른발 실측 길이를 각각 200~320mm 범위로 입력해 주세요.'
      );
      if(input){
        input.setCustomValidity(message);
        input.reportValidity();
        input.focus();
      }
      return null;
    }
    input.setCustomValidity('');
    return Math.round(value * 10) / 10;
  }

  function readSelectValue(selector, fallback){
    var select = qs(selector);
    return select && select.value ? select.value : fallback;
  }

  function readOptionalStreetSize(){
    var size = qs('#foot-street-size');
    var scale = qs('#foot-street-scale');
    var value = size && size.value !== '' ? Number(size.value) : NaN;
    if(!Number.isFinite(value)) return null;
    return { value: value, scale: scale ? scale.value : 'eu' };
  }

  function formatLength(value){
    return String(value) + ' mm';
  }

  function renderResults(){
    if(!state.results) return;
    var result = state.results;
    var width = profileLabel('width', result.width);
    var instep = profileLabel('instep', result.instep);
    var arch = profileLabel('arch', result.arch);
    var toe = profileLabel('toe', result.toe);
    var values = {
      '#foot-result-left-length': formatLength(result.leftLengthMm),
      '#foot-result-right-length': formatLength(result.rightLengthMm),
      '#foot-result-left-width': width,
      '#foot-result-right-width': width,
      '#foot-result-left-instep': instep,
      '#foot-result-right-instep': instep,
      '#foot-result-left-arch': arch,
      '#foot-result-right-arch': arch,
      '#foot-result-left-toe': toe,
      '#foot-result-right-toe': toe
    };
    Object.keys(values).forEach(function(selector){
      var element = qs(selector);
      if(element) element.textContent = values[selector];
    });
    setToeGuideImage(qs('#foot-result-left-toe'), qs('#foot-result-right-toe'), toe, toe);
  }

  function sizeChecklistBody(result){
    var longer = Math.max(result.leftLengthMm, result.rightLengthMm);
    var difference = Math.round(Math.abs(result.leftLengthMm - result.rightLengthMm) * 10) / 10;
    var body = formatText(translated(
      'foot.checklistSizeBody',
      'Compare the manufacturer\'s internal-length chart with the longer foot ({longer} mm; L {left} / R {right}, difference {difference} mm). Use the {fit} preference only as a fitting intent, then check toe curl, heel lift, and pressure after 10 minutes of wear.',
      '더 긴 발 {longer}mm(왼발 {left} / 오른발 {right}, 차이 {difference}mm)을 기준으로 제조사 내측 길이표를 대조하세요. {fit} 선호는 착화 방향으로만 사용하고, 발가락 말림·뒤꿈치 들뜸·10분 착화 후 압박을 직접 확인하세요.'
    ), {
      longer: longer,
      left: result.leftLengthMm,
      right: result.rightLengthMm,
      difference: difference,
      fit: profileLabel('fit', result.fit)
    });
    if(result.streetSize){
      body += ' ' + formatText(translated(
        'foot.checklistStreetContext',
        'Treat the entered street size ({scale} {size}) as a comparison point, not a conversion rule.',
        '입력한 평소 신발 사이즈({scale} {size})는 비교 기준으로만 보고 암벽화 환산 공식으로 사용하지 마세요.'
      ), { scale: result.streetSize.scale.toUpperCase(), size: result.streetSize.value });
    }
    return body;
  }

  function volumeChecklistBody(result){
    var widthGuidance = {
      narrow: {
        en: 'Check that the forefoot does not slide sideways and that the closure can secure the foot without bottoming out.',
        ko: '전족부가 좌우로 밀리지 않고 잠금 장치가 끝까지 남지 않은 채 발을 고정하는지 확인하세요.'
      },
      normal: {
        en: 'Check for even contact around the forefoot without a single pressure ridge.',
        ko: '전족부 둘레가 한 지점만 눌리지 않고 고르게 밀착되는지 확인하세요.'
      },
      wide: {
        en: 'Check the outer metatarsal area and toe-box sidewalls for pinching or numbness.',
        ko: '새끼발가락 쪽 중족부와 토박스 측벽에 찝힘이나 저림이 없는지 확인하세요.'
      }
    }[result.width];
    var instepGuidance = {
      low: {
        en: 'Also confirm heel retention before the closure reaches its limit.',
        ko: '또한 잠금 장치가 조절 한계에 닿기 전에 뒤꿈치가 안정적으로 잡히는지 확인하세요.'
      },
      mid: {
        en: 'Also confirm that the closure wraps the instep evenly.',
        ko: '또한 잠금 장치가 발등 전체를 고르게 감싸는지 확인하세요.'
      },
      high: {
        en: 'Also confirm enough closure adjustment and no concentrated pressure on the top of the foot.',
        ko: '또한 잠금 조절 여유가 충분하고 발등 한 지점에 압박이 몰리지 않는지 확인하세요.'
      }
    }[result.instep];
    return formatText(translated(
      'foot.checklistVolumeBody',
      'Self-check: {width} width / {instep} instep. {widthCheck} {instepCheck}',
      '자가 체크: 발볼 {width} / 발등 {instep}. {widthCheck} {instepCheck}'
    ), {
      width: profileLabel('width', result.width),
      instep: profileLabel('instep', result.instep),
      widthCheck: isKorean() ? widthGuidance.ko : widthGuidance.en,
      instepCheck: isKorean() ? instepGuidance.ko : instepGuidance.en
    });
  }

  function shapeChecklistBody(result){
    var toeGuidance = {
      egypt: { en: 'Check big-toe alignment and tapered toe-box pressure.', ko: '엄지 정렬과 좁아지는 토박스의 엄지 압박을 확인하세요.' },
      greek: { en: 'Check pressure at the second toe and whether it is forced to curl.', ko: '둘째 발가락 끝 압박과 과도한 말림이 없는지 확인하세요.' },
      roman: { en: 'Check that the first three toes are not crowded across the forefoot.', ko: '첫 세 발가락이 전족부에서 서로 겹치거나 몰리지 않는지 확인하세요.' }
    }[result.toe];
    var archGuidance = {
      flat: { en: 'Check for uncomfortable midfoot ridges during edging.', ko: '엣징할 때 중족부 한 지점이 능선처럼 눌리지 않는지 확인하세요.' },
      normal: { en: 'Check that midfoot support stays comfortable under load.', ko: '하중을 실었을 때 중족부 지지가 편안하게 유지되는지 확인하세요.' },
      high: { en: 'Check for an under-arch gap and heel movement under load.', ko: '하중을 실었을 때 아치 아래 뜸과 뒤꿈치 움직임을 확인하세요.' }
    }[result.arch];
    var useGuidance = {
      bouldering: { en: 'For bouldering, repeat heel- and toe-hook motions before deciding.', ko: '볼더링용이라면 힐훅과 토훅 동작을 반복해 본 뒤 결정하세요.' },
      sport: { en: 'For sport climbing, balance edging support with sustained forefoot comfort.', ko: '스포츠클라이밍용이라면 엣징 지지와 지속적인 전족부 편안함을 함께 확인하세요.' },
      multi: { en: 'For multi-pitch use, test prolonged wear and swelling allowance.', ko: '멀티피치용이라면 장시간 착화와 발 부종 여유를 확인하세요.' }
    }[result.type];
    return formatText(translated(
      'foot.checklistShapeBody',
      'Self-check: {arch} arch / {toe} toe; {level}, {type}. {toeCheck} {archCheck} {useCheck}',
      '자가 체크: 아치 {arch} / 발가락 {toe}, {level}·{type}. {toeCheck} {archCheck} {useCheck}'
    ), {
      arch: profileLabel('arch', result.arch),
      toe: profileLabel('toe', result.toe),
      level: profileLabel('level', result.level),
      type: profileLabel('type', result.type),
      toeCheck: isKorean() ? toeGuidance.ko : toeGuidance.en,
      archCheck: isKorean() ? archGuidance.ko : archGuidance.en,
      useCheck: isKorean() ? useGuidance.ko : useGuidance.en
    });
  }

  function appendChecklistCard(grid, title, body){
    var card = document.createElement('div');
    card.className = 'foot-reco-card';
    var top = document.createElement('div');
    top.className = 'foot-reco-top';
    var heading = document.createElement('strong');
    heading.className = 'foot-reco-model';
    heading.textContent = title;
    var meta = document.createElement('div');
    meta.className = 'foot-reco-meta';
    var description = document.createElement('span');
    description.style.gridColumn = '1 / -1';
    description.textContent = body;
    top.appendChild(heading);
    meta.appendChild(description);
    card.appendChild(top);
    card.appendChild(meta);
    grid.appendChild(card);
  }

  function buildRecommendations(){
    var grid = qs('#foot-reco-grid');
    if(!grid || !state.results) return;
    grid.innerHTML = '';
    appendChecklistCard(grid, translated('foot.checklistSizeTitle', '1. Length & size-chart check', '1. 길이·사이즈표 확인'), sizeChecklistBody(state.results));
    appendChecklistCard(grid, translated('foot.checklistVolumeTitle', '2. Width & instep check', '2. 발볼·발등 확인'), volumeChecklistBody(state.results));
    appendChecklistCard(grid, translated('foot.checklistShapeTitle', '3. Shape & use check', '3. 형태·용도 확인'), shapeChecklistBody(state.results));
  }

  function analyze(){
    var leftLength = readLengthInput('#foot-length-input');
    if(leftLength === null) return;
    var rightLength = readLengthInput('#foot-right-length-input');
    if(rightLength === null) return;

    state.results = {
      leftLengthMm: leftLength,
      rightLengthMm: rightLength,
      width: readSelectValue('#foot-width-profile', 'normal'),
      instep: readSelectValue('#foot-instep-profile', 'mid'),
      arch: readSelectValue('#foot-arch-profile', 'normal'),
      toe: readSelectValue('#foot-toe-profile', 'greek'),
      fit: readSelectValue('#foot-fit', 'balanced'),
      streetSize: readOptionalStreetSize(),
      level: readSelectValue('#foot-level', 'beginner'),
      type: readSelectValue('#foot-type', 'bouldering')
    };

    updateProgress(100);
    renderResults();
    buildRecommendations();
    setStep(3);
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
      slot.classList.remove('is-active');
    });
    var resIds = ['length','width','instep','arch','toe'];
    ['left','right'].forEach(function(side){
      resIds.forEach(function(id){
        var el = qs('#foot-result-' + side + '-' + id);
        if(el) el.textContent = '-';
      });
    });
    var grid = qs('#foot-reco-grid');
    if(grid){
      grid.innerHTML = '';
      var empty = document.createElement('div');
      empty.className = 'foot-reco-empty';
      empty.textContent = t('foot.recoEmpty');
      grid.appendChild(empty);
    }
    ['#foot-length-input', '#foot-right-length-input', '#foot-street-size'].forEach(function(selector){
      var input = qs(selector);
      if(input){
        input.value = '';
        input.setCustomValidity('');
      }
    });
    var defaults = {
      '#foot-width-profile': 'normal',
      '#foot-instep-profile': 'mid',
      '#foot-arch-profile': 'normal',
      '#foot-toe-profile': 'greek',
      '#foot-fit': 'balanced',
      '#foot-street-scale': 'eu',
      '#foot-level': 'beginner',
      '#foot-type': 'bouldering'
    };
    Object.keys(defaults).forEach(function(selector){
      var control = qs(selector);
      if(control) control.value = defaults[selector];
    });
    updateProgress(0);
    setStep(1);
    updateCaptureStatus('foot.captureIdle');
    updateCaptureTarget();
    state.currentSlot = computeSlotFromSelects();
    var upload = qs('#foot-upload');
    if(upload) upload.value = '';
  }

  function readHistory(){
    try {
      var parsed = JSON.parse(localStorage.getItem('footAnalysisHistory') || '[]');
      if(!Array.isArray(parsed)) return [];
      return parsed.filter(function(item){ return item && typeof item === 'object'; }).slice(0, 8);
    } catch(error){
      return [];
    }
  }

  function writeHistory(history){
    try {
      localStorage.setItem('footAnalysisHistory', JSON.stringify(history.slice(0, 8)));
      return true;
    } catch(error){
      return false;
    }
  }

  function saveHistory(){
    if(!state.results) return;
    var history = readHistory();
    var entry = {
      version: 2,
      date: new Date().toISOString(),
      leftLengthMm: state.results.leftLengthMm,
      rightLengthMm: state.results.rightLengthMm,
      width: state.results.width,
      instep: state.results.instep,
      arch: state.results.arch,
      toe: state.results.toe,
      fit: state.results.fit,
      level: state.results.level,
      type: state.results.type
    };
    history.unshift(entry);
    writeHistory(history);
    renderHistory();
  }

  function historySummary(item){
    if(item.version === 2 && Number.isFinite(Number(item.leftLengthMm)) && Number.isFinite(Number(item.rightLengthMm))){
      return formatText(translated(
        'foot.historyTemplateExplicit',
        'L {left}mm / R {right}mm · {width} · {instep} · {arch} · {toe}',
        '왼발 {left}mm / 오른발 {right}mm · {width} · {instep} · {arch} · {toe}'
      ), {
        left: Number(item.leftLengthMm),
        right: Number(item.rightLengthMm),
        width: profileLabel('width', item.width),
        instep: profileLabel('instep', item.instep),
        arch: profileLabel('arch', item.arch),
        toe: profileLabel('toe', item.toe)
      });
    }
    return '';
  }

  function renderHistory(){
    var list = qs('#foot-history-list');
    if(!list) return;
    var history = readHistory().filter(function(item){ return !!historySummary(item); });
    if(!history.length){
      list.innerHTML = '';
      var empty = document.createElement('div');
      empty.className = 'foot-history-empty';
      empty.textContent = t('foot.historyEmpty');
      list.appendChild(empty);
      return;
    }
    list.innerHTML = '';
    history.forEach(function(item){
      var row = document.createElement('div');
      row.className = 'foot-history-item';
      var date = new Date(item.date);
      var dateElement = document.createElement('div');
      dateElement.className = 'foot-history-date';
      dateElement.textContent = Number.isNaN(date.getTime()) ? '-' : date.toLocaleDateString();
      var meta = document.createElement('div');
      meta.className = 'foot-history-meta';
      meta.textContent = historySummary(item);
      row.appendChild(dateElement);
      row.appendChild(meta);
      list.appendChild(row);
    });
  }

  function copySummary(){
    if(!state.results) return;
    var summary = formatText(translated(
      'foot.shareTemplateExplicit',
      'Foot fit reference: L {left}mm / R {right}mm, width {width}, instep {instep}, arch {arch}, toe {toe}.',
      '암벽화 핏 참고: 왼발 {left}mm / 오른발 {right}mm, 발볼 {width}, 발등 {instep}, 아치 {arch}, 발가락 {toe}.'
    ), {
      left: state.results.leftLengthMm,
      right: state.results.rightLengthMm,
      width: profileLabel('width', state.results.width),
      instep: profileLabel('instep', state.results.instep),
      arch: profileLabel('arch', state.results.arch),
      toe: profileLabel('toe', state.results.toe)
    });

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
      var files = e.target.files;
      if(e.target.files && e.target.files.length > 1){
        loadUploads(files);
      } else {
        loadUpload(files[0]);
      }
      e.target.value = '';
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
      try { localStorage.removeItem('footAnalysisHistory'); } catch(error){ /* storage may be unavailable */ }
      renderHistory();
    });
    ['#foot-length-input', '#foot-right-length-input'].forEach(function(selector){
      var input = qs(selector);
      if(input) input.addEventListener('input', function(){ input.setCustomValidity(''); });
    });
    document.addEventListener('app:lang', function(){
      renderHistory();
      if(state.results){
        renderResults();
        buildRecommendations();
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

  var initialized = false;

  function ensureInitialized(){
    if(initialized || !qs('#foot')) return;
    initialized = true;
    init();
  }

  function initializeIfFootIsActive(){
    var foot = qs('#foot');
    if(foot && foot.classList.contains('active') && !foot.hidden) ensureInitialized();
  }

  document.addEventListener('app:tab', function(event){
    var tab = event && event.detail ? event.detail.tab : '';
    if(tab === 'foot') ensureInitialized();
    else if(initialized) stopCamera();
  });

  if(document.readyState === 'complete' || document.readyState === 'interactive'){
    setTimeout(initializeIfFootIsActive, 0);
  } else {
    document.addEventListener('DOMContentLoaded', initializeIfFootIsActive, false);
  }
})();
