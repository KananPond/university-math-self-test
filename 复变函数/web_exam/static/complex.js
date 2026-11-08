/* ==========================================================================
 * 复变函数考试模拟系统 · 复平面图形组件
 * 作者：ZCode（GLM）    日期：2026-11-08    版本：1.0
 *
 * 说明：
 * 1. ComplexView.render：把图形规格画到 canvas 上——复平面坐标轴、
 *    点、模半径、辐角弧、实虚部投影虚线、共轭对称点、单位根。
 *    悬停显示复数的坐标、模与辐角。
 * 2. ComplexView.mount：计算题的多空作答表格，右侧同步画出复平面预览。
 * 3. 零依赖，纯原生实现，支持高分屏（devicePixelRatio）。
 * ========================================================================== */

(function () {
    'use strict';

    var AXIS = '#334155';
    var INK = '#0f172a';
    var GRID = 'rgba(148,163,184,0.22)';
    var DASH = 'rgba(100,116,139,0.55)';
    var POINT = '#2563eb';
    var CONJ = '#c97b3f';
    var ARC = '#2f6f5e';
    var MUTED = '#64748b';
    var FONT = '13px "Cambria Math", "Times New Roman", Georgia, serif';
    var LABEL_FONT = 'italic 14px "Cambria Math", "Times New Roman", Georgia, serif';
    var TICK_FONT = '10px "Noto Sans SC", system-ui, sans-serif';

    /* ---------------- 复数解析（与后端 complex_ref 语义一致） ---------------- */

    function readRational(text, index) {
        var start = index;
        var length = text.length;
        while (index < length && text[index] >= '0' && text[index] <= '9') {
            index += 1;
        }
        var intText = text.slice(start, index);

        if (index < length && text[index] === '.') {
            index += 1;
            var fracStart = index;
            while (index < length && text[index] >= '0' && text[index] <= '9') {
                index += 1;
            }
            var fracText = text.slice(fracStart, index);
            if (!intText && !fracText) {
                return null;
            }
            var value = parseFloat((intText || '0') + '.' + (fracText || '0'));
        } else {
            if (!intText) {
                return null;
            }
            value = parseInt(intText, 10);
        }

        if (index < length && text[index] === '/') {
            index += 1;
            var denStart = index;
            while (index < length && text[index] >= '0' && text[index] <= '9') {
                index += 1;
            }
            if (index === denStart) {
                return null;
            }
            var denominator = parseInt(text.slice(denStart, index), 10);
            if (denominator === 0) {
                return null;
            }
            value = value / denominator;
        }

        return { value: value, next: index };
    }

    function readTerm(text, index) {
        var length = text.length;
        var coef = 1;
        var hasNumber = false;
        var cursor = index;

        if (text[cursor] === '(') {
            var depth = 1;
            var scan = cursor + 1;
            while (scan < length) {
                if (text[scan] === '(') {
                    depth += 1;
                } else if (text[scan] === ')') {
                    depth -= 1;
                    if (depth === 0) {
                        break;
                    }
                }
                scan += 1;
            }
            if (scan >= length) {
                return null;
            }
            var inner = readRational(text.slice(cursor + 1, scan), 0);
            if (!inner) {
                return null;
            }
            coef = inner.value;
            hasNumber = true;
            cursor = scan + 1;
        } else {
            var rational = readRational(text, cursor);
            if (rational) {
                coef = rational.value;
                hasNumber = true;
                cursor = rational.next;
            }
        }

        /* 裸写的 √ 只取整数被开方数，"√3/2" 是 (√3)÷2 */
        if (text[cursor] === '√') {
            var radicand = readRational(text.slice(cursor + 1), 0);
            if (!radicand || radicand.value < 0) {
                return null;
            }
            return { value: coef * Math.sqrt(radicand.value),
                     next: radicand.next, consumed: true };
        }

        if (text.substr(cursor, 5) === 'sqrt(') {
            var close = text.indexOf(')', cursor);
            if (close < 0) {
                return null;
            }
            var innerRad = readRational(text.slice(cursor + 5, close), 0);
            if (!innerRad || innerRad.value < 0) {
                return null;
            }
            return { value: coef * Math.sqrt(innerRad.value),
                     next: close + 1, consumed: true };
        }

        if (text[cursor] === 'π') {
            return { value: coef * Math.PI, next: cursor + 1, consumed: true };
        }

        if (hasNumber) {
            return { value: coef, next: cursor, consumed: true };
        }

        return { value: 1, next: cursor, consumed: false };
    }

    function balanced(text) {
        var depth = 0;
        for (var i = 0; i < text.length; i += 1) {
            if (text[i] === '(') {
                depth += 1;
            } else if (text[i] === ')') {
                depth -= 1;
                if (depth < 0) {
                    return false;
                }
            }
        }

        return depth === 0;
    }

    /*
     * 解析复数文本，返回 {re, im} 或 null。
     * 支持 3+4i、1-i、4i、-i、i、3、-3/2、0.75、√13、2√3、√3/2、iπ、-iπ/2。
     */
    function parseComplex(text) {
        if (text === undefined || text === null) {
            return null;
        }
        var cleaned = String(text).replace(/\s+/g, '')
            .replace(/−/g, '-').replace(/·/g, '*').replace(/j/g, 'i');
        if (!cleaned) {
            return null;
        }

        while (cleaned.length > 1 && cleaned[0] === '('
               && cleaned[cleaned.length - 1] === ')'
               && balanced(cleaned.slice(1, -1))) {
            cleaned = cleaned.slice(1, -1);
        }

        var re = 0;
        var im = 0;
        var index = 0;
        var sign = 1;
        var length = cleaned.length;

        while (index < length) {
            if (cleaned[index] === '+') {
                sign = 1;
                index += 1;
            } else if (cleaned[index] === '-') {
                sign = -1;
                index += 1;
            }

            var term = readTerm(cleaned, index);
            if (!term) {
                return null;
            }

            var value = term.value;
            var cursor = term.next;
            var imaginary = false;

            /* 除法后缀（如 √3/2）：先算商，再判断是不是虚部 */
            if (cursor < length && cleaned[cursor] === '/') {
                var divisor = readRational(cleaned.slice(cursor + 1), 0);
                if (!divisor || divisor.value === 0) {
                    return null;
                }
                value = value / divisor.value;
                cursor = divisor.next;
            }

            if (cursor < length && cleaned[cursor] === 'i') {
                imaginary = true;
                cursor += 1;
                if (cursor < length && cleaned[cursor] === 'π') {
                    value = value * Math.PI;
                    cursor += 1;
                }
                /* 虚部后缀除法（如 iπ/2） */
                if (cursor < length && cleaned[cursor] === '/') {
                    var tailDivisor = readRational(cleaned.slice(cursor + 1), 0);
                    if (!tailDivisor || tailDivisor.value === 0) {
                        return null;
                    }
                    value = value / tailDivisor.value;
                    cursor = tailDivisor.next;
                }
            } else if (!term.consumed) {
                return null;
            }

            if (imaginary) {
                im += sign * value;
            } else {
                re += sign * value;
            }
            index = cursor;
        }

        return { re: re, im: im };
    }

    function formatComplex(value) {
        if (!value) {
            return '';
        }
        var parts = [];
        if (Math.abs(value.re) > 1e-12) {
            parts.push(round(value.re));
        }
        if (Math.abs(value.im) > 1e-12) {
            parts.push((parts.length ? (value.im < 0 ? '− ' : '+ ') : '')
                       + (Math.abs(value.im) === 1 ? '' : round(Math.abs(value.im)))
                       + 'i');
        } else if (!parts.length) {
            parts.push('0');
        }

        return parts.join(' ');
    }

    function round(value) {
        var rounded = Math.round(value * 1000) / 1000;
        if (Math.abs(rounded - Math.round(rounded)) < 1e-9) {
            return String(Math.round(rounded));
        }

        return String(rounded);
    }

    function modulus(value) {
        return Math.hypot(value.re, value.im);
    }

    function argumentDegrees(value) {
        return Math.atan2(value.im, value.re) * 180 / Math.PI;
    }

    /* ---------------- 绘图基础设施 ---------------- */

    function makeScale(points, size, padding) {
        /* 按所有点的模确定缩放比例，保证图形饱满又不越界 */
        var maxRadius = 1;
        points.forEach(function (point) {
            maxRadius = Math.max(maxRadius, modulus(point));
        });
        var usable = (size - 2 * padding) / 2;
        var scale = usable / (maxRadius * 1.45);
        if (!isFinite(scale) || scale <= 0) {
            scale = usable / 2;
        }

        return {
            scale: scale,
            center: size / 2,
            toX: function (x) { return this.center + x * this.scale; },
            toY: function (y) { return this.center - y * this.scale; }
        };
    }

    function drawAxes(ctx, size, frame, step) {
        var center = size / 2;
        var limit = size / 2;

        ctx.strokeStyle = GRID;
        ctx.lineWidth = 1;
        for (var value = -Math.ceil(limit / step) * step;
             value <= limit; value += step) {
            if (value === 0) {
                continue;
            }
            var offset = value * frame.scale;
            ctx.beginPath();
            ctx.moveTo(center + offset, 0);
            ctx.lineTo(center + offset, size);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(0, center - offset);
            ctx.lineTo(size, center - offset);
            ctx.stroke();
        }

        ctx.strokeStyle = AXIS;
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.moveTo(0, center);
        ctx.lineTo(size, center);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(center, size);
        ctx.lineTo(center, 0);
        ctx.stroke();

        /* 箭头 */
        ctx.fillStyle = AXIS;
        ctx.beginPath();
        ctx.moveTo(size - 1, center);
        ctx.lineTo(size - 8, center - 3.5);
        ctx.lineTo(size - 8, center + 3.5);
        ctx.closePath();
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(center, 1);
        ctx.lineTo(center - 3.5, 9);
        ctx.lineTo(center + 3.5, 9);
        ctx.closePath();
        ctx.fill();

        /* 轴名 */
        ctx.font = TICK_FONT;
        ctx.fillStyle = MUTED;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText('x', size - 12, center + 4);
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText('iy', center - 10, 12);
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText('O', center + 8, center + 3);
    }

    function drawPoint(ctx, frame, point, options) {
        var x = frame.toX(point.re);
        var y = frame.toY(point.im);
        var color = options.color || POINT;
        var radius = options.radius || 4.5;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();

        if (options.label) {
            ctx.font = LABEL_FONT;
            ctx.fillStyle = options.labelColor || INK;
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(options.label, x + 8, y - 8);
        }
    }

    function drawRadius(ctx, frame, point, color) {
        ctx.strokeStyle = color || 'rgba(37,99,235,0.65)';
        ctx.lineWidth = 1.3;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(frame.center, frame.center);
        ctx.lineTo(frame.toX(point.re), frame.toY(point.im));
        ctx.stroke();
    }

    function drawProjection(ctx, frame, point) {
        ctx.strokeStyle = DASH;
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        ctx.moveTo(frame.toX(point.re), frame.center);
        ctx.lineTo(frame.toX(point.re), frame.toY(point.im));
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(frame.center, frame.toY(point.im));
        ctx.lineTo(frame.toX(point.re), frame.toY(point.im));
        ctx.stroke();
        ctx.setLineDash([]);
    }

    function drawAngleArc(ctx, frame, point) {
        var radius = Math.min(frame.scale * 0.42, 34);
        var start = 0;
        var end = Math.atan2(point.im, point.re);
        if (end <= 0) {
            end += Math.PI * 2;
        }
        ctx.strokeStyle = ARC;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(frame.center, frame.center, radius, -start, -end, true);
        ctx.stroke();

        var mid = -(start + end) / 2;
        ctx.font = TICK_FONT;
        ctx.fillStyle = ARC;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(argumentDegrees(point).toFixed(0) + '°',
                     frame.center + Math.cos(mid) * (radius + 14),
                     frame.center + Math.sin(mid) * (radius + 14));
    }

    function drawCircle(ctx, frame, radius, label) {
        ctx.strokeStyle = 'rgba(47,111,94,0.6)';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.arc(frame.center, frame.center, radius * frame.scale,
                0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
        if (label) {
            ctx.font = TICK_FONT;
            ctx.fillStyle = ARC;
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(label, frame.center + 4,
                         frame.center - radius * frame.scale);
        }
    }

    /* ---------------- 图形渲染 ---------------- */

    /*
     * render(container, spec, options)
     * spec: { kind: 'point'|'roots'|'ops'|'plane', ... }
     */
    function render(container, spec, options) {
        options = options || {};
        var size = options.size || 240;
        var kind = (spec && spec.kind) || 'point';

        var wrap = document.createElement('span');
        wrap.className = 'cv-figure';
        var canvas = document.createElement('canvas');
        var dpr = window.devicePixelRatio || 1;
        canvas.width = Math.max(1, Math.round(size * dpr));
        canvas.height = Math.max(1, Math.round(size * dpr));
        canvas.style.width = size + 'px';
        canvas.style.height = size + 'px';
        canvas.className = 'cv-canvas';
        wrap.appendChild(canvas);
        var tip = document.createElement('span');
        tip.className = 'cv-tip';
        tip.hidden = true;
        wrap.appendChild(tip);

        var points = [];
        var circles = [];
        var main = null;
        var conjugate = null;
        var product = null;
        var labels = {};

        if (kind === 'point') {
            main = parseComplex(spec.z);
            if (main) {
                points.push(main);
                labels.main = spec.label || 'z';
                var show = spec.show || [];
                if (show.indexOf('conj') >= 0) {
                    conjugate = { re: main.re, im: -main.im };
                    points.push(conjugate);
                    labels.conjugate = (spec.label || 'z') + '̄';
                }
            }
        } else if (kind === 'roots') {
            var count = parseInt(spec.n, 10) || 3;
            var radius = spec.radius === undefined ? 1 : spec.radius;
            circles.push({ radius: radius, label: spec.label });
            for (var k = 0; k < count; k += 1) {
                var theta = 2 * Math.PI * k / count;
                var root = { re: radius * Math.cos(theta),
                             im: radius * Math.sin(theta) };
                points.push(root);
            }
            main = points[0];
        } else if (kind === 'ops') {
            var z1 = parseComplex(spec.z1);
            var z2 = parseComplex(spec.z2);
            if (z1 && z2) {
                product = { re: z1.re * z2.re - z1.im * z2.im,
                            im: z1.re * z2.im + z1.im * z2.re };
                points.push(z1);
                points.push(z2);
                points.push(product);
                main = z1;
            }
        } else if (kind === 'plane') {
            (spec.points || []).forEach(function (item) {
                var value = parseComplex(item.z);
                if (value) {
                    value.label = item.label;
                    points.push(value);
                }
            });
            (spec.circles || []).forEach(function (item) {
                circles.push(item);
            });
        }

        var frame = makeScale(points.concat(circles.map(function (circle) {
            return { re: circle.radius, im: 0 };
        })), size, 18);

        function draw() {
            var ctx = canvas.getContext('2d');
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            ctx.clearRect(0, 0, size, size);

            drawAxes(ctx, size, frame, frame.scale >= 30 ? 1 : 2);

            circles.forEach(function (circle) {
                drawCircle(ctx, frame, circle.radius, circle.label);
            });

            if (kind === 'point' && main) {
                var show = spec.show || [];
                if (show.indexOf('proj') >= 0) {
                    drawProjection(ctx, frame, main);
                }
                if (show.indexOf('radius') >= 0) {
                    drawRadius(ctx, frame, main);
                }
                if (show.indexOf('angle') >= 0) {
                    drawAngleArc(ctx, frame, main);
                }
                if (conjugate) {
                    ctx.strokeStyle = 'rgba(201,123,63,0.75)';
                    ctx.lineWidth = 1;
                    ctx.setLineDash([4, 3]);
                    ctx.beginPath();
                    ctx.moveTo(frame.toX(main.re), frame.toY(main.im));
                    ctx.lineTo(frame.toX(conjugate.re), frame.toY(conjugate.im));
                    ctx.stroke();
                    ctx.setLineDash([]);
                }
            }

            if (kind === 'ops' && product) {
                drawRadius(ctx, frame, product, 'rgba(201,123,63,0.7)');
            }

            points.forEach(function (point) {
                var isMain = kind === 'point' && point === main;
                var isConj = point === conjugate;
                var isProduct = point === product;
                drawPoint(ctx, frame, point, {
                    color: isConj ? CONJ : (isProduct ? CONJ : POINT),
                    label: point.label || labels.main || '',
                    labelColor: isConj ? CONJ : INK
                });
                if (isMain && spec.label) {
                    /* 主点标签单独画，避免被后续点覆盖 */
                }
            });
        }

        /* 悬停提示：坐标、模与辐角 */
        canvas.addEventListener('mousemove', function (event) {
            var bounds = canvas.getBoundingClientRect();
            var x = event.clientX - bounds.left;
            var y = event.clientY - bounds.top;
            var found = null;
            points.forEach(function (point) {
                if (found) {
                    return;
                }
                var dx = frame.toX(point.re) - x;
                var dy = frame.toY(point.im) - y;
                if (Math.sqrt(dx * dx + dy * dy) < 10) {
                    found = point;
                }
            });
            if (found) {
                var name = found.label
                    || (kind === 'roots' ? '单位根' : 'z');
                tip.textContent = name + ' = ' + formatComplex(found)
                    + '，|z| ≈ ' + modulus(found).toFixed(3)
                    + '，arg ≈ ' + argumentDegrees(found).toFixed(2) + '°';
                tip.hidden = false;
            } else {
                tip.hidden = true;
            }
        });
        canvas.addEventListener('mouseleave', function () {
            tip.hidden = true;
        });

        draw();

        if (container && container.appendChild) {
            container.appendChild(wrap);
        }

        return canvas;
    }

    /* ---------------- 作答组件（计算题多空） ---------------- */

    /*
     * mount(container, spec, onChange)
     * spec: { blanks: [{label, answer_type}], value: [{text}] }
     */
    function mount(container, spec, onChange) {
        var blanks = spec.blanks || [];
        var saved = spec.value || [];
        var layout = document.createElement('div');
        layout.className = 'cv-answer';

        var inputArea = document.createElement('div');
        inputArea.className = 'cv-answer-input';
        var inputTitle = document.createElement('p');
        inputTitle.className = 'cv-answer-title';
        inputTitle.textContent = '作答（每小问一行，支持 3+4i、√13、π/4）';
        inputArea.appendChild(inputTitle);

        var rows = [];
        blanks.forEach(function (blank, index) {
            var row = document.createElement('div');
            row.className = 'cv-blank-row';
            var label = document.createElement('label');
            label.className = 'cv-blank-label';
            label.textContent = blank.label || ('第 %d 空' % (index + 1));
            var input = document.createElement('input');
            input.type = 'text';
            input.className = 'cv-blank-input';
            input.autocomplete = 'off';
            input.spellcheck = false;
            input.placeholder = blank.answer_type === 'angle' ? '如 π/4'
                : (blank.answer_type === 'complex' ? '如 3+4i' : '如 5、√13');
            if (saved[index] !== undefined && saved[index] !== null) {
                input.value = String(saved[index]);
            }
            input.addEventListener('input', function () {
                refresh(true);
            });
            row.appendChild(label);
            row.appendChild(input);
            inputArea.appendChild(row);
            rows.push(input);
        });

        var previewArea = document.createElement('div');
        previewArea.className = 'cv-answer-preview';
        var previewTitle = document.createElement('p');
        previewTitle.className = 'cv-answer-title';
        previewTitle.textContent = '复平面预览';
        previewArea.appendChild(previewTitle);
        var previewBox = document.createElement('div');
        previewBox.className = 'cv-preview-box';
        previewArea.appendChild(previewBox);

        layout.appendChild(inputArea);
        layout.appendChild(previewArea);
        container.appendChild(layout);

        function currentValues() {
            return rows.map(function (input) {
                return input.value.trim();
            });
        }

        function refresh(notify) {
            previewBox.innerHTML = '';
            var values = currentValues()
                .map(function (text) { return parseComplex(text); })
                .filter(function (value) { return !!value; });
            if (values.length) {
                render(previewBox, {
                    kind: 'plane',
                    points: values.map(function (value, index) {
                        return { z: formatComplex(value),
                                 label: 'z' + (index + 1) };
                    })
                }, { size: 210 });
            } else {
                var hint = document.createElement('p');
                hint.className = 'cv-preview-hint';
                hint.textContent = '填入答案后，这里会画出你算出的复数。';
                previewBox.appendChild(hint);
            }
            if (notify && onChange) {
                onChange();
            }
        }

        refresh(false);

        return {
            get: function () {
                return { blanks: currentValues() };
            },
            inputs: rows
        };
    }

    window.ComplexView = {
        render: render,
        mount: mount,
        parseComplex: parseComplex,
        formatComplex: formatComplex
    };
}());
