const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const entry = process.env.BREATH_QA_URL || pathToFileURL(path.resolve(__dirname, '../app.html')).href;
const storageKey = 'breathing:settings:v1';

async function instrumentAudio(page) {
    await page.addInitScript(() => {
        const NativeAudioContext = window.AudioContext || window.webkitAudioContext;
        window.breathAudioTrace = { oscillators: [], gains: [] };
        function traceParam(param) {
            const events = [];
            for (const method of ['setValueAtTime', 'linearRampToValueAtTime', 'exponentialRampToValueAtTime',
                'setTargetAtTime', 'cancelAndHoldAtTime', 'cancelScheduledValues']) {
                if (typeof param[method] !== 'function') continue;
                const original = param[method].bind(param);
                param[method] = (...args) => { events.push({ method, args }); return original(...args); };
            }
            return events;
        }
        window.AudioContext = class extends NativeAudioContext {
            createOscillator() {
                const node = super.createOscillator();
                const record = { frequency: traceParam(node.frequency), starts: 0, stops: 0 };
                for (const [method, key] of [['start', 'starts'], ['stop', 'stops']]) {
                    const original = node[method].bind(node);
                    node[method] = (...args) => {
                        record[key]++;
                        record.type = node.type;
                        return original(...args);
                    };
                }
                window.breathAudioTrace.oscillators.push(record);
                return node;
            }
            createGain() {
                const node = super.createGain();
                window.breathAudioTrace.gains.push(traceParam(node.gain));
                const connect = node.connect.bind(node);
                node.connect = (destination, ...args) => {
                    const result = connect(destination, ...args);
                    if (destination === this.destination) {
                        const analyser = this.createAnalyser();
                        analyser.fftSize = 32768;
                        connect(analyser);
                        window.breathOutputProbe = analyser;
                    }
                    return result;
                };
                return node;
            }
        };
    });
}

async function setVolume(page, value) {
    await page.locator('#br-volume').evaluate((el, v) => {
        el.value = String(v);
        el.dispatchEvent(new Event('input', { bubbles: true }));
    }, value);
}

async function measureOutput(page) {
    await page.waitForTimeout(1000);
    return page.evaluate(() => {
        const probe = window.breathOutputProbe;
        const samples = new Float32Array(probe.fftSize);
        probe.getFloatTimeDomainData(samples);
        let peak = 0, squares = 0;
        for (const sample of samples) {
            peak = Math.max(peak, Math.abs(sample));
            squares += sample * sample;
        }
        return { peak, rms: Math.sqrt(squares / samples.length) };
    });
}

async function checkLayout(page, width, lang) {
    await page.setViewportSize({ width, height: 1000 });
    await page.evaluate(lang => window.appI18n.setLang(lang), lang);
    const result = await page.evaluate(() => {
        const rect = selector => document.querySelector(selector).getBoundingClientRect();
        const button = document.querySelector('.br-speaker-tone');
        const tone = rect('.br-speaker-tone');
        const map = rect('.br-chakra-map');
        const circle = rect('.br-circle');
        const volume = rect('.br-volume-column');
        const main = rect('.br-timer-main');
        const controls = rect('.br-controls');
        return {
            separate: tone.top >= map.bottom,
            fits: button.scrollWidth <= button.clientWidth && button.scrollHeight <= button.clientHeight,
            ordered: map.right <= circle.left && circle.right <= volume.left,
            centered: Math.abs((circle.left + circle.right - main.left - main.right) / 2) < 2,
            noOverlap: tone.bottom <= controls.top,
            visible: tone.left >= 0 && tone.right <= window.innerWidth,
            blueVolume: getComputedStyle(document.getElementById('br-volume')).accentColor === 'rgb(59, 130, 246)'
        };
    });
    for (const [key, value] of Object.entries(result)) assert(value, `${key} at ${width}px / ${lang}`);
    if (process.env.BREATH_QA_DIR) {
        fs.mkdirSync(process.env.BREATH_QA_DIR, { recursive: true });
        await page.locator('.br-wrapper').screenshot({ path: path.join(process.env.BREATH_QA_DIR, `speaker-tone-${width}-${lang}.png`) });
    }
}

