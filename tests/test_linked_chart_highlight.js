const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const dashboard = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.css'), 'utf8');
const html = fs.readFileSync(path.join(root, 'articles', 'market.html'), 'utf8');

assert(dashboard.includes('var linkedChartLockedSelection = null;'));
assert(dashboard.includes('function registerLinkedChartHitZones'));
assert(dashboard.includes("element.addEventListener('pointerenter'"));
assert(dashboard.includes('activateLinkedChartSelection(svg, index, false)'));
assert(dashboard.includes('activateLinkedChartSelection(svg, index, true)'));
assert(dashboard.includes('linkedChartSelectionMatches(linkedChartLockedSelection, selection)'));
assert(dashboard.includes("mode: intraday ? 'intraday' : 'daily'"));
assert(dashboard.includes("mode: 'intraday'"));
assert((dashboard.match(/registerLinkedChartHitZones\(/g) || []).length >= 6);
assert(css.includes('.linked-chart-hitbox.is-linked-selected'));
assert(css.includes('.linked-chart-hitbox.is-linked-selected.is-locked'));
assert(html.includes('market-dashboard.css?v=20260809-07'));
assert(html.includes('market-dashboard.js?v=20260809-08'));

console.log('Synchronized hover and click-lock chart highlight tests passed.');
