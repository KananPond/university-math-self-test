/* ==========================================================================
 * 线性代数考试模拟系统 · 图形化矩阵组件
 * 作者：ZCode（GLM）    日期：2026-10-02    版本：1.0
 *
 * 说明：
 * 1. MatrixView：把矩阵规格画到 canvas 上——方括号 / 行列式竖线 /
 *    增广分隔线，按元素正负与大小着色（热力图），悬停显示坐标与数值，
 *    分数按上下结构排版。
 * 2. MatrixEditor：固定形状的矩阵作答表格，右侧同步画出图形预览。
 * 3. 零依赖，纯原生实现，支持高分屏（devicePixelRatio）。
 * ========================================================================== */

(function () {
    'use strict';

    var FONT = '16px "Cambria Math", "Times New Roman", Georgia, serif';
    var SMALL_FONT = '13px "Cambria Math", "Times New Roman", Georgia, serif';
    var LABEL_FONT = 'italic 17px "Cambria Math", "Times New Roman", Georgia, serif';
    var ROW_H = 26;
    var PAD_X = 12;
    var GAP_X = 10;
    var BRACKET_W = 10;
    var CAP = 7;

    /* ---------------- 元素解析 ---------------- */

    /* 解析单个元素：整数、小数、分数（"3/2"）或符号（"a"） */
    function parseEntry(raw) {
        var text = String(raw === undefined || raw === null ? '' : raw).trim();
        if (text === '') {
            return { kind: 'empty', text: '·', value: 0 };
        }
        if (/^[+-]?\d+$/.test(text)) {
            return { kind: 'num', value: parseInt(text, 10), text: text };
        }
        if (/^[+-]?(\d+\.\d*|\.\d+|\d+)$/.test(text)) {
            return { kind: 'num', value: parseFloat(text), text: text };
        }
        var frac = text.match(/^([+-]?\d+)\s*\/\s*(\d+)$/);
        if (frac) {
            var den = parseInt(frac[2], 10);
            if (den !== 0) {
                return { kind: 'frac', num: parseInt(frac[1], 10),
                         den: den, text: text };
            }
        }
        return { kind: 'sym', text: text, value: NaN };
    }

    /* 数值着色：正蓝负红零灰，强度随绝对值增大 */
    function cellColor(entry, maxAbs) {
        if (entry.kind === 'sym' || entry.kind === 'empty') {
            return { fill: 'rgba(100,116,139,0.08)', text: '#475569' };
        }
        var magnitude = Math.min(1, Math.abs(entry.value) / (maxAbs || 1));
        var alpha = 0.08 + 0.26 * magnitude;
        if (entry.value > 0) {
            return { fill: 'rgba(37,99,235,' + alpha + ')', text: '#1e3a8a' };
        }
        if (entry.value < 0) {
            return { fill: 'rgba(220,38,38,' + alpha + ')', text: '#7f1d1d' };
        }

        return { fill: 'rgba(100,116,139,0.10)', text: '#475569' };
    }

    function makeRenderer() {
        var offscreen = document.createElement('canvas');
        var context = offscreen.getContext('2d');

        return function measure(text, font) {
            context.font = font;

            return context.measureText(text).width;
        };
    }

    /* ---------------- 绘图 ---------------- */

    /*
     * render(container, spec, options)
     * spec: { label, style: 'matrix'|'det'|'aug', data }
     * options: { colorize: true, fontSize }
     * 返回 canvas 节点（包在 .mat-wrap 里，悬停显示提示）。
     */
    function render(container, spec, options) {
        options = options || {};
        var data = (spec && spec.data) || [];
        var style = (spec && spec.style) || 'matrix';
        var label = (spec && spec.label) || '';
        var measure = makeRenderer();

        var entries = data.map(function (row) {
            return row.map(parseEntry);
        });
        var rows = entries.length;
        var cols = rows ? entries[0].length : 0;
        var maxAbs = 0;
        entries.forEach(function (row) {
            row.forEach(function (entry) {
                if (!isNaN(entry.value)) {
                    maxAbs = Math.max(maxAbs, Math.abs(entry.value));
                }
            });
        });

        /* 计算列宽与行高（分数占两行） */
        var cellW = [];
        var col, row, i;
        for (col = 0; col < cols; col += 1) {
            var width = 0;
            for (row = 0; row < rows; row += 1) {
                var entry = entries[row][col];
                var text = entry.kind === 'frac'
                    ? String(Math.abs(entry.num)) : entry.text;
                width = Math.max(width, measure(text, FONT));
            }
            cellW.push(Math.ceil(width) + PAD_X * 2);
        }
        var hasFraction = entries.some(function (rowEntry) {
            return rowEntry.some(function (entry) {
                return entry.kind === 'frac';
            });
        });
        var contentH = rows * ROW_H + (hasFraction ? 2 : 0);

        var labelW = label ? Math.ceil(measure(label + ' =', LABEL_FONT)) + 8 : 0;
        var bracketW = style === 'det' ? BRACKET_W - 2 : BRACKET_W;
        var cssW = labelW + bracketW * 2 + GAP_X * (cols - 1)
            + cellW.reduce(function (sum, w) { return sum + w; }, 0) + 4;
        var cssH = contentH + 8;

        /* 组装画布（高分屏适配） */
        var wrap = document.createElement('span');
        wrap.className = 'mat-wrap';
        var canvas = document.createElement('canvas');
        var dpr = window.devicePixelRatio || 1;
        canvas.width = Math.max(1, Math.round(cssW * dpr));
        canvas.height = Math.max(1, Math.round(cssH * dpr));
        canvas.style.width = cssW + 'px';
        canvas.style.height = cssH + 'px';
        canvas.className = 'mat-canvas';
        wrap.appendChild(canvas);
        var tip = document.createElement('span');
        tip.className = 'mat-tip';
        tip.hidden = true;
        wrap.appendChild(tip);

        var contentX = labelW + bracketW;
        var contentY = 4;

        function cellRect(r, c) {
            var x = contentX;
            for (var k = 0; k < c; k += 1) {
                x += cellW[k] + GAP_X;
            }

            return { x: x, y: contentY + r * ROW_H + (hasFraction ? 1 : 0),
                     w: cellW[c], h: ROW_H };
        }

        function draw(highlight) {
            var ctx = canvas.getContext('2d');
            if (canvas.width !== Math.round(cssW * dpr)) {
                dpr = window.devicePixelRatio || 1;
                canvas.width = Math.max(1, Math.round(cssW * dpr));
                canvas.height = Math.max(1, Math.round(cssH * dpr));
            }
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            ctx.clearRect(0, 0, cssW, cssH);

            /* 标签 */
            if (label) {
                ctx.font = LABEL_FONT;
                ctx.fillStyle = '#0f172a';
                ctx.textBaseline = 'middle';
                ctx.textAlign = 'right';
                ctx.fillText(label + ' =', labelW - 8, cssH / 2);
            }

            /* 单元格底色与文字 */
            for (row = 0; row < rows; row += 1) {
                for (col = 0; col < cols; col += 1) {
                    var rect = cellRect(row, col);
                    var entry = entries[row][col];
                    var colors = options.colorize === false
                        ? { fill: 'rgba(148,163,184,0.06)', text: '#0f172a' }
                        : cellColor(entry, maxAbs);

                    ctx.fillStyle = colors.fill;
                    roundRect(ctx, rect.x + 1, rect.y + 1,
                              rect.w - 2, rect.h - 2, 4);
                    ctx.fill();

                    ctx.fillStyle = colors.text;
                    ctx.textAlign = 'center';
                    if (entry.kind === 'frac') {
                        ctx.font = SMALL_FONT;
                        var barY = rect.y + rect.h / 2;
                        ctx.fillText(String(Math.abs(entry.num)),
                                     rect.x + rect.w / 2, barY - 7);
                        ctx.fillText(String(entry.den),
                                     rect.x + rect.w / 2, barY + 8);
                        var barW = Math.min(rect.w - 10,
                                            Math.max(measure(
                                                String(Math.abs(entry.num)),
                                                SMALL_FONT),
                                                measure(String(entry.den),
                                                        SMALL_FONT)) + 6);
                        ctx.strokeStyle = colors.text;
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(rect.x + rect.w / 2 - barW / 2, barY);
                        ctx.lineTo(rect.x + rect.w / 2 + barW / 2, barY);
                        ctx.stroke();
                        if (entry.num < 0) {
                            ctx.fillText('−',
                                         rect.x + rect.w / 2 - barW / 2 - 7,
                                         barY - 7);
                        }
                    } else {
                        ctx.font = FONT;
                        ctx.fillText(entry.text,
                                     rect.x + rect.w / 2,
                                     rect.y + rect.h / 2 + 1);
                    }
                }
            }

            /* 增广矩阵分隔虚线（最后一列之前） */
            if (style === 'aug' && cols >= 2) {
                var lineX = cellRect(0, cols - 1).x - GAP_X / 2;
                ctx.strokeStyle = '#0f172a';
                ctx.lineWidth = 1.4;
                ctx.setLineDash([4, 3]);
                ctx.beginPath();
                ctx.moveTo(lineX, contentY + 1);
                ctx.lineTo(lineX, contentY + contentH - 5);
                ctx.stroke();
                ctx.setLineDash([]);
            }

            /* 括号或行列式竖线 */
            var top = contentY;
            var bottom = contentY + rows * ROW_H + (hasFraction ? 2 : 0);
            ctx.strokeStyle = '#0f172a';
            ctx.lineWidth = 2;
            ctx.beginPath();
            if (style === 'det') {
                ctx.moveTo(contentX - 4, top);
                ctx.lineTo(contentX - 4, bottom);
                var rightX = cellRect(0, cols - 1).x + cellW[cols - 1] + 4;
                ctx.moveTo(rightX, top);
                ctx.lineTo(rightX, bottom);
            } else {
                drawBracket(ctx, contentX - 4, top, bottom, 1);
                var endX = cellRect(0, cols - 1).x + cellW[cols - 1] + 4;
                drawBracket(ctx, endX, top, bottom, -1);
            }
            ctx.stroke();

            /* 悬停高亮 */
            if (highlight && highlight.r >= 0) {
                var hi = cellRect(highlight.r, highlight.c);
                ctx.strokeStyle = '#2563eb';
                ctx.lineWidth = 2;
                roundRect(ctx, hi.x + 1, hi.y + 1, hi.w - 2, hi.h - 2, 4);
                ctx.stroke();
            }
        }

        /* 悬停提示：第 r 行第 c 列的值 */
        canvas.addEventListener('mousemove', function (event) {
            var bounds = canvas.getBoundingClientRect();
            var x = event.clientX - bounds.left;
            var y = event.clientY - bounds.top;
            var found = null;
            for (row = 0; row < rows && !found; row += 1) {
                for (col = 0; col < cols && !found; col += 1) {
                    var rect = cellRect(row, col);
                    if (x >= rect.x && x <= rect.x + rect.w
                            && y >= rect.y && y <= rect.y + rect.h) {
                        found = { r: row, c: col };
                    }
                }
            }
            if (found) {
                var entry = entries[found.r][found.c];
                tip.textContent = '第 ' + (found.r + 1) + ' 行 第 '
                    + (found.c + 1) + ' 列：' + entry.text;
                tip.hidden = false;
                draw(found);
            } else {
                tip.hidden = true;
                draw(null);
            }
        });
        canvas.addEventListener('mouseleave', function () {
            tip.hidden = true;
            draw(null);
        });

        draw(null);

        if (container && container.appendChild) {
            container.appendChild(wrap);
        }

        return canvas;
    }

    function drawBracket(ctx, x, top, bottom, direction) {
        ctx.moveTo(x, top);
        ctx.lineTo(x, bottom);
        ctx.moveTo(x, top);
        ctx.lineTo(x + direction * CAP, top);
        ctx.moveTo(x, bottom);
        ctx.lineTo(x + direction * CAP, bottom);
    }

    function roundRect(ctx, x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
    }

    /* ---------------- 作答组件 ---------------- */

    /*
     * mount(container, spec, onChange)
     * spec: { rows, cols, value?: [[str]] }
     * 返回 { get, inputs }；每次修改调用 onChange()。
     */
    function mount(container, spec, onChange) {
        var rows = spec.rows;
        var cols = spec.cols;
        var value = spec.value || [];
        var table = document.createElement('table');
        table.className = 'mat-editor';
        var body = document.createElement('tbody');
        var inputs = [];

        var r, c;
        for (r = 0; r < rows; r += 1) {
            var tr = document.createElement('tr');
            var rowInputs = [];
            for (c = 0; c < cols; c += 1) {
                var td = document.createElement('td');
                var input = document.createElement('input');
                input.type = 'text';
                input.className = 'mat-cell';
                input.autocomplete = 'off';
                input.spellcheck = false;
                input.placeholder = '0';
                if (value[r] && value[r][c] !== undefined
                        && value[r][c] !== null) {
                    input.value = String(value[r][c]);
                }
                input.addEventListener('input', function () {
                    refresh(true);
                });
                td.appendChild(input);
                tr.appendChild(td);
                rowInputs.push(input);
            }
            body.appendChild(tr);
            inputs.push(rowInputs);
        }
        table.appendChild(body);

        var layout = document.createElement('div');
        layout.className = 'mat-answer';
        var inputArea = document.createElement('div');
        inputArea.className = 'mat-answer-input';
        var inputTitle = document.createElement('p');
        inputTitle.className = 'mat-answer-title';
        inputTitle.textContent = '作答矩阵（' + rows + ' 行 × ' + cols
            + ' 列，支持 3/2、0.75、2）';
        inputArea.appendChild(inputTitle);
        inputArea.appendChild(table);

        var previewArea = document.createElement('div');
        previewArea.className = 'mat-answer-preview';
        var previewTitle = document.createElement('p');
        previewTitle.className = 'mat-answer-title';
        previewTitle.textContent = '图形预览';
        previewArea.appendChild(previewTitle);
        var previewBox = document.createElement('div');
        previewBox.className = 'mat-preview-box';
        previewArea.appendChild(previewBox);

        layout.appendChild(inputArea);
        layout.appendChild(previewArea);
        container.appendChild(layout);

        function currentData() {
            return inputs.map(function (row) {
                return row.map(function (input) {
                    return input.value.trim();
                });
            });
        }

        /* redraw：是否同时通知 onChange（挂载时只画预览，不触发） */
        function refresh(notify) {
            previewBox.innerHTML = '';
            render(previewBox, { data: currentData(), style: 'matrix' });
            if (notify && onChange) {
                onChange();
            }
        }

        refresh(false);

        return {
            get: function () {
                return { rows: rows, cols: cols, data: currentData() };
            },
            inputs: inputs
        };
    }

    window.MatrixView = {
        render: render,
        mount: mount,
        parseEntry: parseEntry
    };
}());
