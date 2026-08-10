'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const dashboard = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.css'), 'utf8');
const html = fs.readFileSync(path.join(root, 'articles', 'market.html'), 'utf8');

assert(html.includes('id="technical-range-navigator"'));
assert(html.includes('id="technical-range-start"'));
assert(html.includes('id="technical-range-end"'));
assert(html.includes('id="technical-range-selection"'));
assert(html.includes('id="technical-range-overview"'));
assert(dashboard.includes('var selectedKodexIntradayDateExplicit = false;'));
assert(dashboard.includes('selectedKodexIntradayDateExplicit = true;'));
assert(dashboard.includes('MarketDashboardLive.preferredIntradayDate(indexRows, selectedKodexIntradayDate, selectedKodexIntradayDateExplicit)'));
assert(dashboard.includes('if (kodex) setKodexChartControls(kodex);'));
assert(dashboard.includes('function technicalRangeSlice(rows)'));
assert(dashboard.includes('function updateTechnicalRangeNavigator(rows)'));
assert(dashboard.includes("selection.addEventListener('pointermove'"));
assert(dashboard.includes("selection.addEventListener('keydown'"));
assert((dashboard.match(/technicalRangeSlice\(/g) || []).length >= 7, '모든 주요 기술적 차트가 공통 표시 범위를 사용해야 한다.');
assert(css.includes('.technical-range-navigator {'));
assert(css.includes('position: fixed;'));
assert(css.includes('.market-view-tabs {\n    position: sticky;'));
assert(css.includes('.technical-range-selection.is-dragging'));
assert(css.includes('.technical-range-input::-webkit-slider-thumb'));

console.log('Technical range navigator and live-date selection tests passed.');
