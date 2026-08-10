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
    var kodexHistoryCache = {
        value: null,
        expiresAt: 0,
        pending: null
    };
    var tqqqHistoryCache = {
        value: null,
        expiresAt: 0,
        pending: null
    };
    var kospiPriceHistoryCache = {
        value: null,
        expiresAt: 0,
        pending: null
    };
    var kospiForeignFlowPageCache = {};
    var kospiIntradayDayCache = {};
    var kospiMinutePressureDayCache = {};
    var tqqqIntradayOneMinuteCache = {
        value: null,
        expiresAt: 0,
        pending: null
    };
    var tqqqIntradayFiveMinuteCache = {
        value: null,
        expiresAt: 0,
        pending: null
    };
    var kodexVolumePressureCache = {
        value: null,
        expiresAt: 0,
        pending: null
    };
    var kodexIntradayIndexCache = {
        value: null,
        expiresAt: 0,
        pending: null
    };
    var kodexIntradayDayCache = {};

    function parseNumber(value) {
        if (typeof value === 'number' && Number.isFinite(value)) return value;
        if (typeof value !== 'string') return NaN;
        var normalized = value.replace(/,/g, '').replace(/[^0-9+\-.]/g, '');
        if (!normalized) return NaN;
        return Number(normalized);
    }

    function parseSourceTimestamp(value) {
        var direct = Date.parse(value);
        if (Number.isFinite(direct)) return direct;
        var match = /^(\d{4}-\d{2}-\d{2})\s+(오전|오후)\s+(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(String(value || '').trim());
        if (!match) return NaN;
        var hour = Number(match[3]);
        if (match[2] === '오후' && hour < 12) hour += 12;
        if (match[2] === '오전' && hour === 12) hour = 0;
        return Date.parse(match[1] + 'T' + String(hour).padStart(2, '0') + ':' + match[4] + ':' + (match[5] || '00') + '+09:00');
    }

    function seoulDate(now) {
        var parts = new Intl.DateTimeFormat('en-CA', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        }).formatToParts(new Date(now));
        var values = {};
        parts.forEach(function (part) { values[part.type] = part.value; });
        return values.year + '-' + values.month + '-' + values.day;
    }

    function normalCdf(value) {
        var absolute = Math.abs(value) / Math.sqrt(2);
        var t = 1 / (1 + 0.3275911 * absolute);
        var polynomial = (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t;
        var erf = 1 - polynomial * Math.exp(-absolute * absolute);
        return 0.5 * (1 + (value < 0 ? -erf : erf));
    }

    function sampleSigma(values) {
        if (!Array.isArray(values) || values.length < 2) return NaN;
        var average = values.reduce(function (total, value) { return total + value; }, 0) / values.length;
        var variance = values.reduce(function (total, value) {
            var distance = value - average;
            return total + distance * distance;
        }, 0) / (values.length - 1);
        return Math.sqrt(variance);
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

    function totalInfoTextMap(integration) {
        var result = {};
        (integration && Array.isArray(integration.totalInfos) ? integration.totalInfos : []).forEach(function (item) {
            if (item && item.code) result[item.code] = item.value == null ? '' : String(item.value);
        });
        return result;
    }

    function normalizeInvestorTrends(integration) {
        return (integration && Array.isArray(integration.dealTrendInfos) ? integration.dealTrendInfos : [])
            .map(function (trend) {
                var dateKey = trend && String(trend.bizdate || '');
                var values = {
                    foreign: parseNumber(trend && trend.foreignerPureBuyQuant),
                    institution: parseNumber(trend && trend.organPureBuyQuant),
                    individual: parseNumber(trend && trend.individualPureBuyQuant),
                    close: parseNumber(trend && trend.closePrice),
                    volume: parseNumber(trend && trend.accumulatedTradingVolume)
                };
                if (!/^\d{8}$/.test(dateKey) || !Object.keys(values).every(function (key) {
                    return Number.isFinite(values[key]);
                })) return null;
                return {
                    date: dateKey,
                    foreign: values.foreign,
                    institution: values.institution,
                    individual: values.individual,
                    close: values.close,
                    volume: values.volume
                };
            })
            .filter(Boolean)
            .slice(0, 5);
    }

    function normalizeKodexPriceHistory(payloads) {
        var rowsByDate = {};
        (payloads || []).forEach(function (payload) {
            var rows = payload && payload.isSuccess && Array.isArray(payload.result) ? payload.result : [];
            rows.forEach(function (row) {
                var date = row && String(row.localTradedAt || '');
                var normalized = {
                    date: date,
                    open: parseNumber(row && row.openPrice),
                    high: parseNumber(row && row.highPrice),
                    low: parseNumber(row && row.lowPrice),
                    close: parseNumber(row && row.closePrice),
                    volume: parseNumber(row && row.accumulatedTradingVolume)
                };
                if (!/^\d{4}-\d{2}-\d{2}$/.test(date)
                    || ![normalized.open, normalized.high, normalized.low, normalized.close, normalized.volume].every(Number.isFinite)
                    || normalized.volume <= 0
                    || normalized.high < Math.max(normalized.open, normalized.close)
                    || normalized.low > Math.min(normalized.open, normalized.close)) return;
                var previous = rowsByDate[date];
                if (!previous || normalized.volume >= previous.volume) rowsByDate[date] = normalized;
            });
        });
        return Object.keys(rowsByDate).sort().map(function (date) { return rowsByDate[date]; });
    }

    function normalizeKospiPriceHistory(payload) {
        var rowsByDate = {};
        var itemPattern = /<item\s+data=["']([^"']+)["'][^>]*\/>/gi;
        var match;
        while ((match = itemPattern.exec(String(payload || '')))) {
            var parts = match[1].split('|');
            if (parts.length < 6 || !/^\d{8}$/.test(parts[0])) continue;
            var row = {
                date: parts[0].slice(0, 4) + '-' + parts[0].slice(4, 6) + '-' + parts[0].slice(6, 8),
                open: parseNumber(parts[1]),
                high: parseNumber(parts[2]),
                low: parseNumber(parts[3]),
                close: parseNumber(parts[4]),
                volume: parseNumber(parts[5])
            };
            if (![row.open, row.high, row.low, row.close, row.volume].every(Number.isFinite)
                || row.volume <= 0
                || row.high < Math.max(row.open, row.close)
                || row.low > Math.min(row.open, row.close)) continue;
            rowsByDate[row.date] = row;
        }
        return Object.keys(rowsByDate).sort().map(function (date) { return rowsByDate[date]; });
    }

    function normalizeKospiForeignFlowHtml(payload) {
        var rowsByDate = {};
        var rowPattern = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
        var rowMatch;
        while ((rowMatch = rowPattern.exec(String(payload || '')))) {
            var dateMatch = /<td[^>]*class=["'][^"']*\bdate2\b[^"']*["'][^>]*>\s*(\d{2})\.(\d{2})\.(\d{2})\s*<\/td>/i.exec(rowMatch[1]);
            if (!dateMatch) continue;
            var cells = [];
            var cellPattern = /<td[^>]*>([\s\S]*?)<\/td>/gi;
            var cellMatch;
            while ((cellMatch = cellPattern.exec(rowMatch[1]))) {
                cells.push(cellMatch[1].replace(/<[^>]+>/g, '').replace(/&nbsp;/gi, ' ').trim());
            }
            if (cells.length < 4) continue;
            var normalized = {
                date: '20' + dateMatch[1] + '-' + dateMatch[2] + '-' + dateMatch[3],
                personal: parseNumber(cells[1]),
                foreign: parseNumber(cells[2]),
                institution: parseNumber(cells[3]),
                unit: '억원'
            };
            if (![normalized.personal, normalized.foreign, normalized.institution].every(Number.isFinite)) continue;
            rowsByDate[normalized.date] = normalized;
        }
        return Object.keys(rowsByDate).sort().map(function (date) { return rowsByDate[date]; });
    }

    function mergeKospiTechnicalHistory(priceRows, flowRows) {
        var flowsByDate = {};
        (flowRows || []).forEach(function (row) {
            if (row && /^\d{4}-\d{2}-\d{2}$/.test(row.date)) flowsByDate[row.date] = row;
        });
        return (priceRows || []).map(function (row) {
            var flow = flowsByDate[row.date];
            return {
                date: row.date,
                open: row.open,
                high: row.high,
                low: row.low,
                close: row.close,
                volume: row.volume,
                foreign: flow && Number.isFinite(flow.foreign) ? flow.foreign : null,
                institution: flow && Number.isFinite(flow.institution) ? flow.institution : null,
                personal: flow && Number.isFinite(flow.personal) ? flow.personal : null,
                flowUnit: '억원'
            };
        });
    }

    function normalizeIsoDate(value) {
        var raw = String(value || '').trim();
        if (/^\d{8}$/.test(raw)) {
            return raw.slice(0, 4) + '-' + raw.slice(4, 6) + '-' + raw.slice(6, 8);
        }
        return /^\d{4}-\d{2}-\d{2}$/.test(raw) ? raw : '';
    }

    function isKospiRegularSessionTime(value) {
        return /^\d{2}:\d{2}$/.test(value) && value >= '09:00' && value <= '15:30';
    }

    function normalizeKospiIntradayMinute(payload, expectedDate) {
        var decoded = payload;
        if (!Array.isArray(decoded)) {
            try {
                decoded = JSON.parse(String(payload || ''));
            } catch (error) {
                throw new Error('KOSPI 분봉 응답이 올바르지 않습니다.');
            }
        }
        if (!Array.isArray(decoded)) throw new Error('KOSPI 분봉 응답이 올바르지 않습니다.');
        var expected = normalizeIsoDate(expectedDate);
        var rowsByTimestamp = {};
        decoded.forEach(function (row) {
            var timestamp = row && String(row.localDateTime || '');
            if (!/^\d{14}$/.test(timestamp)) return;
            var date = normalizeIsoDate(timestamp.slice(0, 8));
            var time = timestamp.slice(8, 10) + ':' + timestamp.slice(10, 12);
            var normalized = {
                date: date,
                timestamp: timestamp,
                time: time,
                open: parseNumber(row && row.openPrice),
                high: parseNumber(row && row.highPrice),
                low: parseNumber(row && row.lowPrice),
                close: parseNumber(row && row.currentPrice),
                volume: parseNumber(row && row.accumulatedTradingVolume)
            };
            if ((expected && date !== expected)
                || !isKospiRegularSessionTime(time)
                || ![normalized.open, normalized.high, normalized.low, normalized.close, normalized.volume].every(Number.isFinite)
                || normalized.volume < 0
                || normalized.high < Math.max(normalized.open, normalized.close)
                || normalized.low > Math.min(normalized.open, normalized.close)) return;
            rowsByTimestamp[timestamp] = normalized;
        });
        return Object.keys(rowsByTimestamp).sort().map(function (timestamp) { return rowsByTimestamp[timestamp]; });
    }

    function estimateBvcPressureDays(days) {
        var normalizedDays = (days || []).map(function (day) {
            return {
                date: normalizeIsoDate(day && day.date),
                sourceLastAt: day && day.sourceLastAt || null,
                bars: (day && day.bars || []).filter(function (row) {
                    return row && /^\d{2}:\d{2}$/.test(String(row.time || ''))
                        && [row.open, row.high, row.low, row.close, row.volume].every(Number.isFinite)
                        && row.volume >= 0;
                }).slice().sort(function (left, right) { return left.time.localeCompare(right.time); })
            };
        }).filter(function (day) { return day.date && day.bars.length > 1; });
        var changes = [];
        normalizedDays.forEach(function (day) {
            day.bars.slice(1).forEach(function (row, index) {
                changes.push(row.close - day.bars[index].close);
            });
        });
        var sigma = sampleSigma(changes);
        if (!Number.isFinite(sigma) || sigma <= 0) throw new Error('분봉 변동성을 계산할 수 없습니다.');
        return normalizedDays.map(function (day) {
            var cumulativeDelta = 0;
            var bars = day.bars.map(function (row, index) {
                var neutral = index === 0 || row.time >= '15:20';
                var buyShare = neutral ? 0.5 : normalCdf((row.close - day.bars[index - 1].close) / sigma);
                var estimatedBuyVolume = Math.max(0, Math.min(row.volume, Math.round(row.volume * buyShare)));
                var estimatedSellVolume = row.volume - estimatedBuyVolume;
                var delta = estimatedBuyVolume - estimatedSellVolume;
                cumulativeDelta += delta;
                return {
                    time: row.time,
                    open: row.open,
                    high: row.high,
                    low: row.low,
                    close: row.close,
                    volume: row.volume,
                    estimatedBuyVolume: estimatedBuyVolume,
                    estimatedSellVolume: estimatedSellVolume,
                    delta: delta,
                    cumulativeDelta: cumulativeDelta,
                    neutral: neutral
                };
            });
            return {
                date: day.date,
                interval: '1m',
                sourceLastAt: day.sourceLastAt,
                minuteVolume: bars.reduce(function (total, row) { return total + row.volume; }, 0),
                sigma: sigma,
                sigmaSampleSize: changes.length,
                bars: bars
            };
        });
    }

    function calculateCompositeVolumeMomentum(kospiDays, kodexDays, options) {
        var settings = options || {};
        var varianceAlpha = Number.isFinite(settings.varianceAlpha) ? settings.varianceAlpha : 2 / 121;
        var fastPeriod = Number.isFinite(settings.fastPeriod) ? settings.fastPeriod : 15;
        var slowPeriod = Number.isFinite(settings.slowPeriod) ? settings.slowPeriod : 60;
        var signalPeriod = Number.isFinite(settings.signalPeriod) ? settings.signalPeriod : 15;
        var kospiByDate = {};
        var kodexByDate = {};
        (kospiDays || []).forEach(function (day) { if (day && day.date) kospiByDate[day.date] = day; });
        (kodexDays || []).forEach(function (day) { if (day && day.date) kodexByDate[day.date] = day; });
        var commonDates = Object.keys(kospiByDate).filter(function (date) { return Boolean(kodexByDate[date]); }).sort();
        var kospiVariance = null;
        var kodexVariance = null;
        var fast = null;
        var slow = null;
        var signal = null;

        function normalizePressure(value, variance) {
            var floor = 0.02;
            var scale = Math.sqrt(Math.max(Number.isFinite(variance) ? variance : value * value, floor * floor));
            var z = Math.max(-3, Math.min(3, value / scale));
            return Math.tanh(z / 2);
        }
        function nextVariance(previous, value) {
            return Number.isFinite(previous)
                ? varianceAlpha * value * value + (1 - varianceAlpha) * previous
                : Math.max(value * value, 0.02 * 0.02);
        }
        function nextEma(previous, value, period) {
            var alpha = 2 / (period + 1);
            return previous === null ? value : value * alpha + previous * (1 - alpha);
        }

        return commonDates.map(function (date) {
            var kospiBars = {};
            var kodexBars = {};
            (kospiByDate[date].bars || []).forEach(function (row) { kospiBars[row.time] = row; });
            (kodexByDate[date].bars || []).forEach(function (row) { kodexBars[row.time] = row; });
            var times = Object.keys(kospiBars).filter(function (time) { return Boolean(kodexBars[time]); }).sort();
            var bars = times.map(function (time) {
                var kospi = kospiBars[time];
                var kodex = kodexBars[time];
                var kospiPressure = Number.isFinite(kospi.delta) ? kospi.delta / Math.max(kospi.volume, 1) : 0;
                var kodexPressure = Number.isFinite(kodex.delta) ? kodex.delta / Math.max(kodex.volume, 1) : 0;
                var kospiScore = normalizePressure(kospiPressure, kospiVariance);
                var kodexScore = normalizePressure(kodexPressure, kodexVariance);
                kospiVariance = nextVariance(kospiVariance, kospiPressure);
                kodexVariance = nextVariance(kodexVariance, kodexPressure);
                var direction = 50 * (kospiScore + kodexScore);
                var divergence = 50 * (kodexScore - kospiScore);
                fast = nextEma(fast, direction, fastPeriod);
                slow = nextEma(slow, direction, slowPeriod);
                var momentum = fast - slow;
                signal = nextEma(signal, momentum, signalPeriod);
                return {
                    date: date,
                    sessionDate: date,
                    time: time,
                    kospiPressure: kospiPressure,
                    kodexPressure: kodexPressure,
                    kospiScore: kospiScore * 100,
                    kodexScore: kodexScore * 100,
                    direction: direction,
                    divergence: divergence,
                    momentum: momentum,
                    signal: signal
                };
            });
            var tail = bars.slice(-30);
            function average(key) {
                return tail.length ? tail.reduce(function (total, row) { return total + row[key]; }, 0) / tail.length : NaN;
            }
            return {
                date: date,
                sourceLastAt: [kospiByDate[date].sourceLastAt, kodexByDate[date].sourceLastAt].filter(Boolean).sort().pop() || null,
                bars: bars,
                summary: {
                    direction: average('direction'),
                    momentum: average('momentum'),
                    signal: average('signal'),
                    divergence: average('divergence')
                }
            };
        }).filter(function (day) { return day.bars.length > 1; });
    }

    function normalizeKospiIntradayForeignFlowHtml(payload, expectedDate) {
        var raw = String(payload || '');
        var expected = normalizeIsoDate(expectedDate);
        var payloadDateMatch = /\bbizdate=(\d{8})/i.exec(raw.replace(/&amp;/gi, '&'));
        var payloadDate = payloadDateMatch ? normalizeIsoDate(payloadDateMatch[1]) : '';
        var date = expected || payloadDate;
        if (expected && payloadDate && expected !== payloadDate) {
            throw new Error('선택한 거래일과 KOSPI 장중 수급 날짜가 다릅니다.');
        }
        var rowsByTime = {};
        var rowPattern = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
        var rowMatch;
        while ((rowMatch = rowPattern.exec(raw))) {
            var cells = [];
            var cellPattern = /<td[^>]*>([\s\S]*?)<\/td>/gi;
            var cellMatch;
            while ((cellMatch = cellPattern.exec(rowMatch[1]))) {
                cells.push(cellMatch[1]
                    .replace(/<[^>]+>/g, '')
                    .replace(/&nbsp;/gi, ' ')
                    .replace(/&#160;/gi, ' ')
                    .trim());
            }
            var time = String(cells[0] || '').trim();
            if (cells.length < 4 || !isKospiRegularSessionTime(time)) continue;
            var normalized = {
                date: date || null,
                time: time,
                personal: parseNumber(cells[1]),
                foreign: parseNumber(cells[2]),
                institution: parseNumber(cells[3]),
                unit: '억원'
            };
            if (![normalized.personal, normalized.foreign, normalized.institution].every(Number.isFinite)) continue;
            rowsByTime[time] = normalized;
        }
        return Object.keys(rowsByTime).sort().map(function (time) { return rowsByTime[time]; });
    }

    function extractKospiIntradayForeignFlowPageCount(payload) {
        var raw = String(payload || '').replace(/&amp;/gi, '&');
        var pageCount = 1;
        var pagePattern = /(?:[?&])page=(\d+)/gi;
        var match;
        while ((match = pagePattern.exec(raw))) {
            var page = Number(match[1]);
            if (Number.isFinite(page) && page > pageCount) pageCount = page;
        }
        return pageCount;
    }

    function mergeKospiIntradayForeignFlow(priceRows, flowRows) {
        var snapshotsByKey = {};
        (flowRows || []).forEach(function (row) {
            if (!row || !isKospiRegularSessionTime(String(row.time || '')) || !Number.isFinite(row.foreign)) return;
            var date = normalizeIsoDate(row.date);
            snapshotsByKey[(date || '') + '|' + row.time] = row;
        });
        var snapshots = Object.keys(snapshotsByKey).map(function (key) { return snapshotsByKey[key]; }).sort(function (left, right) {
            return String(left.date || '').localeCompare(String(right.date || '')) || left.time.localeCompare(right.time);
        });
        var flowIndex = 0;
        var latest = null;
        return (priceRows || []).map(function (row) {
            while (flowIndex < snapshots.length) {
                var candidate = snapshots[flowIndex];
                var candidateDate = normalizeIsoDate(candidate.date);
                if (candidateDate && candidateDate < row.date) {
                    flowIndex += 1;
                    continue;
                }
                if (candidateDate && candidateDate > row.date) break;
                if (candidate.time > row.time) break;
                latest = candidate;
                flowIndex += 1;
            }
            var merged = {};
            Object.keys(row).forEach(function (key) { merged[key] = row[key]; });
            var sameDate = latest && (!latest.date || normalizeIsoDate(latest.date) === row.date);
            merged.foreign = sameDate ? latest.foreign : null;
            merged.institution = sameDate ? latest.institution : null;
            merged.personal = sameDate ? latest.personal : null;
            merged.flowObservedAt = sameDate ? latest.time : null;
            merged.flowCarriedForward = Boolean(sameDate && latest.time !== row.time);
            merged.flowUnit = '억원';
            return merged;
        });
    }

    function exponentialMovingAverage(values, period) {
        var multiplier = 2 / (period + 1);
        var result = new Array(values.length).fill(null);
        var previous = null;
        values.forEach(function (value, index) {
            if (!Number.isFinite(value)) return;
            previous = previous === null ? value : value * multiplier + previous * (1 - multiplier);
            result[index] = previous;
        });
        return result;
    }

    function calculateMacd(values, fastPeriod, slowPeriod, signalPeriod) {
        var fast = exponentialMovingAverage(values, fastPeriod || 12);
        var slow = exponentialMovingAverage(values, slowPeriod || 26);
        var macd = values.map(function (_, index) {
            return Number.isFinite(fast[index]) && Number.isFinite(slow[index]) ? fast[index] - slow[index] : null;
        });
        var signal = exponentialMovingAverage(macd, signalPeriod || 9);
        var histogram = macd.map(function (value, index) {
            return Number.isFinite(value) && Number.isFinite(signal[index]) ? value - signal[index] : null;
        });
        return { macd: macd, signal: signal, histogram: histogram };
    }

    function normalizeTqqqPriceHistory(payload) {
        var raw = String(payload || '').trim();
        if (raw.charAt(0) === '{') {
            try {
                var chart = JSON.parse(raw).chart;
                var result = chart && chart.result && chart.result[0];
                var quote = result && result.indicators && result.indicators.quote && result.indicators.quote[0];
                var jsonRows = [];
                (result && result.timestamp || []).forEach(function (timestamp, index) {
                    var open = quote && Number(quote.open[index]);
                    var high = quote && Number(quote.high[index]);
                    var low = quote && Number(quote.low[index]);
                    var close = quote && Number(quote.close[index]);
                    var volume = quote && Number(quote.volume[index]);
                    if (![open, high, low, close, volume].every(Number.isFinite)) return;
                    jsonRows.push({
                        date: new Date(Number(timestamp) * 1000).toISOString().slice(0, 10),
                        open: open,
                        high: high,
                        low: low,
                        close: close,
                        volume: volume
                    });
                });
                return jsonRows;
            } catch (error) {
                return [];
            }
        }

        var rowsByDate = {};
        raw.split(/\r?\n/).slice(1).forEach(function (line) {
            var fields = line.split(',');
            var row = {
                date: String(fields[0] || ''),
                open: parseNumber(fields[1]),
                high: parseNumber(fields[2]),
                low: parseNumber(fields[3]),
                close: parseNumber(fields[4]),
                volume: parseNumber(fields[5])
            };
            if (!/^\d{4}-\d{2}-\d{2}$/.test(row.date)
                || ![row.open, row.high, row.low, row.close, row.volume].every(Number.isFinite)
                || row.volume <= 0
                || row.high < Math.max(row.open, row.close)
                || row.low > Math.min(row.open, row.close)) return;
            rowsByDate[row.date] = row;
        });
        return Object.keys(rowsByDate).sort().map(function (date) { return rowsByDate[date]; });
    }

    function normalizeTqqqIntradayHistory(payload, sourceInterval) {
        var raw = String(payload || '').trim();
        var decoded;
        try {
            decoded = JSON.parse(raw);
        } catch (error) {
            throw new Error('TQQQ 분봉 응답이 올바르지 않습니다.');
        }
        var result = decoded && decoded.chart && decoded.chart.result && decoded.chart.result[0];
        var quote = result && result.indicators && result.indicators.quote && result.indicators.quote[0];
        var timestamps = result && result.timestamp || [];
        if (!quote || !timestamps.length) throw new Error('TQQQ 분봉 이력이 비어 있습니다.');
        var dayRows = {};
        timestamps.forEach(function (timestamp, index) {
            var open = Number(quote.open[index]);
            var high = Number(quote.high[index]);
            var low = Number(quote.low[index]);
            var close = Number(quote.close[index]);
            var volume = Number(quote.volume[index]);
            if (![open, high, low, close, volume].every(Number.isFinite)
                || volume <= 0
                || high < Math.max(open, close)
                || low > Math.min(open, close)) return;
            var dateParts = new Intl.DateTimeFormat('en-CA', {
                timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit'
            }).formatToParts(new Date(Number(timestamp) * 1000));
            var timeParts = new Intl.DateTimeFormat('en-GB', {
                timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
            }).formatToParts(new Date(Number(timestamp) * 1000));
            var dateValues = {};
            var timeValues = {};
            dateParts.forEach(function (part) { dateValues[part.type] = part.value; });
            timeParts.forEach(function (part) { timeValues[part.type] = part.value; });
            var date = dateValues.year + '-' + dateValues.month + '-' + dateValues.day;
            var time = timeValues.hour + ':' + timeValues.minute;
            if (!dayRows[date]) dayRows[date] = [];
            dayRows[date].push({
                timestamp: Number(timestamp),
                time: time,
                open: open,
                high: high,
                low: low,
                close: close,
                volume: volume
            });
        });
        var allChanges = [];
        Object.keys(dayRows).forEach(function (date) {
            dayRows[date].sort(function (left, right) { return left.timestamp - right.timestamp; });
            dayRows[date].slice(1).forEach(function (row, index) {
                allChanges.push(row.close - dayRows[date][index].close);
            });
        });
        var sigma = sampleSigma(allChanges);
        if (!Number.isFinite(sigma) || sigma <= 0) throw new Error('TQQQ 분봉 변동성을 계산할 수 없습니다.');
        return Object.keys(dayRows).sort().map(function (date) {
            var cumulativeDelta = 0;
            var bars = dayRows[date].map(function (row, index) {
                var neutral = index === 0;
                var buyShare = neutral ? 0.5 : normalCdf((row.close - dayRows[date][index - 1].close) / sigma);
                var estimatedBuyVolume = Math.max(0, Math.min(row.volume, Math.round(row.volume * buyShare)));
                var estimatedSellVolume = row.volume - estimatedBuyVolume;
                var delta = estimatedBuyVolume - estimatedSellVolume;
                cumulativeDelta += delta;
                return {
                    time: row.time,
                    open: row.open,
                    high: row.high,
                    low: row.low,
                    close: row.close,
                    volume: row.volume,
                    estimatedBuyVolume: estimatedBuyVolume,
                    estimatedSellVolume: estimatedSellVolume,
                    delta: delta,
                    cumulativeDelta: cumulativeDelta,
                    neutral: neutral
                };
            });
            var minuteVolume = bars.reduce(function (total, row) { return total + row.volume; }, 0);
            return {
                date: date,
                interval: sourceInterval,
                minuteVolume: minuteVolume,
                sourceLastAt: new Date(dayRows[date][dayRows[date].length - 1].timestamp * 1000).toISOString(),
                sigma: sigma,
                sigmaSampleSize: allChanges.length,
                bars: bars
            };
        });
    }

    function calculateCompositeDailyVolumeMomentum(kospiRows, kodexRows, options) {
        var settings = options || {};
        var varianceAlpha = Number.isFinite(settings.varianceAlpha) ? settings.varianceAlpha : 2 / 61;
        var fastPeriod = Number.isFinite(settings.fastPeriod) ? settings.fastPeriod : 5;
        var slowPeriod = Number.isFinite(settings.slowPeriod) ? settings.slowPeriod : 20;
        var signalPeriod = Number.isFinite(settings.signalPeriod) ? settings.signalPeriod : 5;
        var kospiByDate = {};
        var kodexByDate = {};

        function normalizeDailyRows(rows, target) {
            (rows || []).forEach(function (row) {
                var date = normalizeIsoDate(row && row.date);
                if (!date
                    || ![row.open, row.high, row.low, row.close, row.volume].every(Number.isFinite)
                    || row.volume <= 0
                    || row.high < Math.max(row.open, row.close)
                    || row.low > Math.min(row.open, row.close)) return;
                var range = row.high - row.low;
                var pressure = range > 0
                    ? ((row.close - row.low) - (row.high - row.close)) / range
                    : row.close > row.open ? 1 : row.close < row.open ? -1 : 0;
                target[date] = {
                    pressure: Math.max(-1, Math.min(1, pressure)),
                    sourceLastAt: row.sourceLastAt || null
                };
            });
        }
        function normalizePressure(value, variance) {
            var floor = 0.02;
            var scale = Math.sqrt(Math.max(Number.isFinite(variance) ? variance : value * value, floor * floor));
            return Math.tanh(Math.max(-3, Math.min(3, value / scale)) / 2);
        }
        function nextVariance(previous, value) {
            return Number.isFinite(previous)
                ? varianceAlpha * value * value + (1 - varianceAlpha) * previous
                : Math.max(value * value, 0.02 * 0.02);
        }
        function nextEma(previous, value, period) {
            var alpha = 2 / (period + 1);
            return previous === null ? value : value * alpha + previous * (1 - alpha);
        }

        normalizeDailyRows(kospiRows, kospiByDate);
        normalizeDailyRows(kodexRows, kodexByDate);
        var commonDates = Object.keys(kospiByDate).filter(function (date) { return Boolean(kodexByDate[date]); }).sort();
        var kospiVariance = null;
        var kodexVariance = null;
        var fast = null;
        var slow = null;
        var signal = null;

        return commonDates.map(function (date) {
            var kospiPressure = kospiByDate[date].pressure;
            var kodexPressure = kodexByDate[date].pressure;
            var kospiScore = normalizePressure(kospiPressure, kospiVariance);
            var kodexScore = normalizePressure(kodexPressure, kodexVariance);
            kospiVariance = nextVariance(kospiVariance, kospiPressure);
            kodexVariance = nextVariance(kodexVariance, kodexPressure);
            var direction = 50 * (kospiScore + kodexScore);
            var divergence = 50 * (kodexScore - kospiScore);
            fast = nextEma(fast, direction, fastPeriod);
            slow = nextEma(slow, direction, slowPeriod);
            var momentum = fast - slow;
            signal = nextEma(signal, momentum, signalPeriod);
            var point = {
                time: '15:30',
                kospiPressure: kospiPressure,
                kodexPressure: kodexPressure,
                kospiScore: kospiScore * 100,
                kodexScore: kodexScore * 100,
                direction: direction,
                divergence: divergence,
                momentum: momentum,
                signal: signal
            };
            return {
                date: date,
                sourceLastAt: [kospiByDate[date].sourceLastAt, kodexByDate[date].sourceLastAt].filter(Boolean).sort().pop() || date + 'T15:30:00+09:00',
                bars: [point],
                summary: point
            };
        });
    }

    function normalizeKodexVolumePressure(payload) {
        if (!payload || payload.schemaVersion !== 1 || String(payload.symbol) !== '122630' || !Array.isArray(payload.days)) {
            throw new Error('KODEX 거래 압력 데이터가 올바르지 않습니다.');
        }
        var rowsByDate = {};
        var invalidRows = false;
        payload.days.forEach(function (row) {
            var date = row && String(row.date || '');
            var normalized = {
                date: date,
                dailyVolume: parseNumber(row && row.dailyVolume),
                minuteVolume: parseNumber(row && row.minuteVolume),
                estimatedBuyVolume: parseNumber(row && row.estimatedBuyVolume),
                estimatedSellVolume: parseNumber(row && row.estimatedSellVolume),
                buyShare: parseNumber(row && row.buyShare),
                sellShare: parseNumber(row && row.sellShare),
                coverageRatio: parseNumber(row && row.coverageRatio),
                minuteBars: parseNumber(row && row.minuteBars),
                sigma: parseNumber(row && row.sigma),
                sigmaSampleSize: parseNumber(row && row.sigmaSampleSize),
                method: row && String(row.method || '')
            };
            var estimatedTotal = normalized.estimatedBuyVolume + normalized.estimatedSellVolume;
            if (!/^\d{4}-\d{2}-\d{2}$/.test(date)
                || !Object.keys(normalized).filter(function (key) { return key !== 'date' && key !== 'method'; }).every(function (key) {
                    return Number.isFinite(normalized[key]);
                })
                || normalized.dailyVolume <= 0
                || normalized.minuteVolume <= 0
                || normalized.estimatedBuyVolume < 0
                || normalized.estimatedSellVolume < 0
                || Math.abs(estimatedTotal - normalized.dailyVolume) > 1
                || Math.abs(normalized.buyShare + normalized.sellShare - 1) > 0.00001
                || Math.abs(normalized.buyShare - normalized.estimatedBuyVolume / normalized.dailyVolume) > 0.000002
                || Math.abs(normalized.sellShare - normalized.estimatedSellVolume / normalized.dailyVolume) > 0.000002
                || Math.abs(normalized.coverageRatio - normalized.minuteVolume / normalized.dailyVolume) > 0.000002
                || normalized.coverageRatio < 0.95
                || normalized.coverageRatio > 1.005
                || normalized.minuteBars < 300
                || normalized.sigma <= 0
                || normalized.sigmaSampleSize < 2
                || normalized.method !== 'bvc-normal-1m-v1'
                || rowsByDate[date]) {
                invalidRows = true;
                return;
            }
            rowsByDate[date] = normalized;
        });
        if (invalidRows) throw new Error('KODEX 거래 압력 이력에 유효하지 않거나 중복된 행이 있습니다.');
        return Object.keys(rowsByDate).sort().map(function (date) { return rowsByDate[date]; });
    }

    function mergeKodexVolumePressure(history, pressureRows) {
        var pressureByDate = {};
        (pressureRows || []).forEach(function (row) { pressureByDate[row.date] = row; });
        return (history || []).map(function (row) {
            var pressure = pressureByDate[row.date];
            if (!pressure || Math.abs(pressure.dailyVolume - row.volume) / Math.max(row.volume, 1) > 0.005) return row;
            var enriched = {};
            Object.keys(row).forEach(function (key) { enriched[key] = row[key]; });
            enriched.volumePressure = pressure;
            return enriched;
        });
    }

    function normalizeKodexIntradayIndex(payload) {
        if (!payload || payload.schemaVersion !== 1 || String(payload.symbol) !== '122630' || !Array.isArray(payload.days)) {
            throw new Error('KODEX 분봉 색인이 올바르지 않습니다.');
        }
        var rowsByDate = {};
        payload.days.forEach(function (row) {
            var date = row && String(row.date || '');
            var path = row && String(row.path || '');
            var normalized = {
                date: date,
                path: path,
                minuteBars: parseNumber(row && row.minuteBars),
                coverageRatio: parseNumber(row && row.coverageRatio),
                sourceLastAt: row && String(row.sourceLastAt || ''),
                collectedAt: row && String(row.collectedAt || '')
            };
            if (!/^\d{4}-\d{2}-\d{2}$/.test(date)
                || !/^kodex-intraday\/\d{4}-\d{2}-\d{2}\.json$/.test(path)
                || !Number.isFinite(normalized.minuteBars)
                || normalized.minuteBars < 300
                || !Number.isFinite(normalized.coverageRatio)
                || normalized.coverageRatio < 0.95
                || normalized.coverageRatio > 1.005
                || !Number.isFinite(Date.parse(normalized.sourceLastAt))
                || rowsByDate[date]) {
                throw new Error('KODEX 분봉 색인에 유효하지 않은 행이 있습니다.');
            }
            rowsByDate[date] = normalized;
        });
        return Object.keys(rowsByDate).sort().map(function (date) { return rowsByDate[date]; });
    }

    function normalizeKodexIntradayDay(payload) {
        if (!payload || payload.schemaVersion !== 1 || String(payload.symbol) !== '122630'
            || !/^\d{4}-\d{2}-\d{2}$/.test(String(payload.date || ''))
            || payload.interval !== '1m' || payload.method !== 'bvc-normal-1m-v1'
            || !Array.isArray(payload.bars) || payload.bars.length < 300) {
            throw new Error('KODEX 분봉 데이터가 올바르지 않습니다.');
        }
        var cumulativeDelta = 0;
        var rows = payload.bars.map(function (row) {
            var normalized = {
                time: row && String(row.time || ''),
                open: parseNumber(row && row.open),
                high: parseNumber(row && row.high),
                low: parseNumber(row && row.low),
                close: parseNumber(row && row.close),
                volume: parseNumber(row && row.volume),
                estimatedBuyVolume: parseNumber(row && row.estimatedBuyVolume),
                estimatedSellVolume: parseNumber(row && row.estimatedSellVolume),
                delta: parseNumber(row && row.delta),
                cumulativeDelta: parseNumber(row && row.cumulativeDelta),
                neutral: Boolean(row && row.neutral)
            };
            cumulativeDelta += normalized.delta;
            if (!/^\d{2}:\d{2}$/.test(normalized.time)
                || ![normalized.open, normalized.high, normalized.low, normalized.close, normalized.volume,
                    normalized.estimatedBuyVolume, normalized.estimatedSellVolume, normalized.delta,
                    normalized.cumulativeDelta].every(Number.isFinite)
                || normalized.volume < 0
                || normalized.high < Math.max(normalized.open, normalized.close)
                || normalized.low > Math.min(normalized.open, normalized.close)
                || Math.abs(normalized.estimatedBuyVolume + normalized.estimatedSellVolume - normalized.volume) > 1
                || Math.abs(normalized.estimatedBuyVolume - normalized.estimatedSellVolume - normalized.delta) > 1
                || Math.abs(normalized.cumulativeDelta - cumulativeDelta) > 1) {
                throw new Error('KODEX 분봉에 유효하지 않은 값이 있습니다.');
            }
            return normalized;
        });
        return {
            date: String(payload.date),
            dailyVolume: parseNumber(payload.dailyVolume),
            minuteVolume: parseNumber(payload.minuteVolume),
            coverageRatio: parseNumber(payload.coverageRatio),
            sourceLastAt: String(payload.sourceLastAt || ''),
            sigma: parseNumber(payload.sigma),
            sigmaSampleSize: parseNumber(payload.sigmaSampleSize),
            bars: rows
        };
    }

    function normalizeKodexLiveIntradayDay(payload, expectedDate, referenceSigma, referenceSampleSize) {
        if (!Array.isArray(payload) || payload.length < 1 || !/^\d{4}-\d{2}-\d{2}$/.test(expectedDate)) {
            throw new Error('오늘 KODEX 분봉 데이터가 올바르지 않습니다.');
        }
        var compactDate = expectedDate.replace(/-/g, '');
        var rowsByTimestamp = {};
        payload.forEach(function (row) {
            var timestamp = row && String(row.localDateTime || '');
            var normalized = {
                timestamp: timestamp,
                time: timestamp.length === 14 ? timestamp.slice(8, 10) + ':' + timestamp.slice(10, 12) : '',
                open: parseNumber(row && row.openPrice),
                high: parseNumber(row && row.highPrice),
                low: parseNumber(row && row.lowPrice),
                close: parseNumber(row && row.currentPrice),
                volume: parseNumber(row && row.accumulatedTradingVolume)
            };
            if (!/^\d{14}$/.test(timestamp)
                || timestamp.slice(0, 8) !== compactDate
                || !/^\d{2}:\d{2}$/.test(normalized.time)
                || ![normalized.open, normalized.high, normalized.low, normalized.close, normalized.volume].every(Number.isFinite)
                || normalized.volume < 0
                || normalized.high < Math.max(normalized.open, normalized.close)
                || normalized.low > Math.min(normalized.open, normalized.close)
                || rowsByTimestamp[timestamp]) {
                throw new Error('오늘 KODEX 분봉에 유효하지 않은 값이 있습니다.');
            }
            rowsByTimestamp[timestamp] = normalized;
        });
        var rawRows = Object.keys(rowsByTimestamp).sort().map(function (timestamp) { return rowsByTimestamp[timestamp]; });
        var changes = rawRows.slice(1).map(function (row, index) { return row.close - rawRows[index].close; });
        var sigma = Number.isFinite(referenceSigma) && referenceSigma > 0 ? referenceSigma : sampleSigma(changes);
        if (!Number.isFinite(sigma) || sigma <= 0) throw new Error('오늘 KODEX 분봉 변동성을 계산할 수 없습니다.');
        var cumulativeDelta = 0;
        var bars = rawRows.map(function (row, index) {
            var neutral = index === 0 || row.time >= '15:20';
            var buyShare = neutral ? 0.5 : normalCdf((row.close - rawRows[index - 1].close) / sigma);
            var estimatedBuyVolume = Math.max(0, Math.min(row.volume, Math.round(row.volume * buyShare)));
            var estimatedSellVolume = row.volume - estimatedBuyVolume;
            var delta = estimatedBuyVolume - estimatedSellVolume;
            cumulativeDelta += delta;
            return {
                time: row.time,
                open: row.open,
                high: row.high,
                low: row.low,
                close: row.close,
                volume: row.volume,
                estimatedBuyVolume: estimatedBuyVolume,
                estimatedSellVolume: estimatedSellVolume,
                delta: delta,
                cumulativeDelta: cumulativeDelta,
                neutral: neutral
            };
        });
        var minuteVolume = bars.reduce(function (total, row) { return total + row.volume; }, 0);
        var latestTimestamp = rawRows[rawRows.length - 1].timestamp;
        return {
            date: expectedDate,
            dailyVolume: minuteVolume,
            minuteVolume: minuteVolume,
            coverageRatio: 1,
            sourceLastAt: expectedDate + 'T' + latestTimestamp.slice(8, 10) + ':' + latestTimestamp.slice(10, 12) + ':00+09:00',
            sigma: sigma,
            sigmaSampleSize: Number.isFinite(referenceSampleSize) ? referenceSampleSize : changes.length,
            live: true,
            bars: bars
        };
    }

    function ensureCurrentIntradayIndex(indexRows, currentDate, marketStatus, liveDay, now) {
        var rows = (indexRows || []).map(function (row) { return Object.assign({}, row); });
        var date = normalizeIsoDate(currentDate);
        var status = String(marketStatus || '').toUpperCase();
        var latestArchivedDate = rows.filter(function (row) {
            return row && row.path && normalizeIsoDate(row.date);
        }).map(function (row) {
            return row.date;
        }).sort().slice(-1)[0] || '';
        var keepClosingSession = status === 'CLOSE'
            && (Boolean(liveDay) || !latestArchivedDate || date > latestArchivedDate);
        if (!date || (status !== 'PREOPEN' && status !== 'OPEN' && !keepClosingSession)) return rows;
        var current = rows.filter(function (row) { return row.date === date; })[0];
        var values = {
            date: date,
            path: current && current.path || '',
            minuteBars: liveDay && Array.isArray(liveDay.bars) ? liveDay.bars.length : 0,
            coverageRatio: liveDay ? 1 : 0,
            sourceLastAt: liveDay && liveDay.sourceLastAt || '',
            collectedAt: new Date(Number.isFinite(now) ? now : Date.now()).toISOString(),
            live: true,
            closed: status === 'CLOSE',
            pending: !liveDay
        };
        if (current) Object.assign(current, values);
        else rows.push(values);
        return rows.sort(function (left, right) { return left.date.localeCompare(right.date); });
    }

    function preferredIntradayDate(indexRows, currentDate, explicitSelection) {
        var rows = (indexRows || []).filter(function (row) {
            return row && normalizeIsoDate(row.date);
        }).slice().sort(function (left, right) { return left.date.localeCompare(right.date); });
        var dates = rows.map(function (row) { return row.date; });
        var current = normalizeIsoDate(currentDate);
        var liveDate = rows.filter(function (row) { return row.live; }).map(function (row) {
            return row.date;
        }).slice(-1)[0] || '';
        if (!explicitSelection) return liveDate || dates[dates.length - 1] || '';
        if (current && dates.indexOf(current) !== -1) return current;
        return dates[dates.length - 1] || '';
    }

    function buildRollingIntradayDays(days, targetDate) {
        var target = normalizeIsoDate(targetDate);
        var sourceDays = (days || []).filter(function (day) {
            return day && normalizeIsoDate(day.date) && Array.isArray(day.bars);
        }).slice().sort(function (left, right) { return left.date.localeCompare(right.date); });
        if (!target || !sourceDays.length) {
            throw new Error('연속 분봉을 만들 거래일 데이터가 올바르지 않습니다.');
        }
        var bars = [];
        sourceDays.forEach(function (day) {
            var sessionDate = normalizeIsoDate(day.date);
            day.bars.forEach(function (bar) {
                bars.push(Object.assign({}, bar, { date: sessionDate, sessionDate: sessionDate }));
            });
        });
        var currentDay = sourceDays.filter(function (day) { return day.date === target; }).slice(-1)[0] || null;
        var currentBarCount = currentDay ? currentDay.bars.length : 0;
        var previousDays = sourceDays.filter(function (day) { return day.date < target; });
        var previousBarCount = previousDays.reduce(function (total, day) { return total + day.bars.length; }, 0);
        var sourceLastAt = sourceDays.map(function (day) { return day.sourceLastAt; }).filter(Boolean).sort().slice(-1)[0] || '';
        var flowSourceLastAt = sourceDays.map(function (day) { return day.flowSourceLastAt; }).filter(Boolean).sort().slice(-1)[0] || '';
        return {
            date: target,
            previousDate: previousDays.length ? previousDays[previousDays.length - 1].date : '',
            sessionDates: sourceDays.map(function (day) { return day.date; }),
            rolling: sourceDays.length > 1,
            live: Boolean(currentDay && currentDay.live),
            pending: !currentBarCount,
            previousBarCount: previousBarCount,
            currentBarCount: currentBarCount,
            sourceLastAt: sourceLastAt,
            flowSourceLastAt: flowSourceLastAt,
            bars: bars
        };
    }

    function buildRollingIntradayDay(previousDay, currentDay, targetDate) {
        return buildRollingIntradayDays([previousDay, currentDay].filter(Boolean), targetDate);
    }

    function mergeRuntimeIntradayIndex(previousRows, incomingRows) {
        var incoming = Array.isArray(incomingRows) ? incomingRows : [];
        var incomingLiveEntry = incoming.filter(function (row) {
            return row && row.live && !row.path;
        }).slice(-1)[0] || null;
        var byDate = {};
        (Array.isArray(previousRows) ? previousRows : []).concat(incoming).forEach(function (row) {
            if (row && normalizeIsoDate(row.date)) byDate[row.date] = row;
        });
        return Object.keys(byDate).sort().map(function (date) {
            return byDate[date];
        }).filter(function (row) {
            return !row.live || Boolean(row.path)
                || Boolean(incomingLiveEntry && row.date === incomingLiveEntry.date);
        });
    }

    function intradaySourceDate(sourceLastAt, fallbackDate) {
        return normalizeIsoDate(String(sourceLastAt || '').slice(0, 10))
            || normalizeIsoDate(fallbackDate)
            || '';
    }

    function cleanDisplayText(value) {
        var text = value == null ? '' : String(value).trim();
        return !text || /^[-—]+$/.test(text) ? '' : text;
    }

    function validatedPrices(basic, integration, allowMissingSessionPrices) {
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

        if (![value, previousClose].every(Number.isFinite)) {
            throw new Error('가격 데이터가 부족합니다.');
        }
        var sessionPricesComplete = [open, high, low].every(Number.isFinite);
        if (!sessionPricesComplete && !allowMissingSessionPrices) {
            throw new Error('가격 데이터가 부족합니다.');
        }
        if (sessionPricesComplete && (high < low || value < low || value > high || open < low || open > high)) {
            throw new Error('가격 범위가 올바르지 않습니다.');
        }

        return {
            value: value,
            previousClose: previousClose,
            open: open,
            high: high,
            low: low,
            sessionPricesComplete: sessionPricesComplete
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
        var timestamp = parseSourceTimestamp(basic.localTradedAt);
        if (!Number.isFinite(timestamp) || timestamp > now + 10 * 60 * 1000) throw new Error(code + ' 시각이 올바르지 않습니다.');
        var bizdate = integration.dealTrendInfo && String(integration.dealTrendInfo.bizdate || '');
        if (bizdate && bizdate !== marketDateKey(timestamp)) throw new Error(code + ' 수급 거래일이 일치하지 않습니다.');

        var prices = validatedPrices(basic, integration, true);
        var ratio = signedValue(basic.fluctuationsRatio, basic.compareToPreviousPrice);
        var totals = totalInfoMap(integration);
        var trend = integration.dealTrendInfo || {};
        var breadth = integration.upDownStockInfo || {};
        var program = integration.programTrendInfo || {};
        var normalizedFlows = [
            { label: '외국인', value: parseNumber(trend.foreignValue), unit: '억원' },
            { label: '기관', value: parseNumber(trend.institutionalValue), unit: '억원' },
            { label: '개인', value: parseNumber(trend.personalValue), unit: '억원' }
        ];
        var normalizedBreadth = {
            advance: parseNumber(breadth.upperCount) + parseNumber(breadth.riseCount),
            flat: parseNumber(breadth.steadyCount),
            decline: parseNumber(breadth.lowerCount) + parseNumber(breadth.fallCount)
        };
        var normalizedProgram = {
            arbitrage: parseNumber(program.indexDifferenceReal),
            nonArbitrage: parseNumber(program.indexBiDifferenceReal),
            total: parseNumber(program.indexTotalReal),
            unit: '억원'
        };
        var requiredValues = [
            ratio,
            normalizedBreadth.advance,
            normalizedBreadth.flat,
            normalizedBreadth.decline
        ];
        if (code === 'KOSPI') {
            requiredValues = requiredValues.concat(
                normalizedFlows.map(function (flow) { return flow.value; }),
                [normalizedProgram.arbitrage, normalizedProgram.nonArbitrage, normalizedProgram.total]
            );
        }
        if (!requiredValues.every(Number.isFinite)) throw new Error(code + ' 핵심 수치가 부족합니다.');

        return {
            id: code,
            label: code,
            symbol: code === 'KOSPI' ? 'K' : 'Q',
            value: prices.value,
            previousClose: prices.previousClose,
            open: prices.open,
            high: prices.high,
            low: prices.low,
            sessionPricesComplete: prices.sessionPricesComplete,
            changePercent: ratio,
            asOf: new Date(timestamp).toISOString(),
            asOfLabel: formatAsOfLabel(timestamp),
            shortTimeLabel: formatShortTime(timestamp),
            sessionDate: normalizeIsoDate(bizdate) || normalizeIsoDate(marketDateKey(timestamp)),
            stateLabel: stateLabel(basic.marketStatus),
            marketStatus: basic.marketStatus,
            delayed: basic.marketStatus === 'OPEN' && now - timestamp > 10 * 60 * 1000,
            volume: totals.accumulatedTradingVolume,
            tradingValue: totals.accumulatedTradingValue,
            flows: normalizedFlows,
            breadth: normalizedBreadth,
            program: normalizedProgram
        };
    }

    function normalizeStock(definition, basic, integration, now) {
        if (!basic || String(basic.itemCode) !== definition.code || !integration) {
            throw new Error(definition.label + ' 응답이 올바르지 않습니다.');
        }
        var timestamp = parseSourceTimestamp(basic.localTradedAt);
        if (!Number.isFinite(timestamp) || timestamp > now + 10 * 60 * 1000) {
            throw new Error(definition.label + ' 시각이 올바르지 않습니다.');
        }
        var prices = validatedPrices(basic, integration, true);
        var ratio = signedValue(basic.fluctuationsRatio, basic.compareToPreviousPrice);
        if (!Number.isFinite(ratio)) throw new Error(definition.label + ' 등락률이 올바르지 않습니다.');
        var normalized = {
            id: definition.id,
            label: definition.label,
            unit: definition.unit,
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
            sessionPricesComplete: prices.sessionPricesComplete,
            delayed: basic.marketStatus === 'OPEN' && now - timestamp > 10 * 60 * 1000
        };
        if (definition.id === 'KODEX') {
            var totals = totalInfoMap(integration);
            var rawTotals = totalInfoTextMap(integration);
            var investorTrends = normalizeInvestorTrends(integration);
            normalized.volume = Number.isFinite(totals.accumulatedTradingVolume)
                ? totals.accumulatedTradingVolume
                : investorTrends.length ? investorTrends[0].volume : NaN;
            normalized.tradingValueLabel = cleanDisplayText(rawTotals.accumulatedTradingValue);
            normalized.periodReturns = {
                oneMonth: totals.oneMonthEarnRate,
                threeMonth: totals.threeMonthEarnRate,
                sixMonth: totals.sixMonthEarnRate,
                oneYear: totals.oneYearEarnRate
            };
            normalized.etf = {
                baseIndex: cleanDisplayText(rawTotals.etfBaseIdx),
                issuer: cleanDisplayText(rawTotals.issueName),
                fee: cleanDisplayText(rawTotals.fundPay)
            };
            normalized.investorTrends = investorTrends;
        }
        return normalized;
    }

    function normalizeExchange(payload, now) {
        var result = payload && payload.isSuccess && payload.result;
        if (!result || result.reutersCode !== 'FX_USDKRW') throw new Error('달러/원 응답이 올바르지 않습니다.');
        var timestamp = parseSourceTimestamp(result.localTradedAt);
        var value = parseNumber(result.closePrice);
        var ratio = signedValue(result.fluctuationsRatio, result.fluctuationsType);
        if (!Number.isFinite(timestamp) || timestamp > now + 10 * 60 * 1000 || !Number.isFinite(value) || !Number.isFinite(ratio)) {
            throw new Error('달러/원 시세가 올바르지 않습니다.');
        }
        return {
            id: 'USDKRW',
            label: '달러/원',
            value: value,
            changePercent: ratio,
            asOf: new Date(timestamp).toISOString(),
            asOfLabel: formatAsOfLabel(timestamp),
            shortTimeLabel: formatShortTime(timestamp),
            stateLabel: '하나은행 고시',
            marketStatus: result.marketStatus,
            delayed: result.marketStatus === 'OPEN' && now - timestamp > 30 * 60 * 1000
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

    function fetchText(fetchImpl, url, signal, nonce) {
        return fetchImpl(withCacheBust(url, nonce), {
            cache: 'no-store',
            credentials: 'same-origin',
            signal: signal
        }).then(function (response) {
            if (!response.ok) throw new Error('최신 가격 이력을 불러오지 못했습니다.');
            return response.text();
        });
    }

    function fetchTextWithConcurrency(fetchImpl, urls, signal, nonce, limit) {
        var targets = urls || [];
        if (!targets.length) return Promise.resolve([]);
        var results = new Array(targets.length);
        var nextIndex = 0;
        var workerCount = Math.max(1, Math.min(targets.length, Number(limit) || 6));
        function runWorker() {
            var index = nextIndex;
            nextIndex += 1;
            if (index >= targets.length) return Promise.resolve();
            return fetchText(fetchImpl, targets[index], signal, nonce).then(function (payload) {
                results[index] = payload;
                return runWorker();
            });
        }
        var workers = [];
        for (var index = 0; index < workerCount; index += 1) workers.push(runWorker());
        return Promise.all(workers).then(function () { return results; });
    }

    function fetchPair(fetchImpl, baseUrl, category, code, signal, nonce) {
        var prefix = new URL(category + '/' + code + '/', baseUrl).href;
        return Promise.all([
            fetchJson(fetchImpl, prefix + 'basic', signal, nonce),
            fetchJson(fetchImpl, prefix + 'integration', signal, nonce)
        ]);
    }

    function fetchKospiPriceHistory(fetchImpl, baseUrl, signal, nonce, now, ttlMs) {
        if (kospiPriceHistoryCache.value && kospiPriceHistoryCache.expiresAt > now) {
            return Promise.resolve(kospiPriceHistoryCache.value);
        }
        if (kospiPriceHistoryCache.pending) return kospiPriceHistoryCache.pending;
        var historyUrl = new URL('index/KOSPI/history', baseUrl).href;
        kospiPriceHistoryCache.pending = fetchText(fetchImpl, historyUrl, signal, nonce).then(function (payload) {
            var rows = normalizeKospiPriceHistory(payload);
            if (rows.length < 240) throw new Error('KOSPI 1년 가격 이력이 부족합니다.');
            kospiPriceHistoryCache.value = rows;
            kospiPriceHistoryCache.expiresAt = now + ttlMs;
            return rows;
        }).finally(function () {
            kospiPriceHistoryCache.pending = null;
        });
        return kospiPriceHistoryCache.pending;
    }

    function fetchKospiForeignFlowPage(fetchImpl, baseUrl, page, signal, nonce, now, ttlMs) {
        var cache = kospiForeignFlowPageCache[page] || { value: null, expiresAt: 0, pending: null };
        kospiForeignFlowPageCache[page] = cache;
        if (cache.value && cache.expiresAt > now) return Promise.resolve(cache.value);
        if (cache.pending) return cache.pending;
        var pageUrl = new URL('index/KOSPI/foreign-flow/page-' + page, baseUrl).href;
        cache.pending = fetchText(fetchImpl, pageUrl, signal, nonce).then(function (payload) {
            var rows = normalizeKospiForeignFlowHtml(payload);
            if (!rows.length) throw new Error('KOSPI 외국인 수급 ' + page + '페이지가 비어 있습니다.');
            cache.value = rows;
            cache.expiresAt = now + ttlMs;
            return rows;
        }).finally(function () {
            cache.pending = null;
        });
        return cache.pending;
    }

    function fetchKospiTechnicalHistory(fetchImpl, baseUrl, options) {
        var settings = options || {};
        var now = Number.isFinite(settings.now) ? settings.now : Date.now();
        var nonce = settings.nonce || String(now);
        var signal = settings.signal;
        var ttlMs = Number.isFinite(settings.ttlMs) ? settings.ttlMs : 30 * 60 * 1000;
        var pageCount = Math.max(3, Math.min(28, Number(settings.pageCount) || 8));
        if (settings.forceRefresh) {
            kospiPriceHistoryCache.expiresAt = 0;
            for (var refreshPage = 1; refreshPage <= pageCount; refreshPage += 1) {
                if (kospiForeignFlowPageCache[refreshPage]) kospiForeignFlowPageCache[refreshPage].expiresAt = 0;
            }
        }
        var pageRequests = [];
        for (var page = 1; page <= pageCount; page += 1) {
            pageRequests.push(fetchKospiForeignFlowPage(fetchImpl, baseUrl, page, signal, nonce, now, ttlMs));
        }
        return Promise.all([
            fetchKospiPriceHistory(fetchImpl, baseUrl, signal, nonce, now, ttlMs),
            Promise.all(pageRequests)
        ]).then(function (parts) {
            var flowRows = [];
            parts[1].forEach(function (rows) { flowRows = flowRows.concat(rows); });
            return mergeKospiTechnicalHistory(parts[0], flowRows);
        });
    }

    function fetchKospiIntradayDay(fetchImpl, baseUrl, date, options) {
        var settings = options || {};
        var day = normalizeIsoDate(date);
        if (!day) return Promise.reject(new Error('KOSPI 분봉 날짜가 올바르지 않습니다.'));
        if (typeof fetchImpl !== 'function') return Promise.reject(new Error('KOSPI 분봉 요청 함수가 없습니다.'));
        var now = Number.isFinite(settings.now) ? settings.now : Date.now();
        var ttlMs = Number.isFinite(settings.ttlMs) ? settings.ttlMs : 60 * 1000;
        var nonce = settings.nonce || String(now);
        var signal = settings.signal;
        var cacheKey = String(baseUrl || '') + '|' + day;
        var state = kospiIntradayDayCache[cacheKey] || { value: null, expiresAt: 0, pending: null, pendingSignal: null };
        kospiIntradayDayCache[cacheKey] = state;
        if (settings.forceRefresh) state.expiresAt = 0;
        if (state.value && state.expiresAt > now) return Promise.resolve(state.value);
        if (state.pending) {
            var shouldRestart = Boolean(settings.forceRefresh)
                || Boolean(signal && state.pendingSignal && signal !== state.pendingSignal);
            if (!shouldRestart) return state.pending;
            return state.pending.catch(function () { return null; }).then(function () {
                return fetchKospiIntradayDay(fetchImpl, baseUrl, day, Object.assign({}, settings, {
                    forceRefresh: true,
                    nonce: String(Date.now())
                }));
            });
        }

        var compactDate = day.replace(/-/g, '');
        var minuteUrl = new URL('index/KOSPI/minute', baseUrl);
        minuteUrl.searchParams.set('startDateTime', compactDate + '0900');
        minuteUrl.searchParams.set('endDateTime', compactDate + '1530');
        var firstFlowUrl = new URL('index/KOSPI/foreign-flow-time', baseUrl);
        firstFlowUrl.searchParams.set('bizdate', compactDate);
        firstFlowUrl.searchParams.set('sosok', '01');
        firstFlowUrl.searchParams.set('page', '1');

        state.pendingSignal = signal || null;
        state.pending = Promise.all([
            fetchJson(fetchImpl, minuteUrl.href, signal, nonce),
            fetchText(fetchImpl, firstFlowUrl.href, signal, nonce)
        ]).then(function (initialParts) {
            var priceRows = normalizeKospiIntradayMinute(initialParts[0], day);
            if (!priceRows.length) throw new Error('선택한 거래일의 KOSPI 분봉이 없습니다.');
            var pageCount = extractKospiIntradayForeignFlowPageCount(initialParts[1]);
            var maxPages = Number.isFinite(settings.maxPages) ? Math.max(1, Math.floor(settings.maxPages)) : 100;
            if (pageCount > maxPages) throw new Error('KOSPI 장중 수급 페이지 수가 허용 범위를 넘었습니다.');
            var remainingUrls = [];
            for (var page = 2; page <= pageCount; page += 1) {
                var pageUrl = new URL('index/KOSPI/foreign-flow-time', baseUrl);
                pageUrl.searchParams.set('bizdate', compactDate);
                pageUrl.searchParams.set('sosok', '01');
                pageUrl.searchParams.set('page', String(page));
                remainingUrls.push(pageUrl.href);
            }
            return fetchTextWithConcurrency(
                fetchImpl,
                remainingUrls,
                signal,
                nonce,
                settings.concurrencyLimit
            ).then(function (remainingPayloads) {
                var flowRows = [];
                [initialParts[1]].concat(remainingPayloads).forEach(function (payload) {
                    flowRows = flowRows.concat(normalizeKospiIntradayForeignFlowHtml(payload, day));
                });
                var uniqueFlows = {};
                flowRows.forEach(function (row) { uniqueFlows[row.time] = row; });
                flowRows = Object.keys(uniqueFlows).sort().map(function (time) { return uniqueFlows[time]; });
                var bars = mergeKospiIntradayForeignFlow(priceRows, flowRows);
                var latestPrice = priceRows[priceRows.length - 1];
                var latestFlow = flowRows.length ? flowRows[flowRows.length - 1] : null;
                return {
                    date: day,
                    interval: '1m',
                    sourceLastAt: day + 'T' + latestPrice.time + ':00+09:00',
                    flowSourceLastAt: latestFlow ? day + 'T' + latestFlow.time + ':00+09:00' : null,
                    flowPageCount: pageCount,
                    flowSnapshotCount: flowRows.length,
                    minuteVolume: priceRows.reduce(function (total, row) { return total + row.volume; }, 0),
                    bars: bars
                };
            });
        }).then(function (value) {
            state.value = value;
            state.expiresAt = now + ttlMs;
            return value;
        }).finally(function () {
            state.pending = null;
            state.pendingSignal = null;
        });
        return state.pending;
    }

    function fetchKospiMinutePriceDay(fetchImpl, baseUrl, date, options) {
        var settings = options || {};
        var day = normalizeIsoDate(date);
        if (!day) return Promise.reject(new Error('KOSPI 분봉 날짜가 올바르지 않습니다.'));
        var now = Number.isFinite(settings.now) ? settings.now : Date.now();
        var ttlMs = Number.isFinite(settings.ttlMs) ? settings.ttlMs : 15 * 60 * 1000;
        var cacheKey = String(baseUrl || '') + '|' + day;
        var state = kospiMinutePressureDayCache[cacheKey] || { value: null, expiresAt: 0, pending: null };
        kospiMinutePressureDayCache[cacheKey] = state;
        if (settings.forceRefresh) state.expiresAt = 0;
        if (state.value && state.expiresAt > now) return Promise.resolve(state.value);
        if (state.pending) return state.pending;
        var compactDate = day.replace(/-/g, '');
        var minuteUrl = new URL('index/KOSPI/minute', baseUrl);
        minuteUrl.searchParams.set('startDateTime', compactDate + '0900');
        minuteUrl.searchParams.set('endDateTime', compactDate + '1530');
        state.pending = fetchJson(
            fetchImpl,
            minuteUrl.href,
            settings.signal,
            settings.nonce || String(now)
        ).then(function (payload) {
            var bars = normalizeKospiIntradayMinute(payload, day);
            if (bars.length < 2) throw new Error(day + ' KOSPI 분봉이 비어 있습니다.');
            var value = {
                date: day,
                interval: '1m',
                sourceLastAt: day + 'T' + bars[bars.length - 1].time + ':00+09:00',
                bars: bars
            };
            state.value = value;
            state.expiresAt = now + ttlMs;
            return value;
        }).finally(function () {
            state.pending = null;
        });
        return state.pending;
    }

    function fetchKospiMinutePressureDays(fetchImpl, baseUrl, dates, options) {
        var settings = options || {};
        var normalizedDates = (dates || []).map(normalizeIsoDate).filter(function (date, index, values) {
            return Boolean(date) && values.indexOf(date) === index;
        }).sort();
        if (!normalizedDates.length) return Promise.resolve([]);
        var results = new Array(normalizedDates.length);
        var nextIndex = 0;
        var workerCount = Math.max(1, Math.min(normalizedDates.length, Number(settings.concurrencyLimit) || 4));
        function runWorker() {
            var index = nextIndex;
            nextIndex += 1;
            if (index >= normalizedDates.length) return Promise.resolve();
            return fetchKospiMinutePriceDay(fetchImpl, baseUrl, normalizedDates[index], settings).then(function (day) {
                results[index] = day;
            }).catch(function () {
                // Naver keeps only a limited intraday history. A missing older
                // session must not discard newer dates that still overlap the
                // locally archived KODEX minute data.
                results[index] = null;
            }).then(function () {
                return runWorker();
            });
        }
        var workers = [];
        for (var index = 0; index < workerCount; index += 1) workers.push(runWorker());
        return Promise.all(workers).then(function () {
            return estimateBvcPressureDays(results.filter(Boolean));
        });
    }

    function fetchKodexHistory(fetchImpl, baseUrl, signal, nonce, now, ttlMs) {
        if (kodexHistoryCache.value && kodexHistoryCache.expiresAt > now) {
            return Promise.resolve(kodexHistoryCache.value);
        }
        if (kodexHistoryCache.pending) return kodexHistoryCache.pending;

        var historyPrefix = new URL('stock/122630/history/', baseUrl).href;
        kodexHistoryCache.pending = Promise.all([1, 2, 3, 4, 5, 6, 7].map(function (page) {
            return fetchJson(fetchImpl, historyPrefix + 'price-' + page, signal, nonce);
        })).then(function (parts) {
            var history = normalizeKodexPriceHistory(parts);
            if (history.length < 55) throw new Error('KODEX 가격 이력이 부족합니다.');
            kodexHistoryCache.value = history;
            kodexHistoryCache.expiresAt = now + ttlMs;
            return history;
        }).finally(function () {
            kodexHistoryCache.pending = null;
        });
        return kodexHistoryCache.pending;
    }

    function fetchTqqqHistory(fetchImpl, baseUrl, signal, nonce, now, ttlMs) {
        if (tqqqHistoryCache.value && tqqqHistoryCache.expiresAt > now) {
            return Promise.resolve(tqqqHistoryCache.value);
        }
        if (tqqqHistoryCache.pending) return tqqqHistoryCache.pending;

        var historyUrl = new URL('us/TQQQ/history', baseUrl).href;
        tqqqHistoryCache.pending = fetchText(fetchImpl, historyUrl, signal, nonce).then(function (csv) {
            var history = normalizeTqqqPriceHistory(csv);
            if (history.length < 55) throw new Error('TQQQ 가격 이력이 부족합니다.');
            tqqqHistoryCache.value = history;
            tqqqHistoryCache.expiresAt = now + ttlMs;
            return history;
        }).finally(function () {
            tqqqHistoryCache.pending = null;
        });
        return tqqqHistoryCache.pending;
    }

    function fetchTqqqIntradayHistory(fetchImpl, baseUrl, signal, nonce, now, ttlMs, interval) {
        var oneMinute = interval === 1;
        var cache = oneMinute ? tqqqIntradayOneMinuteCache : tqqqIntradayFiveMinuteCache;
        if (cache.value && cache.expiresAt > now) return Promise.resolve(cache.value);
        if (cache.pending) return cache.pending;
        var route = oneMinute ? 'us/TQQQ/intraday-1m' : 'us/TQQQ/intraday-5m';
        cache.pending = fetchText(fetchImpl, new URL(route, baseUrl).href, signal, nonce).then(function (payload) {
            var rows = normalizeTqqqIntradayHistory(payload, oneMinute ? 1 : 5);
            if (!rows.length) throw new Error('TQQQ 분봉 이력이 비어 있습니다.');
            cache.value = rows;
            cache.expiresAt = now + ttlMs;
            return rows;
        }).finally(function () {
            cache.pending = null;
        });
        return cache.pending;
    }

    function fetchKodexVolumePressure(fetchImpl, url, signal, nonce, now, ttlMs) {
        if (kodexVolumePressureCache.value && kodexVolumePressureCache.expiresAt > now) {
            return Promise.resolve(kodexVolumePressureCache.value);
        }
        if (kodexVolumePressureCache.pending) return kodexVolumePressureCache.pending;
        kodexVolumePressureCache.pending = fetchJson(fetchImpl, url, signal, nonce).then(function (payload) {
            var rows = normalizeKodexVolumePressure(payload);
            if (!rows.length) throw new Error('KODEX 거래 압력 이력이 비어 있습니다.');
            kodexVolumePressureCache.value = rows;
            kodexVolumePressureCache.expiresAt = now + ttlMs;
            return rows;
        }).finally(function () {
            kodexVolumePressureCache.pending = null;
        });
        return kodexVolumePressureCache.pending;
    }

    function fetchKodexIntradayIndex(fetchImpl, url, signal, nonce, now, ttlMs) {
        if (kodexIntradayIndexCache.value && kodexIntradayIndexCache.expiresAt > now) {
            return Promise.resolve(kodexIntradayIndexCache.value);
        }
        if (kodexIntradayIndexCache.pending) return kodexIntradayIndexCache.pending;
        kodexIntradayIndexCache.pending = fetchJson(fetchImpl, url, signal, nonce).then(function (payload) {
            var rows = normalizeKodexIntradayIndex(payload);
            if (!rows.length) throw new Error('KODEX 분봉 이력이 비어 있습니다.');
            kodexIntradayIndexCache.value = rows;
            kodexIntradayIndexCache.expiresAt = now + ttlMs;
            return rows;
        }).finally(function () {
            kodexIntradayIndexCache.pending = null;
        });
        return kodexIntradayIndexCache.pending;
    }

    function fetchKodexIntradayDay(indexUrl, date, fetchImpl, options) {
        var settings = options || {};
        var day = String(date || '');
        var now = Number.isFinite(settings.now) ? settings.now : Date.now();
        var ttlMs = Number.isFinite(settings.ttlMs) ? settings.ttlMs : 30 * 60 * 1000;
        var cache = kodexIntradayDayCache[day];
        if (cache && cache.value && cache.expiresAt > now) return Promise.resolve(cache.value);
        if (cache && cache.pending) return cache.pending;
        var indexRows = settings.indexRows || kodexIntradayIndexCache.value || [];
        var entry = indexRows.filter(function (row) { return row.date === day; })[0];
        if (!entry) return Promise.reject(new Error('선택한 거래일의 분봉이 없습니다.'));
        var state = cache || { value: null, expiresAt: 0, pending: null };
        kodexIntradayDayCache[day] = state;
        state.pending = fetchJson(
            fetchImpl,
            new URL(entry.path, indexUrl).href,
            settings.signal,
            settings.nonce || String(now)
        ).then(function (payload) {
            var normalized = normalizeKodexIntradayDay(payload);
            if (normalized.date !== day) throw new Error('선택한 거래일과 분봉 날짜가 다릅니다.');
            state.value = normalized;
            state.expiresAt = now + ttlMs;
            return normalized;
        }).finally(function () {
            state.pending = null;
        });
        return state.pending;
    }

    function fetchKodexLiveIntraday(fetchImpl, baseUrl, date, signal, nonce) {
        var compactDate = String(date || '').replace(/-/g, '');
        if (!/^\d{8}$/.test(compactDate)) return Promise.reject(new Error('오늘 분봉 날짜가 올바르지 않습니다.'));
        var url = new URL('stock/122630/minute', baseUrl);
        url.searchParams.set('startDateTime', compactDate + '0900');
        url.searchParams.set('endDateTime', compactDate + '1530');
        return fetchJson(fetchImpl, url.href, signal, nonce).then(function (payload) {
            if (!Array.isArray(payload) || payload.length < 1) throw new Error('오늘 KODEX 분봉이 아직 없습니다.');
            return payload;
        });
    }

    function fetchLatest(baseUrl, fetchImpl, options) {
        var settings = options || {};
        var now = Number.isFinite(settings.now) ? settings.now : Date.now();
        var nonce = settings.nonce || String(now);
        var signal = settings.signal;
        var currentSeoulDate = seoulDate(now);
        if (settings.forceRefresh) {
            kodexHistoryCache.expiresAt = 0;
            tqqqHistoryCache.expiresAt = 0;
            tqqqIntradayOneMinuteCache.expiresAt = 0;
            tqqqIntradayFiveMinuteCache.expiresAt = 0;
            kodexVolumePressureCache.expiresAt = 0;
            kodexIntradayIndexCache.expiresAt = 0;
            kodexIntradayDayCache = {};
        }
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
        var exchangeRequest = fetchJson(
            fetchImpl,
            new URL('exchange/usdkrw', baseUrl).href,
            signal,
            nonce
        ).then(function (payload) {
            return normalizeExchange(payload, now);
        });

        var optionalIndexRequests = indexRequests.map(function (request) {
            return request.catch(function () { return null; });
        });
        var optionalStockRequests = stockRequests.map(function (request) {
            return request.catch(function () { return null; });
        });
        var optionalExchangeRequest = exchangeRequest.catch(function () { return null; });
        var optionalKodexHistoryRequest = fetchKodexHistory(
            fetchImpl,
            baseUrl,
            signal,
            nonce,
            now,
            Number.isFinite(settings.historyTtlMs) ? settings.historyTtlMs : 15 * 60 * 1000
        ).catch(function () { return null; });
        var optionalTqqqHistoryRequest = fetchTqqqHistory(
            fetchImpl,
            baseUrl,
            signal,
            nonce,
            now,
            Number.isFinite(settings.historyTtlMs) ? settings.historyTtlMs : 15 * 60 * 1000
        ).catch(function () { return null; });
        var optionalTqqqIntradayOneMinuteRequest = fetchTqqqIntradayHistory(
            fetchImpl,
            baseUrl,
            signal,
            nonce,
            now,
            Number.isFinite(settings.historyTtlMs) ? settings.historyTtlMs : 15 * 60 * 1000,
            1
        ).catch(function () { return null; });
        var optionalTqqqIntradayFiveMinuteRequest = fetchTqqqIntradayHistory(
            fetchImpl,
            baseUrl,
            signal,
            nonce,
            now,
            Number.isFinite(settings.historyTtlMs) ? settings.historyTtlMs : 15 * 60 * 1000,
            5
        ).catch(function () { return null; });
        var volumePressureUrl = settings.volumePressureUrl
            || new URL('../assets/data/kodex-volume-pressure.json', baseUrl).href;
        var optionalKodexVolumePressureRequest = fetchKodexVolumePressure(
            fetchImpl,
            volumePressureUrl,
            signal,
            nonce,
            now,
            Number.isFinite(settings.historyTtlMs) ? settings.historyTtlMs : 15 * 60 * 1000
        ).catch(function () { return null; });
        var intradayIndexUrl = settings.intradayIndexUrl
            || new URL('../assets/data/kodex-intraday-index.json', baseUrl).href;
        var optionalKodexIntradayIndexRequest = fetchKodexIntradayIndex(
            fetchImpl,
            intradayIndexUrl,
            signal,
            nonce,
            now,
            Number.isFinite(settings.historyTtlMs) ? settings.historyTtlMs : 15 * 60 * 1000
        ).catch(function () { return null; });
        var optionalKodexLiveIntradayRequest = fetchKodexLiveIntraday(
            fetchImpl,
            baseUrl,
            currentSeoulDate,
            signal,
            nonce
        ).catch(function () { return null; });

        return Promise.all(optionalIndexRequests.concat(optionalStockRequests).concat([
            optionalExchangeRequest,
            optionalKodexHistoryRequest,
            optionalTqqqHistoryRequest,
            optionalTqqqIntradayOneMinuteRequest,
            optionalTqqqIntradayFiveMinuteRequest,
            optionalKodexVolumePressureRequest,
            optionalKodexIntradayIndexRequest,
            optionalKodexLiveIntradayRequest
        ])).then(function (items) {
            var markets = items.slice(0, INDEX_CODES.length).filter(Boolean);
            var instruments = items.slice(INDEX_CODES.length, INDEX_CODES.length + STOCKS.length).filter(Boolean);
            var exchange = items[INDEX_CODES.length + STOCKS.length];
            var kodexHistory = items[INDEX_CODES.length + STOCKS.length + 1];
            var tqqqHistory = items[INDEX_CODES.length + STOCKS.length + 2];
            var tqqqIntradayOneMinute = items[INDEX_CODES.length + STOCKS.length + 3];
            var tqqqIntradayFiveMinute = items[INDEX_CODES.length + STOCKS.length + 4];
            var kodexVolumePressure = items[INDEX_CODES.length + STOCKS.length + 5];
            var kodexIntradayIndex = items[INDEX_CODES.length + STOCKS.length + 6];
            var kodexLiveIntradayRaw = items[INDEX_CODES.length + STOCKS.length + 7];
            if (!markets.length) throw new Error('국내 지수 시세를 불러오지 못했습니다.');
            var primaryMarket = markets.filter(function (market) { return market.id === 'KOSPI'; })[0] || markets[0];
            var kospiMarket = markets.filter(function (market) { return market.id === 'KOSPI'; })[0] || null;
            var marketSessionDate = kospiMarket && kospiMarket.sessionDate || currentSeoulDate;
            var marketTimestamp = Date.parse(primaryMarket.asOf);
            var statuses = markets.map(function (market) { return market.marketStatus; });
            var marketState = statuses.every(function (status) { return status === 'CLOSE'; })
                ? '한국 정규장 마감'
                : statuses.some(function (status) { return status === 'OPEN'; })
                    ? '한국 정규장 장중'
                    : '최근 거래일 시세';
            var missingSources = [];
            INDEX_CODES.forEach(function (code) {
                if (!markets.some(function (market) { return market.id === code; })) missingSources.push(code);
            });
            STOCKS.forEach(function (stock) {
                if (!instruments.some(function (instrument) { return instrument.id === stock.id; })) missingSources.push(stock.label);
            });
            if (!exchange) missingSources.push('달러/원');
            var kodexInstrument = instruments.filter(function (instrument) { return instrument.id === 'KODEX'; })[0];
            if (kodexInstrument && kodexHistory) {
                kodexInstrument.priceHistory = mergeKodexVolumePressure(kodexHistory, kodexVolumePressure);
            } else if (kodexInstrument) {
                missingSources.push('KODEX 가격·수급');
            }
            if (kodexInstrument && !kodexVolumePressure) missingSources.push('KODEX 분봉 기반 거래 압력');
            if (kodexInstrument && kodexIntradayIndex) {
                kodexInstrument.intradayIndex = ensureCurrentIntradayIndex(
                    kodexIntradayIndex,
                    marketSessionDate,
                    kospiMarket && kospiMarket.marketStatus,
                    null,
                    now
                );
                kodexInstrument.intradayIndexUrl = intradayIndexUrl;
            } else if (kodexInstrument) {
                missingSources.push('KODEX 분봉 이력');
            }
            if (kodexInstrument && kodexLiveIntradayRaw && kodexVolumePressure && kodexVolumePressure.length) {
                var referencePressure = kodexVolumePressure[kodexVolumePressure.length - 1];
                try {
                    kodexInstrument.liveIntradayDay = normalizeKodexLiveIntradayDay(
                        kodexLiveIntradayRaw,
                        marketSessionDate,
                        referencePressure.sigma,
                        referencePressure.sigmaSampleSize
                    );
                    kodexInstrument.intradayIndex = ensureCurrentIntradayIndex(
                        kodexInstrument.intradayIndex || [],
                        marketSessionDate,
                        kospiMarket && kospiMarket.marketStatus,
                        kodexInstrument.liveIntradayDay,
                        now
                    );
                } catch (error) {
                    missingSources.push('KODEX 오늘 분봉');
                }
            } else if (kodexInstrument && statuses.some(function (status) { return status === 'OPEN'; })) {
                missingSources.push('KODEX 오늘 분봉');
            }
            if (!tqqqHistory) missingSources.push('TQQQ 가격');
            if (!tqqqIntradayOneMinute && !tqqqIntradayFiveMinute) missingSources.push('TQQQ 분봉 이력');
            var delayedSources = markets.concat(instruments).filter(function (item) { return item.delayed; }).map(function (item) {
                return item.label;
            });
            if (exchange && exchange.delayed) delayedSources.push(exchange.label);
            delayedSources = delayedSources.filter(function (label, index, labels) {
                return labels.indexOf(label) === index;
            });

            return {
                asOf: new Date(marketTimestamp).toISOString(),
                asOfDisplay: formatAsOfDisplay(marketTimestamp),
                marketState: marketState,
                markets: markets,
                instruments: instruments,
                tqqqHistory: tqqqHistory,
                tqqqIntraday: {
                    oneMinute: tqqqIntradayOneMinute || [],
                    fiveMinute: tqqqIntradayFiveMinute || []
                },
                exchange: exchange,
                program: kospiMarket ? kospiMarket.program : null,
                partial: missingSources.length > 0 || delayedSources.length > 0,
                missingSources: missingSources,
                delayedSources: delayedSources,
                retrievedAt: new Date(now).toISOString(),
                sourceLabel: 'Naver Finance의 KRX 공개 시세·수급'
            };
        });
    }

    return {
        fetchLatest: fetchLatest,
        normalizeIndex: normalizeIndex,
        normalizeStock: normalizeStock,
        normalizeExchange: normalizeExchange,
        normalizeKodexPriceHistory: normalizeKodexPriceHistory,
        normalizeKospiPriceHistory: normalizeKospiPriceHistory,
        normalizeKospiForeignFlowHtml: normalizeKospiForeignFlowHtml,
        mergeKospiTechnicalHistory: mergeKospiTechnicalHistory,
        normalizeKospiIntradayMinute: normalizeKospiIntradayMinute,
        normalizeKospiIntradayForeignFlowHtml: normalizeKospiIntradayForeignFlowHtml,
        extractKospiIntradayForeignFlowPageCount: extractKospiIntradayForeignFlowPageCount,
        mergeKospiIntradayForeignFlow: mergeKospiIntradayForeignFlow,
        calculateMacd: calculateMacd,
        fetchKospiTechnicalHistory: fetchKospiTechnicalHistory,
        fetchKospiIntradayDay: fetchKospiIntradayDay,
        estimateBvcPressureDays: estimateBvcPressureDays,
        calculateCompositeVolumeMomentum: calculateCompositeVolumeMomentum,
        calculateCompositeDailyVolumeMomentum: calculateCompositeDailyVolumeMomentum,
        fetchKospiMinutePressureDays: fetchKospiMinutePressureDays,
        normalizeTqqqPriceHistory: normalizeTqqqPriceHistory,
        normalizeTqqqIntradayHistory: normalizeTqqqIntradayHistory,
        normalizeKodexVolumePressure: normalizeKodexVolumePressure,
        normalizeKodexIntradayIndex: normalizeKodexIntradayIndex,
        normalizeKodexIntradayDay: normalizeKodexIntradayDay,
        normalizeKodexLiveIntradayDay: normalizeKodexLiveIntradayDay,
        ensureCurrentIntradayIndex: ensureCurrentIntradayIndex,
        preferredIntradayDate: preferredIntradayDate,
        buildRollingIntradayDay: buildRollingIntradayDay,
        buildRollingIntradayDays: buildRollingIntradayDays,
        mergeRuntimeIntradayIndex: mergeRuntimeIntradayIndex,
        intradaySourceDate: intradaySourceDate,
        mergeKodexVolumePressure: mergeKodexVolumePressure,
        fetchKodexIntradayDay: fetchKodexIntradayDay,
        parseNumber: parseNumber,
        formatAsOfDisplay: formatAsOfDisplay
    };
}));
