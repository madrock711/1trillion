const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const articlesDir = path.join(root, 'articles');
const marketArticles = fs.readdirSync(articlesDir)
    .filter((name) => /^market-\d{4}-\d{2}-\d{2}.*\.html$/.test(name));

if (!marketArticles.length) throw new Error('시황분석 글을 찾지 못했습니다.');

for (const name of marketArticles) {
    const html = fs.readFileSync(path.join(articlesDir, name), 'utf8');
    if (!html.includes('class="content-page-nav market-article-view-tabs"')) {
        throw new Error(`${name}: 시황분석 플로팅 탭이 없습니다.`);
    }
    if (!html.includes('href="market.html?view=technical"')) {
        throw new Error(`${name}: 기술적 분석 직행 링크가 없습니다.`);
    }
    if (!html.includes('../assets/market-article-nav.js?v=20260826-1')) {
        throw new Error(`${name}: 플로팅 탭 스크립트 버전이 없습니다.`);
    }
}

const css = fs.readFileSync(path.join(root, 'style.css'), 'utf8');
if (!css.includes('.reading-shell > .market-article-view-tabs')) {
    throw new Error('시황분석 플로팅 탭 스타일이 없습니다.');
}
if (!css.includes('top: var(--market-article-tabs-top)')) {
    throw new Error('사이트 헤더 아래 고정 위치 규칙이 없습니다.');
}

const script = fs.readFileSync(path.join(root, 'assets', 'market-article-nav.js'), 'utf8');
if (!script.includes("document.querySelector('body > header')")) {
    throw new Error('사이트 헤더 높이 측정 코드가 없습니다.');
}
if (!script.includes("tabs.classList.toggle('is-floating'")) {
    throw new Error('스크롤 플로팅 상태 전환 코드가 없습니다.');
}

console.log(`market article floating nav test passed (${marketArticles.length} articles)`);
