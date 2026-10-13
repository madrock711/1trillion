const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const engine = require('../assets/technical-analysis-engine.js');

function near(actual, expected, tolerance = 1e-9) {
    assert(Number.isFinite(actual), `유한 수치가 필요함: ${actual}`);
    assert(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)), `${actual} ≠ ${expected}`);
}

function dateAt(index) {
    return new Date(Date.UTC(2026, 0, index + 1)).toISOString().slice(0, 10);
}

function bar(close, index, overrides = {}) {
    return Object.assign({ date: dateAt(index), open: close, high: close, low: close, close, volume: 100 }, overrides);
}

// 브라우저 전역과 CommonJS에서 같은 공개 API를 사용할 수 있다.
const sandbox = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../assets/technical-analysis-engine.js'), 'utf8'), sandbox);
assert.equal(typeof sandbox.window.TechnicalAnalysisEngine.indicators, 'function');

// 날짜·시간·OHLC 검증, 중복 정정 및 거래량 결측을 독립적으로 검증한다.
const raw = [
    bar(12, 1, { time: '09:00', volume: null }),
    bar(10, 0, { open: '10', time: '09:01', volume: '25' }),
    bar(11, 0, { time: '09:00', volume: 0 }),
    bar(13, 0, { time: '09:01:00', volume: 30 }),
    bar(15, 2, { date: '2026-02-30' }),
    bar(15, 2, { time: '25:01' }),
    bar(15, 2, { open: null }),
    bar(15, 2, { high: 14 }),
    bar(15, 2, { low: '' }),
    bar(15, 3, { volume: -1 })
];
const normalized = engine.normalizeBars(raw);
assert.equal(normalized.length, 4);
assert.deepEqual(normalized.map(row => `${row.date} ${row.time || ''}`), ['2026-01-01 09:00', '2026-01-01 09:01', '2026-01-02 09:00', '2026-01-04 ']);
assert.equal(normalized[0].volume, 0);
assert.equal(normalized[1].close, 13);
assert.equal(normalized[1].volume, 30);
assert.equal(normalized[2].volume, null);
assert.equal(normalized[3].volume, null);
assert.equal(raw[1].open, '10');
assert.deepEqual(engine.normalizeBars(null), []);

// 월요일 경계는 실행 환경의 시간대와 DST에 영향받지 않는다.
const boundary = [
    bar(10, 0, { date: '2025-12-28', volume: 1 }),
    bar(12, 1, { date: '2025-12-29', volume: 2 }),
    bar(11, 2, { date: '2026-01-02', high: 14, low: 9, volume: 3 }),
    bar(15, 3, { date: '2026-01-05', volume: 4 })
];
const priorTimezone = process.env.TZ;
try {
    process.env.TZ = 'Pacific/Kiritimati';
    const weeklyEast = engine.aggregateBars(boundary, 'weekly');
    process.env.TZ = 'America/Los_Angeles';
    const weeklyWest = engine.aggregateBars(boundary, 'weekly');
    assert.deepEqual(weeklyEast, weeklyWest);
    assert.deepEqual(weeklyWest.map(row => row.date), ['2025-12-22', '2025-12-29', '2026-01-05']);
    assert.deepEqual(weeklyWest[1], { date: '2025-12-29', open: 12, high: 14, low: 9, close: 11, volume: 5 });
} finally {
    if (priorTimezone === undefined) delete process.env.TZ;
    else process.env.TZ = priorTimezone;
}
const monthly = engine.aggregateBars(boundary, 'monthly');
assert.deepEqual(monthly.map(row => row.date), ['2025-12-01', '2026-01-01']);
assert.equal(monthly[0].close, 12);
assert.equal(monthly[1].volume, 7);

