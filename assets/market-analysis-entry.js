(function () {
    'use strict';

    var frame = 0;
    var observer;
    var timer;
    var active = false;
    var gestures = ['wheel', 'touchstart', 'pointerdown', 'keydown'];

    function stop() {
        active = false;
        window.cancelAnimationFrame(frame);
        window.clearTimeout(timer);
        if (observer) observer.disconnect();
        gestures.forEach(function (name) { window.removeEventListener(name, stop, true); });
    }

    function align() {
        if (!active) return;
        window.cancelAnimationFrame(frame);
        frame = window.requestAnimationFrame(function () {
            var panel = document.getElementById('market-view-analysis');
            var latest = document.querySelector('#research-archive .market-article-item');
            if (!active || !panel || panel.hidden || !latest) return;
            latest.scrollIntoView({ block: 'end', behavior: 'instant' });
        });
    }

    window.addEventListener('market-view-changed', function (event) {
        stop();
        if (!event.detail || event.detail.view !== 'analysis') return;
        active = true;
        align();
        // A delayed initial snapshot can still change the layout after tab switching.
        if (window.ResizeObserver) {
            observer = new window.ResizeObserver(align);
            observer.observe(document.getElementById('main-content'));
        }
        gestures.forEach(function (name) { window.addEventListener(name, stop, { capture: true, passive: true }); });
        timer = window.setTimeout(stop, 8000);
    });
    window.addEventListener('pagehide', stop);
}());
