const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const article = fs.readFileSync(path.join(root, 'articles', 'korean-peninsula-energy-ai-lighthouse.html'), 'utf8');
const script = fs.readFileSync(path.join(root, 'assets', 'article-reading.js'), 'utf8');
const styles = fs.readFileSync(path.join(root, 'style.css'), 'utf8');
const sitemap = fs.readFileSync(path.join(root, 'sitemap.xml'), 'utf8');

assert.match(article, /data-reading-enhancements/);
assert.match(article, /class="article-reading-progress" aria-hidden="true"/);
assert.match(article, /assets\/article-reading\.js\?v=20260816-5/);
assert.equal((article.match(/class="article-keyline"/g) || []).length, 5);
assert.match(article, /article:modified_time" content="2026-08-16T12:05:14\+09:00"/);
assert.match(article, /"dateModified": "2026-08-16T12:05:14\+09:00"/);

assert.match(script, /requestAnimationFrame\(updateProgress\)/);
assert.match(script, /prefers-reduced-motion: reduce/);
assert.match(script, /function getCenterCandidate\(\)/);
assert.match(script, /candidate === activeParagraph/);
assert.match(script, /paragraph\.querySelectorAll\('strong, b'\)/);
assert.match(script, /candidate\.querySelectorAll\('\.article-keyline'\)/);
assert.match(script, /duration: 1100/);
assert.match(script, /keyline\.animate\(/);
assert.match(script, /keyline\.classList\.add\('is-highlighted'\)/);
assert.doesNotMatch(script, /is-reading-target/);
assert.doesNotMatch(script, /localStorage/);

assert.match(styles, /\.article-keyline\.is-highlighted/);
assert.match(styles, /@keyframes article-keyline-sweep/);
assert.match(styles, /\.article-reading-progress span/);
assert.match(styles, /rgba\(68, 209, 122, 0\.3\)/);
assert.doesNotMatch(styles, /\.reading-article h2\.is-reading-target/);
assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/);

assert.match(
    sitemap,
    /<loc>https:\/\/www\.hpmplab\.com\/articles\/korean-peninsula-energy-ai-lighthouse\.html<\/loc>\s*<lastmod>2026-08-16<\/lastmod>/
);

console.log('article reading enhancements: ok');
