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
    var keylines = Array.prototype.slice.call(article.querySelectorAll('.article-keyline'));

    function revealKeyline(element) {
        element.classList.add('is-revealed');
    }

    if (reducedMotion || !('IntersectionObserver' in window)) {
        keylines.forEach(revealKeyline);
    } else {
        var keylineObserver = new IntersectionObserver(function (entries, observer) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                revealKeyline(entry.target);
                observer.unobserve(entry.target);
            });
        }, {
            root: null,
            rootMargin: '-42% 0px -42% 0px',
            threshold: 0
        });

        keylines.forEach(function (keyline) {
            keylineObserver.observe(keyline);
        });
    }

    var toc = article.querySelector('.reading-toc');
    var targetTimer = 0;
    var destinationScrollHandler = null;
    var destinationFallback = 0;

    function emphasizeHeading(heading) {
        if (!heading) return;

        window.clearTimeout(targetTimer);
        article.querySelectorAll('.is-reading-target').forEach(function (element) {
            element.classList.remove('is-reading-target');
        });

        heading.setAttribute('data-reading-target-seen', 'true');
        heading.classList.add('is-reading-target');
        targetTimer = window.setTimeout(function () {
            heading.classList.remove('is-reading-target');
        }, reducedMotion ? 400 : 1500);
    }

    function emphasizeWhenVisible(heading) {
        if (!heading) return;

        window.clearTimeout(destinationFallback);
        if (destinationScrollHandler) {
            window.removeEventListener('scroll', destinationScrollHandler);
            destinationScrollHandler = null;
        }

        if (reducedMotion) {
            emphasizeHeading(heading);
            return;
        }

        function finishArrival() {
            window.clearTimeout(destinationFallback);
            if (destinationScrollHandler) {
                window.removeEventListener('scroll', destinationScrollHandler);
                destinationScrollHandler = null;
            }
            emphasizeHeading(heading);
        }

        destinationScrollHandler = function () {
            window.clearTimeout(destinationFallback);
            destinationFallback = window.setTimeout(finishArrival, 140);
        };

        window.addEventListener('scroll', destinationScrollHandler, { passive: true });
        destinationFallback = window.setTimeout(finishArrival, 3000);
    }

    if (toc) {
        toc.addEventListener('click', function (event) {
            var link = event.target.closest('a[href^="#"]');
            if (!link) return;

            var target = document.getElementById(decodeURIComponent(link.hash.slice(1)));
            emphasizeWhenVisible(target);
        });
    }

    if (window.location.hash) {
        window.setTimeout(function () {
            emphasizeWhenVisible(document.getElementById(decodeURIComponent(window.location.hash.slice(1))));
        }, reducedMotion ? 0 : 100);
    }
})();
