(function () {
    'use strict';

    // Run in the head, before the browser restores the old archive position.
    var view = new URLSearchParams(window.location.search).get('view') || 'analysis';
    var navigation = window.performance && typeof window.performance.getEntriesByType === 'function'
        && window.performance.getEntriesByType('navigation')[0];
    var hash = window.location.hash;
    if (view !== 'analysis' || !navigation || navigation.type !== 'reload'
        || (hash && hash !== '#research-archive')) return;

    var previousRestoration = window.history.scrollRestoration;
    window.history.scrollRestoration = 'manual';
    var stopped = false;
    var frame = 0;
    var observer;
    var timer;
    var gestures = ['wheel', 'touchstart', 'pointerdown', 'keydown'];

    function stop() {
        if (stopped) return;
        stopped = true;
        window.cancelAnimationFrame(frame);
        window.clearTimeout(timer);
        if (observer) observer.disconnect();
        gestures.forEach(function (name) { window.removeEventListener(name, stop, true); });
        window.removeEventListener('load', align);
        window.removeEventListener('technical-dashboard-ready', align);
        window.history.scrollRestoration = previousRestoration;
    }

    function align() {
        if (stopped) return;
        window.cancelAnimationFrame(frame);
        frame = window.requestAnimationFrame(function () {
            if (stopped) return;
            var panel = document.getElementById('market-view-analysis');
            var latest = document.querySelector('#research-archive .market-article-item');
            if (!panel || panel.hidden || !latest) return;
            // Leave the latest article, including its date and summary, at the bottom.
            latest.scrollIntoView({ block: 'end', behavior: 'instant' });
        });
    }

    gestures.forEach(function (name) { window.addEventListener(name, stop, { capture: true, passive: true }); });
    window.addEventListener('pagehide', stop, { once: true });
    window.addEventListener('load', align);
    window.addEventListener('technical-dashboard-ready', align);
    document.addEventListener('DOMContentLoaded', function () {
        if (stopped) return;
        align();
        // Initial snapshot/live rendering can change the height above the archive.
        if (window.ResizeObserver) {
            observer = new window.ResizeObserver(align);
            observer.observe(document.getElementById('main-content') || document.body);
        }
        timer = window.setTimeout(stop, 8000);
    }, { once: true });
}());
