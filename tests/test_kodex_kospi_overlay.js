const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const start = source.indexOf('    function isLocalPrivateFlowHost(');
const end = source.indexOf('    function renderKodexIntradayRows(', start);
assert(start >= 0 && end > start);
const status = { textContent: '' };
const legend = { hidden: false };
const unit = { textContent: '' };
const raw = { textContent: '', hidden: true };
const cache = {
    '2026-11-04': { day: { bars: [
        { date: '2026-11-04', time: '09:05', foreign: -10, personal: 3, institution: 7, flowObservedAt: '09:05' },
        { date: '2026-11-04', time: '09:10', foreign: -25, personal: 8, institution: 17, flowObservedAt: '09:10' }
    ] } },
    '2026-11-03': { day: { bars: [
        { date: '2026-11-03', time: '15:30', foreign: 999, personal: 0, institution: -999, flowObservedAt: '15:30' }
    ] } }
};
const context = {
    kospiIntradayViewCache: cache, selectedKodexChartMode: 'intraday', Number,
    selectedKodexFlow: 'amount', displayedKodexFlowSource: 'naver',
    privateFlowState: { status: 'ready', tradeDate: '', fetchedAt: '2026-11-04T02:00:00Z', market: '통합', amount: [], quantity: [] },
    window: { location: { hostname: '127.0.0.1' } },
    document: { getElementById(id) { return ({ 'kodex-flow-status': status, 'kodex-flow-legend': legend, 'kodex-flow-legend-unit': unit, 'kodex-flow-raw': raw })[id]; } },
    formatHistoryDate(value) { return value; },
    formatSigned(value, unit) { return String(value) + unit; }
};
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);
const cacheStart = source.indexOf('    function cacheKospiIntradayDay(');
const cacheEnd = source.indexOf('\n    }', cacheStart) + 6;
assert(cacheStart >= 0 && cacheEnd > cacheStart);
vm.runInContext(source.slice(cacheStart, cacheEnd), context);
assert.equal(context.kodexFlowForRow({ date: '2026-11-04', time: '09:00', endTime: '09:04' }, ''), null, 'future data must not appear');
assert.equal(context.kodexFlowForRow({ date: '2026-11-04', time: '09:05', endTime: '09:09' }, '').foreign, -10);
assert.equal(context.kodexFlowForRow({ date: '2026-11-04', time: '09:10', endTime: '09:14' }, '').foreign, -25);
assert.equal(context.kodexFlowForRow({ date: '2026-11-04', time: '09:25', endTime: '09:29' }, ''), null, 'stale flow must not extend through the session');
assert.equal(context.kodexFlowForRow({ date: '2026-11-05', time: '09:00', endTime: '09:04' }, ''), null, 'prior sessions must never carry forward');
cache['2026-11-04'].day.flowSnapshotCount = 2;
context.cacheKospiIntradayDay({ date: '2026-11-04', bars: [], flowSnapshotCount: 0 });
assert.equal(cache['2026-11-04'].day.bars.length, 2, 'price-only response must not overwrite enriched flow');
context.updateKodexFlowState('quantity', [], { date: '2026-11-04' });
assert.match(status.textContent, /표시할 투자자별 자료가 없습니다/);
assert.equal(legend.hidden, true);
context.updateKodexFlowState('amount', [{ date: '2026-11-04', kospiFlow: cache['2026-11-04'].day.bars[0] }], { date: '2026-11-04' });
assert.match(status.textContent, /09:05 기준 · 외국인 -10억원/);
assert.equal(legend.hidden, false);
context.privateFlowState.fetchedAt = '2026-11-04T11:16:00+09:00';
context.privateFlowState.quantity = [{ bsop_hour: '11:15:00', timez12: '000000111500', frgn_val: '-3014', prsn_val: '314', orgn_val: '1816' }];
const now = Date.parse('2026-11-04T11:16:30+09:00');
assert.match(context.privateFlowRawText('quantity'), /11:15:00/);
assert.equal(context.privateFlowForRow({ date: '2026-11-04', time: '11:15' }, '', 'quantity', now).foreign, -3014);
assert.equal(context.privateFlowForRow({ date: '2026-11-04', time: '11:14' }, '', 'quantity', now), null, 'future observations must not be used');
assert.equal(context.privateFlowForRow({ date: '2026-11-04', time: '11:26' }, '', 'quantity', now), null, 'stale observations must not be used');
assert.equal(context.privateFlowForRow({ date: '2026-11-05', time: '11:15' }, '', 'quantity', now), null, 'observations must not cross sessions');
assert.equal(context.privateFlowForRow({ date: '2026-11-04', time: '11:15' }, '', 'quantity', Date.parse('2026-11-04T15:31:00+09:00')), null, 'outside session must not infer the date');
assert.equal(context.privateFlowForRow({ date: '2026-11-04', time: '11:15' }, '', 'quantity', Date.parse('2026-11-04T11:27:00+09:00')), null, 'stale responses must not be charted');
context.privateFlowState.quantity[0].timez12 = '000000111530';
assert.equal(context.privateFlowForRow({ date: '2026-11-04', time: '11:15' }, '', 'quantity', now), null, 'mismatching time fields must be rejected');
context.privateFlowState.fetchedAt = '2026-11-07T11:16:00+09:00';
assert.equal(context.privateFlowSession(context.privateFlowState.fetchedAt, Date.parse('2026-11-07T11:17:00+09:00')), null, 'weekends must not infer the date');
context.privateFlowState = { status: 'ready', fetchedAt: '2026-11-04T16:00:00+09:00', tradeDate: '2026-11-04',
    persisted: true, dateVerified: true, sessionStatus: 'closed', quantity: [
        { bsop_hour: '15:30:00', timez12: '000000153000', frgn_val: '-3210', prsn_val: '1200', orgn_val: '2010' }
    ] };
const later = Date.parse('2026-11-09T18:00:00+09:00');
assert.equal(context.privateFlowForRow({ date: '2026-11-04', time: '15:30' }, '', 'quantity', later).foreign, -3210,
    'verified persisted close survives after hours, weekends and later days');
assert.equal(context.privateFlowForRow({ date: '2026-11-09', time: '15:30' }, '', 'quantity', later), null,
    'saved close must never attach to another session');
context.privateFlowState.dateVerified = false;
assert.equal(context.privateFlowForRow({ date: '2026-11-04', time: '15:30' }, '', 'quantity', later), null,
    'unverified stale payload remains rejected');
console.log('KODEX KOSPI overlay: timing, inferred sessions, stale data and raw source handling ok');
