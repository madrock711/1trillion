'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.css'), 'utf8');
const html = fs.readFileSync(path.join(root, 'articles', 'market.html'), 'utf8');

function functionSource(name) {
    const start = source.indexOf('function ' + name + '(');
    assert.ok(start >= 0, name + ' 함수가 있어야 한다.');
    const bodyStart = source.indexOf('{', start);
    let depth = 0;
    for (let index = bodyStart; index < source.length; index += 1) {
        if (source[index] === '{') depth += 1;
        if (source[index] === '}') depth -= 1;
        if (depth === 0) return source.slice(start, index + 1);
    }
    throw new Error(name + ' 함수 끝을 찾지 못했다.');
}

const context = {};
vm.createContext(context);
vm.runInContext([
    functionSource('simpleMovingAverage'),
    functionSource('simpleMovingAverageValues'),
    functionSource('stochasticSlowRows'),
    functionSource('priceOverlayRows'),
    functionSource('svgBandPath')
].join('\n'), context);

const rows = Array.from({ length: 60 }, (_, index) => ({ close: index + 1 }));
const overlays = context.priceOverlayRows(rows);
assert.strictEqual(overlays.length, 60);
assert.strictEqual(overlays[4].ma5, 3);
assert.strictEqual(overlays[19].ma20, 10.5);
assert.strictEqual(overlays[59].ma60, 30.5);
assert.strictEqual(overlays[18].bbUpper, null, '볼린저밴드는 20개 봉 전에는 만들면 안 된다.');
assert.ok(Math.abs(overlays[19].bbUpper - (10.5 + Math.sqrt(33.25) * 2)) < 1e-10);
assert.ok(Math.abs(overlays[19].bbLower - (10.5 - Math.sqrt(33.25) * 2)) < 1e-10);
assert.strictEqual(rows[19].ma20, undefined, '가격 오버레이 계산이 원본 행을 바꾸면 안 된다.');

const oscillatorRows = Array.from({ length: 60 }, (_, index) => ({
    high: index + 3,
    low: index,
    close: index + 2
}));
const stochastic = context.stochasticSlowRows(oscillatorRows, 20, 12, 12);
assert.strictEqual(stochastic[40].stochSlowD, null, 'Slow %D는 20·12·12 준비 구간 전에 만들면 안 된다.');
assert.ok(Number.isFinite(stochastic[41].stochSlowK));
assert.ok(Number.isFinite(stochastic[41].stochSlowD));
assert.ok(stochastic[59].stochSlowK >= 0 && stochastic[59].stochSlowK <= 100);
assert.ok(stochastic[59].stochSlowD >= 0 && stochastic[59].stochSlowD <= 100);
assert.strictEqual(oscillatorRows[59].stochSlowK, undefined, '스토캐스틱 계산이 원본 행을 바꾸면 안 된다.');

const bandPath = context.svgBandPath(
    overlays,
    'bbUpper',
    'bbLower',
    (index) => index,
    (value) => value
);
assert.ok(bandPath.startsWith('M '), '볼린저밴드 영역 경로가 생성되어야 한다.');
assert.ok(bandPath.endsWith(' Z'), '볼린저밴드 영역은 닫힌 경로여야 한다.');

assert.ok(source.includes('priceOverlayRows(rollingIntradayRows(day, interval))'), 'KODEX와 TQQQ 분봉은 봉 집계 뒤 가격 오버레이를 계산해야 한다.');
assert.ok(source.includes('if (intraday) rows = priceOverlayRows(rows);'), 'KOSPI 분봉에도 가격 오버레이를 계산해야 한다.');
assert.ok(source.includes("{ key: 'bbUpper', className: 'kodex-history-line is-bollinger' }"));
assert.ok(source.includes("{ key: 'bbLower', className: 'kodex-history-line is-bollinger' }"));
assert.ok(source.includes("node.getAttribute('data-price-ma-period') + (intraday ? '봉선' : '일선')"));
assert.strictEqual((html.match(/볼린저밴드 20·2/g) || []).length, 3, '세 가격 차트에 볼린저밴드 범례가 있어야 한다.');
assert.strictEqual((html.match(/data-price-ma-period="5"/g) || []).length, 3);
assert.ok(css.includes('.kodex-history-bollinger-band'));
assert.ok(css.includes('.kodex-history-line.is-bollinger'));
assert.ok(source.includes('stochasticSlowRows(priceOverlayRows(history), 20, 12, 12)'), 'KODEX 일봉은 표시 구간을 자르기 전에 Slow Stochastic을 계산해야 한다.');
assert.ok(source.includes('if (settings.showStochasticSlow) overlayRows = stochasticSlowRows(overlayRows, 20, 12, 12);'));
assert.ok(source.includes('showStochasticSlow: true'), 'KODEX 분봉에만 Slow Stochastic 오버레이를 켜야 한다.');
assert.strictEqual((source.match(/showStochasticSlow: true/g) || []).length, 1, 'TQQQ와 KOSPI에는 Slow Stochastic을 켜면 안 된다.');
assert.ok(css.includes('.kodex-stochastic-line.is-k'));
assert.ok(css.includes('.kodex-stochastic-line.is-d'));
assert.ok(css.includes('stroke: #ff4f5e;'), 'Slow %K는 빨강이어야 한다.');
assert.ok(css.includes('stroke: #4f8dff;'), 'Slow %D는 파랑이어야 한다.');
assert.ok(css.includes('.kodex-stochastic-zone-fill.is-k-dominant'));
assert.ok(css.includes('.kodex-stochastic-zone-fill.is-d-dominant'));
assert.ok(source.includes("'class': 'kodex-stochastic-zone-fill ' + (kLead >= 0 ? 'is-k-dominant' : 'is-d-dominant')"));
assert.strictEqual((html.match(/Slow %K 20·12/g) || []).length, 1);
assert.strictEqual((html.match(/Slow %D 20·12·12/g) || []).length, 1);

console.log('Price overlays and KODEX-only Slow Stochastic tests passed.');
