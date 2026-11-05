// Explicit production QA only: a short-lived synthetic owner session arrives
// via stdin, never argv, disk or logs. The Python driver revokes it in finally.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
let stage = 'start';
(async () => {
    const fixture = JSON.parse(fs.readFileSync(0, 'utf8'));
    const browser = await chromium.launch({ channel: 'chrome', headless: true });
    try {
        const context = await browser.newContext();
        await context.addCookies([{ name: '__Host-yeonma_session', value: fixture.token,
            domain: 'www.hpmplab.com', path: '/', secure: true, httpOnly: true, sameSite: 'Lax',
            expires: Math.floor(Date.now()/1000) + 600 }]);
        if (fixture.mode === '--run-nh-backend') {
            stage = 'real NH backend request';
            const response = await context.request.get('https://www.hpmplab.com/api/private/nh/session/flow', { timeout: 30000 });
            console.log('NH backend HTTP:', response.status());
            assert.equal(response.status(), 200);
            const data = await response.json();
            assert(data.source === 'NH PLUG' && data.amount.length > 0 && data.quantity.length > 0);
            console.log('NH backend verified:', JSON.stringify({ amountRows: data.amount.length, quantityRows: data.quantity.length, fetchedAt: data.fetchedAt }));
            await new Promise(r => setTimeout(r, 5500));
            const again = await context.request.get('https://www.hpmplab.com/api/private/nh/session/flow', { timeout: 30000 });
            assert.equal(again.status(), 200);
            assert.equal((await again.json()).fetchedAt, data.fetchedAt, 'warm request reuses server flow cache');
            console.log('Second request reused the flow cache.');
            return;
        }
        const page = await context.newPage();
        page.on('response', response => {
            if (new URL(response.url()).pathname.startsWith('/api/private/nh/session/')) {
                console.log('Session QA response:', new URL(response.url()).pathname.split('/').at(-1), response.status());
            }
        });
        stage = 'initial restoration';
        await page.goto('https://www.hpmplab.com/articles/market.html?view=technical&sessionqa=20261105', { waitUntil: 'domcontentloaded' });
        await page.locator('#kodex-private-signout').waitFor({ state: 'visible', timeout: 20000 });
        assert(!(await page.evaluate(() => document.cookie)).includes('__Host-yeonma_session'));
        if (fixture.mode === '--run-nh-chart') {
            stage = 'NH amount and quantity chart overlays';
            await page.locator('[data-kodex-chart-mode="intraday"]').click();
            for (const mode of ['amount', 'quantity']) {
                await page.waitForTimeout(5500);
                await page.locator('[data-kodex-flow="' + mode + '"]').click();
                await page.waitForFunction(() => {
                    const legend = document.querySelector('#kodex-flow-legend');
                    const status = document.querySelector('#kodex-flow-status');
                    return legend && !legend.hidden && status && status.textContent.includes('NH PLUG')
                        && document.querySelectorAll('#kodex-history-chart .kodex-flow-line').length >= 3;
                }, null, { timeout: 35000 });
                assert.match(await page.locator('#kodex-flow-status').innerText(), /NH PLUG/);
                console.log('LIVE NH chart overlay rendered:', mode, 'three investor lines');
            }
            await page.locator('#kodex-history-chart').screenshot({ path: process.env.NH_CHART_SCREENSHOT || require('node:path').join(require('node:os').tmpdir(), 'yeonma-nh-online-chart.png') });
            return;
        }
        stage = 'reload restoration';
        await page.reload({ waitUntil: 'domcontentloaded' });
        await page.locator('#kodex-private-signout').waitFor({ state: 'visible', timeout: 20000 });
        // Session JSON must never be cached and anonymous clients must not see it.
        stage = 'anonymous denial';
        const anonymous = await browser.newContext();
        const unauth = await anonymous.request.get('https://www.hpmplab.com/api/private/nh/session/state');
        assert.equal(unauth.status(), 401);
        await anonymous.close();
        stage = 'server logout';
        await page.waitForTimeout(5500); // Respect the existing 0.2 requests/sec API throttle.
        await page.locator('#kodex-private-signout').click();
        await page.locator('#kodex-private-signin').waitFor({ state: 'visible', timeout: 20000 });
        stage = 'post-logout restoration';
        await page.reload({ waitUntil: 'domcontentloaded' });
        await page.locator('#kodex-private-signin').waitFor({ state: 'visible', timeout: 20000 });
        assert(await page.locator('#kodex-private-signout').isHidden());
        stage = 'revoked-cookie replay';
        await page.waitForTimeout(5500);
        const replay = await context.request.get('https://www.hpmplab.com/api/private/nh/session/state', {
            headers: { Cookie: '__Host-yeonma_session=' + fixture.token }
        });
        assert.equal(replay.status(), 401);
        console.log('LIVE synthetic session: refresh restored, HttpOnly protected, anonymous denied, server logout and replay denial passed. No Google OAuth or NH token issuance performed.');
    } finally { await browser.close(); }
})().catch(() => { console.error('Live browser session QA failed at ' + stage + '. No session values printed.'); process.exitCode = 1; });
