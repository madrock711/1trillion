'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const engine = require('../assets/technical-analysis-engine.js');
const source = fs.readFileSync(path.join(__dirname, '../assets/technical-workbench.js'), 'utf8');

function functionSource(name, nextName) {
    const start = source.indexOf('    function ' + name + '(');
    const end = source.indexOf('    function ' + nextName + '(', start);
    assert(start >= 0 && end > start, name + ' must be available for the runtime regression');
    return source.slice(start, end);
}

function harness() {
    const statuses = {};
    const context = vm.createContext({
        engine,
        alerts: [],
        alertRuntime: {},
        replayKey: null,
        window: { TechnicalAnalysisContexts: {} },
        el: id => statuses[id] || (statuses[id] = {}),
        persist: () => true,
        renderAlerts() {},
        statuses
    });
    vm.runInContext(functionSource('keyOf', 'contextKey'), context);
    vm.runInContext(functionSource('cutoff', 'enriched'), context);
    vm.runInContext(functionSource('enriched', 'heikinAshi'), context);
    vm.runInContext(functionSource('alertRows', 'evaluateAlerts'), context);
    vm.runInContext(functionSource('evaluateAlerts', 'primeAlerts'), context);
    vm.runInContext(functionSource('primeAlerts', 'renderAlerts'), context);
    return context;
}

function bars(date, closes) {
    return closes.map((close, index) => ({
        date,
        time: '09:' + String(index * 5).padStart(2, '0'),
        open: close,
        high: close + 1,
        low: close - 1,
        close,
        volume: 100
    }));
}

function detail(date, closes) {
    return { symbol: 'KODEX', mode: 'intraday', interval: 5, bars: bars(date, closes) };
}

function alert(field, value) {
    return {
        id: 'fixture', symbol: 'KODEX', mode: 'intraday', interval: 5, match: 'all',
        conditions: [{ field, operator: 'above', value }], enabled: true
    };
}

{
    const context = harness();
    const rows = bars('2026-10-13', [100, 102, 104]);
    const existing = context.enriched(rows, 'native', '2026-10-13 09:05');
    assert.equal(existing[0].avwap, null, 'an available anchor must exclude earlier bars');
    assert.equal(existing[1].avwap, 102, 'the selected actual bar must seed VWAP');
    for (const anchor of ['2026-10-01 09:00', '2026-10-14 09:00', '2026-10-13 09:02']) {
        const result = context.enriched(rows, 'native', anchor);
        assert(result.every(row => row.avwap === null && row.avwapUpper === null && row.avwapLower === null),
            'missing anchor ' + anchor + ' must not silently restart VWAP on another bar');
        assert(context.alertRows({ anchor }, { bars: rows }).every(row => row.avwap === null),
            'an alert with an unavailable native anchor must also remain unavailable');
    }
}

{
    const context = harness();
    const rule = alert('close', 110);
    context.alerts = [rule];
    context.evaluateAlerts(detail('2026-10-13', [100, 100]));
    context.evaluateAlerts(detail('2026-10-12', [120, 120]));
    assert.equal(rule.lastTriggered, undefined, 'selecting an earlier archive must not trigger a saved current-session alert');
    context.evaluateAlerts(detail('2026-10-13', [100, 120]));
    assert.equal(rule.lastTriggered, '2026-10-13 09:05', 'an actual later condition transition must still trigger');

    const restored = alert('close', 110);
    restored.createdKey = '2026-10-13 09:05';
    context.alerts = [restored];
    context.alertRuntime = {};
    context.evaluateAlerts(detail('2026-10-12', [100, 100]));
    context.evaluateAlerts(detail('2026-10-12', [100, 120]));
    assert.equal(restored.lastTriggered, undefined, 'restored alerts must reject data before their creation time');
    assert.equal(Object.keys(context.alertRuntime).length, 0, 'old archives must not seed restored runtime state');
    context.evaluateAlerts(detail('2026-10-13', [100, 100]));
    context.evaluateAlerts(detail('2026-10-13', [100, 120]));
    assert.equal(restored.lastTriggered, '2026-10-13 09:05', 'restored alerts must monitor new live updates after priming');
}

