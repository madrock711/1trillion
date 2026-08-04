(function (root, factory) {
    'use strict';

    var api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    if (root) root.MarketDashboardLive = api;
}(typeof window !== 'undefined' ? window : null, function () {
    'use strict';

    var INDEX_CODES = ['KOSPI', 'KOSDAQ'];
    var STOCKS = [
        { id: 'KODEX', code: '122630', label: 'KODEX 레버리지', unit: '원' },
        { id: 'SAMSUNG', code: '005930', label: '삼성전자', unit: '원' },
        { id: 'HYNIX', code: '000660', label: 'SK하이닉스', unit: '원' }
    ];

    function parseNumber(value) {
        if (typeof value === 'number' && Number.isFinite(value)) return value;
        if (typeof value !== 'string') return NaN;
        var normalized = value.replace(/,/g, '').replace(/[^0-9+\-.]/g, '');
        if (!normalized) return NaN;
        return Number(normalized);
    }

    function kstParts(value) {
        var date = value instanceof Date ? value : new Date(value);
        if (!Number.isFinite(date.getTime())) throw new Error('시세 기준 시각이 올바르지 않습니다.');
        var formatter = new Intl.DateTimeFormat('en-CA', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hourCycle: 'h23'
        });
        var values = {};
        formatter.formatToParts(date).forEach(function (part) {
            if (part.type !== 'literal') values[part.type] = part.value;
        });
        return values;
    }

    function marketDateKey(value) {
        var parts = kstParts(value);
        return parts.year + parts.month + parts.day;
    }

    function formatAsOfLabel(value) {
        var parts = kstParts(value);
        return Number(parts.month) + '월 ' + Number(parts.day) + '일 ' + parts.hour + ':' + parts.minute + ' KST';
    }

    function formatAsOfDisplay(value) {
        var parts = kstParts(value);
        return parts.year + '년 ' + Number(parts.month) + '월 ' + Number(parts.day) + '일 ' + parts.hour + ':' + parts.minute + ' KST';
    }

    function formatShortTime(value) {
        var parts = kstParts(value);
        return parts.hour + ':' + parts.minute;
    }

    function signedValue(value, direction) {
        var number = parseNumber(value);
        if (!Number.isFinite(number)) return NaN;
        var directionCode = direction && String(direction.code);
        if (directionCode === '5' && number > 0) return -number;
        if (directionCode === '2' && number < 0) return Math.abs(number);
        return number;
    }

    function totalInfoMap(integration) {
        var result = {};
        (integration && Array.isArray(integration.totalInfos) ? integration.totalInfos : []).forEach(function (item) {
            if (item && item.code) result[item.code] = parseNumber(item.value);
        });
        return result;
    }

    function validatedPrices(basic, integration) {
        var totals = totalInfoMap(integration);
        var value = parseNumber(basic.closePrice);
        var previousClose = totals.lastClosePrice;
        var open = parseNumber(basic.openPrice);
        var high = parseNumber(basic.highPrice);
        var low = parseNumber(basic.lowPrice);

        if (!Number.isFinite(open)) open = totals.openPrice;
        if (!Number.isFinite(high)) high = totals.highPrice;
        if (!Number.isFinite(low)) low = totals.lowPrice;
        if (!Number.isFinite(previousClose)) {
            var change = signedValue(basic.compareToPreviousClosePrice, basic.compareToPreviousPrice);
            previousClose = value - change;
        }

        if (![value, previousClose, open, high, low].every(Number.isFinite)) {
            throw new Error('가격 데이터가 부족합니다.');
        }
        if (high < low || value < low || value > high || open < low || open > high) {
            throw new Error('가격 범위가 올바르지 않습니다.');
        }

        return {
            value: value,
            previousClose: previousClose,
            open: open,
            high: high,
            low: low
        };
    }

    function stateLabel(status) {
        if (status === 'OPEN') return '장중 시세';
        if (status === 'CLOSE') return '정규장 마감';
        if (status === 'PREOPEN') return '개장 전';
        return '최근 시세';
    }

    function normalizeIndex(code, basic, integration, now) {
        if (!basic || basic.itemCode !== code || !integration) throw new Error(code + ' 응답이 올바르지 않습니다.');
        var timestamp = Date.parse(basic.localTradedAt);
        if (!Number.isFinite(timestamp) || timestamp > now + 10 * 60 * 1000) throw new Error(code + ' 시각이 올바르지 않습니다.');
        var bizdate = integration.dealTrendInfo && String(integration.dealTrendInfo.bizdate || '');
        if (bizdate && bizdate !== marketDateKey(timestamp)) throw new Error(code + ' 수급 거래일이 일치하지 않습니다.');

        var prices = validatedPrices(basic, integration);
        var ratio = signedValue(basic.fluctuationsRatio, basic.compareToPreviousPrice);
        var trend = integration.dealTrendInfo || {};
        var breadth = integration.upDownStockInfo || {};
        var program = integration.programTrendInfo || {};

        return {
            id: code,
            label: code,
            symbol: code === 'KOSPI' ? 'K' : 'Q',
            value: prices.value,
            previousClose: prices.previousClose,
            open: prices.open,
            high: prices.high,
            low: prices.low,
            changePercent: ratio,
            asOf: new Date(timestamp).toISOString(),
            asOfLabel: formatAsOfLabel(timestamp),
            shortTimeLabel: formatShortTime(timestamp),
            stateLabel: stateLabel(basic.marketStatus),
            marketStatus: basic.marketStatus,
            flows: [
                { label: '외국인', value: parseNumber(trend.foreignValue), unit: '억원' },
                { label: '기관', value: parseNumber(trend.institutionalValue), unit: '억원' },
                { label: '개인', value: parseNumber(trend.personalValue), unit: '억원' }
            ],
            breadth: {
                advance: parseNumber(breadth.upperCount) + parseNumber(breadth.riseCount),
                flat: parseNumber(breadth.steadyCount),
                decline: parseNumber(breadth.lowerCount) + parseNumber(breadth.fallCount)
            },
            program: {
                arbitrage: parseNumber(program.indexDifferenceReal),
                nonArbitrage: parseNumber(program.indexBiDifferenceReal),
                total: parseNumber(program.indexTotalReal),
                unit: '억원'
            }
        };
    }

    function normalizeStock(definition, basic, integration, now) {
        if (!basic || String(basic.itemCode) !== definition.code || !integration) {
            throw new Error(definition.label + ' 응답이 올바르지 않습니다.');
        }
        var timestamp = Date.parse(basic.localTradedAt);
        if (!Number.isFinite(timestamp) || timestamp > now + 10 * 60 * 1000) {
            throw new Error(definition.label + ' 시각이 올바르지 않습니다.');
        }
        var prices = validatedPrices(basic, integration);
        return {
            id: definition.id,
            label: definition.label,
            unit: definition.unit,
            value: prices.value,
            previousClose: prices.previousClose,
            open: prices.open,
            high: prices.high,
            low: prices.low,
            changePercent: signedValue(basic.fluctuationsRatio, basic.compareToPreviousPrice),
            asOf: new Date(timestamp).toISOString(),
            asOfLabel: formatAsOfLabel(timestamp),
            shortTimeLabel: formatShortTime(timestamp),
            stateLabel: stateLabel(basic.marketStatus),
            marketStatus: basic.marketStatus
        };
    }

    function withCacheBust(url, nonce) {
        var separator = url.indexOf('?') === -1 ? '?' : '&';
        return url + separator + '_=' + encodeURIComponent(nonce);
    }

    function fetchJson(fetchImpl, url, signal, nonce) {
        return fetchImpl(withCacheBust(url, nonce), {
            cache: 'no-store',
            credentials: 'same-origin',
            signal: signal
        }).then(function (response) {
            if (!response.ok) throw new Error('최신 시세를 불러오지 못했습니다.');
            return response.json();
        });
    }

    function fetchPair(fetchImpl, baseUrl, category, code, signal, nonce) {
        var prefix = new URL(category + '/' + code + '/', baseUrl).href;
        return Promise.all([
            fetchJson(fetchImpl, prefix + 'basic', signal, nonce),
            fetchJson(fetchImpl, prefix + 'integration', signal, nonce)
        ]);
    }

    function fetchLatest(baseUrl, fetchImpl, options) {
        var settings = options || {};
        var now = Number.isFinite(settings.now) ? settings.now : Date.now();
        var nonce = settings.nonce || String(now);
        var signal = settings.signal;
        var indexRequests = INDEX_CODES.map(function (code) {
            return fetchPair(fetchImpl, baseUrl, 'index', code, signal, nonce).then(function (parts) {
                return normalizeIndex(code, parts[0], parts[1], now);
            });
        });
        var stockRequests = STOCKS.map(function (stock) {
            return fetchPair(fetchImpl, baseUrl, 'stock', stock.code, signal, nonce).then(function (parts) {
                return normalizeStock(stock, parts[0], parts[1], now);
            });
        });

        return Promise.all(indexRequests.concat(stockRequests)).then(function (items) {
            var markets = items.slice(0, INDEX_CODES.length);
            var instruments = items.slice(INDEX_CODES.length);
            var timestamps = items.map(function (item) { return Date.parse(item.asOf); });
            var newest = Math.max.apply(Math, timestamps);
            var statuses = markets.map(function (market) { return market.marketStatus; });
            var marketState = statuses.every(function (status) { return status === 'CLOSE'; })
                ? '한국 정규장 마감'
                : statuses.some(function (status) { return status === 'OPEN'; })
                    ? '한국 정규장 장중'
                    : '최근 거래일 시세';

            return {
                asOf: new Date(newest).toISOString(),
                asOfDisplay: formatAsOfDisplay(newest),
                marketState: marketState,
                markets: markets,
                instruments: instruments,
                program: markets[0].program,
                sourceLabel: 'Naver Finance의 KRX 공개 시세·수급'
            };
        });
    }

    return {
        fetchLatest: fetchLatest,
        normalizeIndex: normalizeIndex,
        normalizeStock: normalizeStock,
        parseNumber: parseNumber,
        formatAsOfDisplay: formatAsOfDisplay
    };
}));
