// 결정적 OHLCV 시나리오로 고급 차트의 실제 DOM·사용 흐름을 검증한다.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
const server = http.createServer((req, res) => {
    const name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const target = path.resolve(root, '.' + name);
    if (!target.startsWith(root + path.sep) || !fs.existsSync(target) || !fs.statSync(target).isFile()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': mime[path.extname(target)] || 'application/octet-stream' });
    fs.createReadStream(target).pipe(res);
});
function fixture() {
    const rows = [];
    const day = new Date('2026-01-01T00:00:00Z');
    for (let i = 0; i < 180; i++) {
        while ([0, 6].includes(day.getUTCDay())) day.setUTCDate(day.getUTCDate() + 1);
        const open = 100 + i * .4 + Math.sin(i / 4) * 4;
        rows.push({ date: day.toISOString().slice(0, 10), open, high: open + 3, low: open - 2, close: open + 1, volume: 1000 + i * 10 });
        day.setUTCDate(day.getUTCDate() + 1);
    }
    return rows;
}
(async () => {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const browser = await chromium.launch({ channel: 'chrome', headless: true });
    try {
        const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
        const rows = fixture();
        await context.addInitScript(rows => {
            window.TechnicalAnalysisContexts = {};
            ['KODEX', 'KOSPI', 'TQQQ'].forEach(symbol => {
                window.TechnicalAnalysisContexts[symbol + ':daily'] = { symbol, mode: 'daily', interval: 1, bars: rows };
                window.TechnicalAnalysisContexts[symbol + ':intraday'] = { symbol, mode: 'intraday', interval: 5, bars: rows.slice(0, 78).map((r, i) => ({ ...r, date: '2026-10-12', time: String(9 + Math.floor(i * 5 / 60)).padStart(2, '0') + ':' + String(i * 5 % 60).padStart(2, '0') })) };
            });
        }, rows);
        await context.route('**/*', route => {
            const url = new URL(route.request().url());
            if (url.pathname.endsWith('/market-dashboard.js')) return route.fulfill({ contentType: 'text/javascript', body: '' });
            if (url.hostname !== '127.0.0.1') return route.abort();
            return route.continue();
        });
        const page = await context.newPage(); const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        const url = `http://127.0.0.1:${server.address().port}/articles/market.html?view=technical`;
        async function ready() {
            await page.goto(url, { waitUntil: 'domcontentloaded' });
            await page.evaluate(() => {
                document.documentElement.classList.add('market-dashboard-enhanced');
                document.querySelectorAll('[data-view-panel]').forEach(p => { p.hidden = p.dataset.viewPanel !== 'technical'; });
                document.getElementById('market-view-technical').classList.add('is-active');
            });
            await page.waitForFunction(() => document.querySelectorAll('#tw-chart rect').length > 30);
        }
        await ready();
        assert.match(await page.locator('#tw-readout').innerText(), /RSI/);
        assert.equal(await page.locator('#tw-timeframes tbody tr').count(), 3);
        await page.locator('#tw-timeframe').selectOption('weekly');
        await page.waitForFunction(() => document.getElementById('tw-data-note').textContent.includes('주봉'));
        await page.locator('#tw-timeframe').selectOption('native');
        await page.locator('#tw-chart-type').selectOption('heikin');
        await page.waitForFunction(() => document.getElementById('tw-data-note').textContent.includes('변환 가격'));
        await page.locator('#tw-scale').selectOption('log');
        await page.locator('#tw-oscillator').selectOption('macd');
        await page.locator('#tw-replay-start').click();
        await page.waitForFunction(() => document.getElementById('tw-replay-status').textContent.includes('90 / 180'));
        assert(!await page.locator('#tw-readout').innerText().then(t => t.includes(rows.at(-1).date)), '미래 봉은 읽기값에 없어야 한다');
        const downloadPromise = page.waitForEvent('download'); await page.locator('#tw-export').click();
        const download = await downloadPromise;
        const stream = await download.createReadStream(); const chunks = [];
        for await (const chunk of stream) chunks.push(chunk);
        const csv = Buffer.concat(chunks).toString('utf8');
        assert.equal(csv.trim().split('\n').length, 91, '재생 CSV에 미래 데이터가 없어야 한다');
        assert(csv.includes('rsi') && csv.includes('avwap'), '계산값도 내보낸다');
        await page.locator('#tw-replay-step').click();
        await page.waitForFunction(() => document.getElementById('tw-replay-status').textContent.includes('91 / 180'));
        await page.locator('#tw-replay-end').click();
        await page.waitForFunction(() => document.getElementById('tw-replay-range').disabled);
        await page.locator('#tw-tool').selectOption('horizontal');
        await page.locator('#tw-chart').focus(); await page.keyboard.press('End'); await page.keyboard.press('Enter');
        await page.waitForFunction(() => document.querySelectorAll('#tw-chart .tw-user-line').length === 1);
        await page.locator('#tw-undo').click();
        await page.waitForFunction(() => document.querySelectorAll('#tw-chart .tw-user-line').length === 0);
        await page.locator('#tw-tool').selectOption('fib'); await page.locator('#tw-chart').focus();
        await page.keyboard.press('Home'); await page.keyboard.press('Enter'); await page.keyboard.press('End'); await page.keyboard.press('Enter');
        await page.waitForFunction(() => document.querySelectorAll('#tw-chart .tw-user-line').length === 7);
        await page.locator('#tw-tool').selectOption('anchor'); await page.locator('#tw-chart').focus();
        await page.keyboard.press('Home'); await page.keyboard.press('Enter');
        await page.waitForFunction(() => document.getElementById('tw-anchor').value !== '');
        // 알림은 갱신 전후 조건이 바뀔 때만 발생한다.
        await page.locator('.tw-details').first().locator('summary').click();
        await page.locator('[data-condition-operator]').selectOption('above');
        await page.locator('[data-condition-value]').fill(String(rows.at(-1).close + 2));
        await page.locator('#tw-alert-form button[type=submit]').click();
        assert.match(await page.locator('#tw-alert-count').innerText(), /1개/);
        const update = rows.map(r => ({ ...r })); update.at(-1).close += 10; update.at(-1).high += 10;
        await page.evaluate(bars => {
            const detail = { symbol: 'KODEX', mode: 'daily', interval: 1, bars };
            window.TechnicalAnalysisContexts['KODEX:daily'] = detail;
            window.dispatchEvent(new CustomEvent('technical-analysis-data', { detail }));
        }, update);
        assert.match(await page.locator('#tw-alert-status').innerText(), /충족/);
        await page.locator('.tw-details').nth(1).locator('summary').click();
        await page.locator('#tw-template-name').fill('추세와 매물대'); await page.locator('#tw-template-form button').click();
        assert.match(await page.locator('#tw-template-status').innerText(), /저장했습니다/);
        await ready();
        assert.match(await page.locator('#tw-alert-count').innerText(), /1개/, '저장 알림 복구');
        assert.equal(await page.locator('#tw-chart-type').inputValue(), 'heikin', '설정 복구');
        assert.equal(await page.locator('#tw-chart .tw-user-line').count(), 7, '그리기 복구');
        await page.locator('#tw-mode').selectOption('intraday');
        await page.waitForFunction(() => document.getElementById('tw-data-note').textContent.includes('5분봉'));
        assert.deepEqual(await page.locator('#tw-timeframe option').evaluateAll(nodes => nodes.map(n => n.value)), ['native', '15', '30', '60']);
        await page.locator('#tw-timeframe').selectOption('15');
        await page.waitForFunction(() => document.getElementById('tw-data-note').textContent.includes('15분봉'));
        for (const width of [280, 390, 768, 1440]) {
            await page.setViewportSize({ width, height: 1000 });
            const overflow = await page.locator('#technical-workbench').evaluate(e => e.scrollWidth - e.clientWidth);
            assert(overflow <= 1, `워크벤치 가로 넘침 ${width}px: ${overflow}`);
        }
        // 터치 스와이프는 차트를 움직이고, 별도의 탭만 선을 그려야 한다.
        await page.setViewportSize({ width: 390, height: 1000 });
        await page.locator('#tw-tool').selectOption('horizontal');
        await page.locator('#tw-chart').scrollIntoViewIfNeeded();
        const box = await page.locator('#tw-chart').boundingBox();
        const touchY = Math.max(180, Math.min(800, box.y + 150));
        const session = await context.newCDPSession(page);
        await session.send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 1 });
        await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 310, y: touchY }] });
        for (let x = 290; x >= 80; x -= 30) {
            await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: touchY }] });
            await page.waitForTimeout(20);
        }
        await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
        await page.waitForFunction(() => document.querySelector('.tw-chart-shell').scrollLeft > 100);
        assert.equal(await page.locator('#tw-chart .tw-user-line').count(), 0, '스와이프는 그리기를 실행하지 않는다');
        await page.waitForTimeout(150);
        await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 160, y: touchY }] });
        await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
        await page.waitForFunction(() => document.querySelectorAll('#tw-chart .tw-user-line').length === 1);
        await session.detach();
        assert.deepEqual(errors, [], '모든 조작과 저장 복구에 JS 오류가 없어야 한다');
        // 저장 차단도 작업 전체를 깨뜨리지 않고 알린다.
        await page.evaluate(() => { Storage.prototype.setItem = function () { throw new Error('blocked'); }; });
        await page.locator('.tw-details').nth(1).locator('summary').click();
        await page.locator('#tw-template-name').fill('저장 실패'); await page.locator('#tw-template-form button').click();
        assert.match(await page.locator('#tw-template-status').innerText(), /현재 화면에서만/);
        console.log('technical workbench browser: calculations, replay/CSV, keyboard drawings, alerts, persistence and responsive widths passed');
    } finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
