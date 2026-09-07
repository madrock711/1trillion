const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const script = [...html.matchAll(/<script>\s*([\s\S]*?)<\/script>/g)]
    .map((match) => match[1]).find((source) => source.includes('var validCategories'));
assert.ok(script, 'home filter script exists');

function setup(category = 'all') {
    const cards = [...html.matchAll(/<article class="article-card home-article-card" data-category="([^"]+)" data-published="([^"]+)">([\s\S]*?)<\/article>/g)]
        .map((match) => ({
            category: match[1], published: match[2], textContent: match[3].replace(/<[^>]*>/g, ''),
            hidden: false, style: {},
            getAttribute(name) { return name === 'data-category' ? this.category : this.published; }
        }));
    const elements = {
        'article-feed': {querySelectorAll: () => cards, appendChild() {}},
        'article-empty': {hidden: true, textContent: ''},
        'article-search-controls': {hidden: true},
        'article-search-status': {textContent: ''},
        'article-search': {value: '', addEventListener(event, handler) { this[event] = handler; }}
    };
    vm.runInNewContext(script, {
        URLSearchParams,
        window: {location: {search: `?category=${category}`}},
        document: {getElementById: (id) => elements[id], querySelectorAll: () => []}
    });
    return {
        cards, elements,
        visible: () => cards.filter((card) => !card.hidden),
        search(query) { elements['article-search'].value = query; elements['article-search'].input(); }
    };
}

const all = setup();
assert.equal(all.visible().length, all.cards.length);
assert.equal(all.elements['article-search-controls'].hidden, false);
all.search('생각 감정');
assert.ok(all.visible().length > 0);
assert.ok(all.visible().every((card) => card.textContent.includes('생각') && card.textContent.includes('감정')));
all.search('찾을수없는테스트문장');
assert.equal(all.visible().length, 0);
assert.equal(all.elements['article-empty'].hidden, false);
assert.equal(all.elements['article-search-status'].textContent, '0편');
all.search('  ');
assert.equal(all.visible().length, all.cards.length);
assert.equal(all.elements['article-empty'].hidden, true);
assert.equal(all.elements['article-search-status'].textContent, '');
all.search('MICRON');
assert.ok(all.visible().length > 0);
assert.ok(all.visible().every((card) => card.textContent.toLowerCase().includes('micron')));

for (const category of ['essay', 'market', 'health']) {
    const page = setup(category);
    const count = page.cards.filter((card) => card.category === category).length;
    assert.equal(page.visible().length, count);
    page.search('코스피');
    assert.ok(page.visible().every((card) => card.category === category));
    page.search('');
    assert.equal(page.visible().length, count);
}
const invalid = setup('unknown');
assert.equal(invalid.visible().length, invalid.cards.length);
console.log('home article search: ok');
