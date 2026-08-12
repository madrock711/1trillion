'use strict';

var assert = require('assert');
var fs = require('fs');
var path = require('path');
var live = require('../assets/market-live-data.js');
var liveSource = fs.readFileSync(path.join(__dirname, '../assets/market-live-data.js'), 'utf8');
assert.ok(liveSource.includes('return fetchKospiIntradayArchiveDay(indexUrl, day, fetchImpl'), '취소된 저장본 요청은 원격 가격 함수가 아니라 저장본 함수로 재시작해야 한다.');

var root = path.join(__dirname, '..');
var indexPath = path.join(root, 'assets', 'data', 'kospi-intraday-index.json');
var indexRows = live.normalizeKospiIntradayArchiveIndex(JSON.parse(fs.readFileSync(indexPath, 'utf8')));

assert.ok(indexRows.length >= 6, '최근 완료 KOSPI 분봉 저장본이 누적되어야 한다.');
assert.deepStrictEqual(indexRows.map(function (row) { return row.date; }), indexRows.map(function (row) { return row.date; }).slice().sort());

indexRows.forEach(function (entry) {
    var dayPath = path.join(root, 'assets', 'data', entry.path);
    var day = live.normalizeKospiIntradayArchiveDay(JSON.parse(fs.readFileSync(dayPath, 'utf8')));
    assert.strictEqual(day.date, entry.date);
    assert.strictEqual(day.bars.length, entry.minuteBars);
    assert.strictEqual(day.bars[0].time, '09:00');
    assert.strictEqual(day.bars[day.bars.length - 1].time, '15:30');
    assert.ok(day.bars.every(function (bar) { return bar.date === day.date; }));
    if (entry.flowSnapshotCount > 0) {
        var observed = Array.from(new Set(day.bars.map(function (bar) {
            return bar.flowObservedAt || '';
        }).filter(Boolean))).sort();
        assert.ok(day.bars.some(function (bar) { return Number.isFinite(bar.foreign); }));
        assert.ok(observed.length >= 150, '불완전한 과거 수급 저장본을 사용하면 안 된다.');
        assert.ok(observed[0] <= '09:10');
        assert.ok(observed[observed.length - 1] >= '15:25');
    }
});

function makeSession(date, count) {
    return Array.from({ length: count }, function (_, index) {
        return { date: date, sessionDate: date, time: '09:' + String(index).padStart(2, '0'), close: index };
    });
}

var completed = makeSession('2026-08-10', 10).concat(makeSession('2026-08-11', 10));
var firstLive = completed.concat(makeSession('2026-08-12', 1));
var secondLive = completed.concat(makeSession('2026-08-12', 2));
var firstWindow = live.stableIntradayWindow(firstLive, '2026-08-12', 2);
var secondWindow = live.stableIntradayWindow(secondLive, '2026-08-12', 2);
assert.strictEqual(firstWindow.length, 20, '새 첫 봉이 들어와도 표시 봉 수가 늘어나면 안 된다.');
assert.strictEqual(secondWindow.length, 20, '새 봉이 추가될 때 기존 차트 폭이 유지되어야 한다.');
assert.strictEqual(firstWindow[firstWindow.length - 1].date, '2026-08-12');
assert.strictEqual(secondWindow[0].date, '2026-08-10', '새 봉 수만큼 왼쪽 오래된 봉만 밀려나야 한다.');

console.log('KOSPI intraday archive and stable-window tests passed.');
