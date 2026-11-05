const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'articles/market.html'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets/market-dashboard.css'), 'utf8');
const legend = html.match(/<div class="kodex-flow-legend"[\s\S]*?<\/div>/)[0].replace(' hidden', '');
const readout = html.match(/<p class="kodex-history-readout" id="kodex-history-readout"[\s\S]*?<\/p>/)[0];
const source = fs.readFileSync(path.join(root, 'assets/market-dashboard.js'), 'utf8');
const axisStart = source.indexOf('                [flowMax, flowMin].forEach(');
assert(axisStart >= 0, 'flow axis must show only upper and lower labels');
const axisEnd = source.indexOf("                ['foreign', 'personal', 'institution'].forEach", axisStart);
const labels = [];
vm.runInNewContext(source.slice(axisStart, axisEnd), {
    flowMax: 1234, flowMin: -987, right: 908, flowY: v => v,
    makeSvg: (tag, attrs) => ({ tag, attrs }), formatSigned: v => String(v), svg: { appendChild: n => labels.push(n) }
});
assert.deepEqual(labels.map(n => n.textContent), ['1234', '-987']);
(async () => {
    const browser = await chromium.launch({ channel: 'chrome', headless: true });
    try {
        const page = await browser.newPage();
        await page.setContent('<style>:root{--space-3:12px}body{background:#0b1217;padding:20px;color:white}' + css + '</style>' + legend
            + readout + '<svg id="test-flow-chart" width="300" height="100">' + ['foreign','personal','institution'].map((key,i) =>
                '<path class="kodex-flow-line is-' + key + '" d="M0 ' + (20+i*30) + ' H280"/>').join('') + '</svg>');
        for (const width of [390, 768, 1280]) {
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
            const positions = [];
            for (const text of ['투자자별 자료 없음', '11월 5일 12:30–12:44 · 종가 65,000원 · 고가 66,000원 · 저가 64,000원 · 거래량 979,396주 · 추정 순압력 -2.5% · CVD +5,621,020주 · RSI 14 51.1 · MFI 14 58.1 · NH 원본값 12:33:00 기준 외국인 -5932 · 개인 1106 · 기관 5009', '긴 정보 '.repeat(160)]) {
                positions.push(await page.evaluate(text => {
                    const info = document.getElementById('kodex-history-readout');
                    info.textContent = text;
                    return { top: document.getElementById('test-flow-chart').getBoundingClientRect().top,
                        height: info.getBoundingClientRect().height, overflow: getComputedStyle(info).overflowY,
                        canScroll: info.scrollHeight > info.clientHeight, focusable: info.tabIndex === 0 };
                }, text));
            }
            for (const position of positions) {
                assert.equal(position.top, positions[0].top, 'text changes must not move the chart');
                assert.equal(position.height, positions[0].height);
                assert.equal(position.overflow, 'auto');
                assert(position.focusable, 'overflowing detail must remain keyboard reachable');
            }
            assert(positions.at(-1).canScroll, 'long detail remains available through internal scrolling');
            if (process.env.FLOW_STYLE_QA_DIR) await page.screenshot({ path: path.join(process.env.FLOW_STYLE_QA_DIR, 'flow-dashes-' + width + '.png') });
        }
        console.log('Flow axis: upper/lower only. Dashed legend/colors and stable readout/chart geometry passed at 390/768/1280px.');
    } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
