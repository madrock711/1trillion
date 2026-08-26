(function () {
    'use strict';

    var tabs = document.querySelector('.market-article-view-tabs');
    var header = document.querySelector('body > header');
    if (!tabs || !header) return;

    var sentinel = document.createElement('span');
    sentinel.className = 'market-article-view-tabs-sentinel';
    sentinel.setAttribute('aria-hidden', 'true');
    tabs.parentNode.insertBefore(sentinel, tabs);

    var frame = 0;

    function update() {
        frame = 0;
        var headerHeight = Math.ceil(header.getBoundingClientRect().height);
        tabs.style.setProperty('--market-article-tabs-top', headerHeight + 'px');
        tabs.classList.toggle('is-floating', sentinel.getBoundingClientRect().top <= headerHeight);
    }

    function scheduleUpdate() {
        if (frame) return;
        frame = window.requestAnimationFrame(update);
    }

    window.addEventListener('scroll', scheduleUpdate, { passive: true });
    window.addEventListener('resize', scheduleUpdate, { passive: true });
    window.addEventListener('pageshow', scheduleUpdate);

    if ('ResizeObserver' in window) {
        new ResizeObserver(scheduleUpdate).observe(header);
    }

    scheduleUpdate();
}());
