(function () {
    'use strict';

    var article = document.querySelector('[data-reading-enhancements]');
    if (!article) return;

    var progress = document.querySelector('.article-reading-progress span');
    var progressFrame = 0;

    function updateProgress() {
        progressFrame = 0;
        if (!progress) return;

        var articleTop = article.getBoundingClientRect().top + window.scrollY;
        var articleHeight = article.offsetHeight;
        var scrollableDistance = Math.max(articleHeight - window.innerHeight, 1);
        var ratio = (window.scrollY - articleTop) / scrollableDistance;
        var clamped = Math.min(1, Math.max(0, ratio));

        progress.style.transform = 'scaleX(' + clamped.toFixed(4) + ')';
    }

    function requestProgressUpdate() {
        if (progressFrame) return;
        progressFrame = window.requestAnimationFrame(updateProgress);
    }

    window.addEventListener('scroll', requestProgressUpdate, { passive: true });
    window.addEventListener('resize', requestProgressUpdate);
    window.addEventListener('load', requestProgressUpdate);
    updateProgress();

    var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var readingParagraphs = Array.prototype.slice.call(article.querySelectorAll('.article-body section > p'));
    var keylines = [];

    readingParagraphs.forEach(function (paragraph) {
        Array.prototype.forEach.call(paragraph.querySelectorAll('strong, b'), function (keyline) {
            keyline.classList.add('article-keyline');
            keylines.push(keyline);
        });
    });

    if (reducedMotion) {
        keylines.forEach(function (keyline) {
            keyline.classList.add('is-highlighted');
        });
        return;
    }

    var activeParagraph = null;
    var centerFrame = 0;
    var keylineEffects = typeof WeakMap === 'function' ? new WeakMap() : null;

    function replayKeyline(keyline) {
        var previousEffect = keylineEffects ? keylineEffects.get(keyline) : null;
        if (previousEffect) {
            window.clearTimeout(previousEffect.timer);
            if (previousEffect.animation) previousEffect.animation.cancel();
        }

        keyline.style.backgroundImage = 'none';
        keyline.style.backgroundColor = 'rgba(68, 209, 122, 0)';
        keyline.classList.add('is-highlighted');

        var effect = {
            animation: null,
            timer: 0
        };
        if (keylineEffects) keylineEffects.set(keyline, effect);

        effect.timer = window.setTimeout(function () {
            if (typeof keyline.animate === 'function') {
                effect.animation = keyline.animate([
                    { backgroundColor: 'rgba(68, 209, 122, 0)' },
                    { backgroundColor: 'rgba(68, 209, 122, 0.28)' }
                ], {
                    duration: 1000,
                    easing: 'ease-out',
                    fill: 'forwards'
                });

                effect.animation.onfinish = function () {
                    keyline.style.removeProperty('background-image');
                    keyline.style.removeProperty('background-color');
                    effect.animation.cancel();
                    if (keylineEffects && keylineEffects.get(keyline) === effect) {
                        keylineEffects.delete(keyline);
                    }
                };
                return;
            }

            keyline.classList.remove('is-sweeping');
            window.requestAnimationFrame(function () {
                keyline.classList.add('is-sweeping');
                keyline.style.removeProperty('background-image');
                keyline.style.removeProperty('background-color');
            });
        }, 90);
    }

    function getCenterCandidate() {
        var viewportHeight = window.innerHeight;
        var centerY = viewportHeight / 2;
        var best = null;
        var bestDistance = Infinity;

        readingParagraphs.forEach(function (paragraph) {
            var rect = paragraph.getBoundingClientRect();
            if (rect.height < 10 || rect.bottom < 0 || rect.top > viewportHeight) return;

            var paragraphCenter = rect.top + rect.height / 2;
            var distance = Math.abs(paragraphCenter - centerY);
            if (distance >= bestDistance) return;

            bestDistance = distance;
            best = paragraph;
        });

        return best;
    }

    function updateCenterHighlight() {
        centerFrame = 0;
        var candidate = getCenterCandidate();
        if (!candidate || candidate === activeParagraph) return;

        activeParagraph = candidate;
        Array.prototype.forEach.call(candidate.querySelectorAll('.article-keyline'), replayKeyline);
    }

    function requestCenterUpdate() {
        if (centerFrame) return;
        centerFrame = window.requestAnimationFrame(updateCenterHighlight);
    }

    window.addEventListener('scroll', requestCenterUpdate, { passive: true });
    window.addEventListener('resize', requestCenterUpdate);
    updateCenterHighlight();
})();
