const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.js'), 'utf8');
const snapshot = JSON.parse(fs.readFileSync(
    path.join(root, 'assets', 'data', 'market-dashboard-latest.json'),
    'utf8'
));
const start = source.indexOf('    function validateData(data) {');
const end = source.indexOf('\n    function render(data) {', start);

assert(start >= 0 && end > start, 'validateData 함수를 찾을 수 없습니다.');

const context = { result: null, error: null };
vm.createContext(context);
vm.runInContext(`${source.slice(start, end)}\nthis.validateData = validateData;`, context);

assert.doesNotThrow(
    () => context.validateData(structuredClone(snapshot)),
    '최신 대시보드의 실제 스냅샷이 초기화되어야 합니다.'
);

const absentKosdaq = structuredClone(snapshot);
Object.assign(absentKosdaq.markets.find((market) => market.id === 'KOSDAQ'), {
    value: null, open: null, high: null, low: null
});
assert.doesNotThrow(() => context.validateData(absentKosdaq));

const invalidKospi = structuredClone(snapshot);
invalidKospi.markets.find((market) => market.id === 'KOSPI').open = null;
assert.throws(
    () => context.validateData(invalidKospi),
    /KOSPI OHLC 데이터가 올바르지 않습니다/,
    '핵심 지수 KOSPI의 불완전한 OHLC는 차단해야 합니다.'
);

const partialKosdaq = structuredClone(absentKosdaq);
partialKosdaq.markets.find((market) => market.id === 'KOSDAQ').value = 1000;
assert.throws(
    () => context.validateData(partialKosdaq),
    /KOSDAQ OHLC 데이터가 올바르지 않습니다/,
    '보조 지수도 일부 OHLC만 들어온 불완전한 상태는 차단해야 합니다.'
);

console.log('Market dashboard optional OHLC validation tests passed.');
