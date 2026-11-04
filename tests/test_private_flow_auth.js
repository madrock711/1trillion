const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../assets/market-dashboard.js'), 'utf8');
const configSource = fs.readFileSync(path.join(__dirname, '../assets/market-private-config.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '../articles/market.html'), 'utf8');
const headerHtml = html.slice(html.indexOf('<header>'), html.indexOf('</header>'));
assert.match(headerHtml, /id="kodex-private-auth"/, 'account control belongs in the page header');
assert.match(headerHtml, /id="kodex-private-auth-status"[^>]*role="status"[^>]*aria-live="polite"/);
assert.equal((html.match(/id="kodex-private-auth"/g) || []).length, 1, 'account controls must not be duplicated');
assert(!html.slice(html.indexOf('id="kodex-private-flow-panel"'), html.indexOf('id="kodex-history-chart"')).includes('id="kodex-private-auth"'),
    'the account control must no longer be nested in the chart');
assert(source.lastIndexOf('    bindPrivateAuth();') < source.lastIndexOf("    fetchJson(root.getAttribute('data-dashboard-source'))"),
    'header authentication must initialize before market-data fetch');
const loadedConfig = { window: {} };
vm.runInNewContext(configSource, loadedConfig);
assert.equal(loadedConfig.window.YEONMA_PRIVATE_AUTH.clientId, '343043233969-95mv3utlrbafcj1673dpl33ont9mh2j9.apps.googleusercontent.com');
assert.equal(loadedConfig.window.YEONMA_PRIVATE_AUTH.apiUrl, 'https://dfx1foieoh.execute-api.us-east-1.amazonaws.com/api/private/nh/flow');
assert.equal(loadedConfig.window.YEONMA_PRIVATE_AUTH.waitingForToken, true);
assert(html.indexOf('market-private-config.js') > 0 && html.indexOf('market-private-config.js') < html.indexOf('market-dashboard.js'),
    'the public config must load before the dashboard');
const start = source.indexOf('    function isLocalPrivateFlowHost(');
const end = source.indexOf('    function flowSeconds(', start);
assert(start >= 0 && end > start);

function node() {
    return { hidden: false, disabled: false, textContent: '', dataset: {}, listeners: {},
        addEventListener(type, callback) { this.listeners[type] = callback; }, remove() {} };
}
const nodes = Object.fromEntries(['kodex-private-auth', 'kodex-private-signin', 'kodex-private-signout',
    'kodex-google-signin', 'kodex-private-auth-status', 'kodex-private-flow-content', 'kodex-flow-legend', 'kodex-flow-status', 'kodex-flow-legend-unit',
    'kodex-flow-raw', 'kodex-history-readout'].map(id => [id, node()]));
const scripts = [];
const timers = [];
let fetchCall;
let fetchCalls = [];
let responseStatus = 200;
let fetchPromise;
const validPayload = { fetchedAt: '2026-11-04T02:00:00Z', market: 'UNT', amount: [], quantity: [] };
let responsePayload = { authenticated: true };
const context = {
    URL, Date, Number, Array, Boolean, AbortController,
    privateAuthToken: '', privateAuthExpiryTimer: null, privateAuthAttempt: 0,
    privateFlowState: {}, privateFlowTimer: null, privateFlowRequestToken: 0, privateFlowController: null,
    selectedKodexChartMode: 'daily', selectedKodexFlow: 'off',
    kodexIntradayRangePreview: null, displayedKodexFlowSource: '',
    document: { hidden: false, getElementById: id => nodes[id] || null, querySelectorAll: () => [],
        createElement: () => node(), head: { appendChild: element => scripts.push(element) } },
    window: { location: { hostname: 'www.hpmplab.com' },
        setTimeout: (_callback, delay) => { timers.push(delay); return timers.length; }, clearTimeout() {},
        fetch(url, options) { fetchCall = { url, options }; fetchCalls.push(fetchCall); return fetchPromise || Promise.resolve({
            status: responseStatus, ok: responseStatus === 200, json: () => Promise.resolve(responsePayload)
        }); },
        get localStorage() { throw new Error('credentials must not enter localStorage'); }
    }
};
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);
const stateStart = source.indexOf('    function updateKodexFlowState(');
const stateEnd = source.indexOf('    function renderKodexIntradayRows(', stateStart);
assert(stateStart >= 0 && stateEnd > stateStart);
vm.runInContext(source.slice(stateStart, stateEnd), context);
const flush = () => new Promise(resolve => setImmediate(resolve));

(async () => {
    assert.equal(context.privateAuthConfig(), null, 'absent config disables remote auth');
    context.window.YEONMA_PRIVATE_AUTH = { clientId: 'client.apps.googleusercontent.com', apiUrl: 'http://unsafe.example/api/private/nh/flow' };
    assert.equal(context.privateAuthConfig(), null, 'remote API must be HTTPS');
    context.window.YEONMA_PRIVATE_AUTH.apiUrl = 'https://dfx1foieoh.execute-api.us-east-1.amazonaws.com/api/private/nh/flow?token=bad';
    assert.equal(context.privateAuthConfig(), null, 'credentials must not be configured in query string');
    context.window.YEONMA_PRIVATE_AUTH.apiUrl = 'https://private.example/api/private/nh/flow';
    assert.equal(context.privateAuthConfig(), null, 'arbitrary HTTPS origins must not receive a Google token');
    context.window.YEONMA_PRIVATE_AUTH.apiUrl = 'https://a1b2c3d4e5.execute-api.us-east-1.amazonaws.com/api/private/nh/flow';
    assert.equal(context.privateAuthConfig(), null, 'another account API in the same region must not receive a Google token');
    context.window.YEONMA_PRIVATE_AUTH.apiUrl = 'https://a1b2c3d4e5.execute-api.us-east-1.amazonaws.com.attacker.example/api/private/nh/flow';
    assert.equal(context.privateAuthConfig(), null, 'suffix attacks must not receive a Google token');
    context.window.YEONMA_PRIVATE_AUTH.apiUrl = 'https://a1b2c3d4e5.execute-api.us-west-2.amazonaws.com/api/private/nh/flow';
    assert.equal(context.privateAuthConfig(), null, 'unexpected regions must not receive a Google token');
    context.window.YEONMA_PRIVATE_AUTH.apiUrl = 'https://dfx1foieoh.execute-api.us-east-1.amazonaws.com:8443/api/private/nh/flow';
    assert.equal(context.privateAuthConfig(), null, 'unexpected ports must not receive a Google token');
    context.window.YEONMA_PRIVATE_AUTH.apiUrl = 'https://dfx1foieoh.execute-api.us-east-1.amazonaws.com/api/private/nh/flow';
    context.window.YEONMA_PRIVATE_AUTH.sessionUrl = 'https://attacker.example/api/private/nh/session';
    assert(context.privateAuthConfig());
    assert.equal(context.privateAuthConfig().sessionUrl, 'https://dfx1foieoh.execute-api.us-east-1.amazonaws.com/api/private/nh/session',
        'session endpoint must derive only from the validated flow API origin');
    assert.equal(context.isPrivateFlowHost(), false, 'config alone does not grant access');
    context.bindPrivateAuth();
    assert.equal(scripts.length, 0, 'Google library must not load before user action');
    assert.equal(nodes['kodex-private-flow-content'].hidden, true);
    nodes['kodex-private-signin'].listeners.click();
    assert.equal(scripts.length, 1);
    assert.equal(scripts[0].src, 'https://accounts.google.com/gsi/client');
    scripts[0].onerror();
    assert.match(nodes['kodex-private-auth-status'].textContent, /불러오지 못했습니다/);

    responseStatus = 403;
    context.authenticatePrivateFlow('wrong-account-token');
    await flush();
    assert.equal(context.privateAuthToken, '');
    assert.equal(nodes['kodex-private-flow-content'].hidden, true);
    assert.match(nodes['kodex-private-auth-status'].textContent, /볼 수 없습니다/);

    responseStatus = 401;
    context.authenticatePrivateFlow('expired-token');
    await flush();
    assert.equal(context.privateAuthToken, '');
    assert.match(nodes['kodex-private-auth-status'].textContent, /만료/);
    responseStatus = 429;
    context.authenticatePrivateFlow('rate-limited-token');
    await flush();
    assert.equal(context.privateAuthToken, '');
    assert.match(nodes['kodex-private-auth-status'].textContent, /요청이 많습니다/);

    responseStatus = 200;
    responsePayload = { authenticated: false };
    context.authenticatePrivateFlow('unverified-token');
    await flush();
    assert.equal(context.privateAuthToken, '', 'a 200 response without a confirmed identity is insufficient');
    assert.equal(nodes['kodex-private-flow-content'].hidden, true);

    responsePayload = { authenticated: true };
    context.selectedKodexChartMode = 'intraday';
    context.selectedKodexFlow = 'amount';
    fetchCalls = [];
    context.authenticatePrivateFlow('owner-token');
    await flush();
    assert.equal(fetchCall.url, 'https://dfx1foieoh.execute-api.us-east-1.amazonaws.com/api/private/nh/session');
    assert.equal(fetchCalls.length, 1, 'login must never fetch NH flow automatically');
    assert.equal(fetchCall.options.headers.Authorization, 'Bearer owner-token');
    assert.equal(fetchCall.options.credentials, 'omit');
    assert.equal(context.privateAuthToken, 'owner-token');
    assert.equal(context.isPrivateFlowHost(), true);
    assert.equal(nodes['kodex-private-flow-content'].hidden, false);
    assert.equal(context.selectedKodexFlow, 'off', 'flow must wait for an explicit user selection');
    assert.equal(context.privateFlowState.status, 'idle', 'identity confirmation is not NH data');
    assert.match(nodes['kodex-private-auth-status'].textContent, /로그인했습니다/);
    context.window.YEONMA_PRIVATE_AUTH.waitingForToken = true;
    context.selectedKodexFlow = 'amount';
    context.privateFlowState = { status: 'ready', tradeDate: '2026-11-04', fetchedAt: '2026-11-04T02:00:00Z', market: '통합',
        amount: [{ prsn_val: 42 }], quantity: [{ prsn_val: 123 }] };
    fetchCalls = [];
    const timersBeforeWaiting = timers.length;
    context.schedulePrivateFlow(true);
    await flush();
    assert.equal(fetchCalls.length, 0, 'waiting mode must not call NH flow');
    assert.equal(timers.length, timersBeforeWaiting, 'waiting mode must not start a retry timer');
    assert.equal(context.privateFlowState.status, 'waiting-for-token');
    assert.equal(context.privateFlowState.amount.length, 0, 'waiting mode must discard any previously fetched data');
    assert.equal(context.privateFlowState.quantity.length, 0);
    assert.equal(nodes['kodex-flow-legend'].hidden, true);
    assert.equal(nodes['kodex-flow-raw'].hidden, true);
    assert.equal(nodes['kodex-flow-status'].textContent, '온라인 수급 연결을 기다리는 중입니다. PC 임시 서버는 계속 사용할 수 있습니다.');
    context.selectedKodexFlow = 'quantity';
    context.schedulePrivateFlow(false);
    assert.equal(fetchCalls.length, 0, 'quantity must also be paused');
    assert.equal(timers.length, timersBeforeWaiting, 'quantity must not schedule a delayed retry');
    context.window.YEONMA_PRIVATE_AUTH.waitingForToken = false;
    responseStatus = 503;
    context.selectedKodexFlow = 'amount';
    context.schedulePrivateFlow(true);
    await flush();
    assert.equal(fetchCall.url, 'https://dfx1foieoh.execute-api.us-east-1.amazonaws.com/api/private/nh/flow');
    assert.equal(context.privateAuthToken, 'owner-token', 'NH outage must not be treated as failed Google login');
    assert.equal(context.privateFlowState.status, 'error');
    assert.match(nodes['kodex-flow-status'].textContent, /NH 수급을 불러오지 못했습니다/);
    assert.doesNotMatch(nodes['kodex-flow-status'].textContent, /온라인 수급 연결을 기다리는 중/);
    assert.equal(nodes['kodex-private-flow-content'].hidden, false);
    responseStatus = 200;
    responsePayload = validPayload;
    context.schedulePrivateFlow(true);
    await flush();
    assert.equal(context.privateFlowState.status, 'ready', 'clearing the waiting flag resumes live updates');
    assert.equal(context.privateFlowState.fetchedAt, validPayload.fetchedAt);
    responseStatus = 401;
    context.selectedKodexChartMode = 'intraday';
    context.selectedKodexFlow = 'amount';
    context.schedulePrivateFlow(true);
    await flush();
    assert.equal(context.privateAuthToken, '', 'expired token must be discarded during refresh');
    assert.equal(nodes['kodex-private-flow-content'].hidden, true);
    responseStatus = 200;
    responsePayload = { authenticated: true };
    context.selectedKodexChartMode = 'daily';
    context.selectedKodexFlow = 'off';
    context.authenticatePrivateFlow('owner-token');
    await flush();
    nodes['kodex-private-signout'].listeners.click();
    assert.equal(context.privateAuthToken, '');
    assert.equal(context.privateFlowState.amount.length, 0);
    assert.equal(nodes['kodex-private-flow-content'].hidden, true);

    let resolveFetch;
    fetchPromise = new Promise(resolve => { resolveFetch = resolve; });
    context.authenticatePrivateFlow('late-token');
    context.resetPrivateAuth('signed out');
    resolveFetch({ status: 200, ok: true, json: () => Promise.resolve({ authenticated: true }) });
    await flush();
    assert.equal(context.privateAuthToken, '', 'late response must not restore logged-out session');
    let resolveOlder;
    fetchPromise = new Promise(resolve => { resolveOlder = resolve; });
    context.authenticatePrivateFlow('old-token');
    fetchPromise = null;
    context.authenticatePrivateFlow('new-token');
    await flush();
    assert.equal(context.privateAuthToken, 'new-token');
    resolveOlder({ status: 200, ok: true, json: () => Promise.resolve({ authenticated: true }) });
    await flush();
    assert.equal(context.privateAuthToken, 'new-token', 'an older login response must not replace a newer session');
    context.window.location.hostname = '127.0.0.1';
    assert.equal(context.isPrivateFlowHost(), true, 'local private mode remains available');
    context.window.YEONMA_PRIVATE_AUTH.waitingForToken = true;
    assert.equal(context.isPrivateFlowWaiting(), false, 'the PC local server is not paused');
    context.selectedKodexChartMode = 'intraday';
    context.selectedKodexFlow = 'quantity';
    responsePayload = validPayload;
    responseStatus = 200;
    context.schedulePrivateFlow(true);
    await flush();
    assert.equal(fetchCall.url, '/api/private/nh/flow', 'local PC continues to fetch from its loopback server');
    assert.equal(fetchCall.options.credentials, 'same-origin');
    console.log('Private Google flow: config, on-demand load, denial, success, logout and race handling ok');
})().catch(error => { console.error(error); process.exitCode = 1; });
