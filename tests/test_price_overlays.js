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

console.log('KOSPI, KODEX, TQQQ moving-average and Bollinger overlay tests passed.');
