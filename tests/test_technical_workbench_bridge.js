'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const events = [];
const classList = { add() {}, remove() {}, toggle() {} };
const nodes = {};
function node(id) {
    return nodes[id] || (nodes[id] = { id, classList, appendChild() {} });
}
const context = vm.createContext({
    window: {
        TechnicalAnalysisContexts: {},
        dispatchEvent(event) { events.push(event); },
        CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } },
        MarketDashboardLive: {
            calculateMacd(values) {
                return { macd: values.map(() => null), signal: values.map(() => null), histogram: values.map(() => null) };
            },
            stableIntradayWindow(rows, date, count) {
                const dates = Array.from(new Set(rows.map(row => row.sessionDate || row.date))).filter(value => value <= date).slice(-count);
                return rows.filter(row => dates.includes(row.sessionDate || row.date));
            }
        }
    },
    document: { getElementById: node },
    selectedKodexIntradayInterval: 5,
    technicalAnalysisSignatures: {},
    technicalAnalysisRequestedDates: {},
    kospiTechnicalHistory: [],
    parseHistoryDate: date => Date.parse(date + 'T00:00:00Z'),
    mergeCurrentKospiHistory: rows => rows.slice(),
    priceOverlayRows: rows => rows.map(row => ({ ...row, ma20: row.close })),
    stochasticSlowRows: rows => rows,
    rsiMfiRows: rows => rows,
    kospiPeriodMonths: () => 1,
    estimateDailyVolumePressure: row => ({ delta: 0, volume: row.volume }),
    rollingIntradayRows: day => day && day.bars || [],
    clear() {},
    updatePriceOverlayLegend() {},
    updateTechnicalRangeNavigator() {},
    makeSvg() { return {}; },
    formatPrice() {},
    formatNumber() {}
});

function functionSource(name, nextName) {
    return source.slice(source.indexOf('    function ' + name + '('), source.indexOf('    function ' + nextName + '('));
}

function loadPrefix(name, boundary) {
    const start = source.indexOf('    function ' + name + '(');
    const end = source.indexOf(boundary, start);
    assert(end > start, name + ' must contain its data publication boundary');
    vm.runInContext(source.slice(start, end) + '\n    }', context);
}

vm.runInContext(functionSource('publishTechnicalAnalysisData', 'normalizedTechnicalChartState'), context);
vm.runInContext(functionSource('prepareKospiDailyRows', 'normalizeLeadingCycleData'), context);
vm.runInContext(functionSource('intradayDisplayRows', 'intradayCalculationDays'), context);

function bars(count, intraday) {
    return Array.from({ length: count }, (_, index) => ({
        date: new Date(Date.UTC(2026, 0, index + 1)).toISOString().slice(0, 10),
        ...(intraday ? { time: '09:30', endTime: '09:34' } : {}),
        open: 100 + index,
        high: 105 + index,
        low: 95 + index,
        close: 102 + index,
        volume: 1000 + index
    }));
}

const history = bars(150);
context.kospiTechnicalHistory = history;
const period = context.prepareKospiDailyRows(null);
assert(period.length < history.length, 'fixture must have indicator warmup before the chosen month');
assert.equal(context.window.TechnicalAnalysisContexts['KOSPI:daily'].bars.length, history.length,
    'KOSPI workbench must receive warmup history before the period and navigator cuts');
assert.equal(context.window.TechnicalAnalysisContexts['KOSPI:daily'].interval, 1);

loadPrefix('renderKodexDailyChart', '        if (history.length < 5) {');
loadPrefix('renderTqqqHistoryChart', '        if (history.length < 5) {');
context.renderKodexDailyChart({ priceHistory: history }, node('kodex-history-chart'), node('summary'), node('readout'));
context.renderTqqqHistoryChart(history);
for (const symbol of ['KODEX', 'TQQQ']) {
    const data = context.window.TechnicalAnalysisContexts[symbol + ':daily'];
    assert.equal(data.bars.length, history.length, symbol + ' must publish the full available daily dataset');
    assert.equal(data.asOf, history[history.length - 1].date);
}

loadPrefix('renderKospiRows', '        updateTechnicalRangeNavigator(rows);');
loadPrefix('renderKodexIntradayRows', '        rememberTechnicalRangePreview(svg, displayRows');
const intraday = bars(12, true);
const selectedDay = { date: intraday[11].date, displaySessionCount: 4, bars: intraday };
context.renderKospiRows(intraday, { mode: 'intraday', interval: 15, date: selectedDay.date, day: selectedDay });
context.renderKodexIntradayRows(selectedDay, 15, node('kodex-history-chart'), node('summary'), node('readout'));
context.renderKodexIntradayRows(selectedDay, 5, node('tqqq-history-chart'), node('summary'), node('readout'));
for (const symbol of ['KOSPI', 'KODEX', 'TQQQ']) {
    const data = context.window.TechnicalAnalysisContexts[symbol + ':intraday'];
    assert.equal(data.bars.length, 4, symbol + ' must publish displayed sessions before the navigator slice');
    assert.equal(data.bars[0].date, intraday[8].date, 'indicator warmup sessions must not replace the chosen sessions');
    assert.equal(data.asOf, selectedDay.date + ' 09:34', 'source session/time labels must remain in the source market time');
    assert.equal(data.interval, symbol === 'TQQQ' ? 5 : 15);
}

const incoming = bars(6, true);
incoming[0].volume = null;
context.publishTechnicalAnalysisData('KODEX', 'intraday', incoming, { interval: 5, date: incoming[5].date });
const published = context.window.TechnicalAnalysisContexts['KODEX:intraday'];
assert.equal(published.bars[0].volume, null, 'missing volume must remain missing');
incoming[0].close = 999;
assert.equal(published.bars[0].close, 102, 'later chart mutations must not modify the cached data');

const beforeCorrection = events.length;
context.publishTechnicalAnalysisData('KODEX', 'intraday', incoming, { interval: 5, date: incoming[5].date });
assert.equal(events.length, beforeCorrection + 1, 'a historical OHLC correction must reach the workbench');
context.publishTechnicalAnalysisData('KODEX', 'intraday', incoming, { interval: 5, date: incoming[5].date });
assert.equal(events.length, beforeCorrection + 1, 'unchanged navigator rerenders must not republish identical data');
assert(events.every(event => event.type === 'technical-analysis-data'));
assert.equal(events[events.length - 1].detail, context.window.TechnicalAnalysisContexts['KODEX:intraday'],
    'late initialization must see the exact most recently published context');

const dailyBeforeClear = context.window.TechnicalAnalysisContexts['KODEX:daily'];
context.publishTechnicalAnalysisData('KODEX', 'intraday', [], { interval: 5, date: '2026-10-13' });
assert.equal(context.window.TechnicalAnalysisContexts['KODEX:intraday'].bars.length, 0,
    'a failed or empty session must clear stale bars');
assert.equal(context.window.TechnicalAnalysisContexts['KODEX:intraday'].asOf, '2026-10-13');
assert.equal(context.window.TechnicalAnalysisContexts['KODEX:daily'], dailyBeforeClear,
    'clearing intraday data must preserve the independent daily context');

console.log('Technical workbench full-history, source-time, cache, correction, and empty-session bridge tests passed.');
