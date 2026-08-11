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

assert.strictEqual(live.liveRefreshDelay(closed), null, '정규장 마감 뒤 자동 갱신 타이머를 중단해야 한다.');
assert.strictEqual(live.liveRefreshDelay(open), 60000, '장중에는 1분 갱신을 유지해야 한다.');
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
const html = fs.readFileSync(path.join(__dirname, '../articles/market.html'), 'utf8');
assert.ok(dashboard.includes('if (!shouldPollLiveData(latestLiveData)) return;'), '마감 뒤 예약 타이머 생성 자체를 막아야 한다.');
assert.ok(dashboard.includes('liveSignature === lastAppliedLiveSignature'), '같은 데이터의 SVG 재생성을 막아야 한다.');
assert.ok(!dashboard.includes('5 * 60 * 1000'), '마감 뒤 5분 재렌더 경로가 남으면 안 된다.');
assert.ok(html.includes('market-live-data.js?v=20260811-2'));
assert.ok(html.includes('market-dashboard.js?v=20260811-19'));

console.log('Market live refresh policy tests passed.');
