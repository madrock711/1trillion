const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'articles/market.html'), 'utf8');
const js = fs.readFileSync(path.join(root, 'assets/market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets/market-dashboard.css'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'assets/data/korea-leading-cycle.json'), 'utf8'));
const kospi = JSON.parse(fs.readFileSync(path.join(root, 'assets/data/kospi-monthly-history.json'), 'utf8'));

assert.strictEqual(data.schemaVersion, 1);
assert.strictEqual(data.seriesId, 'KOR_LEADING_COMPOSITE_CYCLICAL_COMPONENT');
assert(data.observations.length > 600, 'official monthly series should retain its long history');
assert.strictEqual(data.observations[0].period, '1970-01');
assert.strictEqual(data.latestPeriod, data.observations[data.observations.length - 1].period);
assert.strictEqual(data.latestValue, data.observations[data.observations.length - 1].value);
assert.strictEqual(kospi.schemaVersion, 1);
assert.strictEqual(kospi.seriesId, 'KOSPI_MONTHLY_OHLCV');
assert(kospi.observations.length >= 400, 'KOSPI monthly history should cover multiple business cycles');
assert.strictEqual(kospi.firstPeriod, '1990-01');
assert.strictEqual(kospi.latestPeriod, kospi.observations[kospi.observations.length - 1].date.slice(0, 7));

assert(html.includes('data-leading-cycle-source="../assets/data/korea-leading-cycle.json"'));
assert(html.includes('data-kospi-monthly-source="../assets/data/kospi-monthly-history.json"'));
assert(html.includes('id="leading-cycle-chart"'));
assert(html.includes('1990년 이후 전체 기간'));
assert(html.includes('국가지표 경기종합지수'));

assert(js.includes('function monthlyKospiCloses(market)'));
assert(js.includes('function leadingCycleComparisonRows(market)'));
assert(js.includes('function normalizeKospiMonthlyData(payload)'));
assert(js.includes('if (!leadingCycleData || !kospiMonthlyData) return [];'));
assert(js.includes('period >= firstKospiPeriod'));
assert(js.includes('function paddedExtent(values, minimumSpread)'));
assert(js.includes("d: seriesPath('leading', leadingExtent)"));
assert(js.includes("d: seriesPath('kospi', kospiExtent)"));
assert(js.includes("'class': 'leading-cycle-axis-label is-leading'"));
assert(js.includes("'class': 'leading-cycle-axis-label is-kospi'"));
assert(js.includes("role: 'slider'"));
assert(js.includes("hitbox.addEventListener('pointermove'"));
assert(js.includes('renderLeadingCycleComparison(displayKospi)'));

assert(css.includes('.leading-cycle-series.is-leading'));
assert(css.includes('.leading-cycle-series.is-kospi'));
assert(css.includes('stroke-dasharray: 8 5'));
assert(css.includes('.leading-cycle-legend .is-kospi::before'));
assert(css.includes('.leading-cycle-summary'));

console.log('Leading-cycle and KOSPI comparison chart tests passed.');
