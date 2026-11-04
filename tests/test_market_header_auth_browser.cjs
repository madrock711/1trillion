// Offline responsive UI test: Google and the private API are fully mocked.
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const pageUrl = pathToFileURL(path.resolve(__dirname, '../articles/market.html')).href + '?view=technical';

(async () => {
    const browser = await chromium.launch({ channel: 'chrome', headless: true });
    try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
        await page.route(/^https?:\/\//, route => route.abort());
        await page.route('**/api/private/nh/session', route => route.fulfill({
            status: 200, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' },
            body: JSON.stringify({ authenticated: true })
        }));
        await page.addInitScript(() => {
            let callback;
            window.google = { accounts: { id: {
                initialize(options) { callback = options.callback; },
                renderButton(element, options) {
                    if (options.type !== 'icon') throw new Error('Expected compact Google button');
                    const button = document.createElement('button');
                    button.textContent = 'G';
                    button.setAttribute('aria-label', 'Google 계정 선택');
                    button.onclick = () => callback({ credential: 'offline-test-token' });
                    element.appendChild(button);
                },
                disableAutoSelect() {}
            } } };
        });
        await page.goto(pageUrl, { waitUntil: 'domcontentloaded' });
        const auth = page.locator('#kodex-private-auth');
        await auth.waitFor({ state: 'visible', timeout: 15000 });
        assert(await page.locator('header #kodex-private-signin').isVisible());
        for (const width of [320, 390, 768, 1040, 1280]) {
            await page.setViewportSize({ width, height: 900 });
            const result = await page.evaluate(() => {
                const rect = selector => {
                    const r = document.querySelector(selector).getBoundingClientRect();
                    return { left: r.left, right: r.right, top: r.top, bottom: r.bottom };
                };
                const overlaps = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
                const account = rect('#kodex-private-auth');
                const title = rect('.header-title');
                const navigation = rect('header nav');
                return { width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth,
                    account, title, navigation, overlapsTitle: overlaps(account, title), overlapsNav: overlaps(account, navigation) };
            });
            assert(result.scroll <= result.width + 1, `Horizontal overflow at ${width}: ${JSON.stringify(result)}`);
            assert(!result.overlapsTitle && !result.overlapsNav, `Header overlaps at ${width}: ${JSON.stringify(result)}`);
            assert(result.account.left >= 0 && result.account.right <= width, `Account control off-screen at ${width}`);
            if (process.env.HEADER_QA_DIR && (width === 320 || width === 1280)) {
                await page.locator('header').screenshot({ path: path.join(process.env.HEADER_QA_DIR, `market-header-${width}.png`) });
            }
        }
        for (const width of [320, 1280]) {
            await page.setViewportSize({ width, height: 900 });
            await page.locator('#kodex-private-signin').click();
            assert(await page.getByRole('button', { name: 'Google 계정 선택' }).isVisible());
            assert.match(await page.locator('#kodex-private-auth-status').innerText(), /계정을 선택/);
            const statusLayout = await page.evaluate(() => {
                const status = document.querySelector('#kodex-private-auth-status').getBoundingClientRect();
                const nav = document.querySelector('header nav').getBoundingClientRect();
                return { statusTop: status.top, navBottom: nav.bottom, scroll: document.documentElement.scrollWidth,
                    width: document.documentElement.clientWidth };
            });
            assert(statusLayout.statusTop >= statusLayout.navBottom - 1,
                `Account status overlaps navigation at ${width}: ${JSON.stringify(statusLayout)}`);
            assert(statusLayout.scroll <= statusLayout.width + 1, `Account status overflows at ${width}`);
            if (process.env.HEADER_QA_DIR) {
                await page.locator('header').screenshot({ path: path.join(process.env.HEADER_QA_DIR, `market-header-${width}-prompt.png`) });
            }
            await page.getByRole('button', { name: 'Google 계정 선택' }).click();
            await page.locator('#kodex-private-signout').waitFor({ state: 'visible' });
            assert.match(await page.locator('#kodex-private-auth-status').innerText(), /로그인했습니다/);
            if (process.env.HEADER_QA_DIR) {
                await page.locator('header').screenshot({ path: path.join(process.env.HEADER_QA_DIR, `market-header-${width}-signed-in.png`) });
            }
            await page.locator('#kodex-private-signout').click();
            assert(await page.locator('#kodex-private-signin').isVisible());
            assert.match(await page.locator('#kodex-private-auth-status').innerText(), /로그아웃/);
        }
        console.log('Header account controls: responsive layout, sign-in and sign-out passed (offline mocks).');
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
