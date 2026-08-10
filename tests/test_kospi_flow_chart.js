'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const live = require('../assets/market-live-data.js');

async function main() {
    const dashboardSource = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
    const dashboardCss = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.css'), 'utf8');
    const marketHtml = fs.readFileSync(path.join(__dirname, '../articles/market.html'), 'utf8');
    assert.ok(
        dashboardSource.includes("calculateMacd(history.map(function (row) { return row.foreign; })"),
        'KOSPI 일봉 MACD는 종가가 아니라 외국인 순매수에 연결되어야 한다.'
    );
    assert.ok(dashboardSource.includes('fetchKospiIntradayDay('), 'KOSPI 분봉 수급 fetch 연결이 유지되어야 한다.');
    assert.ok(dashboardSource.includes("marketStatus === 'OPEN'"), '개장 중 당일 분봉은 실시간으로 표시되어야 한다.');
    assert.ok(dashboardSource.includes("formatHistoryDate(date) + ' · 오늘 실시간'"), '당일 실시간 날짜 라벨이 있어야 한다.');
    assert.ok(dashboardSource.includes("formatHistoryDate(date) + ' · 마감'"), '이전 거래일은 보관된 마감 차트로 표시되어야 한다.');
    assert.ok(dashboardSource.includes('preferredIntradayDate(indexRows, selectedKodexIntradayDate, selectedKodexIntradayDateExplicit)'), '새로고침 기본값은 오늘을 고르되 명시적으로 고른 이전 거래일은 유지해야 한다.');
    assert.ok(dashboardSource.includes('kospi-flow-volume-force'), 'KOSPI 거래량 X-ray 채움이 유지되어야 한다.');
    assert.ok(dashboardSource.includes('kospi-flow-cvd'), 'KOSPI 누적 순압력 CVD가 유지되어야 한다.');
    assert.ok(dashboardSource.includes('kospiIntradayViewCache'), '자동 갱신 중 기존 KOSPI 분봉 차트를 유지해야 한다.');
    assert.ok(dashboardSource.includes('kospiIntradayAbortController.abort()'), '날짜 전환 시 이전 KOSPI 분봉 요청을 취소해야 한다.');
    assert.ok(dashboardSource.includes("'분봉 수급 불러오기 중단 · 다시 시도'"), '분봉 요청 timeout 뒤 새로고침 상태를 복구해야 한다.');
    assert.ok(dashboardSource.includes("setKospiFlowRefreshState('ready', latestDaily"), '일봉 전환 뒤 새로고침 버튼을 다시 활성화해야 한다.');
    assert.ok(dashboardSource.includes("volumeGroup.setAttribute('aria-label', volumeLabel)"), '거래량 X-ray 묶음에 접근 가능한 설명이 있어야 한다.');
    assert.ok(dashboardSource.includes("if (title) title.textContent = 'KOSPI';"), 'KOSPI 카드 제목은 모드가 바뀌어도 한 줄로 유지되어야 한다.');
    assert.ok(dashboardSource.includes("if (title) title.textContent = 'KODEX 레버리지';"), 'KODEX 카드 제목은 모드가 바뀌어도 한 줄로 유지되어야 한다.');
    assert.ok(dashboardSource.includes("if (title) title.textContent = 'TQQQ';"), 'TQQQ 카드 제목은 모드가 바뀌어도 한 줄로 유지되어야 한다.');
    assert.ok(dashboardSource.includes("selectedKodexIntradayInterval + '분'"), 'KOSPI 분봉 간격은 짧은 분 표기를 사용해야 한다.');
    assert.ok(dashboardSource.includes("interval + '분'"), 'KODEX와 TQQQ 분봉 간격은 짧은 분 표기를 사용해야 한다.');
    assert.ok(dashboardCss.includes('.kospi-flow-foreign.is-buy { fill: #ffb454; }'), '외국인 순매수는 X-ray와 구별되는 색이어야 한다.');
    assert.ok(dashboardCss.includes('.kospi-flow-foreign.is-sell { fill: #35d3c8; }'), '외국인 순매도는 X-ray와 구별되는 색이어야 한다.');
    assert.ok(dashboardCss.includes('.kospi-flow-readout'), 'KOSPI 상세 수치에는 전용 높이 규칙이 있어야 한다.');
    assert.ok(dashboardCss.includes('block-size: calc(0.76rem * 1.55 * 2)'), '데스크톱 상세 수치 높이는 두 줄로 고정되어야 한다.');
    assert.ok(dashboardCss.includes('overflow-y: auto'), '고정 높이를 넘는 상세 수치는 영역 안에서 읽을 수 있어야 한다.');
    assert.ok(dashboardCss.includes('scrollbar-gutter: stable'), '스크롤바 출현으로 수치 줄바꿈 폭이 달라지지 않아야 한다.');
    assert.ok(marketHtml.includes('data-shared-intraday-date'), 'KOSPI와 KODEX의 분봉 거래일 선택이 동기화되어야 한다.');
    assert.ok(marketHtml.includes('수급 MACD'), '공개 범례는 수급 MACD임을 명시해야 한다.');
    assert.ok(marketHtml.includes('id="kospi-flow-title">KOSPI</h3>'), 'KOSPI 카드에는 종목명 한 줄만 표시해야 한다.');
    assert.ok(marketHtml.includes('id="kodex-history-title">KODEX 레버리지</h3>'), 'KODEX 카드에는 종목명 한 줄만 표시해야 한다.');
    assert.ok(marketHtml.includes('id="tqqq-history-title">TQQQ</h3>'), 'TQQQ 카드에는 종목명 한 줄만 표시해야 한다.');
    assert.ok(!marketHtml.includes('id="kospi-flow-eyebrow"'), 'KOSPI 중복 분류 문구를 다시 넣으면 안 된다.');
    assert.ok(!marketHtml.includes('id="kospi-flow-method"'), 'KOSPI 사용법 설명을 카드 상단에 다시 넣으면 안 된다.');
    assert.ok(!marketHtml.includes('id="kodex-history-eyebrow"'), 'KODEX 중복 분류 문구를 다시 넣으면 안 된다.');
    assert.ok(!marketHtml.includes('id="tqqq-history-eyebrow"'), 'TQQQ 중복 분류 문구를 다시 넣으면 안 된다.');
    assert.ok(!marketHtml.includes('class="kodex-history-method"'), '가격 차트 카드의 반복 설명을 다시 넣으면 안 된다.');
    assert.ok(marketHtml.includes('class="kodex-chart-refresh-anchor kospi-flow-refresh-anchor"'), 'KOSPI 새로고침은 카드 최상단 앵커에 있어야 한다.');

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

    const foreignFlowValues = Array.from({ length: 80 }, (_, index) => -8000 + index * 250);
    const foreignFlowMacd = live.calculateMacd(foreignFlowValues, 12, 26, 9);
    assert.strictEqual(foreignFlowMacd.macd.length, foreignFlowValues.length);
    assert.strictEqual(foreignFlowMacd.signal.length, foreignFlowValues.length);
    assert.strictEqual(foreignFlowMacd.histogram.length, foreignFlowValues.length);
    assert.ok(Number.isFinite(foreignFlowMacd.macd[79]));
    assert.ok(Number.isFinite(foreignFlowMacd.signal[79]));
    assert.ok(foreignFlowMacd.macd[79] > 0, '외국인 누적 순매수 개선 모멘텀은 양의 MACD여야 한다.');

    const minutePayload = [
        { localDateTime: '20260807085900', currentPrice: 99, openPrice: 99, highPrice: 100, lowPrice: 98, accumulatedTradingVolume: 9 },
        { localDateTime: '20260807090000', currentPrice: 100, openPrice: 99, highPrice: 101, lowPrice: 98, accumulatedTradingVolume: 10 },
        { localDateTime: '20260807090100', currentPrice: 101, openPrice: 100, highPrice: 102, lowPrice: 99, accumulatedTradingVolume: 11 },
        { localDateTime: '20260807090200', currentPrice: 102, openPrice: 101, highPrice: 103, lowPrice: 100, accumulatedTradingVolume: 12 },
        { localDateTime: '20260807090300', currentPrice: 103, openPrice: 102, highPrice: 104, lowPrice: 101, accumulatedTradingVolume: 13 },
        { localDateTime: '20260807090400', currentPrice: 102, openPrice: 103, highPrice: 104, lowPrice: 101, accumulatedTradingVolume: 14 },
        { localDateTime: '20260807090500', currentPrice: 104, openPrice: 102, highPrice: 105, lowPrice: 101, accumulatedTradingVolume: 15 },
        { localDateTime: '20260807153100', currentPrice: 105, openPrice: 104, highPrice: 106, lowPrice: 103, accumulatedTradingVolume: 16 },
        { localDateTime: '20260808090000', currentPrice: 106, openPrice: 105, highPrice: 107, lowPrice: 104, accumulatedTradingVolume: 17 }
    ];
    const intradayPriceRows = live.normalizeKospiIntradayMinute(JSON.stringify(minutePayload), '2026-08-07');
    assert.strictEqual(intradayPriceRows.length, 6);
    assert.strictEqual(intradayPriceRows[0].time, '09:00');
    assert.strictEqual(intradayPriceRows[5].time, '09:05');

    const intradayFlowPage1 = [
        '<table>',
        '<tr><td class="date2">15:31</td><td>500</td><td>600</td><td>-1,100</td></tr>',
        '<tr><td class="date2">09:05</td><td>-100</td><td>400</td><td>-300</td></tr>',
        '<tr><td class="date2">09:03</td><td>-50</td><td>250</td><td>-200</td></tr>',
        '</table>',
        '<a href="/sise/investorDealTrendTime.nhn?bizdate=20260807&amp;sosok=01&amp;page=1">1</a>',
        '<a href="/sise/investorDealTrendTime.nhn?bizdate=20260807&amp;sosok=01&amp;page=2">2</a>'
    ].join('');
    const intradayFlowPage2 = [
        '<table>',
        '<tr><td class="date2">09:01</td><td>-25</td><td>100</td><td>-75</td></tr>',
        '<tr><td class="date2">08:59</td><td>0</td><td>0</td><td>0</td></tr>',
        '</table>',
        '<a href="/sise/investorDealTrendTime.nhn?bizdate=20260807&amp;sosok=01&amp;page=1">1</a>',
        '<a href="/sise/investorDealTrendTime.nhn?bizdate=20260807&amp;sosok=01&amp;page=2">2</a>'
    ].join('');

    assert.strictEqual(live.extractKospiIntradayForeignFlowPageCount(intradayFlowPage1), 2);
    const flowPage1Rows = live.normalizeKospiIntradayForeignFlowHtml(intradayFlowPage1, '2026-08-07');
    const flowPage2Rows = live.normalizeKospiIntradayForeignFlowHtml(intradayFlowPage2, '2026-08-07');
    assert.deepStrictEqual(flowPage1Rows.map((row) => row.time), ['09:03', '09:05']);
    assert.strictEqual(flowPage2Rows.length, 1);
    assert.strictEqual(flowPage2Rows[0].foreign, 100);

    const intradayMerged = live.mergeKospiIntradayForeignFlow(
        intradayPriceRows,
        flowPage1Rows.concat(flowPage2Rows)
    );
    assert.strictEqual(intradayMerged[0].foreign, null, '최초 발표 전 09:00 수급을 추정하면 안 된다.');
    assert.strictEqual(intradayMerged[1].foreign, 100);
    assert.strictEqual(intradayMerged[2].foreign, 100);
    assert.strictEqual(intradayMerged[2].flowObservedAt, '09:01');
    assert.strictEqual(intradayMerged[2].flowCarriedForward, true);
    assert.strictEqual(intradayMerged[3].foreign, 250);
    assert.strictEqual(intradayMerged[3].flowCarriedForward, false);
    assert.strictEqual(intradayMerged[5].foreign, 400);

    const calls = [];
    const fetchStub = async (url) => {
        const parsed = new URL(url);
        calls.push(parsed.pathname + parsed.search);
        if (parsed.pathname.endsWith('/minute')) {
            return { ok: true, json: async () => minutePayload };
        }
        if (parsed.pathname.endsWith('/foreign-flow-time')) {
            const page = parsed.searchParams.get('page');
            return { ok: true, text: async () => page === '2' ? intradayFlowPage2 : intradayFlowPage1 };
        }
        return { ok: false };
    };
    const fetchOptions = { now: Date.parse('2026-08-07T16:00:00+09:00'), ttlMs: 60000 };
    const intradayDay = await live.fetchKospiIntradayDay(
        fetchStub,
        'https://example.test/market-data/',
        '2026-08-07',
        fetchOptions
    );
    assert.strictEqual(intradayDay.date, '2026-08-07');
    assert.strictEqual(intradayDay.interval, '1m');
    assert.strictEqual(intradayDay.flowPageCount, 2);
    assert.strictEqual(intradayDay.flowSnapshotCount, 3);
    assert.strictEqual(intradayDay.bars.length, 6);
    assert.strictEqual(intradayDay.bars[2].foreign, 100);
    assert.strictEqual(intradayDay.bars[4].flowObservedAt, '09:03');
    assert.strictEqual(intradayDay.minuteVolume, 75);
    assert.strictEqual(calls.length, 3, '가격 1회와 수급 2페이지를 모두 요청해야 한다.');
    await live.fetchKospiIntradayDay(
        fetchStub,
        'https://example.test/market-data/',
        '2026-08-07',
        fetchOptions
    );
    assert.strictEqual(calls.length, 3, 'TTL 안에서는 선택 거래일 결과를 캐시해야 한다.');

    const manyPageLinks = Array.from({ length: 12 }, (_, index) => (
        '<a href="/sise/investorDealTrendTime.nhn?bizdate=20260807&amp;sosok=01&amp;page=' + (index + 1) + '">' + (index + 1) + '</a>'
    )).join('');
    const manyPageFlowHtml = [
        '<table><tr><td class="date2">09:01</td><td>-25</td><td>100</td><td>-75</td></tr></table>',
        manyPageLinks
    ].join('');
    let activeRequests = 0;
    let maxActiveRequests = 0;
    const concurrencyFetch = async (url) => {
        activeRequests += 1;
        maxActiveRequests = Math.max(maxActiveRequests, activeRequests);
        await new Promise((resolve) => setTimeout(resolve, 2));
        activeRequests -= 1;
        const parsed = new URL(url);
        if (parsed.pathname.endsWith('/minute')) return { ok: true, json: async () => minutePayload };
        if (parsed.pathname.endsWith('/foreign-flow-time')) return { ok: true, text: async () => manyPageFlowHtml };
        return { ok: false };
    };
    const concurrentDay = await live.fetchKospiIntradayDay(
        concurrencyFetch,
        'https://concurrency.test/market-data/',
        '2026-08-07',
        { now: Date.parse('2026-08-07T16:01:00+09:00'), ttlMs: 60000, concurrencyLimit: 4 }
    );
    assert.strictEqual(concurrentDay.flowPageCount, 12);
    assert.ok(maxActiveRequests <= 4, '장중 수급 페이지 요청은 설정한 동시성 한도를 넘으면 안 된다.');

    const firstController = new AbortController();
    const secondController = new AbortController();
    let abortRetryCalls = 0;
    const abortRetryFetch = (url, options) => {
        abortRetryCalls += 1;
        const parsed = new URL(url);
        if (options.signal === firstController.signal) {
            return new Promise((resolve, reject) => {
                const abort = () => {
                    const error = new Error('aborted');
                    error.name = 'AbortError';
                    reject(error);
                };
                if (options.signal.aborted) abort();
                else options.signal.addEventListener('abort', abort, { once: true });
            });
        }
        if (parsed.pathname.endsWith('/minute')) return Promise.resolve({ ok: true, json: async () => minutePayload });
        if (parsed.pathname.endsWith('/foreign-flow-time')) {
            const page = parsed.searchParams.get('page');
            return Promise.resolve({ ok: true, text: async () => page === '2' ? intradayFlowPage2 : intradayFlowPage1 });
        }
        return Promise.resolve({ ok: false });
    };
    const abortedRequest = live.fetchKospiIntradayDay(
        abortRetryFetch,
        'https://abort-retry.test/market-data/',
        '2026-08-07',
        { now: Date.parse('2026-08-07T16:02:00+09:00'), signal: firstController.signal }
    ).catch((error) => error.name);
    firstController.abort();
    const retriedDay = await live.fetchKospiIntradayDay(
        abortRetryFetch,
        'https://abort-retry.test/market-data/',
        '2026-08-07',
        { now: Date.parse('2026-08-07T16:02:01+09:00'), signal: secondController.signal }
    );
    assert.strictEqual(await abortedRequest, 'AbortError');
    assert.strictEqual(retriedDay.bars.length, 6, '취소 직후 같은 날짜를 다시 요청해도 새 응답을 받아야 한다.');
    assert.ok(abortRetryCalls >= 5, '취소된 pending 요청을 재사용하지 않고 가격·수급을 다시 요청해야 한다.');

    console.log('KOSPI daily/intraday price, foreign-flow merge, cache, and foreign-flow MACD tests passed.');
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
