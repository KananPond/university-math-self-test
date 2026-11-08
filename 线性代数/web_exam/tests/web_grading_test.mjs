/* ==========================================================================
 * 线性代数考试模拟系统 · 端到端测试
 * 作者：ZCode（GLM）    日期：2026-10-02    版本：1.0
 *
 * 说明：
 * 1. 用最小的 DOM 替身加载真实的 static/app.js，不改动被测代码逻辑。
 * 2. 试卷由服务端按种子抽取，判分走真实 HTTP 接口（分数精确比对）。
 * 3. 标准答案由 tests/answer_key.py 提供（前端拿不到，这里只用于测试）。
 * 4. 用法：先启动 web_exam/server.py，再执行 node tests/web_grading_test.mjs
 * ========================================================================== */

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const STATIC_DIR = path.join(ROOT, 'static');
const RECORD_DIR = path.join(ROOT, 'records');
const BASE_URL = process.env.EXAM_BASE_URL || 'http://127.0.0.1:8766';

let failures = 0;

function check(name, condition, detail) {
    if (condition) {
        console.log(`  [通过] ${name}`);
    } else {
        failures += 1;
        console.log(`  [失败] ${name}${detail ? ' —— ' + detail : ''}`);
    }
}

/* ---------------- 最小 DOM 替身 ---------------- */

function makeFake() {
    const target = function fakeNode() {};
    return new Proxy(target, {
        get(node, prop) {
            if (prop === Symbol.toPrimitive) {
                return () => '';
            }
            if (prop === 'then') {
                return undefined;
            }
            if (prop === 'length') {
                return 0;
            }
            if (prop === 'value' || prop === 'textContent' || prop === 'innerHTML') {
                return '';
            }
            return makeFake();
        },
        set() {
            return true;
        },
        apply() {
            return makeFake();
        },
        has() {
            return true;
        }
    });
}

function installFakeDom(presetSeed) {
    const store = new Map();
    if (presetSeed !== undefined) {
        /* 预置种子：让前端 app.js 与测试 1 探测的试卷保持一致 */
        store.set('laexam_v1', JSON.stringify({ seed: presetSeed }));
    }

    globalThis.window = {
        setInterval: () => 0,
        clearInterval: () => {},
        setTimeout: () => 0,
        clearTimeout: () => {},
        confirm: () => true,
        alert: () => {},
        scrollTo: () => {},
        location: { reload: () => {} },
        devicePixelRatio: 1,
        MatrixView: undefined
    };
    globalThis.document = {
        body: makeFake(),
        createElement: () => makeFake(),
        createTextNode: () => makeFake(),
        getElementById: () => makeFake(),
        querySelector: () => makeFake(),
        querySelectorAll: () => [],
        addEventListener: () => {}
    };
    globalThis.localStorage = {
        getItem: (key) => (store.has(key) ? store.get(key) : null),
        setItem: (key, value) => store.set(key, String(value)),
        removeItem: (key) => store.delete(key)
    };

    const realFetch = globalThis.fetch;
    globalThis.fetch = (url, options) =>
        realFetch(url.startsWith('http') ? url : BASE_URL + url, options);
}

function loadFrontend(presetSeed) {
    installFakeDom(presetSeed);
    const matrixSource = fs.readFileSync(path.join(STATIC_DIR, 'matrix.js'), 'utf8');
    vm.runInThisContext(matrixSource, { filename: 'matrix.js' });
    const appSource = fs.readFileSync(path.join(STATIC_DIR, 'app.js'), 'utf8');
    vm.runInThisContext(appSource, { filename: 'app.js' });

    return globalThis.window;
}

/* ---------------- 取标准答案 ---------------- */

function fetchAnswerKey(seed) {
    const output = execFileSync('python',
        [path.join(HERE, 'answer_key.py'), String(seed)],
        { cwd: ROOT, encoding: 'utf8' });

    return JSON.parse(output);
}

async function fetchPaper(seed) {
    const url = seed === undefined
        ? `${BASE_URL}/api/paper`
        : `${BASE_URL}/api/paper?seed=${seed}`;
    const response = await fetch(url);

    return response.json();
}

