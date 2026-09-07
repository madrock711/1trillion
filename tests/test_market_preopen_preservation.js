const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets/market-dashboard.js'), 'utf8');
const snapshot = JSON.parse(fs.readFileSync(path.join(root, 'assets/data/market-dashboard-20260904-0818.json'), 'utf8'));
const start = source.indexOf('    function findById(items, id) {');
const end = source.indexOf('    function clearLiveRefreshTimer()', start);
assert(start >= 0 && end > start);
const context = {
    window: {}, document: { getElementById: () => ({ textContent: '' }) },
    lastAppliedLiveSignature: '',
    formatSigned: (value, unit) => `${value}${unit}`,
    formatNumber: String, formatKstDateTime: String
};
for (const name of ['renderMarketCards', 'renderCheckpoints', 'renderAnalysis', 'renderKospiHistoryChart',
    'renderLeadingCycleComparison', 'renderKodex', 'renderLoadState']) context[name] = () => {};
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);

const observed = {
    ...structuredClone(snapshot.markets[0]),
    marketStatus: 'PREOPEN', stateLabel: '개장 전', changePercent: 0,
    asOf: '2026-09-04T08:23:00+09:00', asOfLabel: '9월 4일 08:23 KST',
    flows: ['외국인', '기관', '개인'].map(label => ({ label, value: 0, unit: '억원' })),
    program: { total: 0, arbitrage: 0, nonArbitrage: 0, unit: '억원' }
};
const data = structuredClone(snapshot);
context.applyLiveMarketData(data, { markets: [observed], instruments: [], exchange: null });
for (const key of ['markets', 'changes', 'factors', 'flows', 'technical', 'checkpoints']) {
    assert.deepStrictEqual(data[key], snapshot[key], `장전 초기화 값으로 ${key} 기록을 덮으면 안 됩니다.`);
}
const instrument = structuredClone(snapshot.technical.instruments[0]);
const originalInstrument = structuredClone(instrument);
assert.strictEqual(context.replaceTechnicalObservation(instrument, observed), false);
assert.deepStrictEqual(instrument, originalInstrument);

// Zero is a valid observation after the regular session opens.
const opened = { ...observed, marketStatus: 'OPEN', stateLabel: '장중', asOf: '2026-09-04T09:01:00+09:00' };
context.applyLiveMarketData(data, { markets: [opened], instruments: [], exchange: null });
assert.strictEqual(data.markets[0].changePercent, 0);
assert.strictEqual(data.markets[0].asOf, opened.asOf);
assert.strictEqual(data.flows.program.total, 0);
assert(data.changes.find(item => item.label === 'KOSPI').meaning.includes('0% 보합'));
console.log('market preopen preservation tests passed');
