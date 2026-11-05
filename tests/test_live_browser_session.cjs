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