async function postJson(url, payload) {
    const response = await fetch(`${BASE_URL}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    return response.json();
}

/* ---------------- 测试主体 ---------------- */

async function main() {
    const healthResponse = await fetch(`${BASE_URL}/api/health`).catch(() => null);
    const health = healthResponse ? await healthResponse.json() : null;
    if (!health || !health.ok) {
        console.error(`判分服务未启动（${BASE_URL}）。`);
        console.error('请先执行： python web_exam/server.py');
        process.exit(2);
    }

    console.log('【测试 1】服务端抽题与答案隔离');
    /* 选一个同时包含特征向量题（x_la_04）与基础解系题（x_la_07）的种子，
     * 保证语义判分分支一定被测到 */
    let seed = null;
    for (let candidate = 20261002; candidate < 20261002 + 60; candidate += 1) {
        const probe = await fetchPaper(candidate);
        const ids = probe.paper.sections.flatMap((s) => s.questions.map((q) => q.id));
        if (ids.includes('x_la_04') && ids.includes('x_la_07')) {
            seed = candidate;
            break;
        }
    }
    if (seed === null) {
        seed = 20261002;
    }
    const first = await fetchPaper(seed);
    const again = await fetchPaper(seed);
    const other = await fetchPaper(seed + 1);
    const idsOf = (data) => data.paper.sections
        .flatMap((s) => s.questions.map((q) => q.id));
    check('同一 seed 抽出的试卷完全一致',
        JSON.stringify(idsOf(first)) === JSON.stringify(idsOf(again)));
    check('不同 seed 抽出的试卷不同',
        JSON.stringify(idsOf(first)) !== JSON.stringify(idsOf(other)));
    check('每卷抽取 32 题', idsOf(first).length === 32,
        `实际 ${idsOf(first).length}`);
    check('题库规模为 62 题（20/16/16/10）',
        health.bank.choice === 20 && health.bank.judge === 16
        && health.bank.fill === 16 && health.bank.calc === 10,
        JSON.stringify(health.bank));
    const scoreSum = first.paper.sections
        .flatMap((s) => s.questions)
        .reduce((sum, q) => sum + q.score, 0);
    check('每卷合计 100 分', scoreSum === 100, `实际 ${scoreSum}`);

    const leaked = ['answer', 'explain', 'verify', 'grading', 'answer_text']
        .filter((field) => first.paper.sections.some((s) =>
            s.questions.some((q) => Object.prototype.hasOwnProperty.call(q, field))));
    check('下发数据不含答案、解析与判分规则',
        leaked.length === 0, `泄漏字段：${leaked.join(', ')}`);

    const calcQuestion = first.paper.sections
        .flatMap((s) => s.questions).find((q) => q.answer_type === 'matrix');
    check('计算题下发作答形状与矩阵数据',
        !!calcQuestion && typeof calcQuestion.rows === 'number'
        && typeof calcQuestion.cols === 'number'
        && !!calcQuestion.matrices,
        '缺少 rows/cols/matrices');
    check('选择题携带图形矩阵数据（题面可视化）',
        first.paper.sections.some((s) => s.type === 'choice'
            && s.questions.some((q) => !!q.matrices)));

    console.log('【测试 2】加载真实 app.js 并渲染整卷');
    const frontWindow = loadFrontend(seed);
    await frontWindow.__laReady;
    const internals = frontWindow.__laExam;
    const state = internals.state;
    check('app.js 拉取到试卷', !!state.paper);
    check('前端题量为 32 题', internals.getQuestions().length === 32,
        `实际 ${internals.getQuestions().length}`);
    check('前端记录了抽题种子', typeof state.seed === 'number');

    console.log('【测试 2b】开考前处于待开始状态，点击按钮后才计时');
    check('初始状态为未开始',
        state.started === false && state.submitted === false,
        `started=${state.started} submitted=${state.submitted}`);
    internals.startExam();
    check('点击“开始考试”后进入考试状态', state.started === true);
    check('开始考试后倒计时初始化为 120 分钟',
        state.secondsLeft === state.paper.duration_minutes * 60,
        `实际 ${state.secondsLeft}`);
    check('未交卷', state.submitted === false);

    const key = fetchAnswerKey(state.seed);
    const questions = internals.getQuestions();
    check('标准答案覆盖全部 32 题',
        Object.keys(key.choice).length + Object.keys(key.judge).length
        + Object.keys(key.fill).length + Object.keys(key.calc).length === 32);

    console.log('【测试 3】实时得分：全卷客观题作答后即满分');
    state.answers.choice = { ...key.choice };
    state.answers.judge = { ...key.judge };
    state.answers.fill = { ...key.fill };
    state.answers.calc = { ...key.calc };
    await internals.refreshLiveScore();
    check('全部答对后实时得分为 100',
        state.live && state.live.score === 100,
        `实际 ${state.live && state.live.score}`);
    check('实时统计覆盖全部 32 题',
        state.live && state.live.total === 32 && state.live.answered === 32);

    state.answers.choice = {};
    state.answers.judge = {};
    state.answers.fill = {};
    state.answers.calc = {};
    await internals.refreshLiveScore();
    check('清空作答后实时得分归零',
        state.live && state.live.score === 0,
        `实际 ${state.live && state.live.score}`);

    console.log('【测试 4】交卷判分：满分与零分');
    state.answers.choice = { ...key.choice };
    state.answers.judge = { ...key.judge };
    state.answers.fill = { ...key.fill };
    state.answers.calc = { ...key.calc };
    await internals.gradeAll();
    check('按标准答案交卷得 100 分', state.graded.score === 100,
        `实际 ${state.graded.score}`);
    check('交卷后进入已交卷状态',
        state.submitted === true && state.graded.results.length === 32);
    check('判分结果携带逐题解析',
        state.graded.results.every((r) => typeof r.explain === 'string'
            && r.explain.length > 0));

    console.log('【测试 5】分数 / 矩阵作答的判分细节');
    const wrongSubmission = {
        seed: state.seed,
        answers: {
            choice: Object.fromEntries(Object.keys(key.choice)
                .map((id) => [id, (key.choice[id] + 1) % 4])),
            judge: Object.fromEntries(Object.keys(key.judge)
                .map((id) => [id, !key.judge[id]])),
            fill: Object.fromEntries(Object.keys(key.fill)
                .map((id) => [id, '123456'])),
            /* 逐格不同值：保证不与任何标准答案相符，
             * 也不是特征向量（如 (t,t) 对 [[3,1],[1,3]] 恰是 λ=4 的特征向量） */
            calc: Object.fromEntries(Object.keys(key.calc).map((id) => {
                const shape = key.calc[id];
                return [id, { rows: shape.rows, cols: shape.cols,
                    data: shape.data.map((row, r) =>
                        row.map((cell, c) => String(7 + r * shape.cols + c))) }];
            }))
        }
    };
    const wrongResult = await postJson('/api/grade', wrongSubmission);
    check('全部答错时得 0 分', wrongResult.score === 0,
        `实际 ${wrongResult.score}`);

    const decimalAnswers = { ...state.answers.calc };
    let decimalTarget = null;
    for (const [id, shape] of Object.entries(key.calc)) {
        if (shape.data.some((row) => row.some((cell) => cell.includes('/')))) {
            decimalTarget = id;
            decimalAnswers[id] = {
                rows: shape.rows,
                cols: shape.cols,
                data: shape.data.map((row) => row.map((cell) => {
                    if (!cell.includes('/')) {
                        return cell;
                    }
                    const [top, bottom] = cell.split('/');
                    return String(Number(top) / Number(bottom));
                }))
            };
            break;
        }
    }
    if (decimalTarget) {
        const decimalResult = await postJson('/api/grade', {
            seed: state.seed,
            answers: {
                choice: key.choice, judge: key.judge, fill: key.fill,
                calc: decimalAnswers
            }
        });
        const target = decimalResult.results.find((r) => r.id === decimalTarget);
        check(`分数答案可用等值小数作答（${decimalTarget} 得满分）`,
            target.score === target.full,
            `实际 ${target.score}/${target.full}`);
        check('等值小数作答不影响总分 100', decimalResult.score === 100,
            `实际 ${decimalResult.score}`);
    }

    const partialEntry = wrongSubmission;
    const partialId = Object.keys(key.calc).find((id) => {
        const shape = key.calc[id];
        return shape.rows * shape.cols >= 4
            && !(key.calc[id].data.some((row) =>
                row.some((cell) => cell.includes('/'))));
    });
    if (partialId) {
        const shape = key.calc[partialId];
        const data = shape.data.map((row, r) => row.map((cell, c) =>
            r === 0 && c === 0 ? cell : '999'));
        partialEntry.answers.calc[partialId] = {
            rows: shape.rows, cols: shape.cols, data
        };
        partialEntry.answers.choice = key.choice;
        partialEntry.answers.judge = key.judge;
        partialEntry.answers.fill = key.fill;
        const partialResult = await postJson('/api/grade', partialEntry);
        const target = partialResult.results.find((r) => r.id === partialId);
        const entries = shape.rows * shape.cols;
        const expected = Math.round(5 * 1 / entries);
        check(`矩阵题按正确元素比例给分（${partialId} 对 1/${entries} 元素）`,
            target.score === expected,
            `实际 ${target.score}，期望 ${expected}`);
    }

    console.log('【测试 6】语义判分：特征向量与基础解系不唯一');
    if (idsOf(first).includes('x_la_04')) {
        const multipleResult = await postJson('/api/grade', {
            seed: state.seed,
            answers: {
                choice: key.choice, judge: key.judge, fill: key.fill,
                calc: {
                    ...state.answers.calc,
                    x_la_04: { rows: 2, cols: 1, data: [['-3'], ['-3']] }
                }
            }
        });
        const target = multipleResult.results.find((r) => r.id === 'x_la_04');
        check('特征向量非零倍数判满分',
            target.score === target.full, `实际 ${target.score}/${target.full}`);
    }
    if (idsOf(first).includes('x_la_07')) {
        const basisResult = await postJson('/api/grade', {
            seed: state.seed,
            answers: {
                choice: key.choice, judge: key.judge, fill: key.fill,
                calc: {
                    ...state.answers.calc,
                    x_la_07: { rows: 4, cols: 2, data:
                        [['1', '5'], ['-2', '-8'], ['1', '1'], ['0', '2']] }
                }
            }
        });
        const target = basisResult.results.find((r) => r.id === 'x_la_07');
        check('另一组合法基础解系判满分',
            target.score === target.full, `实际 ${target.score}/${target.full}`);

        const badBasis = await postJson('/api/grade', {
            seed: state.seed,
            answers: {
                choice: key.choice, judge: key.judge, fill: key.fill,
                calc: {
                    ...state.answers.calc,
                    x_la_07: { rows: 4, cols: 2, data:
                        [['1', '2'], ['-2', '-4'], ['1', '2'], ['0', '0']] }
                }
            }
        });
        const badTarget = badBasis.results.find((r) => r.id === 'x_la_07');
        check('相关列（重复向量）不得满分',
            badTarget.score < badTarget.full,
            `实际 ${badTarget.score}/${badTarget.full}`);
    }

    console.log('【测试 7】实时得分接口不泄露答案');
    const scoreResponse = await fetch(`${BASE_URL}/api/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seed: state.seed, answers: state.answers })
    });
    const scoreData = await scoreResponse.json();
    const scoreKeys = Object.keys(scoreData).sort();
    check('实时得分只返回总分与进度',
        JSON.stringify(scoreKeys) === JSON.stringify(
            ['answered', 'full', 'ok', 'score', 'total']),
        JSON.stringify(scoreKeys));

    console.log('【测试 8】保存答题记录');
    const before = fs.existsSync(RECORD_DIR)
        ? fs.readdirSync(RECORD_DIR).length : 0;
    const saveResult = await postJson('/api/save', {
        paperId: String(state.seed),
        paperTitle: '线性代数考试模拟卷（端到端测试）',
        savedAt: '2026-10-02 12:00:00',
        elapsedText: '12:00',
        seed: state.seed,
        score: state.graded.score,
        totalScore: state.graded.total_score,
        details: state.graded.results.map((entry) => ({
            id: entry.id,
            no: entry.no,
            section: entry.section,
            score: entry.score,
            full: entry.full,
            chosen: entry.chosen === undefined ? null : entry.chosen,
            answer: entry.answer,
            answer_text: entry.answer_text,
            submitted: entry.submitted || null
        }))
    });
    check('保存记录返回 ok', saveResult.ok === true, JSON.stringify(saveResult));
    const after = fs.readdirSync(RECORD_DIR).length;
    check('记录文件写入 records 目录（json + markdown）', after === before + 2,
        `前 ${before} 后 ${after}`);
    const savedPath = path.join(RECORD_DIR, saveResult.file);
    const savedRecord = JSON.parse(fs.readFileSync(savedPath, 'utf8'));
    check('记录包含逐题明细与种子',
        savedRecord.seed === state.seed && savedRecord.details.length === 32);

    console.log('');
    if (failures > 0) {
        console.error(`端到端测试未通过，共 ${failures} 项失败。`);
        process.exit(1);
    }
    console.log('端到端测试全部通过。');
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
