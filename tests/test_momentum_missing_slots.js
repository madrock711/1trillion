const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(require('path').join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const code = source.slice(source.indexOf('    function renderCompositeMomentumChart('), source.indexOf('    function showCompositeMomentumStatus('));
const nodes = [];
const element = { appendChild(node) { nodes.push(node); }, classList: { toggle() {} } };
const context = {
    document: { getElementById() { return element; } }, clear() { nodes.length = 0; },
    selectedKodexChartMode: 'daily',
    technicalRangeRows: [{ date: '2026-09-08', close: 100 }, { date: '2026-09-09', close: 101 }, { date: '2026-09-10', close: 102 }],
    technicalRangeSlice: rows => rows, makeSvg: (tag, attrs) => ({ tag, attrs }),
    rememberTechnicalRangePreview() {},
    registerLinkedChartHitZones() {}, formatSigned: String, formatHistoryDate: value => value,
    technicalRangePointLabel: row => row.date, compositeDirectionLabel: () => ''
};
vm.createContext(context);
vm.runInContext(code, context);
for (const days of [[], [{ date: '2026-09-09', summary: { date: '2026-09-09', direction: 1, momentum: 2, signal: 1, divergence: 0 } }]]) {
    assert.doesNotThrow(() => context.renderCompositeMomentumChart(days));
    assert(nodes.some(node => node.textContent === '2026-09-08'));
    assert(nodes.some(node => node.textContent === '2026-09-10'));
    assert.strictEqual(nodes.filter(node => node.tag === 'rect').length, days.length);
    assert(!JSON.stringify(nodes).includes('NaN'));
}
console.log('Momentum missing-slot rendering passed');
