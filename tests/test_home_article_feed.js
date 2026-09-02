const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const home = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const app = fs.readFileSync(path.join(root, 'app.html'), 'utf8');
const archive = fs.readFileSync(path.join(root, 'articles', 'index.html'), 'utf8');
const market = fs.readFileSync(path.join(root, 'articles', 'market.html'), 'utf8');
const styles = fs.readFileSync(path.join(root, 'style.css'), 'utf8');
const i18n = fs.readFileSync(path.join(root, 'i18n.js'), 'utf8');
const sitemap = fs.readFileSync(path.join(root, 'sitemap.xml'), 'utf8');

assert.match(home, /<title>연마 아티클 \| 사람과 사회, 몸과 마음에 관한 글<\/title>/);
assert.match(home, /<link rel="canonical" href="https:\/\/www\.hpmplab\.com\/">/);
assert.match(home, /<meta name="twitter:card" content="summary_large_image">/);
assert.match(home, /<meta property="og:image" content="https:\/\/www\.hpmplab\.com\/assets\/images\/articles\/market-2026-09-03-chip-rebound-balance-1200x630\.webp">/);
assert.match(home, /<a class="skip-link" href="#main-content">최신 아티클로 건너뛰기<\/a>/);
assert.match(home, /<main class="content-page article-index-page article-home-page" id="main-content" tabindex="-1">/);

assert.match(home, /var allowed = \['breathing', 'co2', 'foot', 'sequence', 'lottery', 'abrahang'\]/);
assert.match(home, /window\.location\.replace\('\/app\.html\?tab=' \+ encodeURIComponent\(tab\)\)/);
assert.match(home, /var validCategories = \['all', 'essay', 'market', 'health'\]/);
assert.doesNotMatch(home, /requested === 'market'/);

const homeHeader = home.match(/<header>[\s\S]*?<\/header>/)?.[0] || '';
const articleNavIndex = homeHeader.indexOf('href="/" aria-current="page">아티클');
const toolsNavIndex = homeHeader.indexOf('href="app.html">도구');
const marketNavIndex = homeHeader.indexOf('href="articles/market.html">시황');
assert.ok(articleNavIndex >= 0 && articleNavIndex < toolsNavIndex && toolsNavIndex < marketNavIndex);

const cardTags = [...home.matchAll(/<article class="article-card home-article-card" data-category="([^"]+)" data-published="([^"]+)">/g)];
assert.equal(cardTags.length, 44);
assert.equal((home.match(/<h3 class="home-article-title">/g) || []).length, 44);
assert.deepEqual(
    cardTags.reduce((counts, match) => ({...counts, [match[1]]: (counts[match[1]] || 0) + 1}), {}),
    {market: 29, health: 9, essay: 6}
);
assert.ok(cardTags.every((match, index) => index === 0 || Date.parse(cardTags[index - 1][2]) >= Date.parse(match[2])));
assert.equal((home.match(/loading="eager"/g) || []).length, 1);
assert.equal((home.match(/fetchpriority="high"/g) || []).length, 1);
assert.equal((home.match(/loading="lazy"/g) || []).length, 43);

for (const match of home.matchAll(/class="home-article-link" href="([^"]+)"/g)) {
    assert.ok(fs.existsSync(path.join(root, ...match[1].split('/'))), `missing article: ${match[1]}`);
}
const homeArticlePaths = [...home.matchAll(/class="home-article-link" href="articles\/([^"]+)"/g)].map((match) => match[1]);
const latestArchiveArticles = [...archive.matchAll(/<article class="article-card" data-category="(essay|market|health)" data-published="([^"]+)">([\s\S]*?)<\/article>/g)]
    .map((match) => ({
        published: match[2],
        href: match[3].match(/<h3><a href="([^"]+)"/)?.[1]
    }))
    .sort((a, b) => Date.parse(b.published) - Date.parse(a.published))
    .map((item) => item.href);
assert.deepEqual(homeArticlePaths, latestArchiveArticles);
for (const match of home.matchAll(/class="article-card-image" src="([^"]+)"/g)) {
    assert.ok(fs.existsSync(path.join(root, ...match[1].split('/'))), `missing image: ${match[1]}`);
}

