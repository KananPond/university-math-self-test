/* ==========================================================================
 * 复平面实验台 · 交互逻辑
 * 作者：ZCode（GLM）    日期：2026-11-08    版本：1.0
 *
 * 说明：
 * 1. 输入 z₁、z₂ 后，主画布实时给出：模半径、辐角弧、实部/虚部投影虚线、
 *    共轭点 z̄₁、乘积 z₁z₂ 与商 z₁/z₂；鼠标悬停任一标注点可读出该点的
 *    代数形式、模与辐角。
 * 2. 勾选「演示乘法几何」后点击「▶ 播放」，用 1.6 秒动画演示
 *    「复数乘法 = 旋转 arg z₂ + 伸缩 |z₂|」，动画结束后短暂高亮 z₁z₂。
 * 3. 棣莫弗公式单独一块：画出 z, z², …, zⁿ 的轨迹（连线逐段变淡），
 *    直观看到模按 n 次方增长、辐角按 n 倍旋转；另有一块画 m 次单位根。
 * 4. parseComplex 是不依赖 DOM 的纯函数，并挂到 window.PlaneLab.parseComplex，
 *    便于离线自检脚本把「纯函数区」整段抽取后单独测试。
 * 5. 本页纯浏览器计算（浮点），仅用于直观理解；考试判分仍在服务端按精确值进行。
 * ========================================================================== */

/* ===== 纯函数区开始（离线自检脚本可整段抽取） ===== */

/* 解析失败时统一给出的提示文案 */
var PLANE_PARSE_ERROR = '无法识别的复数写法';

function isDigitChar(ch) {
    return ch >= '0' && ch <= '9';
}

