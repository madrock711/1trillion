const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const config = {};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../assets/market-private-config.js'), 'utf8'), { window: config });
const node = () => ({ hidden: false, disabled: false, dataset: {}, listeners: {}, textContent: '',
    addEventListener(k, fn) { this.listeners[k] = fn; } });
const nodes = Object.fromEntries(['kodex-private-auth', 'kodex-private-signin', 'kodex-private-signout',
    'kodex-google-signin', 'kodex-private-auth-status', 'kodex-private-flow-content'].map(k => [k, node()]));
let calls = [], status = 200, payload, pending;
const session = () => ({ authenticated: true, expiresAt: Math.floor(Date.now() / 1000) + 604800, csrfToken: 'a'.repeat(64) });
const ctx = { URL, Date, Number, Array, Boolean, Math, AbortController,
    privateAuthSession: null, privateAuthAttempt: 0, privateAuthExpiryTimer: null,
    privateFlowState: {}, privateFlowTimer: null, privateFlowRequestToken: 0, privateFlowController: null,
    selectedKodexFlow: 'off', selectedKodexChartMode: 'daily',
    document: { getElementById: k => nodes[k], querySelectorAll: () => [] },
    window: { location: { hostname: 'www.hpmplab.com' }, YEONMA_PRIVATE_AUTH: config.YEONMA_PRIVATE_AUTH,
        setTimeout() { return 1; }, clearTimeout() {}, addEventListener() {},
        fetch(url, options) { calls.push({ url, options }); return pending || Promise.resolve({ status, ok: status === 200, json: () => Promise.resolve(payload) }); },
        get localStorage() { throw Error('No credential persistence in localStorage'); },
        get sessionStorage() { throw Error('No credential persistence in sessionStorage'); } } };
vm.createContext(ctx);
vm.runInContext(source.slice(source.indexOf('    function isLocalPrivateFlowHost('), source.indexOf('    function flowSeconds(')), ctx);
ctx.clearPrivateFlowVisuals = () => {};
const flush = () => new Promise(r => setImmediate(r));
(async () => {
    const good = ctx.window.YEONMA_PRIVATE_AUTH;
    for (const url of ['http://www.hpmplab.com/api/private/nh/session/flow',
        'https://evil.example/api/private/nh/session/flow', good.apiUrl + '?token=bad',
        'https://www.hpmplab.com:8443/api/private/nh/session/flow']) {
        ctx.window.YEONMA_PRIVATE_AUTH = { ...good, apiUrl: url };
        assert.equal(ctx.privateAuthConfig(), null);
    }
    ctx.window.YEONMA_PRIVATE_AUTH = good;
    payload = session();
    ctx.authenticatePrivateFlow('mock-google-credential');
    await flush();
    assert.equal(calls.at(-1).options.method, 'POST');
    assert.equal(calls.at(-1).options.credentials, 'include');
    assert.equal(calls.at(-1).options.headers.Authorization, 'Bearer mock-google-credential');
    assert.equal(ctx.privateAuthSession.csrfToken, payload.csrfToken);
    assert(!JSON.stringify(ctx.privateAuthSession).includes('mock-google-credential'));
    assert(ctx.isPrivateFlowWaiting());
    ctx.privateAuthSession = null;
    await ctx.restorePrivateSession();
    assert(ctx.privateAuthSession);
    assert.equal(calls.at(-1).options.headers, undefined, 'restore uses cookie, not Google token');
    status = 503;
    await ctx.logoutPrivateSession();
    assert(ctx.privateAuthSession, 'failed server logout must not falsely report success');
    status = 200; payload = { authenticated: false };
    await ctx.logoutPrivateSession();
    assert.equal(ctx.privateAuthSession, null);
    assert.equal(calls.at(-1).options.headers['X-Yeonma-CSRF'], 'a'.repeat(64));
    status = 401;
    await ctx.restorePrivateSession();
    assert.equal(ctx.privateAuthSession, null);
    status = 200; payload = { ...session(), expiresAt: 1 };
    ctx.authenticatePrivateFlow('expired'); await flush();
    assert.equal(ctx.privateAuthSession, null);
    status = 403;
    ctx.authenticatePrivateFlow('wrong-owner'); await flush();
    assert.equal(ctx.privateAuthSession, null);
    assert.match(nodes['kodex-private-auth-status'].textContent, /볼 수 없습니다/);
    let resolve;
    pending = new Promise(r => { resolve = r; });
    ctx.authenticatePrivateFlow('late');
    ctx.resetPrivateAuth();
    resolve({ status: 200, ok: true, json: () => Promise.resolve(session()) });
    await flush();
    assert.equal(ctx.privateAuthSession, null, 'late login must not restore signed-out UI');
    pending = null;
    ctx.window.location.hostname = '127.0.0.1';
    assert(ctx.isPrivateFlowHost(), 'local NH server remains independent');
    assert(!ctx.isPrivateFlowWaiting());
    console.log('Cookie session frontend: login, restoration, expiry, server logout, failure, races and owner denial passed.');
})().catch(e => { console.error(e); process.exitCode = 1; });
