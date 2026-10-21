const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/market-analysis-entry.js', 'utf8');

function scenario({ type = 'reload', view = 'analysis', hash = '', hidden = false } = {}) {
    const listeners = new Map();
    const frames = new Map();
    const timers = new Map();
    let next = 0;
    let resized;
    let disconnected = false;
    const calls = [];
    const latest = { scrollIntoView: options => calls.push(options) };
    const panel = { hidden };
    function add(name, fn) {
        if (!listeners.has(name)) listeners.set(name, new Set());
        listeners.get(name).add(fn);
    }
    const window = {
        location: { search: '?view=' + view, hash },
        performance: { getEntriesByType: () => [{ type }] },
        history: { scrollRestoration: 'auto' },
        addEventListener: add,
        removeEventListener: (name, fn) => listeners.get(name)?.delete(fn),
        requestAnimationFrame: fn => { frames.set(++next, fn); return next; },
        cancelAnimationFrame: id => frames.delete(id),
        setTimeout: fn => { timers.set(++next, fn); return next; },
        clearTimeout: id => timers.delete(id),
        ResizeObserver: class {
            constructor(fn) { resized = fn; }
            observe() {}
            disconnect() { disconnected = true; }
        }
    };
    const document = {
        addEventListener: add,
        getElementById: id => id === 'market-view-analysis' ? panel : {},
        querySelector: () => latest
    };
    vm.runInNewContext(source, { window, document, URLSearchParams });
    return {
        window, calls,
        emit(name) { for (const fn of [...(listeners.get(name) || [])]) fn(); },
        flush() { const pending = [...frames.values()]; frames.clear(); pending.forEach(fn => fn()); },
        resize() { resized?.(); },
        expire() { for (const fn of [...timers.values()]) fn(); },
        get disconnected() { return disconnected; }
    };
}

for (const options of [{ type: 'navigate' }, { type: 'back_forward' }, { view: 'technical' }, { view: 'strategy' }, { hash: '#factor-title' }]) {
    const run = scenario(options);
    run.emit('DOMContentLoaded'); run.emit('load'); run.flush();
    assert.equal(run.calls.length, 0, JSON.stringify(options));
    assert.equal(run.window.history.scrollRestoration, 'auto');
}
for (const hash of ['', '#research-archive']) {
    const run = scenario({ hash });
    assert.equal(run.window.history.scrollRestoration, 'manual');
    run.emit('DOMContentLoaded'); run.flush();
    assert.equal(run.calls.length, 1);
    assert.equal(run.calls[0].block, 'end');
    run.emit('technical-dashboard-ready'); run.resize(); run.flush();
    assert.equal(run.calls.length, 2, 'Delayed data layout gets a single coalesced alignment');
    run.expire(); run.resize(); run.flush();
    assert.equal(run.calls.length, 2);
    assert(run.disconnected);
    assert.equal(run.window.history.scrollRestoration, 'auto');
}
for (const gesture of ['wheel', 'touchstart', 'pointerdown', 'keydown', 'pagehide']) {
    const run = scenario();
    run.emit('DOMContentLoaded');
    run.emit(gesture); run.emit('load'); run.emit('technical-dashboard-ready'); run.resize(); run.flush();
    assert.equal(run.calls.length, 0, gesture + ' cancels pending scrolling');
    assert.equal(run.window.history.scrollRestoration, 'auto');
}
const hidden = scenario({ hidden: true });
hidden.emit('DOMContentLoaded'); hidden.flush();
assert.equal(hidden.calls.length, 0, 'Never jump to a hidden analysis panel');
console.log('Market analysis reload positioning: passed');
