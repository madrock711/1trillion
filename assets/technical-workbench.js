(function () {
    'use strict';
    var root = document.getElementById('technical-workbench');
    var engine = window.TechnicalAnalysisEngine;
    if (!root || !engine) return;
    var storageKey = 'hpmplab-technical-workbench-v1';
    var chart = document.getElementById('tw-chart');
    var defaults = {
        symbol: 'KODEX', mode: 'daily', timeframe: 'native', chartType: 'candles', scale: 'linear', window: '120',
        oscillator: 'rsi', overlays: { profile: true, avwap: true, supertrend: true, ema: false, patterns: false }
    };
    var fields = { close: '종가', rsi: 'RSI 14', macdHistogram: 'MACD 히스토그램', avwap: '앵커 VWAP', supertrend: '슈퍼트렌드' };
    var operators = { above: '초과', below: '미만', crossesAbove: '상향 돌파', crossesBelow: '하향 돌파' };
    var stored = readStorage();
    var state = validSettings(stored.settings);
    var templates = Array.isArray(stored.templates) ? stored.templates.slice(0, 20).filter(function (t) {
        return t && typeof t.name === 'string' && t.name.length <= 40 && t.settings;
    }) : [];
    var drawings = stored.drawings && typeof stored.drawings === 'object' && !Array.isArray(stored.drawings) ? stored.drawings : {};
    var anchors = stored.anchors && typeof stored.anchors === 'object' && !Array.isArray(stored.anchors) ? stored.anchors : {};
    var alerts = Array.isArray(stored.alerts) ? stored.alerts.slice(0, 40).filter(validAlert) : [];
    var alertRuntime = {};
    var replayKey = null;
    var replayInterval = null;
    var replayTimer = null;
    var selectedIndex = null;
    var pendingPoint = null;
    var activeRows = [];
    var rawRows = [];
    var renderedRows = [];
    var geometry = null;
    var frame = 0;
    var currentTool = 'inspect';

    function el(id) { return document.getElementById('tw-' + id); }
    function make(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }
    function svg(tag, attributes, text) {
        var node = document.createElementNS('http://www.w3.org/2000/svg', tag);
        Object.keys(attributes || {}).forEach(function (key) { node.setAttribute(key, attributes[key]); });
        if (text !== undefined) node.textContent = text;
        return node;
    }
    function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
    function keyOf(row) { return String(row.date || row.sessionDate || '') + (row.time ? ' ' + row.time : ''); }
    function contextKey() { return state.symbol + ':' + state.mode; }
    function drawingKey() { return contextKey() + ':' + state.timeframe; }
    function currentContext() { return (window.TechnicalAnalysisContexts || {})[contextKey()]; }
    function number(value, digits) {
        return Number.isFinite(value) ? new Intl.NumberFormat('ko-KR', { maximumFractionDigits: digits === undefined ? (state.symbol === 'TQQQ' ? 2 : 0) : digits }).format(value) : '—';
    }
    function readStorage() {
        try { return JSON.parse(window.localStorage.getItem(storageKey) || '{}') || {}; } catch (_) { return {}; }
    }
    function persist(statusId) {
        try {
            window.localStorage.setItem(storageKey, JSON.stringify({ settings: state, templates: templates, drawings: drawings, anchors: anchors, alerts: alerts }));
            return true;
        } catch (_) {
            el(statusId || 'template-status').textContent = '브라우저 저장 공간을 사용할 수 없습니다. 현재 화면에서만 유지됩니다.';
            return false;
        }
    }
    function oneOf(value, choices, fallback) { return choices.indexOf(value) !== -1 ? value : fallback; }
    function validSettings(input) {
        var s = input && typeof input === 'object' ? input : {};
        return {
            symbol: oneOf(s.symbol, ['KODEX', 'KOSPI', 'TQQQ'], 'KODEX'),
            mode: oneOf(s.mode, ['daily', 'intraday'], 'daily'),
            timeframe: oneOf(s.timeframe, ['native', 'weekly', 'monthly', '5', '15', '30', '60'], 'native'),
            chartType: oneOf(s.chartType, ['candles', 'heikin', 'line'], 'candles'),
            scale: oneOf(s.scale, ['linear', 'log'], 'linear'), window: oneOf(String(s.window), ['60', '120', '240', 'all'], '120'),
            oscillator: oneOf(s.oscillator, ['rsi', 'macd', 'none'], 'rsi'),
            overlays: Object.keys(defaults.overlays).reduce(function (o, key) {
                o[key] = s.overlays && typeof s.overlays[key] === 'boolean' ? s.overlays[key] : defaults.overlays[key]; return o;
            }, {})
        };
    }
    function validCondition(c) {
        return c && Object.prototype.hasOwnProperty.call(fields, c.field) && Object.prototype.hasOwnProperty.call(operators, c.operator)
            && typeof c.value === 'number' && Number.isFinite(c.value);
    }
    function validAlert(a) {
        return a && typeof a.id === 'string' && ['KODEX', 'KOSPI', 'TQQQ'].indexOf(a.symbol) !== -1
            && ['daily', 'intraday'].indexOf(a.mode) !== -1 && Number.isFinite(a.interval) && a.interval > 0
            && ['all', 'any'].indexOf(a.match) !== -1 && Array.isArray(a.conditions) && a.conditions.length > 0
            && a.conditions.length <= 5 && a.conditions.every(validCondition);
    }
    function schedule() {
        if (frame) return;
        frame = window.requestAnimationFrame(function () { frame = 0; render(); });
    }
    function timeframeChoices() {
        var ctx = currentContext();
        var nativeInterval = ctx && ctx.interval || 1;
        return state.mode === 'daily' ? ['native', 'weekly', 'monthly']
            : ['native'].concat(['5', '15', '30', '60'].filter(function (n) { return Number(n) > nativeInterval && Number(n) % nativeInterval === 0; }));
    }
    function timeframeLabel(tf, ctx) {
        if (tf === 'weekly') return '주봉';
        if (tf === 'monthly') return '월봉';
        if (tf === 'native') return state.mode === 'daily' ? '일봉' : (ctx && ctx.interval || 5) + '분봉';
        return tf + '분봉';
    }
    function syncControls() {
        el('symbol').value = state.symbol;
        el('mode').value = state.mode;
        var select = el('timeframe');
        var choices = timeframeChoices();
        if (choices.indexOf(state.timeframe) === -1) state.timeframe = 'native';
        clear(select);
        choices.forEach(function (choice) {
            var option = make('option', '', timeframeLabel(choice, currentContext())); option.value = choice; select.appendChild(option);
        });
        select.value = state.timeframe;
        el('chart-type').value = state.chartType;
        el('scale').value = state.scale;
        el('window').value = state.window;
        el('oscillator').value = state.oscillator;
        root.querySelectorAll('[data-tw-overlay]').forEach(function (input) { input.checked = state.overlays[input.dataset.twOverlay]; });
    }
    function nativeBars() {
        var ctx = currentContext();
        return engine.normalizeBars(ctx && ctx.bars || []);
    }
    function cutoff(rows) {
        if (replayKey === null) return rows;
        return rows.filter(function (row) { return keyOf(row) <= replayKey; });
    }
    function enriched(rows, tf, anchorKey) {
        var grouped = engine.aggregateBars(rows, tf);
        var index = anchorKey ? grouped.findIndex(function (row) { return keyOf(row) === anchorKey; }) : 0;
        var result = engine.indicators(grouped, { anchorIndex: Math.max(0, index) });
        if (anchorKey && index < 0) result.forEach(function (row) { row.avwap = row.avwapUpper = row.avwapLower = null; });
        return result;
    }
    function heikinAshi(rows) {
        var previous = null;
        return rows.map(function (r) {
            var close = (r.open + r.high + r.low + r.close) / 4;
            var open = previous ? (previous.open + previous.close) / 2 : (r.open + r.close) / 2;
            var result = Object.assign({}, r, { open: open, close: close, high: Math.max(r.high, open, close), low: Math.min(r.low, open, close) });
            previous = result; return result;
        });
    }
    function anchorOptions(rows) {
        var select = el('anchor');
        var selected = anchors[drawingKey()] || '';
        clear(select);
        var first = make('option', '', '첫 봉'); first.value = ''; select.appendChild(first);
        rows.forEach(function (row) { var option = make('option', '', keyOf(row)); option.value = keyOf(row); select.appendChild(option); });
        if (selected && !rows.some(function (row) { return keyOf(row) === selected; })) {
            var unavailable = make('option', '', selected + ' · 현재 범위 밖'); unavailable.value = selected; select.appendChild(unavailable);
        }
        select.value = selected;
    }
    function render() {
        syncControls();
        rawRows = nativeBars();
        var visibleRaw = cutoff(rawRows);
        activeRows = enriched(visibleRaw, state.timeframe, anchors[drawingKey()]);
        var limit = state.window === 'all' ? activeRows.length : Number(state.window);
        renderedRows = activeRows.slice(-limit);
        anchorOptions(engine.aggregateBars(rawRows, state.timeframe));
        clear(chart);
        var available = renderedRows.length > 0;
        el('export').disabled = !available;
        el('replay-start').disabled = rawRows.length < 2 || replayKey !== null;
        el('replay-play').disabled = !available || replayKey === null;
        el('replay-step').disabled = !available || replayKey === null || keyOf(rawRows[rawRows.length - 1]) <= replayKey;
        el('replay-end').disabled = replayKey === null;
        el('replay-range').disabled = !available || replayKey === null;
        el('replay-range').max = Math.max(1, rawRows.length);
        el('replay-range').value = visibleRaw.length || 1;
        el('replay-status').textContent = replayKey === null ? '전체 데이터 · ' + rawRows.length + '봉' : '재생 ' + visibleRaw.length + ' / ' + rawRows.length + ' · ' + replayKey;
        el('replay-start').parentNode.classList.toggle('is-active', replayKey !== null);
        var list = validDrawings();
        el('undo').disabled = !list.length && !pendingPoint;
        el('clear-drawings').disabled = !list.length && !pendingPoint;
        if (!available) {
            chart.appendChild(svg('text', { x: 550, y: 240, 'text-anchor': 'middle', 'class': 'tw-empty' }, '선택한 가격 데이터가 아직 없습니다.'));
            el('readout').textContent = state.symbol + ' ' + (state.mode === 'daily' ? '일봉' : '분봉') + '을 불러오는 중입니다. 아래 차트의 새로고침으로 다시 시도할 수 있습니다.';
            el('data-note').textContent = '가격이 없는 구간에는 지표와 매물대를 표시하지 않습니다.';
            clear(el('timeframes')); geometry = null; return;
        }
        drawChart();
        var row = renderedRows[Math.min(selectedIndex === null ? renderedRows.length - 1 : selectedIndex, renderedRows.length - 1)];
        showReadout(row);
        renderTimeframes(visibleRaw);
        var ctx = currentContext();
        el('data-note').textContent = state.symbol + ' · ' + timeframeLabel(state.timeframe, ctx) + ' · 마지막 원본 봉 ' + keyOf(visibleRaw[visibleRaw.length - 1])
            + ' · 매물대는 표시한 ' + renderedRows.length + '봉의 OHLCV 추정치이며 실제 가격별 체결량과 다를 수 있습니다.'
            + (state.chartType === 'heikin' ? ' 하이킨 아시는 변환 가격입니다. 지표·알림·내보내기는 원본 가격을 사용합니다.' : '')
            + (replayKey !== null ? ' 재생 시점까지의 봉으로 지표와 시간봉을 다시 계산합니다.' : '')
            + (ctx && ctx.mode === 'intraday' ? ' 거래소별 현지 거래일·봉 시각을 사용합니다.' : '');
        var missingVolume = renderedRows.filter(function (row) { return !Number.isFinite(row.volume); }).length;
        if (missingVolume) el('data-note').textContent += ' 거래량이 없는 ' + missingVolume + '봉은 매물대에서 제외합니다.';
        var anchor = anchors[drawingKey()];
        if (state.overlays.avwap && anchor && !activeRows.some(function (row) { return keyOf(row) === anchor; })) el('data-note').textContent += ' VWAP 시작점이 현재 이력에 없어 VWAP를 표시하지 않습니다.';
    }
    function pathFor(rows, field, x, y, predicate) {
        var path = ''; var pen = false;
        rows.forEach(function (row, i) {
            var value = row[field];
            if (!Number.isFinite(value) || predicate && !predicate(row)) { pen = false; return; }
            path += (pen ? ' L' : ' M') + x(i).toFixed(2) + ',' + y(value).toFixed(2); pen = true;
        });
        return path;
    }
    function linePath(rows, field, x, y, className, parent, predicate) {
        var path = pathFor(rows, field, x, y, predicate);
        if (path) (parent || chart).appendChild(svg('path', { d: path, 'class': className }));
    }
    function drawChart() {
        var rows = renderedRows;
        var transformed = state.chartType === 'heikin' ? heikinAshi(activeRows).slice(-rows.length) : rows;
        var left = 46, right = state.overlays.profile ? 836 : 1000, top = 25, bottom = 330;
        var values = [];
        transformed.forEach(function (r) { values.push(r.high, r.low); });
        rows.forEach(function (r) {
            ['avwap', 'avwapUpper', 'avwapLower', 'supertrend', 'ema20', 'ema50'].forEach(function (field) {
                var enabled = field.indexOf('avwap') === 0 ? state.overlays.avwap : field.indexOf('ema') === 0 ? state.overlays.ema : state.overlays.supertrend;
                if (enabled && Number.isFinite(r[field]) && r[field] > 0) values.push(r[field]);
            });
        });
        var min = Math.min.apply(Math, values), max = Math.max.apply(Math, values);
        var spread = Math.max(max - min, Math.abs(max) * .005, .01);
        min = Math.max(min - spread * .06, .000001); max += spread * .06;
        var log = state.scale === 'log' && min > 0;
        var lowAxis = log ? Math.log(min) : min, highAxis = log ? Math.log(max) : max;
        function y(v) { return top + (highAxis - (log ? Math.log(Math.max(v, .000001)) : v)) / (highAxis - lowAxis) * (bottom - top); }
        function inverseY(px) { var v = highAxis - (px - top) / (bottom - top) * (highAxis - lowAxis); return log ? Math.exp(v) : v; }
        var step = (right - left) / rows.length;
        function x(i) { return left + step * (i + .5); }
        geometry = { left: left, right: right, top: top, bottom: bottom, x: x, y: y, inverseY: inverseY, step: step };
        for (var tick = 0; tick <= 4; tick++) {
            var py = top + (bottom - top) * tick / 4;
            chart.appendChild(svg('line', { x1: left, x2: right, y1: py, y2: py, 'class': 'tw-grid' }));
            chart.appendChild(svg('text', { x: right + 8, y: py + 4, 'class': 'tw-axis' }, number(inverseY(py))));
        }
        var defs = svg('defs'); var clip = svg('clipPath', { id: 'tw-price-clip' });
        clip.appendChild(svg('rect', { x: left, y: top, width: right - left, height: bottom - top })); defs.appendChild(clip); chart.appendChild(defs);
        var plot = svg('g', { 'clip-path': 'url(#tw-price-clip)' }); chart.appendChild(plot);
        if (state.chartType === 'line') linePath(rows, 'close', x, y, 'tw-price-line', plot);
        else transformed.forEach(function (r, i) {
            var cls = r.close >= r.open ? 'tw-candle-up' : 'tw-candle-down';
            plot.appendChild(svg('line', { x1: x(i), x2: x(i), y1: y(r.high), y2: y(r.low), 'class': cls }));
            plot.appendChild(svg('rect', { x: x(i) - Math.max(1, Math.min(9, step * .65)) / 2, y: Math.min(y(r.open), y(r.close)), width: Math.max(1, Math.min(9, step * .65)), height: Math.max(1, Math.abs(y(r.open) - y(r.close))), 'class': cls }));
        });
        if (state.overlays.avwap) {
            linePath(rows, 'avwap', x, y, 'tw-vwap', plot);
            linePath(rows, 'avwapUpper', x, y, 'tw-vwap-band', plot);
            linePath(rows, 'avwapLower', x, y, 'tw-vwap-band', plot);
        }
        if (state.overlays.supertrend) {
            linePath(rows, 'supertrend', x, y, 'tw-super-up', plot, function (r) { return r.supertrendDirection === 'up'; });
            linePath(rows, 'supertrend', x, y, 'tw-super-down', plot, function (r) { return r.supertrendDirection === 'down'; });
        }
        if (state.overlays.ema) { linePath(rows, 'ema20', x, y, 'tw-ema20', plot); linePath(rows, 'ema50', x, y, 'tw-ema50', plot); }
        var profile = state.overlays.profile ? engine.volumeProfile(rows, { bins: 32, valueArea: .7 }) : null;
        if (profile && profile.totalVolume > 0 && Number.isFinite(profile.poc)) {
            var maxVol = Math.max.apply(Math, profile.bins.map(function (b) { return b.volume; }));
            profile.bins.forEach(function (b) {
                var width = b.volume / maxVol * 110;
                var cls = 'tw-profile' + (b.low <= profile.poc && b.high >= profile.poc ? ' is-poc' : b.low >= profile.val && b.high <= profile.vah ? ' is-value-area' : '');
                chart.appendChild(svg('rect', { x: 1084 - width, y: y(b.high), width: width, height: Math.max(1, y(b.low) - y(b.high)), 'class': cls }));
            });
            ['poc', 'vah', 'val'].forEach(function (name) {
                chart.appendChild(svg('line', { x1: left, x2: right, y1: y(profile[name]), y2: y(profile[name]), 'class': 'tw-level' }));
            });
            chart.appendChild(svg('text', { x: 974, y: 16, 'class': 'tw-axis' }, '매물대 · 추정'));
            chart.appendChild(svg('text', { x: left, y: 351 }, 'POC ' + number(profile.poc) + ' · VAH ' + number(profile.vah) + ' · VAL ' + number(profile.val)));
        } else if (state.overlays.profile) chart.appendChild(svg('text', { x: 974, y: 55 }, '거래량 없음'));
        var volumeMax = Math.max.apply(Math, [1].concat(rows.map(function (r) { return Number.isFinite(r.volume) ? r.volume : 0; })));
        rows.forEach(function (r, i) {
            if (!Number.isFinite(r.volume)) return;
            var h = r.volume / volumeMax * 44;
            chart.appendChild(svg('rect', { x: x(i) - step * .3, y: 415 - h, width: Math.max(1, step * .6), height: h, 'class': r.close >= r.open ? 'tw-candle-up' : 'tw-candle-down', opacity: .55 }));
        });
        chart.appendChild(svg('text', { x: left, y: 370 }, '거래량'));
        drawOscillator(rows, x, left, right);
        var indices = rows.length === 1 ? [0] : [0, Math.floor((rows.length - 1) / 2), rows.length - 1];
        indices.forEach(function (i) {
            chart.appendChild(svg('text', { x: x(i), y: 532, 'text-anchor': i === 0 ? 'start' : i === rows.length - 1 ? 'end' : 'middle', 'class': 'tw-axis' }, keyOf(rows[i])));
        });
        var legend = [];
        if (state.overlays.avwap) legend.push('VWAP ±1σ');
        if (state.overlays.supertrend) legend.push('슈퍼트렌드 10·3');
        if (state.overlays.ema) legend.push('EMA 20·50');
        chart.appendChild(svg('text', { x: left, y: 16, 'class': 'tw-axis' }, legend.join(' · ')));
        drawUserLines(plot, rows, x, y, left, right);
        if (state.overlays.patterns) drawPatterns(plot, rows, x, y);
        var hit = svg('rect', { x: left, y: top, width: right - left, height: bottom - top, 'class': 'tw-hit' });
        hit.addEventListener('pointermove', function (event) { inspectAt(event, false); });
        hit.addEventListener('click', function (event) { inspectAt(event, true); });
        chart.appendChild(hit);
        drawCrosshair(selectedIndex);
    }
    function drawOscillator(rows, x, left, right) {
        if (state.oscillator === 'none') return;
        var top = 451, bottom = 504;
        var isRsi = state.oscillator === 'rsi';
        var values = isRsi ? [0, 100] : [0].concat(rows.reduce(function (all, r) { return all.concat([r.macd, r.macdSignal, r.macdHistogram].filter(Number.isFinite)); }, []));
        var min = Math.min.apply(Math, values), max = Math.max.apply(Math, values);
        var spread = Math.max(max - min, .000001);
        function y(v) { return top + (max - v) / spread * (bottom - top); }
        chart.appendChild(svg('text', { x: left, y: 442 }, isRsi ? 'RSI 14' : 'MACD 12·26·9'));
        (isRsi ? [30, 70] : [0]).forEach(function (v) {
            chart.appendChild(svg('line', { x1: left, x2: right, y1: y(v), y2: y(v), 'class': 'tw-grid' }));
            chart.appendChild(svg('text', { x: right + 8, y: y(v) + 4 }, number(v, 2)));
        });
        if (isRsi) linePath(rows, 'rsi', x, y, 'tw-oscillator-line');
        else {
            rows.forEach(function (r, i) {
                if (!Number.isFinite(r.macdHistogram)) return;
                chart.appendChild(svg('rect', { x: x(i) - geometry.step * .3, y: Math.min(y(0), y(r.macdHistogram)), width: Math.max(1, geometry.step * .6), height: Math.max(1, Math.abs(y(0) - y(r.macdHistogram))), 'class': r.macdHistogram >= 0 ? 'tw-candle-up' : 'tw-candle-down', opacity: .65 }));
            });
            linePath(rows, 'macd', x, y, 'tw-oscillator-line'); linePath(rows, 'macdSignal', x, y, 'tw-vwap');
        }
    }
    function showReadout(row) {
        if (!row) return;
        var trend = row.supertrendDirection === 'up' ? '상승' : row.supertrendDirection === 'down' ? '하락' : '계산 대기';
        el('readout').textContent = keyOf(row) + ' · 시가 ' + number(row.open) + ' / 고가 ' + number(row.high) + ' / 저가 ' + number(row.low) + ' / 종가 ' + number(row.close)
            + ' · 거래량 ' + number(row.volume) + ' · RSI ' + number(row.rsi, 1) + ' · VWAP ' + number(row.avwap) + ' · 추세 ' + trend;
    }
    function drawCrosshair(index) {
        chart.querySelectorAll('[data-tw-crosshair]').forEach(function (node) { node.remove(); });
        if (index === null || !geometry || !renderedRows[index]) return;
        chart.appendChild(svg('line', { x1: geometry.x(index), x2: geometry.x(index), y1: geometry.top, y2: 508, 'class': 'tw-crosshair', 'data-tw-crosshair': 'true' }));
    }
    function inspectAt(event, commit) {
        if (!geometry) return;
        var point = chart.createSVGPoint(); point.x = event.clientX; point.y = event.clientY;
        var matrix = chart.getScreenCTM(); if (!matrix) return;
        point = point.matrixTransform(matrix.inverse());
        var index = Math.max(0, Math.min(renderedRows.length - 1, Math.floor((point.x - geometry.left) / geometry.step)));
        selectedIndex = index; showReadout(renderedRows[index]); drawCrosshair(index);
        if (commit) commitPoint(index, geometry.inverseY(Math.max(geometry.top, Math.min(geometry.bottom, point.y))));
    }
    function validDrawings() {
        var list = drawings[drawingKey()];
        return Array.isArray(list) ? list.slice(-100).filter(function (d) {
            return d && ['horizontal', 'trend', 'fib'].indexOf(d.type) !== -1 && Array.isArray(d.points)
                && d.points.length === (d.type === 'horizontal' ? 1 : 2) && d.points.every(function (p) {
                    return p && typeof p.key === 'string' && Number.isFinite(p.price) && p.price > 0;
                });
        }) : [];
    }
    function commitPoint(index, price) {
        var row = renderedRows[index]; if (!row || currentTool === 'inspect') return;
        if (currentTool === 'anchor') {
            anchors[drawingKey()] = keyOf(row); persist(); schedule(); return;
        }
        var point = { key: keyOf(row), price: price };
        if (currentTool !== 'horizontal' && !pendingPoint) {
            pendingPoint = point; el('tool-help').textContent = '두 번째 지점을 선택하세요. 그리기 취소로 첫 지점을 지울 수 있습니다.'; schedule(); return;
        }
        var points = currentTool === 'horizontal' ? [point] : [pendingPoint, point];
        var list = validDrawings(); list.push({ type: currentTool, points: points }); drawings[drawingKey()] = list.slice(-100);
        pendingPoint = null; updateToolHelp(); persist(); schedule();
    }
    function drawUserLines(plot, rows, x, y, left, right) {
        function indexFor(point) { return rows.findIndex(function (r) { return keyOf(r) === point.key; }); }
        validDrawings().forEach(function (d) {
            if (replayKey !== null && d.points.some(function (p) { return p.key > replayKey; })) return;
            var a = d.points[0], b = d.points[1];
            if (d.type === 'horizontal') {
                plot.appendChild(svg('line', { x1: left, x2: right, y1: y(a.price), y2: y(a.price), 'class': 'tw-user-line' }));
                plot.appendChild(svg('text', { x: left + 4, y: y(a.price) - 5 }, number(a.price))); return;
            }
            var ai = indexFor(a), bi = indexFor(b); if (ai < 0 || bi < 0) return;
            if (d.type === 'trend') plot.appendChild(svg('line', { x1: x(ai), x2: x(bi), y1: y(a.price), y2: y(b.price), 'class': 'tw-user-line' }));
            else [0, .236, .382, .5, .618, .786, 1].forEach(function (ratio) {
                var value = b.price + (a.price - b.price) * ratio;
                plot.appendChild(svg('line', { x1: Math.min(x(ai), x(bi)), x2: right, y1: y(value), y2: y(value), 'class': 'tw-user-line', opacity: .65 }));
                plot.appendChild(svg('text', { x: Math.min(x(ai), x(bi)) + 4, y: y(value) - 4 }, ratio.toFixed(3) + ' · ' + number(value)));
            });
        });
        if (pendingPoint) {
            var i = indexFor(pendingPoint);
            if (i >= 0) plot.appendChild(svg('circle', { cx: x(i), cy: y(pendingPoint.price), r: 4, 'class': 'tw-point' }));
        }
    }
    function drawPatterns(plot, rows, x, y) {
        var offset = activeRows.length - rows.length;
        engine.detectPatterns(activeRows).slice(-5).forEach(function (p) {
            var i = p.confirmedIndex - offset;
            if (i < 0 || i >= rows.length) return;
            plot.appendChild(svg('circle', { cx: x(i), cy: y(p.level), r: 4, 'class': 'tw-point' }));
            plot.appendChild(svg('text', { x: Math.min(x(i) + 8, geometry.right - 120), y: y(p.level) - 8 }, p.label));
        });
    }
    function renderTimeframes(rows) {
        var holder = el('timeframes'); clear(holder);
        var table = make('table'); var caption = make('caption', 'tw-table-caption', '시간 단위별 추세'); table.appendChild(caption);
        var thead = make('thead'); var header = make('tr');
        ['시간 단위', '종가', 'RSI 14', '슈퍼트렌드', 'EMA 20 대비'].forEach(function (label) { var th = make('th', '', label); th.scope = 'col'; header.appendChild(th); });
        thead.appendChild(header); table.appendChild(thead); var body = make('tbody');
        timeframeChoices().forEach(function (tf) {
            var calculated = enriched(rows, tf, ''); var last = calculated[calculated.length - 1]; if (!last) return;
            var tr = make('tr'); var label = make('th', '', timeframeLabel(tf, currentContext())); label.scope = 'row'; tr.appendChild(label);
            tr.appendChild(make('td', '', number(last.close))); tr.appendChild(make('td', '', number(last.rsi, 1)));
            tr.appendChild(make('td', last.supertrendDirection === 'up' ? 'is-up' : last.supertrendDirection === 'down' ? 'is-down' : '', last.supertrendDirection === 'up' ? '상승' : last.supertrendDirection === 'down' ? '하락' : '계산 대기'));
            tr.appendChild(make('td', '', Number.isFinite(last.ema20) ? number((last.close / last.ema20 - 1) * 100, 2) + '%' : '—'));
            body.appendChild(tr);
        });
        table.appendChild(body); holder.appendChild(table);
    }
    function stopPlayback() {
        if (replayTimer !== null) window.clearInterval(replayTimer);
        replayTimer = null; el('replay-play').textContent = '재생';
    }
    function endReplay() { stopPlayback(); replayKey = null; replayInterval = null; selectedIndex = null; alertRuntime = {}; primeAlerts(); schedule(); }
    function stepReplay() {
        var index = rawRows.findIndex(function (row) { return keyOf(row) > replayKey; });
        if (index < 0) { stopPlayback(); return; }
        replayKey = keyOf(rawRows[index]); selectedIndex = null; schedule();
        if (index === rawRows.length - 1) stopPlayback();
    }
    function updateToolHelp() {
        el('tool-help').textContent = currentTool === 'inspect' ? '차트에서 봉을 선택해 가격과 지표 값을 확인하세요.'
            : currentTool === 'anchor' ? '차트의 봉을 선택하면 VWAP 계산을 그 지점부터 시작합니다.'
            : currentTool === 'horizontal' ? '가격 위치를 선택하면 수평선을 그립니다.' : '차트에서 시작점과 끝점을 차례로 선택하세요.';
    }
    function addCondition(value) {
        var holder = el('conditions'); if (holder.children.length >= 5) return;
        var condition = value || { field: 'close', operator: 'crossesAbove', value: '' };
        var row = make('div', 'tw-condition');
        var fieldLabel = make('label'); var field = make('select'); field.setAttribute('aria-label', '알림 지표'); field.dataset.conditionField = 'true';
        Object.keys(fields).forEach(function (key) { var option = make('option', '', fields[key]); option.value = key; field.appendChild(option); }); field.value = condition.field;
        fieldLabel.appendChild(field); row.appendChild(fieldLabel);
        var opLabel = make('label'); var op = make('select'); op.setAttribute('aria-label', '알림 비교'); op.dataset.conditionOperator = 'true';
        Object.keys(operators).forEach(function (key) { var option = make('option', '', operators[key]); option.value = key; op.appendChild(option); }); op.value = condition.operator;
        opLabel.appendChild(op); row.appendChild(opLabel);
        var input = make('input'); input.type = 'number'; input.step = 'any'; input.required = true; input.value = condition.value; input.setAttribute('aria-label', '알림 기준값'); input.dataset.conditionValue = 'true'; row.appendChild(input);
        var remove = make('button', '', '삭제'); remove.type = 'button'; remove.setAttribute('aria-label', '이 알림 조건 삭제');
        remove.addEventListener('click', function () { if (holder.children.length > 1) { row.remove(); el('add-condition').disabled = false; } }); row.appendChild(remove);
        holder.appendChild(row); el('add-condition').disabled = holder.children.length >= 5;
    }
    function alertRows(alert, ctx) {
        var rows = engine.normalizeBars(ctx && ctx.bars || []);
        var anchor = alert.anchor || '';
        var index = anchor ? rows.findIndex(function (row) { return keyOf(row) === anchor; }) : 0;
        var calculated = engine.indicators(rows, { anchorIndex: Math.max(0, index) });
        if (anchor && index < 0) calculated.forEach(function (row) { row.avwap = null; });
        return calculated;
    }
    function evaluateAlerts(detail) {
        if (replayKey !== null) return;
        alerts.forEach(function (alert) {
            if (alert.enabled === false || alert.symbol !== detail.symbol || alert.mode !== detail.mode || alert.interval !== detail.interval) return;
            var rows = alertRows(alert, detail); if (rows.length < 2) return;
            var last = rows[rows.length - 1];
            var lastKey = keyOf(last);
            if (alert.createdKey && lastKey < alert.createdKey) return;
            var result = engine.evaluateConditions(rows, alert.conditions, alert.match);
            var signature = JSON.stringify([lastKey, result.values]);
            var runtime = alertRuntime[alert.id];
            if (!runtime) { alertRuntime[alert.id] = { signature: signature, matched: result.matched, lastKey: lastKey }; return; }
            if (lastKey < runtime.lastKey) return;
            if (runtime.signature === signature) return;
            if (result.available && result.matched && !runtime.matched) {
                alert.lastTriggered = keyOf(last);
                el('alert-status').textContent = alert.symbol + ' · ' + alert.lastTriggered + '에 저장한 조건을 충족했습니다.';
                persist('alert-status'); renderAlerts();
            }
            runtime.signature = signature; runtime.matched = result.available && result.matched; runtime.lastKey = lastKey;
        });
    }
    function primeAlerts() {
        Object.keys(window.TechnicalAnalysisContexts || {}).forEach(function (key) { evaluateAlerts(window.TechnicalAnalysisContexts[key]); });
    }
    function renderAlerts() {
        el('alert-count').textContent = alerts.length + '개'; clear(el('alert-list'));
        if (!alerts.length) { el('alert-list').appendChild(make('li', '', '저장한 알림이 없습니다. 지표와 기준값을 정해 추가하세요.')); return; }
        alerts.forEach(function (alert) {
            var li = make('li'); var description = make('div', 'tw-alert-description');
            var context = (window.TechnicalAnalysisContexts || {})[alert.symbol + ':' + alert.mode];
            var summary = alert.conditions.map(function (c) { return fields[c.field] + ' ' + operators[c.operator] + ' ' + number(c.value, 2); }).join(alert.match === 'all' ? ' 그리고 ' : ' 또는 ');
            description.appendChild(make('span', '', alert.symbol + ' · ' + (alert.mode === 'daily' ? '일봉' : alert.interval + '분봉') + ' · ' + summary));
            description.appendChild(make('small', '', alert.enabled === false ? '일시 정지'
                : context && context.interval !== alert.interval ? '저장한 ' + alert.interval + '분봉 데이터 대기 · 공통 분봉 간격을 맞추세요.'
                : alert.lastTriggered ? '최근 충족: ' + alert.lastTriggered : '다음 데이터 갱신부터 감시'));
            li.appendChild(description);
            var toggle = make('button', '', alert.enabled === false ? '다시 감시' : '정지'); toggle.type = 'button';
            toggle.addEventListener('click', function () { alert.enabled = alert.enabled === false; delete alertRuntime[alert.id]; primeAlerts(); persist('alert-status'); renderAlerts(); });
            var remove = make('button', '', '삭제'); remove.type = 'button'; remove.setAttribute('aria-label', alert.symbol + ' 알림 삭제');
            remove.addEventListener('click', function () { alerts = alerts.filter(function (a) { return a.id !== alert.id; }); delete alertRuntime[alert.id]; persist('alert-status'); renderAlerts(); });
            li.appendChild(toggle); li.appendChild(remove); el('alert-list').appendChild(li);
        });
    }
    function renderTemplates() {
        var select = el('template'); clear(select); var empty = make('option', '', '선택하세요'); empty.value = ''; select.appendChild(empty);
        templates.forEach(function (t, i) { var option = make('option', '', t.name); option.value = String(i); select.appendChild(option); });
        el('template-load').disabled = !templates.length; el('template-delete').disabled = !templates.length;
    }
    function applyMode() {
        var active = document.querySelector('[data-kodex-chart-mode="' + state.mode + '"]');
        if (active && active.getAttribute('aria-pressed') !== 'true') active.click();
    }
    function bind() {
        var mapping = { symbol: 'symbol', mode: 'mode', timeframe: 'timeframe', 'chart-type': 'chartType', scale: 'scale', window: 'window', oscillator: 'oscillator' };
        Object.keys(mapping).forEach(function (id) { el(id).addEventListener('change', function () {
            state[mapping[id]] = this.value; pendingPoint = null; selectedIndex = null;
            if (id === 'mode' || id === 'symbol') { endReplay(); state.timeframe = 'native'; }
            if (id === 'mode') applyMode();
            persist(); schedule();
        }); });
        root.querySelectorAll('[data-tw-overlay]').forEach(function (input) { input.addEventListener('change', function () { state.overlays[this.dataset.twOverlay] = this.checked; persist(); schedule(); }); });
        el('anchor').addEventListener('change', function () { anchors[drawingKey()] = this.value; persist(); schedule(); });
        el('tool').addEventListener('change', function () { currentTool = this.value; pendingPoint = null; updateToolHelp(); schedule(); });
        el('undo').addEventListener('click', function () { if (pendingPoint) pendingPoint = null; else { var list = validDrawings(); list.pop(); drawings[drawingKey()] = list; } updateToolHelp(); persist(); schedule(); });
        el('clear-drawings').addEventListener('click', function () { drawings[drawingKey()] = []; pendingPoint = null; updateToolHelp(); persist(); schedule(); });
        chart.addEventListener('keydown', function (event) {
            if (!renderedRows.length) return;
            if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Enter', 'Escape'].indexOf(event.key) === -1) return;
            event.preventDefault();
            if (event.key === 'Escape') { pendingPoint = null; selectedIndex = null; updateToolHelp(); schedule(); return; }
            if (selectedIndex === null) selectedIndex = renderedRows.length - 1;
            if (event.key === 'ArrowLeft') selectedIndex = Math.max(0, selectedIndex - 1);
            if (event.key === 'ArrowRight') selectedIndex = Math.min(renderedRows.length - 1, selectedIndex + 1);
            if (event.key === 'Home') selectedIndex = 0;
            if (event.key === 'End') selectedIndex = renderedRows.length - 1;
            showReadout(renderedRows[selectedIndex]); drawCrosshair(selectedIndex);
            if (event.key === 'Enter') commitPoint(selectedIndex, renderedRows[selectedIndex].close);
        });
        el('replay-start').addEventListener('click', function () { stopPlayback(); replayInterval = currentContext().interval; replayKey = keyOf(rawRows[Math.max(0, Math.floor(rawRows.length * .5) - 1)]); selectedIndex = null; pendingPoint = null; schedule(); });
        el('replay-step').addEventListener('click', stepReplay);
        el('replay-play').addEventListener('click', function () {
            if (replayTimer !== null) { stopPlayback(); return; }
            if (replayKey === null || !rawRows.length || replayKey >= keyOf(rawRows[rawRows.length - 1])) return;
            el('replay-play').textContent = '일시 정지'; replayTimer = window.setInterval(stepReplay, Number(el('replay-speed').value));
        });
        el('replay-speed').addEventListener('change', function () { if (replayTimer !== null) { stopPlayback(); el('replay-play').click(); } });
        el('replay-range').addEventListener('input', function () { stopPlayback(); replayKey = keyOf(rawRows[Math.max(0, Math.min(rawRows.length - 1, Number(this.value) - 1))]); selectedIndex = null; schedule(); });
        el('replay-end').addEventListener('click', function () { endReplay(); alertRuntime = {}; primeAlerts(); });
        el('export').addEventListener('click', function () {
            var blob = new Blob(['\ufeff' + engine.toCSV(activeRows)], { type: 'text/csv;charset=utf-8' });
            var url = URL.createObjectURL(blob); var link = make('a'); link.href = url;
            link.download = state.symbol + '-' + state.mode + '-' + state.timeframe + (replayKey === null ? '' : '-replay') + '.csv';
            document.body.appendChild(link); link.click(); link.remove(); window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
        });
        el('add-condition').addEventListener('click', function () { addCondition(); });
        el('alert-form').addEventListener('submit', function (event) {
            event.preventDefault();
            if (replayKey !== null) { el('alert-status').textContent = '최신으로 돌아온 뒤 알림을 저장하세요.'; return; }
            var ctx = currentContext();
            if (!ctx || !rawRows.length) { el('alert-status').textContent = '가격 데이터를 불러온 뒤 알림을 저장하세요.'; return; }
            if (alerts.length >= 40) { el('alert-status').textContent = '알림은 40개까지 저장합니다. 기존 알림을 삭제하세요.'; return; }
            var conditions = Array.prototype.map.call(el('conditions').children, function (row) {
                return { field: row.querySelector('[data-condition-field]').value, operator: row.querySelector('[data-condition-operator]').value, value: Number(row.querySelector('[data-condition-value]').value) };
            });
            if (!conditions.every(validCondition)) { el('alert-status').textContent = '모든 조건에 올바른 숫자를 입력하세요.'; return; }
            var anchor = anchors[drawingKey()] || '';
            if (anchor && state.timeframe !== 'native') {
                var originalAnchor = rawRows.find(function (row) { return keyOf(engine.aggregateBars([row], state.timeframe)[0]) === anchor; });
                if (originalAnchor) anchor = keyOf(originalAnchor);
            }
            var alert = { id: String(Date.now()) + '-' + String(Math.random()).slice(2, 9), symbol: state.symbol, mode: state.mode, interval: ctx.interval,
                match: el('alert-match').value, conditions: conditions, enabled: true, anchor: anchor, createdKey: keyOf(rawRows[rawRows.length - 1]) };
            alerts.push(alert); primeAlerts();
            if (persist('alert-status')) el('alert-status').textContent = '원본 ' + timeframeLabel('native', ctx) + '에 알림을 저장했습니다. 다음 데이터 갱신부터 확인합니다.';
            renderAlerts();
        });
        el('template-form').addEventListener('submit', function (event) {
            event.preventDefault(); var name = el('template-name').value.trim(); if (!name) return;
            var existing = templates.findIndex(function (t) { return t.name === name; });
            if (existing < 0 && templates.length >= 20) { el('template-status').textContent = '설정은 20개까지 저장합니다. 기존 설정을 삭제하세요.'; return; }
            var template = { name: name, settings: validSettings(state) };
            if (existing >= 0) templates[existing] = template; else templates.push(template);
            if (persist()) el('template-status').textContent = '“' + name + '” 설정을 저장했습니다.';
            renderTemplates();
        });
        el('template-load').addEventListener('click', function () {
            var value = el('template').value; if (value === '' || !templates[Number(value)]) return;
            state = validSettings(templates[Number(value)].settings); pendingPoint = null; endReplay(); applyMode(); persist(); schedule();
            el('template-status').textContent = '저장한 차트 설정을 불러왔습니다.';
        });
        el('template-delete').addEventListener('click', function () {
            var value = el('template').value; if (value === '') return;
            templates.splice(Number(value), 1); persist(); renderTemplates(); el('template-status').textContent = '설정을 삭제했습니다.';
        });
        window.addEventListener('technical-analysis-data', function (event) {
            if (!event.detail) return;
            evaluateAlerts(event.detail);
            renderAlerts();
            if (event.detail.symbol === state.symbol && event.detail.mode === state.mode) {
                if (replayKey !== null && (event.detail.interval !== replayInterval || event.detail.bars.length && !engine.normalizeBars(event.detail.bars).some(function (row) { return keyOf(row) === replayKey; }))) endReplay();
                schedule();
            }
        });
        document.querySelectorAll('[data-kodex-chart-mode]').forEach(function (button) { button.addEventListener('click', function () {
            var mode = button.getAttribute('data-kodex-chart-mode');
            if (state.mode !== mode) { state.mode = mode; state.timeframe = 'native'; }
            pendingPoint = null; endReplay(); persist(); schedule();
        }); });
        document.addEventListener('visibilitychange', function () { if (document.hidden) stopPlayback(); });
        document.querySelectorAll('[data-market-view]').forEach(function (link) { link.addEventListener('click', function () { if (link.getAttribute('data-market-view') !== 'technical') stopPlayback(); }); });
        window.addEventListener('pagehide', stopPlayback);
    }
    syncControls(); bind(); addCondition(); renderTemplates(); renderAlerts(); primeAlerts(); applyMode(); render();
}());