// 분봉 집계는 같은 거래일의 동일 시간 버킷만 합치고 결측 거래량을 보존한다.
const minutes = [
    bar(10, 0, { time: '09:00', volume: 1 }),
    bar(12, 0, { time: '09:04', volume: 2 }),
    bar(11, 0, { time: '09:05', volume: null }),
    bar(13, 1, { time: '09:00', volume: 4 })
];
const fiveMinutes = engine.aggregateBars(minutes, '5');
assert.deepEqual(fiveMinutes.map(row => [row.date, row.time, row.volume]), [['2026-01-01', '09:00', 3], ['2026-01-01', '09:05', null], ['2026-01-02', '09:00', 4]]);
assert.deepEqual([fiveMinutes[0].open, fiveMinutes[0].high, fiveMinutes[0].low, fiveMinutes[0].close], [10, 12, 10, 12]);
assert.equal(engine.aggregateBars(minutes, '60').length, 2);
assert.equal(engine.aggregateBars(minutes, '60')[0].volume, null);

// 등차수열의 EMA와 MACD는 손으로 구한 SMA 시작값·정상상태와 일치한다.
const linear = Array.from({ length: 65 }, (_, index) => bar(index + 1, index));
const derived = engine.indicators(linear);
assert(derived.slice(0, 19).every(row => row.ema20 === null));
near(derived[19].ema20, 10.5);
near(derived[20].ema20, 11.5);
assert(derived.slice(0, 49).every(row => row.ema50 === null));
near(derived[49].ema50, 25.5);
near(derived[50].ema50, 26.5);
assert.equal(derived[24].macd, null);
near(derived[25].macd, 7);
assert.equal(derived[32].macdSignal, null);
near(derived[33].macdSignal, 7);
near(derived[33].macdHistogram, 0);
assert(derived.slice(0, 14).every(row => row.rsi === null));
near(derived[14].rsi, 100);
assert(derived.slice(0, 9).every(row => row.atr === null && row.supertrend === null && row.supertrendDirection === null));

// Wilder의 대표 RSI 표와 연속 손실·보합 경계값을 검증한다.
const wilderCloses = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64, 46.21];
const wilder = engine.indicators(wilderCloses.map((close, index) => bar(close, index)));
near(wilder[14].rsi, 70.46413502109705);
near(wilder[15].rsi, 66.24961855355505);
near(wilder[20].rsi, 62.8807183099624);
near(engine.indicators(Array.from({ length: 16 }, (_, index) => bar(20 - index, index)))[15].rsi, 0);
near(engine.indicators(Array.from({ length: 16 }, (_, index) => bar(10, index)))[15].rsi, 50);

// 실제 범위에는 전일 종가의 갭이 포함되고, 첫 ATR 뒤에는 Wilder 평균을 적용한다.
const gapBars = [
    bar(10, 0, { high: 11, low: 9 }),
    bar(12, 1, { high: 13, low: 11 }),
    bar(11, 2, { high: 12, low: 10 }),
    bar(15, 3, { high: 16, low: 14 })
];
const atrRows = engine.indicators(gapBars, { atrPeriod: 3 });
assert.equal(atrRows[1].atr, null);
near(atrRows[2].atr, 7 / 3);
near(atrRows[3].atr, 29 / 9);

// Supertrend 밴드 유지·상승 전환·하락 전환을 독립적인 간단 수치로 확인한다.
const trend = engine.indicators([
    bar(10, 0, { high: 11, low: 9 }),
    bar(14, 1, { high: 15, low: 13 }),
    bar(13, 2, { high: 14, low: 12 }),
    bar(8, 3, { high: 9, low: 7 })
], { atrPeriod: 1, atrMultiplier: 1 });
assert.deepEqual(trend.map(row => row.supertrendDirection), ['down', 'up', 'up', 'down']);
assert.deepEqual(trend.map(row => row.supertrend), [12, 9, 11, 14]);

