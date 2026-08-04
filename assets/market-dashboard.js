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
        var digits = unit === '원' ? 0 : 2;
        return formatNumber(value, digits) + (unit === '원' ? '원' : '');
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
        var timestamp = Date.parse(data.asOf);
        return !Number.isFinite(timestamp) || Date.now() - timestamp > 4 * 60 * 60 * 1000;
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
            name.appendChild(make('small', '', (stale ? '지난 스냅샷' : market.stateLabel) + ' · ' + market.asOfLabel));
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
            content.appendChild(make('strong', '', checkpoint.label));
            content.appendChild(make('span', toneClass(checkpoint.tone), checkpoint.value));
            content.appendChild(make('small', '', checkpoint.detail));
            item.appendChild(content);
            list.appendChild(item);
        });
    }

    function renderAnalysis(data) {
        document.getElementById('market-headline').textContent = data.headline;
        document.getElementById('market-summary').textContent = data.summary;

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

        var flowSummary = document.getElementById('market-flow-summary');
        clear(flowSummary);
        [
            ['차익 프로그램', formatSigned(data.flows.program.arbitrage, data.flows.program.unit)],
            ['비차익 프로그램', formatSigned(data.flows.program.nonArbitrage, data.flows.program.unit)],
            ['전체 프로그램', formatSigned(data.flows.program.total, data.flows.program.unit)],
            [
                '외국인 KOSPI200 선물' + (data.flows.futuresAsOfLabel ? ' · ' + data.flows.futuresAsOfLabel : ''),
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
        clear(switcher);
        data.technical.instruments.forEach(function (instrument, index) {
            var button = make('button', '', instrument.label);
            button.type = 'button';
            button.setAttribute('aria-pressed', index === 0 ? 'true' : 'false');
            button.addEventListener('click', function () {
                Array.prototype.forEach.call(switcher.querySelectorAll('button'), function (candidate) {
                    candidate.setAttribute('aria-pressed', candidate === button ? 'true' : 'false');
                });
                renderTechnicalInstrument(instrument);
            });
            switcher.appendChild(button);
        });
        renderTechnicalInstrument(data.technical.instruments[0]);
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
        renderSources(data);
        renderLatestArticle(data);
        loadState.textContent = (stale ? '마지막 업데이트 · ' : '') + data.asOfDisplay + ' · ' + data.marketState;
        loadState.setAttribute('data-state', stale ? 'stale' : 'ready');
    }

    function fetchJson(url) {
        return fetch(url, { cache: 'no-store' }).then(function (response) {
            if (!response.ok) throw new Error('시장 스냅샷을 불러오지 못했습니다.');
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
        .then(render)
        .catch(function () {
            clear(loadState);
            loadState.appendChild(document.createTextNode('시장 스냅샷을 불러오지 못했습니다. '));
            var archiveLink = make('a', '', '최근 시황 리서치 보기');
            archiveLink.href = '?view=analysis#research-archive';
            loadState.appendChild(archiveLink);
            loadState.setAttribute('data-state', 'error');
        });
}());
