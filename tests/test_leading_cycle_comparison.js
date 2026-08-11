const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'articles/market.html'), 'utf8');
const js = fs.readFileSync(path.join(root, 'assets/market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets/market-dashboard.css'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'assets/data/korea-leading-cycle.json'), 'utf8'));

assert.strictEqual(data.schemaVersion, 1);
assert.strictEqual(data.seriesId, 'KOR_LEADING_COMPOSITE_CYCLICAL_COMPONENT');
assert(data.observations.length > 600, 'official monthly series should retain its long history');
assert.strictEqual(data.observations[0].period, '1970-01');
assert.strictEqual(data.latestPeriod, data.observations[data.observations.length - 1].period);
assert.strictEqual(data.latestValue, data.observations[data.observations.length - 1].value);

assert(html.includes('data-leading-cycle-source="../assets/data/korea-leading-cycle.json"'));
assert(html.includes('id="leading-cycle-chart"'));
assert(html.includes('첫 공통월 = 100'));
assert(html.includes('국가데이터처 경기종합지수'));

assert(js.includes('function monthlyKospiCloses(market)'));
assert(js.includes('function leadingCycleComparisonRows(market)'));
assert(js.includes('leading / baselineLeading * 100'));
assert(js.includes('kospiRow.value / baselineKospi * 100'));
assert(js.includes("d: seriesPath('leadingNormalized')"));
assert(js.includes("d: seriesPath('kospiNormalized')"));
assert(js.includes('renderLeadingCycleComparison(displayKospi)'));

assert(css.includes('.leading-cycle-series.is-leading'));
assert(css.includes('.leading-cycle-series.is-kospi'));
assert(css.includes('.leading-cycle-summary'));

console.log('Leading-cycle and KOSPI comparison chart tests passed.');