const jsonBlocks = [...home.matchAll(/<script type="application\/ld\+json">\s*([\s\S]*?)\s*<\/script>/g)].map((match) => JSON.parse(match[1]));
assert.equal(jsonBlocks.length, 1);
const collection = jsonBlocks[0]['@graph'].find((item) => item['@type'] === 'CollectionPage');
assert.ok(collection);
assert.equal(collection.mainEntity.numberOfItems, cardTags.length);
assert.equal(collection.mainEntity.itemListElement.length, cardTags.length);
assert.deepEqual(collection.mainEntity.itemListElement.map((item) => item.position), Array.from({length: 44}, (_, index) => index + 1));
assert.deepEqual(
    collection.mainEntity.itemListElement.map((item) => item.url),
    homeArticlePaths.map((pathname) => `https://www.hpmplab.com/articles/${pathname}`)
);
assert.deepEqual(
    collection.mainEntity.itemListElement.map((item) => item.name),
    [...home.matchAll(/<h3 class="home-article-title">([^<]+)<\/h3>/g)].map((match) => match[1])
);

assert.match(styles, /\.article-home-page\s*\{/);
assert.match(styles, /\.home-article-link\s*\{/);
assert.match(styles, /\.home-article-title\s*\{/);
assert.equal((archive.match(/loading="eager"/g) || []).length, 1);
assert.equal((archive.match(/fetchpriority="high"/g) || []).length, 1);

assert.match(app, /href="\/" data-i18n="nav\.articles">아티클<\/a>[\s\S]*href="app\.html" aria-current="page" data-i18n="nav\.tools">도구<\/a>[\s\S]*href="articles\/market\.html" data-i18n="nav\.market">시황<\/a>/);
assert.equal((i18n.match(/'nav\.market':/g) || []).length, 2);
assert.match(archive, /href="\.\/" aria-current="page">아티클<\/a>[\s\S]*href="\.\.\/app\.html">도구<\/a>[\s\S]*href="market\.html">시황<\/a>/);
assert.match(market, /href="\.\.\/">아티클<\/a>[\s\S]*href="\.\.\/app\.html">도구<\/a>[\s\S]*href="market\.html" aria-current="page">시황<\/a>/);
const marketHero = market.match(/<section class="content-page-hero market-dashboard-hero">([\s\S]*?)<\/section>/)?.[1] || '';
assert.match(marketHero, /aria-label="시황 글"[\s\S]*>일일시황 <span class="article-category-count">29<\/span>/);
assert.doesNotMatch(marketHero, />전체 |\?category=essay|\?category=health/);
assert.equal((market.match(/<article class="market-article-item">/g) || []).length, 29);

const detailFiles = fs.readdirSync(path.join(root, 'articles'))
    .filter((name) => name.endsWith('.html') && name !== 'index.html' && name !== 'market.html');
assert.equal(detailFiles.length, 44);
for (const name of detailFiles) {
    const detail = fs.readFileSync(path.join(root, 'articles', name), 'utf8');
    const header = detail.match(/<header>[\s\S]*?<\/header>/)?.[0] || '';
    const primaryNav = header.match(/<nav aria-label="주요 이동">([\s\S]*?)<\/nav>/)?.[1] || '';
    assert.equal((primaryNav.match(/<a /g) || []).length, 3, `${name}: primary navigation link count`);
    assert.doesNotMatch(primaryNav, /가이드|소개|문의/, `${name}: legacy primary navigation`);
    if (name.startsWith('market-')) {
        assert.match(primaryNav, /href="\.\.\/">아티클<\/a>[\s\S]*href="\.\.\/app\.html">도구<\/a>[\s\S]*href="market\.html" aria-current="page">시황<\/a>/, `${name}: market navigation`);
    } else {
        assert.match(primaryNav, /href="\.\.\/" aria-current="page">아티클<\/a>[\s\S]*href="\.\.\/app\.html">도구<\/a>[\s\S]*href="market\.html">시황<\/a>/, `${name}: article navigation`);
    }
}

for (const pathname of ['', 'articles/', 'articles/market.html']) {
    const escaped = pathname.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replaceAll('/', '\\/');
    assert.match(sitemap, new RegExp(`<loc>https:\\/\\/www\\.hpmplab\\.com\\/${escaped}<\\/loc><lastmod>2026-09-03<\\/lastmod>`));
}

console.log('home article feed: ok');