{
    const context = harness();
    const rule = alert('avwap', 110);
    context.alerts = [rule];
    const incoming = detail('2026-10-13', [100, 100]);
    context.evaluateAlerts(incoming);
    incoming.bars[0].high = 200;
    assert.equal(context.alertRows(rule, incoming)[1].avwap, 116.5,
        'fixture must change VWAP through a historical high correction without changing the last close or volume');
    context.evaluateAlerts(incoming);
    assert.equal(rule.lastTriggered, '2026-10-13 09:05', 'a corrected indicator condition must not be discarded as an unchanged latest quote');
    const signature = context.alertRuntime[rule.id].signature;
    rule.lastTriggered = 'unchanged';
    context.evaluateAlerts(incoming);
    assert.equal(rule.lastTriggered, 'unchanged', 'identical indicator updates must not notify repeatedly');
    assert.equal(context.alertRuntime[rule.id].signature, signature);
}

{
    const context = harness();
    context.replayKey = '2026-10-13 09:10';
    const incoming = detail('2026-10-13', [100, 102, 104, 1000]);
    incoming.bars[3].volume = 100000;
    const prefix = context.cutoff(incoming.bars);
    const aggregated = context.enriched(prefix, '60', '');
    assert.equal(aggregated.length, 1);
    assert.equal(aggregated[0].close, 104, 'higher-timeframe replay must omit the future native close');
    assert.equal(aggregated[0].high, 105, 'higher-timeframe replay must omit the future native high');
    assert.equal(aggregated[0].volume, 300, 'higher-timeframe replay must omit future volume');
    context.alerts = [alert('close', 110)];
    context.evaluateAlerts(incoming);
    assert.equal(Object.keys(context.alertRuntime).length, 0, 'historical replay must suspend alert evaluation');
}

{
    const start = source.indexOf("        window.addEventListener('technical-analysis-data', function (event) {");
    const end = source.indexOf("        document.querySelectorAll('[data-kodex-chart-mode]')", start);
    assert(start >= 0 && end > start, 'the actual source-data listener must exist');
    const context = harness();
    let onData;
    context.window.addEventListener = (_, listener) => { onData = listener; };
    context.window.clearInterval = () => {};
    context.schedule = () => {};
    context.state = { symbol: 'KODEX', mode: 'intraday' };
    context.replayTimer = null;
    context.selectedIndex = null;
    context.replayKey = '2026-10-13 09:00';
    context.replayInterval = 5;
    vm.runInContext(functionSource('stopPlayback', 'endReplay'), context);
    vm.runInContext(functionSource('endReplay', 'stepReplay'), context);
    vm.runInContext(source.slice(start, end), context);
    onData({ detail: detail('2026-10-13', [100, 110, 120]) });
    assert.equal(context.replayKey, '2026-10-13 09:00', 'normal updates with the same native interval must keep replay active');
    const changed = { ...detail('2026-10-13', [100, 110, 120]), interval: 60 };
    changed.bars = engine.aggregateBars(changed.bars, '60');
    assert.equal(changed.bars[0].time, '09:00', 'fixture must retain the same replay key at the larger interval');
    context.window.TechnicalAnalysisContexts['KODEX:intraday'] = changed;
    onData({ detail: changed });
    assert.equal(context.replayKey, null, 'source interval changes must end replay even when a new aggregate retains its old timestamp');
    assert.equal(context.replayInterval, null, 'ending replay must clear the source interval snapshot');

    const rule = alert('close', 110);
    context.alerts = [rule];
    context.alertRuntime = { fixture: { matched: false, lastKey: '2026-10-12 09:05', signature: 'before-replay' } };
    context.replayKey = '2026-10-12 09:00';
    context.replayInterval = 5;
    const afterReplay = detail('2026-10-13', [120, 120]);
    context.window.TechnicalAnalysisContexts['KODEX:intraday'] = afterReplay;
    onData({ detail: afterReplay });
    assert.equal(context.replayKey, null, 'switching to a different available session must exit the old replay');
    assert.equal(rule.lastTriggered, undefined, 'replay exit must re-prime alerts without reporting skipped historical transitions');
    assert.equal(context.alertRuntime.fixture.matched, true, 'replay exit must seed runtime from the current source');
}

