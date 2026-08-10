'use strict';

var assert = require('assert');
var fs = require('fs');
var path = require('path');
var live = require('../assets/market-live-data.js');

var archivePath = path.join(__dirname, '..', 'assets', 'data', 'kodex-volume-pressure.json');
var archive = JSON.parse(fs.readFileSync(archivePath, 'utf8'));
var normalized = live.normalizeKodexVolumePressure(archive);
var intradayIndexPath = path.join(__dirname, '..', 'assets', 'data', 'kodex-intraday-index.json');
var intradayIndex = live.normalizeKodexIntradayIndex(JSON.parse(fs.readFileSync(intradayIndexPath, 'utf8')));

assert.ok(normalized.length >= 6, 'archive should retain at least the initial six validated sessions');
var dates = normalized.map(function (row) { return row.date; });
var rawDates = archive.days.map(function (row) { return row.date; });
assert.strictEqual(normalized.length, archive.days.length, 'every archived row should normalize successfully');
assert.strictEqual(new Set(rawDates).size, rawDates.length, 'archive dates should be unique');
assert.deepStrictEqual(rawDates, rawDates.slice().sort(), 'archive dates should remain ascending');
['2026-07-29', '2026-07-30', '2026-07-31', '2026-08-03', '2026-08-04', '2026-08-05'].forEach(function (date) {
    assert.ok(dates.indexOf(date) !== -1, 'initial session is missing: ' + date);
});
normalized.forEach(function (row) {
    assert.strictEqual(row.estimatedBuyVolume + row.estimatedSellVolume, row.dailyVolume);
    assert.ok(Math.abs(row.buyShare + row.sellShare - 1) <= 0.00001);
    assert.ok(Math.abs(row.buyShare - row.estimatedBuyVolume / row.dailyVolume) <= 0.000002);
    assert.ok(Math.abs(row.sellShare - row.estimatedSellVolume / row.dailyVolume) <= 0.000002);
    assert.ok(Math.abs(row.coverageRatio - row.minuteVolume / row.dailyVolume) <= 0.000002);
});

assert.ok(intradayIndex.length >= 7, 'the initial available minute sessions should remain archived');
[
    '2026-07-29', '2026-07-30', '2026-07-31', '2026-08-03', '2026-08-04', '2026-08-05', '2026-08-06'
].forEach(function (date) {
    assert.ok(intradayIndex.some(function (row) { return row.date === date; }), 'intraday session is missing: ' + date);
});
intradayIndex.forEach(function (entry) {
    var dayPath = path.join(__dirname, '..', 'assets', 'data', entry.path);
    var day = live.normalizeKodexIntradayDay(JSON.parse(fs.readFileSync(dayPath, 'utf8')));
    assert.strictEqual(day.date, entry.date);
    assert.strictEqual(day.bars.length, entry.minuteBars);
    day.bars.forEach(function (bar) {
        assert.strictEqual(bar.estimatedBuyVolume + bar.estimatedSellVolume, bar.volume);
        assert.strictEqual(bar.estimatedBuyVolume - bar.estimatedSellVolume, bar.delta);
    });
});

var liveDay = live.normalizeKodexLiveIntradayDay([
    { localDateTime: '20260807090000', openPrice: 100, highPrice: 101, lowPrice: 99, currentPrice: 100, accumulatedTradingVolume: 1000 },
    { localDateTime: '20260807090100', openPrice: 100, highPrice: 103, lowPrice: 100, currentPrice: 102, accumulatedTradingVolume: 800 }
], '2026-08-07', 1, 300);
assert.strictEqual(liveDay.date, '2026-08-07');
assert.strictEqual(liveDay.bars.length, 2);
assert.strictEqual(liveDay.bars[0].delta, 0, 'opening minute should remain neutral');
assert.ok(liveDay.bars[1].delta > 0, 'rising live minute should show buy pressure');
assert.strictEqual(liveDay.bars[1].estimatedBuyVolume + liveDay.bars[1].estimatedSellVolume, 800);

var tqqqIntraday = live.normalizeTqqqIntradayHistory(JSON.stringify({
    chart: {
        result: [{
            timestamp: [1786109400, 1786109700, 1786110000],
            indicators: { quote: [{
                open: [70, 70, 71], high: [71, 72, 74], low: [69, 70, 71], close: [70, 71, 73], volume: [1000, 800, 900]
            }] }
        }]
    }
}), 5);
assert.strictEqual(tqqqIntraday.length, 1);
assert.strictEqual(tqqqIntraday[0].interval, 5);
assert.strictEqual(tqqqIntraday[0].bars.length, 3);
assert.strictEqual(tqqqIntraday[0].bars[2].estimatedBuyVolume + tqqqIntraday[0].bars[2].estimatedSellVolume, 900);

var koreaBaseTimestamp = Math.floor(Date.parse('2026-08-10T00:00:00Z') / 1000);
var koreanWarmup = live.normalizeKoreanYahooIntradayHistory(JSON.stringify({
    chart: {
        result: [{
            timestamp: [koreaBaseTimestamp, koreaBaseTimestamp + 300, koreaBaseTimestamp + 600],
            indicators: { quote: [{
                open: [100, 100, 102], high: [101, 103, 103], low: [99, 100, 100], close: [100, 102, 101], volume: [1000, 900, 800]
            }] }
        }]
    }
}), 5, 'KODEX');
assert.strictEqual(koreanWarmup[0].date, '2026-08-10');
assert.strictEqual(koreanWarmup[0].bars[0].time, '09:00');
assert.strictEqual(koreanWarmup[0].bars[2].time, '09:10');
assert.strictEqual(koreanWarmup[0].bars[2].estimatedBuyVolume + koreanWarmup[0].bars[2].estimatedSellVolume, 800);

var history = [
    { date: '2026-07-28', open: 1, high: 2, low: 1, close: 2, volume: 500 },
    { date: normalized[0].date, open: 1, high: 2, low: 1, close: 2, volume: normalized[0].dailyVolume }
];
var merged = live.mergeKodexVolumePressure(history, normalized);
assert.strictEqual(merged[0].volumePressure, undefined, 'older history should retain the legacy bar');
assert.strictEqual(merged[1].volumePressure.date, normalized[0].date, 'matching day should receive the estimate');
assert.strictEqual(history[1].volumePressure, undefined, 'merge should not mutate source history');

var mismatched = live.mergeKodexVolumePressure([
    { date: normalized[0].date, open: 1, high: 2, low: 1, close: 2, volume: 1 }
], normalized);
assert.strictEqual(mismatched[0].volumePressure, undefined, 'large daily-volume mismatch should fall back to legacy');

console.log('KODEX volume-pressure browser data tests passed.');
