// Production data with local dashboard assets: range preview and floating boundary regression.
const assert = require('node:assert/strict');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const root = path.resolve(__dirname, '..');

(async () => {
    const browser = await chromium.launch({ channel: 'chrome', headless: true });
    try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
        await page.route(/\/assets\/market-dashboard\.(js|css)(\?|$)/, route => {
            const name = new URL(route.request().url()).pathname.split('/').pop();
            return route.fulfill({
                path: path.join(root, 'assets', name),
                contentType: name.endsWith('.js') ? 'text/javascript' : 'text/css'
            });
        });
        await page.route(/googlesyndication|doubleclick|googletagmanager|google-analytics/, route => route.abort());
        await page.goto('https://www.hpmplab.com/articles/market.html?view=technical', {
            waitUntil: 'commit',
            timeout: 60000
        });
        await page.waitForFunction(() => document.querySelectorAll('#kospi-flow-chart path, #kospi-flow-chart line, #kospi-flow-chart rect').length > 100, null, { timeout: 90000 });
        await page.locator('#kospi-flow-chart').scrollIntoViewIfNeeded();

        const start = page.locator('#technical-range-start');
        const fullShapeCount = await page.locator('#kospi-flow-chart path, #kospi-flow-chart line, #kospi-flow-chart rect').count();
        await start.evaluate(input => {
            input.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 1, button: 0 }));
            input.value = '58';
            input.dispatchEvent(new Event('input', { bubbles: true }));
        });
        await page.waitForFunction(() => document.querySelector('#kospi-flow-chart .technical-range-preview-label'));
        const previewShapeCount = await page.locator('#kospi-flow-chart path, #kospi-flow-chart line, #kospi-flow-chart rect').count();
        assert(previewShapeCount <= 5, `preview should stay lightweight: ${previewShapeCount}`);
        assert(previewShapeCount < fullShapeCount / 20, `preview ${previewShapeCount} should be much smaller than full ${fullShapeCount}`);
        await start.evaluate(input => {
            input.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 1, button: 0 }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
        });
        await page.waitForFunction(() => document.querySelectorAll('#kospi-flow-chart path, #kospi-flow-chart line, #kospi-flow-chart rect').length > 100);

        async function settleScroll(y) {
            await page.evaluate(value => window.scrollTo(0, value), y);
            await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        }

        async function verifyFloatingBoundary(width) {
            await page.setViewportSize({ width, height: 900 });
            await settleScroll(0);
            const geometry = await page.evaluate(() => {
                const panel = document.querySelector('[data-view-panel="technical"]');
                return {
                    panelBottom: panel.getBoundingClientRect().bottom + window.scrollY,
                    viewportHeight: window.innerHeight
                };
            });
            const bottomOffset = width <= 720 ? 8 : 12;
            const boundary = geometry.panelBottom - (geometry.viewportHeight - bottomOffset);
            const before = Math.max(0, boundary - 36);
            const after = boundary + 36;
            const positions = [];
            const states = [];
            for (const y of [before, after, before, after]) {
                await settleScroll(y);
                const state = await page.evaluate(() => {
                    const slot = document.getElementById('technical-range-navigator-slot');
                    const navigator = document.getElementById('technical-range-navigator');
                    const next = slot.nextElementSibling;
                    return {
                        floating: navigator.classList.contains('is-floating'),
                        slotHeight: parseFloat(slot.style.height) || 0,
                        navigatorHeight: navigator.getBoundingClientRect().height,
                        nextDocumentTop: next.getBoundingClientRect().top + window.scrollY
                    };
                });
                states.push(state.floating);
                positions.push(state.nextDocumentTop);
                if (state.floating) assert(Math.abs(state.slotHeight - state.navigatorHeight) <= 1, 'floating slot must preserve navigator height');
            }
            assert.deepEqual(states, [true, false, true, false], `${width}px floating boundary should be deterministic`);
            assert(Math.max(...positions) - Math.min(...positions) <= 1, `${width}px layout moved across floating boundary`);
        }

        await verifyFloatingBoundary(1280);
        await verifyFloatingBoundary(390);
        console.log(`Range preview reduced KOSPI SVG shapes from ${fullShapeCount} to ${previewShapeCount}; floating boundaries stayed stable.`);
    } finally {
        await browser.close();
    }
})().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
