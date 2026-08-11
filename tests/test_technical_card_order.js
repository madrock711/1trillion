const assert = require('assert');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '../articles/market.html'), 'utf8');
const js = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.css'), 'utf8');

const cardIds = Array.from(html.matchAll(/data-technical-card="([^"]+)"/g), (match) => match[1]);
assert.deepStrictEqual(cardIds, [
    'kospi-flow',
    'leading-cycle-comparison',
    'kodex-quote',
    'kodex-range',
    'kodex-history',
    'composite-momentum',
    'tqqq-history',
    'kodex-investor',
    'kodex-levels',
    'kodex-market-context'
]);
assert.strictEqual(new Set(cardIds).size, cardIds.length, 'technical card ids must be unique');
assert(!html.includes('market-technical-chart'), '별도 KODEX OHLC 비교 카드는 제거되어야 한다.');

assert(/'kospi-flow',\r?\n\s*'leading-cycle-comparison',\r?\n\s*'kodex-history',\r?\n\s*'composite-momentum',\r?\n\s*'tqqq-history'/.test(js), 'default order should keep the macro comparison ahead of KODEX, composite, and TQQQ charts');
assert(js.includes("hpmplab-technical-card-order-v2"), 'technical order must persist in localStorage');
assert(js.includes("data-technical-card-move"), 'technical cards need move controls');
assert(js.includes("updateTechnicalCardOrderControls(stack)"), 'move control disabled states must be refreshed');
assert(css.includes('.technical-card-order-controls'), 'move controls must be positioned and styled');
assert(css.includes('.technical-orderable--wide'), 'full-width chart cards must retain their layout');

console.log('Technical card ordering structure and persistence tests passed.');
