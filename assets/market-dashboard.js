(function () {
    'use strict';

    var root = document.querySelector('[data-dashboard-source]');
    if (!root) return;

    document.documentElement.classList.add('market-dashboard-enhanced');

    var validViews = ['analysis', 'strategy', 'technical', 'kodex'];
    var viewLinks = Array.prototype.slice.call(document.querySelectorAll('[data-market-view]'));
    var viewPanels = Array.prototype.slice.call(document.querySelectorAll('[data-view-panel]'));
    var loadState = document.getElementById('dashboard-load-state');
    var dashboardData = null;
    var liveMarketSource = root.getAttribute('data-live-market-source');
    var selectedInstrumentId = null;
    var latestLiveData = null;
    var liveRefreshTimer = null;
    var liveRefreshPromise = null;
    var lastLiveRefreshAt = 0;
    var selectedKodexPeriod = '3m';

    function clear(node) {
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
        return validViews.indexOf(requested) === -1 ? 'analysis' : requested;
    }

    function setView(view, historyMode) {
        var selected = validViews.indexOf(view) === -1 ? 'analysis' : view;

        root.classList.toggle('market-dashboard-page--kodex-focus', selected === 'kodex');

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
        document.getElementById('market-technical-interpretation').textContent = formatKstDateTime(dashboardData.generatedAt)
            + ' 작성 분석 · ' + instrument.interpretation;
        var technicalTime = instrument.asOfLabel || (dashboardData && dashboardData.asOfDisplay) || '작성 시점';
        var technicalState = instrument.delayed
            ? '마지막 확인 시세'
            : instrument.liveUpdated ? '최근 시세' : '시황분석 작성 당시 시세';
        document.getElementById('market-technical-note').textContent = technicalTime + ' ' + technicalState
            + '와 작성 당시 기준선을 비교합니다. 점의 좌우 순서는 실제 장중 경로를 뜻하지 않습니다.';

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
        document.getElementById('market-technical-note').textContent = data.technical.note;
        var switcher = document.getElementById('market-instrument-switch');
        var selectedInstrument = data.technical.instruments.filter(function (instrument) {
            return instrument.id === selectedInstrumentId;
        })[0] || data.technical.instruments[0];
        selectedInstrumentId = selectedInstrument.id;
        var expectedIds = data.technical.instruments.map(function (instrument) { return instrument.id; }).join('|');
        var currentIds = Array.prototype.map.call(switcher.querySelectorAll('button[data-instrument-id]'), function (button) {
            return button.getAttribute('data-instrument-id');
        }).join('|');
        if (expectedIds !== currentIds) {
            clear(switcher);
            data.technical.instruments.forEach(function (instrument) {
                var button = make('button', '', instrument.label);
                button.type = 'button';
                button.setAttribute('data-instrument-id', instrument.id);
                button.addEventListener('click', function () {
                    selectedInstrumentId = button.getAttribute('data-instrument-id');
                    Array.prototype.forEach.call(switcher.querySelectorAll('button'), function (candidate) {
                        candidate.setAttribute('aria-pressed', candidate === button ? 'true' : 'false');
                    });
                    renderTechnicalInstrument(findById(dashboardData.technical.instruments, selectedInstrumentId));
                });
                switcher.appendChild(button);
            });
        }
        Array.prototype.forEach.call(switcher.querySelectorAll('button[data-instrument-id]'), function (button) {
            button.setAttribute('aria-pressed', button.getAttribute('data-instrument-id') === selectedInstrumentId ? 'true' : 'false');
        });
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

    function formatCompactShares(value) {
        if (!Number.isFinite(value)) return '수급 미제공';
        var absolute = Math.abs(value);
        if (absolute >= 100000000) return formatSigned(value / 100000000, '억주', 2);
        if (absolute >= 10000) return formatSigned(value / 10000, '만주', 1);
        return formatSigned(value, '주', 0);
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

    function renderKodexHistoryChart(instrument) {
        var svg = document.getElementById('kodex-history-chart');
        var summary = document.getElementById('kodex-history-summary');
        var readout = document.getElementById('kodex-history-readout');
        if (!svg || !summary || !readout) return;
        clear(svg);
        clear(summary);

        var liveInstrument = instrument && instrument.liveSnapshot || {};
        var history = (liveInstrument.priceHistory || instrument && instrument.priceHistory || []).filter(function (row) {
            return row && Number.isFinite(parseHistoryDate(row.date))
                && [row.open, row.high, row.low, row.close, row.volume].every(Number.isFinite);
        }).sort(function (left, right) {
            return parseHistoryDate(left.date) - parseHistoryDate(right.date);
        });

        Array.prototype.forEach.call(document.querySelectorAll('[data-kodex-period]'), function (button) {
            button.setAttribute('aria-pressed', button.getAttribute('data-kodex-period') === selectedKodexPeriod ? 'true' : 'false');
            if (button.getAttribute('data-chart-bound') === 'true') return;
            button.setAttribute('data-chart-bound', 'true');
            button.addEventListener('click', function () {
                selectedKodexPeriod = button.getAttribute('data-kodex-period') === '1m' ? '1m' : '3m';
                var currentInstrument = dashboardData && findById(dashboardData.technical.instruments, 'KODEX');
                if (currentInstrument) renderKodexHistoryChart(currentInstrument);
            });
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

        var width = 1000;
        var margin = { left: 24, right: 88 };
        var innerWidth = width - margin.left - margin.right;
        var priceTop = 34;
        var priceBottom = 338;
        var volumeTop = 374;
        var volumeBottom = 454;
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

        for (var gridIndex = 0; gridIndex <= 4; gridIndex += 1) {
            var gridY = priceTop + (priceBottom - priceTop) * gridIndex / 4;
            svg.appendChild(makeSvg('line', {
                x1: margin.left,
                y1: gridY,
                x2: width - margin.right,
                y2: gridY,
                'class': 'kodex-history-grid'
            }));
            var gridPrice = maxPrice - (maxPrice - minPrice) * gridIndex / 4;
            var priceLabel = makeSvg('text', {
                x: width - margin.right + 10,
                y: gridY + 4,
                'class': 'kodex-history-axis-label'
            });
            priceLabel.textContent = formatNumber(gridPrice, 0);
            svg.appendChild(priceLabel);
        }

        [['일봉', priceTop + 12], ['거래량', volumeTop + 12]].forEach(function (item) {
            var label = makeSvg('text', { x: margin.left, y: item[1], 'class': 'kodex-history-section-label' });
            label.textContent = item[0];
            svg.appendChild(label);
        });

        var maxVolume = Math.max.apply(Math, rows.map(function (row) { return row.volume; }));
        function volumeY(value) {
            return volumeBottom - value / Math.max(maxVolume, 1) * (volumeBottom - volumeTop);
        }

        function updateReadout(row) {
            var parts = [
                formatHistoryDate(row.date),
                '종가 ' + formatPrice(row.close, '원'),
                '시가 ' + formatPrice(row.open, '원'),
                '고가 ' + formatPrice(row.high, '원'),
                '저가 ' + formatPrice(row.low, '원'),
                '거래량 ' + formatNumber(row.volume, 0) + '주'
            ];
            readout.textContent = parts.join(' · ');
        }

        rows.forEach(function (row, index) {
            var x = xFor(index);
            var rising = row.close > row.open;
            var falling = row.close < row.open;
            var tone = rising ? 'is-up' : falling ? 'is-down' : 'is-flat';
            var group = makeSvg('g', { 'class': 'kodex-history-candle-group ' + tone });
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
            group.addEventListener('pointerenter', function () { updateReadout(row); });
            var title = makeSvg('title');
            title.textContent = formatHistoryDate(row.date) + ' 종가 ' + formatPrice(row.close, '원');
            group.appendChild(title);
            svg.appendChild(group);

            svg.appendChild(makeSvg('rect', {
                x: x - candleWidth / 2,
                y: volumeY(row.volume),
                width: candleWidth,
                height: Math.max(1, volumeBottom - volumeY(row.volume)),
                rx: 0.7,
                'class': 'kodex-history-volume ' + tone
            }));
        });

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
                y: 488,
                'class': 'kodex-history-date-label',
                'text-anchor': index === 0 ? 'start' : index === rows.length - 1 ? 'end' : 'middle'
            });
            tick.textContent = formatHistoryDate(rows[index].date).replace('월 ', '/').replace('일', '');
            svg.appendChild(tick);
        });

        var latest = rows[rows.length - 1];
        updateReadout(latest);
        var periodReturn = rows[0].close ? (latest.close / rows[0].close - 1) * 100 : NaN;
        var periodVolume = rows.reduce(function (total, row) { return total + row.volume; }, 0);
        appendKodexMetric(summary, selectedKodexPeriod === '1m' ? '1개월 수익률' : '3개월 수익률', formatSigned(periodReturn, '%', 2));
        appendKodexMetric(summary, '기간 최고', formatPrice(Math.max.apply(Math, rows.map(function (row) { return row.high; })), '원'));
        appendKodexMetric(summary, '기간 최저', formatPrice(Math.min.apply(Math, rows.map(function (row) { return row.low; })), '원'));
        appendKodexMetric(summary, '누적 거래량', formatCompactShares(periodVolume));
        appendKodexMetric(summary, '일평균 거래량', formatCompactShares(periodVolume / rows.length));
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

        var rangeTrack = document.querySelector('#market-view-kodex .kodex-range-track');
        var rangeLabels = document.querySelector('#market-view-kodex .kodex-range-labels');
        rangeTrack.hidden = !rangeAvailable;
        rangeLabels.hidden = !rangeAvailable;
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

        document.getElementById('kodex-data-note').textContent = '가격·거래량은 ' + (liveInstrument.asOfLabel || instrument.asOfLabel || data.asOfDisplay)
            + ' 기준입니다. 투자자별 수치는 거래일별 순매매 수량이며 체결 주도 방향을 뜻하지 않습니다.';
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
        ['value', 'previousClose', 'open', 'high', 'low', 'changePercent', 'asOf', 'asOfLabel', 'shortTimeLabel', 'stateLabel', 'marketStatus', 'delayed'].forEach(function (key) {
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
        return {
            asOf: primaryMarket.asOf,
            asOfDisplay: formatKstDateTime(primaryMarket.asOf),
            marketState: marketState,
            markets: markets,
            instruments: instruments,
            exchange: exchange,
            program: (findById(markets, 'KOSPI') || {}).program || incoming.program || previous.program || null,
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
            data.technical.note = incomingKospi.asOfLabel + ' 기준 당일 OHLC·현재가와 리서치 기준선을 항목별로 비교합니다. 점의 좌우 순서는 실제 장중 경로를 뜻하지 않습니다.';
        }
        updateExchangeCheckpoint(data, liveData.exchange);

        renderMarketCards(data, false);
        renderCheckpoints(data);
        renderAnalysis(data, liveData);
        renderTechnical(data);
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
        if (liveRefreshPromise) return liveRefreshPromise;
        var settings = options || {};
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
            { signal: controller ? controller.signal : undefined }
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
            return refreshLiveMarketData(data);
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
