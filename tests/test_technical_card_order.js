const assert = require('assert');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '../articles/market.html'), 'utf8');
const js = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.css'), 'utf8');

const cardIds = Array.from(html.matchAll(/data-technical-card="([^"]+)"/g), (match) => match[1]);
assert.deepStrictEqual(cardIds, [
    'kospi-flow',
    'kodex-technical',
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

assert(js.includes("'kospi-flow',\n        'kodex-history',\n        'composite-momentum',\n        'tqqq-history'"), 'default order should keep KOSPI, KODEX, composite, and TQQQ charts together');
assert(js.includes("hpmplab-technical-card-order-v2"), 'technical order must persist in localStorage');
assert(js.includes("data-technical-card-move"), 'technical cards need move controls');
assert(js.includes("updateTechnicalCardOrderControls(stack)"), 'move control disabled states must be refreshed');
assert(css.includes('.technical-card-order-controls'), 'move controls must be positioned and styled');
assert(css.includes('.technical-orderable--wide'), 'full-width chart cards must retain their layout');

console.log('Technical card ordering structure and persistence tests passed.');
