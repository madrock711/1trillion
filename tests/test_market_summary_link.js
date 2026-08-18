const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'articles', 'market.html'), 'utf8');
const dashboard = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.css'), 'utf8');

assert.match(
    html,
    /<a class="market-dashboard-card market-summary-card" id="market-summary-article-link" href="market-2026-08-19\.html">/,
    '오늘 시장 요약 카드는 최신 시황 글로 이동하는 네이티브 링크여야 합니다.'
);
assert(
    dashboard.includes("['market-latest-article-link', 'market-summary-article-link']"),
    '최신 시황 데이터가 CTA와 요약 카드 링크를 함께 갱신해야 합니다.'
);
assert(css.includes('.market-summary-card:focus-visible'), '키보드 포커스 표시가 있어야 합니다.');

console.log('market summary link tests passed');
