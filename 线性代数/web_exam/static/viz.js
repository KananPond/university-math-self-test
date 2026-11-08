/* ==========================================================================
 * 矩阵可视化实验台 · 交互逻辑
 * 作者：ZCode（GLM）    日期：2026-10-02    版本：1.0
 *
 * 说明：
 * 1. 输入任意 1×1 ～ 4×4 矩阵，实时给出热力图、行列式、迹、秩、
 *    逆矩阵（可逆时）与特征值（2×2、3×3 给出精确数值思路下的实根）。
 * 2. 2×2 矩阵额外提供线性变换动画：坐标网格被矩阵变形，
 *    显示 î、ĵ 的像、单位正方形变成的平行四边形（面积 = |det|）
 *    以及实特征方向。
 * 3. 本页纯浏览器计算（浮点），仅用于直观理解，考试判分仍在服务端。
 * ========================================================================== */

(function () {
    'use strict';

    var MAX_SIZE = 4;
    var rows = 2;
    var cols = 2;
    var inputs = [];
    var animateHandle = null;

    /* ---------------- 编辑器 ---------------- */

    function buildEditor() {
        var host = document.getElementById('editor');
        host.innerHTML = '';
        inputs = [];
        var table = document.createElement('table');
        table.className = 'mat-editor';
        var body = document.createElement('tbody');
        for (var r = 0; r < rows; r += 1) {
            var tr = document.createElement('tr');
            var rowInputs = [];
            for (var c = 0; c < cols; c += 1) {
                var td = document.createElement('td');
                var input = document.createElement('input');
                input.type = 'text';
                input.className = 'mat-cell';
                input.autocomplete = 'off';
                input.spellcheck = false;
                input.value = defaultValue(r, c);
                input.addEventListener('input', refresh);
                td.appendChild(input);
                tr.appendChild(td);
                rowInputs.push(input);
            }
            body.appendChild(tr);
            inputs.push(rowInputs);
        }
        table.appendChild(body);
        host.appendChild(table);
    }

    function defaultValue(r, c) {
        return r === c ? '1' : '0';
    }

    function readMatrix() {
        var data = [];
        for (var r = 0; r < rows; r += 1) {
            var row = [];
            for (var c = 0; c < cols; c += 1) {
                var text = inputs[r][c].value.trim();
                var value = parseFloat(text);
                if (text.indexOf('/') >= 0) {
                    var parts = text.split('/');
                    var top = parseFloat(parts[0]);
                    var bottom = parseFloat(parts[1]);
                    value = bottom ? top / bottom : NaN;
                }
                row.push(isNaN(value) ? 0 : value);
            }
            data.push(row);
        }

        return data;
    }

    /* ---------------- 数值工具 ---------------- */

    function det2(a) {
        return a[0][0] * a[1][1] - a[0][1] * a[1][0];
    }

    function detN(m) {
        var n = m.length;
        if (n === 1) {
            return m[0][0];
        }
        if (n === 2) {
            return det2(m);
        }
        var total = 0;
        for (var j = 0; j < n; j += 1) {
            var minor = m.slice(1).map(function (row) {
                return row.filter(function (_, k) { return k !== j; });
            });
            total += (j % 2 ? -1 : 1) * m[0][j] * detN(minor);
        }

        return total;
    }

    function rankN(m) {
        var matrix = m.map(function (row) { return row.slice(); });
        var n = matrix[0].length;
        var rank = 0;
        for (var col = 0; col < n && rank < matrix.length; col += 1) {
            var pivot = -1;
            for (var i = rank; i < matrix.length; i += 1) {
                if (Math.abs(matrix[i][col]) > 1e-9) {
                    pivot = i;
                    break;
                }
            }
            if (pivot < 0) {
                continue;
            }
            var tmp = matrix[rank];
            matrix[rank] = matrix[pivot];
            matrix[pivot] = tmp;
            var factor = matrix[rank][col];
            for (var k = 0; k < n; k += 1) {
                matrix[rank][k] /= factor;
            }
            for (var i2 = 0; i2 < matrix.length; i2 += 1) {
                if (i2 !== rank && Math.abs(matrix[i2][col]) > 1e-9) {
                    var f = matrix[i2][col];
                    for (var k2 = 0; k2 < n; k2 += 1) {
                        matrix[i2][k2] -= f * matrix[rank][k2];
                    }
                }
            }
            rank += 1;
        }

        return rank;
    }

    function inverseN(m) {
        var n = m.length;
        var d = detN(m);
        if (Math.abs(d) < 1e-9 || n !== m[0].length) {
            return null;
        }
        var aug = m.map(function (row, i) {
            var identity = [];
            for (var k = 0; k < n; k += 1) {
                identity.push(k === i ? 1 : 0);
            }

            return row.concat(identity);
        });
        for (var col = 0; col < n; col += 1) {
            var pivot = -1;
            for (var i = col; i < n; i += 1) {
                if (Math.abs(aug[i][col]) > 1e-9) {
                    pivot = i;
                    break;
                }
            }
            if (pivot < 0) {
                return null;
            }
            var tmp = aug[col];
            aug[col] = aug[pivot];
            aug[pivot] = tmp;
            var factor = aug[col][col];
            for (var k = 0; k < 2 * n; k += 1) {
                aug[col][k] /= factor;
            }
            for (var i2 = 0; i2 < n; i2 += 1) {
                if (i2 !== col && Math.abs(aug[i2][col]) > 1e-9) {
                    var f = aug[i2][col];
                    for (var k2 = 0; k2 < 2 * n; k2 += 1) {
                        aug[i2][k2] -= f * aug[col][k2];
                    }
                }
            }
        }

        return aug.map(function (row) {
            return row.slice(n);
        });
    }

    /* 特征值：2×2 用求根公式；3×3 用卡尔达诺公式（浮点） */
    function eigenValues(m) {
        var n = m.length;
        if (n !== m[0].length || n < 2 || n > 3) {
            return null;
        }
        if (n === 2) {
            var tr = m[0][0] + m[1][1];
            var disc = tr * tr - 4 * det2(m);
            if (disc < 0) {
                return { real: [tr / 2, tr / 2], complex: true,
                         imag: Math.sqrt(-disc) / 2 };
            }

            return { real: [(tr + Math.sqrt(disc)) / 2,
                            (tr - Math.sqrt(disc)) / 2], complex: false };
        }

        var tr = m[0][0] + m[1][1] + m[2][2];
        var c2 = m[0][0] * m[1][1] + m[0][0] * m[2][2] + m[1][1] * m[2][2]
            - m[0][1] * m[1][0] - m[0][2] * m[2][0] - m[1][2] * m[2][1];
        var d3 = detN(m);
        var p = tr / -3;
        var q = -tr * tr * tr / 27 - tr * c2 / 6 - d3 / 2;
        var shift = tr / 3;
        var disc2 = q * q / 4 + p * p * p / 27;
        if (disc2 >= 0) {
            var root = Math.sqrt(disc2);
            var u = Math.cbrt(-q / 2 + root);
            var v = Math.cbrt(-q / 2 - root);

            return { real: [u + v - shift,
                            -(u + v) / 2 - shift,
                            (u - v) * Math.sqrt(3) / 2 - shift],
                     complex: true };
        }
        var r = Math.sqrt(-p * p * p / 27);
        var phi = Math.acos(Math.max(-1, Math.min(1, -q / (2 * r))));
        var a = 2 * Math.sqrt(-p / 3);

        return { real: [a * Math.cos(phi / 3) - shift,
                        a * Math.cos((phi + 2 * Math.PI) / 3) - shift,
                        a * Math.cos((phi + 4 * Math.PI) / 3) - shift],
                 complex: false };
    }

    /* 2×2 实矩阵的单位特征方向 */
    function eigenDirections(m) {
        var eig = eigenValues(m);
        if (!eig || eig.complex) {
            return [];
        }
        var directions = [];
        eig.real.forEach(function (lambda) {
            var v = null;
            if (Math.abs(m[0][1]) > 1e-9) {
                v = [m[0][1], lambda - m[0][0]];
            } else if (Math.abs(m[1][0]) > 1e-9) {
                v = [lambda - m[1][1], m[1][0]];
            } else {
                v = Math.abs(lambda - m[0][0]) < 1e-9 ? [1, 0] : [0, 1];
            }
            var norm = Math.hypot(v[0], v[1]);
            if (norm > 1e-9) {
                directions.push([v[0] / norm, v[1] / norm]);
            }
        });

        return directions;
    }

    /* ---------------- 渲染 ---------------- */

    function fmt(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '—';
        }
        var rounded = Math.round(value * 10000) / 10000;

        return String(rounded);
    }

    function matrixToText(m) {
        return m.map(function (row) {
            return row.map(function (v) { return fmt(v); }).join('　');
        }).join('；');
    }

    function refresh() {
        var data = readMatrix();
        var heat = document.getElementById('heatmap');
        heat.innerHTML = '';
        window.MatrixView.render(heat, { data: data, style: 'matrix' });

        var stats = document.getElementById('stats');
        stats.innerHTML = '';
        var isSquare = rows === cols;
        var determinant = isSquare ? detN(data) : null;
        var eigen = isSquare ? eigenValues(data) : null;

        addStat(stats, '规模', rows + ' × ' + cols);
        addStat(stats, '行列式', isSquare ? fmt(determinant) : '—（非方阵）');
        addStat(stats, '迹', isSquare
            ? fmt(data.reduce(function (sum, row, i) {
                return sum + row[i];
            }, 0)) : '—（非方阵）');
        addStat(stats, '秩', String(rankN(data)));
        var inv = isSquare ? inverseN(data) : null;
        addStat(stats, '逆矩阵', inv ? matrixToText(inv) : '不可逆（|A| = 0 或非方阵）');
        addStat(stats, '特征值', eigen
            ? (eigen.real.map(fmt).join('，') + (eigen.complex
                ? '（含复数或为共轭/等根的近似展示）' : ''))
            : '—（仅支持 2×2、3×3）');
        addStat(stats, '几何意义', isSquare && rows === 2
            ? '矩阵把平面做线性变换：|det| = ' + fmt(Math.abs(determinant))
              + ' 是面积放大倍数，det < 0 表示翻转定向。'
            : '方阵的 |det| 是体积放大倍数；秩是像空间的维数。');

        drawTransform(data);
    }

    function addStat(table, name, value) {
        var row = document.createElement('tr');
        var th = document.createElement('th');
        th.textContent = name;
        var td = document.createElement('td');
        td.textContent = value;
        row.appendChild(th);
        row.appendChild(td);
        table.appendChild(row);
    }

    /* ---------------- 2×2 线性变换动画 ---------------- */

    function drawTransform(data) {
        var panel = document.getElementById('transform-panel');
        if (rows !== 2 || cols !== 2) {
            panel.style.display = 'none';

            return;
        }
        panel.style.display = '';
        drawPlane(data, 1);
        if (animateHandle) {
            window.cancelAnimationFrame(animateHandle);
            animateHandle = null;
        }
    }

    function drawPlane(matrix, t) {
        var canvas = document.getElementById('plane');
        var ctx = canvas.getContext('2d');
        var w = canvas.width;
        var h = canvas.height;
        ctx.clearRect(0, 0, w, h);

        /* 插值矩阵：t=0 恒等，t=1 目标矩阵 */
        var m = [
            [1 + (matrix[0][0] - 1) * t, matrix[0][1] * t],
            [matrix[1][0] * t, 1 + (matrix[1][1] - 1) * t]
        ];
        var scale = 46;
        var origin = { x: w / 2, y: h / 2 };

        function project(px, py) {
            return { x: origin.x + (m[0][0] * px + m[0][1] * py) * scale,
                     y: origin.y - (m[1][0] * px + m[1][1] * py) * scale };
        }

        /* 原始网格（浅蓝） */
        ctx.strokeStyle = 'rgba(37,99,235,0.35)';
        ctx.lineWidth = 1;
        for (var g = -5; g <= 5; g += 1) {
            ctx.beginPath();
            ctx.moveTo(origin.x + g * scale, 0);
            ctx.lineTo(origin.x + g * scale, h);
            ctx.moveTo(0, origin.y + g * scale);
            ctx.lineTo(w, origin.y + g * scale);
            ctx.stroke();
        }

        /* 变换后网格（红） */
        ctx.strokeStyle = 'rgba(220,38,38,0.45)';
        for (var k = -5; k <= 5; k += 1) {
            ctx.beginPath();
            for (var s = -6; s <= 6; s += 1) {
                var p1 = project(k, s);
                var p2 = project(k, s + 0.25);
                if (s === -6) {
                    ctx.moveTo(p1.x, p1.y);
                } else {
                    ctx.lineTo(p1.x, p1.y);
                }
            }
            ctx.stroke();
            ctx.beginPath();
            for (var s2 = -6; s2 <= 6; s2 += 1) {
                var q1 = project(s2, k);
                var q2 = project(s2 + 0.25, k);
                if (s2 === -6) {
                    ctx.moveTo(q1.x, q1.y);
                } else {
                    ctx.lineTo(q1.x, q1.y);
                }
            }
            ctx.stroke();
        }

        /* 单位正方形变成的平行四边形（面积 = |det|） */
        var corners = [project(0, 0), project(1, 0), project(1, 1), project(0, 1)];
        ctx.fillStyle = 'rgba(245,158,11,0.30)';
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 2;
        ctx.beginPath();
        corners.forEach(function (p, index) {
            if (index === 0) {
                ctx.moveTo(p.x, p.y);
            } else {
                ctx.lineTo(p.x, p.y);
            }
        });
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        /* 基向量与特征方向 */
        drawArrow(ctx, origin, project(1, 0), '#16a34a', 'î');
        drawArrow(ctx, origin, project(0, 1), '#16a34a', 'ĵ');
        eigenDirections(matrix).forEach(function (dir, index) {
            var far = project(dir[0] * 6, dir[1] * 6);
            var back = project(-dir[0] * 6, -dir[1] * 6);
            ctx.strokeStyle = 'rgba(22,163,74,0.85)';
            ctx.lineWidth = 2.5;
            ctx.setLineDash([7, 5]);
            ctx.beginPath();
            ctx.moveTo(back.x, back.y);
            ctx.lineTo(far.x, far.y);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.fillStyle = '#16a34a';
            ctx.font = '13px "Segoe UI", sans-serif';
            ctx.fillText('特征方向 ' + (index + 1), far.x - 66, far.y - 8);
        });

        /* 坐标轴标签 */
        ctx.fillStyle = '#475569';
        ctx.font = '12px "Segoe UI", sans-serif';
        ctx.fillText('x', w - 16, origin.y - 8);
        ctx.fillText('y', origin.x + 8, 16);
        document.getElementById('transform-note').textContent =
            'det = ' + fmt(det2(matrix)) + '，动画进度 '
            + Math.round(t * 100) + '%（恒等变换 → 当前矩阵）';
    }

    function drawArrow(ctx, from, to, color, label) {
        var dx = to.x - from.x;
        var dy = to.y - from.y;
        var len = Math.hypot(dx, dy);
        if (len < 2) {
            return;
        }
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
        var angle = Math.atan2(dy, dx);
        ctx.beginPath();
        ctx.moveTo(to.x, to.y);
        ctx.lineTo(to.x - 10 * Math.cos(angle - 0.4),
                   to.y - 10 * Math.sin(angle - 0.4));
        ctx.lineTo(to.x - 10 * Math.cos(angle + 0.4),
                   to.y - 10 * Math.sin(angle + 0.4));
        ctx.closePath();
        ctx.fill();
        ctx.font = '14px "Cambria Math", Georgia, serif';
        ctx.fillText(label, to.x + 8, to.y - 6);
    }

    function playAnimation() {
        var data = readMatrix();
        if (animateHandle) {
            window.cancelAnimationFrame(animateHandle);
        }
        var start = null;
        function step(timestamp) {
            if (start === null) {
                start = timestamp;
            }
            var t = Math.min(1, (timestamp - start) / 1200);
            drawPlane(data, t);
            if (t < 1) {
                animateHandle = window.requestAnimationFrame(step);
            } else {
                animateHandle = null;
            }
        }
        animateHandle = window.requestAnimationFrame(step);
    }

    /* ---------------- 工具栏 ---------------- */

    function resize(deltaRows, deltaCols) {
        var newRows = Math.min(MAX_SIZE, Math.max(1, rows + deltaRows));
        var newCols = Math.min(MAX_SIZE, Math.max(1, cols + deltaCols));
        if (newRows === rows && newCols === cols) {
            return;
        }
        var old = readMatrix();
        rows = newRows;
        cols = newCols;
        buildEditor();
        for (var r = 0; r < Math.min(old.length, rows); r += 1) {
            for (var c = 0; c < Math.min(old[r].length, cols); c += 1) {
                inputs[r][c].value = fmt(old[r][c]);
            }
        }
        refresh();
    }

    function loadSample() {
        var samples = [
            [[1, 2], [3, 4]],
            [[2, 1], [1, 2]],
            [[0, 1], [-1, 0]],
            [[1, 1, 0], [1, 1, 0], [0, 0, 1]],
            [[1, 0, 2], [0, 1, 0], [0, 0, 1]]
        ];
        var sample = samples[Math.floor(Math.random() * samples.length)];
        rows = sample.length;
        cols = sample[0].length;
        buildEditor();
        for (var r = 0; r < rows; r += 1) {
            for (var c = 0; c < cols; c += 1) {
                inputs[r][c].value = String(sample[r][c]);
            }
        }
        refresh();
    }

    document.getElementById('btn-row-add').addEventListener('click',
        function () { resize(1, 0); });
    document.getElementById('btn-row-sub').addEventListener('click',
        function () { resize(-1, 0); });
    document.getElementById('btn-col-add').addEventListener('click',
        function () { resize(0, 1); });
    document.getElementById('btn-col-sub').addEventListener('click',
        function () { resize(0, -1); });
    document.getElementById('btn-sample').addEventListener('click', loadSample);
    document.getElementById('btn-animate').addEventListener('click',
        playAnimation);

    buildEditor();
    refresh();
}());