{
    const start = source.indexOf("        el('alert-form').addEventListener('submit', function (event) {");
    const end = source.indexOf("        el('template-form').addEventListener('submit'", start);
    assert(start >= 0 && end > start, 'the actual alert creation listener must exist');
    const context = harness();
    let submitAlert;
    context.statuses['alert-form'] = { addEventListener: (_, listener) => { submitAlert = listener; } };
    context.statuses['alert-match'] = { value: 'all' };
    const inputs = {
        '[data-condition-field]': { value: 'avwap' },
        '[data-condition-operator]': { value: 'above' },
        '[data-condition-value]': { value: '110' }
    };
    context.statuses.conditions = { children: [{ querySelector: selector => inputs[selector] }] };
    context.fields = { avwap: 'VWAP' };
    context.operators = { above: '초과' };
    context.timeframeLabel = () => '원본';
    vm.runInContext(functionSource('contextKey', 'drawingKey'), context);
    vm.runInContext(functionSource('drawingKey', 'currentContext'), context);
    vm.runInContext(functionSource('currentContext', 'number'), context);
    vm.runInContext(functionSource('validCondition', 'validAlert'), context);
    vm.runInContext(source.slice(start, end), context);

    context.state = { symbol: 'KODEX', mode: 'daily', timeframe: 'monthly' };
    context.rawRows = ['2026-10-05', '2026-10-06'].map(date => ({ date, open: 100, high: 101, low: 99, close: 100, volume: 100 }));
    context.anchors = { 'KODEX:daily:monthly': '2026-10-01' };
    context.window.TechnicalAnalysisContexts['KODEX:daily'] = { symbol: 'KODEX', mode: 'daily', interval: 1, bars: context.rawRows };
    submitAlert({ preventDefault() {} });
    assert.equal(context.alerts[0].anchor, '2026-10-05', 'a holiday month boundary must translate to its first actual native bar for alerts');
    assert(context.alertRows(context.alerts[0], { bars: context.rawRows }).every(row => row.avwap !== null),
        'translated monthly anchors must produce available native VWAP');

    context.alerts = [];
    context.state = { symbol: 'TQQQ', mode: 'intraday', timeframe: '60' };
    context.rawRows = bars('2026-10-13', [100, 102]).map((row, index) => ({ ...row, time: index ? '09:35' : '09:30' }));
    context.anchors = { 'TQQQ:intraday:60': '2026-10-13 09:00' };
    context.window.TechnicalAnalysisContexts['TQQQ:intraday'] = { symbol: 'TQQQ', mode: 'intraday', interval: 5, bars: context.rawRows };
    submitAlert({ preventDefault() {} });
    assert.equal(context.alerts[0].anchor, '2026-10-13 09:30', 'a US 60-minute bucket must translate to its first actual 09:30 source bar');
}

{
    const start = source.indexOf("        document.querySelectorAll('[data-kodex-chart-mode]').forEach(function (button) { button.addEventListener('click'");
    const end = source.indexOf("        document.addEventListener('visibilitychange'", start);
    assert(start >= 0 && end > start, 'the actual shared chart-mode handler must exist');
    let onModeClick;
    let requestedMode = 'daily';
    const context = vm.createContext({
        state: { mode: 'daily', timeframe: 'weekly' },
        pendingPoint: null,
        document: {
            querySelectorAll: () => [{
                getAttribute: () => requestedMode,
                addEventListener: (_, listener) => { onModeClick = listener; }
            }]
        },
        endReplay() {}, persist() {}, schedule() {}
    });
    vm.runInContext(source.slice(start, end), context);
    onModeClick();
    assert.equal(context.state.timeframe, 'weekly', 'applying the already selected mode must preserve a restored weekly template');
    requestedMode = 'intraday';
    context.state = { mode: 'intraday', timeframe: '15' };
    onModeClick();
    assert.equal(context.state.timeframe, '15', 'applying a saved intraday mode must preserve its restored 15-minute aggregation');
    requestedMode = 'daily';
    onModeClick();
    assert.equal(context.state.mode, 'daily');
    assert.equal(context.state.timeframe, 'native', 'a genuine user mode change must reset incompatible aggregation');
}

console.log('Technical workbench anchor availability, archive alerts, corrected indicators, replay prefix, and template state tests passed.');
