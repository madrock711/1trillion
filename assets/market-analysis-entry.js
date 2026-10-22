(function () {
    'use strict';

    var frame = 0;
    window.addEventListener('market-view-changed', function (event) {
        window.cancelAnimationFrame(frame);
        if (!event.detail || event.detail.view !== 'analysis') return;
        frame = window.requestAnimationFrame(function () {
            var panel = document.getElementById('market-view-analysis');
            var latest = document.querySelector('#research-archive .market-article-item');
            if (!panel || panel.hidden || !latest) return;
            // The previous chart's scroll offset does not belong to this view.
            latest.scrollIntoView({ block: 'end', behavior: 'instant' });
        });
    });
}());
