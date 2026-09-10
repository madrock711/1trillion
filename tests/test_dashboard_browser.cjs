// Full-page regression: real production data, with optional local JS/CSS overrides.
// PLAYWRIGHT_MODULE can point to the bundled Playwright package on this machine.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
(async () => {
    const browser = await chromium.launch({ channel: 'chrome', headless: true });
    try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', message => {
            if (message.type() === 'error' && message.text().includes('초기화 실패')) errors.push(message.text());
        });
        if (process.env.DASHBOARD_LOCAL === '1') {
            await page.route(/\/assets\/market-dashboard\.(js|css)(\?|$)/, route => {
                const name = new URL(route.request().url()).pathname.split('/').pop();
                return route.fulfill({ path: path.join(root, 'assets', name), contentType: name.endsWith('.js') ? 'text/javascript' : 'text/css' });
            });
        }
        await page.route(/googlesyndication|doubleclick|googletagmanager|google-analytics/, route => route.abort());
        await page.goto('https://www.hpmplab.com/articles/market.html?view=technical', { waitUntil: 'commit', timeout: 60000 });
        const ids = ['kospi-flow-chart', 'kodex-history-chart', 'composite-momentum-chart', 'tqqq-history-chart'];
        async function charts(mode) {
            for (const id of ids) {
                await page.locator('#' + id).scrollIntoViewIfNeeded();
                await page.waitForFunction(id => document.getElementById(id).querySelectorAll('path,line,rect').length > 30, id, { timeout: 90000 });
            }
            console.log(mode, await page.locator('svg[id]').evaluateAll(els => els.map(e => ({ id: e.id, shapes: e.querySelectorAll('path,line,rect').length }))));
            assert.deepEqual(errors, [], 'Full page must initialize without errors');
        }
        await charts('daily');
        if (await page.locator('[data-analytics-consent="denied"]').isVisible()) {
            await page.locator('[data-analytics-consent="denied"]').click();
        }
        await page.locator('[data-kodex-chart-mode="intraday"]').click();
        await page.waitForFunction(() => ['kospi-flow-chart', 'kodex-history-chart', 'composite-momentum-chart', 'tqqq-history-chart'].every(id => document.getElementById(id).classList.contains('is-intraday')), null, { timeout: 90000 });
        await charts('intraday');
        const screenshotDir = path.join(root, 'docs/screenshot');
        fs.mkdirSync(screenshotDir, { recursive: true });
        await page.locator('#kospi-flow-chart').scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(screenshotDir, 'dashboard-restored.png') });
        for (const width of [280, 390, 768, 1280]) {
            await page.setViewportSize({ width, height: 900 });
            const overflow = await page.locator('.market-checkpoint-list li').evaluateAll(els => els.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent));
            assert.deepEqual(overflow, [], `Checkpoint overflow at ${width}px`);
        }
        await page.setViewportSize({ width: 280, height: 900 });
        await page.locator('.market-checkpoint-panel').scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(screenshotDir, 'dashboard-checkpoints-280.png') });
        console.log('Full page, daily/intraday charts and checkpoint widths passed');
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
