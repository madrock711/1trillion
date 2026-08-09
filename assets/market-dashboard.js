(function () {
    'use strict';

    var root = document.querySelector('[data-dashboard-source]');
    if (!root) return;

    document.documentElement.classList.add('market-dashboard-enhanced');

    var validViews = ['analysis', 'strategy', 'technical'];
    var viewLinks = Array.prototype.slice.call(document.querySelectorAll('[data-market-view]'));
    var viewPanels = Array.prototype.slice.call(document.querySelectorAll('[data-view-panel]'));
    var loadState = document.getElementById('dashboard-load-state');
    var dashboardData = null;
    var liveMarketSource = root.getAttribute('data-live-market-source');
    var kodexVolumeSource = root.getAttribute('data-kodex-volume-source');
    var kodexIntradaySource = root.getAttribute('data-kodex-intraday-source');
    var selectedInstrumentId = null;
    var latestLiveData = null;
    var liveRefreshTimer = null;
    var liveRefreshPromise = null;
    var lastLiveRefreshAt = 0;
    var selectedKodexPeriod = '3m';
    var selectedKodexChartMode = 'daily';
    var selectedKodexIntradayDate = '';
    var selectedKodexIntradayInterval = 5;
    var kodexIntradayRenderToken = 0;
    var kospiTechnicalHistory = [];
    var kospiHistoryRequestToken = 0;
    var kospiIntradayRenderToken = 0;
    var kospiIntradayForceRefresh = false;
    var kospiIntradayViewCache = {};
    var kospiIntradayAbortController = null;
    var kospiIntradayRequestDate = '';
    var compositeMomentumState = { key: '', days: [], pending: null };
    var compositeMomentumRenderToken = 0;
    var compositeMomentumForceRefresh = false;
    var linkedChartViews = {};
    var linkedChartHoverSelection = null;
    var linkedChartLockedSelection = null;
    var technicalCardOrderStorageKey = 'hpmplab-technical-card-order-v2';
    var defaultTechnicalCardOrder = [
        'kospi-flow',
        'kodex-history',
        'composite-momentum',
        'tqqq-history',
        'kodex-technical',
        'kodex-quote',
        'kodex-range',
        'kodex-investor',
        'kodex-levels',
        'kodex-market-context'
    ];

    function clear(node) {
        if (node && node.id && linkedChartViews[node.id]) delete linkedChartViews[node.id];
        while (node && node.firstChild) node.removeChild(node.firstChild);
    }

    function make(tagName, className, text) {
        var node = document.createElement(tagName);
        if (className) node.className = className;
        if (text !== undefined && text !== null) node.textContent = text;
        return node;
    }

    function makeSvg(tagName, attributes) {
        var node = document.createElementNS('http://www.w3.org/2000/svg', tagName);
        Object.keys(attributes || {}).forEach(function (key) {
            node.setAttribute(key, String(attributes[key]));
        });
        return node;
    }

    function formatNumber(value, maximumFractionDigits) {
        if (typeof value !== 'number' || !Number.isFinite(value)) return '데이터 없음';
        return new Intl.NumberFormat('ko-KR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: maximumFractionDigits === undefined ? 2 : maximumFractionDigits
        }).format(value);
    }

    function formatSigned(value, unit, maximumFractionDigits) {
        if (typeof value !== 'number' || !Number.isFinite(value)) return '데이터 없음';
        var sign = value > 0 ? '+' : value < 0 ? '-' : '';
        return sign + formatNumber(
            Math.abs(value),
            maximumFractionDigits === undefined ? 0 : maximumFractionDigits
        ) + (unit || '');
    }

    function formatPrice(value, unit) {
        if (typeof value !== 'number' || !Number.isFinite(value)) return '데이터 없음';
        var digits = unit === '원' ? 0 : 2;
        return formatNumber(value, digits) + (unit === '원' ? '원' : '');
    }

    function formatKstDateTime(value) {
        var timestamp = Date.parse(value);
        if (!Number.isFinite(timestamp)) return '시각 확인 불가';
        if (window.MarketDashboardLive && typeof window.MarketDashboardLive.formatAsOfDisplay === 'function') {
            return window.MarketDashboardLive.formatAsOfDisplay(timestamp);
        }
        return new Intl.DateTimeFormat('ko-KR', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hourCycle: 'h23'
        }).format(new Date(timestamp)) + ' KST';
    }

    function kstTimestampFromLabel(label, fallback) {
        var reference = formatKstDateTime(fallback);
        var referenceMatch = /^(\d{4})년\s+(\d{1,2})월\s+(\d{1,2})일/.exec(reference);
        var fullMatch = /^(?:(\d{4})년\s+)?(\d{1,2})월\s+(\d{1,2})일\s+(\d{1,2}):(\d{2})/.exec(label || '');
        var shortMatch = /^(\d{1,2}):(\d{2})$/.exec(label || '');
        if (!referenceMatch || (!fullMatch && !shortMatch)) return fallback;
        var year = fullMatch && fullMatch[1] ? fullMatch[1] : referenceMatch[1];
        var month = fullMatch ? fullMatch[2] : referenceMatch[2];
        var day = fullMatch ? fullMatch[3] : referenceMatch[3];
        var hour = fullMatch ? fullMatch[4] : shortMatch[1];
        var minute = fullMatch ? fullMatch[5] : shortMatch[2];
        function pad(value) { return String(value).padStart(2, '0'); }
        var timestamp = Date.parse(year + '-' + pad(month) + '-' + pad(day) + 'T' + pad(hour) + ':' + pad(minute) + ':00+09:00');
        return Number.isFinite(timestamp) ? new Date(timestamp).toISOString() : fallback;
    }

    function marketById(data, id) {
        return findById(data && data.markets, id);
    }

    function renderLoadState(data, liveData, state, checking, silent) {
        clear(loadState);
        var liveKospi = marketById(liveData, 'KOSPI');
        var savedKospi = marketById(data, 'KOSPI');
        var displayMarket = liveKospi || savedKospi;
        var displayTime = displayMarket && displayMarket.asOfLabel ? displayMarket.asOfLabel : data.asOfDisplay;
        var displayState = liveData
            ? liveData.marketState + (liveData.partial ? ' · 일부 항목 지연' : '')
            : '최근 기록';
        var marketText = checking
            ? '시장 시세 확인 중'
            : liveData
                ? '시장 시세 ' + displayTime + ' · ' + displayState
                : '시장 시세 ' + displayTime + ' · ' + displayState;
        loadState.appendChild(make('span', 'market-dashboard-time market-dashboard-time--market', marketText));
        loadState.appendChild(make(
            'span',
            'market-dashboard-time market-dashboard-time--analysis',
            '시황분석 작성 ' + formatKstDateTime(data.generatedAt)
        ));
        loadState.setAttribute('data-state', state);
        loadState.setAttribute('aria-live', silent ? 'off' : 'polite');
    }

    function toneClass(tone) {
        if (tone === 'positive') return 'market-tone-positive';
        if (tone === 'danger') return 'market-tone-danger';
        if (tone === 'warning') return 'market-tone-warning';
        return 'market-tone-info';
    }

    function currentViewFromUrl() {
        var requested = new URLSearchParams(window.location.search).get('view') || 'analysis';
        if (requested === 'kodex') return 'technical';
        return validViews.indexOf(requested) === -1 ? 'analysis' : requested;
    }

    function setView(view, historyMode) {
        var selected = validViews.indexOf(view) === -1 ? 'analysis' : view;

        viewLinks.forEach(function (link) {
            var active = link.getAttribute('data-market-view') === selected;
            if (active) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });

        viewPanels.forEach(function (panel) {
            panel.hidden = panel.getAttribute('data-view-panel') !== selected;
        });

        if (historyMode) {
            var nextUrl = new URL(window.location.href);
            nextUrl.searchParams.set('view', selected);
            window.history[historyMode + 'State']({ view: selected }, '', nextUrl.pathname + nextUrl.search + nextUrl.hash);
        }
    }

    function directTechnicalCards(stack) {
        return Array.prototype.filter.call(stack.children, function (node) {
            return node.hasAttribute && node.hasAttribute('data-technical-card');
        });
    }

    function readTechnicalCardOrder() {
        try {
            var stored = JSON.parse(window.localStorage.getItem(technicalCardOrderStorageKey) || '[]');
            return Array.isArray(stored) ? stored.filter(function (id) { return typeof id === 'string'; }) : [];
        } catch (error) {
            return [];
        }
    }

    function saveTechnicalCardOrder(stack) {
        try {
            window.localStorage.setItem(technicalCardOrderStorageKey, JSON.stringify(
                directTechnicalCards(stack).map(function (card) { return card.getAttribute('data-technical-card'); })
            ));
        } catch (error) {
            // 저장이 제한된 브라우저에서도 현재 화면의 카드 이동은 그대로 유지한다.
        }
    }

    function updateTechnicalCardOrderControls(stack) {
        var cards = directTechnicalCards(stack);
        cards.forEach(function (card, index) {
            var up = card.querySelector('[data-technical-card-move="up"]');
            var down = card.querySelector('[data-technical-card-move="down"]');
            if (up) up.disabled = index === 0;
            if (down) down.disabled = index === cards.length - 1;
        });
    }

    function moveTechnicalCard(stack, card, direction) {
        var cards = directTechnicalCards(stack);
        var currentIndex = cards.indexOf(card);
        var targetIndex = currentIndex + direction;
        if (currentIndex < 0 || targetIndex < 0 || targetIndex >= cards.length) return;

        if (direction < 0) stack.insertBefore(card, cards[targetIndex]);
        else stack.insertBefore(cards[targetIndex], card);

        saveTechnicalCardOrder(stack);
        updateTechnicalCardOrderControls(stack);
        card.classList.remove('is-order-updated');
        window.requestAnimationFrame(function () { card.classList.add('is-order-updated'); });

        var status = document.getElementById('technical-card-order-status');
        if (status) {
            var title = card.getAttribute('data-technical-card-title') || '선택한 분석 카드';
            status.textContent = title + ' 박스를 ' + (direction < 0 ? '위로' : '아래로') + ' 이동했습니다.';
        }
    }

    function initializeTechnicalCardOrdering() {
        var stack = document.getElementById('technical-card-stack');
        if (!stack) return;

        var cardsById = {};
        directTechnicalCards(stack).forEach(function (card) {
            cardsById[card.getAttribute('data-technical-card')] = card;
        });

        var savedOrder = readTechnicalCardOrder();
        var requestedOrder = savedOrder.concat(defaultTechnicalCardOrder).filter(function (id, index, values) {
            return cardsById[id] && values.indexOf(id) === index;
        });
        Object.keys(cardsById).forEach(function (id) {
            if (requestedOrder.indexOf(id) === -1) requestedOrder.push(id);
        });
        requestedOrder.forEach(function (id) { stack.appendChild(cardsById[id]); });

        directTechnicalCards(stack).forEach(function (card) {
            var title = card.getAttribute('data-technical-card-title') || '분석 카드';
            var controls = make('div', 'technical-card-order-controls');
            controls.setAttribute('role', 'group');
            controls.setAttribute('aria-label', title + ' 위치 이동');

            [['up', '⌃', '위로 이동', -1], ['down', '⌄', '아래로 이동', 1]].forEach(function (config) {
                var button = make('button', 'technical-card-order-button', config[1]);
                button.type = 'button';
                button.setAttribute('data-technical-card-move', config[0]);
                button.setAttribute('aria-label', title + ' ' + config[2]);
                button.title = config[2];
                button.addEventListener('click', function () {
                    moveTechnicalCard(stack, card, config[3]);
                });
                controls.appendChild(button);
            });
            card.insertBefore(controls, card.firstChild);
        });

        updateTechnicalCardOrderControls(stack);
    }

    viewLinks.forEach(function (link) {
        link.addEventListener('click', function (event) {
            if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
            event.preventDefault();
            var selectedView = link.getAttribute('data-market-view');
            setView(selectedView, 'push');
            link.focus({ preventScroll: true });
            if (window.matchMedia('(max-width: 720px)').matches) {
                var selectedPanel = document.querySelector('[data-view-panel="' + selectedView + '"]');
                if (selectedPanel) selectedPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    window.addEventListener('popstate', function () {
        setView(currentViewFromUrl());
    });

    initializeTechnicalCardOrdering();
    setView(currentViewFromUrl());

    function isStaleSnapshot(data) {
        var kospi = marketById(data, 'KOSPI');
        var timestamp = Date.parse(kospi && kospi.asOf ? kospi.asOf : data.asOf);
        if (!Number.isFinite(timestamp)) return true;
        var age = Date.now() - timestamp;
        if (/장중/.test(data.marketState || '') && age > 10 * 60 * 1000) return true;
        return age > 4 * 24 * 60 * 60 * 1000;
    }

    function renderMarketCards(data, stale) {
        var container = document.getElementById('market-index-grid');
        clear(container);

        data.markets.forEach(function (market) {
            var card = make('article', 'market-index-card');
            var head = make('div', 'market-index-head');
            head.appendChild(make('span', 'market-index-symbol', market.symbol));

            var name = make('div', 'market-index-name');
            name.appendChild(make('strong', '', market.label));
            var marketStateText = stale || market.delayed || !market.liveUpdated
                ? '최근 기록'
                : String(market.stateLabel || '최근 시세').replace('스냅샷', '시세');
            name.appendChild(make('small', '', marketStateText + ' · ' + market.asOfLabel));
            head.appendChild(name);

            var quote = make('div', 'market-index-quote');
            quote.appendChild(make('strong', 'market-index-value', formatNumber(market.value, 2)));
            var changeClass = market.changePercent >= 0 ? 'is-positive' : 'is-negative';
            var arrow = market.changePercent >= 0 ? '▲ 상승 ' : '▼ 하락 ';
            quote.appendChild(make('span', 'market-index-change ' + changeClass, arrow + formatSigned(market.changePercent, '%', 2)));
            head.appendChild(quote);
            card.appendChild(head);

            var body = make('div', 'market-index-body');
            var bodyLabel = make('p', 'market-index-body-label');
            var rows;
            if (Array.isArray(market.flows) && market.flows.length) {
                bodyLabel.appendChild(make('span', '', '투자자 수급'));
                bodyLabel.appendChild(make('span', '', '억원'));
                rows = market.flows.map(function (flow) {
                    return {
                        label: flow.label,
                        value: flow.value,
                        display: formatSigned(flow.value, flow.unit),
                        tone: flow.value > 0 ? 'positive' : flow.value < 0 ? 'negative' : 'flat'
                    };
                });
            } else {
                bodyLabel.appendChild(make('span', '', '시장 폭'));
                bodyLabel.appendChild(make('span', '', '종목 수'));
                rows = [
                    { label: '상승', value: market.breadth.advance, display: formatNumber(market.breadth.advance, 0) + '개', tone: 'positive' },
                    { label: '보합', value: market.breadth.flat, display: formatNumber(market.breadth.flat, 0) + '개', tone: 'flat' },
                    { label: '하락', value: market.breadth.decline, display: formatNumber(market.breadth.decline, 0) + '개', tone: 'negative' }
                ];
            }
            body.appendChild(bodyLabel);

            var maxValue = Math.max.apply(Math, rows.map(function (row) { return Math.abs(row.value); }).concat([1]));
            var list = make('div', 'market-flow-list');
            rows.forEach(function (row) {
                var item = make('div', 'market-flow-row');
                item.appendChild(make('span', 'market-flow-label', row.label));
                var track = make('span', 'market-flow-track');
                var bar = make('span', 'market-flow-bar is-' + row.tone);
                bar.style.setProperty('--flow-width', Math.max(3, Math.abs(row.value) / maxValue * 100).toFixed(1) + '%');
                track.appendChild(bar);
                item.appendChild(track);
                item.appendChild(make('strong', 'market-flow-value', row.display));
                list.appendChild(item);
            });
            body.appendChild(list);
            card.appendChild(body);
            container.appendChild(card);
        });
    }

    function renderStance(data) {
        var container = document.getElementById('market-stance-strip');
        clear(container);

        var statusCell = make('div', 'market-stance-cell');
        statusCell.appendChild(make('small', '', '오늘 대응 판단'));
        statusCell.appendChild(make('strong', '', data.stance.label));
        container.appendChild(statusCell);

        var allocationCell = make('div', 'market-stance-cell market-stance-cell--allocation');
        allocationCell.appendChild(make('small', '', '공격 · 관망 · 방어'));
        allocationCell.appendChild(make('strong', '', data.stance.attack + ' · ' + data.stance.wait + ' · ' + data.stance.defense));
        var bars = make('span', 'market-stance-mini-bars');
        bars.style.setProperty('--attack', data.stance.attack + 'fr');
        bars.style.setProperty('--wait', data.stance.wait + 'fr');
        bars.style.setProperty('--defense', data.stance.defense + 'fr');
        bars.appendChild(make('span'));
        bars.appendChild(make('span'));
        bars.appendChild(make('span'));
        allocationCell.appendChild(bars);
        container.appendChild(allocationCell);

        var rangeCell = make('div', 'market-stance-cell');
        rangeCell.appendChild(make('small', '', '오늘 핵심 범위'));
        rangeCell.appendChild(make('strong', '', data.scenarios[0].range.replace('KOSPI ', '')));
        container.appendChild(rangeCell);
    }

    function renderCheckpoints(data) {
        var list = document.getElementById('market-checkpoint-list');
        clear(list);
        data.checkpoints.forEach(function (checkpoint) {
            var item = make('li');
            var content = make('div');
            var detail = checkpoint.detail;
            if (checkpoint.label === '외국인 선물' && data.flows && data.flows.futuresAsOfLabel) {
                detail = data.flows.futuresAsOfLabel.replace('지연값', '지연 시세');
            }
            content.appendChild(make('strong', '', checkpoint.label));
            content.appendChild(make('span', toneClass(checkpoint.tone), checkpoint.value));
            content.appendChild(make('small', '', detail));
            item.appendChild(content);
            list.appendChild(item);
        });
    }

    function renderAnalysis(data, liveData) {
        document.getElementById('market-headline').textContent = data.headline;
        document.getElementById('market-summary').textContent = data.summary;
        var writtenAt = document.getElementById('market-analysis-written-at');
        var writtenAtDisplay = formatKstDateTime(data.generatedAt);
        writtenAt.textContent = '작성 ' + writtenAtDisplay;
        writtenAt.setAttribute('datetime', data.generatedAt);
        var strategyWrittenAt = document.getElementById('market-strategy-written-at');
        if (strategyWrittenAt) strategyWrittenAt.textContent = writtenAtDisplay + ' 작성본 기준';

        var liveKospi = liveData ? findById(liveData.markets, 'KOSPI') : null;
        var savedKospi = findById(data.markets, 'KOSPI');
        var factsAsOf = document.getElementById('market-facts-as-of');
        factsAsOf.textContent = liveKospi
            ? '국내 시장 · ' + liveKospi.asOfLabel + ' ' + liveKospi.stateLabel
            : '국내 시장 · ' + (savedKospi && savedKospi.asOfLabel ? savedKospi.asOfLabel : data.asOfDisplay) + ' 최근 기록';

        var changeList = document.getElementById('market-change-list');
        clear(changeList);
        data.changes.forEach(function (change) {
            var item = make('div', 'market-change-item');
            item.appendChild(make('strong', '', change.label));
            var values = make('div', 'market-change-values');
            values.appendChild(make('span', '', change.before));
            values.appendChild(make('span', '', '→'));
            values.appendChild(make('b', '', change.after));
            item.appendChild(values);
            item.appendChild(make('p', '', change.meaning));
            changeList.appendChild(item);
        });

        var factorGrid = document.getElementById('market-factor-grid');
        clear(factorGrid);
        data.factors.forEach(function (factor) {
            var item = make('article', 'market-factor-item');
            item.setAttribute('data-tone', factor.tone);
            item.appendChild(make('span', '', factor.label));
            item.appendChild(make('strong', '', factor.metric));
            item.appendChild(make('small', '', factor.detail));
            factorGrid.appendChild(item);
        });

        var dataNote = document.getElementById('market-analysis-data-note');
        if (liveKospi) {
            var exchangeLabel = liveData.exchange ? liveData.exchange.asOfLabel : null;
            dataNote.textContent = '국내 지수·현물 수급·시장 폭·프로그램은 ' + liveKospi.asOfLabel
                + (exchangeLabel ? ', 원/달러는 ' + exchangeLabel + ' 기준입니다. ' : ' 기준입니다. 원/달러는 ' + data.asOfDisplay + ' 기록입니다. ')
                + (liveData.partial ? '일부 항목은 표시된 마지막 확인 시각 기준입니다. ' : '')
                + '메모리·미 국채·일정은 '
                + writtenAtDisplay + ' 작성 당시 공개자료를 반영했습니다.';
        } else {
            dataNote.textContent = '국내 시장 수치는 ' + (savedKospi && savedKospi.asOfLabel ? savedKospi.asOfLabel : data.asOfDisplay)
                + ' 최근 기록입니다. 메모리·미 국채·일정은 '
                + writtenAtDisplay + ' 작성 당시 공개자료를 반영했습니다.';
        }

        var flowSummary = document.getElementById('market-flow-summary');
        clear(flowSummary);
        [
            ['차익 프로그램', formatSigned(data.flows.program.arbitrage, data.flows.program.unit)],
            ['비차익 프로그램', formatSigned(data.flows.program.nonArbitrage, data.flows.program.unit)],
            ['전체 프로그램', formatSigned(data.flows.program.total, data.flows.program.unit)],
            [
                '외국인 KOSPI200 선물' + (data.flows.futuresAsOfLabel ? ' · ' + data.flows.futuresAsOfLabel.replace('지연값', '지연 시세') : ''),
                formatSigned(data.flows.kospi200FuturesForeign, data.flows.futuresUnit)
            ]
        ].forEach(function (row) {
            var item = make('div', 'market-flow-summary-item');
            item.appendChild(make('span', '', row[0]));
            item.appendChild(make('strong', '', row[1]));
            flowSummary.appendChild(item);
        });

        var memoryGrid = document.getElementById('market-memory-grid');
        clear(memoryGrid);
        data.memory.forEach(function (memory) {
            var item = make('div', 'market-memory-item');
            var label = make('span', '', memory.label);
            var value = make('strong', '', memory.value + ' · ' + memory.change);
            item.appendChild(label);
            item.appendChild(value);
            memoryGrid.appendChild(item);
        });
        document.getElementById('market-memory-as-of').textContent = data.memoryAsOfLabel
            ? data.memoryAsOfLabel + ' 공개가격입니다.'
            : '시황분석 작성 당시 공개된 최근 가격입니다.';
    }

    function renderAllocation(data) {
        document.getElementById('strategy-stance-title').textContent = data.stance.label;
        document.getElementById('strategy-note').textContent = data.stance.note;
        var container = document.getElementById('strategy-allocation');
        clear(container);

        [
            { key: 'attack', label: '공격', value: data.stance.attack },
            { key: 'wait', label: '관망', value: data.stance.wait },
            { key: 'defense', label: '방어', value: data.stance.defense }
        ].forEach(function (allocation) {
            var row = make('div', 'market-allocation-row');
            row.setAttribute('data-key', allocation.key);
            row.appendChild(make('span', '', allocation.label));
            var track = make('span', 'market-allocation-track');
            var fill = make('span', 'market-allocation-fill');
            fill.style.setProperty('--allocation-width', allocation.value + '%');
            track.appendChild(fill);
            row.appendChild(track);
            row.appendChild(make('strong', '', allocation.value));
            container.appendChild(row);
        });
    }

    function renderScenarioDetail(scenario) {
        var detail = document.getElementById('market-scenario-detail');
        clear(detail);
        detail.appendChild(make('strong', 'market-scenario-range', scenario.range));
        detail.appendChild(make('p', '', scenario.summary));
        detail.appendChild(make('h4', '', '성립 조건'));
        var conditions = make('ul');
        scenario.conditions.forEach(function (condition) {
            conditions.appendChild(make('li', '', condition));
        });
        detail.appendChild(conditions);
        detail.appendChild(make('h4', '', '무효화 기준'));
        detail.appendChild(make('p', 'market-scenario-invalidation', scenario.invalidation));
    }

    function renderScenarios(data) {
        var switcher = document.getElementById('market-scenario-switch');
        clear(switcher);
        data.scenarios.forEach(function (scenario, index) {
            var button = make('button', '', scenario.label);
            button.type = 'button';
            button.setAttribute('aria-pressed', index === 0 ? 'true' : 'false');
            button.addEventListener('click', function () {
                Array.prototype.forEach.call(switcher.querySelectorAll('button'), function (candidate) {
                    candidate.setAttribute('aria-pressed', candidate === button ? 'true' : 'false');
                });
                renderScenarioDetail(scenario);
            });
            switcher.appendChild(button);
        });
        renderScenarioDetail(data.scenarios[0]);
    }

    function renderStrategyLevels(data) {
        var tbody = document.getElementById('strategy-levels');
        clear(tbody);
        data.strategyLevels.forEach(function (level) {
            var row = make('tr');
            row.appendChild(make('td', '', level.asset));
            row.appendChild(make('td', '', level.support));
            row.appendChild(make('td', '', level.pivot));
            row.appendChild(make('td', '', level.resistance));
            tbody.appendChild(row);
        });
    }

    function checklistStorageKey(data) {
        return 'market-strategy-checklist:' + data.snapshotId;
    }

    function readChecklistState(data) {
        try {
            var parsed = JSON.parse(window.localStorage.getItem(checklistStorageKey(data)) || '{}');
            return parsed && typeof parsed === 'object' ? parsed : {};
        } catch (error) {
            return {};
        }
    }

    function writeChecklistState(data, state) {
        try {
            window.localStorage.setItem(checklistStorageKey(data), JSON.stringify(state));
        } catch (error) {
            return;
        }
    }

    function renderChecklist(data) {
        var container = document.getElementById('strategy-checklist');
        var counter = document.getElementById('strategy-check-count');
        var state = readChecklistState(data);
        clear(container);

        function updateCount() {
            var count = data.checklist.filter(function (item) { return Boolean(state[item.id]); }).length;
            counter.textContent = count + ' / ' + data.checklist.length;
        }

        data.checklist.forEach(function (item) {
            var label = make('label');
            var input = make('input');
            input.type = 'checkbox';
            input.checked = Boolean(state[item.id]);
            input.addEventListener('change', function () {
                state[item.id] = input.checked;
                writeChecklistState(data, state);
                updateCount();
            });
            label.appendChild(input);
            label.appendChild(make('span', '', item.label));
            container.appendChild(label);
        });
        updateCount();
    }

    function renderEvents(data) {
        var list = document.getElementById('market-event-list');
        clear(list);
        data.events.forEach(function (event) {
            var item = make('li');
            item.appendChild(make('time', '', event.time));
            item.appendChild(make('strong', '', event.name));
            item.appendChild(make('span', '', event.path));
            list.appendChild(item);
        });
    }

    function renderTechnicalInstrument(instrument) {
        document.getElementById('technical-chart-title').textContent = instrument.label + ' 당일 OHLC·현재가 비교';
        document.getElementById('market-technical-interpretation').textContent = instrument.interpretation;
        var technicalTime = instrument.asOfLabel || (dashboardData && dashboardData.asOfDisplay) || '작성 시점';
        var technicalState = instrument.delayed
            ? '마지막 확인 시세'
            : instrument.liveUpdated ? '최근 시세' : '시황분석 작성 당시 시세';
        document.getElementById('market-technical-note').textContent = technicalTime + ' ' + technicalState
            + '와 당일 가격 범위, 지지·저항 기준선입니다.';

        var svg = document.getElementById('market-technical-chart');
        clear(svg);
        var width = 760;
        var height = 320;
        var margin = { top: 28, right: 112, bottom: 58, left: 68 };
        var innerWidth = width - margin.left - margin.right;
        var innerHeight = height - margin.top - margin.bottom;
        var values = instrument.points.map(function (point) { return point.value; })
            .concat(instrument.levels.map(function (level) { return level.value; }));
        var minValue = Math.min.apply(Math, values);
        var maxValue = Math.max.apply(Math, values);
        var spread = Math.max(maxValue - minValue, Math.abs(maxValue || 1) * 0.01);
        minValue -= spread * 0.08;
        maxValue += spread * 0.08;

        function xFor(index) {
            if (instrument.points.length === 1) return margin.left + innerWidth / 2;
            return margin.left + index * (innerWidth / (instrument.points.length - 1));
        }

        function yFor(value) {
            return margin.top + (maxValue - value) / (maxValue - minValue) * innerHeight;
        }

        for (var gridIndex = 0; gridIndex <= 4; gridIndex += 1) {
            var gridY = margin.top + innerHeight * gridIndex / 4;
            svg.appendChild(makeSvg('line', { x1: margin.left, y1: gridY, x2: margin.left + innerWidth, y2: gridY, 'class': 'market-chart-grid' }));
            var gridValue = maxValue - (maxValue - minValue) * gridIndex / 4;
            var axisLabel = makeSvg('text', { x: margin.left - 10, y: gridY + 4, 'class': 'market-chart-axis-label', 'text-anchor': 'end' });
            axisLabel.textContent = formatPrice(gridValue, instrument.unit);
            svg.appendChild(axisLabel);
        }

        instrument.levels.forEach(function (level) {
            var levelY = yFor(level.value);
            svg.appendChild(makeSvg('line', { x1: margin.left, y1: levelY, x2: margin.left + innerWidth, y2: levelY, 'class': 'market-chart-level' }));
            var levelLabel = makeSvg('text', { x: width - 8, y: levelY + 4, 'class': 'market-chart-level-label' });
            levelLabel.textContent = level.label + ' ' + formatPrice(level.value, instrument.unit);
            svg.appendChild(levelLabel);
        });

        var baseline = margin.top + innerHeight;
        instrument.points.forEach(function (point, index) {
            var pointX = xFor(index);
            var pointY = yFor(point.value);
            svg.appendChild(makeSvg('line', {
                x1: pointX,
                y1: pointY,
                x2: pointX,
                y2: baseline,
                'class': 'market-chart-observation-guide'
            }));
            svg.appendChild(makeSvg('circle', {
                cx: pointX,
                cy: pointY,
                r: index === instrument.points.length - 1 ? 7 : 5,
                'class': index === instrument.points.length - 1 ? 'market-chart-point is-current' : 'market-chart-point'
            }));
            var pointLabel = makeSvg('text', { x: pointX, y: height - 24, 'class': 'market-chart-point-label' });
            pointLabel.textContent = point.label;
            svg.appendChild(pointLabel);
        });

        var levels = document.getElementById('market-technical-levels');
        clear(levels);
        instrument.levels.forEach(function (level) {
            var item = make('div', 'market-technical-level');
            item.appendChild(make('span', '', level.label));
            item.appendChild(make('strong', '', formatPrice(level.value, instrument.unit)));
            levels.appendChild(item);
        });

        var table = document.getElementById('market-technical-table');
        clear(table);
        instrument.points.forEach(function (point) {
            var row = make('tr');
            row.appendChild(make('td', '', point.label));
            row.appendChild(make('td', '', formatPrice(point.value, instrument.unit)));
            table.appendChild(row);
        });
    }

    function renderTechnical(data) {
        var selectedInstrument = data.technical.instruments.filter(function (instrument) {
            return instrument.id === 'KODEX';
        })[0];
        if (!selectedInstrument) return;
        selectedInstrumentId = selectedInstrument.id;
        renderTechnicalInstrument(selectedInstrument);
    }

    function pointValue(instrument, matcher) {
        var point = (instrument && instrument.points || []).filter(function (item) {
            return matcher.test(item.label || '');
        })[0];
        return point && Number.isFinite(point.value) ? point.value : NaN;
    }

    function formatTradingDate(value) {
        var match = /^(\d{4})(\d{2})(\d{2})$/.exec(value || '');
        if (!match) return value || '날짜 확인 불가';
        return Number(match[2]) + '월 ' + Number(match[3]) + '일';
    }

    function appendKodexMetric(container, label, value) {
        var item = make('div', 'kodex-metric-item');
        item.appendChild(make('span', '', label));
        item.appendChild(make('strong', '', value));
        container.appendChild(item);
    }

    function parseHistoryDate(value) {
        var timestamp = Date.parse(String(value || '') + 'T00:00:00+09:00');
        return Number.isFinite(timestamp) ? timestamp : NaN;
    }

    function formatHistoryDate(value) {
        var match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || '');
        if (!match) return value || '날짜 확인 불가';
        return Number(match[2]) + '월 ' + Number(match[3]) + '일';
    }

    function formatCompactVolume(value) {
        if (!Number.isFinite(value)) return '데이터 없음';
        if (value >= 100000000) return formatNumber(value / 100000000, 2) + '억주';
        if (value >= 10000) return formatNumber(value / 10000, 1) + '만주';
        return formatNumber(value, 0) + '주';
    }

    function simpleMovingAverage(rows, period) {
        var result = new Array(rows.length).fill(null);
        var sum = 0;
        rows.forEach(function (row, index) {
            sum += row.close;
            if (index >= period) sum -= rows[index - period].close;
            if (index >= period - 1) result[index] = sum / period;
        });
        return result;
    }

    function svgPathForSeries(values, startIndex, xFor, yFor) {
        var path = '';
        values.slice(startIndex).forEach(function (value, index) {
            if (!Number.isFinite(value)) return;
            path += (path ? ' L ' : 'M ') + xFor(index).toFixed(2) + ' ' + yFor(value).toFixed(2);
        });
        return path;
    }

    function validVolumePressure(row) {
        var pressure = row && row.volumePressure;
        if (!pressure) return null;
        var estimatedTotal = pressure.estimatedBuyVolume + pressure.estimatedSellVolume;
        if (![pressure.estimatedBuyVolume, pressure.estimatedSellVolume, pressure.coverageRatio].every(Number.isFinite)
            || pressure.estimatedBuyVolume < 0
            || pressure.estimatedSellVolume < 0
            || estimatedTotal <= 0
            || pressure.coverageRatio < 0.95
            || pressure.coverageRatio > 1.005) return null;
        return {
            estimatedBuyVolume: pressure.estimatedBuyVolume,
            estimatedSellVolume: pressure.estimatedSellVolume,
            delta: pressure.estimatedBuyVolume - pressure.estimatedSellVolume,
            buyShare: pressure.estimatedBuyVolume / estimatedTotal,
            sellShare: pressure.estimatedSellVolume / estimatedTotal,
            coverageRatio: pressure.coverageRatio
        };
    }

    function renderSynchronizedTechnicalCharts() {
        var kospi = dashboardData && findById(dashboardData.markets, 'KOSPI');
        var kodex = dashboardData && findById(dashboardData.technical.instruments, 'KODEX');
        if (kospi) renderKospiHistoryChart(kospi);
        if (kodex) {
            renderKodexHistoryChart(kodex);
            renderCompositeMomentumCard(kodex);
        }
        renderTqqqSynchronized();
    }

    function bindKodexChartControls() {
        Array.prototype.forEach.call(document.querySelectorAll('[data-kodex-chart-mode]'), function (button) {
            button.setAttribute('aria-pressed', button.getAttribute('data-kodex-chart-mode') === selectedKodexChartMode ? 'true' : 'false');
            if (button.getAttribute('data-chart-bound') === 'true') return;
            button.setAttribute('data-chart-bound', 'true');
            button.addEventListener('click', function () {
                clearLinkedChartSelection(false);
                selectedKodexChartMode = button.getAttribute('data-kodex-chart-mode') === 'intraday' ? 'intraday' : 'daily';
                renderSynchronizedTechnicalCharts();
            });
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-kodex-period]'), function (button) {
            button.setAttribute('aria-pressed', button.getAttribute('data-kodex-period') === selectedKodexPeriod ? 'true' : 'false');
            if (button.getAttribute('data-chart-bound') === 'true') return;
            button.setAttribute('data-chart-bound', 'true');
            button.addEventListener('click', function () {
                clearLinkedChartSelection(false);
                selectedKodexPeriod = button.getAttribute('data-kodex-period') === '1m' ? '1m' : '3m';
                renderSynchronizedTechnicalCharts();
            });
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-kodex-interval]'), function (button) {
            button.setAttribute('aria-pressed', Number(button.getAttribute('data-kodex-interval')) === selectedKodexIntradayInterval ? 'true' : 'false');
            if (button.getAttribute('data-chart-bound') === 'true') return;
            button.setAttribute('data-chart-bound', 'true');
            button.addEventListener('click', function () {
                clearLinkedChartSelection(false);
                selectedKodexIntradayInterval = Number(button.getAttribute('data-kodex-interval')) || 5;
                renderSynchronizedTechnicalCharts();
            });
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-shared-intraday-date]'), function (dateSelect) {
            if (dateSelect.getAttribute('data-chart-bound') === 'true') return;
            dateSelect.setAttribute('data-chart-bound', 'true');
            dateSelect.addEventListener('change', function () {
                clearLinkedChartSelection(false);
                selectedKodexIntradayDate = dateSelect.value;
                renderSynchronizedTechnicalCharts();
            });
        });
        var refreshButton = document.getElementById('kodex-chart-refresh');
        if (refreshButton && refreshButton.getAttribute('data-chart-bound') !== 'true') {
            refreshButton.setAttribute('data-chart-bound', 'true');
            refreshButton.addEventListener('click', function () {
                refreshTimeSensitiveData();
            });
        }
    }

    function setChartRefreshState(state, message) {
        var button = document.getElementById('kodex-chart-refresh');
        var status = document.getElementById('kodex-chart-refresh-status');
        if (!button || !status) return;
        var loading = state === 'loading';
        button.disabled = loading;
        button.classList.toggle('is-loading', loading);
        button.setAttribute('aria-busy', loading ? 'true' : 'false');
        status.textContent = message || '';
    }

    function refreshTimeSensitiveData() {
        if (!dashboardData) return Promise.resolve(false);
        compositeMomentumForceRefresh = true;
        compositeMomentumState.key = '';
        setChartRefreshState('loading', '최신 데이터 확인 중');
        return refreshLiveMarketData(dashboardData, { silent: true, force: true }).then(function (applied) {
            var now = new Date();
            var time = new Intl.DateTimeFormat('ko-KR', {
                timeZone: 'Asia/Seoul',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hourCycle: 'h23'
            }).format(now);
            setChartRefreshState('ready', applied ? time + ' 갱신' : time + ' 일부 데이터 유지');
            return applied;
        }).catch(function () {
            setChartRefreshState('error', '갱신 실패 · 다시 시도');
            return false;
        });
    }

    function setKodexChartControls(instrument) {
        bindKodexChartControls();
        var liveInstrument = instrument && instrument.liveSnapshot || {};
        var indexRows = liveInstrument.intradayIndex || instrument && instrument.intradayIndex || [];
        Array.prototype.forEach.call(document.querySelectorAll('[data-shared-daily-controls]'), function (node) {
            node.hidden = selectedKodexChartMode !== 'daily';
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-shared-intraday-controls]'), function (node) {
            node.hidden = selectedKodexChartMode !== 'intraday';
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-kodex-chart-mode]'), function (button) {
            button.setAttribute('aria-pressed', button.getAttribute('data-kodex-chart-mode') === selectedKodexChartMode ? 'true' : 'false');
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-kodex-period]'), function (button) {
            button.setAttribute('aria-pressed', button.getAttribute('data-kodex-period') === selectedKodexPeriod ? 'true' : 'false');
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-kodex-interval]'), function (button) {
            button.setAttribute('aria-pressed', Number(button.getAttribute('data-kodex-interval')) === selectedKodexIntradayInterval ? 'true' : 'false');
        });
        Array.prototype.forEach.call(document.querySelectorAll('[data-kodex-daily-legend]'), function (node) {
            node.hidden = selectedKodexChartMode !== 'daily';
        });
        var dates = indexRows.map(function (row) { return row.date; });
        if (!selectedKodexIntradayDate || dates.indexOf(selectedKodexIntradayDate) === -1) {
            selectedKodexIntradayDate = dates[dates.length - 1] || '';
        }
        Array.prototype.forEach.call(document.querySelectorAll('[data-shared-intraday-date]'), function (dateSelect) {
            if (dateSelect.options.length !== dates.length || Array.prototype.some.call(dateSelect.options, function (option, index) {
                return option.value !== dates[index];
            })) {
                clear(dateSelect);
                dates.forEach(function (date) {
                    var option = document.createElement('option');
                    option.value = date;
                    option.textContent = formatHistoryDate(date);
                    dateSelect.appendChild(option);
                });
            }
            dateSelect.value = selectedKodexIntradayDate;
        });
        return indexRows;
    }

    function aggregateIntradayBars(bars, interval) {
        var groups = [];
        (bars || []).forEach(function (bar) {
            var parts = String(bar.time || '').split(':');
            var minuteOfDay = Number(parts[0]) * 60 + Number(parts[1]);
            var bucket = Math.floor((minuteOfDay - 9 * 60) / interval);
            var current = groups[groups.length - 1];
            if (!current || current.bucket !== bucket) {
                current = {
                    bucket: bucket,
                    time: bar.time,
                    endTime: bar.time,
                    open: bar.open,
                    high: bar.high,
                    low: bar.low,
                    close: bar.close,
                    volume: 0,
                    estimatedBuyVolume: 0,
                    estimatedSellVolume: 0,
                    delta: 0,
                    cumulativeDelta: 0
                };
                groups.push(current);
            }
            current.endTime = bar.time;
            current.high = Math.max(current.high, bar.high);
            current.low = Math.min(current.low, bar.low);
            current.close = bar.close;
            current.volume += bar.volume;
            current.estimatedBuyVolume += bar.estimatedBuyVolume;
            current.estimatedSellVolume += bar.estimatedSellVolume;
            current.delta += bar.delta;
        });
        var cvd = 0;
        groups.forEach(function (row) {
            cvd += row.delta;
            row.cumulativeDelta = cvd;
        });
        return groups;
    }

    function aggregateCompositeBars(bars, interval) {
        var groups = [];
        (bars || []).forEach(function (bar) {
            var parts = String(bar.time || '').split(':');
            var minuteOfDay = Number(parts[0]) * 60 + Number(parts[1]);
            var bucket = Math.floor((minuteOfDay - 9 * 60) / interval);
            var current = groups[groups.length - 1];
            if (!current || current.bucket !== bucket) {
                current = Object.assign({ bucket: bucket, endTime: bar.time }, bar);
                groups.push(current);
            } else {
                current = Object.assign(current, bar, { bucket: bucket, time: current.time, endTime: bar.time });
            }
        });
        return groups;
    }

    function compositeDirectionLabel(direction, momentum) {
        if (direction >= 8) return momentum >= 0 ? '매수 우위 강화' : '매수 우위 둔화';
        if (direction <= -8) return momentum <= 0 ? '매도 우위 강화' : '매도 압력 완화';
        return momentum >= 0 ? '중립권 상향' : '중립권 하향';
    }

    function renderCompositeMomentumChart(days) {
        var svg = document.getElementById('composite-momentum-chart');
        var title = document.getElementById('composite-momentum-title');
        var badge = document.getElementById('composite-momentum-badge');
        var readout = document.getElementById('composite-momentum-readout');
        var summary = document.getElementById('composite-momentum-summary');
        if (!svg || !title || !badge || !readout || !summary) return;
        clear(svg);
        clear(summary);
        var rows;
        if (selectedKodexChartMode === 'intraday') {
            var selectedDay = (days || []).filter(function (day) { return day.date === selectedKodexIntradayDate; })[0];
            if (!selectedDay) {
                readout.textContent = '선택한 거래일은 두 시장의 공통 1분봉이 부족합니다.';
                return;
            }
            rows = aggregateCompositeBars(selectedDay.bars, selectedKodexIntradayInterval).map(function (row) {
                return Object.assign({ label: row.time }, row);
            });
            title.textContent = formatHistoryDate(selectedDay.date) + ' KOSPI·KODEX 거래량 모멘텀';
            badge.textContent = selectedKodexIntradayInterval + '분봉 · 공통 시각';
        } else {
            rows = (days || []).map(function (day) {
                return Object.assign({ label: day.date }, day.summary);
            });
            title.textContent = 'KOSPI·KODEX 합성 거래량 모멘텀 · ' + rows.length + '거래일';
            badge.textContent = '장 마감 30분 평균';
        }
        rows = rows.filter(function (row) {
            return [row.direction, row.momentum, row.signal, row.divergence].every(Number.isFinite);
        });
        if (rows.length < 2) {
            readout.textContent = '합성 거래량 모멘텀을 계산할 공통 구간이 부족합니다.';
            return;
        }

        var width = 1000;
        var left = 42;
        var right = 944;
        var momentumTop = 42;
        var momentumBottom = 292;
        var innerWidth = right - left;
        var xStep = innerWidth / rows.length;
        function xFor(index) { return left + xStep * index + xStep / 2; }
        var momentumMax = Math.max(5, Math.max.apply(Math, rows.map(function (row) {
            return Math.max(Math.abs(row.momentum), Math.abs(row.signal));
        })) * 1.15);
        function momentumY(value) { return momentumTop + (momentumMax - value) / (momentumMax * 2) * (momentumBottom - momentumTop); }
        [momentumTop, (momentumTop + momentumBottom) / 2, momentumBottom].forEach(function (y) {
            svg.appendChild(makeSvg('line', { x1: left, y1: y, x2: right, y2: y, 'class': 'composite-momentum-grid' }));
        });
        svg.appendChild(makeSvg('line', { x1: left, y1: momentumY(0), x2: right, y2: momentumY(0), 'class': 'composite-momentum-zero' }));
        var momentumLabel = makeSvg('text', { x: left, y: momentumTop + 13, 'class': 'composite-momentum-label' });
        momentumLabel.textContent = '방향 모멘텀';
        svg.appendChild(momentumLabel);
        [momentumMax, 0, -momentumMax].forEach(function (value) {
            var label = makeSvg('text', { x: right + 10, y: momentumY(value) + 4, 'class': 'composite-momentum-axis' });
            label.textContent = formatSigned(value, '', 0);
            svg.appendChild(label);
        });

        var signalPath = '';
        rows.forEach(function (row, index) {
            var x = xFor(index);
            signalPath += (signalPath ? ' L ' : 'M ') + x.toFixed(2) + ' ' + momentumY(row.signal).toFixed(2);
            var zeroY = momentumY(0);
            var valueY = momentumY(row.momentum);
            svg.appendChild(makeSvg('rect', {
                x: x - Math.max(1.5, Math.min(10, xStep * 0.34)),
                y: Math.min(zeroY, valueY),
                width: Math.max(3, Math.min(20, xStep * 0.68)),
                height: Math.max(1, Math.abs(valueY - zeroY)),
                rx: 0.8,
                'class': 'composite-momentum-bar ' + (row.momentum >= 0 ? 'is-buy' : 'is-sell')
            }));
        });
        svg.appendChild(makeSvg('path', { d: signalPath, 'class': 'composite-signal-line' }));

        function updateReadout(row) {
            var label = selectedKodexChartMode === 'intraday'
                ? formatHistoryDate(selectedKodexIntradayDate) + ' ' + row.time + (row.endTime && row.endTime !== row.time ? '–' + row.endTime : '')
                : formatHistoryDate(row.label);
            readout.textContent = label
                + ' · ' + compositeDirectionLabel(row.direction, row.momentum)
                + ' · 합성 방향 ' + formatSigned(row.direction, '점', 1)
                + ' · 모멘텀 ' + formatSigned(row.momentum, '점', 1)
                + ' · KODEX−KOSPI 괴리 ' + formatSigned(row.divergence, '점', 1);
        }
        registerLinkedChartHitZones(svg, rows, updateReadout, {
            mode: selectedKodexChartMode,
            left: left,
            right: right,
            top: momentumTop,
            bottom: momentumBottom,
            className: 'composite-momentum-hit',
            ariaLabel: function (row) {
                return (row.label || row.time) + ', 합성 방향 ' + formatSigned(row.direction, '점', 1);
            }
        });
        var tickIndexes = [0, Math.floor((rows.length - 1) / 2), rows.length - 1].filter(function (value, index, values) {
            return values.indexOf(value) === index;
        });
        tickIndexes.forEach(function (index) {
            var label = makeSvg('text', { x: xFor(index), y: 330, 'class': 'composite-momentum-axis', 'text-anchor': index === 0 ? 'start' : index === rows.length - 1 ? 'end' : 'middle' });
            label.textContent = selectedKodexChartMode === 'intraday'
                ? rows[index].time
                : formatHistoryDate(rows[index].label).replace('월 ', '/').replace('일', '');
            svg.appendChild(label);
        });
        var latest = rows[rows.length - 1];
        updateReadout(latest);
        appendKodexMetric(summary, '현재 판정', compositeDirectionLabel(latest.direction, latest.momentum));
        appendKodexMetric(summary, '합성 방향', formatSigned(latest.direction, '점', 1));
        appendKodexMetric(summary, '모멘텀', formatSigned(latest.momentum, '점', 1));
        appendKodexMetric(summary, 'KODEX−KOSPI 괴리', formatSigned(latest.divergence, '점', 1));
    }

    function renderCompositeMomentumCard(instrument) {
        var readout = document.getElementById('composite-momentum-readout');
        if (!readout || !instrument || !window.MarketDashboardLive) return;
        var api = window.MarketDashboardLive;
        if (typeof api.fetchKospiMinutePressureDays !== 'function'
            || typeof api.fetchKodexIntradayDay !== 'function'
            || typeof api.calculateCompositeVolumeMomentum !== 'function') return;
        var liveInstrument = instrument.liveSnapshot || {};
        var indexRows = liveInstrument.intradayIndex || instrument.intradayIndex || [];
        var indexUrl = liveInstrument.intradayIndexUrl || instrument.intradayIndexUrl
            || (kodexIntradaySource ? new URL(kodexIntradaySource, window.location.href).href : '');
        var liveDay = liveInstrument.liveIntradayDay || instrument.liveIntradayDay || null;
        var dates = indexRows.map(function (row) { return row.date; }).filter(Boolean).slice(-12);
        if (liveDay && dates.indexOf(liveDay.date) === -1) dates.push(liveDay.date);
        if (!dates.length || !indexUrl || !liveMarketSource) return;
        var key = dates.join(',') + '|' + (liveDay && liveDay.sourceLastAt || 'archive');
        if (compositeMomentumState.key === key && compositeMomentumState.days.length) {
            renderCompositeMomentumChart(compositeMomentumState.days);
            return;
        }
        if (compositeMomentumState.pending && compositeMomentumState.key === key) return;
        var token = ++compositeMomentumRenderToken;
        compositeMomentumState.key = key;
        readout.textContent = '공통 거래일의 1분봉을 정규화하고 있습니다.';
        var kodexRequests = dates.map(function (date) {
            if (liveDay && liveDay.date === date) return Promise.resolve(liveDay);
            return api.fetchKodexIntradayDay(indexUrl, date, window.fetch.bind(window), { indexRows: indexRows });
        });
        var forceRefresh = compositeMomentumForceRefresh;
        compositeMomentumForceRefresh = false;
        compositeMomentumState.pending = Promise.all([
            api.fetchKospiMinutePressureDays(
                window.fetch.bind(window),
                new URL(liveMarketSource, window.location.href).href,
                dates,
                { concurrencyLimit: 4, forceRefresh: forceRefresh }
            ),
            Promise.all(kodexRequests)
        ]).then(function (parts) {
            if (token !== compositeMomentumRenderToken) return;
            var days = api.calculateCompositeVolumeMomentum(parts[0], parts[1]);
            compositeMomentumState.days = days;
            renderCompositeMomentumChart(days);
        }).catch(function () {
            if (token !== compositeMomentumRenderToken) return;
            readout.textContent = '합성 거래량 모멘텀 데이터를 불러오지 못했습니다.';
        }).finally(function () {
            if (token === compositeMomentumRenderToken) compositeMomentumState.pending = null;
        });
    }

    function formatPressurePercent(delta, volume) {
        var percent = delta / Math.max(volume, 1) * 100;
        if (Math.abs(percent) < 0.005) percent = 0;
        return formatSigned(percent, '%', 2);
    }

    function pressureStrengthScale(rows, deltaFor, volumeFor) {
        var ratios = rows.map(function (row) {
            return Math.abs(deltaFor(row)) / Math.max(volumeFor(row), 1);
        }).filter(function (value) {
            return Number.isFinite(value) && value > 0;
        }).sort(function (left, right) {
            return left - right;
        });
        if (!ratios.length) return 1;
        var percentileIndex = Math.min(ratios.length - 1, Math.floor((ratios.length - 1) * 0.9));
        return Math.max(ratios[percentileIndex], 0.01);
    }

    function pressureFillRatio(delta, volume, scale) {
        return Math.min(1, Math.abs(delta) / Math.max(volume, 1) / Math.max(scale, 0.01));
    }

    function addChartGrid(svg, left, right, top, bottom, minValue, maxValue, formatter) {
        for (var index = 0; index <= 4; index += 1) {
            var y = top + (bottom - top) * index / 4;
            svg.appendChild(makeSvg('line', { x1: left, y1: y, x2: right, y2: y, 'class': 'kodex-history-grid' }));
            var label = makeSvg('text', { x: right + 10, y: y + 4, 'class': 'kodex-history-axis-label' });
            label.textContent = formatter(maxValue - (maxValue - minValue) * index / 4);
            svg.appendChild(label);
        }
    }

    function addChartSectionLabel(svg, text, x, y) {
        var label = makeSvg('text', { x: x, y: y, 'class': 'kodex-history-section-label' });
        label.textContent = text;
        svg.appendChild(label);
    }

    function linkedChartSelectionFor(view, index) {
        var row = view.rows[index];
        var progress = view.rows.length > 1 ? index / (view.rows.length - 1) : 0;
        var date = row && (row.date || (view.mode === 'daily' ? row.label : '')) || '';
        return {
            mode: view.mode,
            date: date,
            progress: progress,
            sourceId: view.svg.id,
            sourceIndex: index
        };
    }

    function linkedChartSelectionMatches(left, right) {
        if (!left || !right || left.mode !== right.mode) return false;
        if (left.mode === 'daily') return Boolean(left.date) && left.date === right.date;
        return Math.abs(left.progress - right.progress) < 0.0025;
    }

    function linkedChartIndexFor(view, selection) {
        if (!view || !view.rows.length || !selection || view.mode !== selection.mode) return -1;
        if (selection.mode === 'intraday') {
            return Math.max(0, Math.min(view.rows.length - 1, Math.round(selection.progress * (view.rows.length - 1))));
        }
        var exactIndex = view.rows.findIndex(function (row) {
            return (row.date || row.label || '') === selection.date;
        });
        if (exactIndex >= 0) return exactIndex;
        var target = parseHistoryDate(selection.date);
        if (!Number.isFinite(target)) {
            return Math.max(0, Math.min(view.rows.length - 1, Math.round(selection.progress * (view.rows.length - 1))));
        }
        var nearestIndex = -1;
        var nearestDistance = Infinity;
        view.rows.forEach(function (row, index) {
            var value = parseHistoryDate(row.date || row.label || '');
            if (!Number.isFinite(value)) return;
            var distance = Math.abs(value - target);
            if (distance < nearestDistance) {
                nearestDistance = distance;
                nearestIndex = index;
            }
        });
        return nearestIndex;
    }

    function applyLinkedChartSelection(selection) {
        Object.keys(linkedChartViews).forEach(function (id) {
            var view = linkedChartViews[id];
            var index = linkedChartIndexFor(view, selection);
            var selectedIndex = String(index);
            Array.prototype.forEach.call(view.svg.querySelectorAll('[data-chart-bar-index]'), function (element) {
                var selected = index >= 0 && element.getAttribute('data-chart-bar-index') === selectedIndex;
                element.classList.toggle('is-linked-selected', selected);
                element.classList.toggle('is-selected', selected);
                element.classList.toggle('is-locked', selected && Boolean(linkedChartLockedSelection));
                element.setAttribute('aria-selected', selected ? 'true' : 'false');
            });
            if (index >= 0 && view.rows[index]) view.updateReadout(view.rows[index]);
        });
    }

    function clearLinkedChartSelection(restoreLatest) {
        linkedChartHoverSelection = null;
        linkedChartLockedSelection = null;
        Object.keys(linkedChartViews).forEach(function (id) {
            var view = linkedChartViews[id];
            Array.prototype.forEach.call(view.svg.querySelectorAll('[data-chart-bar-index]'), function (element) {
                element.classList.remove('is-linked-selected', 'is-selected', 'is-locked');
                element.setAttribute('aria-selected', 'false');
            });
            if (restoreLatest && view.rows.length) view.updateReadout(view.rows[view.rows.length - 1]);
        });
    }

    function activateLinkedChartSelection(svg, index, lockSelection) {
        var view = svg && linkedChartViews[svg.id];
        if (!view || !view.rows[index]) return;
        var selection = linkedChartSelectionFor(view, index);
        if (lockSelection) {
            if (linkedChartSelectionMatches(linkedChartLockedSelection, selection)) {
                clearLinkedChartSelection(true);
                return;
            }
            linkedChartLockedSelection = selection;
        } else {
            if (linkedChartLockedSelection) return;
            linkedChartHoverSelection = selection;
        }
        applyLinkedChartSelection(linkedChartLockedSelection || linkedChartHoverSelection);
    }

    function bindLinkedChartBar(svg, element, index, row, updateReadout) {
        element.setAttribute('data-chart-bar-index', String(index));
        element.setAttribute('aria-selected', 'false');
        element.addEventListener('pointerenter', function () {
            activateLinkedChartSelection(svg, index, false);
        });
        element.addEventListener('focus', function () {
            activateLinkedChartSelection(svg, index, false);
        });
        element.addEventListener('click', function (event) {
            event.stopPropagation();
            activateLinkedChartSelection(svg, index, true);
        });
    }

    function registerLinkedChartHitZones(svg, rows, updateReadout, options) {
        var settings = options || {};
        var left = Number(settings.left) || 0;
        var right = Number(settings.right) || 1000;
        var top = Number(settings.top) || 0;
        var bottom = Number(settings.bottom) || 500;
        var xStep = (right - left) / Math.max(rows.length, 1);
        var view = {
            svg: svg,
            rows: rows,
            updateReadout: updateReadout,
            mode: settings.mode === 'intraday' ? 'intraday' : 'daily'
        };
        linkedChartViews[svg.id] = view;
        rows.forEach(function (row, index) {
            var hitbox = makeSvg('rect', {
                x: left + xStep * index,
                y: top,
                width: Math.max(1, xStep),
                height: Math.max(1, bottom - top),
                'class': 'linked-chart-hitbox' + (settings.className ? ' ' + settings.className : ''),
                tabindex: '0',
                role: 'button',
                'aria-label': (typeof settings.ariaLabel === 'function' ? settings.ariaLabel(row) : (row.date || row.label || row.time || '')) + ' 차트 값 보기'
            });
            bindLinkedChartBar(svg, hitbox, index, row, updateReadout);
            svg.appendChild(hitbox);
        });
        if (svg.__linkedChartBlankClick) svg.removeEventListener('click', svg.__linkedChartBlankClick);
        svg.__linkedChartBlankClick = function (event) {
            if (!event.target.closest || !event.target.closest('.linked-chart-hitbox')) clearLinkedChartSelection(true);
        };
        svg.addEventListener('click', svg.__linkedChartBlankClick);
        var current = linkedChartLockedSelection || linkedChartHoverSelection;
        if (current) {
            applyLinkedChartSelection(current);
            Promise.resolve().then(function () {
                if (linkedChartViews[svg.id] === view) {
                    applyLinkedChartSelection(linkedChartLockedSelection || linkedChartHoverSelection);
                }
            });
        }
    }

    function kospiPeriodMonths() {
        return selectedKodexPeriod === '1m' ? 1 : 3;
    }

    function kospiPeriodLabel() {
        return selectedKodexPeriod === '1m' ? '1개월' : '3개월';
    }

    function kospiFlowPageCount() {
        return 15;
    }

    function seoulIsoDate(value) {
        var timestamp = Date.parse(value);
        if (!Number.isFinite(timestamp)) return '';
        var parts = new Intl.DateTimeFormat('en-CA', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        }).formatToParts(new Date(timestamp));
        var values = {};
        parts.forEach(function (part) { values[part.type] = part.value; });
        return values.year + '-' + values.month + '-' + values.day;
    }

    function mergeCurrentKospiHistory(rows, market) {
        var result = (rows || []).map(function (row) { return Object.assign({}, row); });
        if (!market || !market.asOf || ![market.open, market.high, market.low, market.value].every(Number.isFinite)) return result;
        var date = seoulIsoDate(market.asOf);
        if (!date) return result;
        var foreignFlow = (market.flows || []).filter(function (flow) { return flow.label === '외국인'; })[0];
        var current = {
            date: date,
            open: market.open,
            high: market.high,
            low: market.low,
            close: market.value,
            volume: Number.isFinite(market.volume) ? market.volume : null,
            foreign: foreignFlow && Number.isFinite(foreignFlow.value) ? foreignFlow.value : null,
            institution: null,
            personal: null,
            flowUnit: foreignFlow && foreignFlow.unit || '억원'
        };
        var index = result.findIndex(function (row) { return row.date === date; });
        if (index >= 0) {
            if (!Number.isFinite(current.volume)) current.volume = result[index].volume;
            result[index] = Object.assign({}, result[index], current);
        } else if (Number.isFinite(current.volume) && current.volume > 0) {
            result.push(current);
        }
        return result.sort(function (left, right) { return parseHistoryDate(left.date) - parseHistoryDate(right.date); });
    }

    function setKospiFlowRefreshState(state, message) {
        var button = document.getElementById('kospi-flow-refresh');
        var status = document.getElementById('kospi-flow-refresh-status');
        if (!button || !status) return;
        var loading = state === 'loading';
        button.disabled = loading;
        button.classList.toggle('is-loading', loading);
        button.setAttribute('aria-busy', loading ? 'true' : 'false');
        status.textContent = message || '';
    }

    function bindKospiFlowControls() {
        bindKodexChartControls();
        var refreshButton = document.getElementById('kospi-flow-refresh');
        if (refreshButton && refreshButton.getAttribute('data-chart-bound') !== 'true') {
            refreshButton.setAttribute('data-chart-bound', 'true');
            refreshButton.addEventListener('click', function () {
                kospiIntradayForceRefresh = selectedKodexChartMode === 'intraday';
                var liveRefresh = dashboardData ? refreshLiveMarketData(dashboardData, { force: true, silent: true }) : Promise.resolve(false);
                return Promise.all([liveRefresh, loadKospiTechnicalHistory(true)]).then(function () {
                    renderSynchronizedTechnicalCharts();
                });
            });
        }
    }

    function loadKospiTechnicalHistory(forceRefresh) {
        bindKospiFlowControls();
        if (!liveMarketSource || !window.MarketDashboardLive
            || typeof window.MarketDashboardLive.fetchKospiTechnicalHistory !== 'function') return Promise.resolve(false);
        var requestToken = ++kospiHistoryRequestToken;
        var readout = document.getElementById('kospi-flow-readout');
        setKospiFlowRefreshState('loading', kospiPeriodLabel() + ' 데이터 확인 중');
        if (readout && !kospiTechnicalHistory.length) readout.textContent = 'KOSPI 가격과 외국인 수급 이력을 불러오는 중입니다.';
        var controller = typeof AbortController === 'function' ? new AbortController() : null;
        var timeoutId = window.setTimeout(function () { if (controller) controller.abort(); }, 20000);
        return window.MarketDashboardLive.fetchKospiTechnicalHistory(
            window.fetch.bind(window),
            new URL(liveMarketSource, window.location.href).href,
            {
                pageCount: kospiFlowPageCount(),
                signal: controller && controller.signal,
                now: Date.now(),
                nonce: String(Date.now()),
                forceRefresh: Boolean(forceRefresh)
            }
        ).then(function (rows) {
            window.clearTimeout(timeoutId);
            if (requestToken !== kospiHistoryRequestToken) return false;
            kospiTechnicalHistory = rows;
            var market = dashboardData && findById(dashboardData.markets, 'KOSPI');
            renderKospiHistoryChart(market);
            var displayRows = mergeCurrentKospiHistory(rows, market);
            var latest = displayRows[displayRows.length - 1];
            setKospiFlowRefreshState('ready', latest ? formatHistoryDate(latest.date) + ' 기준' : '최근 거래일 기준');
            return true;
        }).catch(function () {
            window.clearTimeout(timeoutId);
            if (requestToken !== kospiHistoryRequestToken) return false;
            setKospiFlowRefreshState('error', '불러오기 실패 · 다시 시도');
            if (readout) readout.textContent = 'KOSPI 가격·외국인 수급 이력을 불러오지 못했습니다.';
            return false;
        });
    }

    function prepareKospiDailyRows(market) {
        var history = mergeCurrentKospiHistory(kospiTechnicalHistory, market).filter(function (row) {
            return row && Number.isFinite(parseHistoryDate(row.date))
                && [row.open, row.high, row.low, row.close, row.volume].every(Number.isFinite)
                && row.volume > 0;
        }).sort(function (left, right) {
            return parseHistoryDate(left.date) - parseHistoryDate(right.date);
        });
        if (!history.length) return [];
        var ma5 = simpleMovingAverage(history, 5);
        var ma20 = simpleMovingAverage(history, 20);
        var ma60 = simpleMovingAverage(history, 60);
        var flowMacd = window.MarketDashboardLive.calculateMacd(history.map(function (row) { return row.foreign; }), 12, 26, 9);
        var threshold = new Date(parseHistoryDate(history[history.length - 1].date));
        threshold.setMonth(threshold.getMonth() - kospiPeriodMonths());
        var startIndex = history.findIndex(function (row) { return parseHistoryDate(row.date) >= threshold.getTime(); });
        if (startIndex < 0) startIndex = 0;
        var runningCvd = 0;
        return history.slice(startIndex).map(function (row, index) {
            var sourceIndex = startIndex + index;
            var pressure = estimateDailyVolumePressure(row);
            runningCvd += pressure.delta;
            return Object.assign({}, row, pressure, {
                cumulativeDelta: runningCvd,
                ma5: ma5[sourceIndex],
                ma20: ma20[sourceIndex],
                ma60: ma60[sourceIndex],
                flowMacd: flowMacd.macd[sourceIndex],
                flowSignal: flowMacd.signal[sourceIndex],
                flowHistogram: flowMacd.histogram[sourceIndex]
            });
        });
    }

    function prepareKospiIntradayRows(day) {
        var minuteRows = (day && day.bars || []).map(function (row) {
            var pressure = estimateDailyVolumePressure(row);
            return Object.assign({}, row, pressure);
        });
        var rows = aggregateIntradayBars(minuteRows, selectedKodexIntradayInterval);
        rows.forEach(function (row) {
            row.date = day.date;
            var bucketRows = minuteRows.filter(function (source) {
                return source.time >= row.time && source.time <= row.endTime;
            });
            var last = bucketRows[bucketRows.length - 1];
            row.foreign = last && Number.isFinite(last.foreign) ? last.foreign : null;
            row.flowObservedAt = last && last.flowObservedAt || null;
            row.flowCarriedForward = Boolean(last && last.flowCarriedForward);
        });
        var flowMacd = window.MarketDashboardLive.calculateMacd(rows.map(function (row) { return row.foreign; }), 12, 26, 9);
        return rows.map(function (row, index) {
            return Object.assign({}, row, {
                flowMacd: flowMacd.macd[index],
                flowSignal: flowMacd.signal[index],
                flowHistogram: flowMacd.histogram[index]
            });
        });
    }

    function renderKospiRows(rows, options) {
        var svg = document.getElementById('kospi-flow-chart');
        var summary = document.getElementById('kospi-flow-summary');
        var readout = document.getElementById('kospi-flow-readout');
        var title = document.getElementById('kospi-flow-title');
        var eyebrow = document.getElementById('kospi-flow-eyebrow');
        var method = document.getElementById('kospi-flow-method');
        var sourceNote = document.getElementById('kospi-flow-source-note');
        if (!svg || !summary || !readout) return;
        clear(svg);
        clear(summary);
        var intraday = options.mode === 'intraday';
        svg.classList.toggle('is-intraday', intraday);
        if (title) title.textContent = intraday
            ? 'KOSPI 가격과 외국인 수급 · ' + formatHistoryDate(options.date) + ' ' + selectedKodexIntradayInterval + '분봉'
            : 'KOSPI 가격과 외국인 수급 · ' + kospiPeriodLabel();
        if (eyebrow) eyebrow.textContent = intraday
            ? 'KOSPI 분봉 · 거래량 X-ray · CVD · 외국인 수급 MACD'
            : 'KOSPI 일봉 · 거래량 X-ray · CVD · 외국인 수급 MACD';
        if (method) method.textContent = intraday
            ? '거래량 막대에는 가격 움직임으로 추정한 매수·매도 우위를 겹치고, 외국인 장중 누적 순매수의 흐름은 막대와 MACD로 함께 표시합니다.'
            : '거래량 막대에는 일봉 가격 범위와 종가 위치로 추정한 매수·매도 우위를 겹치고, 외국인 일별 순매수의 흐름은 막대와 MACD로 함께 표시합니다.';
        if (sourceNote) sourceNote.textContent = intraday
            ? 'KOSPI 분봉과 외국인 장중 누적 순매수는 Naver Finance의 KRX 공개 데이터 기준입니다.'
            : 'KOSPI 일봉과 외국인 현물 순매수는 Naver Finance의 KRX 공개 데이터 기준입니다.';
        Array.prototype.forEach.call(document.querySelectorAll('[data-kospi-daily-legend]'), function (node) {
            node.hidden = intraday;
        });
        if (rows.length < 5) {
            var empty = makeSvg('text', { x: 500, y: 350, 'class': 'kodex-history-empty', 'text-anchor': 'middle' });
            empty.textContent = '선택한 기준의 KOSPI 가격·수급 데이터를 확인하고 있습니다.';
            svg.appendChild(empty);
            return;
        }

        svg.setAttribute('viewBox', '0 0 1000 720');
        var width = 1000;
        var margin = { left: 28, right: 92 };
        var right = width - margin.right;
        var priceTop = 34;
        var priceBottom = 328;
        var flowTop = 366;
        var flowPlotTop = 392;
        var flowBottom = 520;
        var flowZero = (flowPlotTop + flowBottom) / 2;
        var macdTop = 566;
        var macdBottom = 676;
        var xStep = (right - margin.left) / rows.length;
        var candleWidth = Math.max(1.4, Math.min(8.5, xStep * 0.58));
        function xFor(index) { return margin.left + xStep * index + xStep / 2; }

        var priceValues = [];
        rows.forEach(function (row) {
            priceValues.push(row.high, row.low);
            if (!intraday) [row.ma5, row.ma20, row.ma60].forEach(function (value) {
                if (Number.isFinite(value)) priceValues.push(value);
            });
        });
        var minPrice = Math.min.apply(Math, priceValues);
        var maxPrice = Math.max.apply(Math, priceValues);
        var priceSpread = Math.max(maxPrice - minPrice, Math.abs(maxPrice || 1) * 0.01);
        minPrice -= priceSpread * 0.05;
        maxPrice += priceSpread * 0.05;
        function priceY(value) { return priceTop + (maxPrice - value) / (maxPrice - minPrice) * (priceBottom - priceTop); }
        addChartGrid(svg, margin.left, right, priceTop, priceBottom, minPrice, maxPrice, function (value) {
            return formatNumber(value, 0);
        });
        addChartSectionLabel(svg, intraday ? selectedKodexIntradayInterval + '분봉' : '일봉', margin.left, priceTop + 12);
        addChartSectionLabel(svg, '거래량 X-ray · CVD · 외국인 현물', margin.left, flowTop + 12);
        addChartSectionLabel(svg, '외국인 수급 MACD 12 · 26 · 9', margin.left, macdTop + 12);

        var maxVolume = Math.max.apply(Math, rows.map(function (row) { return row.volume; }));
        function volumeY(value) { return flowBottom - value / Math.max(maxVolume, 1) * (flowBottom - flowPlotTop); }
        var forceScale = pressureStrengthScale(rows, function (row) { return row.delta; }, function (row) { return row.volume; });
        var cvdValues = rows.map(function (row) { return row.cumulativeDelta; });
        var minCvd = Math.min.apply(Math, [0].concat(cvdValues));
        var maxCvd = Math.max.apply(Math, [0].concat(cvdValues));
        var cvdSpread = Math.max(maxCvd - minCvd, 1);
        function cvdY(value) { return flowPlotTop + 3 + (maxCvd - value) / cvdSpread * (flowBottom - flowPlotTop - 10); }
        var foreignValues = rows.map(function (row) { return row.foreign; }).filter(Number.isFinite);
        var maxForeignAbs = Math.max.apply(Math, [1].concat(foreignValues.map(Math.abs)));
        function foreignY(value) {
            var halfHeight = (flowBottom - flowPlotTop) / 2 - 4;
            return flowZero - value / maxForeignAbs * halfHeight;
        }
        svg.appendChild(makeSvg('line', { x1: margin.left, y1: flowZero, x2: right, y2: flowZero, 'class': 'kospi-flow-zero-line' }));
        [
            { value: maxForeignAbs, y: flowPlotTop + 5 },
            { value: 0, y: flowZero + 4 },
            { value: -maxForeignAbs, y: flowBottom - 3 }
        ].forEach(function (tick) {
            var label = makeSvg('text', { x: right + 10, y: tick.y, 'class': 'kospi-flow-axis-label' });
            label.textContent = formatSigned(tick.value, '억', 0);
            svg.appendChild(label);
        });

        var macdValues = [];
        rows.forEach(function (row) {
            [row.flowMacd, row.flowSignal, row.flowHistogram].forEach(function (value) {
                if (Number.isFinite(value)) macdValues.push(Math.abs(value));
            });
        });
        var maxMacdAbs = Math.max.apply(Math, [1].concat(macdValues));
        function macdY(value) { return macdTop + (maxMacdAbs - value) / (maxMacdAbs * 2) * (macdBottom - macdTop); }
        var macdZero = macdY(0);
        svg.appendChild(makeSvg('line', { x1: margin.left, y1: macdZero, x2: right, y2: macdZero, 'class': 'kospi-flow-zero-line' }));

        function rowLabel(row) {
            return intraday ? formatHistoryDate(row.date) + ' ' + row.endTime : formatHistoryDate(row.date);
        }
        function updateReadout(row) {
            var parts = [
                rowLabel(row),
                '종가 ' + formatNumber(row.close, 2),
                '시가 ' + formatNumber(row.open, 2),
                '고가 ' + formatNumber(row.high, 2),
                '저가 ' + formatNumber(row.low, 2),
                '거래량 ' + formatNumber(row.volume, 0) + '천주',
                '추정 순압력 ' + formatPressurePercent(row.delta, row.volume),
                'CVD ' + formatSigned(row.cumulativeDelta, '천주', 0)
            ];
            if (Number.isFinite(row.foreign)) parts.push('외국인 ' + formatSigned(row.foreign, '억원', 0));
            if (Number.isFinite(row.flowMacd)) parts.push('수급 MACD ' + formatSigned(row.flowMacd, '억원', 2));
            if (Number.isFinite(row.flowSignal)) parts.push('Signal ' + formatSigned(row.flowSignal, '억원', 2));
            readout.textContent = parts.join(' · ');
        }

        var cvdPath = '';
        rows.forEach(function (row, index) {
            var x = xFor(index);
            var tone = row.close > row.open ? 'is-up' : row.close < row.open ? 'is-down' : 'is-flat';
            var candleGroup = makeSvg('g', { 'class': 'kospi-flow-candle-group ' + tone, tabindex: '0', role: 'img' });
            candleGroup.appendChild(makeSvg('line', {
                x1: x, y1: priceY(row.high), x2: x, y2: priceY(row.low), 'class': 'kospi-flow-candle-wick ' + tone
            }));
            candleGroup.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: Math.min(priceY(row.open), priceY(row.close)),
                width: candleWidth,
                height: Math.max(1.8, Math.abs(priceY(row.open) - priceY(row.close))),
                rx: 1,
                'class': 'kospi-flow-candle ' + tone
            }));
            bindLinkedChartBar(svg, candleGroup, index, row, updateReadout);
            candleGroup.setAttribute('aria-label', rowLabel(row) + ', 종가 ' + formatNumber(row.close, 2));
            svg.appendChild(candleGroup);

            var volumeTop = volumeY(row.volume);
            var volumeHeight = Math.max(1, flowBottom - volumeTop);
            var forceHeight = Math.max(1.5, volumeHeight * pressureFillRatio(row.delta, row.volume, forceScale));
            var volumeGroup = makeSvg('g', { 'class': 'kospi-flow-volume-group kodex-history-volume-group', tabindex: '0', role: 'img' });
            volumeGroup.appendChild(makeSvg('rect', {
                x: x - candleWidth * 0.58, y: volumeTop, width: candleWidth * 1.16, height: volumeHeight,
                rx: 0.7, 'class': 'kospi-flow-volume is-xray-base'
            }));
            volumeGroup.appendChild(makeSvg('rect', {
                x: x - candleWidth * 0.58,
                y: flowBottom - forceHeight,
                width: candleWidth * 1.16,
                height: forceHeight,
                rx: 0.7,
                'class': 'kospi-flow-volume-force ' + (row.delta >= 0 ? 'is-buy' : 'is-sell')
            }));
            bindLinkedChartBar(svg, volumeGroup, index, row, updateReadout);
            var volumeLabel = rowLabel(row)
                + ', 거래량 ' + formatNumber(row.volume, 0) + '천주'
                + ', 추정 순압력 ' + formatPressurePercent(row.delta, row.volume)
                + ', CVD ' + formatSigned(row.cumulativeDelta, '천주', 0);
            if (Number.isFinite(row.foreign)) volumeLabel += ', 외국인 ' + formatSigned(row.foreign, '억원', 0);
            volumeGroup.setAttribute('aria-label', volumeLabel);
            svg.appendChild(volumeGroup);

            if (Number.isFinite(row.foreign)) {
                var foreignEnd = foreignY(row.foreign);
                var foreignBar = makeSvg('rect', {
                    x: x - candleWidth * 0.22,
                    y: Math.min(flowZero, foreignEnd),
                    width: candleWidth * 0.44,
                    height: Math.max(1.5, Math.abs(foreignEnd - flowZero)),
                    'class': 'kospi-flow-foreign ' + (row.foreign >= 0 ? 'is-buy' : 'is-sell')
                });
                svg.appendChild(foreignBar);
                bindLinkedChartBar(svg, foreignBar, index, row, updateReadout);
            }
            if (Number.isFinite(row.flowHistogram)) {
                var histogramEnd = macdY(row.flowHistogram);
                var histogramBar = makeSvg('rect', {
                    x: x - candleWidth * 0.42,
                    y: Math.min(macdZero, histogramEnd),
                    width: candleWidth * 0.84,
                    height: Math.max(1, Math.abs(histogramEnd - macdZero)),
                    'class': 'kospi-flow-macd-histogram ' + (row.flowHistogram >= 0 ? 'is-positive' : 'is-negative')
                });
                svg.appendChild(histogramBar);
                bindLinkedChartBar(svg, histogramBar, index, row, updateReadout);
            }
            cvdPath += (cvdPath ? ' L ' : 'M ') + x.toFixed(2) + ' ' + cvdY(row.cumulativeDelta).toFixed(2);
        });
        if (cvdPath) svg.appendChild(makeSvg('path', { d: cvdPath, 'class': 'kospi-flow-cvd' }));

        if (!intraday) [
            { key: 'ma5', className: 'kodex-history-line is-ma5' },
            { key: 'ma20', className: 'kodex-history-line is-ma20' },
            { key: 'ma60', className: 'kodex-history-line is-ma60' }
        ].forEach(function (series) {
            var path = svgPathForSeries(rows.map(function (row) { return row[series.key]; }), 0, xFor, priceY);
            if (path) svg.appendChild(makeSvg('path', { d: path, 'class': series.className }));
        });
        var macdPath = svgPathForSeries(rows.map(function (row) { return row.flowMacd; }), 0, xFor, macdY);
        var signalPath = svgPathForSeries(rows.map(function (row) { return row.flowSignal; }), 0, xFor, macdY);
        if (macdPath) svg.appendChild(makeSvg('path', { d: macdPath, 'class': 'kospi-flow-macd-line' }));
        if (signalPath) svg.appendChild(makeSvg('path', { d: signalPath, 'class': 'kospi-flow-signal-line' }));

        var tickIndexes = [0, Math.floor((rows.length - 1) * 0.25), Math.floor((rows.length - 1) * 0.5), Math.floor((rows.length - 1) * 0.75), rows.length - 1]
            .filter(function (value, index, values) { return value >= 0 && values.indexOf(value) === index; });
        tickIndexes.forEach(function (index) {
            var label = makeSvg('text', {
                x: xFor(index), y: 707, 'class': 'kodex-history-date-label',
                'text-anchor': index === 0 ? 'start' : index === rows.length - 1 ? 'end' : 'middle'
            });
            label.textContent = intraday ? rows[index].endTime : formatHistoryDate(rows[index].date);
            svg.appendChild(label);
        });

        registerLinkedChartHitZones(svg, rows, updateReadout, {
            mode: intraday ? 'intraday' : 'daily',
            left: margin.left,
            right: right,
            top: priceTop,
            bottom: macdBottom,
            className: 'kospi-flow-hitbox',
            ariaLabel: rowLabel
        });

        var first = rows[0];
        var latest = rows[rows.length - 1];
        var latestMacd = rows.slice().reverse().filter(function (row) {
            return Number.isFinite(row.flowMacd) && Number.isFinite(row.flowSignal);
        })[0];
        appendKodexMetric(summary, intraday ? '현재 지수' : '최근 종가', formatNumber(latest.close, 2));
        appendKodexMetric(summary, intraday ? '장중 수익률' : '기간 수익률', formatSigned((latest.close / first.open - 1) * 100, '%', 2));
        appendKodexMetric(summary, '종료 CVD', formatSigned(latest.cumulativeDelta, '천주', 0));
        if (intraday) {
            appendKodexMetric(summary, '외국인 장중 누적', formatSigned(latest.foreign, '억원', 0));
        } else {
            var cumulativeForeign = rows.reduce(function (total, row) {
                return total + (Number.isFinite(row.foreign) ? row.foreign : 0);
            }, 0);
            appendKodexMetric(summary, '외국인 기간 누적', formatSigned(cumulativeForeign, '억원', 0));
        }
        appendKodexMetric(summary, '수급 MACD', latestMacd
            ? (latestMacd.flowMacd >= latestMacd.flowSignal ? 'MACD가 Signal 위' : 'MACD가 Signal 아래')
            : '수급 데이터 확인 중');
        appendKodexMetric(summary, intraday ? '기준 시각' : '기준일', rowLabel(latest));
        updateReadout(latest);
    }

    function renderKospiIntradayChart() {
        var svg = document.getElementById('kospi-flow-chart');
        var summary = document.getElementById('kospi-flow-summary');
        var readout = document.getElementById('kospi-flow-readout');
        if (!svg || !summary || !readout) return;
        if (!selectedKodexIntradayDate || !liveMarketSource || !window.MarketDashboardLive
            || typeof window.MarketDashboardLive.fetchKospiIntradayDay !== 'function') {
            renderKospiRows([], { mode: 'intraday', date: selectedKodexIntradayDate });
            readout.textContent = '선택한 거래일의 KOSPI 분봉과 외국인 수급을 확인하고 있습니다.';
            return;
        }
        var selectedDate = selectedKodexIntradayDate;
        var cached = kospiIntradayViewCache[selectedDate];
        var forceRefresh = kospiIntradayForceRefresh;
        kospiIntradayForceRefresh = false;
        if (cached && cached.day) {
            renderKospiRows(prepareKospiIntradayRows(cached.day), { mode: 'intraday', date: cached.day.date });
            if (!forceRefresh && Date.now() - cached.receivedAt < 60 * 1000) {
                setKospiFlowRefreshState('ready', cached.day.flowSourceLastAt
                    ? formatHistoryDate(cached.day.date) + ' ' + cached.day.flowSourceLastAt.slice(11, 16) + ' 수급 기준'
                    : formatHistoryDate(cached.day.date) + ' 가격 기준');
                return;
            }
        } else {
            renderKospiRows([], { mode: 'intraday', date: selectedDate });
        }
        if (kospiIntradayAbortController && kospiIntradayRequestDate === selectedDate && !forceRefresh) return;
        if (kospiIntradayAbortController) kospiIntradayAbortController.abort();
        kospiIntradayAbortController = typeof AbortController === 'function' ? new AbortController() : null;
        kospiIntradayRequestDate = selectedDate;
        var token = ++kospiIntradayRenderToken;
        var controller = kospiIntradayAbortController;
        var timeoutId = window.setTimeout(function () { if (controller) controller.abort(); }, 20000);
        if (!cached) readout.textContent = formatHistoryDate(selectedDate) + ' 분봉과 외국인 수급을 불러오는 중입니다.';
        setKospiFlowRefreshState('loading', formatHistoryDate(selectedDate) + ' 분봉 수급 확인 중');
        window.MarketDashboardLive.fetchKospiIntradayDay(
            window.fetch.bind(window),
            new URL(liveMarketSource, window.location.href).href,
            selectedDate,
            {
                now: Date.now(),
                nonce: String(Date.now()),
                forceRefresh: forceRefresh,
                signal: controller && controller.signal,
                concurrencyLimit: 6
            }
        ).then(function (day) {
            if (token !== kospiIntradayRenderToken || selectedKodexChartMode !== 'intraday') return;
            kospiIntradayViewCache[day.date] = { day: day, receivedAt: Date.now() };
            renderKospiRows(prepareKospiIntradayRows(day), { mode: 'intraday', date: day.date });
            setKospiFlowRefreshState('ready', day.flowSourceLastAt
                ? formatHistoryDate(day.date) + ' ' + day.flowSourceLastAt.slice(11, 16) + ' 수급 기준'
                : formatHistoryDate(day.date) + ' 가격 기준');
        }).catch(function (error) {
            if (token !== kospiIntradayRenderToken) return;
            if (error && error.name === 'AbortError') {
                setKospiFlowRefreshState(cached ? 'ready' : 'error', cached
                    ? formatHistoryDate(selectedDate) + ' 이전 수급 유지'
                    : '분봉 수급 불러오기 중단 · 다시 시도');
                return;
            }
            readout.textContent = '선택한 거래일의 KOSPI 분봉·외국인 수급을 불러오지 못했습니다.';
            setKospiFlowRefreshState('error', '분봉 수급 불러오기 실패');
        }).finally(function () {
            window.clearTimeout(timeoutId);
            if (controller === kospiIntradayAbortController) {
                kospiIntradayAbortController = null;
                kospiIntradayRequestDate = '';
            }
        });
    }

    function renderKospiHistoryChart(market) {
        bindKospiFlowControls();
        var instrument = dashboardData && findById(dashboardData.technical.instruments, 'KODEX');
        if (instrument) setKodexChartControls(instrument);
        if (selectedKodexChartMode === 'intraday') {
            renderKospiIntradayChart();
            return;
        }
        if (kospiIntradayAbortController) {
            kospiIntradayAbortController.abort();
            kospiIntradayAbortController = null;
            kospiIntradayRequestDate = '';
        }
        kospiIntradayRenderToken += 1;
        var dailyRows = prepareKospiDailyRows(market);
        renderKospiRows(dailyRows, { mode: 'daily' });
        var latestDaily = dailyRows[dailyRows.length - 1];
        setKospiFlowRefreshState('ready', latestDaily
            ? formatHistoryDate(latestDaily.date) + ' 기준'
            : kospiPeriodLabel() + ' 일봉');
    }

    function renderKodexDailyChart(instrument, svg, summary, readout) {
        var svg = document.getElementById('kodex-history-chart');
        var liveInstrument = instrument && instrument.liveSnapshot || {};
        var history = (liveInstrument.priceHistory || instrument && instrument.priceHistory || []).filter(function (row) {
            return row && Number.isFinite(parseHistoryDate(row.date))
                && [row.open, row.high, row.low, row.close, row.volume].every(Number.isFinite);
        }).sort(function (left, right) {
            return parseHistoryDate(left.date) - parseHistoryDate(right.date);
        });

        if (history.length < 5) {
            readout.textContent = '3개월 일봉·거래량 차트를 불러오지 못했습니다. 최근 거래일 수급표는 아래에서 확인할 수 있습니다.';
            var empty = makeSvg('text', { x: 500, y: 250, 'class': 'kodex-history-empty', 'text-anchor': 'middle' });
            empty.textContent = '3개월 일봉·거래량 데이터를 확인하고 있습니다.';
            svg.appendChild(empty);
            return;
        }

        var latestTimestamp = parseHistoryDate(history[history.length - 1].date);
        var threshold = new Date(latestTimestamp);
        threshold.setMonth(threshold.getMonth() - (selectedKodexPeriod === '1m' ? 1 : 3));
        var startIndex = history.findIndex(function (row) { return parseHistoryDate(row.date) >= threshold.getTime(); });
        if (startIndex < 0) startIndex = 0;
        var rows = history.slice(startIndex);
        var ma5 = simpleMovingAverage(history, 5);
        var ma20 = simpleMovingAverage(history, 20);
        var ma60 = simpleMovingAverage(history, 60);

        svg.setAttribute('viewBox', '0 0 1000 530');
        var width = 1000;
        var margin = { left: 24, right: 88 };
        var innerWidth = width - margin.left - margin.right;
        var priceTop = 34;
        var priceBottom = 300;
        var volumeTop = 336;
        var volumePlotTop = volumeTop + 30;
        var volumeBottom = 476;
        var xStep = innerWidth / rows.length;
        var candleWidth = Math.max(2.5, Math.min(9, xStep * 0.58));

        function xFor(index) { return margin.left + xStep * index + xStep / 2; }

        var priceValues = [];
        rows.forEach(function (row) { priceValues.push(row.high, row.low); });
        [ma5, ma20, ma60].forEach(function (series) {
            series.slice(startIndex).forEach(function (value) {
                if (Number.isFinite(value)) priceValues.push(value);
            });
        });
        var minPrice = Math.min.apply(Math, priceValues);
        var maxPrice = Math.max.apply(Math, priceValues);
        var priceSpread = Math.max(maxPrice - minPrice, Math.abs(maxPrice || 1) * 0.01);
        minPrice -= priceSpread * 0.05;
        maxPrice += priceSpread * 0.05;
        function priceY(value) {
            return priceTop + (maxPrice - value) / (maxPrice - minPrice) * (priceBottom - priceTop);
        }

        addChartGrid(svg, margin.left, width - margin.right, priceTop, priceBottom, minPrice, maxPrice, function (value) {
            return formatNumber(value, 0);
        });
        addChartSectionLabel(svg, '일봉', margin.left, priceTop + 12);
        addChartSectionLabel(svg, '거래량 X-ray · CVD', margin.left, volumeTop + 12);

        var maxVolume = Math.max.apply(Math, rows.map(function (row) { return row.volume; }));
        function volumeY(value) {
            return volumeBottom - value / Math.max(maxVolume, 1) * (volumeBottom - volumePlotTop);
        }

        var dailyPressure = {};
        var runningCvd = 0;
        rows.forEach(function (row) {
            var pressure = validVolumePressure(row);
            if (!pressure) return;
            runningCvd += pressure.delta;
            dailyPressure[row.date] = {
                delta: pressure.delta,
                imbalance: pressure.delta / Math.max(row.volume, 1) * 100,
                cvd: runningCvd,
                coverageRatio: pressure.coverageRatio
            };
        });
        rows.forEach(function (row) {
            if (dailyPressure[row.date]) dailyPressure[row.date].volume = row.volume;
        });
        var pressureRows = Object.keys(dailyPressure).map(function (date) { return dailyPressure[date]; });
        var forceScale = pressureStrengthScale(pressureRows, function (row) { return row.delta; }, function (row) {
            return row.volume || 1;
        });
        var cvdValues = pressureRows.map(function (row) { return row.cvd; });
        var minCvd = Math.min.apply(Math, [0].concat(cvdValues));
        var maxCvd = Math.max.apply(Math, [0].concat(cvdValues));
        var cvdSpread = Math.max(maxCvd - minCvd, 1);
        function cvdY(value) { return volumePlotTop + 3 + (maxCvd - value) / cvdSpread * (volumeBottom - volumePlotTop - 10); }

        function updateReadout(row) {
            var parts = [
                formatHistoryDate(row.date),
                '종가 ' + formatPrice(row.close, '원'),
                '시가 ' + formatPrice(row.open, '원'),
                '고가 ' + formatPrice(row.high, '원'),
                '저가 ' + formatPrice(row.low, '원'),
                '거래량 ' + formatNumber(row.volume, 0) + '주'
            ];
            var pressure = dailyPressure[row.date];
            if (pressure) {
                parts.push('추정 순압력 ' + formatSigned(pressure.imbalance, '%', 2));
                parts.push('CVD ' + formatSigned(pressure.cvd, '주', 0));
                parts.push('분봉 포착률 ' + formatNumber(pressure.coverageRatio * 100, 1) + '%');
            }
            readout.textContent = parts.join(' · ');
        }

        rows.forEach(function (row, index) {
            var x = xFor(index);
            var rising = row.close > row.open;
            var falling = row.close < row.open;
            var tone = rising ? 'is-up' : falling ? 'is-down' : 'is-flat';
            var group = makeSvg('g', { 'class': 'kodex-history-candle-group ' + tone, tabindex: '0', role: 'img' });
            group.appendChild(makeSvg('line', {
                x1: x,
                y1: priceY(row.high),
                x2: x,
                y2: priceY(row.low),
                'class': 'kodex-history-wick'
            }));
            var bodyTop = Math.min(priceY(row.open), priceY(row.close));
            var bodyHeight = Math.max(1.8, Math.abs(priceY(row.open) - priceY(row.close)));
            group.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: bodyTop,
                width: candleWidth,
                height: bodyHeight,
                rx: 0.8,
                'class': 'kodex-history-candle'
            }));
            bindLinkedChartBar(svg, group, index, row, updateReadout);
            group.setAttribute('aria-label', formatHistoryDate(row.date) + ', 종가 ' + formatPrice(row.close, '원')
                + (dailyPressure[row.date] ? ', 추정 순압력 ' + formatSigned(dailyPressure[row.date].imbalance, '%', 2) : ''));
            var title = makeSvg('title');
            title.textContent = formatHistoryDate(row.date) + ' 종가 ' + formatPrice(row.close, '원');
            group.appendChild(title);
            svg.appendChild(group);

            var pressure = dailyPressure[row.date];
            var volumeGroup = makeSvg('g', { 'class': 'kodex-history-volume-group', tabindex: '0', role: 'img' });
            volumeGroup.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: volumeY(row.volume),
                width: candleWidth,
                height: Math.max(1, volumeBottom - volumeY(row.volume)),
                rx: 0.7,
                'class': 'kodex-history-volume ' + (pressure ? 'is-xray-base' : tone)
            }));
            if (pressure) {
                var totalHeight = Math.max(1, volumeBottom - volumeY(row.volume));
                var forceHeight = Math.max(1.5, totalHeight * pressureFillRatio(pressure.delta, row.volume, forceScale));
                volumeGroup.appendChild(makeSvg('rect', {
                    x: x - candleWidth / 2,
                    y: volumeBottom - forceHeight,
                    width: candleWidth,
                    height: forceHeight,
                    rx: 0.7,
                    'class': 'kodex-history-volume-force ' + (pressure.delta >= 0 ? 'is-buy' : 'is-sell')
                }));
            }
            bindLinkedChartBar(svg, volumeGroup, index, row, updateReadout);
            volumeGroup.setAttribute('aria-label', formatHistoryDate(row.date) + ', 거래량 ' + formatNumber(row.volume, 0) + '주'
                + (pressure ? ', 추정 순압력 ' + formatSigned(pressure.imbalance, '%', 2) : ''));
            var volumeTitle = makeSvg('title');
            volumeTitle.textContent = formatHistoryDate(row.date) + ' 거래량 ' + formatNumber(row.volume, 0) + '주'
                + (pressure ? ', 추정 순압력 ' + formatSigned(pressure.imbalance, '%', 2) : '');
            volumeGroup.appendChild(volumeTitle);
            svg.appendChild(volumeGroup);
        });

        var cvdPath = '';
        rows.forEach(function (row, index) {
            var pressure = dailyPressure[row.date];
            if (!pressure) return;
            cvdPath += (cvdPath ? ' L ' : 'M ') + xFor(index).toFixed(2) + ' ' + cvdY(pressure.cvd).toFixed(2);
        });
        if (cvdPath) svg.appendChild(makeSvg('path', { d: cvdPath, 'class': 'kodex-history-cvd' }));

        [
            { values: ma5, className: 'is-ma5' },
            { values: ma20, className: 'is-ma20' },
            { values: ma60, className: 'is-ma60' }
        ].forEach(function (series) {
            var path = svgPathForSeries(series.values, startIndex, xFor, priceY);
            if (path) svg.appendChild(makeSvg('path', { d: path, 'class': 'kodex-history-line ' + series.className }));
        });

        var tickIndexes = [0, Math.floor((rows.length - 1) / 4), Math.floor((rows.length - 1) / 2), Math.floor((rows.length - 1) * 3 / 4), rows.length - 1]
            .filter(function (value, index, values) { return values.indexOf(value) === index; });
        tickIndexes.forEach(function (index) {
            var tick = makeSvg('text', {
                x: xFor(index),
                y: 512,
                'class': 'kodex-history-date-label',
                'text-anchor': index === 0 ? 'start' : index === rows.length - 1 ? 'end' : 'middle'
            });
            tick.textContent = formatHistoryDate(rows[index].date).replace('월 ', '/').replace('일', '');
            svg.appendChild(tick);
        });

        registerLinkedChartHitZones(svg, rows, updateReadout, {
            mode: 'daily',
            left: margin.left,
            right: width - margin.right,
            top: priceTop,
            bottom: volumeBottom,
            ariaLabel: function (row) { return formatHistoryDate(row.date); }
        });

        var latest = rows[rows.length - 1];
        updateReadout(latest);
        var periodReturn = rows[0].close ? (latest.close / rows[0].close - 1) * 100 : NaN;
        var periodVolume = rows.reduce(function (total, row) { return total + row.volume; }, 0);
        appendKodexMetric(summary, selectedKodexPeriod === '1m' ? '1개월 수익률' : '3개월 수익률', formatSigned(periodReturn, '%', 2));
        appendKodexMetric(summary, '기간 최고', formatPrice(Math.max.apply(Math, rows.map(function (row) { return row.high; })), '원'));
        appendKodexMetric(summary, '기간 최저', formatPrice(Math.min.apply(Math, rows.map(function (row) { return row.low; })), '원'));
        appendKodexMetric(summary, '누적 거래량', formatCompactVolume(periodVolume));
        appendKodexMetric(summary, '일평균 거래량', formatCompactVolume(periodVolume / rows.length));
    }

    function renderKodexIntradayRows(day, interval, svg, summary, readout, options) {
        var settings = options || {};
        var priceText = typeof settings.priceFormatter === 'function'
            ? settings.priceFormatter
            : function (value) { return formatPrice(value, '원'); };
        var axisText = typeof settings.axisFormatter === 'function'
            ? settings.axisFormatter
            : function (value) { return formatNumber(value, 0); };
        var rows = aggregateIntradayBars(day.bars, interval);
        svg.setAttribute('viewBox', '0 0 1000 590');
        var width = 1000;
        var margin = { left: 24, right: 88 };
        var right = width - margin.right;
        var innerWidth = right - margin.left;
        var priceTop = 34;
        var priceBottom = 305;
        var volumeTop = 345;
        var volumePlotTop = volumeTop + 32;
        var volumeBottom = 530;
        var xStep = innerWidth / rows.length;
        var candleWidth = Math.max(2.5, Math.min(14, xStep * 0.62));
        function xFor(index) { return margin.left + xStep * index + xStep / 2; }

        var minPrice = Math.min.apply(Math, rows.map(function (row) { return row.low; }));
        var maxPrice = Math.max.apply(Math, rows.map(function (row) { return row.high; }));
        var priceSpread = Math.max(maxPrice - minPrice, Math.abs(maxPrice || 1) * 0.005);
        minPrice -= priceSpread * 0.04;
        maxPrice += priceSpread * 0.04;
        function priceY(value) { return priceTop + (maxPrice - value) / (maxPrice - minPrice) * (priceBottom - priceTop); }
        addChartGrid(svg, margin.left, right, priceTop, priceBottom, minPrice, maxPrice, axisText);
        addChartSectionLabel(svg, interval + '분봉', margin.left, priceTop + 12);
        addChartSectionLabel(svg, '거래량 X-ray · CVD', margin.left, volumeTop + 12);

        var maxVolume = Math.max.apply(Math, rows.map(function (row) { return row.volume; }));
        var forceScale = pressureStrengthScale(rows, function (row) { return row.delta; }, function (row) { return row.volume; });
        var minCvd = Math.min.apply(Math, [0].concat(rows.map(function (row) { return row.cumulativeDelta; })));
        var maxCvd = Math.max.apply(Math, [0].concat(rows.map(function (row) { return row.cumulativeDelta; })));
        var cvdSpread = Math.max(maxCvd - minCvd, 1);
        function volumeY(value) { return volumeBottom - value / Math.max(maxVolume, 1) * (volumeBottom - volumePlotTop); }
        function cvdY(value) { return volumePlotTop + 3 + (maxCvd - value) / cvdSpread * (volumeBottom - volumePlotTop - 11); }

        function updateReadout(row) {
            readout.textContent = formatHistoryDate(day.date) + ' ' + row.time + (row.endTime !== row.time ? '–' + row.endTime : '')
                + ' · 종가 ' + priceText(row.close)
                + ' · 고가 ' + priceText(row.high)
                + ' · 저가 ' + priceText(row.low)
                + ' · 거래량 ' + formatNumber(row.volume, 0) + '주'
                + ' · 추정 순압력 ' + formatPressurePercent(row.delta, row.volume)
                + ' · CVD ' + formatSigned(row.cumulativeDelta, '주', 0);
        }

        var cvdPath = '';
        rows.forEach(function (row, index) {
            var x = xFor(index);
            var tone = row.close > row.open ? 'is-up' : row.close < row.open ? 'is-down' : 'is-flat';
            var group = makeSvg('g', { 'class': 'kodex-history-candle-group ' + tone, tabindex: '0', role: 'img' });
            group.appendChild(makeSvg('line', { x1: x, y1: priceY(row.high), x2: x, y2: priceY(row.low), 'class': 'kodex-history-wick' }));
            group.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: Math.min(priceY(row.open), priceY(row.close)),
                width: candleWidth,
                height: Math.max(1.8, Math.abs(priceY(row.open) - priceY(row.close))),
                rx: 0.8,
                'class': 'kodex-history-candle'
            }));
            bindLinkedChartBar(svg, group, index, row, updateReadout);
            group.setAttribute('aria-label', row.time + ', 종가 ' + priceText(row.close) + ', 추정 순압력 ' + formatSigned(row.delta, '주', 0));
            svg.appendChild(group);
            var volumeGroup = makeSvg('g', { 'class': 'kodex-history-volume-group', tabindex: '0', role: 'img' });
            volumeGroup.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: volumeY(row.volume),
                width: candleWidth,
                height: Math.max(1, volumeBottom - volumeY(row.volume)),
                rx: 0.7,
                'class': 'kodex-history-volume is-xray-base'
            }));
            var totalHeight = Math.max(1, volumeBottom - volumeY(row.volume));
            var forceHeight = Math.max(1.5, totalHeight * pressureFillRatio(row.delta, row.volume, forceScale));
            volumeGroup.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: volumeBottom - forceHeight,
                width: candleWidth,
                height: forceHeight,
                rx: 0.7,
                'class': 'kodex-history-volume-force ' + (row.delta >= 0 ? 'is-buy' : 'is-sell')
            }));
            bindLinkedChartBar(svg, volumeGroup, index, row, updateReadout);
            volumeGroup.setAttribute('aria-label', row.time + ', 거래량 ' + formatNumber(row.volume, 0) + '주, 추정 순압력 ' + formatPressurePercent(row.delta, row.volume));
            svg.appendChild(volumeGroup);
            cvdPath += (cvdPath ? ' L ' : 'M ') + x.toFixed(2) + ' ' + cvdY(row.cumulativeDelta).toFixed(2);
        });
        if (cvdPath) svg.appendChild(makeSvg('path', { d: cvdPath, 'class': 'kodex-history-cvd' }));

        var tickIndexes = [0, Math.floor((rows.length - 1) / 4), Math.floor((rows.length - 1) / 2), Math.floor((rows.length - 1) * 3 / 4), rows.length - 1]
            .filter(function (value, index, values) { return values.indexOf(value) === index; });
        tickIndexes.forEach(function (index) {
            var tick = makeSvg('text', {
                x: xFor(index), y: 572, 'class': 'kodex-history-date-label',
                'text-anchor': index === 0 ? 'start' : index === rows.length - 1 ? 'end' : 'middle'
            });
            tick.textContent = rows[index].time;
            svg.appendChild(tick);
        });

        registerLinkedChartHitZones(svg, rows, updateReadout, {
            mode: 'intraday',
            left: margin.left,
            right: right,
            top: priceTop,
            bottom: volumeBottom,
            ariaLabel: function (row) { return formatHistoryDate(day.date) + ' ' + row.time; }
        });

        var latest = rows[rows.length - 1];
        updateReadout(latest);
        var totalVolume = rows.reduce(function (total, row) { return total + row.volume; }, 0);
        var totalDelta = rows.reduce(function (total, row) { return total + row.delta; }, 0);
        appendKodexMetric(summary, '거래일', formatHistoryDate(day.date));
        appendKodexMetric(summary, '봉 간격', interval + '분');
        appendKodexMetric(summary, '장중 수익률', formatSigned((latest.close / rows[0].open - 1) * 100, '%', 2));
        appendKodexMetric(summary, '거래량', formatCompactVolume(totalVolume));
        appendKodexMetric(summary, '추정 순압력', formatPressurePercent(totalDelta, totalVolume));
        appendKodexMetric(summary, '종료 CVD', formatSigned(latest.cumulativeDelta, '주', 0));
    }

    function renderKodexIntradayChart(instrument, svg, summary, readout, indexRows) {
        var liveInstrument = instrument && instrument.liveSnapshot || {};
        var liveDay = liveInstrument.liveIntradayDay || instrument && instrument.liveIntradayDay || null;
        var indexUrl = liveInstrument.intradayIndexUrl || instrument && instrument.intradayIndexUrl
            || (kodexIntradaySource ? new URL(kodexIntradaySource, window.location.href).href : '');
        var selectedIsLive = liveDay && liveDay.date === selectedKodexIntradayDate;
        if (!indexRows.length || !selectedKodexIntradayDate || (!selectedIsLive && !indexUrl)
            || !window.MarketDashboardLive || typeof window.MarketDashboardLive.fetchKodexIntradayDay !== 'function') {
            readout.textContent = '보존된 분봉 거래일을 불러오지 못했습니다.';
            var empty = makeSvg('text', { x: 500, y: 300, 'class': 'kodex-history-empty', 'text-anchor': 'middle' });
            empty.textContent = '분봉 데이터를 확인하고 있습니다.';
            svg.appendChild(empty);
            return;
        }
        var token = ++kodexIntradayRenderToken;
        readout.textContent = formatHistoryDate(selectedKodexIntradayDate) + ' 분봉과 추정 순압력을 불러오는 중입니다.';
        var dayRequest = selectedIsLive
            ? Promise.resolve(liveDay)
            : window.MarketDashboardLive.fetchKodexIntradayDay(
                indexUrl,
                selectedKodexIntradayDate,
                window.fetch.bind(window),
                { indexRows: indexRows }
            );
        dayRequest.then(function (day) {
            if (token !== kodexIntradayRenderToken || selectedKodexChartMode !== 'intraday') return;
            clear(svg);
            clear(summary);
            renderKodexIntradayRows(day, selectedKodexIntradayInterval, svg, summary, readout);
        }).catch(function () {
            if (token !== kodexIntradayRenderToken) return;
            readout.textContent = '선택한 거래일의 분봉을 불러오지 못했습니다.';
            clear(svg);
            var empty = makeSvg('text', { x: 500, y: 300, 'class': 'kodex-history-empty', 'text-anchor': 'middle' });
            empty.textContent = '다른 거래일을 선택해 다시 확인해 주세요.';
            svg.appendChild(empty);
        });
    }

    function renderKodexHistoryChart(instrument) {
        var svg = document.getElementById('kodex-history-chart');
        var summary = document.getElementById('kodex-history-summary');
        var readout = document.getElementById('kodex-history-readout');
        if (!svg || !summary || !readout) return;
        clear(svg);
        clear(summary);
        var indexRows = setKodexChartControls(instrument);
        var title = document.getElementById('kodex-history-title');
        var eyebrow = document.getElementById('kodex-history-eyebrow');
        svg.classList.toggle('is-intraday', selectedKodexChartMode === 'intraday');
        if (title) title.textContent = selectedKodexChartMode === 'daily'
            ? 'KODEX 레버리지 ' + (selectedKodexPeriod === '1m' ? '1개월' : '3개월') + ' 가격 흐름'
            : 'KODEX 레버리지 분봉 거래량 X-ray';
        if (eyebrow) eyebrow.textContent = selectedKodexChartMode === 'daily'
            ? '일봉·거래량 X-ray·CVD'
            : '분봉·거래량 X-ray·CVD';
        if (selectedKodexChartMode === 'intraday') {
            renderKodexIntradayChart(instrument, svg, summary, readout, indexRows);
            return;
        }
        kodexIntradayRenderToken += 1;
        renderKodexDailyChart(instrument, svg, summary, readout);
    }

    function formatUsdPrice(value) {
        return Number.isFinite(value) ? '$' + formatNumber(value, 2) : '데이터 없음';
    }

    function estimateDailyVolumePressure(row) {
        var range = row.high - row.low;
        var closeLocation = range > 0
            ? ((row.close - row.low) - (row.high - row.close)) / range
            : row.close > row.open ? 1 : row.close < row.open ? -1 : 0;
        closeLocation = Math.max(-1, Math.min(1, closeLocation));
        var delta = Math.round(row.volume * closeLocation);
        return {
            delta: delta,
            imbalance: closeLocation * 100,
            estimatedBuyVolume: Math.round((row.volume + delta) / 2),
            estimatedSellVolume: Math.round((row.volume - delta) / 2),
            volume: row.volume,
            cvd: 0
        };
    }

    function renderTqqqHistoryChart(rawHistory) {
        var svg = document.getElementById('tqqq-history-chart');
        var summary = document.getElementById('tqqq-history-summary');
        var readout = document.getElementById('tqqq-history-readout');
        if (!svg || !summary || !readout) return;
        clear(svg);
        clear(summary);
        svg.classList.remove('is-intraday');
        var title = document.getElementById('tqqq-history-title');
        var eyebrow = document.getElementById('tqqq-history-eyebrow');
        var method = document.getElementById('tqqq-history-method');
        var sourceNote = document.getElementById('tqqq-history-source-note');
        if (title) title.textContent = 'TQQQ ' + (selectedKodexPeriod === '1m' ? '1개월' : '3개월') + ' 가격 흐름';
        if (eyebrow) eyebrow.textContent = '미국 정규장 일봉·거래량 X-ray·CVD';
        if (method) method.textContent = '막대 높이는 거래량, 빨강·파랑 채움은 일봉 가격 범위와 종가 위치로 추정한 매수·매도 우위입니다.';
        if (sourceNote) sourceNote.textContent = '미국 정규장 일봉 기준이며, 순압력은 체결 Bid/Ask가 아닌 일중 가격 범위와 종가 위치를 거래량에 반영한 추정치입니다.';
        Array.prototype.forEach.call(document.querySelectorAll('[data-tqqq-daily-legend]'), function (node) { node.hidden = false; });
        var history = (rawHistory || []).filter(function (row) {
            return row && Number.isFinite(parseHistoryDate(row.date))
                && [row.open, row.high, row.low, row.close, row.volume].every(Number.isFinite);
        }).sort(function (left, right) {
            return parseHistoryDate(left.date) - parseHistoryDate(right.date);
        });

        if (history.length < 5) {
            readout.textContent = 'TQQQ 3개월 일봉과 거래량을 확인하고 있습니다.';
            var empty = makeSvg('text', { x: 400, y: 230, 'class': 'kodex-history-empty', 'text-anchor': 'middle' });
            empty.textContent = 'TQQQ 일봉 데이터를 불러오는 중입니다.';
            svg.appendChild(empty);
            return;
        }

        var latestTimestamp = parseHistoryDate(history[history.length - 1].date);
        var threshold = new Date(latestTimestamp);
        threshold.setMonth(threshold.getMonth() - (selectedKodexPeriod === '1m' ? 1 : 3));
        var startIndex = history.findIndex(function (row) { return parseHistoryDate(row.date) >= threshold.getTime(); });
        if (startIndex < 0) startIndex = 0;
        var rows = history.slice(startIndex);
        var ma5 = simpleMovingAverage(history, 5);
        var ma20 = simpleMovingAverage(history, 20);
        var ma60 = simpleMovingAverage(history, 60);

        svg.setAttribute('viewBox', '0 0 800 460');
        svg.classList.remove('is-intraday');
        var width = 800;
        var margin = { left: 24, right: 78 };
        var right = width - margin.right;
        var priceTop = 30;
        var priceBottom = 258;
        var volumeTop = 290;
        var volumePlotTop = volumeTop + 30;
        var volumeBottom = 412;
        var xStep = (right - margin.left) / rows.length;
        var candleWidth = Math.max(2.5, Math.min(8, xStep * 0.58));
        function xFor(index) { return margin.left + xStep * index + xStep / 2; }

        var values = [];
        rows.forEach(function (row) { values.push(row.high, row.low); });
        [ma5, ma20, ma60].forEach(function (series) {
            series.slice(startIndex).forEach(function (value) {
                if (Number.isFinite(value)) values.push(value);
            });
        });
        var minPrice = Math.min.apply(Math, values);
        var maxPrice = Math.max.apply(Math, values);
        var spread = Math.max(maxPrice - minPrice, Math.abs(maxPrice || 1) * 0.01);
        minPrice -= spread * 0.05;
        maxPrice += spread * 0.05;
        function priceY(value) { return priceTop + (maxPrice - value) / (maxPrice - minPrice) * (priceBottom - priceTop); }
        addChartGrid(svg, margin.left, right, priceTop, priceBottom, minPrice, maxPrice, formatUsdPrice);
        addChartSectionLabel(svg, '일봉', margin.left, priceTop + 12);
        addChartSectionLabel(svg, '거래량 X-ray · CVD', margin.left, volumeTop + 12);

        var maxVolume = Math.max.apply(Math, rows.map(function (row) { return row.volume; }));
        function volumeY(value) { return volumeBottom - value / Math.max(maxVolume, 1) * (volumeBottom - volumePlotTop); }
        var runningCvd = 0;
        var dailyPressure = rows.map(function (row) {
            var pressure = estimateDailyVolumePressure(row);
            runningCvd += pressure.delta;
            pressure.cvd = runningCvd;
            return pressure;
        });
        var forceScale = pressureStrengthScale(dailyPressure, function (row) { return row.delta; }, function (row) { return row.volume; });
        var cvdValues = dailyPressure.map(function (row) { return row.cvd; });
        var minCvd = Math.min.apply(Math, [0].concat(cvdValues));
        var maxCvd = Math.max.apply(Math, [0].concat(cvdValues));
        var cvdSpread = Math.max(maxCvd - minCvd, 1);
        function cvdY(value) { return volumePlotTop + 3 + (maxCvd - value) / cvdSpread * (volumeBottom - volumePlotTop - 10); }
        function updateReadout(row) {
            var rowIndex = rows.indexOf(row);
            var pressure = dailyPressure[rowIndex];
            readout.textContent = formatHistoryDate(row.date)
                + ' · 종가 ' + formatUsdPrice(row.close)
                + ' · 시가 ' + formatUsdPrice(row.open)
                + ' · 고가 ' + formatUsdPrice(row.high)
                + ' · 저가 ' + formatUsdPrice(row.low)
                + ' · 거래량 ' + formatCompactVolume(row.volume)
                + ' · 추정 순압력 ' + formatSigned(pressure.imbalance, '%', 2)
                + ' · CVD ' + formatSigned(pressure.cvd, '주', 0);
        }

        rows.forEach(function (row, index) {
            var x = xFor(index);
            var tone = row.close > row.open ? 'is-up' : row.close < row.open ? 'is-down' : 'is-flat';
            var group = makeSvg('g', { 'class': 'kodex-history-candle-group ' + tone, tabindex: '0', role: 'img' });
            group.appendChild(makeSvg('line', { x1: x, y1: priceY(row.high), x2: x, y2: priceY(row.low), 'class': 'kodex-history-wick' }));
            group.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: Math.min(priceY(row.open), priceY(row.close)),
                width: candleWidth,
                height: Math.max(1.8, Math.abs(priceY(row.open) - priceY(row.close))),
                rx: 0.8,
                'class': 'kodex-history-candle'
            }));
            bindLinkedChartBar(svg, group, index, row, updateReadout);
            var pressure = dailyPressure[index];
            group.setAttribute('aria-label', formatHistoryDate(row.date) + ', 종가 ' + formatUsdPrice(row.close)
                + ', 추정 순압력 ' + formatSigned(pressure.imbalance, '%', 2));
            svg.appendChild(group);

            var volumeGroup = makeSvg('g', { 'class': 'kodex-history-volume-group', tabindex: '0', role: 'img' });
            volumeGroup.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: volumeY(row.volume),
                width: candleWidth,
                height: Math.max(1, volumeBottom - volumeY(row.volume)),
                rx: 0.7,
                'class': 'kodex-history-volume is-xray-base'
            }));
            var totalHeight = Math.max(1, volumeBottom - volumeY(row.volume));
            var forceHeight = Math.max(1.5, totalHeight * pressureFillRatio(pressure.delta, row.volume, forceScale));
            volumeGroup.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: volumeBottom - forceHeight,
                width: candleWidth,
                height: forceHeight,
                rx: 0.7,
                'class': 'kodex-history-volume-force ' + (pressure.delta >= 0 ? 'is-buy' : 'is-sell')
            }));
            bindLinkedChartBar(svg, volumeGroup, index, row, updateReadout);
            volumeGroup.setAttribute('aria-label', formatHistoryDate(row.date) + ', 거래량 ' + formatCompactVolume(row.volume)
                + ', 추정 순압력 ' + formatSigned(pressure.imbalance, '%', 2));
            svg.appendChild(volumeGroup);
        });

        var cvdPath = '';
        dailyPressure.forEach(function (pressure, index) {
            cvdPath += (cvdPath ? ' L ' : 'M ') + xFor(index).toFixed(2) + ' ' + cvdY(pressure.cvd).toFixed(2);
        });
        if (cvdPath) svg.appendChild(makeSvg('path', { d: cvdPath, 'class': 'kodex-history-cvd' }));

        [
            { values: ma5, className: 'is-ma5' },
            { values: ma20, className: 'is-ma20' },
            { values: ma60, className: 'is-ma60' }
        ].forEach(function (line) {
            var path = '';
            line.values.slice(startIndex).forEach(function (value, index) {
                if (!Number.isFinite(value)) return;
                path += (path ? ' L ' : 'M ') + xFor(index).toFixed(2) + ' ' + priceY(value).toFixed(2);
            });
            if (path) svg.appendChild(makeSvg('path', { d: path, 'class': 'kodex-history-line ' + line.className }));
        });

        var tickIndexes = [0, Math.floor((rows.length - 1) / 2), rows.length - 1]
            .filter(function (value, index, valuesForTick) { return valuesForTick.indexOf(value) === index; });
        tickIndexes.forEach(function (index) {
            var tick = makeSvg('text', {
                x: xFor(index), y: 444, 'class': 'kodex-history-date-label',
                'text-anchor': index === 0 ? 'start' : index === rows.length - 1 ? 'end' : 'middle'
            });
            tick.textContent = formatHistoryDate(rows[index].date);
            svg.appendChild(tick);
        });

        registerLinkedChartHitZones(svg, rows, updateReadout, {
            mode: 'daily',
            left: margin.left,
            right: right,
            top: priceTop,
            bottom: volumeBottom,
            ariaLabel: function (row) { return formatHistoryDate(row.date); }
        });

        var latest = rows[rows.length - 1];
        updateReadout(latest);
        appendKodexMetric(summary, '최근 종가', formatUsdPrice(latest.close));
        appendKodexMetric(summary, '기간 수익률', formatSigned((latest.close / rows[0].open - 1) * 100, '%', 2));
        appendKodexMetric(summary, '최근 거래량', formatCompactVolume(latest.volume));
        appendKodexMetric(summary, '종료 CVD', formatSigned(dailyPressure[dailyPressure.length - 1].cvd, '주', 0));
        appendKodexMetric(summary, '기준일', formatHistoryDate(latest.date));
    }

    function matchingTqqqIntradayDay(rows, selectedDate, exactOnly) {
        var sorted = (rows || []).slice().sort(function (left, right) {
            return parseHistoryDate(left.date) - parseHistoryDate(right.date);
        });
        var exact = sorted.filter(function (day) { return day.date === selectedDate; })[0];
        if (exact) return exact;
        if (exactOnly) return null;
        var earlier = sorted.filter(function (day) {
            return parseHistoryDate(day.date) <= parseHistoryDate(selectedDate);
        });
        return earlier[earlier.length - 1] || null;
    }

    function renderTqqqIntradayChart(intradayHistory) {
        var svg = document.getElementById('tqqq-history-chart');
        var summary = document.getElementById('tqqq-history-summary');
        var readout = document.getElementById('tqqq-history-readout');
        if (!svg || !summary || !readout) return;
        clear(svg);
        clear(summary);
        svg.classList.add('is-intraday');
        Array.prototype.forEach.call(document.querySelectorAll('[data-tqqq-daily-legend]'), function (node) { node.hidden = true; });
        var oneMinuteRows = intradayHistory && intradayHistory.oneMinute || [];
        var fiveMinuteRows = intradayHistory && intradayHistory.fiveMinute || [];
        var preferredRows = selectedKodexIntradayInterval === 1 ? oneMinuteRows : fiveMinuteRows;
        var alternateRows = selectedKodexIntradayInterval === 1 ? fiveMinuteRows : oneMinuteRows;
        var day = matchingTqqqIntradayDay(preferredRows, selectedKodexIntradayDate, true)
            || matchingTqqqIntradayDay(alternateRows, selectedKodexIntradayDate, true)
            || matchingTqqqIntradayDay(preferredRows, selectedKodexIntradayDate, false)
            || matchingTqqqIntradayDay(alternateRows, selectedKodexIntradayDate, false);
        var title = document.getElementById('tqqq-history-title');
        var eyebrow = document.getElementById('tqqq-history-eyebrow');
        var method = document.getElementById('tqqq-history-method');
        var sourceNote = document.getElementById('tqqq-history-source-note');
        if (!day) {
            if (title) title.textContent = 'TQQQ 분봉 가격 흐름';
            if (eyebrow) eyebrow.textContent = '미국 정규장 분봉·거래량 X-ray·CVD';
            readout.textContent = '선택 기준에 대응하는 TQQQ 분봉을 확인하고 있습니다.';
            var empty = makeSvg('text', { x: 500, y: 300, 'class': 'kodex-history-empty', 'text-anchor': 'middle' });
            empty.textContent = 'TQQQ 분봉 데이터를 불러오는 중입니다.';
            svg.appendChild(empty);
            return;
        }
        var sourceInterval = Number(day.interval) || 5;
        var effectiveInterval = Math.max(selectedKodexIntradayInterval, sourceInterval);
        if (title) title.textContent = 'TQQQ ' + effectiveInterval + '분봉 가격 흐름';
        if (eyebrow) eyebrow.textContent = '미국 정규장 분봉·거래량 X-ray·CVD';
        if (method) method.textContent = 'KODEX와 같은 선택 기준으로 TQQQ 가격·거래량·추정 순압력과 CVD를 비교합니다.';
        var sameDate = day.date === selectedKodexIntradayDate;
        if (sourceNote) sourceNote.textContent = sameDate
            ? formatHistoryDate(day.date) + ' 미국 정규장 ' + sourceInterval + '분 원자료를 사용했습니다.'
            : 'KODEX ' + formatHistoryDate(selectedKodexIntradayDate) + ' 선택에 대응하는 가장 최근 미국 정규장 '
                + formatHistoryDate(day.date) + ' 데이터를 표시합니다.';
        renderKodexIntradayRows(day, effectiveInterval, svg, summary, readout, {
            priceFormatter: formatUsdPrice,
            axisFormatter: function (value) { return '$' + formatNumber(value, 2); }
        });
        if (!sameDate) appendKodexMetric(summary, 'KODEX 비교일', formatHistoryDate(selectedKodexIntradayDate));
    }

    function renderTqqqSynchronized() {
        var daily = latestLiveData && latestLiveData.tqqqHistory
            || dashboardData && dashboardData.tqqqHistory
            || [];
        if (selectedKodexChartMode === 'intraday') {
            renderTqqqIntradayChart(latestLiveData && latestLiveData.tqqqIntraday || null);
            return;
        }
        renderTqqqHistoryChart(daily);
    }

    function renderKodex(data) {
        var instrument = findById(data.technical.instruments, 'KODEX');
        if (!instrument) return;

        var points = instrument.points || [];
        var currentPoint = points[points.length - 1];
        var liveInstrument = instrument.liveSnapshot || {};
        var current = Number.isFinite(liveInstrument.value)
            ? liveInstrument.value
            : currentPoint && Number.isFinite(currentPoint.value) ? currentPoint.value : NaN;
        var previousClose = Number.isFinite(liveInstrument.previousClose)
            ? liveInstrument.previousClose
            : pointValue(instrument, /전일/);
        var sessionPricesComplete = liveInstrument.sessionPricesComplete !== false;
        var open = sessionPricesComplete && Number.isFinite(liveInstrument.open)
            ? liveInstrument.open
            : sessionPricesComplete ? pointValue(instrument, /^시가/) : NaN;
        var high = sessionPricesComplete && Number.isFinite(liveInstrument.high)
            ? liveInstrument.high
            : sessionPricesComplete ? pointValue(instrument, /고가/) : NaN;
        var low = sessionPricesComplete && Number.isFinite(liveInstrument.low)
            ? liveInstrument.low
            : sessionPricesComplete ? pointValue(instrument, /저가/) : NaN;
        if (sessionPricesComplete && !Number.isFinite(low)) low = Math.min.apply(Math, points.map(function (point) { return point.value; }));
        if (sessionPricesComplete && !Number.isFinite(high)) high = Math.max.apply(Math, points.map(function (point) { return point.value; }));
        var changePercent = Number.isFinite(liveInstrument.changePercent)
            ? liveInstrument.changePercent
            : Number.isFinite(instrument.changePercent)
                ? instrument.changePercent
            : Number.isFinite(current) && Number.isFinite(previousClose) && previousClose !== 0
                ? (current / previousClose - 1) * 100
                : NaN;
        var range = high - low;
        var rangeAvailable = [current, open, high, low].every(Number.isFinite) && range > 0;
        var rangePosition = rangeAvailable
            ? Math.max(0, Math.min(100, (current - low) / range * 100))
            : 50;

        document.getElementById('kodex-current-price').textContent = formatPrice(current, '원');
        var changeNode = document.getElementById('kodex-change');
        changeNode.textContent = formatSigned(changePercent, '%', 2);
        changeNode.className = 'kodex-change ' + (changePercent > 0 ? 'is-positive' : changePercent < 0 ? 'is-negative' : 'is-flat');
        document.getElementById('kodex-as-of').textContent = (liveInstrument.asOfLabel || instrument.asOfLabel || data.asOfDisplay)
            + ' · ' + (liveInstrument.stateLabel || instrument.stateLabel || '최근 시세');

        var metrics = document.getElementById('kodex-metrics');
        clear(metrics);
        appendKodexMetric(metrics, '전일 종가', formatPrice(previousClose, '원'));
        appendKodexMetric(metrics, '시가', formatPrice(open, '원'));
        appendKodexMetric(metrics, '고가', formatPrice(high, '원'));
        appendKodexMetric(metrics, '저가', formatPrice(low, '원'));
        var volume = Number.isFinite(liveInstrument.volume) ? liveInstrument.volume : instrument.volume;
        var tradingValueLabel = liveInstrument.tradingValueLabel || instrument.tradingValueLabel;
        appendKodexMetric(metrics, '누적 거래량', Number.isFinite(volume) ? formatNumber(volume, 0) + '주' : '확인 중');
        appendKodexMetric(metrics, '누적 거래대금', tradingValueLabel || (sessionPricesComplete ? '확인 중' : '장 종료 후 미제공'));

        var rangeTrack = document.querySelector('.kodex-range-card .kodex-range-track');
        var rangeLabels = document.querySelector('.kodex-range-card .kodex-range-labels');
        if (rangeTrack) rangeTrack.hidden = !rangeAvailable;
        if (rangeLabels) rangeLabels.hidden = !rangeAvailable;
        document.getElementById('kodex-range-fill').style.width = rangePosition + '%';
        document.getElementById('kodex-range-marker').style.left = rangePosition + '%';
        document.getElementById('kodex-range-low').textContent = formatPrice(low, '원');
        document.getElementById('kodex-range-current').textContent = formatPrice(current, '원');
        document.getElementById('kodex-range-high').textContent = formatPrice(high, '원');
        document.getElementById('kodex-range-summary').textContent = rangeAvailable
            ? '당일 저가에서 고가까지의 범위 중 ' + formatNumber(rangePosition, 1) + '% 지점입니다. 시가 대비 '
                + formatSigned((current / open - 1) * 100, '%', 2) + '입니다.'
            : '장 종료 후 고가·저가가 표시되지 않는 시간에는 종가와 최근 수급을 우선 보여줍니다.';

        var returnGrid = document.getElementById('kodex-return-grid');
        clear(returnGrid);
        var returns = liveInstrument.periodReturns || instrument.periodReturns || {};
        [
            ['1개월', returns.oneMonth],
            ['3개월', returns.threeMonth],
            ['6개월', returns.sixMonth],
            ['1년', returns.oneYear]
        ].forEach(function (item) {
            if (!Number.isFinite(item[1])) return;
            appendKodexMetric(returnGrid, item[0], formatSigned(item[1], '%', 2));
        });
        returnGrid.hidden = !returnGrid.childElementCount;

        var etf = liveInstrument.etf || instrument.etf || {};
        var etfMeta = [etf.baseIndex, etf.issuer, etf.fee ? '총보수 ' + etf.fee : ''].filter(Boolean);
        document.getElementById('kodex-etf-meta').textContent = etfMeta.join(' · ');

        renderKodexHistoryChart(instrument);
        renderCompositeMomentumCard(instrument);
        renderTqqqSynchronized();

        var trends = liveInstrument.investorTrends || instrument.investorTrends || [];
        var trendBody = document.getElementById('kodex-investor-trends');
        clear(trendBody);
        if (!trends.length) {
            var emptyRow = make('tr');
            var emptyCell = make('td', '', '최근 거래일 수급을 확인하고 있습니다.');
            emptyCell.colSpan = 6;
            emptyRow.appendChild(emptyCell);
            trendBody.appendChild(emptyRow);
            document.getElementById('kodex-investor-date').textContent = '거래일별 순매매 수량';
        } else {
            trends.forEach(function (trend) {
                var row = make('tr');
                row.appendChild(make('td', '', formatTradingDate(trend.date)));
                row.appendChild(make('td', '', formatPrice(trend.close, '원')));
                row.appendChild(make('td', trend.foreign > 0 ? 'is-positive' : trend.foreign < 0 ? 'is-negative' : '', formatSigned(trend.foreign, '주')));
                row.appendChild(make('td', trend.institution > 0 ? 'is-positive' : trend.institution < 0 ? 'is-negative' : '', formatSigned(trend.institution, '주')));
                row.appendChild(make('td', trend.individual > 0 ? 'is-positive' : trend.individual < 0 ? 'is-negative' : '', formatSigned(trend.individual, '주')));
                row.appendChild(make('td', '', formatNumber(trend.volume, 0) + '주'));
                trendBody.appendChild(row);
            });
            document.getElementById('kodex-investor-date').textContent = formatTradingDate(trends[0].date) + '까지';
        }

        var level = (data.strategyLevels || []).filter(function (item) {
            return item.asset === 'KODEX 레버리지';
        })[0];
        var levelContainer = document.getElementById('kodex-reference-levels');
        clear(levelContainer);
        if (level) {
            appendKodexMetric(levelContainer, '지지', level.support);
            appendKodexMetric(levelContainer, '중심', level.pivot);
            appendKodexMetric(levelContainer, '저항', level.resistance);
        }
        document.getElementById('kodex-level-written-at').textContent = formatKstDateTime(data.generatedAt) + ' 작성 기준';

        var kospi = marketById(data, 'KOSPI');
        var foreign = flowByLabel(kospi, '외국인');
        var institution = flowByLabel(kospi, '기관');
        var program = kospi && kospi.program ? kospi.program : data.flows && data.flows.program;
        var context = document.getElementById('kodex-market-context');
        clear(context);
        appendKodexMetric(context, 'KOSPI', Number.isFinite(kospi && kospi.value)
            ? formatNumber(kospi.value, 2) + ' · ' + formatSigned(kospi.changePercent, '%', 2)
            : '데이터 없음');
        appendKodexMetric(context, '외국인 현물', foreign ? formatSigned(foreign.value, foreign.unit) : '데이터 없음');
        appendKodexMetric(context, '기관 현물', institution ? formatSigned(institution.value, institution.unit) : '데이터 없음');
        appendKodexMetric(context, '프로그램', program && Number.isFinite(program.total) ? formatSigned(program.total, program.unit) : '데이터 없음');

        var estimatedDays = (liveInstrument.priceHistory || instrument.priceHistory || []).filter(function (row) {
            return Boolean(validVolumePressure(row));
        }).length;
        var indexedDays = (liveInstrument.intradayIndex || instrument.intradayIndex || []).length;
        estimatedDays = Math.max(estimatedDays, indexedDays);
        document.getElementById('kodex-data-note').textContent = '가격·거래량은 ' + (liveInstrument.asOfLabel || instrument.asOfLabel || data.asOfDisplay)
            + ' 기준입니다. 최근 ' + estimatedDays + '거래일은 분봉 기반 순압력과 CVD를 볼 수 있습니다. 빨강·파랑은 체결별 Bid/Ask가 아니라 가격 변화와 거래량으로 추정한 매수·매도 우위입니다.';
    }

    function renderSources(data) {
        document.getElementById('dashboard-source-summary').textContent = data.sourceLabel;
        var links = document.getElementById('market-source-links');
        clear(links);
        data.sources.forEach(function (source) {
            var link = make('a', '', source.label);
            link.href = source.href;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            links.appendChild(link);
        });
    }

    function renderLatestArticle(data) {
        var link = document.getElementById('market-latest-article-link');
        if (!link || !data.latestArticle) return;
        link.href = data.latestArticle.href;
        link.setAttribute('aria-label', data.latestArticle.title + ' 읽기');
    }

    function validateData(data) {
        if (!data || data.schemaVersion !== 1) throw new Error('지원하지 않는 대시보드 데이터입니다.');
        if (!data.generatedAt || !Number.isFinite(Date.parse(data.generatedAt))) throw new Error('시황분석 작성 시각이 올바르지 않습니다.');
        if (!data.asOf || !Number.isFinite(Date.parse(data.asOf))) throw new Error('대시보드 기준 시각이 올바르지 않습니다.');
        if (!Array.isArray(data.markets) || data.markets.length < 2) throw new Error('시장 지수 데이터가 부족합니다.');
        if (!data.stance || data.stance.attack + data.stance.wait + data.stance.defense !== 100) throw new Error('대응 점수 합계가 올바르지 않습니다.');
        ['checkpoints', 'changes', 'factors', 'memory', 'scenarios', 'strategyLevels', 'events', 'checklist', 'sources'].forEach(function (key) {
            if (!Array.isArray(data[key]) || !data[key].length) throw new Error(key + ' 데이터가 부족합니다.');
        });
        if (!data.technical || !Array.isArray(data.technical.instruments) || !data.technical.instruments.length) {
            throw new Error('기술적 분석 데이터가 부족합니다.');
        }
        if (!data.latestArticle || !data.latestArticle.href || !data.latestArticle.title) {
            throw new Error('최신 시황 글 정보가 부족합니다.');
        }
        data.markets.forEach(function (market) {
            if (![market.value, market.open, market.high, market.low].every(function (value) { return typeof value === 'number' && Number.isFinite(value); })) {
                throw new Error(market.label + ' OHLC 데이터가 올바르지 않습니다.');
            }
            if (market.high < market.low || market.value < market.low || market.value > market.high || market.open < market.low || market.open > market.high) {
                throw new Error(market.label + ' 현재가가 장중 범위를 벗어났습니다.');
            }
        });
        data.technical.instruments.forEach(function (instrument) {
            if (!Array.isArray(instrument.points) || !instrument.points.length || !Array.isArray(instrument.levels) || !instrument.levels.length) {
                throw new Error(instrument.label + ' 기술적 분석 데이터가 부족합니다.');
            }
        });
        return data;
    }

    function render(data) {
        dashboardData = data;
        var stale = isStaleSnapshot(data);
        data.markets.forEach(function (market) {
            if (!market.asOf) market.asOf = kstTimestampFromLabel(market.asOfLabel, data.asOf);
        });
        data.technical.instruments.forEach(function (instrument) {
            var matchingMarket = findById(data.markets, instrument.id);
            var lastPoint = instrument.points[instrument.points.length - 1];
            if (!instrument.asOf) instrument.asOf = matchingMarket && matchingMarket.asOf
                ? matchingMarket.asOf
                : kstTimestampFromLabel(lastPoint && lastPoint.label, data.asOf);
            if (!instrument.asOfLabel) instrument.asOfLabel = matchingMarket && matchingMarket.asOfLabel
                ? matchingMarket.asOfLabel
                : formatKstDateTime(instrument.asOf);
        });
        renderMarketCards(data, stale);
        renderStance(data);
        renderCheckpoints(data);
        renderAnalysis(data);
        renderAllocation(data);
        renderScenarios(data);
        renderStrategyLevels(data);
        renderChecklist(data);
        renderEvents(data);
        renderTechnical(data);
        renderKospiHistoryChart(findById(data.markets, 'KOSPI'));
        renderKodex(data);
        renderSources(data);
        renderLatestArticle(data);
        renderLoadState(data, null, stale ? 'stale' : 'ready', false, false);
    }

    function findById(items, id) {
        return (items || []).filter(function (item) { return item.id === id; })[0];
    }

    function replaceMarketValues(market, liveMarket) {
        if (!market || !liveMarket) return false;
        if (Number.isFinite(Date.parse(market.asOf)) && Date.parse(liveMarket.asOf) < Date.parse(market.asOf)) return false;
        ['value', 'previousClose', 'open', 'high', 'low', 'changePercent', 'asOf', 'asOfLabel', 'shortTimeLabel', 'stateLabel', 'marketStatus', 'delayed', 'volume', 'tradingValue'].forEach(function (key) {
            market[key] = liveMarket[key];
        });
        if (Array.isArray(market.flows)) market.flows = liveMarket.flows;
        if (market.breadth) market.breadth = liveMarket.breadth;
        if (liveMarket.program) market.program = liveMarket.program;
        market.liveUpdated = true;
        return true;
    }

    function replaceTechnicalObservation(instrument, liveInstrument) {
        if (!instrument || !liveInstrument) return false;
        if (Number.isFinite(Date.parse(instrument.asOf)) && Date.parse(liveInstrument.asOf) < Date.parse(instrument.asOf)) return false;
        instrument.liveSnapshot = liveInstrument;
        if (liveInstrument.sessionPricesComplete !== false) {
            instrument.points = [
                { label: '전일 종가', value: liveInstrument.previousClose },
                { label: '시가', value: liveInstrument.open },
                { label: '고가', value: liveInstrument.high },
                { label: '저가', value: liveInstrument.low },
                { label: liveInstrument.shortTimeLabel, value: liveInstrument.value }
            ];
            instrument.levels.forEach(function (level) {
                if (level.label === '현재') level.value = liveInstrument.value;
            });
            instrument.asOf = liveInstrument.asOf;
            instrument.asOfLabel = liveInstrument.asOfLabel;
            instrument.liveUpdated = true;
            instrument.delayed = Boolean(liveInstrument.delayed);
            ['changePercent', 'marketStatus', 'stateLabel', 'volume', 'tradingValueLabel', 'periodReturns', 'etf', 'investorTrends', 'priceHistory'].forEach(function (key) {
                if (liveInstrument[key] !== undefined) instrument[key] = liveInstrument[key];
            });
        }
        return true;
    }

    function updateInstitutionCheckpoint(data, liveMarket) {
        var institution = (liveMarket.flows || []).filter(function (flow) {
            return flow.label === '기관';
        })[0];
        var checkpoint = (data.checkpoints || []).filter(function (item) {
            return item.label === '기관 현물';
        })[0];
        if (!institution || !checkpoint) return;
        checkpoint.value = formatSigned(institution.value, institution.unit);
        checkpoint.detail = liveMarket.marketStatus === 'CLOSE' ? '정규장 누적 순매매' : '장중 누적 순매매';
        checkpoint.tone = institution.value > 0 ? 'positive' : institution.value < 0 ? 'danger' : 'info';
    }

    function updateExchangeCheckpoint(data, exchange) {
        var checkpoint = (data.checkpoints || []).filter(function (item) {
            return item.label === '달러/원';
        })[0];
        if (!exchange || !checkpoint) return;
        checkpoint.value = formatNumber(exchange.value, 2) + '원';
        checkpoint.detail = exchange.shortTimeLabel + ' 하나은행 고시환율';
        checkpoint.tone = exchange.changePercent <= 0 ? 'positive' : 'warning';
    }

    function updateProgramCheckpoint(data, program, liveMarket) {
        var checkpoint = (data.checkpoints || []).filter(function (item) {
            return item.label === '외국인 선물' || item.label === '전체 프로그램';
        })[0];
        if (!program || !checkpoint || !Number.isFinite(program.total)) return;
        checkpoint.label = '전체 프로그램';
        checkpoint.value = formatSigned(program.total, program.unit);
        checkpoint.detail = liveMarket && liveMarket.marketStatus === 'CLOSE'
            ? '정규장 누적 프로그램 순매매'
            : '장중 누적 프로그램 순매매';
        checkpoint.tone = program.total > 0 ? 'positive' : program.total < 0 ? 'warning' : 'info';
    }

    function flowByLabel(market, label) {
        return (market && market.flows || []).filter(function (flow) {
            return flow.label === label;
        })[0];
    }

    function updateLiveChange(data, label, after, meaning) {
        var change = (data.changes || []).filter(function (item) {
            return item.label === label;
        })[0];
        if (!change) return;
        change.after = after;
        change.meaning = meaning;
    }

    function updateLiveFactor(data, label, metric, detail, tone) {
        var factor = (data.factors || []).filter(function (item) {
            return item.label === label;
        })[0];
        if (!factor) return;
        factor.metric = metric;
        factor.detail = detail;
        factor.tone = tone;
    }

    function flowMeaning(value, marketStatus) {
        var session = marketStatus === 'CLOSE' ? '정규장 누적' : '장중 누적';
        if (value > 0) return session + ' 순매수입니다.';
        if (value < 0) return session + ' 순매도입니다.';
        return session + ' 순매매가 보합입니다.';
    }

    function updateLiveAnalysisFacts(data, liveMarket, exchange) {
        if (!liveMarket) return;
        var foreign = flowByLabel(liveMarket, '외국인');
        var institution = flowByLabel(liveMarket, '기관');
        var personal = flowByLabel(liveMarket, '개인');
        var session = liveMarket.marketStatus === 'CLOSE' ? '정규장' : '장중';
        var direction = liveMarket.changePercent > 0 ? '상승' : liveMarket.changePercent < 0 ? '하락' : '보합';

        updateLiveChange(
            data,
            'KOSPI',
            liveMarket.asOfLabel + ' ' + formatSigned(liveMarket.changePercent, '%', 2),
            session + ' 기준 전일 대비 ' + formatSigned(liveMarket.changePercent, '%', 2) + ' ' + direction + '입니다.'
        );
        if (foreign) {
            updateLiveChange(data, '외국인 현물', formatSigned(foreign.value, foreign.unit), flowMeaning(foreign.value, liveMarket.marketStatus));
        }
        if (institution) {
            updateLiveChange(data, '기관 현물', formatSigned(institution.value, institution.unit), flowMeaning(institution.value, liveMarket.marketStatus));
        }

        if (institution && foreign && personal) {
            updateLiveFactor(
                data,
                '수급',
                '기관 ' + formatSigned(institution.value, institution.unit),
                '외국인 ' + formatSigned(foreign.value, foreign.unit) + ', 개인 ' + formatSigned(personal.value, personal.unit) + ' · ' + liveMarket.asOfLabel,
                institution.value > 0 ? 'positive' : institution.value < 0 ? 'warning' : 'info'
            );
        }

        if (liveMarket.breadth) {
            var directionalTotal = liveMarket.breadth.advance + liveMarket.breadth.decline;
            var advanceRatio = directionalTotal > 0 ? liveMarket.breadth.advance / directionalTotal * 100 : 0;
            updateLiveFactor(
                data,
                '시장 폭',
                '상승·하락 종목 중 ' + formatNumber(advanceRatio, 1) + '% 상승',
                '상승 ' + formatNumber(liveMarket.breadth.advance, 0) + '개, 보합 ' + formatNumber(liveMarket.breadth.flat, 0)
                    + '개, 하락 ' + formatNumber(liveMarket.breadth.decline, 0) + '개 · ' + liveMarket.asOfLabel,
                advanceRatio >= 60 ? 'positive' : advanceRatio <= 40 ? 'danger' : 'info'
            );
        }

        if (exchange) {
            updateLiveFactor(
                data,
                '매크로',
                '원/달러 ' + formatNumber(exchange.value, 2) + '원',
                exchange.asOfLabel + ' 하나은행 고시환율 · 전일 대비 ' + formatSigned(exchange.changePercent, '%', 2),
                exchange.changePercent <= 0 ? 'positive' : 'warning'
            );
        }
    }

    function newestById(previousItems, incomingItems, rejectedSources) {
        var byId = {};
        (previousItems || []).forEach(function (item) { byId[item.id] = item; });
        (incomingItems || []).forEach(function (item) {
            var previous = byId[item.id];
            if (previous && Number.isFinite(Date.parse(previous.asOf)) && Date.parse(item.asOf) < Date.parse(previous.asOf)) {
                rejectedSources.push(item.label || item.id);
                return;
            }
            if (previous && Array.isArray(previous.priceHistory) && !Array.isArray(item.priceHistory)) {
                item.priceHistory = previous.priceHistory;
            }
            if (previous && Array.isArray(previous.intradayIndex) && !Array.isArray(item.intradayIndex)) {
                item.intradayIndex = previous.intradayIndex;
                item.intradayIndexUrl = previous.intradayIndexUrl;
            }
            if (previous && previous.liveIntradayDay && !item.liveIntradayDay) {
                item.liveIntradayDay = previous.liveIntradayDay;
            }
            byId[item.id] = item;
        });
        return Object.keys(byId).map(function (id) { return byId[id]; });
    }

    function mergeLiveResponse(previous, incoming) {
        if (!previous) return incoming;
        var rejectedSources = [];
        var markets = newestById(previous.markets, incoming.markets, rejectedSources);
        var instruments = newestById(previous.instruments, incoming.instruments, rejectedSources);
        var exchange = incoming.exchange || previous.exchange || null;
        if (incoming.exchange && previous.exchange && Date.parse(incoming.exchange.asOf) < Date.parse(previous.exchange.asOf)) {
            rejectedSources.push(incoming.exchange.label);
            exchange = previous.exchange;
        }
        var primaryMarket = findById(markets, 'KOSPI') || markets[0];
        var statuses = markets.map(function (market) { return market.marketStatus; });
        var marketState = statuses.length && statuses.every(function (status) { return status === 'CLOSE'; })
            ? '한국 정규장 마감'
            : statuses.some(function (status) { return status === 'OPEN'; })
                ? '한국 정규장 장중'
                : '최근 거래일 시세';
        var missingSources = (incoming.missingSources || []).slice();
        var delayedSources = (incoming.delayedSources || []).concat(rejectedSources).filter(function (label, index, labels) {
            return labels.indexOf(label) === index;
        });
        var previousTqqqIntraday = previous.tqqqIntraday || {};
        var incomingTqqqIntraday = incoming.tqqqIntraday || {};
        return {
            asOf: primaryMarket.asOf,
            asOfDisplay: formatKstDateTime(primaryMarket.asOf),
            marketState: marketState,
            markets: markets,
            instruments: instruments,
            exchange: exchange,
            program: (findById(markets, 'KOSPI') || {}).program || incoming.program || previous.program || null,
            tqqqHistory: incoming.tqqqHistory || previous.tqqqHistory || [],
            tqqqIntraday: {
                oneMinute: Array.isArray(incomingTqqqIntraday.oneMinute) && incomingTqqqIntraday.oneMinute.length
                    ? incomingTqqqIntraday.oneMinute
                    : previousTqqqIntraday.oneMinute || [],
                fiveMinute: Array.isArray(incomingTqqqIntraday.fiveMinute) && incomingTqqqIntraday.fiveMinute.length
                    ? incomingTqqqIntraday.fiveMinute
                    : previousTqqqIntraday.fiveMinute || []
            },
            partial: Boolean(incoming.partial || rejectedSources.length),
            missingSources: missingSources,
            delayedSources: delayedSources,
            retrievedAt: incoming.retrievedAt,
            sourceLabel: incoming.sourceLabel
        };
    }

    function applyLiveMarketData(data, liveData, silent) {
        if (!liveData || !Array.isArray(liveData.markets) || !liveData.markets.length) return false;
        var applied = false;

        liveData.markets.forEach(function (liveMarket) {
            if (replaceMarketValues(findById(data.markets, liveMarket.id), liveMarket)) applied = true;
            if (replaceTechnicalObservation(findById(data.technical.instruments, liveMarket.id), liveMarket)) applied = true;
        });
        liveData.instruments.forEach(function (liveInstrument) {
            if (replaceTechnicalObservation(findById(data.technical.instruments, liveInstrument.id), liveInstrument)) applied = true;
        });

        var incomingKospi = findById(liveData.markets, 'KOSPI');
        var displayKospi = findById(data.markets, 'KOSPI');
        if (incomingKospi) {
            updateInstitutionCheckpoint(data, incomingKospi);
            updateProgramCheckpoint(data, incomingKospi.program || liveData.program, incomingKospi);
            updateLiveAnalysisFacts(data, incomingKospi, liveData.exchange);
            if (data.flows && incomingKospi.program) data.flows.program = incomingKospi.program;
            data.technical.note = incomingKospi.asOfLabel + ' 기준 당일 가격 범위와 지지·저항 기준선입니다.';
        }
        updateExchangeCheckpoint(data, liveData.exchange);

        renderMarketCards(data, false);
        renderCheckpoints(data);
        renderAnalysis(data, liveData);
        renderTechnical(data);
        renderKospiHistoryChart(displayKospi);
        renderKodex(data);
        var exchangeText = liveData.exchange
            ? ', 원/달러는 ' + liveData.exchange.asOfLabel + ' 기준입니다. '
            : ' 기준입니다. 원/달러는 ' + data.asOfDisplay + ' 기록입니다. ';
        document.getElementById('dashboard-source-summary').textContent = '국내 지수·현물 수급·시장 폭·프로그램은 '
            + displayKospi.asOfLabel + exchangeText
            + (liveData.partial ? '일부 항목은 화면에 표시된 마지막 확인 시각 기준입니다. ' : '')
            + '메모리·미 국채·전망은 '
            + formatKstDateTime(data.generatedAt) + ' 작성 당시 공개자료를 반영했습니다.';
        renderLoadState(data, liveData, liveData.partial ? 'partial' : 'ready', false, Boolean(silent));
        return applied;
    }

    function clearLiveRefreshTimer() {
        if (!liveRefreshTimer) return;
        window.clearTimeout(liveRefreshTimer);
        liveRefreshTimer = null;
    }

    function shouldPollLiveData(liveData) {
        if (!liveData) return true;
        var markets = liveData.markets || [];
        if (markets.some(function (market) {
            return market.marketStatus === 'OPEN' || market.marketStatus === 'PREOPEN';
        })) return true;
        return Boolean(liveData.partial && !markets.every(function (market) { return market.marketStatus === 'CLOSE'; }));
    }

    function scheduleLiveRefresh(data, retrySoon) {
        clearLiveRefreshTimer();
        if (document.hidden) return;
        var delay = retrySoon || shouldPollLiveData(latestLiveData) ? 60 * 1000 : 5 * 60 * 1000;
        liveRefreshTimer = window.setTimeout(function () {
            refreshLiveMarketData(data, { silent: true });
        }, delay);
    }

    function refreshLiveMarketData(data, options) {
        if (!liveMarketSource || !window.MarketDashboardLive) return Promise.resolve(false);
        var settings = options || {};
        if (liveRefreshPromise) {
            if (settings.force) {
                return liveRefreshPromise.then(function () {
                    return refreshLiveMarketData(data, settings);
                });
            }
            return liveRefreshPromise;
        }
        var controller = typeof AbortController === 'function' ? new AbortController() : null;
        var timeoutId = window.setTimeout(function () {
            if (controller) controller.abort();
        }, 9000);
        var absoluteBase = new URL(liveMarketSource, window.location.href).href;
        if (!settings.silent) renderLoadState(data, latestLiveData, 'loading', true, false);
        lastLiveRefreshAt = Date.now();

        liveRefreshPromise = window.MarketDashboardLive.fetchLatest(
            absoluteBase,
            window.fetch.bind(window),
            {
                signal: controller ? controller.signal : undefined,
                volumePressureUrl: kodexVolumeSource ? new URL(kodexVolumeSource, window.location.href).href : undefined,
                intradayIndexUrl: kodexIntradaySource ? new URL(kodexIntradaySource, window.location.href).href : undefined,
                forceRefresh: Boolean(settings.force)
            }
        ).then(function (liveData) {
            window.clearTimeout(timeoutId);
            latestLiveData = mergeLiveResponse(latestLiveData, liveData);
            var applied = applyLiveMarketData(data, latestLiveData, settings.silent);
            if (!applied) renderLoadState(data, latestLiveData, latestLiveData.partial ? 'partial' : 'ready', false, settings.silent);
            scheduleLiveRefresh(data);
            return applied;
        }).catch(function () {
            window.clearTimeout(timeoutId);
            renderLoadState(
                data,
                latestLiveData,
                latestLiveData ? 'partial' : isStaleSnapshot(data) ? 'stale' : 'partial',
                false,
                settings.silent
            );
            scheduleLiveRefresh(data, true);
            return false;
        }).then(function (result) {
            liveRefreshPromise = null;
            return result;
        });
        return liveRefreshPromise;
    }

    function loadKodexIntradayIndex(data) {
        if (!kodexIntradaySource || !window.MarketDashboardLive
            || typeof window.MarketDashboardLive.normalizeKodexIntradayIndex !== 'function') return Promise.resolve(false);
        var instrument = data && data.technical && findById(data.technical.instruments, 'KODEX');
        if (!instrument) return Promise.resolve(false);
        var absoluteUrl = new URL(kodexIntradaySource, window.location.href).href;
        return fetch(absoluteUrl + (absoluteUrl.indexOf('?') === -1 ? '?' : '&') + '_=' + Date.now(), {
            cache: 'no-store'
        }).then(function (response) {
            if (!response.ok) throw new Error('KODEX 분봉 색인을 불러오지 못했습니다.');
            return response.json();
        }).then(window.MarketDashboardLive.normalizeKodexIntradayIndex).then(function (rows) {
            instrument.intradayIndex = rows;
            instrument.intradayIndexUrl = absoluteUrl;
            renderKodex(data);
            return true;
        }).catch(function () {
            return false;
        });
    }

    function cacheBustedUrl(url) {
        var resolved = new URL(url, window.location.href);
        resolved.searchParams.set('_', String(Date.now()));
        return resolved.href;
    }

    function fetchJson(url) {
        return fetch(cacheBustedUrl(url), { cache: 'no-store' }).then(function (response) {
            if (!response.ok) throw new Error('시장 데이터를 불러오지 못했습니다.');
            return response.json().then(function (data) {
                return { data: data, responseUrl: response.url };
            });
        });
    }

    fetchJson(root.getAttribute('data-dashboard-source'))
        .then(function (result) {
            if (!result.data.snapshot) return result.data;
            return fetchJson(new URL(result.data.snapshot, result.responseUrl).href).then(function (snapshotResult) {
                return snapshotResult.data;
            });
        })
        .then(validateData)
        .then(function (data) {
            render(data);
            return Promise.all([refreshLiveMarketData(data), loadKodexIntradayIndex(data), loadKospiTechnicalHistory(false)]);
        })
        .catch(function () {
            clear(loadState);
            loadState.appendChild(document.createTextNode('시장 데이터를 불러오지 못했습니다. '));
            var archiveLink = make('a', '', '최근 시황 리서치 보기');
            archiveLink.href = '?view=analysis#research-archive';
            loadState.appendChild(archiveLink);
            loadState.setAttribute('data-state', 'error');
        });

    document.addEventListener('visibilitychange', function () {
        if (!dashboardData) return;
        if (document.hidden) {
            clearLiveRefreshTimer();
            return;
        }
        if (Date.now() - lastLiveRefreshAt >= 60 * 1000) refreshLiveMarketData(dashboardData, { silent: true });
        else scheduleLiveRefresh(dashboardData);
    });

    window.addEventListener('focus', function () {
        if (!dashboardData || Date.now() - lastLiveRefreshAt < 60 * 1000) return;
        refreshLiveMarketData(dashboardData, { silent: true });
    });
}());