// 거래량 가중 분산·사용자 앵커·결측 뒤의 계산 중단을 검증한다.
const weighted = [bar(10, 0, { volume: 1 }), bar(20, 1, { volume: 3 }), bar(30, 2, { volume: 0 })];
const avwap = engine.indicators(weighted);
near(avwap[1].avwap, 17.5);
near(avwap[1].avwapUpper, 17.5 + Math.sqrt(18.75));
near(avwap[1].avwapLower, 17.5 - Math.sqrt(18.75));
near(avwap[2].avwap, 17.5);
near(engine.indicators([bar(9, 0, { high: 15, low: 6, volume: 1 }), bar(18, 1, { high: 24, low: 12, volume: 1 })])[1].avwap, 14);
const anchored = engine.indicators(weighted, { anchorIndex: 1 });
assert.equal(anchored[0].avwap, null);
near(anchored[1].avwap, 20);
assert(engine.indicators(weighted, { anchorIndex: 100 }).every(row => row.avwap === null));
const volumeGap = engine.indicators([bar(10, 0), bar(20, 1, { volume: null }), bar(30, 2)]);
near(volumeGap[0].avwap, 10);
assert.equal(volumeGap[1].avwap, null);
assert.equal(volumeGap[2].avwap, null);
assert.equal(engine.indicators([bar(10, 0, { volume: 0 })])[0].avwap, null);

// OHLCV 추정 매물대는 각 봉 거래량을 가격 중첩 구간에 비례 배분하며 총량을 보존한다.
const profileBars = [
    bar(15, 0, { open: 10, low: 10, high: 20, volume: 100 }),
    bar(10, 1, { low: 10, high: 15, volume: 50 }),
    bar(20, 2, { volume: 20 })
];
const profile = engine.volumeProfile(profileBars, { bins: 2, valueArea: 0.7 });
assert.equal(profile.method, 'ohlcv-estimate');
assert.equal(profile.totalVolume, 170);
assert.equal(profile.coverage, 1);
assert.deepEqual(profile.bins, [{ low: 10, high: 15, volume: 100 }, { low: 15, high: 20, volume: 70 }]);
near(profile.poc, 12.5);
assert.equal(profile.val, 10);
assert.equal(profile.vah, 20);
const denseProfile = engine.volumeProfile(profileBars, { bins: 37 });
near(denseProfile.bins.reduce((sum, bin) => sum + bin.volume, 0), 170);
const partialProfile = engine.volumeProfile([bar(10, 0, { volume: 5 }), bar(20, 1, { volume: null })]);
near(partialProfile.coverage, 0.5);
near(partialProfile.totalVolume, 5);
assert.deepEqual(partialProfile.bins, [{ low: 10, high: 10, volume: 5 }]);
assert.equal(engine.volumeProfile([bar(10, 0, { volume: null })]).poc, null);
assert.equal(engine.volumeProfile([bar(10, 0, { volume: 0 })]).poc, null);
assert.equal(engine.volumeProfile([]).coverage, 0);

// 극값은 우측 lookback개 봉이 있어야 확정되며, 패턴은 목선 돌파 뒤에만 나타난다.
const patternCloses = [90, 92, 95, 100, 96, 93, 90, 89, 92, 95, 99, 95, 92, 88, 87, 86, 85];
const patternBars = patternCloses.map((close, index) => bar(close, index));
assert.equal(engine.pivots(patternBars.slice(0, 6)).highs.length, 0);
assert.deepEqual(engine.pivots(patternBars.slice(0, 7)).highs, [{ index: 3, value: 100, confirmedIndex: 6 }]);
assert.deepEqual(engine.detectPatterns(patternBars.slice(0, 13)), []);
const patterns = engine.detectPatterns(patternBars);
assert.deepEqual(patterns, [{ type: 'double-top', label: '이중 천장', index: 10, confirmedIndex: 13, level: 89 }]);
assert.deepEqual(engine.detectPatterns(patternCloses.map((close, index) => bar(200 - close, index))), [{ type: 'double-bottom', label: '이중 바닥', index: 10, confirmedIndex: 13, level: 111 }]);

// 재생 시점까지의 계산은 미래 봉을 추가해도 변하지 않는다.
for (let length = 1; length <= linear.length; length += 1) {
    assert.deepEqual(engine.indicators(linear.slice(0, length)), derived.slice(0, length));
}
for (let length = 1; length <= patternBars.length; length += 1) {
    const replayPatterns = engine.detectPatterns(patternBars.slice(0, length));
    assert(replayPatterns.every(pattern => pattern.confirmedIndex < length));
    assert.deepEqual(replayPatterns, patterns.filter(pattern => pattern.confirmedIndex < length));
}

