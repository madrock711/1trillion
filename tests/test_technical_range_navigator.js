'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const dashboard = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.css'), 'utf8');
const html = fs.readFileSync(path.join(root, 'articles', 'market.html'), 'utf8');

assert(html.includes('id="technical-range-navigator"'));
assert(html.includes('id="technical-range-navigator-slot"'));
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
assert(dashboard.includes('function placeTechnicalRangeNavigator(stack)'));
assert(dashboard.includes("firstChart.insertAdjacentElement('afterend', slot)"));
assert(dashboard.includes('function updateFloatingDashboardControls()'));
assert(dashboard.includes('slotTop <= triggerTop'));
assert(dashboard.includes("navigator.classList.toggle('is-floating', shouldFloat)"));
assert(dashboard.includes("tabs.classList.toggle('is-floating'"));
assert(dashboard.includes("selection.addEventListener('pointermove'"));
assert(dashboard.includes("selection.addEventListener('keydown'"));
assert((dashboard.match(/technicalRangeSlice\(/g) || []).length >= 7, '모든 주요 기술적 차트가 공통 표시 범위를 사용해야 한다.');
assert(css.includes('.technical-range-navigator {'));
assert(css.includes('.technical-range-navigator.is-floating {\n    position: fixed;'));
assert(css.includes('.technical-range-navigator-slot {'));
assert(css.includes('.market-view-tabs {\n    --market-tabs-sticky-top: 64px;\n    position: sticky;'));
assert(css.includes('.market-view-tabs.is-floating {'));
assert(css.includes('.technical-range-selection.is-dragging'));
assert(css.includes('.technical-range-input::-webkit-slider-thumb'));

const navigatorSlotIndex = html.indexOf('id="technical-range-navigator-slot"');
const firstChartEndIndex = html.indexOf('</section>', html.indexOf('data-technical-card="kospi-flow"'));
const nextCardIndex = html.indexOf('data-technical-card="kodex-technical"');
assert(firstChartEndIndex < navigatorSlotIndex && navigatorSlotIndex < nextCardIndex, '표시구간 네비게이터는 첫 차트 바로 뒤에 있어야 한다.');

console.log('Technical range navigator and live-date selection tests passed.');
