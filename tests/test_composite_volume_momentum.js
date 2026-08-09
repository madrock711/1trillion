'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const live = require('../assets/market-live-data.js');

function timeFor(index) {
    const total = 9 * 60 + index;
    return String(Math.floor(total / 60)).padStart(2, '0') + ':' + String(total % 60).padStart(2, '0');
}

function pressureDay(date, ratios) {
    let cvd = 0;
    return {
        date,
        sourceLastAt: date + 'T15:30:00+09:00',
        bars: ratios.map((ratio, index) => {
            const volume = 1000;
            const delta = Math.round(volume * ratio);
            cvd += delta;
            return {
                time: timeFor(index), open: 100, high: 101, low: 99, close: 100,
                volume, delta, cumulativeDelta: cvd,
                estimatedBuyVolume: (volume + delta) / 2,
                estimatedSellVolume: (volume - delta) / 2
            };
        })
    };
}

(async function run() {
    assert.strictEqual(typeof live.estimateBvcPressureDays, 'function');
    assert.strictEqual(typeof live.calculateCompositeVolumeMomentum, 'function');
    assert.strictEqual(typeof live.fetchKospiMinutePressureDays, 'function');

    const ratios = Array(40).fill(-0.12).concat(Array(40).fill(0.28));
    const kospi = [pressureDay('2026-08-07', ratios)];
    const kodex = [pressureDay('2026-08-07', ratios)];
    const composite = live.calculateCompositeVolumeMomentum(kospi, kodex);
    assert.strictEqual(composite.length, 1);
    assert.strictEqual(composite[0].bars.length, 80);
    assert(composite[0].bars[79].direction > 0, 'same-sign buy pressure should produce a positive direction');
    assert(composite[0].bars[79].momentum > 0, 'a sell-to-buy transition should produce positive momentum');

    const kospiStable = [pressureDay('2026-08-07', Array(80).fill(0.1))];
    const kodexAccelerating = [pressureDay('2026-08-07', Array(50).fill(0.1).concat(Array(30).fill(0.75)))];
    const divergence = live.calculateCompositeVolumeMomentum(kospiStable, kodexAccelerating)[0].bars;
    assert(divergence[79].divergence > 0, 'KODEX acceleration should produce a positive KODEX-minus-KOSPI divergence');

    const baseKospi = [pressureDay('2026-08-07', ratios.slice(0, 70))];
    const baseKodex = [pressureDay('2026-08-07', ratios.slice(0, 70))];
    const before = live.calculateCompositeVolumeMomentum(baseKospi, baseKodex)[0].bars;
    const after = live.calculateCompositeVolumeMomentum(
        [pressureDay('2026-08-07', ratios.slice(0, 70).concat([1]))],
        [pressureDay('2026-08-07', ratios.slice(0, 70).concat([-1]))]
    )[0].bars;
    assert.deepStrictEqual(
        before.map(row => [row.direction, row.momentum, row.signal, row.divergence]),
        after.slice(0, 70).map(row => [row.direction, row.momentum, row.signal, row.divergence]),
        'future bars must not change previously calculated scores'
    );

    const minutePayload = [
        { localDateTime: '20260807090000', openPrice: 100, highPrice: 101, lowPrice: 99, currentPrice: 100, accumulatedTradingVolume: 1000 },
        { localDateTime: '20260807090100', openPrice: 100, highPrice: 102, lowPrice: 100, currentPrice: 101, accumulatedTradingVolume: 1200 },
        { localDateTime: '20260807090200', openPrice: 101, highPrice: 102, lowPrice: 100, currentPrice: 100.5, accumulatedTradingVolume: 1300 }
    ];
    const requested = [];
    const fetched = await live.fetchKospiMinutePressureDays(async url => {
        requested.push(url);
        return { ok: true, json: async () => minutePayload };
    }, 'https://example.test/market-data/', ['2026-08-07'], { forceRefresh: true });
    assert.strictEqual(fetched.length, 1);
    assert.strictEqual(fetched[0].bars.length, 3);
    assert(requested[0].includes('startDateTime=202608070900'));
    assert(Number.isFinite(fetched[0].bars[1].delta));

    const partialRequested = [];
    const partial = await live.fetchKospiMinutePressureDays(async url => {
        partialRequested.push(url);
        const missing = url.includes('202607300900');
        return { ok: true, json: async () => missing ? [] : minutePayload };
    }, 'https://partial.example.test/market-data/', ['2026-07-30', '2026-08-07'], { forceRefresh: true });
    assert.strictEqual(partialRequested.length, 2);
    assert.strictEqual(partial.length, 1, 'missing older KOSPI minutes must not discard overlapping sessions');
    assert.strictEqual(partial[0].date, '2026-08-07');

    const html = fs.readFileSync(path.join(__dirname, '..', 'articles', 'market.html'), 'utf8');
    const dashboard = fs.readFileSync(path.join(__dirname, '..', 'assets', 'market-dashboard.js'), 'utf8');
    const css = fs.readFileSync(path.join(__dirname, '..', 'assets', 'market-dashboard.css'), 'utf8');
    assert(html.includes('data-technical-card="composite-momentum"'));
    assert(html.includes('id="composite-momentum-chart"'));
    assert(html.includes('viewBox="0 0 1000 350"'));
    assert(!html.includes('합성 매수 방향'));
    assert(!html.includes('합성 매도 방향'));
    assert(html.includes('실제 Bid/Ask 체결 분류는 아닙니다'));
    assert(dashboard.includes("'kospi-flow',\n        'kodex-history',\n        'composite-momentum',\n        'tqqq-history'"));
    assert(dashboard.includes("document.querySelector('.kodex-range-card .kodex-range-track')"));
    assert(!dashboard.includes("'class': 'composite-direction-line"));
    assert(!dashboard.includes("'class': 'composite-divergence-line"));
    assert(css.includes('.composite-momentum-card'));
    console.log('composite volume momentum tests passed');
}()).catch(error => {
    console.error(error);
    process.exitCode = 1;
});