// 복합 조건은 null을 숫자 0으로 해석하지 않고 교차의 이전 값도 확인한다.
const conditionRows = [{ close: 10, rsi: 49, macdHistogram: null }, { close: 11, rsi: 51, macdHistogram: null }];
const priceUp = { field: 'close', operator: 'crossesAbove', value: 10 };
const rsiUp = { field: 'rsi', operator: 'above', value: 50 };
const noMacd = { field: 'macdHistogram', operator: 'below', value: 1 };
assert.equal(engine.evaluateConditions(conditionRows, [priceUp, rsiUp]).matched, true);
assert.equal(engine.evaluateConditions(conditionRows, [priceUp, noMacd]).matched, false);
assert.equal(engine.evaluateConditions(conditionRows, [priceUp, noMacd]).available, false);
assert.equal(engine.evaluateConditions(conditionRows, [priceUp, noMacd], 'any').matched, true);
assert.equal(engine.evaluateConditions(conditionRows, [noMacd]).available, false);
assert.equal(engine.evaluateConditions(conditionRows.slice(1), [priceUp]).available, false);
assert.equal(engine.evaluateConditions(conditionRows, [{ field: 'rsi', operator: 'crossesBelow', value: 50 }]).matched, false);
assert.equal(engine.evaluateConditions(conditionRows.reverse(), [{ field: 'rsi', operator: 'crossesBelow', value: 50 }]).matched, true);
assert.equal(engine.evaluateConditions([], []).matched, false);
assert.equal(engine.evaluateConditions(conditionRows, [{ field: 'secret', operator: 'above', value: 0 }]).available, false);

// CSV의 결측 셀은 공란, 지표는 이용 가능한 열만 포함하며 수식 주입을 막는다.
const csv = engine.toCSV(derived);
assert(csv.startsWith('date,time,open,high,low,close,volume,ema20,ema50,rsi,mfi,macd,macdSignal,macdHistogram,atr,supertrend,supertrendDirection,avwap,avwapUpper,avwapLower\r\n'));
const initialCells = csv.split('\r\n')[1].split(',');
assert.equal(initialCells[7], '');
assert.equal(initialCells[10], '');
assert(engine.toCSV([bar(10, 0)]).split('\r\n')[0] === 'date,time,open,high,low,close,volume');
assert(engine.toCSV(derived, { bom: true }).startsWith('\uFEFFdate'));
const malicious = engine.toCSV([{ date: '=HYPERLINK("https://example.com")', time: '@SUM(1)', close: 10, volume: null }]);
assert(malicious.includes('"\'=HYPERLINK(""https://example.com"")"'));
assert(malicious.includes("'@SUM(1)"));

console.log('기술적 분석 엔진: 수치·집계·거래량·패턴·재생·조건·CSV 검증 통과');

// MFI의 거래량 가중치, 예열·결측 복구와 영거래량을 독립 수치로 확인한다.
const mfiFixture = [bar(10, 0), bar(12, 1, { volume: 2 }), bar(11, 2, { volume: 3 }), bar(13, 3, { volume: 4 })];
const mfiValues = engine.indicators(mfiFixture, { mfiPeriod: 3 });
assert.equal(mfiValues[2].mfi, null);
near(mfiValues[3].mfi, 100 * (24 + 52) / (24 + 52 + 33));
const flat = Array.from({ length: 18 }, (_, i) => bar(10, i, { volume: 0 }));
near(engine.indicators(flat)[14].mfi, 50);
const rising = Array.from({ length: 32 }, (_, i) => bar(10 + i, i));
near(engine.indicators(rising)[14].mfi, 100);
near(engine.indicators(rising.slice().reverse().map((r, i) => bar(r.close, i)))[14].mfi, 0);
rising[15].volume = null;
const missingMfi = engine.indicators(rising);
assert.equal(missingMfi[15].mfi, null);
assert.equal(missingMfi[28].mfi, null);
near(missingMfi[29].mfi, 100);
near(engine.indicators(mfiFixture.slice(0, 3), { mfiPeriod: 2 })[2].mfi, engine.indicators(mfiFixture, { mfiPeriod: 2 })[2].mfi);
