/* 공개 OHLCV와 지표 정의로 계산하는 기술적 분석 엔진. 외부 코드·거래 데이터는 사용하지 않는다. */
(function (root, factory) {
    'use strict';
    var engine = factory();
    if (typeof module === 'object' && module.exports) module.exports = engine;
    if (root) root.TechnicalAnalysisEngine = engine;
}(typeof window !== 'undefined' ? window : typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';

    var indicatorFields = ['ema20', 'ema50', 'rsi', 'macd', 'macdSignal', 'macdHistogram', 'atr', 'supertrend', 'supertrendDirection', 'avwap', 'avwapUpper', 'avwapLower'];

    function number(value) {
        if (value === null || value === undefined || typeof value === 'boolean' || typeof value === 'object' || (typeof value === 'string' && !value.trim())) return null;
        var parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : null;
    }

    function dateString(value) {
        if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
        var parsed = new Date(value + 'T00:00:00Z');
        return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value ? value : null;
    }

    function timeString(value) {
        if (value === null || value === undefined || value === '') return '';
        if (typeof value !== 'string') return null;
        var match = /^(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(value);
        if (!match || Number(match[1]) > 23 || Number(match[2]) > 59 || Number(match[3] || 0) > 59) return null;
        return match[1] + ':' + match[2] + (match[3] && match[3] !== '00' ? ':' + match[3] : '');
    }

    function normalizeBars(raw) {
        if (!Array.isArray(raw)) return [];
        var byIdentity = Object.create(null);
        raw.forEach(function (row) {
            if (!row || typeof row !== 'object') return;
            var date = dateString(row.date);
            var time = timeString(row.time);
            var open = number(row.open);
            var high = number(row.high);
            var low = number(row.low);
            var close = number(row.close);
            if (!date || time === null || open === null || high === null || low === null || close === null) return;
            if (Math.min(open, high, low, close) <= 0 || high < Math.max(open, low, close) || low > Math.min(open, high, close)) return;
            var volume = number(row.volume);
            var bar = { date: date, open: open, high: high, low: low, close: close, volume: volume !== null && volume >= 0 ? volume : null };
            if (time) bar.time = time;
            // 마지막 유효 정정값을 채택한다. 거래량 결측은 0으로 대체하지 않는다.
            byIdentity[date + 'T' + (time || '')] = bar;
        });
        return Object.keys(byIdentity).sort().map(function (key) { return byIdentity[key]; });
    }

    function aggregateBars(raw, timeframe) {
        var rows = normalizeBars(raw);
        var frame = String(timeframe || 'native');
        var minutes = /^(5|15|30|60)$/.test(frame) ? Number(frame) : null;
        if (frame !== 'weekly' && frame !== 'monthly' && minutes === null) return rows;
        var buckets = Object.create(null);
        var keys = [];
        rows.forEach(function (bar) {
            var date = bar.date;
            var time = '';
            if (frame === 'weekly') {
                var day = new Date(date + 'T00:00:00Z');
                day.setUTCDate(day.getUTCDate() - ((day.getUTCDay() + 6) % 7));
                date = day.toISOString().slice(0, 10);
            } else if (frame === 'monthly') {
                date = date.slice(0, 7) + '-01';
            } else if (bar.time) {
                var minuteOfDay = Number(bar.time.slice(0, 2)) * 60 + Number(bar.time.slice(3, 5));
                var bucketMinute = Math.floor(minuteOfDay / minutes) * minutes;
                time = String(Math.floor(bucketMinute / 60)).padStart(2, '0') + ':' + String(bucketMinute % 60).padStart(2, '0');
            }
            var key = date + 'T' + time;
            if (!buckets[key]) {
                buckets[key] = { date: date, open: bar.open, high: bar.high, low: bar.low, close: bar.close, volume: bar.volume };
                if (time) buckets[key].time = time;
                keys.push(key);
            } else {
                var result = buckets[key];
                result.high = Math.max(result.high, bar.high);
                result.low = Math.min(result.low, bar.low);
                result.close = bar.close;
                result.volume = result.volume === null || bar.volume === null ? null : result.volume + bar.volume;
            }
        });
        return keys.map(function (key) { return buckets[key]; });
    }

    function periodOption(value, fallback) {
        var parsed = number(value);
        return parsed !== null && parsed >= 1 && parsed <= 10000 ? Math.floor(parsed) : fallback;
    }

    // EMA는 최초 연속 period개 관측값의 SMA로 시작하며, 결측 뒤에는 다시 예열한다.
    function ema(values, period) {
        var result = [];
        var count = 0;
        var sum = 0;
        var previous = null;
        var alpha = 2 / (period + 1);
        values.forEach(function (value) {
            if (value === null) {
                count = 0;
                sum = 0;
                previous = null;
                result.push(null);
                return;
            }
            if (previous === null) {
                count += 1;
                sum += value;
                if (count === period) previous = sum / period;
            } else {
                previous = previous + alpha * (value - previous);
            }
            result.push(previous);
        });
        return result;
    }

    function indicators(raw, options) {
        var rows = normalizeBars(raw);
        options = options || {};
        var atrPeriod = periodOption(options.atrPeriod, 10);
        var rsiPeriod = periodOption(options.rsiPeriod, 14);
        var multiplier = number(options.atrMultiplier);
        if (multiplier === null || multiplier <= 0) multiplier = 3;
        var anchor = number(options.anchorIndex);
        anchor = anchor === null ? 0 : Math.max(0, Math.floor(anchor));
        var closes = rows.map(function (bar) { return bar.close; });
        var ema20 = ema(closes, 20);
        var ema50 = ema(closes, 50);
        var fast = ema(closes, 12);
        var slow = ema(closes, 26);
        var macd = fast.map(function (value, index) { return value === null || slow[index] === null ? null : value - slow[index]; });
        var signal = ema(macd, 9);
        var trSum = 0;
        var atr = null;
        var gain = 0;
        var loss = 0;
        var upper = null;
        var lower = null;
        var direction = null;
        var volumeSum = 0;
        var mean = 0;
        var moment = 0;
        var missingVolume = false;
        return rows.map(function (bar, index) {
            var result = Object.assign({}, bar);
            indicatorFields.forEach(function (field) { result[field] = null; });
            result.ema20 = ema20[index];
            result.ema50 = ema50[index];
            result.macd = macd[index];
            result.macdSignal = signal[index];
            result.macdHistogram = macd[index] === null || signal[index] === null ? null : macd[index] - signal[index];
            var tr = index === 0 ? bar.high - bar.low : Math.max(bar.high - bar.low, Math.abs(bar.high - rows[index - 1].close), Math.abs(bar.low - rows[index - 1].close));
            if (index < atrPeriod) trSum += tr;
            if (index === atrPeriod - 1) atr = trSum / atrPeriod;
            else if (index >= atrPeriod) atr = (atr * (atrPeriod - 1) + tr) / atrPeriod;
            result.atr = atr;
            if (index > 0) {
                var change = bar.close - rows[index - 1].close;
                var up = Math.max(change, 0);
                var down = Math.max(-change, 0);
                if (index <= rsiPeriod) {
                    gain += up;
                    loss += down;
                    if (index === rsiPeriod) { gain /= rsiPeriod; loss /= rsiPeriod; }
                } else {
                    gain = (gain * (rsiPeriod - 1) + up) / rsiPeriod;
                    loss = (loss * (rsiPeriod - 1) + down) / rsiPeriod;
                }
                if (index >= rsiPeriod) result.rsi = loss === 0 ? (gain === 0 ? 50 : 100) : 100 - 100 / (1 + gain / loss);
            }
            if (atr !== null) {
                var mid = (bar.high + bar.low) / 2;
                var basicUpper = mid + multiplier * atr;
                var basicLower = mid - multiplier * atr;
                if (upper === null) {
                    upper = basicUpper;
                    lower = basicLower;
                    direction = 'down';
                } else {
                    var previousClose = rows[index - 1].close;
                    upper = basicUpper < upper || previousClose > upper ? basicUpper : upper;
                    lower = basicLower > lower || previousClose < lower ? basicLower : lower;
                    direction = direction === 'down' ? (bar.close > upper ? 'up' : 'down') : (bar.close < lower ? 'down' : 'up');
                }
                result.supertrendDirection = direction;
                result.supertrend = direction === 'up' ? lower : upper;
            }
            if (index >= anchor) {
                if (bar.volume === null) missingVolume = true;
                if (!missingVolume && bar.volume > 0) {
                    var typical = (bar.high + bar.low + bar.close) / 3;
                    var nextVolume = volumeSum + bar.volume;
                    var difference = typical - mean;
                    mean += difference * bar.volume / nextVolume;
                    // 가중 Welford 갱신으로 큰 주가에서도 분산 상쇄 오차를 줄인다.
                    moment += bar.volume * difference * (typical - mean);
                    volumeSum = nextVolume;
                }
                if (!missingVolume && volumeSum > 0) {
                    var deviation = Math.sqrt(Math.max(0, moment / volumeSum));
                    result.avwap = mean;
                    result.avwapUpper = mean + deviation;
                    result.avwapLower = mean - deviation;
                }
            }
            return result;
        });
    }

    function volumeProfile(raw, options) {
        var rows = normalizeBars(raw);
        options = options || {};
        var count = Math.max(1, Math.min(200, periodOption(options.bins, 32)));
        var area = number(options.valueArea);
        if (area === null || area <= 0 || area > 1) area = 0.7;
        var known = rows.filter(function (bar) { return bar.volume !== null; });
        var totalVolume = known.reduce(function (sum, bar) { return sum + bar.volume; }, 0);
        var result = { bins: [], poc: null, vah: null, val: null, totalVolume: totalVolume, coverage: rows.length ? known.length / rows.length : 0, method: 'ohlcv-estimate' };
        if (!known.length || totalVolume <= 0) return result;
        var low = known[0].low;
        var high = known[0].high;
        known.forEach(function (bar) { low = Math.min(low, bar.low); high = Math.max(high, bar.high); });
        if (high === low) {
            result.bins = [{ low: low, high: high, volume: totalVolume }];
            result.poc = result.vah = result.val = low;
            return result;
        }
        var width = (high - low) / count;
        for (var index = 0; index < count; index += 1) {
            result.bins.push({ low: low + index * width, high: index === count - 1 ? high : low + (index + 1) * width, volume: 0 });
        }
        known.forEach(function (bar) {
            if (bar.volume === 0) return;
            if (bar.high === bar.low) {
                var pointIndex = Math.min(count - 1, Math.max(0, Math.floor((bar.close - low) / width)));
                result.bins[pointIndex].volume += bar.volume;
                return;
            }
            var start = Math.max(0, Math.min(count - 1, Math.floor((bar.low - low) / width)));
            var end = Math.max(0, Math.min(count - 1, Math.floor((bar.high - low) / width)));
            var allocated = 0;
            var lastTouched = start;
            for (var i = start; i <= end; i += 1) {
                var bin = result.bins[i];
                var overlap = Math.max(0, Math.min(bar.high, bin.high) - Math.max(bar.low, bin.low));
                if (overlap > 0) {
                    var amount = bar.volume * overlap / (bar.high - bar.low);
                    bin.volume += amount;
                    allocated += amount;
                    lastTouched = i;
                }
            }
            result.bins[lastTouched].volume += bar.volume - allocated;
        });
        var pocIndex = 0;
        result.bins.forEach(function (bin, index) { if (bin.volume > result.bins[pocIndex].volume) pocIndex = index; });
        var left = pocIndex;
        var right = pocIndex;
        var covered = result.bins[pocIndex].volume;
        while (covered < totalVolume * area && (left > 0 || right < count - 1)) {
            var leftVolume = left > 0 ? result.bins[left - 1].volume : -1;
            var rightVolume = right < count - 1 ? result.bins[right + 1].volume : -1;
            if (rightVolume > leftVolume) { right += 1; covered += result.bins[right].volume; }
            else { left -= 1; covered += result.bins[left].volume; }
        }
        result.poc = (result.bins[pocIndex].low + result.bins[pocIndex].high) / 2;
        result.val = result.bins[left].low;
        result.vah = result.bins[right].high;
        return result;
    }

    function pivots(raw, lookback) {
        var rows = normalizeBars(raw);
        var span = periodOption(lookback, 3);
        var result = { highs: [], lows: [] };
        for (var index = span; index + span < rows.length; index += 1) {
            var high = true;
            var low = true;
            for (var offset = 1; offset <= span; offset += 1) {
                if (rows[index].high <= rows[index - offset].high || rows[index].high <= rows[index + offset].high) high = false;
                if (rows[index].low >= rows[index - offset].low || rows[index].low >= rows[index + offset].low) low = false;
            }
            if (high) result.highs.push({ index: index, value: rows[index].high, confirmedIndex: index + span });
            if (low) result.lows.push({ index: index, value: rows[index].low, confirmedIndex: index + span });
        }
        return result;
    }

    function detectPatterns(raw) {
        var rows = normalizeBars(raw);
        var points = pivots(rows, 3);
        var result = [];
        function scan(extremes, troughs, isTop) {
            for (var secondIndex = 1; secondIndex < extremes.length; secondIndex += 1) {
                var second = extremes[secondIndex];
                if (second.index < rows.length - 120) continue;
                var first = extremes[secondIndex - 1];
                var distance = second.index - first.index;
                if (distance < 6 || distance > 80 || Math.abs(first.value - second.value) / ((first.value + second.value) / 2) > 0.02) continue;
                var between = troughs.filter(function (point) { return point.index > first.index && point.index < second.index; });
                if (!between.length) continue;
                var neckline = between.reduce(function (value, point) { return isTop ? Math.min(value, point.value) : Math.max(value, point.value); }, between[0].value);
                var extreme = (first.value + second.value) / 2;
                if ((isTop ? extreme - neckline : neckline - extreme) / extreme < 0.01) continue;
                for (var index = second.confirmedIndex; index < rows.length; index += 1) {
                    // 확인 이전 가격 돌파는 과거 신호로 표시하지 않는다.
                    if (isTop ? rows[index].close < neckline : rows[index].close > neckline) {
                        result.push({ type: isTop ? 'double-top' : 'double-bottom', label: isTop ? '이중 천장' : '이중 바닥', index: second.index, confirmedIndex: index, level: neckline });
                        break;
                    }
                    // 패턴 극값을 먼저 넘어선 후보는 무효화한다.
                    if (isTop ? rows[index].close > Math.max(first.value, second.value) * 1.02 : rows[index].close < Math.min(first.value, second.value) * 0.98) break;
                }
            }
        }
        scan(points.highs, points.lows, true);
        scan(points.lows, points.highs, false);
        return result.sort(function (a, b) { return a.confirmedIndex - b.confirmedIndex; }).slice(-8);
    }

    function evaluateConditions(rows, conditions, match) {
        rows = Array.isArray(rows) ? rows : [];
        conditions = Array.isArray(conditions) ? conditions : [];
        var current = rows.length ? rows[rows.length - 1] : null;
        var previous = rows.length > 1 ? rows[rows.length - 2] : null;
        var allowed = ['close', 'rsi', 'macdHistogram', 'avwap', 'supertrend'];
        var values = conditions.map(function (condition) {
            condition = condition || {};
            var last = current ? number(current[condition.field]) : null;
            var prior = previous ? number(previous[condition.field]) : null;
            var threshold = number(condition.value);
            var crosses = condition.operator === 'crossesAbove' || condition.operator === 'crossesBelow';
            var supported = allowed.indexOf(condition.field) !== -1 && ['above', 'below', 'crossesAbove', 'crossesBelow'].indexOf(condition.operator) !== -1;
            var available = supported && threshold !== null && last !== null && (!crosses || prior !== null);
            var matched = false;
            if (available) {
                if (condition.operator === 'above') matched = last > threshold;
                else if (condition.operator === 'below') matched = last < threshold;
                else if (condition.operator === 'crossesAbove') matched = prior <= threshold && last > threshold;
                else matched = prior >= threshold && last < threshold;
            }
            return { field: condition.field, operator: condition.operator, value: threshold, current: last, previous: prior, available: available, matched: matched };
        });
        var any = match === 'any';
        return {
            matched: values.length > 0 && (any ? values.some(function (value) { return value.matched; }) : values.every(function (value) { return value.available && value.matched; })),
            available: values.length > 0 && (any ? values.some(function (value) { return value.available; }) : values.every(function (value) { return value.available; })),
            values: values
        };
    }

    function toCSV(raw, options) {
        var rows = Array.isArray(raw) ? raw.filter(function (row) { return row && typeof row === 'object'; }) : [];
        var fields = ['date', 'time', 'open', 'high', 'low', 'close', 'volume'].concat(indicatorFields.filter(function (field) {
            return rows.some(function (row) { return field === 'supertrendDirection' ? row[field] === 'up' || row[field] === 'down' : number(row[field]) !== null; });
        }));
        function cell(value, field) {
            if (value === null || value === undefined) return '';
            if (field !== 'date' && field !== 'time' && field !== 'supertrendDirection') {
                value = number(value);
                if (value === null) return '';
            }
            var text = String(value);
            if (field === 'date' || field === 'time' || field === 'supertrendDirection') {
                if (/^[\s]*[=+@-]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text;
            }
            return /[",\r\n]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
        }
        return (options && options.bom ? '\uFEFF' : '') + [fields.join(',')].concat(rows.map(function (row) {
            return fields.map(function (field) { return cell(row[field], field); }).join(',');
        })).join('\r\n');
    }

    return {
        normalizeBars: normalizeBars,
        aggregateBars: aggregateBars,
        indicators: indicators,
        volumeProfile: volumeProfile,
        pivots: pivots,
        detectPatterns: detectPatterns,
        evaluateConditions: evaluateConditions,
        toCSV: toCSV
    };
}));
