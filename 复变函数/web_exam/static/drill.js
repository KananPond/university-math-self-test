/* ==========================================================================
 * 复变函数考试模拟系统 · 闪电训练
 * 作者：ZCode（GLM）    日期：2026-11-08    版本：1.0
 *
 * 说明：
 * 1. 把「复数的表示与运算」拆成随机小题，一题一题快问快答，
 *    答错立即排回队列重做，答对才算过 —— 这就是「肌肉记忆」的训练循环。
 * 2. 题目由服务端按种子即时生成，答案不下发；判分也在服务端完成。
 * 3. 掌握度按知识点记录在 localStorage：越不熟的知识点，下一轮出题越多。
 * 4. 跨轮次的错题保存在服务端错题本里，反复答对才移出。
 * ========================================================================== */

(function () {
    'use strict';

    var STORAGE_KEY = 'cv_drill_v1';
    var SESSION_SIZE = 15;
    var PLACEHOLDER = {
        number: '如 5、3/4、√13',
        complex: '如 3+4i、-i、1/2-1/2i',
        angle: '如 π/4、3π/4、-π/2'
    };

    var state = {
        seed: null,
        items: [],
        queue: [],
        current: null,
        answered: false,
        streak: 0,
        session: { done: 0, right: 0, wrong: 0, repeats: 0, marks: [] },
        mastery: {},
        wrongProgress: {},
        selectedKps: [],
        mode: 'all',
        running: false
    };

    var allKps = [];

    /* ---------------- 通用工具 ---------------- */

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        if (text !== undefined && text !== null) {
            node.textContent = text;
        }

        return node;
    }

    function escapeHtml(text) {
        return String(text).replace(/[&<>"']/g, function (ch) {
            return {
                '&': '&amp;', '<': '&lt;', '>': '&gt;',
                '"': '&quot;', "'": '&#39;'
            }[ch];
        });
    }

    function renderInline(text) {
        return escapeHtml(text).replace(/`([^`]+)`/g, '<code>$1</code>');
    }

    async function getJson(url) {
        var response = await fetch(url, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error('请求失败（HTTP ' + response.status + '）');
        }

        return response.json();
    }

    async function postJson(url, payload) {
        var response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            var message = '请求失败（HTTP ' + response.status + '）';
            try {
                var data = await response.json();
                if (data && data.error) {
                    message = data.error;
                }
            } catch (error) {
                /* 保留默认信息 */
            }
            throw new Error(message);
        }

        return response.json();
    }

    /* ---------------- 本地存储：掌握度 ---------------- */

    function loadLocal() {
        var raw = null;
        try {
            raw = localStorage.getItem(STORAGE_KEY);
        } catch (error) {
            raw = null;
        }
        if (!raw) {
            return;
        }
        try {
            var saved = JSON.parse(raw);
            state.mastery = saved.mastery || {};
            state.wrongProgress = saved.wrongProgress || {};
            state.selectedKps = saved.selectedKps || [];
        } catch (error) {
            /* 数据损坏时按新用户处理 */
        }
    }

    function saveLocal() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({
                mastery: state.mastery,
                wrongProgress: state.wrongProgress,
                selectedKps: state.selectedKps
            }));
        } catch (error) {
            /* 存储不可用时不影响训练 */
        }
    }

    function levelOf(kp) {
        var entry = state.mastery[kp];
        return entry ? (entry.level || 0) : 0;
    }

    /* ---------------- 侧栏渲染 ---------------- */

    function renderKpChips(kps) {
        var box = document.getElementById('kp-chips');
        box.innerHTML = '';
        if (!state.selectedKps.length) {
            state.selectedKps = kps.slice();
        }
        kps.forEach(function (kp) {
            var chip = el('button', 'kp-chip', kp);
            chip.type = 'button';
            if (state.selectedKps.indexOf(kp) >= 0) {
                chip.classList.add('on');
            }
            chip.addEventListener('click', function () {
                var index = state.selectedKps.indexOf(kp);
                if (index >= 0) {
                    if (state.selectedKps.length === 1) {
                        return;
                    }
                    state.selectedKps.splice(index, 1);
                } else {
                    state.selectedKps.push(kp);
                }
                saveLocal();
                renderKpChips(kps);
            });
            box.appendChild(chip);
        });
    }

    function renderMastery(kps) {
        var box = document.getElementById('mastery-list');
        box.innerHTML = '';
        kps.forEach(function (kp) {
            var entry = state.mastery[kp] || { attempts: 0, correct: 0, level: 0 };
            var rate = entry.attempts
                ? Math.round(entry.correct * 100 / entry.attempts) : 0;
            var row = el('div', 'mastery-row');
            row.appendChild(el('span', 'mastery-name', kp));
            var bar = el('div', 'mastery-bar');
            var fill = el('div', 'mastery-fill');
            fill.style.width = rate + '%';
            if (rate < 60) {
                fill.classList.add('low');
            }
            bar.appendChild(fill);
            row.appendChild(bar);
            row.appendChild(el('span', 'mastery-count',
                rate + '% · L' + (entry.level || 0)));
            box.appendChild(row);
        });
    }

    function renderStats() {
        document.getElementById('stat-done').textContent = state.session.done;
        document.getElementById('stat-right').textContent = state.session.right;
        document.getElementById('stat-wrong').textContent = state.session.wrong;
        document.getElementById('stat-streak').textContent = state.streak;

        var row = document.getElementById('qmark-row');
        row.innerHTML = '';
        state.session.marks.forEach(function (mark) {
            var dot = el('span', 'qmark ' + (mark ? 'hit' : 'miss'));
            row.appendChild(dot);
        });

        document.getElementById('session-hint').textContent = state.running
            ? '本轮还剩 ' + state.queue.length + ' 题未过关'
            : '点「开始一轮训练」开始';
    }

    /* ---------------- 题目装载 ---------------- */

    function shuffle(list) {
        var copy = list.slice();
        for (var i = copy.length - 1; i > 0; i -= 1) {
            var j = Math.floor(Math.random() * (i + 1));
            var tmp = copy[i];
            copy[i] = copy[j];
            copy[j] = tmp;
        }

        return copy;
    }

    /* 掌握度低的知识点排在前面，多出题 */
    function buildQueue(items, size) {
        var groups = {};
        items.forEach(function (item) {
            var kp = item.kp || '其他';
            if (!groups[kp]) {
                groups[kp] = [];
            }
            groups[kp].push(item);
        });

        var kpList = Object.keys(groups).sort(function (a, b) {
            return levelOf(a) - levelOf(b);
        }).map(function (kp) {
            return { kp: kp, list: shuffle(groups[kp]) };
        });

        var queue = [];
        var round = 0;
        while (queue.length < size) {
            var added = false;
            for (var i = 0; i < kpList.length && queue.length < size; i += 1) {
                if (round < kpList[i].list.length) {
                    queue.push(kpList[i].list[round]);
                    added = true;
                }
            }
            if (!added) {
                break;
            }
            round += 1;
        }

        return queue;
    }

    async function startSession(mode) {
        var kps = state.selectedKps.slice();
        try {
            if (mode === 'wrong') {
                var data = await getJson('/api/drill/wrongbook');
                var items = data.items || [];
                if (!items.length) {
                    window.alert('错题本是空的 —— 先做几轮训练吧。');
                    return;
                }
                state.mode = 'wrong';
                state.items = items;
                state.queue = items.slice(0, SESSION_SIZE);
                state.seed = null;
            } else {
                var seed = Math.floor(Math.random() * 1000000) + 1;
                var url = '/api/drill?seed=' + seed + '&count=40';
                if (kps.length) {
                    url += '&kp=' + encodeURIComponent(kps.join(','));
                }
                var payload = await getJson(url);
                state.mode = 'all';
                state.seed = seed;
                state.items = payload.items || [];
                state.queue = buildQueue(state.items, SESSION_SIZE);
            }
        } catch (error) {
            window.alert('装载训练题失败：' + error.message);
            return;
        }

        state.session = { done: 0, right: 0, wrong: 0, repeats: 0,
                          marks: [], perKp: {} };
        state.streak = 0;
        state.running = true;
        state.answered = false;
        renderStats();
        nextItem();
    }

    /* ---------------- 出题与作答 ---------------- */

    function nextItem() {
        state.current = null;
        state.answered = false;
        var inputBox = document.getElementById('drill-input');
        var actions = document.getElementById('drill-actions');
        var feedback = document.getElementById('drill-feedback');
        var figure = document.getElementById('drill-figure');
        inputBox.innerHTML = '';
        actions.innerHTML = '';
        feedback.innerHTML = '';
        figure.innerHTML = '';

        if (!state.queue.length) {
            finishSession();
            return;
        }

        var item = state.queue.shift();
        state.current = item;

        document.getElementById('drill-stem').innerHTML =
            renderInline(item.stem);

        if (item.figure) {
            window.ComplexView.render(figure, item.figure);
        }

        if (item.kind === 'blanks') {
            buildBlanksInput(item);
        } else {
            buildSingleInput(item);
        }

        renderStats();
    }

    function buildSingleInput(item) {
        var box = document.getElementById('drill-input');
        var input = el('input', 'drill-input');
        input.type = 'text';
        input.placeholder = PLACEHOLDER[item.answer_type || 'number']
            || PLACEHOLDER.number;
        input.autocomplete = 'off';
        input.spellcheck = false;
        box.appendChild(input);

        var button = el('button', 'btn btn-primary', '确认');
        button.type = 'button';
        button.addEventListener('click', function () {
            submitAnswer(input.value);
        });
        input.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                submitAnswer(input.value);
            }
        });
        var actions = document.getElementById('drill-actions');
        actions.appendChild(button);
        var skip = el('button', 'btn', '跳过');
        skip.type = 'button';
        skip.addEventListener('click', function () {
            state.queue.push(item);
            state.queue = shuffle(state.queue);
            nextItem();
        });
        actions.appendChild(skip);
        setTimeout(function () { input.focus(); }, 30);
    }

    function buildBlanksInput(item) {
        var box = document.getElementById('drill-input');
        var inputs = [];
        (item.blanks || []).forEach(function (blank, index) {
            var row = el('div', 'cv-blank-row');
            var label = el('label', 'cv-blank-label',
                blank.label || ('第 %d 空' % (index + 1)));
            var input = el('input', 'drill-input');
            input.type = 'text';
            input.placeholder = PLACEHOLDER[blank.answer_type || 'number']
                || PLACEHOLDER.number;
            input.autocomplete = 'off';
            input.spellcheck = false;
            row.appendChild(label);
            row.appendChild(input);
            box.appendChild(row);
            inputs.push(input);
        });

        var button = el('button', 'btn btn-primary', '确认');
        button.type = 'button';
        button.addEventListener('click', function () {
            var values = {};
            inputs.forEach(function (input, index) {
                values[String(index)] = input.value.trim();
            });
            submitAnswer(values, inputs);
        });
        var actions = document.getElementById('drill-actions');
        actions.appendChild(button);
        setTimeout(function () {
            if (inputs.length) {
                inputs[0].focus();
            }
        }, 30);
    }

    async function submitAnswer(response, inputs) {
        if (state.answered || !state.current) {
            return;
        }
        state.answered = true;
        var item = state.current;

        var payload = { response: response };
        if (item.wrongId) {
            payload.wrongId = item.wrongId;
        } else {
            payload.id = item.id;
            payload.seed = state.seed;
        }

        var result;
        try {
            result = await postJson('/api/drill/check', payload);
        } catch (error) {
            window.alert('判分失败：' + error.message);
            state.answered = false;
            return;
        }

        var kp = item.kp || '其他';
        if (!state.session.perKp[kp]) {
            state.session.perKp[kp] = { total: 0, right: 0 };
        }
        state.session.perKp[kp].total += 1;

        if (result.correct) {
            state.streak += 1;
            state.session.right += 1;
            state.session.perKp[kp].right += 1;
            state.session.marks.push(true);
            if (inputs) {
                inputs.forEach(function (input) {
                    input.classList.add('right');
                    input.readOnly = true;
                });
            }
            if (item.wrongId) {
                markWrongMastered(item.wrongId);
            }
        } else {
            state.streak = 0;
            state.session.wrong += 1;
            state.session.marks.push(false);
            if (inputs) {
                inputs.forEach(function (input) {
                    input.classList.add('wrong');
                    input.readOnly = true;
                });
            }
            await rememberWrong(item);
            /* 答错立刻排回队列，稍后重做 —— 必须答对才算过 */
            state.session.repeats += 1;
            var position = Math.min(2, state.queue.length);
            state.queue.splice(position, 0, item);
        }

        state.session.done += 1;
        renderStats();
        showFeedback(result);
    }

    async function rememberWrong(item) {
        if (item.wrongId) {
            return;
        }
        try {
            var result = await postJson('/api/drill/wrong',
                                       { id: item.id, seed: state.seed });
            if (result && result.wrongId) {
                item.wrongId = result.wrongId;
            }
            refreshWrongbookHint();
        } catch (error) {
            /* 错题本登记失败不影响训练 */
        }
    }

    function markWrongMastered(wrongId) {
        var progress = state.wrongProgress[wrongId] || { streak: 0 };
        progress.streak += 1;
        state.wrongProgress[wrongId] = progress;
        saveLocal();
        if (progress.streak >= 2) {
            postJson('/api/drill/mastered', { wrongId: wrongId })
                .then(function () {
                    delete state.wrongProgress[wrongId];
                    saveLocal();
                    refreshWrongbookHint();
                })
                .catch(function () { /* 忽略 */ });
        }
    }

    function showFeedback(result) {
        var box = document.getElementById('drill-feedback');
        box.innerHTML = '';
        var feedback = el('div', 'drill-feedback '
                          + (result.correct ? 'good' : 'bad'));
        feedback.appendChild(el('div', 'verdict ' + (result.correct ? 'good' : 'bad'),
            result.correct ? '✓ 答对了' : '✗ 答错了，这题会再考一次'));
        if (result.expected) {
            var expected = el('div', 'expected');
            expected.appendChild(el('strong', null, '正确答案：'));
            expected.appendChild(document.createTextNode(' ' + result.expected));
            feedback.appendChild(expected);
        }
        if (result.explain) {
            feedback.appendChild(el('div', null, result.explain));
        }
        if (result.details && result.details.length) {
            var list = el('ul');
            result.details.forEach(function (detail) {
                var text = detail.label + '：'
                    + (detail.right ? '✓ ' : '✗ ')
                    + (detail.submitted || '（空）')
                    + '　→　' + (Array.isArray(detail.answer)
                                 ? detail.answer.join(' 或 ') : detail.answer);
                list.appendChild(el('li', null, text));
            });
            feedback.appendChild(list);
        }
        box.appendChild(feedback);

        var actions = document.getElementById('drill-actions');
        actions.innerHTML = '';
        var next = el('button', 'btn btn-primary', '下一题');
        next.type = 'button';
        next.addEventListener('click', nextItem);
        actions.appendChild(next);
    }

    /* ---------------- 一轮结束 ---------------- */

    function finishSession() {
        state.running = false;
        state.current = null;
        updateMastery();
        renderStats();

        document.getElementById('drill-stem').innerHTML =
            '本轮结束 🎉';
        document.getElementById('drill-input').innerHTML = '';
        document.getElementById('drill-figure').innerHTML = '';
        var feedback = document.getElementById('drill-feedback');
        feedback.innerHTML = '';
        var box = el('div', 'drill-feedback good');
        box.appendChild(el('div', 'verdict good', '本轮完成'));
        box.appendChild(el('div', null,
            '共练 ' + state.session.done + ' 题，答对 ' + state.session.right
            + ' 次，答错 ' + state.session.wrong + ' 次'
            + (state.session.repeats
               ? '（其中 ' + state.session.repeats + ' 题重做后才答对）' : '')));
        box.appendChild(el('div', null,
            '答错的题已存入错题本，连续两次答对才会移出。'));
        feedback.appendChild(box);

        var actions = document.getElementById('drill-actions');
        actions.innerHTML = '';
        var again = el('button', 'btn btn-primary', '再来一轮');
        again.type = 'button';
        again.addEventListener('click', function () {
            startSession(state.mode);
        });
        actions.appendChild(again);
    }

    function updateMastery() {
        var perKp = state.session.perKp || {};
        Object.keys(perKp).forEach(function (kp) {
            var info = perKp[kp];
            var entry = state.mastery[kp]
                || { attempts: 0, correct: 0, level: 0 };
            entry.attempts += info.total;
            entry.correct += info.right;
            var rate = info.total ? info.right / info.total : 0;
            if (rate >= 0.9) {
                entry.level = Math.min(5, (entry.level || 0) + 1);
            } else if (rate < 0.6) {
                entry.level = Math.max(0, (entry.level || 0) - 1);
            }
            state.mastery[kp] = entry;
        });
        saveLocal();
        renderMastery(allKps.length ? allKps : state.selectedKps);
    }

    /* ---------------- 服务状态与错题本 ---------------- */

    async function checkService() {
        var box = document.getElementById('service-state');
        try {
            var health = await getJson('/api/health');
            box.className = 'service-state online';
            box.querySelector('.text').textContent =
                '本地判分服务 · 题库 ' + health.bankTotal + ' 题';
            if (health.drillKps && health.drillKps.length) {
                allKps = health.drillKps;
                renderKpChips(allKps);
                renderMastery(allKps);
            }
        } catch (error) {
            box.className = 'service-state offline';
            box.querySelector('.text').textContent = '本地判分服务离线';
        }
    }

    async function refreshWrongbookHint() {
        try {
            var data = await getJson('/api/drill/wrongbook');
            var count = (data.items || []).length;
            document.getElementById('wrongbook-hint').textContent =
                count ? ('错题本里有 ' + count + ' 道题待消灭') : '错题本是空的';
        } catch (error) {
            document.getElementById('wrongbook-hint').textContent = '';
        }
    }

    /* ---------------- 事件绑定 ---------------- */

    document.getElementById('btn-start').addEventListener('click', function () {
        startSession('all');
    });
    document.getElementById('btn-wrong-mode').addEventListener('click',
        function () {
            startSession('wrong');
        });

    /* ---------------- 初始化 ---------------- */

    loadLocal();
    renderStats();
    checkService();
    refreshWrongbookHint();
}());
