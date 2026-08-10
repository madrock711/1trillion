'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const live = require('../assets/market-live-data.js');

const archiveIndex = [
    { date: '2026-08-06', path: 'kodex-intraday/2026-08-06.json', minuteBars: 391 },
    { date: '2026-08-07', path: 'kodex-intraday/2026-08-07.json', minuteBars: 391 }
];

const preopenIndex = live.ensureCurrentIntradayIndex(
    archiveIndex,
    '2026-08-10',
    'PREOPEN',
    null,
    Date.parse('2026-08-10T08:30:00+09:00')
);
assert.deepStrictEqual(preopenIndex.map((row) => row.date), ['2026-08-06', '2026-08-07', '2026-08-10']);
assert.strictEqual(preopenIndex[2].live, true);
assert.strictEqual(preopenIndex[2].pending, true);
assert.strictEqual(preopenIndex[2].minuteBars, 0, '장전부터 오늘 날짜를 선택할 수 있어야 한다.');
assert.strictEqual(preopenIndex[2].path, '', '장전 항목을 보존 파일로 오인하면 안 된다.');

const closedIndex = live.ensureCurrentIntradayIndex(archiveIndex, '2026-08-10', 'CLOSE', null);
assert.deepStrictEqual(closedIndex.map((row) => row.date), ['2026-08-06', '2026-08-07'], '휴장 상태에는 가짜 오늘 항목을 만들면 안 된다.');

const firstLiveDay = live.normalizeKodexLiveIntradayDay([
    { localDateTime: '20260810090000', openPrice: 90605, highPrice: 91660, lowPrice: 90480, currentPrice: 90605, accumulatedTradingVolume: 207894 }
], '2026-08-10', 125, 300);
assert.strictEqual(firstLiveDay.bars.length, 1, '09:00 첫 봉 하나도 즉시 표시해야 한다.');
assert.strictEqual(firstLiveDay.bars[0].delta, 0, '첫 봉은 기준 가격이 없어 중립으로 처리해야 한다.');

const openIndex = live.ensureCurrentIntradayIndex(
    archiveIndex,
    '2026-08-10',
    'OPEN',
    firstLiveDay,
    Date.parse('2026-08-10T09:00:30+09:00')
);
assert.strictEqual(openIndex[2].minuteBars, 1);
assert.strictEqual(openIndex[2].pending, false);

const rolledRuntimeIndex = live.mergeRuntimeIntradayIndex(
    archiveIndex.concat([{ date: '2026-08-10', path: '', live: true, pending: false }]),
    archiveIndex.concat([{ date: '2026-08-11', path: '', live: true, pending: true }])
);
assert.deepStrictEqual(
    rolledRuntimeIndex.map((row) => row.date),
    ['2026-08-06', '2026-08-07', '2026-08-11'],
    '새 거래일 응답에는 이전 path 없는 live placeholder가 남으면 안 된다.'
);
assert.strictEqual(
    live.intradaySourceDate('2026-08-07T15:30:00+09:00', '2026-08-10'),
    '2026-08-07',
    '장전 연결 상태는 선택한 오늘이 아니라 실제 수급 기준 거래일을 써야 한다.'
);

const previousDay = {
    date: '2026-08-07',
    sourceLastAt: '2026-08-07T15:30:00+09:00',
    bars: [
        { time: '09:00', open: 1, high: 2, low: 1, close: 2, volume: 10, estimatedBuyVolume: 5, estimatedSellVolume: 5, delta: 0 },
        { time: '09:01', open: 2, high: 3, low: 2, close: 3, volume: 20, estimatedBuyVolume: 15, estimatedSellVolume: 5, delta: 10 },
        { time: '09:02', open: 3, high: 3, low: 2, close: 2, volume: 30, estimatedBuyVolume: 10, estimatedSellVolume: 20, delta: -10 },
        { time: '09:03', open: 2, high: 4, low: 2, close: 4, volume: 40, estimatedBuyVolume: 30, estimatedSellVolume: 10, delta: 20 }
    ]
};
const rollingPreopen = live.buildRollingIntradayDay(previousDay, null, '2026-08-10');
assert.strictEqual(rollingPreopen.bars.length, 4);
assert.strictEqual(rollingPreopen.currentBarCount, 0);
assert.ok(rollingPreopen.bars.every((bar) => bar.date === '2026-08-07'));

const rollingOpen = live.buildRollingIntradayDay(previousDay, firstLiveDay, '2026-08-10');
assert.strictEqual(rollingOpen.bars.length, 5);
assert.strictEqual(rollingOpen.previousBarCount, 4);
assert.strictEqual(rollingOpen.currentBarCount, 1);
assert.strictEqual(rollingOpen.bars[3].sessionDate, '2026-08-07');
assert.strictEqual(rollingOpen.bars[4].sessionDate, '2026-08-10');

const dashboard = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.css'), 'utf8');
assert.ok(dashboard.includes("var bucketKey = sessionDate + '|' + bucket"), '서로 다른 거래일의 같은 시각 봉을 합치면 안 된다.');
assert.ok(dashboard.includes('rows.slice(-previousCount)'), '전일 한 세션 폭을 유지하며 왼쪽 봉이 밀려나야 한다.');
assert.ok(dashboard.includes('previousArchivedIntradayEntry(indexRows, selectedKodexIntradayDate)'), '오늘 보기에는 직전 보존 거래일을 연결해야 한다.');
assert.ok(dashboard.includes("formatHistoryDate(date) + ' · 오늘 장전'"), '장전 오늘 라벨이 유지되어야 한다.');
assert.ok(dashboard.includes("row && row.path"), '장전 placeholder를 합성 모멘텀 원자료로 요청하면 안 된다.');
assert.ok(dashboard.includes('MarketDashboardLive.intradaySourceDate(cached.flowSourceLastAt, selectedDate)'), '장전 수급 기준일은 전 거래일 실제 날짜를 표시해야 한다.');
assert.ok(dashboard.includes('MarketDashboardLive.mergeRuntimeIntradayIndex('), '날짜 목록 병합은 회귀 테스트 가능한 helper를 사용해야 한다.');
assert.ok(css.includes('.intraday-session-divider'), '두 거래일의 경계를 차트에서 구분해야 한다.');

console.log('Intraday current-session continuity tests passed.');
