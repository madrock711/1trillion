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
    const loopModeSelect = root.querySelector('#sequenceLoopMode');
    const overlapControl = root.querySelector('#sequenceOverlapControl');
    const fpsInput = root.querySelector('#sequenceFps');
    const autoGridBtn = root.querySelector('#sequenceAutoGrid');
    const autoMeta = root.querySelector('#sequenceAutoMeta');
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
    const maskEdge = root.querySelector('#sequenceMaskEdge');
    const maskInner = root.querySelector('#sequenceMaskInner');
    const maskNoise = root.querySelector('#sequenceMaskNoise');
    const maskDissolve = root.querySelector('#sequenceMaskDissolve');
    const maskDistort = root.querySelector('#sequenceMaskDistort');
    const maskPresetButtons = root.querySelectorAll('[data-mask-preset]');
    let defaultAutoMeta = autoMeta ? autoMeta.innerHTML : '';

    let currentVideo = null;
    let maskImage = null;
    let maskUrl = '';
    let maskCache = null;
    let maskCacheWidth = 0;
    let maskCacheHeight = 0;
    let generatedMask = null;

    function updateLoopModeUI() {
      const loopMode = loopModeSelect.value;
      overlapControl.style.display = loopMode === 'overlap' ? 'block' : 'none';
    }

    function setGrid(cols, rows) {
      root.querySelector('#sequenceGridCols').value = cols;
      root.querySelector('#sequenceGridRows').value = rows;
    }

    function showError(message) {
      alert(message);
      videoPreview.style.display = 'none';
      generateBtn.disabled = true;
      videoInfo.style.display = 'none';
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
        currentVideo = videoPreview;
        generateBtn.disabled = false;

        videoInfo.style.display = 'block';
        videoInfoContent.innerHTML = `
          재생시간: ${testVideo.duration.toFixed(2)}초<br>
          해상도: ${testVideo.videoWidth} × ${testVideo.videoHeight}px<br>
          형식: ${file.type || '알 수 없음'}<br>
          파일크기: ${(file.size / 1024 / 1024).toFixed(2)}MB
        `;
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

        const onSeeked = () => {
          clearTimeout(timeoutId);
          video.removeEventListener('seeked', onSeeked);
          video.removeEventListener('error', onError);
          setTimeout(resolve, 50);
        };

        const onError = (e) => {
          clearTimeout(timeoutId);
          video.removeEventListener('seeked', onSeeked);
          video.removeEventListener('error', onError);
          reject(new Error('Video seek error: ' + e.message));
        };

        timeoutId = setTimeout(() => {
          video.removeEventListener('seeked', onSeeked);
          video.removeEventListener('error', onError);
          reject(new Error('Seek timeout'));
        }, 5000);

        video.addEventListener('seeked', onSeeked, { once: true });
        video.addEventListener('error', onError, { once: true });

        try {
          video.currentTime = safeTime;
        } catch (e) {
          clearTimeout(timeoutId);
          video.removeEventListener('seeked', onSeeked);
          video.removeEventListener('error', onError);
          reject(e);
        }
      });
    }

    async function generateDirectSpriteSheet(video, cols, rows, frameWidth, frameHeight) {
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

      const duration = video.duration;
      if (!duration || !isFinite(duration) || duration <= 0) {
        throw new Error('비디오 duration을 읽을 수 없습니다.');
      }

      canvas.width = cols * frameWidth;
      canvas.height = rows * frameHeight;
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const interval = duration / totalFrames;

      for (let i = 0; i < totalFrames; i++) {
        const row = Math.floor(i / cols);
        const col = i % cols;
        const time = (i * interval) % duration;

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

    async function generatePingPongSpriteSheet(video, cols, rows, frameWidth, frameHeight) {
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

      const duration = video.duration;
      if (!duration || !isFinite(duration) || duration <= 0) {
        throw new Error('비디오 duration을 읽을 수 없습니다.');
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
        const time = (timeIndex * interval) % duration;

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

    async function generateOverlapSpriteSheet(video, cols, rows, frameWidth, frameHeight, overlapPercent) {
      const totalFrames = cols * rows;
      const canvas = outputCanvas;
      const ctx = canvas.getContext('2d');
      const useMask = !!(maskToggle.checked && getMaskSource());

      if (video.readyState < 2) {
        await new Promise(resolve => video.addEventListener('loadedmetadata', resolve, { once: true }));
      }

      const duration = video.duration;
      if (!duration || !isFinite(duration) || duration <= 0) {
        throw new Error('비디오 duration을 읽을 수 없습니다.');
      }

      canvas.width = cols * frameWidth;
      canvas.height = rows * frameHeight;
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const overlapRatio = overlapPercent / 100;
      const overlapFrames = Math.ceil(totalFrames * overlapRatio);
      const uniqueFrames = totalFrames - overlapFrames;
      const overlapDuration = duration * overlapRatio;
      const cutTime = overlapDuration;

      const samplingDuration = duration - overlapDuration;
      const interval = samplingDuration / uniqueFrames;
      const overlapInterval = overlapDuration / overlapFrames;

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
          const time = cutTime + (i * interval);
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
          const alpha = (overlapIndex + 1) / overlapFrames;

          const startTime = overlapIndex * overlapInterval;
          const endTime = (duration - overlapDuration) + (overlapIndex * overlapInterval);

          await seekToTime(video, Math.min(endTime, duration - 0.001));
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

    function generateMaskTexture() {
      const frameWidth = parseInt(root.querySelector('#sequenceFrameWidth').value, 10) || 128;
      const frameHeight = parseInt(root.querySelector('#sequenceFrameHeight').value, 10) || 128;
      const edge = parseFloat(maskEdge.value || '0.25');
      const inner = parseFloat(maskInner.value || '0.2');
      const noise = parseFloat(maskNoise.value || '0.15');
      const dissolve = parseFloat(maskDissolve.value || '0');
      const distort = parseFloat(maskDistort.value || '0.08');

      maskCanvas.width = frameWidth;
      maskCanvas.height = frameHeight;

      const ctx = maskCanvas.getContext('2d');
      const imageData = ctx.createImageData(frameWidth, frameHeight);
      const data = imageData.data;
      const rng = mulberry32(Math.floor(Date.now() % 2147483647));

      const invW = 1 / frameWidth;
      const invH = 1 / frameHeight;

      for (let y = 0; y < frameHeight; y++) {
        for (let x = 0; x < frameWidth; x++) {
          const idx = (y * frameWidth + x) * 4;
          const fx = x * invW;
          const fy = y * invH;
          const offsetX = Math.sin((fy + fx) * Math.PI * 4) * distort * 0.5;
          const offsetY = Math.cos((fx - fy) * Math.PI * 4) * distort * 0.5;
          const ux = Math.min(1, Math.max(0, fx + offsetX));
          const uy = Math.min(1, Math.max(0, fy + offsetY));
          const distX = Math.min(ux, 1 - ux);
          const distY = Math.min(uy, 1 - uy);
          const dist = Math.min(distX, distY);
          const edgeWidth = Math.max(0.001, edge);
          let alpha = Math.min(1, Math.max(0, dist / edgeWidth));

          const dx = ux - 0.5;
          const dy = uy - 0.5;
          const radial = Math.sqrt(dx * dx + dy * dy) * 2;
          const innerFactor = 1 - Math.min(1, radial);
          alpha = alpha * (1 - inner) + alpha * innerFactor * inner;

          const n = (rng() + rng()) * 0.5;
          alpha = alpha * (1 - noise) + alpha * n * noise;

          if (dissolve > 0) {
            const threshold = dissolve;
            alpha = alpha * (n > threshold ? 1 : 0);
          }

          const a = Math.round(alpha * 255);
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

    function applyPreset(name) {
      const presets = {
        soft: { edge: 0.35, inner: 0.35, noise: 0.08, dissolve: 0, distort: 0.08 },
        hard: { edge: 0.12, inner: 0.05, noise: 0.02, dissolve: 0, distort: 0.02 },
        dissolve: { edge: 0.25, inner: 0.2, noise: 0.25, dissolve: 0.35, distort: 0.12 },
        noise: { edge: 0.28, inner: 0.15, noise: 0.35, dissolve: 0.05, distort: 0.18 }
      };
      const preset = presets[name];
      if (!preset) { return; }
      maskEdge.value = preset.edge;
      maskInner.value = preset.inner;
      maskNoise.value = preset.noise;
      maskDissolve.value = preset.dissolve;
      maskDistort.value = preset.distort;
      generateMaskTexture();
    }

    maskPresetButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const preset = btn.getAttribute('data-mask-preset');
        applyPreset(preset);
      });
    });

    root.querySelectorAll('[data-sequence-grid]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const value = btn.getAttribute('data-sequence-grid');
        const [cols, rows] = value.split('x').map(Number);
        setGrid(cols, rows);
      });
    });

    loopModeSelect.addEventListener('change', updateLoopModeUI);
    updateLoopModeUI();

    document.addEventListener('app:lang', () => {
      if (autoMeta) {
        defaultAutoMeta = autoMeta.innerHTML;
        updateAutoMeta();
      }
    });

    autoGridBtn.addEventListener('click', () => {
      if (!currentVideo || !isFinite(currentVideo.duration) || currentVideo.duration <= 0) {
        showError('먼저 비디오를 업로드해 주세요.');
        return;
      }
      const fps = Math.max(1, parseInt(fpsInput.value || '24', 10));
      const duration = currentVideo.duration;
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
      const overlapPercent = parseInt(root.querySelector('#sequenceOverlapPercent').value, 10);

      generateBtn.disabled = true;
      progress.classList.add('is-active');
      previewSection.classList.remove('is-active');

      try {
        if (loopMode === 'pingpong') {
          await generatePingPongSpriteSheet(currentVideo, cols, rows, frameWidth, frameHeight);
        } else if (loopMode === 'overlap') {
          await generateOverlapSpriteSheet(currentVideo, cols, rows, frameWidth, frameHeight, overlapPercent);
        } else {
          await generateDirectSpriteSheet(currentVideo, cols, rows, frameWidth, frameHeight);
        }
        previewSection.classList.add('is-active');
        previewSection.scrollIntoView({ behavior: 'smooth' });
      } catch (error) {
        alert('오류 발생: ' + error.message);
        console.error(error);
      } finally {
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
        const overlapPercent = root.querySelector('#sequenceOverlapPercent').value;
        filename += `-overlap${overlapPercent}`;
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
