const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'articles/market.html'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets/market-dashboard.css'), 'utf8');
const legend = html.match(/<div class="kodex-flow-legend"[\s\S]*?<\/div>/)[0].replace(' hidden', '');
(async () => {
    const browser = await chromium.launch({ channel: 'chrome', headless: true });
    try {
        const page = await browser.newPage();
        await page.setContent('<style>body{background:#0b1217;padding:20px;color:white}' + css + '</style>' + legend
            + '<svg width="300" height="100">' + ['foreign','personal','institution'].map((key,i) =>
                '<path class="kodex-flow-line is-' + key + '" d="M0 ' + (20+i*30) + ' H280"/>').join('') + '</svg>');
        for (const width of [390, 1280]) {
            await page.setViewportSize({ width, height: 400 });
            const styles = await page.evaluate(() => ['foreign','personal','institution'].map(key => {
                const line = getComputedStyle(document.querySelector('.kodex-flow-line.is-' + key));
                const label = getComputedStyle(document.querySelector('.kodex-flow-legend .is-' + key), '::before');
                return { key, dash: line.strokeDasharray, stroke: line.stroke, legendStyle: label.borderTopStyle,
                    legendColor: label.borderTopColor, legendWidth: label.borderTopWidth };
            }));
            for (const item of styles) {
                assert.equal(item.dash, '6px, 3px');
                assert.equal(item.legendStyle, 'dashed');
                assert.equal(item.legendColor, item.stroke);
                assert.equal(item.legendWidth, '2px');
            }
            if (process.env.FLOW_STYLE_QA_DIR) await page.screenshot({ path: path.join(process.env.FLOW_STYLE_QA_DIR, 'flow-dashes-' + width + '.png') });
        }
        console.log('Investor flow lines and legend: all dashed, matching colors at 390/1280px.');
    } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
