'use strict';

const assert = require('assert');
const live = require('../assets/market-live-data.js');

function response(payload) {
    return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(payload)
    });
}

const kospiBasic = {
    itemCode: 'KOSPI',
    localTradedAt: '2026-08-12T09:05:00+09:00',
    closePrice: '6420',
    openPrice: '6400',
    highPrice: '6430',
    lowPrice: '6390',
    fluctuationsRatio: '0.85',
    compareToPreviousPrice: { code: '2' },
    marketStatus: 'OPEN'
};
const kospiIntegration = {
    totalInfos: [
        { code: 'lastClosePrice', value: '6366' },
        { code: 'accumulatedTradingVolume', value: '120000' },
        { code: 'accumulatedTradingValue', value: '4500000' }
    ],
    dealTrendInfo: { bizdate: '20260812', foreignValue: '120', institutionalValue: '-30', personalValue: '-90' },
    upDownStockInfo: { upperCount: '0', riseCount: '500', steadyCount: '50', lowerCount: '0', fallCount: '300' },
    programTrendInfo: { indexDifferenceReal: '10', indexBiDifferenceReal: '20', indexTotalReal: '30' }
};
const kodexBasic = {
    itemCode: '122630',
    localTradedAt: '2026-08-12T09:05:00+09:00',
    closePrice: '92000',
    openPrice: '91000',
    highPrice: '92500',
    lowPrice: '90500',
    fluctuationsRatio: '1.1',
    compareToPreviousPrice: { code: '2' },
    marketStatus: 'OPEN'
};
const kodexIntegration = {
    totalInfos: [
        { code: 'lastClosePrice', value: '91000' },
        { code: 'accumulatedTradingVolume', value: '10000' }
    ],
    dealTrendInfos: []
};
const pressurePayload = {
    schemaVersion: 1,
    symbol: '122630',
    days: [{
        date: '2026-08-11', dailyVolume: 1000, minuteVolume: 1000,
        estimatedBuyVolume: 550, estimatedSellVolume: 450,
        buyShare: 0.55, sellShare: 0.45, coverageRatio: 1,
        minuteBars: 381, sigma: 125, sigmaSampleSize: 300,
        method: 'bvc-normal-1m-v1'
    }]
};
const indexPayload = {
    schemaVersion: 1,
    symbol: '122630',
    days: [{
        date: '2026-08-11', path: 'kodex-intraday/2026-08-11.json',
        minuteBars: 381, coverageRatio: 1,
        sourceLastAt: '2026-08-11T15:30:00+09:00',
        collectedAt: '2026-08-11T16:00:00+09:00'
    }]
};
const minutePayload = [{
    localDateTime: '20260812090000', openPrice: 91000, highPrice: 91200,
    lowPrice: 90900, currentPrice: 91100, accumulatedTradingVolume: 500
}];

function fakeFetch(url) {
    if (url.includes('/index/KOSPI/basic')) return response(kospiBasic);
    if (url.includes('/index/KOSPI/integration')) return response(kospiIntegration);
    if (url.includes('/stock/122630/basic')) return response(kodexBasic);
    if (url.includes('/stock/122630/integration')) return response(kodexIntegration);
    if (url.includes('/stock/122630/minute')) return response(minutePayload);
    if (url.includes('kodex-volume-pressure.json')) return response(pressurePayload);
    if (url.includes('kodex-intraday-index.json')) return response(indexPayload);
    throw new Error('Unexpected URL ' + url);
}

live.fetchCurrentSession('https://example.test/market-data/', fakeFetch, {
    now: Date.parse('2026-08-12T09:05:30+09:00'),
    volumePressureUrl: 'https://example.test/assets/data/kodex-volume-pressure.json',
    intradayIndexUrl: 'https://example.test/assets/data/kodex-intraday-index.json'
}).then((result) => {
    assert.strictEqual(result.markets[0].sessionDate, '2026-08-12');
    assert.strictEqual(result.markets[0].marketStatus, 'OPEN');
    assert.strictEqual(result.instruments[0].liveIntradayDay.date, '2026-08-12');
    assert.strictEqual(result.instruments[0].liveIntradayDay.bars.length, 1);
    assert.deepStrictEqual(
        result.instruments[0].intradayIndex.map((row) => row.date),
        ['2026-08-11', '2026-08-12'],
        '무거운 이력 요청 전에도 당일 거래일을 즉시 추가해야 한다.'
    );
    console.log('Current-session prime tests passed.');
}).catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
