const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const snapshot = JSON.parse(fs.readFileSync(path.join(__dirname, '../assets/data/market-dashboard-latest.json'), 'utf8'));
const nodes = new Map();
function node(text) { return { textContent: text, children: [], appendChild(n) { this.children.push(n); }, setAttribute() {} }; }
const context = {
    document: { getElementById(id) { if (!nodes.has(id)) nodes.set(id, node()); return nodes.get(id); } },
    make: (_tag, _class, text) => node(text), clear: el => { el.children = []; },
    formatKstDateTime: String, findById: (items, id) => (items || []).find(item => item.id === id)
};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('    function formatNumber('), source.indexOf('    function formatPrice(')), context);
vm.runInContext(source.slice(source.indexOf('    function renderAnalysis('), source.indexOf('    function renderAllocation(')), context);
for (const flows of [null, {}, { program: null }, { program: { total: 0, arbitrage: 1, nonArbitrage: -1, unit: '억원' } }]) {
    assert.doesNotThrow(() => context.renderAnalysis({ ...snapshot, flows }));
    const values = nodes.get('market-flow-summary').children.map(n => n.children[1].textContent);
    assert.deepEqual(values.slice(0, 3), flows?.program ? ['+1억원', '-1억원', '0억원'] : ['데이터 없음', '데이터 없음', '데이터 없음']);
}
console.log('Actual snapshot analysis with null/missing/zero program flows passed');
