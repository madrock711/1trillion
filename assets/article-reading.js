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
    var keylineAnimations = typeof WeakMap === 'function' ? new WeakMap() : null;

    function replayKeyline(keyline) {
        keyline.classList.add('is-highlighted');

        if (typeof keyline.animate === 'function') {
            if (keylineAnimations) {
                var previousAnimation = keylineAnimations.get(keyline);
                if (previousAnimation) previousAnimation.cancel();
            }

            var animation = keyline.animate([
                { backgroundSize: '0% 100%' },
                { backgroundSize: '100% 100%' }
            ], {
                duration: 1100,
                easing: 'cubic-bezier(0.22, 1, 0.36, 1)'
            });

            if (keylineAnimations) keylineAnimations.set(keyline, animation);
            return;
        }

        keyline.classList.remove('is-sweeping');
        window.requestAnimationFrame(function () {
            window.requestAnimationFrame(function () {
                keyline.classList.add('is-sweeping');
            });
        });
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