(async () => {
    const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--mute-audio'] });
    try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
        await instrumentAudio(page);
        await page.goto(entry, { waitUntil: 'load' });
        await page.locator('.br-embed[data-br-initialized="1"]').waitFor();
        await page.evaluate(key => { localStorage.removeItem(key); }, storageKey);
        await page.reload({ waitUntil: 'load' });
        assert.equal(await page.locator('.br-chakra-map [data-chakra]').count(), 7);
        assert(await page.locator('#br-speaker-note').isHidden());

        await setVolume(page, 0.3);
        await page.locator('.br-speaker-tone span').first().click();
        assert.equal(await page.locator('[data-chakra][aria-pressed="true"]').count(), 1);
        assert.equal(await page.locator('#br-chakra-frequency').textContent(), '\uC2A4\uD53C\uCEE4 \uCCAD\uC18C \u00B7 165Hz');
        assert(await page.locator('#br-speaker-note').isVisible());
        assert.equal(await page.locator('#br-volume').inputValue(), '0.3', 'selection must not raise volume');
        assert.equal(await page.evaluate(() => window.breathAudioTrace.oscillators.length), 0, 'selection must not autoplay');

        for (const width of [1280, 768, 390, 320]) {
            for (const lang of ['ko', 'en']) await checkLayout(page, width, lang);
        }
        await page.evaluate(() => window.appI18n.setLang('en'));
        assert.equal(await page.locator('#br-chakra-frequency').textContent(), 'Speaker cleaning \u00B7 165Hz');
        await page.locator('#br-in-sec').fill('1');
        await page.locator('#br-start').click();
        await page.waitForFunction(() => Number(document.getElementById('br-round').textContent) >= 3);
        let trace = await page.evaluate(() => window.breathAudioTrace);
        assert.equal(trace.oscillators.length, 1, 'phase transitions must reuse the same speaker oscillator');
        assert.equal(trace.oscillators[0].type, 'sine');
        assert.deepEqual(trace.oscillators[0].frequency.map(event => [event.method, event.args[0]]), [['setValueAtTime', 165]]);
        assert.equal(trace.oscillators[0].stops, 0);
        assert(trace.gains.some(events => events.some(event => event.method === 'exponentialRampToValueAtTime')), 'fade-in remains enabled');
        assert(trace.gains.some(events => events.some(event => event.method === 'exponentialRampToValueAtTime' && event.args[0] === 0.9)), 'speaker tone uses higher gain');
        await setVolume(page, 1);
        const fullOutput = await measureOutput(page);
        assert(Math.abs(fullOutput.peak - 0.9) < 0.01, 'maximum speaker output is 0.9, not the old 0.22 ceiling');
        assert(Math.abs(fullOutput.rms - 0.9 / Math.sqrt(2)) < 0.01, 'output remains an undistorted sine wave');
        assert(fullOutput.peak < 1, 'maximum output leaves digital clipping headroom');
        await setVolume(page, 0.5);
        const halfOutput = await measureOutput(page);
        assert(Math.abs(halfOutput.peak / fullOutput.peak - 0.5) < 0.01, 'volume slider still scales boosted output');

        const measuredHz = await page.evaluate(async frequency => {
            const ctx = new OfflineAudioContext(1, 96000, 48000);
            const oscillator = ctx.createOscillator();
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(frequency, 0);
            oscillator.connect(ctx.destination);
            oscillator.start();
            const samples = (await ctx.startRendering()).getChannelData(0);
            let crossings = 0;
            for (let i = 48001; i < samples.length; i++) if (samples[i - 1] < 0 && samples[i] >= 0) crossings++;
            return crossings;
        }, trace.oscillators[0].frequency[0].args[0]);
        assert(Math.abs(measuredHz - 165) <= 1, 'rendered fixed tone must measure 165Hz');

        await setVolume(page, 0);
        trace = await page.evaluate(() => window.breathAudioTrace);
        assert(trace.gains.some(events => events.some(event => event.method === 'setTargetAtTime' && event.args[0] === 0)), 'volume reaches mute through smoothing');
        assert((await measureOutput(page)).peak < 0.001, 'boosted speaker tone still mutes completely');
        await page.locator('#br-start').click();
        assert.equal((await page.evaluate(() => window.breathAudioTrace.oscillators[0].stops)), 1, 'pause stops the tone');
        await page.locator('#br-start').click();
        assert.equal((await page.evaluate(() => window.breathAudioTrace.oscillators.length)), 2, 'resume creates a fresh tone');
        await page.locator('#br-reset').click();
        assert.equal(await page.locator('#br-total').textContent(), '00:00');
        assert.equal((await page.evaluate(() => window.breathAudioTrace.oscillators[1].stops)), 1, 'reset stops the tone');

        await page.reload({ waitUntil: 'load' });
        assert.equal(await page.locator('.br-speaker-tone').getAttribute('aria-pressed'), 'true', 'preset is restored');
        assert.equal(await page.locator('#br-volume').inputValue(), '0', 'mute is restored');
        assert.equal(await page.evaluate(() => window.breathAudioTrace.oscillators.length), 0, 'restoring settings must not autoplay');
        await page.locator('#br-start').click();
        await setVolume(page, 1);
        await page.locator('[data-chakra="root"]').click();
        assert(await page.locator('#br-speaker-note').isHidden());
        trace = await page.evaluate(() => window.breathAudioTrace);
        assert(trace.oscillators[0].frequency.some(event => event.method === 'setTargetAtTime' && event.args[0] === 396), 'live preset switching retunes smoothly');
        assert(trace.gains.some(events => events.some(event => event.method === 'setTargetAtTime' && event.args[0] === 0.22)), 'switching back to chakra restores the original gain smoothly');
        await page.waitForFunction(() => window.breathAudioTrace.oscillators.length >= 3);
        trace = await page.evaluate(() => window.breathAudioTrace);
        for (const startHz of [396 * 0.6875, 396 * 1.7778]) {
            assert(trace.oscillators.some(tone => tone.frequency.some(event => event.method === 'setValueAtTime' && event.args[0] === startHz)), 'chakra pitch sweeps remain enabled in both phases');
        }
        assert(trace.gains.at(-1).some(event => event.method === 'exponentialRampToValueAtTime' && event.args[0] === 0.22), 'new chakra phases keep their original gain');
        await page.locator('.br-speaker-tone').click();
        trace = await page.evaluate(() => window.breathAudioTrace);
        assert(trace.oscillators.at(-1).frequency.some(event => event.method === 'setTargetAtTime' && event.args[0] === 165));
        assert(trace.gains.at(-1).some(event => event.method === 'setTargetAtTime' && event.args[0] === 0.9), 'switching live to speaker tone raises gain smoothly');
        assert(Math.abs((await measureOutput(page)).peak - 0.9) < 0.01, 'live switching also reaches full speaker output');
        await page.locator('#br-start').click();
        console.log('Speaker tone: 165Hz sine, measured peak 0.9 without clipping, proportional volume/mute, smooth preset gains, continuous phases, pause/reset, persistence, no autoplay, chakra sweeps and layouts passed (320/390/768/1280px, ko/en).');
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