/* 清理待解析文本：去空白、统一减号与乘号、sqrt( → √(、pi → π、j → i */
function cleanComplexText(text) {
    var cleaned = String(text).replace(/\s+/g, '');
    cleaned = cleaned.replace(/[−–—]/g, '-');
    cleaned = cleaned.replace(/[·×*]/g, '');
    cleaned = cleaned.replace(/sqrt\(/gi, '√(');
    cleaned = cleaned.replace(/pi/gi, 'π');
    cleaned = cleaned.replace(/j/g, 'i');

    return cleaned;
}

/* 读取一个十进制数（整数或小数），失败返回 null */
function readNumber(text, index) {
    var start = index;
    var seen = false;
    while (index < text.length && isDigitChar(text[index])) {
        index += 1;
        seen = true;
    }
    if (index < text.length && text[index] === '.') {
        index += 1;
        while (index < text.length && isDigitChar(text[index])) {
            index += 1;
            seen = true;
        }
    }
    if (!seen) {
        return null;
    }

    return { value: parseFloat(text.slice(start, index)), next: index };
}

/* 读取一个有理数（整数、小数或分数 a/b），失败返回 null */
function readRational(text, index) {
    var numerator = readNumber(text, index);
    if (!numerator) {
        return null;
    }
    if (text[numerator.next] === '/') {
        var denominator = readNumber(text, numerator.next + 1);
        if (!denominator || denominator.value === 0) {
            return null;
        }

        return { value: numerator.value / denominator.value, next: denominator.next };
    }

    return numerator;
}

/* 读取根式：√13 / √(3/2)，index 指向 √ */
function readRadical(text, index) {
    var cursor = index + 1;
    if (text[cursor] === '(') {
        var close = text.indexOf(')', cursor);
        if (close < 0) {
            return null;
        }
        var inner = readRational(text.slice(cursor + 1, close), 0);
        if (!inner || inner.next !== close - cursor - 1) {
            return null;
        }

        return { value: Math.sqrt(inner.value), next: close + 1 };
    }
    var start = cursor;
    while (cursor < text.length && isDigitChar(text[cursor])) {
        cursor += 1;
    }
    if (cursor === start) {
        return null;
    }

    return { value: Math.sqrt(parseInt(text.slice(start, cursor), 10)), next: cursor };
}

/* 读取一个「原子」：数字 / 分数 / 根式 / 带系数的根式（如 2√3），失败返回 null */
function readAtom(text, index) {
    var ch = text[index];
    if (ch === undefined) {
        return null;
    }
    if (isDigitChar(ch) || ch === '.') {
        var number = readNumber(text, index);
        if (!number) {
            return null;
        }
        if (text[number.next] === '√') {
            var radical = readRadical(text, number.next);
            if (!radical) {
                return null;
            }

            return { value: number.value * radical.value, next: radical.next };
        }

        return number;
    }
    if (ch === '(') {
        var close = text.indexOf(')', index);
        if (close < 0) {
            return null;
        }
        var inner = readRational(text.slice(index + 1, close), 0);
        if (!inner || inner.next !== close - index - 1) {
            return null;
        }
        var value = inner.value;
        var next = close + 1;
        if (text[next] === '√') {
            var radical2 = readRadical(text, next);
            if (!radical2) {
                return null;
            }

            return { value: value * radical2.value, next: radical2.next };
        }

        return { value: value, next: next };
    }
    if (ch === '√') {
        var radical3 = readRadical(text, index);
        if (!radical3) {
            return null;
        }

        return { value: radical3.value, next: radical3.next };
    }

    return null;
}

/* 读取一个「项」：可选 i / π 后缀，可选的 ÷分母 */
function readTerm(text, index) {
    var value = null;
    var hasImag = false;
    var hasPi = false;
    var consumed = false;

    /* i 与 π 的先后顺序都允许（如 -iπ/2、πi）；分母后面也可带 i（如 3/4i） */
    function readSuffix() {
        for (var k = 0; k < 2; k += 1) {
            var ch = text[index];
            if (ch === 'i' && !hasImag) {
                hasImag = true;
                index += 1;
                consumed = true;
            } else if (ch === 'π' && !hasPi) {
                hasPi = true;
                index += 1;
                consumed = true;
            } else {
                break;
            }
        }
    }

    var atom = readAtom(text, index);
    if (atom) {
        value = atom.value;
        index = atom.next;
        consumed = true;
    }

    readSuffix();

    if (value === null) {
        value = 1;
    }
    if (text[index] === '/') {
        var divisor = readAtom(text, index + 1);
        if (!divisor || divisor.value === 0) {
            return null;
        }
        value = value / divisor.value;
        index = divisor.next;
        consumed = true;
    }
    readSuffix();

    if (hasPi) {
        value = value * Math.PI;
    }

    if (!consumed) {
        return null;
    }

    return { value: value, imaginary: hasImag, next: index };
}

/* 解析复数文本。
 *
 * 返回 { ok: true, re: 实部, im: 虚部 } 或 { ok: false, message: 提示文案 }。
 * 支持：3+4i、1-i、4i、-i、i、3、-3/2、0.75、√13、2√3、√3/2、√(3/2)、
 *       π、π/4、-iπ/2。
 */
function parseComplex(text) {
    if (typeof text !== 'string') {
        return { ok: false, message: PLANE_PARSE_ERROR };
    }
    var cleaned = cleanComplexText(text);
    if (!cleaned) {
        return { ok: false, message: PLANE_PARSE_ERROR };
    }

    var re = 0;
    var im = 0;
    var index = 0;
    var length = cleaned.length;
    while (index < length) {
        var sign = 1;
        var ch = cleaned[index];
        if (ch === '+') {
            index += 1;
        } else if (ch === '-') {
            sign = -1;
            index += 1;
        }
        var term = readTerm(cleaned, index);
        if (!term) {
            return { ok: false, message: PLANE_PARSE_ERROR };
        }
        if (term.imaginary) {
            im += sign * term.value;
        } else {
            re += sign * term.value;
        }
        index = term.next;
        /* 项与项之间只能出现 + 或 - */
        if (index < length && cleaned[index] !== '+' && cleaned[index] !== '-') {
            return { ok: false, message: PLANE_PARSE_ERROR };
        }
    }

    return { ok: true, re: re, im: im };
}

/* ===== 纯函数区结束 ===== */

(function () {
    'use strict';

    var ANIM_MS = 1600;
    var HIGHLIGHT_MS = 900;
    var MAX_N = 12;
    var MAX_M = 24;

    /* 主画布配色 */
    var COLOR_Z1 = '#2563eb';
    var COLOR_Z2 = '#d97706';
    var COLOR_CONJ = '#9333ea';
    var COLOR_PROD = '#16a34a';
    var COLOR_QUOT = '#dc2626';
    var COLOR_ARC = '#f59e0b';
    var COLOR_GRID = '#e2e8f0';
    var COLOR_AXIS = '#64748b';

    var state = {
        z1: { ok: true, re: 3, im: 2 },
        z2: { ok: true, re: 1, im: 1 },
        n: 5,
        m: 6,
        anim: null,
        highlightEnd: 0
    };

    var rafId = null;
    var hoverTargets = [];

    var dom = {};

    /* ---------------- 复数运算 ---------------- */

    function cmul(left, right) {
        return {
            re: left.re * right.re - left.im * right.im,
            im: left.re * right.im + left.im * right.re
        };
    }

    function cdiv(left, right) {
        var denominator = right.re * right.re + right.im * right.im;
        if (Math.abs(denominator) < 1e-12) {
            return null;
        }

        return {
            re: (left.re * right.re + left.im * right.im) / denominator,
            im: (left.im * right.re - left.re * right.im) / denominator
        };
    }

    function cabs(z) {
        return Math.sqrt(z.re * z.re + z.im * z.im);
    }

    /* 辐角（弧度）；零复数没有辐角，返回 null */
    function carg(z) {
        if (Math.abs(z.re) < 1e-12 && Math.abs(z.im) < 1e-12) {
            return null;
        }

        return Math.atan2(z.im, z.re);
    }

    function cpow(z, n) {
        var result = { re: 1, im: 0 };
        var base = z;
        for (var i = 0; i < n; i += 1) {
            result = cmul(result, base);
        }

        return result;
    }

    /* ---------------- 数值格式化 ---------------- */

    /* 保留 4 位小数并去掉多余的 0，用于悬停提示 */
    function fmtValue(value) {
        if (typeof value !== 'number' || !isFinite(value)) {
            return '—';
        }
        var rounded = Math.round(value * 10000) / 10000;

        return String(rounded);
    }

    function fmt4(value) {
        if (typeof value !== 'number' || !isFinite(value)) {
            return '—';
        }

        return value.toFixed(4);
    }

    function fmt2(value) {
        if (typeof value !== 'number' || !isFinite(value)) {
            return '—';
        }

        return value.toFixed(2);
    }

    /* 角度（度）转文本 */
    function fmtAngle(radian) {
        if (radian === null || radian === undefined) {
            return '—';
        }

        return fmt2(radian * 180 / Math.PI);
    }

    /* 把辐角折算到 (-180°, 180°] */
    function normalizeAngle(radian) {
        var value = radian % (2 * Math.PI);
        if (value > Math.PI) {
            value -= 2 * Math.PI;
        }
        if (value <= -Math.PI) {
            value += 2 * Math.PI;
        }

        return value;
    }

    /* 复数的紧凑代数形式，例如 3+2i、1-i、4i、-i、3 */
    function formatComplex(z) {
        if (!z) {
            return '—';
        }
        var re = fmtValue(z.re);
        var im = fmtValue(z.im);
        if (Math.abs(z.im) < 1e-9) {
            return re;
        }
        if (Math.abs(z.re) < 1e-9) {
            if (Math.abs(z.im - 1) < 1e-9) {
                return 'i';
            }
            if (Math.abs(z.im + 1) < 1e-9) {
                return '-i';
            }

            return im + 'i';
        }

        return re + (z.im < 0 ? '-' : '+') + fmtValue(Math.abs(z.im)) + 'i';
    }

    /* 模：能写成整数或根式时写精确值，例如 3+2i → √13 */
    function formatModulus(z) {
        if (!z) {
            return '—';
        }
        var square = z.re * z.re + z.im * z.im;
        var rounded = Math.round(square);
        if (Math.abs(square - rounded) < 1e-9) {
            var root = Math.round(Math.sqrt(rounded));
            if (Math.abs(root * root - rounded) < 1e-9) {
                return String(root);
            }

            return '√' + rounded;
        }

        return fmtValue(Math.sqrt(square));
    }

    /* 说明区里的代数形式：实部 + 虚部，各保留 4 位小数 */
    function algebraicText(z) {
        if (!z) {
            return '—';
        }
        if (Math.abs(z.im) < 5e-5) {
            return fmt4(z.re) + ' + 0.0000i';
        }

        return fmt4(z.re) + (z.im < 0 ? ' - ' : ' + ') + fmt4(Math.abs(z.im)) + 'i';
    }

    var SUPERSCRIPT = { '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
                        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };

    /* 整数转上标，例如 12 → ¹² */
    function sup(value) {
        return String(value).split('').map(function (ch) {
            return SUPERSCRIPT[ch] || ch;
        }).join('');
    }

    /* ---------------- 画布准备 ---------------- */

    /* 按容器宽度与 devicePixelRatio 调整画布尺寸，返回 CSS 像素下的上下文 */
    function fitCanvas(canvas, ratio, minHeight, maxHeight) {
        var box = canvas.parentNode;
        var cssWidth = Math.max(260, Math.floor(box.clientWidth));
        var cssHeight = Math.round(Math.min(maxHeight, Math.max(minHeight, cssWidth * ratio)));
        var dpr = window.devicePixelRatio || 1;
        canvas.style.width = cssWidth + 'px';
        canvas.style.height = cssHeight + 'px';
        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(cssHeight * dpr);
        var ctx = canvas.getContext('2d');
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        return { ctx: ctx, w: cssWidth, h: cssHeight };
    }

    /* 坐标网格与坐标轴 */
    function drawGrid(ctx, w, h, ox, oy, scale, radius) {
        var steps = [0.5, 1, 2, 5, 10, 20, 50, 100, 200];
        var step = steps[steps.length - 1];
        for (var i = 0; i < steps.length; i += 1) {
            if (steps[i] * scale >= 26) {
                step = steps[i];
                break;
            }
        }
        var limit = Math.ceil(radius / step) * step;

        ctx.strokeStyle = COLOR_GRID;
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (var g = -limit; g <= limit + 1e-9; g += step) {
            var gx = ox + g * scale;
            if (gx < 0 || gx > w) {
                continue;
            }
            ctx.moveTo(gx, 0);
            ctx.lineTo(gx, h);
        }
        for (var g2 = -limit; g2 <= limit + 1e-9; g2 += step) {
            var gy = oy - g2 * scale;
            if (gy < 0 || gy > h) {
                continue;
            }
            ctx.moveTo(0, gy);
            ctx.lineTo(w, gy);
        }
        ctx.stroke();

        /* 坐标轴 */
        ctx.strokeStyle = COLOR_AXIS;
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.moveTo(0, oy);
        ctx.lineTo(w, oy);
        ctx.moveTo(ox, h);
        ctx.lineTo(ox, 0);
        ctx.stroke();

        /* 刻度与刻度值 */
        ctx.fillStyle = COLOR_AXIS;
        ctx.font = '11px "Segoe UI", sans-serif';
        ctx.textAlign = 'center';
        for (var t = -limit; t <= limit + 1e-9; t += step) {
            if (Math.abs(t) < 1e-9) {
                continue;
            }
            var tx = ox + t * scale;
            if (tx > 4 && tx < w - 4) {
                ctx.fillText(fmtValue(t), tx, oy + 14);
            }
            var ty = oy - t * scale;
            if (ty > 12 && ty < h - 4) {
                ctx.textAlign = 'right';
                ctx.fillText(fmtValue(t), ox - 6, ty + 4);
                ctx.textAlign = 'center';
            }
        }

        /* 轴名 */
        ctx.font = '12px "Segoe UI", sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('实轴 Re', w - 6, oy - 8);
        ctx.textAlign = 'left';
        ctx.fillText('虚轴 Im', ox + 8, 14);

        /* 原点 */
        ctx.fillStyle = COLOR_AXIS;
        ctx.beginPath();
        ctx.arc(ox, oy, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.textAlign = 'left';
        ctx.fillText('O', ox + 6, oy + 16);

        return step;
    }

    /* 实心圆点 */
    function drawDot(ctx, x, y, color, radius) {
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
    }

    /* 空心圆点 */
    function drawRing(ctx, x, y, color, radius) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.stroke();
    }

    /* 空心方块 */
    function drawSquare(ctx, x, y, color, size) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(x - size, y - size, size * 2, size * 2);
    }

    /* ---------------- 主画布 ---------------- */

    function drawMain() {
        hoverTargets = [];
        var c = fitCanvas(dom.mainCanvas, 0.7, 320, 520);
        var ctx = c.ctx;
        var w = c.w;
        var h = c.h;
        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, w, h);

        var z1 = state.z1.ok ? state.z1 : null;
        var z2 = state.z2.ok ? state.z2 : null;
        var prod = null;
        var quot = null;
        var candidates = [];
        if (z1) {
            candidates.push(z1);
        }
        if (z2) {
            candidates.push(z2);
        }
        if (z1 && z2) {
            prod = cmul(z1, z2);
            candidates.push(prod);
            quot = cdiv(z1, z2);
            if (quot) {
                candidates.push(quot);
            }
        }

        var radius = 2;
        candidates.forEach(function (p) {
            radius = Math.max(radius, cabs(p));
        });
        radius *= 1.5;

        var ox = w / 2;
        var oy = h / 2;
        var scale = (Math.min(w, h) / 2 - 34) / radius;

        function sx(re) {
            return ox + re * scale;
        }

        function sy(im) {
            return oy - im * scale;
        }

        drawGrid(ctx, w, h, ox, oy, scale, radius);

        /* z₁：投影虚线、模半径、辐角弧、点与标签 */
        if (z1) {
            var px = sx(z1.re);
            var py = sy(z1.im);

            ctx.setLineDash([4, 4]);
            ctx.strokeStyle = '#94a3b8';
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(px, oy);
            ctx.moveTo(px, py);
            ctx.lineTo(ox, py);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.fillStyle = COLOR_AXIS;
            ctx.font = '11px "Segoe UI", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('Re = ' + fmtValue(z1.re), px, oy - 8);
            ctx.textAlign = 'right';
            ctx.fillText('Im = ' + fmtValue(z1.im), ox - 6, py - 6);
            ctx.textAlign = 'left';

            ctx.strokeStyle = 'rgba(37,99,235,0.85)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(ox, oy);
            ctx.lineTo(px, py);
            ctx.stroke();

            ctx.fillStyle = COLOR_Z1;
            ctx.font = '12px "Segoe UI", sans-serif';
            ctx.fillText('|z₁| = ' + formatModulus(z1), px + 10, py + 18);

            var theta1 = carg(z1);
            if (theta1 !== null) {
                var arcR = Math.max(20, Math.min(cabs(z1), radius * 0.9) * 0.42);
                ctx.strokeStyle = COLOR_ARC;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(ox, oy, arcR, 0, -theta1, theta1 > 0);
                ctx.stroke();
                var mid = theta1 / 2;
                ctx.fillStyle = '#b45309';
                ctx.font = '12px "Segoe UI", sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(fmtAngle(theta1) + '°',
                    ox + Math.cos(mid) * (arcR + 20),
                    oy - Math.sin(mid) * (arcR + 20));
                ctx.textAlign = 'left';
            }

            drawDot(ctx, px, py, COLOR_Z1, 5.5);
            ctx.fillStyle = COLOR_Z1;
            ctx.font = 'bold 14px "Cambria Math", Georgia, serif';
            ctx.fillText('z₁', px + 9, py - 9);
            hoverTargets.push({
                x: px,
                y: py,
                text: 'z₁ = ' + formatComplex(z1) + '，|z₁| = ' + formatModulus(z1)
                    + '，arg z₁ ≈ ' + fmtAngle(theta1) + '°'
            });

            /* 共轭点 z̄₁ */
            var cpx = sx(z1.re);
            var cpy = sy(-z1.im);
            ctx.setLineDash([6, 4]);
            ctx.strokeStyle = 'rgba(147,51,234,0.85)';
            ctx.lineWidth = 1.6;
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(cpx, cpy);
            ctx.stroke();
            ctx.setLineDash([]);
            drawRing(ctx, cpx, cpy, COLOR_CONJ, 5);
            ctx.fillStyle = COLOR_CONJ;
            ctx.font = 'bold 14px "Cambria Math", Georgia, serif';
            ctx.textAlign = 'right';
            ctx.fillText('z̄₁', cpx - 9, cpy + 16);
            ctx.textAlign = 'left';
            hoverTargets.push({
                x: cpx,
                y: cpy,
                text: 'z̄₁ = ' + formatComplex({ re: z1.re, im: -z1.im })
                    + '，|z̄₁| = ' + formatModulus(z1)
                    + '，arg z̄₁ ≈ ' + fmtAngle(carg({ re: z1.re, im: -z1.im })) + '°'
            });
        }

        /* z₂ */
        if (z2) {
            var qx = sx(z2.re);
            var qy = sy(z2.im);
            drawDot(ctx, qx, qy, COLOR_Z2, 5.5);
            ctx.fillStyle = COLOR_Z2;
            ctx.font = 'bold 14px "Cambria Math", Georgia, serif';
            ctx.fillText('z₂', qx + 9, qy - 9);
            hoverTargets.push({
                x: qx,
                y: qy,
                text: 'z₂ = ' + formatComplex(z2) + '，|z₂| = ' + formatModulus(z2)
                    + '，arg z₂ ≈ ' + fmtAngle(carg(z2)) + '°'
            });
        }

        /* 乘积 z₁z₂（动画期间先淡出，动画结束后再高亮） */
        if (prod) {
            var mx = sx(prod.re);
            var my = sy(prod.im);
            var animating = !!state.anim;
            ctx.globalAlpha = animating ? 0.3 : 1;
            drawDot(ctx, mx, my, COLOR_PROD, 5.5);
            ctx.fillStyle = COLOR_PROD;
            ctx.font = 'bold 14px "Cambria Math", Georgia, serif';
            ctx.fillText('z₁z₂', mx + 9, my - 9);
            ctx.globalAlpha = 1;
            hoverTargets.push({
                x: mx,
                y: my,
                text: 'z₁z₂ = ' + formatComplex(prod) + '，|z₁z₂| = ' + formatModulus(prod)
                    + '，arg(z₁z₂) ≈ ' + fmtAngle(carg(prod)) + '°'
            });

            /* 动画结束后的短暂高亮 */
            var now = performance.now();
            if (!animating && state.highlightEnd > now && prod) {
                var phase = (state.highlightEnd - now) / HIGHLIGHT_MS;
                ctx.strokeStyle = COLOR_PROD;
                ctx.lineWidth = 2;
                for (var ring = 0; ring < 2; ring += 1) {
                    var rr = 8 + 18 * (1 - phase) + ring * 8;
                    ctx.globalAlpha = Math.max(0, phase * 0.9 - ring * 0.25);
                    ctx.beginPath();
                    ctx.arc(mx, my, rr, 0, Math.PI * 2);
                    ctx.stroke();
                }
                ctx.globalAlpha = 1;
            }
        }

        /* 商 z₁/z₂ */
        if (quot) {
            var dx = sx(quot.re);
            var dy = sy(quot.im);
            drawSquare(ctx, dx, dy, COLOR_QUOT, 5);
            ctx.fillStyle = COLOR_QUOT;
            ctx.font = 'bold 14px "Cambria Math", Georgia, serif';
            ctx.fillText('z₁/z₂', dx + 10, dy + 14);
            hoverTargets.push({
                x: dx,
                y: dy,
                text: 'z₁/z₂ = ' + formatComplex(quot) + '，|z₁/z₂| = ' + formatModulus(quot)
                    + '，arg(z₁/z₂) ≈ ' + fmtAngle(carg(quot)) + '°'
            });
        }

        if (state.anim && z1 && z2) {
            drawAnimation(ctx, ox, oy, scale, z1, z2, prod, w, h);
        }
    }

    /* 乘法动画：前半段旋转 arg z₂，后半段伸缩 |z₂| */
    function drawAnimation(ctx, ox, oy, scale, z1, z2, prod, w, h) {
        var progress = state.anim.progress;
        var r1 = cabs(z1);
        var r2 = cabs(z2);
        var theta1 = carg(z1) || 0;
        var phi = carg(z2) || 0;
        var current;
        var status;

        if (progress < 0.5) {
            var u = easeInOut(progress / 0.5);
            var angle = theta1 + u * phi;
            current = { re: r1 * Math.cos(angle), im: r1 * Math.sin(angle) };
            ctx.strokeStyle = 'rgba(249,115,22,0.9)';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(ox, oy, r1 * scale, -theta1, -angle, phi > 0);
            ctx.stroke();
            status = '第 1 步：把 z₁ 旋转 ' + fmtAngle(phi) + '°（arg z₂）';
        } else {
            var u2 = easeInOut((progress - 0.5) / 0.5);
            var angle2 = theta1 + phi;
            var length = r1 * (1 + (r2 - 1) * u2);
            current = { re: length * Math.cos(angle2), im: length * Math.sin(angle2) };
            if (prod) {
                ctx.setLineDash([5, 5]);
                ctx.strokeStyle = 'rgba(22,163,74,0.8)';
                ctx.lineWidth = 1.6;
                ctx.beginPath();
                ctx.moveTo(ox + r1 * Math.cos(angle2) * scale, oy - r1 * Math.sin(angle2) * scale);
                ctx.lineTo(ox + prod.re * scale, oy - prod.im * scale);
                ctx.stroke();
                ctx.setLineDash([]);
            }
            status = '第 2 步：再伸缩 ' + fmtValue(r2) + ' 倍（|z₂|）';
        }
        ctx.textAlign = 'left';

        ctx.strokeStyle = '#f97316';
        ctx.lineWidth = 2.6;
        ctx.beginPath();
        ctx.moveTo(ox, oy);
        ctx.lineTo(ox + current.re * scale, oy - current.im * scale);
        ctx.stroke();
        drawDot(ctx, ox + current.re * scale, oy - current.im * scale, '#f97316', 6);
        ctx.fillStyle = '#c2410c';
        ctx.font = '12px "Segoe UI", sans-serif';
        ctx.fillText('当前：' + formatComplex(current),
            ox + current.re * scale + 10, oy - current.im * scale + 20);

        /* 阶段说明固定放在画布左下角，避免与图上文字打架 */
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        ctx.fillRect(8, h - 30, 258, 22);
        ctx.fillStyle = '#c2410c';
        ctx.font = '12px "Segoe UI", sans-serif';
        ctx.fillText(status, 14, h - 14);
    }

    /* 缓入缓出 */
    function easeInOut(t) {
        if (t < 0) {
            return 0;
        }
        if (t > 1) {
            return 1;
        }
        if (t < 0.5) {
            return 2 * t * t;
        }

        return 1 - Math.pow(-2 * t + 2, 2) / 2;
    }

    /* ---------------- 幂的轨迹 ---------------- */

    function drawPowers() {
        var c = fitCanvas(dom.powCanvas, 0.55, 240, 380);
        var ctx = c.ctx;
        var w = c.w;
        var h = c.h;
        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, w, h);

        var z1 = state.z1.ok ? state.z1 : null;
        if (!z1) {
            ctx.fillStyle = COLOR_AXIS;
            ctx.font = '13px "Segoe UI", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('请先输入有效的 z₁', w / 2, h / 2);
            ctx.textAlign = 'left';

            return;
        }

        var n = state.n;
        var points = [];
        var current = { re: z1.re, im: z1.im };
        for (var k = 1; k <= n; k += 1) {
            points.push(current);
            current = cmul(current, z1);
        }

        var maxR = 0;
        points.forEach(function (p) {
            maxR = Math.max(maxR, cabs(p));
        });
        var radius = Math.max(1.2, maxR * 1.15);
        var ox = w / 2;
        var oy = h / 2;
        var scale = (Math.min(w, h) / 2 - 34) / radius;

        drawGrid(ctx, w, h, ox, oy, scale, radius);

        /* 连线逐段变淡 */
        for (var i = 0; i < points.length - 1; i += 1) {
            var alpha = points.length > 2
                ? 0.85 - 0.6 * (i / (points.length - 2))
                : 0.85;
            ctx.strokeStyle = 'rgba(37,99,235,' + alpha.toFixed(3) + ')';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(ox + points[i].re * scale, oy - points[i].im * scale);
            ctx.lineTo(ox + points[i + 1].re * scale, oy - points[i + 1].im * scale);
            ctx.stroke();
        }

        /* 幂次点 */
        for (var j = 0; j < points.length; j += 1) {
            var x = ox + points[j].re * scale;
            var y = oy - points[j].im * scale;
            var isLast = (j === points.length - 1);
            var r = 4 + 1.2 * j;
            if (isLast) {
                drawRing(ctx, x, y, COLOR_PROD, r + 2);
                drawDot(ctx, x, y, COLOR_PROD, r);
            } else {
                drawDot(ctx, x, y, COLOR_Z1, r);
            }
            ctx.fillStyle = isLast ? COLOR_PROD : COLOR_Z1;
            ctx.font = (isLast ? 'bold ' : '') + '13px "Cambria Math", Georgia, serif';
            /* 标签沿「原点 → 该点」的方向外推，幂次点密集时也不会互相压住 */
            var distance = cabs(points[j]);
            var ux = distance > 1e-9 ? points[j].re / distance : 0;
            var uy = distance > 1e-9 ? points[j].im / distance : -1;
            ctx.textAlign = 'center';
            ctx.fillText('z' + sup(j + 1), x + ux * (r + 11), y - uy * (r + 11) + 4);
        }
        ctx.textAlign = 'left';
    }

    /* ---------------- 单位根 ---------------- */

    /* m ∈ {1,2,3,4,6} 时根可以写成精确值 */
    var ROOT_EXACT = {
        1: ['1'],
        2: ['1', '-1'],
        3: ['1', '-1/2+√3/2 i', '-1/2-√3/2 i'],
        4: ['1', 'i', '-1', '-i'],
        6: ['1', '1/2+√3/2 i', '-1/2+√3/2 i', '-1', '-1/2-√3/2 i', '1/2-√3/2 i']
    };

    function drawRoots() {
        var c = fitCanvas(dom.rootCanvas, 0.8, 240, 340);
        var ctx = c.ctx;
        var w = c.w;
        var h = c.h;
        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, w, h);

        var m = state.m;
        var ox = w / 2;
        var oy = h / 2;
        var scale = (Math.min(w, h) / 2 - 40);

        /* 单位圆 */
        ctx.strokeStyle = COLOR_AXIS;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.arc(ox, oy, scale, 0, Math.PI * 2);
        ctx.stroke();

        /* 正实轴参考线 */
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(ox - scale - 10, oy);
        ctx.lineTo(ox + scale + 10, oy);
        ctx.stroke();
        ctx.setLineDash([]);

        var exact = ROOT_EXACT[m] || null;
        var points = [];
        for (var k = 0; k < m; k += 1) {
            var angle = 2 * Math.PI * k / m;
            points.push({ x: ox + Math.cos(angle) * scale, y: oy - Math.sin(angle) * scale });
        }

        /* 正多边形 */
        if (m >= 2) {
            ctx.strokeStyle = 'rgba(37,99,235,0.45)';
            ctx.lineWidth = 1.4;
            ctx.beginPath();
            points.forEach(function (p, index) {
                if (index === 0) {
                    ctx.moveTo(p.x, p.y);
                } else {
                    ctx.lineTo(p.x, p.y);
                }
            });
            ctx.closePath();
            ctx.stroke();
        }

        /* 辐角参考线与根 */
        for (var j = 0; j < m; j += 1) {
            var p2 = points[j];
            ctx.strokeStyle = 'rgba(148,163,184,0.75)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(ox, oy);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
            drawDot(ctx, p2.x, p2.y, COLOR_Z1, 5);

            var label = exact ? exact[j] : (fmt2(360 * j / m) + '°');
            ctx.fillStyle = COLOR_Z1;
            ctx.font = '12px "Cambria Math", Georgia, serif';
            ctx.textAlign = 'center';
            ctx.fillText(label, p2.x + Math.cos(2 * Math.PI * j / m) * 26,
                p2.y - Math.sin(2 * Math.PI * j / m) * 26 + 4);
        }
        ctx.textAlign = 'left';

        ctx.fillStyle = COLOR_AXIS;
        ctx.font = '12px "Segoe UI", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('|z| = 1，arg z = ' + fmt2(360 / m) + '°k', w / 2, h - 8);
        ctx.textAlign = 'left';
    }

    /* ---------------- 说明区 ---------------- */

    function addRow(table, name, algebra, modulus, angle) {
        var row = document.createElement('tr');
        var th = document.createElement('th');
        th.textContent = name;
        var td1 = document.createElement('td');
        td1.textContent = algebra;
        var td2 = document.createElement('td');
        td2.textContent = modulus;
        var td3 = document.createElement('td');
        td3.textContent = angle;
        row.appendChild(th);
        row.appendChild(td1);
        row.appendChild(td2);
        row.appendChild(td3);
        table.appendChild(row);
    }

    function updateTable() {
        var table = dom.infoTable;
        table.innerHTML = '';
        var head = document.createElement('tr');
        var h1 = document.createElement('th');
        h1.textContent = '复数';
        var h2 = document.createElement('th');
        h2.textContent = '代数形式';
        var h3 = document.createElement('th');
        h3.textContent = '模';
        var h4 = document.createElement('th');
        h4.textContent = '辐角(°)';
        head.appendChild(h1);
        head.appendChild(h2);
        head.appendChild(h3);
        head.appendChild(h4);
        table.appendChild(head);

        var z1 = state.z1.ok ? state.z1 : null;
        var z2 = state.z2.ok ? state.z2 : null;
        var prod = (z1 && z2) ? cmul(z1, z2) : null;
        var quot = (z1 && z2) ? cdiv(z1, z2) : null;

        function fill(name, value, invalidText) {
            if (!value) {
                addRow(table, name, invalidText, '—', '—');

                return;
            }
            addRow(table, name, algebraicText(value), fmt4(cabs(value)), fmtAngle(carg(value)));
        }

        fill('z₁', z1, '输入无效');
        fill('z₂', z2, '输入无效');
        fill('z₁z₂', prod, '输入无效');
        if (z1 && z2 && !quot) {
            addRow(table, 'z₁/z₂', '不可除（除数为零）', '不可除（除数为零）', '不可除（除数为零）');
        } else {
            fill('z₁/z₂', quot, '输入无效');
        }

        /* 一小段中文说明 */
        var summary = '';
        if (z1 && z2) {
            var arg1 = carg(z1);
            var arg2 = carg(z2);
            summary = '乘法：|z₁z₂| = |z₁|·|z₂| = ' + fmt4(cabs(z1)) + ' × ' + fmt4(cabs(z2))
                + ' = ' + fmt4(cabs(prod)) + '；arg(z₁z₂) = arg z₁ + arg z₂ = '
                + fmtAngle(arg1) + '° + ' + fmtAngle(arg2) + '° = '
                + fmtAngle(carg(prod)) + '°。';
            if (quot) {
                summary += ' 除法：|z₁/z₂| = |z₁|/|z₂| = ' + fmt4(cabs(quot))
                    + '；arg(z₁/z₂) = arg z₁ − arg z₂ = ' + fmtAngle(carg(quot)) + '°。';
            } else {
                summary += ' 除法：z₂ = 0，除数为零，z₁/z₂ 不存在。';
            }
        } else {
            summary = '请输入有效的 z₁ 与 z₂，这里会给出乘积与商的模、辐角关系。';
        }
        dom.summary.textContent = summary;

        var sideNote = '说明：代数形式按「实部 + 虚部 i」书写，实部、虚部与模均保留 4 位小数，'
            + '辐角保留 2 位小数；本页为浮点近似显示，考试判分仍按服务端精确值进行。';
        dom.sideNote.textContent = sideNote;
    }

    /* ---------------- 幂与单位根的说明文字 ---------------- */

    function updatePowerNote() {
        var z1 = state.z1.ok ? state.z1 : null;
        if (!z1) {
            dom.powNote.textContent = '请输入有效的 z₁ 后查看幂的轨迹。';

            return;
        }
        var r = cabs(z1);
        var theta = carg(z1);
        var last = cpow(z1, state.n);
        var text = '从 z₁ 出发连乘 n = ' + state.n + ' 次：|z₁| = ' + fmtValue(r)
            + ' → |z₁' + sup(state.n) + '| = ' + fmtValue(Math.pow(r, state.n))
            + '，辐角由 ' + fmtAngle(theta) + '° 旋转为 '
            + fmtAngle(normalizeAngle((theta || 0) * state.n)) + '°。';
        if (cabs(last) > 0 && Math.abs(r) > 1e-9) {
            text += ' 这正是棣莫弗公式 zⁿ = rⁿ(cos nθ + i sin nθ)。';
        }
        dom.powNote.textContent = text;
    }

    function updateRootNote() {
        var m = state.m;
        var text = 'm = ' + m + ' 时，单位圆上共有 ' + m + ' 个 m 次单位根，相邻两根的辐角相差 '
            + fmt2(360 / m) + '°。';
        if (ROOT_EXACT[m]) {
            text += ' 这几个根可以写成精确值：' + ROOT_EXACT[m].join('、') + '。';
        } else {
            text += ' 这里只标出各根的辐角。';
        }
        dom.rootNote.textContent = text;
    }

    /* ---------------- 输入处理 ---------------- */

    function setError(node, message) {
        node.textContent = message || '';
    }

    function readComplexInput(input, errorNode) {
        var result = parseComplex(input.value);
        if (!result.ok) {
            setError(errorNode, result.message);

            return null;
        }
        setError(errorNode, '');

        return { ok: true, re: result.re, im: result.im };
    }

    function readCountInput(input, errorNode, maxValue) {
        var text = input.value.trim();
        if (!/^\d+$/.test(text)) {
            setError(errorNode, '请输入正整数（1～' + maxValue + '）');

            return null;
        }
        var value = parseInt(text, 10);
        if (value < 1 || value > maxValue) {
            setError(errorNode, '请输入正整数（1～' + maxValue + '）');

            return null;
        }
        setError(errorNode, '');

        return value;
    }

    function refresh() {
        var z1 = readComplexInput(dom.z1Input, dom.z1Error);
        if (z1) {
            state.z1 = z1;
        } else {
            state.z1 = { ok: false, message: PLANE_PARSE_ERROR };
        }

        var z2 = readComplexInput(dom.z2Input, dom.z2Error);
        if (z2) {
            state.z2 = z2;
        } else {
            state.z2 = { ok: false, message: PLANE_PARSE_ERROR };
        }

        var n = readCountInput(dom.nInput, dom.nError, MAX_N);
        if (n !== null) {
            state.n = n;
        }

        var m = readCountInput(dom.mInput, dom.mError, MAX_M);
        if (m !== null) {
            state.m = m;
        }

        /* 动画进行中输入变化：立即回到静态画面 */
        if (state.anim) {
            state.anim = null;
            state.highlightEnd = 0;
        }

        drawMain();
        drawPowers();
        drawRoots();
        updateTable();
        updatePowerNote();
        updateRootNote();
        updateAnimNote();
    }

    function updateAnimNote() {
        if (!dom.animCheck.checked) {
            dom.animNote.textContent = '勾选「演示乘法几何」后点击「▶ 播放」，'
                + '用动画演示复数乘法 = 旋转 arg z₂ + 伸缩 |z₂|。';

            return;
        }
        if (!state.z1.ok || !state.z2.ok) {
            dom.animNote.textContent = '请先输入有效的 z₁ 与 z₂。';

            return;
        }
        var z1 = state.z1;
        var z2 = state.z2;
        dom.animNote.textContent = '动画：把 z₁ 旋转 ' + fmtAngle(carg(z2)) + '°（arg z₂），'
            + '再伸缩 ' + fmtValue(cabs(z2)) + ' 倍（|z₂|），终点即 z₁z₂ = '
            + formatComplex(cmul(z1, z2)) + '。';
    }

    /* ---------------- 动画循环 ---------------- */

    function ensureTick() {
        if (rafId === null) {
            rafId = window.requestAnimationFrame(tick);
        }
    }

    function tick() {
        rafId = null;
        var now = performance.now();
        if (state.anim) {
            state.anim.progress = Math.min(1, (now - state.anim.start) / ANIM_MS);
            drawMain();
            if (state.anim.progress < 1) {
                ensureTick();
            } else {
                state.anim = null;
                state.highlightEnd = now + HIGHLIGHT_MS;
                ensureTick();
            }

            return;
        }
        if (state.highlightEnd > now) {
            drawMain();
            ensureTick();
        } else {
            state.highlightEnd = 0;
        }
    }

    function playAnimation() {
        if (!dom.animCheck.checked) {
            dom.animNote.textContent = '请先勾选「演示乘法几何」再播放。';

            return;
        }
        if (!state.z1.ok || !state.z2.ok) {
            dom.animNote.textContent = '请先输入有效的 z₁ 与 z₂。';

            return;
        }
        state.highlightEnd = 0;
        state.anim = { start: performance.now(), progress: 0 };
        ensureTick();
    }

    /* ---------------- 悬停提示 ---------------- */

    function bindHover(canvas, tip) {
        canvas.addEventListener('mousemove', function (event) {
            var rect = canvas.getBoundingClientRect();
            var mx = event.clientX - rect.left;
            var my = event.clientY - rect.top;
            var best = null;
            var bestDistance = 16;
            hoverTargets.forEach(function (target) {
                var distance = Math.hypot(target.x - mx, target.y - my);
                if (distance < bestDistance) {
                    bestDistance = distance;
                    best = target;
                }
            });
            if (!best) {
                tip.classList.remove('show');

                return;
            }
            tip.textContent = best.text;
            tip.style.left = Math.max(0, Math.min(mx + 12, canvas.clientWidth - tip.offsetWidth - 4)) + 'px';
            tip.style.top = Math.max(0, my - 32) + 'px';
            tip.classList.add('show');
        });
        canvas.addEventListener('mouseleave', function () {
            tip.classList.remove('show');
        });
    }

    /* ---------------- 初始化 ---------------- */

    function init() {
        dom.mainCanvas = document.getElementById('main-canvas');
        dom.powCanvas = document.getElementById('pow-canvas');
        dom.rootCanvas = document.getElementById('root-canvas');
        dom.z1Input = document.getElementById('z1-input');
        dom.z2Input = document.getElementById('z2-input');
        dom.nInput = document.getElementById('n-input');
        dom.mInput = document.getElementById('m-input');
        dom.z1Error = document.getElementById('z1-error');
        dom.z2Error = document.getElementById('z2-error');
        dom.nError = document.getElementById('n-error');
        dom.mError = document.getElementById('m-error');
        dom.infoTable = document.getElementById('info-table');
        dom.summary = document.getElementById('summary');
        dom.sideNote = document.getElementById('side-note');
        dom.powNote = document.getElementById('pow-note');
        dom.rootNote = document.getElementById('root-note');
        dom.animNote = document.getElementById('anim-note');
        dom.animCheck = document.getElementById('anim-check');
        dom.btnPlay = document.getElementById('btn-play');
        dom.tip = document.getElementById('main-tip');

        dom.z1Input.addEventListener('input', refresh);
        dom.z2Input.addEventListener('input', refresh);
        dom.nInput.addEventListener('input', refresh);
        dom.mInput.addEventListener('input', refresh);
        dom.animCheck.addEventListener('change', updateAnimNote);
        dom.btnPlay.addEventListener('click', playAnimation);
        bindHover(dom.mainCanvas, dom.tip);

        var resizeTimer = null;
        window.addEventListener('resize', function () {
            if (resizeTimer !== null) {
                window.clearTimeout(resizeTimer);
            }
            resizeTimer = window.setTimeout(function () {
                resizeTimer = null;
                drawMain();
                drawPowers();
                drawRoots();
            }, 120);
        });

        refresh();
    }

    /* 导出纯函数，便于离线自检脚本单独抽取测试 */
    if (typeof window !== 'undefined') {
        window.PlaneLab = window.PlaneLab || {};
        window.PlaneLab.parseComplex = parseComplex;
    }

    if (typeof document !== 'undefined') {
        init();
    }
}());
