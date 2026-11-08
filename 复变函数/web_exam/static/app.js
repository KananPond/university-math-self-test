/* ==========================================================================
 * 复变函数考试模拟系统 · 答题与判分逻辑
 * 作者：ZCode（GLM）    日期：2026-11-08    版本：1.0
 *
 * 说明：
 * 1. 试卷由服务端按随机种子从题库抽取，前端只拿得到题面，拿不到答案。
 * 2. 交卷时把全部作答提交给 /api/grade，由服务端统一判分并返回解析；
 *    平时作答通过 /api/score 实时统计总分（不下发对错明细）。
 * 3. 题面中的 [[key]] 标记用 ComplexView 渲染成复平面图解，
 *    计算题在多空表格里作答并同步显示复平面预览。
 * 4. 作答实时写入 localStorage，刷新页面不丢失，同一份卷子可复现。
 * ========================================================================== */

(function () {
    'use strict';

    var LETTERS = ['A', 'B', 'C', 'D'];
    var STORAGE_KEY = 'cv_exam_v1';
    var EMPTY_ANSWERS = function () {
        return { choice: {}, judge: {}, fill: {}, calc: {} };
    };

    var PLACEHOLDER = {
        number: '如 5、3/4、√13',
        complex: '如 3+4i、-i、1/2-1/2i',
        angle: '如 π/4、3π/4、-π/2'
    };

    var state = {
        seed: null,
        paper: null,
        bank: null,
        answers: EMPTY_ANSWERS(),
        live: null,
        graded: null,
        secondsLeft: null,
        started: false,
        submitted: false,
        service: 'unknown'
    };

    var allQuestions = [];
    var timerHandle = null;
    var scoreTimer = null;

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

    /* 把题面中的反引号片段渲染成行内代码 */
    function renderInline(text) {
        return escapeHtml(text).replace(/`([^`]+)`/g, '<code>$1</code>');
    }

    function formatTime(totalSeconds) {
        var seconds = Math.max(0, Math.floor(totalSeconds));
        var hours = Math.floor(seconds / 3600);
        var minutes = Math.floor((seconds % 3600) / 60);
        var rest = seconds % 60;
        var pad = function (value) { return value < 10 ? '0' + value : '' + value; };
        if (hours > 0) {
            return hours + ':' + pad(minutes) + ':' + pad(rest);
        }

        return pad(minutes) + ':' + pad(rest);
    }

    /* ---------------- 本地存储 ---------------- */

    function persist() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({
                seed: state.seed,
                answers: state.answers,
                live: state.live,
                graded: state.graded,
                secondsLeft: state.secondsLeft,
                started: state.started,
                submitted: state.submitted
            }));
        } catch (error) {
            /* 存储不可用时不影响答题 */
        }
    }

    function restore() {
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
            state.seed = saved.seed || null;
            state.answers = saved.answers || EMPTY_ANSWERS();
            if (!state.answers.calc) {
                state.answers.calc = {};
            }
            if (!state.answers.fill) {
                state.answers.fill = {};
            }
            state.live = saved.live || null;
            state.graded = saved.graded || null;
            state.started = !!saved.started;
            state.submitted = !!saved.submitted;
            if (typeof saved.secondsLeft === 'number') {
                state.secondsLeft = saved.secondsLeft;
            }
        } catch (error) {
            /* 数据损坏时按新卷处理 */
        }
    }

    function clearStorage() {
        try {
            localStorage.removeItem(STORAGE_KEY);
        } catch (error) {
            /* 忽略 */
        }
    }

    /* ---------------- 网络 ---------------- */

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
                /* 保留默认错误信息 */
            }
            throw new Error(message);
        }

        return response.json();
    }

    /* ---------------- 题面渲染 ---------------- */

    /* 把含 [[key]] 标记与 `行内代码` 的文本渲染进容器 */
    function renderRichText(container, text, figures) {
        var parts = String(text).split(/(\[\[[A-Za-z0-9_]+\]\])/);
        parts.forEach(function (part) {
            if (!part) {
                return;
            }
            var marker = part.match(/^\[\[([A-Za-z0-9_]+)\]\]$/);
            if (marker) {
                var spec = (figures || {})[marker[1]];
                var figure = el('span', 'cv-figure-box');
                container.appendChild(figure);
                if (spec) {
                    window.ComplexView.render(figure, spec);
                } else {
                    figure.textContent = part;
                }

                return;
            }
            var span = el('span');
            span.innerHTML = renderInline(part);
            container.appendChild(span);
        });
    }

    /* ---------------- 作答状态 ---------------- */

    function isAnswered(section, question) {
        var id = question.id;
        if (section.type === 'choice') {
            return typeof state.answers.choice[id] === 'number';
        }
        if (section.type === 'judge') {
            return typeof state.answers.judge[id] === 'boolean';
        }
        if (section.mode === 'blanks') {
            var value = state.answers.calc[id];
            if (!value || !value.blanks) {
                return false;
            }
            return Object.keys(value.blanks).some(function (key) {
                return String(value.blanks[key]).trim() !== '';
            });
        }

        return String(state.answers.fill[id] || '').trim() !== '';
    }

    function answeredCount() {
        return allQuestions.filter(function (item) {
            return isAnswered(item.section, item.question);
        }).length;
    }

    function liveTotals() {
        if (!state.live) {
            return { score: 0, full: 0, answered: 0, total: allQuestions.length };
        }

        return state.live;
    }

    /* ---------------- 侧栏 ---------------- */

    function updateScorePanel() {
        var totals = liveTotals();
        document.getElementById('score-value').textContent =
            state.started ? String(totals.score) : '--';
        document.getElementById('score-sub').textContent = state.started
            ? '已答 ' + (totals.answered || 0) + '/' + (totals.total || 0)
              + ' 题'
            : '尚未开始考试';

        var answered = answeredCount();
        document.getElementById('progress-text').textContent =
            '已答 ' + answered + ' / ' + allQuestions.length + ' 题';
        var percent = allQuestions.length
            ? Math.round(answered * 100 / allQuestions.length) : 0;
        document.getElementById('progress-fill-side').style.width = percent + '%';
        document.getElementById('progress-fill').style.width = percent + '%';
    }

    function renderNav() {
        var nav = document.getElementById('nav');
        nav.innerHTML = '';
        state.paper.sections.forEach(function (section) {
            var group = el('div', 'nav-group');
            group.appendChild(el('p', 'nav-group-title', section.title));
            var grid = el('div', 'nav-grid');
            section.questions.forEach(function (question) {
                var item = el('button', 'nav-item', question.no);
                item.type = 'button';
                if (isAnswered(section, question)) {
                    item.classList.add('answered');
                }
                item.addEventListener('click', function () {
                    var target = document.getElementById('q-' + question.id);
                    if (target && target.scrollIntoView) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                });
                grid.appendChild(item);
            });
            group.appendChild(grid);
            nav.appendChild(group);
        });
    }

    function refreshNavStates() {
        var items = document.querySelectorAll('.nav-item');
        Array.prototype.forEach.call(items, function (node, index) {
            if (!allQuestions[index]) {
                return;
            }
            node.classList.toggle('answered',
                isAnswered(allQuestions[index].section, allQuestions[index].question));
        });
    }

    /* ---------------- 试卷渲染 ---------------- */

    function renderLanding() {
        var body = document.getElementById('paper-body');
        body.innerHTML = '';

        var panel = el('section', 'panel landing');
        var title = el('h2', null, state.paper.title);
        var metaLines = [
            '抽题种子 ' + state.seed + '（同一种子必得同一份卷）',
            '题量构成：' + state.paper.sections.map(function (section) {
                return section.title.replace(/^[一二三四]、/, '') + ' '
                    + section.questions.length + ' 题';
            }).join(' · '),
            '满分 ' + state.paper.total_score + ' 分 · 考试时间 '
                + state.paper.duration_minutes + ' 分钟'
        ];
        var meta = el('p', 'meta');
        meta.innerHTML = metaLines.map(renderInline).join('<br>');
        var button = el('button', 'btn btn-primary', '开始考试');
        button.id = 'btn-start';
        button.type = 'button';
        button.addEventListener('click', startExam);
        var drillLink = el('a', 'btn btn-ghost', '先做闪电训练');
        drillLink.href = 'drill.html';
        panel.appendChild(title);
        panel.appendChild(meta);
        panel.appendChild(button);
        panel.appendChild(el('p', 'meta',
            '提示：想先把复数的加减乘除与模、辐角练到不用想，'
            + '可以先到「闪电训练」页做针对性练习。'));
        panel.appendChild(drillLink);
        body.appendChild(panel);

        document.getElementById('instructions').innerHTML = '';
        state.paper.instructions.forEach(function (note) {
            var item = el('li');
            item.innerHTML = renderInline(note);
            document.getElementById('instructions').appendChild(item);
        });
    }

    function renderSectionHead(section) {
        var head = el('div', 'section-head');
        head.appendChild(el('h2', null, section.title + '（共 ' + section.score + ' 分）'));
        head.appendChild(el('p', null, section.desc));

        return head;
    }

    function renderChoice(item) {
        var section = item.section;
        var question = item.question;
        var box = el('div', 'q-body options');
        question.options.forEach(function (option, index) {
            var button = el('button', 'btn btn-choice');
            button.type = 'button';
            var label = el('span', 'option-label');
            label.appendChild(el('span', 'option-letter', LETTERS[index] + '.'));
            var text = el('span');
            renderRichText(text, option, question.figures);
            label.appendChild(text);
            button.appendChild(label);
            if (state.answers.choice[question.id] === index) {
                button.classList.add('selected');
            }
            button.addEventListener('click', function () {
                state.answers.choice[question.id] = index;
                persist();
                Array.prototype.forEach.call(
                    box.querySelectorAll('.btn-choice'), function (node) {
                        node.classList.remove('selected');
                    });
                button.classList.add('selected');
                refreshNavStates();
                updateScorePanel();
                scheduleScoreRefresh();
            });
            box.appendChild(button);
        });
        if (state.graded) {
            attachExplain(box, section, question);
        }

        return box;
    }

    function renderJudge(item) {
        var section = item.section;
        var question = item.question;
        var box = el('div', 'q-body');
        var right = el('button', 'btn btn-judge', '对');
        var wrong = el('button', 'btn btn-judge', '错');
        right.type = 'button';
        wrong.type = 'button';
        var chosen = state.answers.judge[question.id];
        if (chosen === true) {
            right.classList.add('selected-right');
        }
        if (chosen === false) {
            wrong.classList.add('selected-wrong');
        }
        right.addEventListener('click', function () {
            state.answers.judge[question.id] = true;
            persist();
            right.classList.add('selected-right');
            wrong.classList.remove('selected-wrong');
            afterObjectiveAnswer();
        });
        wrong.addEventListener('click', function () {
            state.answers.judge[question.id] = false;
            persist();
            wrong.classList.add('selected-wrong');
            right.classList.remove('selected-right');
            afterObjectiveAnswer();
        });
        box.appendChild(right);
        box.appendChild(wrong);
        if (state.graded) {
            attachExplain(box, section, question);
        }

        return box;
    }

    function renderFill(item) {
        var section = item.section;
        var question = item.question;
        var box = el('div', 'q-body');
        var input = el('input', 'fill-input');
        input.type = 'text';
        input.placeholder = PLACEHOLDER[question.answer_type || 'number']
            || PLACEHOLDER.number;
        input.autocomplete = 'off';
        input.spellcheck = false;
        input.value = state.answers.fill[question.id] || '';
        input.addEventListener('input', function () {
            state.answers.fill[question.id] = input.value.trim();
            persist();
            refreshNavStates();
            updateScorePanel();
            scheduleScoreRefresh();
        });
        box.appendChild(input);
        if (state.graded) {
            attachExplain(box, section, question);
        }

        return box;
    }

    function renderCalc(item) {
        var section = item.section;
        var question = item.question;
        var box = el('div', 'q-body');
        var holder = el('div');
        box.appendChild(holder);
        var saved = state.answers.calc[question.id];
        var savedBlanks = null;
        if (saved && saved.blanks) {
            savedBlanks = (question.blanks || []).map(function (blank, index) {
                return saved.blanks[String(index)];
            });
        }
        window.ComplexView.mount(holder, {
            blanks: question.blanks || [],
            value: savedBlanks
        }, function () {
            /* 作答内容从输入框实时回收到 state */
            var inputs = holder.querySelectorAll('.cv-blank-input');
            var values = {};
            for (var index = 0; index < inputs.length; index += 1) {
                values[String(index)] = String(inputs[index].value || '').trim();
            }
            state.answers.calc[question.id] = { blanks: values };
            persist();
            refreshNavStates();
            updateScorePanel();
            scheduleScoreRefresh();
        });
        if (state.graded) {
            attachExplain(box, section, question);
        }

        return box;
    }

    function afterObjectiveAnswer() {
        refreshNavStates();
        updateScorePanel();
        scheduleScoreRefresh();
    }

    /* 交卷后逐题解析（含你的作答与正确答案） */
    function attachExplain(box, section, question) {
        var outcome = null;
        (state.graded.results || []).forEach(function (entry) {
            if (entry.id === question.id) {
                outcome = entry;
            }
        });
        if (!outcome) {
            return;
        }

        var details = el('details', 'q-explain');
        var summary = el('summary', null,
            '查看解析 · 得 ' + outcome.score + ' / ' + outcome.full + ' 分');
        details.appendChild(summary);
        var body = el('div', 'explain-body');

        var mine = el('p');
        mine.appendChild(el('strong', null, '你的作答：'));
        mine.appendChild(document.createTextNode(describeChosen(outcome)));
        body.appendChild(mine);

        var answer = el('p');
        answer.appendChild(el('strong', null, '正确答案：'));
        answer.appendChild(document.createTextNode(describeAnswer(outcome)));
        body.appendChild(answer);

        body.appendChild(el('p', null, '解析：' + outcome.explain));
        details.appendChild(body);
        box.appendChild(details);
    }

    function describeAnswer(outcome) {
        if (outcome.mode === 'blanks' && Array.isArray(outcome.answer)) {
            return outcome.answer.map(function (item) {
                var text = Array.isArray(item.answer)
                    ? item.answer.join(' 或 ') : item.answer;
                return item.label + ' = ' + text;
            }).join('；');
        }
        if (outcome.answer_text !== null && outcome.answer_text !== undefined) {
            return String(outcome.answer_text);
        }
        if (Array.isArray(outcome.answer)) {
            return outcome.answer.join(' 或 ');
        }
        if (outcome.answer && typeof outcome.answer === 'object') {
            return JSON.stringify(outcome.answer);
        }

        return String(outcome.answer);
    }

    function describeChosen(outcome) {
        if (!outcome.answered) {
            return '（未作答）';
        }
        if (typeof outcome.chosen === 'boolean') {
            return outcome.chosen ? '对' : '错';
        }
        if (typeof outcome.chosen === 'number') {
            return '选项 ' + LETTERS[outcome.chosen];
        }
        if (outcome.mode === 'blanks' && Array.isArray(outcome.submitted)) {
            return outcome.submitted.map(function (item) {
                return item.label + ' = ' + (item.submitted || '（空）');
            }).join('；');
        }
        if (typeof outcome.chosen === 'string' && outcome.chosen) {
            return outcome.chosen;
        }

        return '（已作答）';
    }

    function renderQuestion(item) {
        var section = item.section;
        var question = item.question;
        var block = el('article', 'question');
        block.id = 'q-' + question.id;

        var head = el('div', 'question-head');
        head.appendChild(el('span', 'q-no', question.no + '.'));
        var stem = el('div', 'q-stem');
        renderRichText(stem, question.stem, question.figures);
        head.appendChild(stem);
        block.appendChild(head);

        if (question.kp) {
            block.appendChild(el('span', 'q-kp', question.kp));
        }

        if (section.type === 'choice') {
            block.appendChild(renderChoice(item));
        } else if (section.type === 'judge') {
            block.appendChild(renderJudge(item));
        } else if (section.mode === 'blanks') {
            block.appendChild(renderCalc(item));
        } else {
            block.appendChild(renderFill(item));
        }

        return block;
    }

    function collectQuestions() {
        allQuestions = [];
        state.paper.sections.forEach(function (section) {
            section.questions.forEach(function (question) {
                allQuestions.push({ section: section, question: question });
            });
        });
    }

    function renderPaper() {
        var body = document.getElementById('paper-body');
        body.innerHTML = '';
        collectQuestions();
        state.paper.sections.forEach(function (section) {
            var block = el('section', 'section-block');
            block.appendChild(renderSectionHead(section));
            section.questions.forEach(function (question) {
                block.appendChild(renderQuestion({ section: section,
                                                   question: question }));
            });
            body.appendChild(block);
        });
        renderNav();
        updateScorePanel();

        document.getElementById('instructions').innerHTML = '';
        state.paper.instructions.forEach(function (note) {
            var item = el('li');
            item.innerHTML = renderInline(note);
            document.getElementById('instructions').appendChild(item);
        });
    }

    /* ---------------- 实时得分 ---------------- */

    function scheduleScoreRefresh() {
        if (scoreTimer) {
            window.clearTimeout(scoreTimer);
        }
        scoreTimer = window.setTimeout(function () {
            scoreTimer = null;
            refreshLiveScore();
        }, 400);
    }

    async function refreshLiveScore() {
        if (!state.started || state.submitted || !state.paper) {
            return;
        }
        try {
            var result = await postJson('/api/score', {
                seed: state.seed,
                answers: state.answers
            });
            state.live = {
                score: result.score,
                full: result.full,
                answered: result.answered,
                total: result.total
            };
            persist();
            updateScorePanel();
        } catch (error) {
            /* 服务不可用时静默，下次作答再试 */
        }
    }

    /* ---------------- 计时 ---------------- */

    function updateTimer() {
        var node = document.getElementById('timer');
        node.textContent = formatTime(state.secondsLeft === null
            ? state.paper.duration_minutes * 60 : state.secondsLeft);
        if (state.started && !state.submitted && state.secondsLeft <= 300) {
            node.classList.add('danger');
        }
    }

    function startTimer() {
        if (timerHandle) {
            window.clearInterval(timerHandle);
        }
        timerHandle = window.setInterval(function () {
            state.secondsLeft -= 1;
            persist();
            updateTimer();
            if (state.secondsLeft <= 0) {
                window.clearInterval(timerHandle);
                window.alert('考试时间到，系统自动交卷。');
                gradeAll();
            }
        }, 1000);
    }

    /* ---------------- 开考与交卷 ---------------- */

    function startExam() {
        if (state.started) {
            return;
        }
        state.started = true;
        state.secondsLeft = state.paper.duration_minutes * 60;
        persist();
        renderPaper();
        updateTimer();
        startTimer();
        refreshLiveScore();
        window.scrollTo({ top: 0, behavior: 'auto' });
    }

    function commentFor(score, total) {
        var ratio = total ? score / total : 0;
        if (ratio >= 0.9) {
            return '优秀！基本功已经成型，注意错题里的细节。';
        }
        if (ratio >= 0.75) {
            return '良好。基础扎实，去闪电训练把运算再提速。';
        }
        if (ratio >= 0.6) {
            return '及格。建议把复数的模、辐角与四则运算重刷一遍。';
        }

        return '还需要加强。建议先做闪电训练，把复数的表示与运算练熟再回来。';
    }

    function renderResult() {
        var graded = state.graded;
        document.getElementById('result-score').textContent = String(graded.score);
        document.getElementById('result-total').textContent =
            '/ ' + graded.total_score + ' 分';
        document.getElementById('result-comment').textContent =
            commentFor(graded.score, graded.total_score);

        var table = document.getElementById('result-table');
        table.innerHTML = '';
        var head = el('tr');
        ['题号', '大题', '知识点', '状态', '得分'].forEach(function (text) {
            head.appendChild(el('th', null, text));
        });
        table.appendChild(head);
        graded.results.forEach(function (entry) {
            var row = el('tr');
            row.appendChild(el('td', null, entry.no));
            row.appendChild(el('td', null, entry.section));
            row.appendChild(el('td', null, entry.kp || '-'));
            var status = el('td');
            if (entry.score >= entry.full) {
                status.appendChild(el('span', 'good', '✓ 通过'));
            } else if (entry.score > 0) {
                status.appendChild(el('span', null,
                    '部分（' + (entry.correct || '') + '）'));
            } else {
                status.appendChild(el('span', 'bad', '✗ ' +
                    (entry.answered ? '有误' : '未作答')));
            }
            row.appendChild(status);
            row.appendChild(el('td', null, entry.score + ' / ' + entry.full));
            table.appendChild(row);

            var detailRow = el('tr');
            var cell = el('td', null);
            cell.colSpan = 5;
            var details = el('details', 'q-explain');
            details.appendChild(el('summary', null, '查看解析'));
            var explainBody = el('div', 'explain-body');
            explainBody.appendChild(el('p', null,
                '你的作答：' + describeChosen(entry)));
            explainBody.appendChild(el('p', null,
                '正确答案：' + describeAnswer(entry)));
            explainBody.appendChild(el('p', null, '解析：' + entry.explain));
            details.appendChild(explainBody);
            cell.appendChild(details);
            detailRow.appendChild(cell);
            table.appendChild(detailRow);
        });

        document.getElementById('modal-mask').hidden = false;
    }

    async function gradeAll(auto) {
        if (!state.started) {
            window.alert('请先点击“开始考试”。');

            return;
        }
        if (state.submitted) {
            renderResult();

            return;
        }
        var unanswered = allQuestions.length - answeredCount();
        var message = unanswered > 0
            ? '还有 ' + unanswered + ' 题未作答，确定交卷评分吗？'
            : '确定交卷评分吗？';
        if (!auto && !window.confirm(message)) {
            return;
        }

        try {
            var result = await postJson('/api/grade', {
                seed: state.seed,
                answers: state.answers
            });
            state.graded = result;
            state.submitted = true;
            if (timerHandle) {
                window.clearInterval(timerHandle);
                timerHandle = null;
            }
            persist();
            renderPaper();
            renderResult();
        } catch (error) {
            window.alert('评分失败：' + error.message);
        }
    }

    async function saveRecord() {
        if (!state.graded) {
            window.alert('请先交卷评分，再保存答题记录。');

            return;
        }
        try {
            var result = await postJson('/api/save', {
                paperId: String(state.seed),
                paperTitle: state.paper.title + '（种子 ' + state.seed + '）',
                savedAt: new Date().toISOString().slice(0, 19).replace('T', ' '),
                elapsedText: formatTime((state.paper.duration_minutes * 60)
                    - (state.secondsLeft || 0)),
                seed: state.seed,
                score: state.graded.score,
                totalScore: state.graded.total_score,
                details: state.graded.results.map(function (entry) {
                    return {
                        id: entry.id,
                        no: entry.no,
                        section: entry.section,
                        kp: entry.kp || '',
                        score: entry.score,
                        full: entry.full,
                        chosen: entry.chosen === undefined ? null : entry.chosen,
                        answer: entry.answer,
                        answer_text: entry.answer_text,
                        submitted: entry.submitted || null
                    };
                })
            });
            document.getElementById('save-hint').textContent =
                '已保存：' + result.file;
            window.alert('答题记录已保存到 records 目录：\n' + result.file);
        } catch (error) {
            window.alert('保存失败：' + error.message);
        }
    }

    /* ---------------- 服务状态 ---------------- */

    async function checkService() {
        var box = document.getElementById('service-state');
        try {
            var health = await getJson('/api/health');
            state.service = 'online';
            state.bank = health.bank;
            box.className = 'service-state online';
            box.querySelector('.text').textContent =
                '本地判分服务 · 题库 ' + health.bankTotal + ' 题';
        } catch (error) {
            state.service = 'offline';
            box.className = 'service-state offline';
            box.querySelector('.text').textContent = '本地判分服务离线';
        }
    }

    /* ---------------- 初始化 ---------------- */

    async function fetchPaper() {
        var url = state.seed !== null
            ? '/api/paper?seed=' + encodeURIComponent(state.seed)
            : '/api/paper';
        var data = await getJson(url);
        state.seed = data.seed;
        state.paper = data.paper;
        state.bank = data.bank;
        collectQuestions();
        persist();
    }

    async function init() {
        restore();
        checkService();
        try {
            await fetchPaper();
        } catch (error) {
            var body = document.getElementById('paper-body');
            body.innerHTML = '';
            var panel = el('section', 'panel landing');
            panel.appendChild(el('h2', null, '无法连接本地判分服务'));
            panel.appendChild(el('p', 'meta',
                '请先运行 start.bat（Windows）或 ./start.sh 启动服务，'
                + '然后刷新本页。'));
            body.appendChild(panel);

            return;
        }

        document.getElementById('paper-title').textContent = state.paper.title;
        document.getElementById('paper-subtitle').textContent = state.paper.course;

        if (state.started) {
            renderPaper();
            updateTimer();
            if (!state.submitted) {
                startTimer();
                refreshLiveScore();
            }
            if (state.graded && state.submitted) {
                renderResult();
            }
        } else {
            renderLanding();
            updateTimer();
        }
    }

    /* ---------------- 事件绑定 ---------------- */

    document.getElementById('btn-submit').addEventListener('click', function () {
        gradeAll(false);
    });
    document.getElementById('btn-save').addEventListener('click', saveRecord);
    document.getElementById('btn-save-in-modal').addEventListener('click',
        saveRecord);
    document.getElementById('btn-newpaper').addEventListener('click', function () {
        if (window.confirm('将重新抽一套试卷并清空全部作答，确定吗？')) {
            clearStorage();
            window.location.reload();
        }
    });
    document.getElementById('btn-close-modal').addEventListener('click',
        function () {
            document.getElementById('modal-mask').hidden = true;
        });
    document.getElementById('btn-close-modal2').addEventListener('click',
        function () {
            document.getElementById('modal-mask').hidden = true;
        });

    /* ---------------- 测试钩子 ---------------- */

    window.__cvExam = {
        state: state,
        getQuestions: function () {
            return allQuestions;
        },
        startExam: startExam,
        refreshLiveScore: refreshLiveScore,
        gradeAll: gradeAll,
        liveTotals: liveTotals
    };

    window.__cvReady = init();
}());
