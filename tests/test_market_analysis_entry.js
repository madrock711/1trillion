const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/market-analysis-entry.js', 'utf8');
const dashboard = fs.readFileSync('assets/market-dashboard.js', 'utf8');
const clickBinding = dashboard.slice(dashboard.indexOf('    viewLinks.forEach(function (link) {\n        link.addEventListener'), dashboard.indexOf("    window.addEventListener('popstate'"));

function scenario(initialView, mobile = false) {
    const handlers = new Map();
    const frames = new Map();
    const calls = [];
    const links = {};
    let next = 0;
    let current = initialView;
    const panel = { hidden: current !== 'analysis' };
    const window = {
        addEventListener: (name, fn) => handlers.set(name, fn),
        dispatchEvent: event => handlers.get(event.type)?.(event),
        CustomEvent: function (type, options) { this.type = type; this.detail = options.detail; },
        requestAnimationFrame: fn => { frames.set(++next, fn); return next; },
        cancelAnimationFrame: id => frames.delete(id),
        matchMedia: () => ({ matches: mobile })
    };
    const viewLinks = ['analysis', 'technical', 'strategy'].map(view => links[view] = {
        getAttribute: () => view,
        addEventListener: (name, fn) => { links[view].click = fn; },
        focus: options => assert(options.preventScroll)
    });
    const document = {
        getElementById: () => panel,
        querySelector: selector => ({ scrollIntoView: options => calls.push({ selector, block: options.block }) })
    };
    const context = vm.createContext({ window, document, viewLinks,
        currentViewFromUrl: () => current,
        setView: view => { current = view; panel.hidden = view !== 'analysis'; }
    });
    vm.runInContext(source, context);
    vm.runInContext(clickBinding, context);
    return {
        calls,
        click(view, modifiers = {}) { links[view].click({ button: 0, preventDefault() {}, ...modifiers }); },
        flush() { const pending = [...frames.values()]; frames.clear(); pending.forEach(fn => fn()); }
    };
}
for (const mobile of [false, true]) {
    for (const from of ['technical', 'strategy']) {
        const run = scenario(from, mobile);
        assert.equal(run.calls.length, 0, 'No automatic scroll on initial load or reload');
        run.click('analysis'); run.flush();
        assert.equal(run.calls.length, 1, 'One positioning action per transition, including mobile');
        assert.equal(run.calls[0].selector, '#research-archive .market-article-item');
        assert.equal(run.calls[0].block, 'end');
        run.click('analysis'); run.flush();
        assert.equal(run.calls.length, 1, 'Clicking the active tab must not reset reading position');
    }
}
const fastSwitch = scenario('technical');
fastSwitch.click('analysis'); fastSwitch.click('technical'); fastSwitch.flush();
assert.equal(fastSwitch.calls.length, 0, 'Cancelled transition must not scroll a now-hidden panel');
const modified = scenario('technical');
modified.click('analysis', { ctrlKey: true }); modified.flush();
assert.equal(modified.calls.length, 0, 'New-tab modifier retains browser navigation');
console.log('Market analysis tab transition positioning: passed');
