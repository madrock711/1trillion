'use strict';

const assert = require('assert');
const live = require('../assets/market-live-data.js');

const priceXml = [
    '<protocol>',
    '<chartdata>',
    '<item data="20260806|6250.10|6320.50|6230.25|6305.40|1234567" />',
    '<item data="20260807|6310.00|6388.20|6290.75|6375.15|1456789" />',
    '</chartdata>',
    '</protocol>'
].join('');

const priceRows = live.normalizeKospiPriceHistory(priceXml);
assert.strictEqual(priceRows.length, 2);
assert.deepStrictEqual(priceRows[0], {
    date: '2026-08-06',
    open: 6250.1,
    high: 6320.5,
    low: 6230.25,
    close: 6305.4,
    volume: 1234567
});

const flowHtml = [
    '<table>',
    '<tr><td class="date2">26.08.07</td><td>1,100</td><td class="rate_up">2,350</td><td>-3,450</td></tr>',
    '<tr><td class="date2">26.08.06</td><td>-900</td><td class="rate_down">-1,250</td><td>2,150</td></tr>',
    '</table>'
].join('');

const flowRows = live.normalizeKospiForeignFlowHtml(flowHtml);
assert.strictEqual(flowRows.length, 2);
assert.strictEqual(flowRows[0].date, '2026-08-06');
assert.strictEqual(flowRows[0].foreign, -1250);
assert.strictEqual(flowRows[1].foreign, 2350);

const merged = live.mergeKospiTechnicalHistory(priceRows, flowRows);
assert.strictEqual(merged.length, 2);
assert.strictEqual(merged[0].foreign, -1250);
assert.strictEqual(merged[1].foreign, 2350);
assert.strictEqual(merged[1].volume, 1456789);

const closeValues = Array.from({ length: 80 }, (_, index) => 100 + index * 2);
const macd = live.calculateMacd(closeValues, 12, 26, 9);
assert.strictEqual(macd.macd.length, closeValues.length);
assert.strictEqual(macd.signal.length, closeValues.length);
assert.strictEqual(macd.histogram.length, closeValues.length);
assert.ok(Number.isFinite(macd.macd[79]));
assert.ok(Number.isFinite(macd.signal[79]));
assert.ok(macd.macd[79] > 0);

console.log('KOSPI price, foreign-flow merge, and MACD tests passed.');
