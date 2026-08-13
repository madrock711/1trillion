'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const live = require('../assets/market-live-data.js');

const closed = {
    markets: [
        { id: 'KOSPI', marketStatus: 'CLOSE', asOf: '2026-08-11T18:59:00+09:00' },
        { id: 'KOSDAQ', marketStatus: 'CLOSE', asOf: '2026-08-11T18:59:00+09:00' }
    ],
    partial: false,
    retrievedAt: '2026-08-11T19:00:00+09:00'
};
const open = {
    markets: [{ id: 'KOSPI', marketStatus: 'OPEN', asOf: '2026-08-11T10:00:00+09:00' }],
    partial: false
};

const usOpen = Date.parse('2026-08-13T10:00:00-04:00');
const usClosed = Date.parse('2026-08-13T17:00:00-04:00');
assert.strictEqual(live.isUsRegularMarketOpen(usOpen), true, '미국 동부 09:30~16:00은 TQQQ 자동 갱신 시간이어야 한다.');
assert.strictEqual(live.isUsRegularMarketOpen(usClosed), false, '미국 정규장 마감 뒤에는 TQQQ 자동 갱신을 중단해야 한다.');
assert.strictEqual(live.liveRefreshDelay(closed, usClosed), null, '한국장과 미국장이 모두 마감되면 자동 갱신 타이머를 중단해야 한다.');
assert.strictEqual(live.liveRefreshDelay(closed, usOpen), 60000, '한국장 마감 뒤에도 미국 정규장 중에는 1분 갱신을 유지해야 한다.');
assert.strictEqual(live.liveRefreshDelay(open, usClosed), 60000, '한국 장중에는 1분 갱신을 유지해야 한다.');
assert.strictEqual(
    live.liveObservationSignature(closed),
    live.liveObservationSignature(Object.assign({}, closed, { retrievedAt: '2026-08-11T19:05:00+09:00' })),
    '조회 시각만 달라진 동일 응답은 차트를 다시 그리면 안 된다.'
);
assert.strictEqual(
    live.shouldRefreshLiveDataOnAttention(closed, Date.parse('2026-08-11T20:00:00+09:00')),
    false,
    '같은 거래일 마감 뒤 포커스 복귀만으로 갱신하면 안 된다.'
);
assert.strictEqual(
    live.shouldRefreshLiveDataOnAttention(closed, Date.parse('2026-08-12T08:30:00+09:00')),
    true,
    '다음 날짜에 페이지로 돌아오면 새 거래일 확인은 허용해야 한다.'
);

const dashboard = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const liveSource = fs.readFileSync(path.join(__dirname, '../assets/market-live-data.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '../articles/market.html'), 'utf8');
assert.ok(dashboard.includes('if (!shouldPollLiveData(latestLiveData)) return;'), '마감 뒤 예약 타이머 생성 자체를 막아야 한다.');
assert.ok(dashboard.includes('liveSignature === lastAppliedLiveSignature'), '같은 데이터의 SVG 재생성을 막아야 한다.');
assert.ok(!dashboard.includes('5 * 60 * 1000'), '마감 뒤 5분 재렌더 경로가 남으면 안 된다.');
assert.ok(html.includes('id="tqqq-chart-refresh"'), 'TQQQ 카드에 독립 새로고침 버튼이 있어야 한다.');
assert.ok(dashboard.includes('refreshTqqqLiveData({ force: true, reportError: true })'), 'TQQQ 버튼은 다른 국내 데이터를 거치지 않고 TQQQ만 강제 갱신해야 한다.');
assert.ok(dashboard.includes("if (usRegularMarketActive() && !domesticMarketActive(latestLiveData))"), '미국장만 열렸을 때 TQQQ 전용 폴링 경로를 사용해야 한다.');
assert.ok(liveSource.includes('fetchTqqqLatest: fetchTqqqLatest'), 'TQQQ 독립 데이터 요청 함수를 공개해야 한다.');
assert.ok(liveSource.includes('usRegularMarketOpen ? 60 * 1000 : 15 * 60 * 1000'), '미국 정규장 중 TQQQ 1분봉 캐시는 1분이어야 한다.');
assert.ok(liveSource.includes('usRegularMarketOpen ? 5 * 60 * 1000 : 15 * 60 * 1000'), '미국 정규장 중 TQQQ 5분 원자료 캐시는 5분이어야 한다.');
assert.ok(html.includes('market-live-data.js?v=20260813-01'));
assert.ok(html.includes('market-dashboard.js?v=20260813-01'));

console.log('Market live refresh policy tests passed.');
