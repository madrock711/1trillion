const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'articles/market.html'), 'utf8');
const js = fs.readFileSync(path.join(root, 'assets/market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets/market-dashboard.css'), 'utf8');
const snapshot = JSON.parse(fs.readFileSync(path.join(root, 'assets/data/market-dashboard-latest.json'), 'utf8'));

assert(!html.includes('data-technical-card="kodex-technical"'), '별도 KODEX OHLC 비교 카드는 없어야 한다.');
assert(!html.includes('id="market-technical-chart"'), '제거한 OHLC 비교 SVG가 남아 있으면 안 된다.');

assert(js.includes('function kodexAnalysisLevels(instrumentOrLevels)'));
assert(js.includes('function appendKodexAnalysisLevels(svg, levels, priceY, left, right, top, bottom)'));
assert(js.includes('appendKodexAnalysisLevels(svg, analysisLevels, priceY, margin.left, width - margin.right, priceTop, priceBottom);'), '일봉 차트에 발행 기준선을 표시해야 한다.');
assert(js.includes('appendKodexAnalysisLevels(svg, analysisLevels, priceY, margin.left, right, priceTop, priceBottom);'), '분봉 차트에 발행 기준선을 표시해야 한다.');
assert(js.includes('kodexIntradayRenderOptions.analysisLevels = kodexAnalysisLevels(instrument);'), '공통 분봉 재렌더에도 같은 기준선을 전달해야 한다.');
assert(!js.includes('function renderTechnicalInstrument('), '제거한 카드의 렌더러가 남아 있으면 안 된다.');

assert(css.includes('.kodex-analysis-level.is-support'));
assert(css.includes('.kodex-analysis-level.is-pivot'));
assert(css.includes('.kodex-analysis-level.is-resistance'));
assert(css.includes('.kodex-history-legend .is-analysis-support'));
assert(css.includes('.kodex-history-legend .is-analysis-pivot'));
assert(css.includes('.kodex-history-legend .is-analysis-resistance'));
assert(!css.includes('.kodex-analysis-level-label-bg'), '차트 내부 가격표 배경은 없어야 한다.');
assert(!js.includes("var text = level.label + ' ' + formatPrice(level.value, '원');"), '가격축에는 기준선 설명을 함께 쓰지 않는다.');
assert(js.includes('label.textContent = formatNumber(level.value, 0);'), '우측 가격축에는 가격 숫자만 표시해야 한다.');
assert(html.includes('<span class="is-analysis-support">1차 지지</span>'));
assert(html.includes('<span class="is-analysis-pivot">반등 기준</span>'));
assert(html.includes('<span class="is-analysis-resistance">저항</span>'));

const kodex = snapshot.technical.instruments.find((instrument) => instrument.id === 'KODEX');
assert(kodex, '최신 발행 스냅샷에 KODEX 기술 데이터가 필요하다.');
['1차 지지', '반등 기준', '저항'].forEach((label) => {
    const level = kodex.levels.find((item) => item.label === label);
    assert(level && Number.isFinite(level.value), `${label} 숫자가 최신 발행 스냅샷에 있어야 한다.`);
});

console.log('KODEX published support and resistance overlay tests passed.');
