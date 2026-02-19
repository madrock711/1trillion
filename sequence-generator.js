(() => {
  function initSequenceGenerator(root) {
    if (!root) { return; }

    const videoInput = root.querySelector('#sequenceVideoInput');
    const uploadSection = root.querySelector('#sequenceUpload');
    const videoPreview = root.querySelector('#sequenceVideoPreview');
    const generateBtn = root.querySelector('#sequenceGenerateBtn');
    const outputCanvas = root.querySelector('#sequenceOutputCanvas');
    const previewSection = root.querySelector('#sequencePreview');
    const downloadBtn = root.querySelector('#sequenceDownloadBtn');
    const progress = root.querySelector('#sequenceProgress');
    const progressBar = root.querySelector('#sequenceProgressBar');
    const videoInfo = root.querySelector('#sequenceVideoInfo');
    const videoInfoContent = root.querySelector('#sequenceVideoInfoContent');
    const trimSection = root.querySelector('#sequenceTrim');
    const trimStartInput = root.querySelector('#sequenceTrimStart');
    const trimEndInput = root.querySelector('#sequenceTrimEnd');
    const trimStartValue = root.querySelector('#sequenceTrimStartValue');
    const trimEndValue = root.querySelector('#sequenceTrimEndValue');
    const trimMeta = root.querySelector('#sequenceTrimMeta');
    const loopModeSelect = root.querySelector('#sequenceLoopMode');
    const overlapControl = root.querySelector('#sequenceOverlapControl');
    const overlapFramesInput = root.querySelector('#sequenceOverlapFrames');
    const overlapNote = root.querySelector('#sequenceOverlapNote');
    const fpsInput = root.querySelector('#sequenceFps');
    const autoGridBtn = root.querySelector('#sequenceAutoGrid');
    const autoMeta = root.querySelector('#sequenceAutoMeta');
    const totalFramesMeta = root.querySelector('#sequenceTotalFrames');
    const maskToggle = root.querySelector('#sequenceMaskToggle');
    const maskInvert = root.querySelector('#sequenceMaskInvert');
    const maskInput = root.querySelector('#sequenceMaskInput');
    const maskPreview = root.querySelector('#sequenceMaskPreview');
    const maskClear = root.querySelector('#sequenceMaskClear');
    const maskDrop = root.querySelector('#sequenceMaskDrop');
    const maskSourceInputs = root.querySelectorAll('input[name="sequenceMaskSource"]');
    const maskCanvas = root.querySelector('#sequenceMaskCanvas');
    const maskGenerateBtn = root.querySelector('#sequenceMaskGenerate');
    const maskDownloadBtn = root.querySelector('#sequenceMaskDownload');
    const maskNoiseType = root.querySelector('#sequenceMaskNoiseType');
    const maskShape = root.querySelector('#sequenceMaskShape');
    const maskEdge = root.querySelector('#sequenceMaskEdge');
    const maskPolar = root.querySelector('#sequenceMaskPolar');
    const maskWarp = root.querySelector('#sequenceMaskWarp');
    const maskSwirl = root.querySelector('#sequenceMaskSwirl');
    const maskPixelate = root.querySelector('#sequenceMaskPixelate');
    const maskThreshold = root.querySelector('#sequenceMaskThreshold');
    const maskScale = root.querySelector('#sequenceMaskScale');
    const maskIntensity = root.querySelector('#sequenceMaskIntensity');
    const maskContrast = root.querySelector('#sequenceMaskContrast');
    const maskGamma = root.querySelector('#sequenceMaskGamma');
    const maskTiling = root.querySelector('#sequenceMaskTiling');
    const maskSaveBtn = root.querySelector('#sequenceMaskSave');
    const maskStatus = root.querySelector('#sequenceMaskStatus');
    const maskPresetSelect = root.querySelector('#sequenceMaskPresetSelect');
    let defaultAutoMeta = autoMeta ? autoMeta.innerHTML : '';

    let currentVideo = null;
    let maskImage = null;
    let maskUrl = '';
    let maskCache = null;
    let maskCacheWidth = 0;
    let maskCacheHeight = 0;
    let generatedMask = null;
    let trimStart = 0;
    let trimEnd = 0;
    let trimReady = false;
    const MIN_TRIM_GAP = 0.05;

    function updateLoopModeUI() {
      const loopMode = loopModeSelect.value;
      overlapControl.style.display = loopMode === 'overlap' ? 'block' : 'none';
    }

    function setGrid(cols, rows) {
      root.querySelector('#sequenceGridCols').value = cols;
      root.querySelector('#sequenceGridRows').value = rows;
      updateOverlapNoteUI();
    }

    function showError(message) {
      alert(message);
      videoPreview.style.display = 'none';
      generateBtn.disabled = true;
      videoInfo.style.display = 'none';
      trimReady = false;
      setTrimEnabled(false);
    }

    function updateAutoMeta(frames, cols, rows, clamped) {
      if (!autoMeta) { return; }
      if (!frames || !cols || !rows) {
        autoMeta.innerHTML = defaultAutoMeta;
        return;
      }
      const extra = clamped ? ' (최대 256프레임으로 제한됨)' : '';
      autoMeta.textContent = `총 ${frames}프레임 · ${cols}×${rows}${extra}`;
    }

    function applyTemplate(template, data) {
      if (!template) { return ''; }
      return template.replace(/\{(\w+)\}/g, (match, key) => {
        const value = data[key];
        return value == null ? match : value;
      });
    }

    function getTotalFramesEstimate() {
      if (!currentVideo || !isFinite(currentVideo.duration) || currentVideo.duration <= 0) {
        return null;
      }
      const fps = Math.max(1, parseInt(fpsInput.value || '24', 10));
      const trim = getTrimRange();
      const duration = trim.duration || currentVideo.duration;
      if (!duration || duration <= 0) { return null; }
      return Math.max(1, Math.round(duration * fps));
    }

    function updateTotalFramesUI() {
      if (!totalFramesMeta || !window.appI18n) { return; }
      const frames = getTotalFramesEstimate();
      if (!frames) {
        totalFramesMeta.textContent = '';
        return;
      }
      const template = window.appI18n.t('sequence.totalFramesLabel');
      totalFramesMeta.textContent = applyTemplate(template, { frames });
    }

    function getTotalGridFrames() {
      const cols = parseInt(root.querySelector('#sequenceGridCols').value, 10) || 1;
      const rows = parseInt(root.querySelector('#sequenceGridRows').value, 10) || 1;
      return Math.max(1, cols * rows);
    }

    function clampOverlapFrames(totalFrames) {
      if (!overlapFramesInput) { return 1; }
      const maxFrames = Math.max(1, totalFrames - 1);
      overlapFramesInput.max = String(maxFrames);
      const raw = parseInt(overlapFramesInput.value || '1', 10);
      const clamped = Math.min(Math.max(raw, 1), maxFrames);
      overlapFramesInput.value = String(clamped);
      return clamped;
    }

    function updateOverlapNoteUI() {
      if (!overlapNote || !window.appI18n) { return; }
      const totalFrames = getTotalGridFrames();
      const overlapFrames = clampOverlapFrames(totalFrames);
      const template = window.appI18n.t('sequence.overlapHint');
      overlapNote.textContent = applyTemplate(template, {
        overlap: overlapFrames,
        total: totalFrames
      });
    }

    function formatSeconds(value) {
      if (!isFinite(value)) { return '--'; }
      return `${value.toFixed(2)}s`;
    }

    function setTrimEnabled(enabled) {
      if (!trimSection) { return; }
      trimSection.classList.toggle('is-disabled', !enabled);
      if (trimStartInput) { trimStartInput.disabled = !enabled; }
      if (trimEndInput) { trimEndInput.disabled = !enabled; }
      if (!enabled) {
        if (trimStartValue) { trimStartValue.textContent = '--'; }
        if (trimEndValue) { trimEndValue.textContent = '--'; }
        if (trimMeta) { trimMeta.textContent = '--'; }
      }
    }

    function normalizeTrim(start, end, duration, preferEnd) {
      let s = Math.min(Math.max(start, 0), duration);
      let e = Math.min(Math.max(end, 0), duration);
      if (e - s < MIN_TRIM_GAP) {
        if (preferEnd) {
          s = Math.max(0, e - MIN_TRIM_GAP);
        } else {
          e = Math.min(duration, s + MIN_TRIM_GAP);
        }
      }
      return { start: s, end: e };
    }

    function updateTrimUI(duration) {
      if (!trimStartInput || !trimEndInput) { return; }
      trimStartInput.max = duration;
      trimEndInput.max = duration;
      trimStartInput.value = trimStart;
      trimEndInput.value = trimEnd;
      if (trimStartValue) { trimStartValue.textContent = formatSeconds(trimStart); }
      if (trimEndValue) { trimEndValue.textContent = formatSeconds(trimEnd); }
      if (trimMeta) {
        const length = Math.max(0, trimEnd - trimStart);
        trimMeta.textContent = `${formatSeconds(trimStart)} - ${formatSeconds(trimEnd)} (${formatSeconds(length)})`;
      }
    }

    function setTrimRange(start, end, duration, preferEnd) {
      const normalized = normalizeTrim(start, end, duration, preferEnd);
      trimStart = normalized.start;
      trimEnd = normalized.end;
      updateTrimUI(duration);
      updateTotalFramesUI();
    }

    function getTrimRange() {
      if (!currentVideo || !isFinite(currentVideo.duration) || currentVideo.duration <= 0) {
        return { start: 0, end: 0, duration: 0 };
      }
      const duration = currentVideo.duration;
      if (!trimReady) {
        return { start: 0, end: duration, duration };
      }
      const normalized = normalizeTrim(trimStart, trimEnd, duration, false);
      return {
        start: normalized.start,
        end: normalized.end,
        duration: Math.max(0, normalized.end - normalized.start)
      };
    }

    setTrimEnabled(false);

    function handleVideoFile(file) {
      if (!file || !file.type.startsWith('video/')) { return; }

      if (currentVideo) {
        URL.revokeObjectURL(currentVideo.src);
        currentVideo.pause();
        currentVideo.removeAttribute('src');
        currentVideo.load();
      }

      videoPreview.style.display = 'none';
      generateBtn.disabled = true;
      videoInfo.style.display = 'none';
      previewSection.classList.remove('is-active');
      trimReady = false;
      setTrimEnabled(false);
      updateTotalFramesUI();

      const url = URL.createObjectURL(file);
      const testVideo = document.createElement('video');
      testVideo.preload = 'auto';
      testVideo.muted = true;
      testVideo.playsInline = true;

      let loadSuccess = false;
      let timeoutId;

      const onSuccess = () => {
        if (loadSuccess) { return; }
        loadSuccess = true;
        clearTimeout(timeoutId);

        if (!isFinite(testVideo.duration) || testVideo.duration <= 0) {
          showError('비디오의 재생 시간을 확인할 수 없습니다.\n다른 파일을 사용하거나 재인코딩해 주세요.');
          return;
        }

        videoPreview.src = url;
        videoPreview.style.display = 'block';
        videoPreview.loop = true;
        currentVideo = videoPreview;
        generateBtn.disabled = false;

        videoInfo.style.display = 'block';
        videoInfoContent.innerHTML = `
          재생시간: ${testVideo.duration.toFixed(2)}초<br>
          해상도: ${testVideo.videoWidth} × ${testVideo.videoHeight}px<br>
          형식: ${file.type || '알 수 없음'}<br>
          파일크기: ${(file.size / 1024 / 1024).toFixed(2)}MB
        `;
        trimReady = true;
        setTrimEnabled(true);
        trimStart = 0;
        trimEnd = testVideo.duration;
        updateTrimUI(testVideo.duration);
        updateTotalFramesUI();
        updateAutoMeta();
      };

      const onError = () => {
        if (loadSuccess) { return; }
        clearTimeout(timeoutId);
        showError('비디오를 로드할 수 없습니다.\nMP4 (H.264) 형식으로 변환 후 다시 시도해 주세요.');
      };

      timeoutId = setTimeout(() => {
        if (loadSuccess) { return; }
        if (isFinite(testVideo.duration) && testVideo.duration > 0) {
          onSuccess();
        } else {
          showError('비디오 로딩 시간이 초과되었습니다.\n더 짧은 파일로 다시 시도해 주세요.');
        }
      }, 10000);

      testVideo.addEventListener('canplay', onSuccess, { once: true });
      testVideo.addEventListener('canplaythrough', onSuccess, { once: true });
      testVideo.addEventListener('error', onError, { once: true });

      testVideo.src = url;
      testVideo.load();
    }

    function clearMask() {
      if (maskUrl) {
        URL.revokeObjectURL(maskUrl);
        maskUrl = '';
      }
      maskImage = null;
      generatedMask = null;
      maskCache = null;
      maskCacheWidth = 0;
      maskCacheHeight = 0;
      maskInput.value = '';
      maskToggle.checked = false;
      if (maskInvert) { maskInvert.checked = false; }
      if (maskPreview) {
        maskPreview.src = '';
        maskPreview.style.display = 'none';
      }
    }

    function getMaskSource() {
      const source = Array.from(maskSourceInputs).find(input => input.checked)?.value || 'upload';
      if (source === 'generator') {
        return generatedMask;
      }
      return maskImage;
    }

    function handleMaskFile(file) {
      if (!file || !file.type.startsWith('image/')) { return; }
      if (maskUrl) {
        URL.revokeObjectURL(maskUrl);
      }
      maskCache = null;
      maskCacheWidth = 0;
      maskCacheHeight = 0;
      maskUrl = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        maskImage = img;
        if (maskPreview) {
          maskPreview.src = maskUrl;
          maskPreview.style.display = 'block';
        }
        maskToggle.checked = true;
      };
      img.onerror = () => {
        clearMask();
        showError('마스크 이미지를 불러올 수 없습니다.');
      };
      img.src = maskUrl;
    }

    function buildMaskCanvases(width, height) {
      const sourceImage = getMaskSource();
      if (!sourceImage) { return null; }
      if (maskCache && maskCacheWidth === width && maskCacheHeight === height) {
        return maskCache;
      }

      const baseCanvas = document.createElement('canvas');
      baseCanvas.width = width;
      baseCanvas.height = height;
      const baseCtx = baseCanvas.getContext('2d');
      baseCtx.clearRect(0, 0, width, height);
      baseCtx.drawImage(sourceImage, 0, 0, width, height);
      const baseData = baseCtx.getImageData(0, 0, width, height);
      const basePixels = baseData.data;
      // Use luminance as alpha so grayscale masks work even without alpha.
      for (let i = 0; i < basePixels.length; i += 4) {
        const r = basePixels[i];
        const g = basePixels[i + 1];
        const b = basePixels[i + 2];
        const a = basePixels[i + 3];
        const lum = Math.round(0.2126 * r + 0.7152 * g + 0.0722 * b);
        basePixels[i] = 255;
        basePixels[i + 1] = 255;
        basePixels[i + 2] = 255;
        basePixels[i + 3] = Math.round((a / 255) * lum);
      }
      baseCtx.putImageData(baseData, 0, 0);

      const invertedCanvas = document.createElement('canvas');
      invertedCanvas.width = width;
      invertedCanvas.height = height;
      const invertedCtx = invertedCanvas.getContext('2d');
      invertedCtx.drawImage(baseCanvas, 0, 0);
      const imageData = invertedCtx.getImageData(0, 0, width, height);
      const data = imageData.data;
      for (let i = 0; i < data.length; i += 4) {
        data[i + 3] = 255 - data[i + 3];
      }
      invertedCtx.putImageData(imageData, 0, 0);

      maskCache = { baseCanvas, invertedCanvas };
      maskCacheWidth = width;
      maskCacheHeight = height;
      return maskCache;
    }

    function applyMask(tempCtx, width, height, invert) {
      const cache = buildMaskCanvases(width, height);
      if (!cache) { return; }
      const maskCanvas = invert ? cache.invertedCanvas : cache.baseCanvas;
      tempCtx.globalCompositeOperation = 'destination-in';
      tempCtx.drawImage(maskCanvas, 0, 0, width, height);
      tempCtx.globalCompositeOperation = 'source-over';
    }

    function seekToTime(video, time) {
      return new Promise((resolve, reject) => {
        if (!isFinite(time) || time < 0) {
          reject(new Error(`Invalid time: ${time}`));
          return;
        }

        if (!isFinite(video.duration) || video.duration <= 0) {
          reject(new Error('Video duration is invalid'));
          return;
        }

        const safeTime = Math.min(time, video.duration - 0.001);
        let timeoutId;

        const cleanup = () => {
          clearTimeout(timeoutId);
          video.removeEventListener('seeked', onSeeked);
          video.removeEventListener('error', onError);
        };

        const finish = () => {
          cleanup();
          resolve();
        };

        const onSeeked = () => {
          if (typeof video.requestVideoFrameCallback === 'function') {
            const onFrame = () => finish();
            video.requestVideoFrameCallback(onFrame);
          } else {
            setTimeout(finish, 50);
          }
        };

        const onError = (e) => {
          cleanup();
          reject(new Error('Video seek error: ' + e.message));
        };

        timeoutId = setTimeout(() => {
          cleanup();
          reject(new Error('Seek timeout'));
        }, 15000);

        video.addEventListener('seeked', onSeeked, { once: true });
        video.addEventListener('error', onError, { once: true });

        try {
          video.currentTime = safeTime;
        } catch (e) {
          cleanup();
          reject(e);
        }
      });
    }

    async function generateDirectSpriteSheet(video, cols, rows, frameWidth, frameHeight, trimStartTime, trimEndTime) {
      const totalFrames = cols * rows;
      const canvas = outputCanvas;
      const ctx = canvas.getContext('2d');
      const useMask = !!(maskToggle.checked && getMaskSource());
      const tempCanvas = useMask ? document.createElement('canvas') : null;
      const tempCtx = useMask ? tempCanvas.getContext('2d') : null;
      if (useMask) {
        tempCanvas.width = frameWidth;
        tempCanvas.height = frameHeight;
        buildMaskCanvases(frameWidth, frameHeight);
      }

      if (video.readyState < 2) {
        await new Promise(resolve => video.addEventListener('loadedmetadata', resolve, { once: true }));
      }

      const rawDuration = video.duration;
      if (!rawDuration || !isFinite(rawDuration) || rawDuration <= 0) {
        throw new Error('비디오 duration을 읽을 수 없습니다.');
      }
      const duration = Math.max(0, trimEndTime - trimStartTime);
      if (!duration || duration < MIN_TRIM_GAP) {
        throw new Error('잘린 구간이 너무 짧습니다.');
      }

      canvas.width = cols * frameWidth;
      canvas.height = rows * frameHeight;
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const interval = duration / totalFrames;

      for (let i = 0; i < totalFrames; i++) {
        const row = Math.floor(i / cols);
        const col = i % cols;
        const time = trimStartTime + ((i * interval) % duration);

        await seekToTime(video, time);
        if (useMask) {
          tempCtx.clearRect(0, 0, frameWidth, frameHeight);
          tempCtx.drawImage(video, 0, 0, frameWidth, frameHeight);
          applyMask(tempCtx, frameWidth, frameHeight, maskInvert && maskInvert.checked);
          ctx.drawImage(tempCanvas, col * frameWidth, row * frameHeight);
        } else {
          ctx.drawImage(video, col * frameWidth, row * frameHeight, frameWidth, frameHeight);
        }

        const percent = Math.round(((i + 1) / totalFrames) * 100);
        progressBar.style.width = percent + '%';
        progressBar.textContent = percent + '%';
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    }

    async function generatePingPongSpriteSheet(video, cols, rows, frameWidth, frameHeight, trimStartTime, trimEndTime) {
      const totalFrames = cols * rows;
      const halfFrames = Math.ceil(totalFrames / 2);
      const canvas = outputCanvas;
      const ctx = canvas.getContext('2d');
      const useMask = !!(maskToggle.checked && getMaskSource());
      const tempCanvas = useMask ? document.createElement('canvas') : null;
      const tempCtx = useMask ? tempCanvas.getContext('2d') : null;
      if (useMask) {
        tempCanvas.width = frameWidth;
        tempCanvas.height = frameHeight;
        buildMaskCanvases(frameWidth, frameHeight);
      }

      if (video.readyState < 2) {
        await new Promise(resolve => video.addEventListener('loadedmetadata', resolve, { once: true }));
      }

      const rawDuration = video.duration;
      if (!rawDuration || !isFinite(rawDuration) || rawDuration <= 0) {
        throw new Error('비디오 duration을 읽을 수 없습니다.');
      }
      const duration = Math.max(0, trimEndTime - trimStartTime);
      if (!duration || duration < MIN_TRIM_GAP) {
        throw new Error('잘린 구간이 너무 짧습니다.');
      }

      canvas.width = cols * frameWidth;
      canvas.height = rows * frameHeight;
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const interval = duration / halfFrames;
      const timeIndices = [];
      for (let i = 0; i < halfFrames; i++) {
        timeIndices.push(i);
      }
      for (let i = halfFrames - 2; i > 0; i--) {
        timeIndices.push(i);
      }

      for (let i = 0; i < Math.min(totalFrames, timeIndices.length); i++) {
        const row = Math.floor(i / cols);
        const col = i % cols;
        const timeIndex = timeIndices[i];
        const time = trimStartTime + ((timeIndex * interval) % duration);

        await seekToTime(video, time);
        if (useMask) {
          tempCtx.clearRect(0, 0, frameWidth, frameHeight);
          tempCtx.drawImage(video, 0, 0, frameWidth, frameHeight);
          applyMask(tempCtx, frameWidth, frameHeight, maskInvert && maskInvert.checked);
          ctx.drawImage(tempCanvas, col * frameWidth, row * frameHeight);
        } else {
          ctx.drawImage(video, col * frameWidth, row * frameHeight, frameWidth, frameHeight);
        }

        const percent = Math.round(((i + 1) / totalFrames) * 100);
        progressBar.style.width = percent + '%';
        progressBar.textContent = percent + '%';
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    }

    async function generateOverlapSpriteSheet(video, cols, rows, frameWidth, frameHeight, overlapFrames, trimStartTime, trimEndTime) {
      const totalFrames = cols * rows;
      const canvas = outputCanvas;
      const ctx = canvas.getContext('2d');
      const useMask = !!(maskToggle.checked && getMaskSource());

      if (video.readyState < 2) {
        await new Promise(resolve => video.addEventListener('loadedmetadata', resolve, { once: true }));
      }

      const rawDuration = video.duration;
      if (!rawDuration || !isFinite(rawDuration) || rawDuration <= 0) {
        throw new Error('비디오 duration을 읽을 수 없습니다.');
      }
      const duration = Math.max(0, trimEndTime - trimStartTime);
      if (!duration || duration < MIN_TRIM_GAP) {
        throw new Error('잘린 구간이 너무 짧습니다.');
      }

      canvas.width = cols * frameWidth;
      canvas.height = rows * frameHeight;
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const maxOverlapFrames = Math.max(1, totalFrames - 1);
      const safeOverlapFrames = Math.min(Math.max(overlapFrames, 1), maxOverlapFrames);
      const uniqueFrames = totalFrames - safeOverlapFrames;
      const interval = duration / totalFrames;
      const overlapSteps = Math.max(1, safeOverlapFrames - 1);

      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = frameWidth;
      tempCanvas.height = frameHeight;
      const tempCtx = tempCanvas.getContext('2d');
      if (useMask) {
        buildMaskCanvases(frameWidth, frameHeight);
      }

      for (let i = 0; i < totalFrames; i++) {
        const row = Math.floor(i / cols);
        const col = i % cols;
        const x = col * frameWidth;
        const y = row * frameHeight;

        if (i < uniqueFrames) {
          const time = trimStartTime + (i * interval);
          await seekToTime(video, time);
          if (useMask) {
            tempCtx.clearRect(0, 0, frameWidth, frameHeight);
            tempCtx.drawImage(video, 0, 0, frameWidth, frameHeight);
            applyMask(tempCtx, frameWidth, frameHeight, maskInvert && maskInvert.checked);
            ctx.drawImage(tempCanvas, x, y);
          } else {
            ctx.drawImage(video, x, y, frameWidth, frameHeight);
          }
        } else {
          const overlapIndex = i - uniqueFrames;
          if (overlapIndex >= safeOverlapFrames) { continue; }
          const alpha = safeOverlapFrames === 1 ? 1 : (overlapIndex / overlapSteps);
          const startIndex = overlapIndex;
          const endIndex = uniqueFrames + overlapIndex;
          const startTime = trimStartTime + (startIndex * interval);
          const endTime = trimStartTime + (endIndex * interval);

          await seekToTime(video, Math.min(endTime, trimEndTime - 0.001));
          tempCtx.clearRect(0, 0, frameWidth, frameHeight);
          tempCtx.drawImage(video, 0, 0, frameWidth, frameHeight);
          const endFrameData = tempCtx.getImageData(0, 0, frameWidth, frameHeight);

          await seekToTime(video, startTime);
          tempCtx.clearRect(0, 0, frameWidth, frameHeight);
          tempCtx.drawImage(video, 0, 0, frameWidth, frameHeight);
          const startFrameData = tempCtx.getImageData(0, 0, frameWidth, frameHeight);

          const blendedData = tempCtx.createImageData(frameWidth, frameHeight);
          for (let p = 0; p < startFrameData.data.length; p += 4) {
            blendedData.data[p] = endFrameData.data[p] * (1 - alpha) + startFrameData.data[p] * alpha;
            blendedData.data[p + 1] = endFrameData.data[p + 1] * (1 - alpha) + startFrameData.data[p + 1] * alpha;
            blendedData.data[p + 2] = endFrameData.data[p + 2] * (1 - alpha) + startFrameData.data[p + 2] * alpha;
            blendedData.data[p + 3] = endFrameData.data[p + 3] * (1 - alpha) + startFrameData.data[p + 3] * alpha;
          }

          tempCtx.putImageData(blendedData, 0, 0);
          if (useMask) {
            applyMask(tempCtx, frameWidth, frameHeight, maskInvert && maskInvert.checked);
          }
          ctx.drawImage(tempCanvas, x, y);
        }

        const percent = Math.round(((i + 1) / totalFrames) * 100);
        progressBar.style.width = percent + '%';
        progressBar.textContent = percent + '%';
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    }

    uploadSection.addEventListener('click', () => videoInput.click());
    uploadSection.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadSection.classList.add('is-drag');
    });
    uploadSection.addEventListener('dragleave', () => {
      uploadSection.classList.remove('is-drag');
    });
    uploadSection.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadSection.classList.remove('is-drag');
      const file = e.dataTransfer.files[0];
      handleVideoFile(file);
    });
    videoInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      handleVideoFile(file);
    });

    if (trimStartInput) {
      trimStartInput.addEventListener('input', () => {
        if (!trimReady || !currentVideo) { return; }
        const duration = currentVideo.duration;
        const startValue = parseFloat(trimStartInput.value || '0');
        setTrimRange(startValue, trimEnd, duration, false);
        currentVideo.currentTime = Math.min(Math.max(trimStart, 0), duration - 0.001);
        currentVideo.pause();
      });
    }

    if (trimEndInput) {
      trimEndInput.addEventListener('input', () => {
        if (!trimReady || !currentVideo) { return; }
        const duration = currentVideo.duration;
        const endValue = parseFloat(trimEndInput.value || '0');
        setTrimRange(trimStart, endValue, duration, true);
        currentVideo.currentTime = Math.min(Math.max(trimEnd, 0), duration - 0.001);
        currentVideo.pause();
      });
    }

    if (videoPreview) {
      videoPreview.addEventListener('seeking', () => {
        if (!trimReady || !currentVideo) { return; }
        if (videoPreview.currentTime < trimStart || videoPreview.currentTime > trimEnd) {
          videoPreview.currentTime = trimStart;
        }
      });
      videoPreview.addEventListener('timeupdate', () => {
        if (!trimReady || !currentVideo) { return; }
        if (trimEnd <= trimStart) { return; }
        if (videoPreview.currentTime < trimStart) {
          videoPreview.currentTime = trimStart;
          return;
        }
        if (videoPreview.currentTime >= trimEnd) {
          videoPreview.currentTime = trimStart;
          if (!videoPreview.paused) { videoPreview.play().catch(() => {}); }
        }
      });
    }

    maskInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      handleMaskFile(file);
    });
    maskClear.addEventListener('click', clearMask);

    if (maskDrop) {
      maskDrop.addEventListener('click', () => {
        maskInput.click();
      });
      maskDrop.addEventListener('dragover', (e) => {
        e.preventDefault();
        maskDrop.classList.add('is-drag');
      });
      maskDrop.addEventListener('dragleave', () => {
        maskDrop.classList.remove('is-drag');
      });
      maskDrop.addEventListener('drop', (e) => {
        e.preventDefault();
        maskDrop.classList.remove('is-drag');
      const file = e.dataTransfer.files[0];
      handleMaskFile(file);
    });
  }

    maskSourceInputs.forEach(input => {
      input.addEventListener('change', () => {
        maskCache = null;
        maskCacheWidth = 0;
        maskCacheHeight = 0;
      });
    });

    function mulberry32(seed) {
      return function() {
        let t = seed += 0x6D2B79F5;
        t = Math.imul(t ^ t >>> 15, t | 1);
        t ^= t + Math.imul(t ^ t >>> 7, t | 61);
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
      };
    }

    function lerp(a, b, t) { return a + (b - a) * t; }
    function smoothstep(edge0, edge1, x) {
      const t = Math.min(1, Math.max(0, (x - edge0) / (edge1 - edge0)));
      return t * t * (3 - 2 * t);
    }

    function hash2(x, y) {
      let h = x * 374761393 + y * 668265263;
      h = (h ^ (h >> 13)) * 1274126177;
      return (h ^ (h >> 16)) >>> 0;
    }

    function valueNoise(x, y) {
      const x0 = Math.floor(x);
      const y0 = Math.floor(y);
      const xf = x - x0;
      const yf = y - y0;
      const h00 = hash2(x0, y0) / 4294967295;
      const h10 = hash2(x0 + 1, y0) / 4294967295;
      const h01 = hash2(x0, y0 + 1) / 4294967295;
      const h11 = hash2(x0 + 1, y0 + 1) / 4294967295;
      const u = smoothstep(0, 1, xf);
      const v = smoothstep(0, 1, yf);
      return lerp(lerp(h00, h10, u), lerp(h01, h11, u), v);
    }

    function fbm(x, y, octaves) {
      let value = 0;
      let amp = 0.5;
      let freq = 1;
      for (let i = 0; i < octaves; i++) {
        value += valueNoise(x * freq, y * freq) * amp;
        freq *= 2;
        amp *= 0.5;
      }
      return value;
    }

    function ridged(x, y) {
      let sum = 0;
      let amp = 0.5;
      let freq = 1;
      for (let i = 0; i < 4; i++) {
        const n = valueNoise(x * freq, y * freq);
        sum += (1 - Math.abs(2 * n - 1)) * amp;
        freq *= 2;
        amp *= 0.5;
      }
      return sum;
    }

    function worley(x, y) {
      const xi = Math.floor(x);
      const yi = Math.floor(y);
      let minDist = 10;
      for (let j = -1; j <= 1; j++) {
        for (let i = -1; i <= 1; i++) {
          const hx = hash2(xi + i, yi + j);
          const hy = hash2(xi + i + 17, yi + j + 29);
          const fx = (hx / 4294967295);
          const fy = (hy / 4294967295);
          const px = xi + i + fx;
          const py = yi + j + fy;
          const dx = x - px;
          const dy = y - py;
          minDist = Math.min(minDist, Math.sqrt(dx * dx + dy * dy));
        }
      }
      return Math.min(1, minDist);
    }

    function generateMaskTexture() {
      const frameWidth = parseInt(root.querySelector('#sequenceFrameWidth').value, 10) || 128;
      const frameHeight = parseInt(root.querySelector('#sequenceFrameHeight').value, 10) || 128;
      const edge = parseFloat(maskEdge.value || '0.28');
      const polar = parseFloat(maskPolar.value || '0');
      const warp = parseFloat(maskWarp.value || '0.25');
      const swirl = parseFloat(maskSwirl.value || '0.15');
      const pixelate = parseFloat(maskPixelate.value || '0');
      const threshold = parseFloat(maskThreshold.value || '0');
      const scale = parseFloat(maskScale.value || '1');
      const intensity = parseFloat(maskIntensity.value || '1');
      const contrast = parseFloat(maskContrast.value || '1');
      const gamma = parseFloat(maskGamma.value || '1');
      const tiling = parseInt(maskTiling.value || '1', 10);

      maskCanvas.width = frameWidth;
      maskCanvas.height = frameHeight;

      const ctx = maskCanvas.getContext('2d');
      const imageData = ctx.createImageData(frameWidth, frameHeight);
      const data = imageData.data;
      const rng = mulberry32(1337);

      const invW = 1 / frameWidth;
      const invH = 1 / frameHeight;
      const shape = maskShape.value || 'radial';
      const noiseType = maskNoiseType.value || 'perlin';

      for (let y = 0; y < frameHeight; y++) {
        for (let x = 0; x < frameWidth; x++) {
          const idx = (y * frameWidth + x) * 4;
          let baseFx = x * invW;
          let baseFy = y * invH;
          if (scale !== 1) {
            baseFx = (baseFx - 0.5) / scale + 0.5;
            baseFy = (baseFy - 0.5) / scale + 0.5;
          }
          if (baseFx < 0 || baseFx > 1 || baseFy < 0 || baseFy > 1) {
            data[idx] = 255;
            data[idx + 1] = 255;
            data[idx + 2] = 255;
            data[idx + 3] = 0;
            continue;
          }
          let fx = baseFx;
          let fy = baseFy;

          if (pixelate > 0) {
            const step = Math.max(1, Math.floor(lerp(1, 24, pixelate)));
            fx = Math.floor(fx * frameWidth / step) * step / frameWidth;
            fy = Math.floor(fy * frameHeight / step) * step / frameHeight;
          }

          if (polar > 0) {
            const cx = fx - 0.5;
            const cy = fy - 0.5;
            const radius = Math.min(0.5, Math.sqrt(cx * cx + cy * cy));
            const angle = Math.atan2(cy, cx);
            const mappedX = (angle / (Math.PI * 2) + 0.5);
            const mappedY = radius * 2;
            const seamWidth = 0.04;
            const seamBlend = smoothstep(0, 1, Math.min(mappedX, 1 - mappedX) / seamWidth);
            fx = lerp(fx, mappedX, polar * seamBlend);
            fy = lerp(fy, mappedY, polar);
            fx = Math.min(1, Math.max(0, fx));
            fy = Math.min(1, Math.max(0, fy));
          }

          if (swirl > 0) {
            const cx = fx - 0.5;
            const cy = fy - 0.5;
            const radius = Math.sqrt(cx * cx + cy * cy);
            const ang = Math.atan2(cy, cx) + radius * swirl * 4;
            fx = 0.5 + Math.cos(ang) * radius;
            fy = 0.5 + Math.sin(ang) * radius;
            fx = Math.min(1, Math.max(0, fx));
            fy = Math.min(1, Math.max(0, fy));
          }

          if (warp > 0) {
            const warpVal = fbm(fx * tiling * 3, fy * tiling * 3, 3);
            fx = Math.min(1, Math.max(0, fx + (warpVal - 0.5) * warp));
            fy = Math.min(1, Math.max(0, fy + (warpVal - 0.5) * warp));
          }

          if (fx < 0 || fx > 1 || fy < 0 || fy > 1) {
            data[idx] = 255;
            data[idx + 1] = 255;
            data[idx + 2] = 255;
            data[idx + 3] = 0;
            continue;
          }

          const nx = fx * tiling * 4;
          const ny = fy * tiling * 4;
          let n = 0;
          if (noiseType === 'worley') {
            n = 1 - worley(nx, ny);
          } else if (noiseType === 'ridged') {
            n = ridged(nx, ny);
          } else if (noiseType === 'white') {
            n = rng();
          } else {
            n = fbm(nx, ny, 4);
          }

          let shapeMask = 1;
          if (shape === 'radial') {
            const dx = baseFx - 0.5;
            const dy = baseFy - 0.5;
            const d = Math.sqrt(dx * dx + dy * dy) / 0.5;
            shapeMask = 1 - smoothstep(1 - edge, 1, d);
          } else if (shape === 'linear') {
            const d = Math.abs(baseFx - 0.5) / 0.5;
            shapeMask = 1 - smoothstep(1 - edge, 1, d);
          } else if (shape === 'diamond') {
            const d = (Math.abs(baseFx - 0.5) + Math.abs(baseFy - 0.5)) / 0.5;
            shapeMask = 1 - smoothstep(1 - edge, 1, d);
          } else {
            const d = Math.max(Math.abs(baseFx - 0.5), Math.abs(baseFy - 0.5)) / 0.5;
            shapeMask = 1 - smoothstep(1 - edge, 1, d);
          }

          let alpha = n * shapeMask;
          // Ensure outer edge fades to black even when gamma=1
          alpha *= smoothstep(0, 1, shapeMask);
          alpha *= intensity;
          if (contrast !== 1) {
            alpha = Math.min(1, Math.max(0, (alpha - 0.5) * contrast + 0.5));
          }
          if (gamma !== 1) {
            alpha = Math.pow(Math.min(1, Math.max(0, alpha)), 1 / gamma);
          }
          if (threshold > 0) {
            alpha = alpha >= threshold ? 1 : 0;
          }

          const a = Math.round(Math.min(1, Math.max(0, alpha)) * 255);
          data[idx] = 255;
          data[idx + 1] = 255;
          data[idx + 2] = 255;
          data[idx + 3] = a;
        }
      }

      ctx.putImageData(imageData, 0, 0);
      generatedMask = maskCanvas;
      maskToggle.checked = true;
      const generatorRadio = Array.from(maskSourceInputs).find(input => input.value === 'generator');
      if (generatorRadio) { generatorRadio.checked = true; }
    }

    generateMaskTexture();

    if (maskGenerateBtn) {
      maskGenerateBtn.addEventListener('click', generateMaskTexture);
    }
    if (maskDownloadBtn) {
      maskDownloadBtn.addEventListener('click', () => {
        if (!generatedMask) { return; }
        const link = document.createElement('a');
        link.download = 'mask-texture.png';
        link.href = generatedMask.toDataURL('image/png');
        link.click();
      });
    }

    const realtimeInputs = [
      maskNoiseType, maskShape, maskEdge, maskPolar, maskWarp, maskSwirl,
      maskPixelate, maskThreshold, maskScale, maskIntensity, maskContrast, maskGamma, maskTiling
    ];

    function updateMaskValues() {
      const valueEls = root.querySelectorAll('[data-mask-value]');
      valueEls.forEach((el) => {
        const id = el.getAttribute('data-mask-value');
        const input = root.querySelector('#' + id);
        if (!input) { return; }
        el.textContent = input.value;
      });
    }

    realtimeInputs.forEach((input) => {
      if (!input) { return; }
      input.addEventListener('input', () => {
    generateMaskTexture();
    updateMaskValues();
        updateMaskValues();
      });
      input.addEventListener('change', () => {
        generateMaskTexture();
        updateMaskValues();
      });
    });

    updateMaskValues();

    function collectMaskSettings() {
      return {
        noiseType: maskNoiseType.value,
        shape: maskShape.value,
        edge: maskEdge.value,
        polar: maskPolar.value,
        warp: maskWarp.value,
        swirl: maskSwirl.value,
        pixelate: maskPixelate.value,
        threshold: maskThreshold.value,
        scale: maskScale.value,
        intensity: maskIntensity.value,
        contrast: maskContrast.value,
        gamma: maskGamma.value,
        tiling: maskTiling.value
      };
    }

    function applyMaskSettings(settings) {
      if (!settings) { return; }
      maskNoiseType.value = settings.noiseType ?? maskNoiseType.value;
      maskShape.value = settings.shape ?? maskShape.value;
      maskEdge.value = settings.edge ?? maskEdge.value;
      maskPolar.value = settings.polar ?? maskPolar.value;
      maskWarp.value = settings.warp ?? maskWarp.value;
      maskSwirl.value = settings.swirl ?? maskSwirl.value;
      maskPixelate.value = settings.pixelate ?? maskPixelate.value;
      maskThreshold.value = settings.threshold ?? maskThreshold.value;
      maskScale.value = settings.scale ?? maskScale.value;
      maskIntensity.value = settings.intensity ?? maskIntensity.value;
      maskContrast.value = settings.contrast ?? maskContrast.value;
      maskGamma.value = settings.gamma ?? maskGamma.value;
      maskTiling.value = settings.tiling ?? maskTiling.value;
      generateMaskTexture();
      updateMaskValues();
    }

    function collectSequenceSettings() {
      return {
        cols: root.querySelector('#sequenceGridCols').value,
        rows: root.querySelector('#sequenceGridRows').value,
        frameWidth: root.querySelector('#sequenceFrameWidth').value,
        frameHeight: root.querySelector('#sequenceFrameHeight').value,
        fps: root.querySelector('#sequenceFps').value,
        loopMode: loopModeSelect.value,
        overlapFrames: overlapFramesInput ? overlapFramesInput.value : ''
      };
    }

    function applySequenceSettings(settings) {
      if (!settings) { return; }
      const colsInput = root.querySelector('#sequenceGridCols');
      const rowsInput = root.querySelector('#sequenceGridRows');
      const widthInput = root.querySelector('#sequenceFrameWidth');
      const heightInput = root.querySelector('#sequenceFrameHeight');
      const fpsValue = settings.fps ?? fpsInput.value;
      const loopModeValue = settings.loopMode ?? loopModeSelect.value;
      if (colsInput && settings.cols != null) { colsInput.value = settings.cols; }
      if (rowsInput && settings.rows != null) { rowsInput.value = settings.rows; }
      if (widthInput && settings.frameWidth != null) { widthInput.value = settings.frameWidth; }
      if (heightInput && settings.frameHeight != null) { heightInput.value = settings.frameHeight; }
      fpsInput.value = fpsValue;
      loopModeSelect.value = loopModeValue;
      if (overlapFramesInput && settings.overlapFrames != null) { overlapFramesInput.value = settings.overlapFrames; }
      updateLoopModeUI();
      updateAutoMeta();
      updateOverlapNoteUI();
      updateTotalFramesUI();
    }

    const builtinPresets = [
      { id: 'soft', name: 'Soft Edge', values: { noiseType: 'perlin', shape: 'radial', edge: 0.35, polar: 0.05, warp: 0.18, swirl: 0.1, pixelate: 0, threshold: 0, scale: 1, intensity: 1, contrast: 1, gamma: 1, tiling: 1 } },
      { id: 'hard', name: 'Hard Edge', values: { noiseType: 'perlin', shape: 'square', edge: 0.12, polar: 0, warp: 0.08, swirl: 0, pixelate: 0, threshold: 0.12, scale: 1, intensity: 1, contrast: 1.2, gamma: 1, tiling: 1 } },
      { id: 'dissolve', name: 'Dissolve', values: { noiseType: 'worley', shape: 'radial', edge: 0.25, polar: 0, warp: 0.25, swirl: 0.2, pixelate: 0, threshold: 0.4, scale: 1, intensity: 1, contrast: 1.15, gamma: 1, tiling: 2 } },
      { id: 'noise', name: 'Noise Soft', values: { noiseType: 'white', shape: 'radial', edge: 0.3, polar: 0, warp: 0.15, swirl: 0.05, pixelate: 0.15, threshold: 0, scale: 1, intensity: 1, contrast: 0.9, gamma: 1, tiling: 3 } }
    ];

    function loadSavedPresets() {
      try {
        const raw = localStorage.getItem('sequenceMaskPresets');
        return raw ? JSON.parse(raw) : {};
      } catch (e) {
        return {};
      }
    }

    function savePresetsMap(map) {
      try {
        localStorage.setItem('sequenceMaskPresets', JSON.stringify(map));
      } catch (e) {
        console.warn('Unable to save presets map', e);
      }
    }

    function normalizePresetPayload(payload) {
      if (!payload) { return null; }
      if (payload.mask || payload.sequence) { return payload; }
      return { mask: payload };
    }

    function refreshPresetSelect() {
      if (!maskPresetSelect) { return; }
      const current = maskPresetSelect.value;
      const placeholderText = maskPresetSelect.querySelector('option')?.textContent || 'Preset';
      maskPresetSelect.innerHTML = '';
      const placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.textContent = placeholderText;
      maskPresetSelect.appendChild(placeholder);
      builtinPresets.forEach(preset => {
        const option = document.createElement('option');
        option.value = 'builtin:' + preset.id;
        option.textContent = preset.name;
        maskPresetSelect.appendChild(option);
      });
      const saved = loadSavedPresets();
      Object.keys(saved).forEach(name => {
        const option = document.createElement('option');
        option.value = 'saved:' + name;
        option.textContent = name;
        maskPresetSelect.appendChild(option);
      });
      if (current) { maskPresetSelect.value = current; }
    }

    if (maskSaveBtn) {
      maskSaveBtn.addEventListener('click', () => {
        const name = prompt('저장할 이름을 입력하세요');
        if (!name) { return; }
        const data = {
          mask: collectMaskSettings(),
          sequence: collectSequenceSettings()
        };
        try {
          const map = loadSavedPresets();
          map[name] = data;
          savePresetsMap(map);
          refreshPresetSelect();
          if (maskPresetSelect) {
            maskPresetSelect.value = 'saved:' + name;
          }
          if (maskStatus) { maskStatus.textContent = '저장됨: ' + name; }
        } catch (e) {
          console.warn('Unable to save mask settings', e);
          if (maskStatus) { maskStatus.textContent = '저장 실패'; }
        }
      });
    }

    refreshPresetSelect();

    if (maskPresetSelect) {
      maskPresetSelect.addEventListener('change', () => {
        const value = maskPresetSelect.value;
        if (!value) { return; }
        if (value.startsWith('builtin:')) {
          const id = value.replace('builtin:', '');
          const preset = builtinPresets.find(p => p.id === id);
          if (preset) {
            applyMaskSettings(preset.values);
            if (maskStatus) { maskStatus.textContent = '불러옴: ' + preset.name; }
          }
        } else if (value.startsWith('saved:')) {
          const name = value.replace('saved:', '');
          const saved = loadSavedPresets();
          const payload = normalizePresetPayload(saved[name]);
          if (payload) {
            if (payload.mask) { applyMaskSettings(payload.mask); }
            if (payload.sequence) { applySequenceSettings(payload.sequence); }
            if (maskStatus) { maskStatus.textContent = '불러옴: ' + name; }
          }
        }
      });
    }

    root.querySelectorAll('[data-sequence-grid]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const value = btn.getAttribute('data-sequence-grid');
        const [cols, rows] = value.split('x').map(Number);
        setGrid(cols, rows);
        updateOverlapNoteUI();
      });
    });

    const gridColsInput = root.querySelector('#sequenceGridCols');
    const gridRowsInput = root.querySelector('#sequenceGridRows');
    if (gridColsInput) {
      gridColsInput.addEventListener('input', updateOverlapNoteUI);
      gridColsInput.addEventListener('change', updateOverlapNoteUI);
    }
    if (gridRowsInput) {
      gridRowsInput.addEventListener('input', updateOverlapNoteUI);
      gridRowsInput.addEventListener('change', updateOverlapNoteUI);
    }

    loopModeSelect.addEventListener('change', updateLoopModeUI);
    updateLoopModeUI();
    updateOverlapNoteUI();
    updateTotalFramesUI();

    document.addEventListener('app:lang', () => {
      if (autoMeta) {
        defaultAutoMeta = autoMeta.innerHTML;
        updateAutoMeta();
      }
      updateTotalFramesUI();
      updateOverlapNoteUI();
    });

    if (fpsInput) {
      fpsInput.addEventListener('input', updateTotalFramesUI);
      fpsInput.addEventListener('change', updateTotalFramesUI);
    }

    if (overlapFramesInput) {
      overlapFramesInput.addEventListener('input', updateOverlapNoteUI);
      overlapFramesInput.addEventListener('change', updateOverlapNoteUI);
    }

    autoGridBtn.addEventListener('click', () => {
      if (!currentVideo || !isFinite(currentVideo.duration) || currentVideo.duration <= 0) {
        showError('먼저 비디오를 업로드해 주세요.');
        return;
      }
      const fps = Math.max(1, parseInt(fpsInput.value || '24', 10));
      const trim = getTrimRange();
      const duration = trim.duration || currentVideo.duration;
      if (!duration || duration < MIN_TRIM_GAP) {
        showError('잘린 구간이 너무 짧습니다.');
        return;
      }
      let frames = Math.max(1, Math.round(duration * fps));
      const maxFrames = 256;
      let clamped = false;
      if (frames > maxFrames) {
        frames = maxFrames;
        clamped = true;
      }

      let cols = Math.ceil(Math.sqrt(frames));
      let rows = Math.ceil(frames / cols);
      if (cols > 16) {
        cols = 16;
        rows = Math.ceil(frames / cols);
      }
      if (rows > 16) {
        rows = 16;
        frames = 256;
        clamped = true;
      }

      setGrid(cols, rows);
      updateAutoMeta(frames, cols, rows, clamped);
    });

    generateBtn.addEventListener('click', async () => {
      if (!currentVideo) { return; }

      const cols = parseInt(root.querySelector('#sequenceGridCols').value, 10);
      const rows = parseInt(root.querySelector('#sequenceGridRows').value, 10);
      const frameWidth = parseInt(root.querySelector('#sequenceFrameWidth').value, 10);
      const frameHeight = parseInt(root.querySelector('#sequenceFrameHeight').value, 10);
      const loopMode = loopModeSelect.value;
      const overlapFrames = clampOverlapFrames(cols * rows);
      const trim = getTrimRange();
      if (!trim.duration || trim.duration < MIN_TRIM_GAP) {
        showError('잘린 구간이 너무 짧습니다.');
        return;
      }

      generateBtn.disabled = true;
      progress.classList.add('is-active');
      previewSection.classList.remove('is-active');
      const wasLooping = currentVideo.loop;
      const wasPlaying = !currentVideo.paused && !currentVideo.ended;
      currentVideo.loop = false;
      currentVideo.pause();

      try {
        await seekToTime(currentVideo, trim.start);
        if (loopMode === 'pingpong') {
          await generatePingPongSpriteSheet(currentVideo, cols, rows, frameWidth, frameHeight, trim.start, trim.end);
        } else if (loopMode === 'overlap') {
          await generateOverlapSpriteSheet(currentVideo, cols, rows, frameWidth, frameHeight, overlapFrames, trim.start, trim.end);
        } else {
          await generateDirectSpriteSheet(currentVideo, cols, rows, frameWidth, frameHeight, trim.start, trim.end);
        }
        previewSection.classList.add('is-active');
        previewSection.scrollIntoView({ behavior: 'smooth' });
      } catch (error) {
        alert('오류 발생: ' + error.message);
        console.error(error);
      } finally {
        currentVideo.loop = wasLooping;
        if (wasPlaying) { currentVideo.play().catch(() => {}); }
        generateBtn.disabled = false;
        progress.classList.remove('is-active');
      }
    });

    downloadBtn.addEventListener('click', () => {
      const link = document.createElement('a');
      const cols = root.querySelector('#sequenceGridCols').value;
      const rows = root.querySelector('#sequenceGridRows').value;
      const loopMode = loopModeSelect.value;

      let filename = `sprite-${cols}x${rows}`;
      if (loopMode === 'overlap') {
        const overlapFrames = clampOverlapFrames(parseInt(cols, 10) * parseInt(rows, 10));
        filename += `-overlap${overlapFrames}f`;
      } else if (loopMode === 'pingpong') {
        filename += `-pingpong`;
      }
      filename += '.png';

      link.download = filename;
      link.href = outputCanvas.toDataURL('image/png');
      link.click();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initSequenceGenerator(document.querySelector('.sequence-embed'));
  });
})();
