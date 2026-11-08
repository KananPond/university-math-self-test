# -*- coding: utf-8 -*-
"""
文件名：checker.py
作者：ZCode（GLM）
日期：2026-10-02
版本：1.0
文件说明：
1. 服务端判分内核：把前端提交的数值 / 矩阵作答解析成精确分数后比对。
2. 与模板中 gcc 编译判分（judge.py）对应：这里不需要编译，
   线性代数的判分核心是“分数精确比较 + 矩阵逐元素比较 + 语义判分”。
3. 全部运算走 bank/linalg_ref.py 的 Fraction 实现，无浮点误差。
"""

import sys
import os
from fractions import Fraction

WEB_EXAM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(WEB_EXAM_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from bank import linalg_ref as la  # noqa: E402

# 数值作答允许的相对误差（十进制写法与分数严格相等时误差为 0）
EPSILON = Fraction(1, 10 ** 9)


def near_equal(left, right):
    """判断两个分数是否相等（留一个极小的数值容差）。"""
    return abs(left - right) <= EPSILON


def grade_choice(question, chosen):
    """选择题判分。"""
    answered = isinstance(chosen, int) and 0 <= chosen < len(question["options"])
    right = answered and chosen == question["answer"]

    return {
        "answered": answered,
        "right": right,
        "score": question["score"] if right else 0,
        "answer": question["answer"],
        "answer_text": "ABCD"[question["answer"]],
        "chosen": chosen if answered else None,
    }


def grade_judge(question, chosen):
    """判断题判分。"""
    answered = isinstance(chosen, bool)
    right = answered and chosen == question["answer"]

    return {
        "answered": answered,
        "right": right,
        "score": question["score"] if right else 0,
        "answer": question["answer"],
        "answer_text": "对" if question["answer"] else "错",
        "chosen": chosen if answered else None,
    }


def grade_number(question, text):
    """填空题判分：作答解析成精确分数后与标准答案比对。"""
    submitted = la.to_frac(text) if isinstance(text, str) else None
    expected = la.to_frac(question["answer"])
    answered = submitted is not None
    right = answered and near_equal(submitted, expected)

    return {
        "answered": answered,
        "right": right,
        "score": question["score"] if right else 0,
        "answer": question["answer"],
        "answer_text": question["answer"],
        "submitted": str(submitted) if submitted is not None else None,
        "chosen": text if isinstance(text, str) else None,
    }


def parse_submission_matrix(payload):
    """把前端提交的矩阵作答 {rows, cols, data} 解析成分数矩阵。"""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None

    return la.parse_matrix(data)


def matrix_is_zero(matrix):
    """判断矩阵是否全零。"""
    return all(value == 0 for row in matrix for value in row)


def semantic_eigvec_score(question, submitted):
    """特征向量语义判分：Av = λv 且 v ≠ 0 即满分，否则 0 分。"""
    spec = question["grading"]
    matrix = (question.get("matrices") or {}).get(spec["matrix"])
    if matrix is None:
        return 0.0
    A = la.parse_matrix(matrix["data"])
    eigen = la.to_frac(spec["eigen"])
    if A is None or eigen is None:
        return 0.0

    if la.mat_vec(A, [row[0] for row in submitted]) \
            == [[eigen * row[0]] for row in submitted] \
            and not matrix_is_zero(submitted):
        return 1.0

    return 0.0


def semantic_null_basis_score(question, submitted):
    """基础解系语义判分：按列检查非零解与线性无关。"""
    spec = question["grading"]
    matrix = (question.get("matrices") or {}).get(spec["matrix"])
    if matrix is None:
        return 0.0
    A = la.parse_matrix(matrix["data"])
    if A is None:
        return 0.0

    _, unknowns = la.dims(A)
    free = unknowns - la.rank(A)
    if la.dims(submitted)[0] != unknowns:
        return 0.0

    vectors = []
    for c in range(la.dims(submitted)[1]):
        vector = [submitted[i][c] for i in range(unknowns)]
        if matrix_is_zero([vector]):
            continue
        product = la.mat_vec(A, vector)
        if any(value != 0 for row in product for value in row):
            continue
        vectors.append(vector)

    if not vectors:
        return 0.0

    # 合法列按份额给分：与已收集向量线性无关的给满份额，
    # 重复（相关）的合法解给一半份额；集齐 free 个无关向量即满分
    share = 1.0 / free if free else 0.0
    score = 0.0
    independent = []
    for vector in vectors:
        if not independent:
            score += share
            independent.append(vector)
            continue
        combined = [list(row) for row in zip(*(independent + [vector]))]
        if la.rank(combined) > len(independent):
            score += share
            independent.append(vector)
        else:
            score += share / 2

    if free > 0 and len(independent) == free:
        return 1.0

    return min(1.0, score)


def semantic_score(question, submitted):
    """按题目声明的语义规则给出 0~1 的得分率，规则不适用返回 None。"""
    grading = question.get("grading")
    if not grading:
        return None

    if grading.get("kind") == "eigvec":
        return semantic_eigvec_score(question, submitted)

    if grading.get("kind") == "null_basis":
        return semantic_null_basis_score(question, submitted)

    return None


def grade_matrix(question, payload):
    """计算题判分：默认逐元素比例给分，带 grading 的题目语义判分。"""
    submitted = parse_submission_matrix(payload)
    expected = la.parse_matrix(question["answer"]["data"])
    rows, cols = question["rows"], question["cols"]

    answered = submitted is not None
    if submitted is not None:
        actual_shape = la.dims(submitted)
        answered = actual_shape == (rows, cols)
        if not answered:
            submitted = None

    if not answered:
        return {
            "answered": False,
            "right": False,
            "score": 0,
            "correct": 0,
            "total": rows * cols,
            "answer": question["answer"],
            "answer_text": None,
            "submitted": None,
        }

    # 语义判分（特征向量 / 基础解系等答案不唯一的题）
    ratio = semantic_score(question, submitted)
    if ratio is None:
        correct = 0
        for i in range(rows):
            for j in range(cols):
                if near_equal(submitted[i][j], expected[i][j]):
                    correct += 1
        ratio = correct / float(rows * cols)

    score = int(question["score"] * ratio + 0.5)

    return {
        "answered": True,
        "right": score == question["score"],
        "score": score,
        "correct": round(question["score"] * ratio, 2),
        "total": rows * cols,
        "answer": question["answer"],
        "answer_text": None,
        "submitted": {"rows": rows, "cols": cols,
                      "data": [[str(v) for v in row] for row in submitted]},
    }


def score_objective(paper, answers):
    """实时统计全部作答的当前得分（只返回总分，不下发答案）。

    线性代数试卷没有需要编译的代码题，四类题目都是客观题，
    因此实时得分可以覆盖整张试卷。
    """
    choice_answers = answers.get("choice") or {}
    judge_answers = answers.get("judge") or {}
    fill_answers = answers.get("fill") or {}
    calc_answers = answers.get("calc") or {}

    score = 0
    full = 0
    answered = 0
    total = 0

    for section in paper["sections"]:
        for question in section["questions"]:
            question_id = question["id"]
            total += 1
            full += question["score"]

            if section["type"] == "choice":
                chosen = choice_answers.get(question_id)
                valid = isinstance(chosen, int) \
                    and 0 <= chosen < len(question["options"])
            elif section["type"] == "judge":
                chosen = judge_answers.get(question_id)
                valid = isinstance(chosen, bool)
            elif section["mode"] == "matrix":
                chosen = calc_answers.get(question_id)
                valid = isinstance(chosen, dict) \
                    and la.parse_matrix(
                        (chosen.get("data") or [])) is not None
            else:
                chosen = fill_answers.get(question_id)
                valid = isinstance(chosen, str) \
                    and la.to_frac(chosen) is not None

            if not valid:
                continue

            answered += 1
            if section["type"] == "choice":
                if chosen == question["answer"]:
                    score += question["score"]
            elif section["type"] == "judge":
                if chosen == question["answer"]:
                    score += question["score"]
            elif section["mode"] == "matrix":
                outcome = grade_matrix(question, chosen)
                score += outcome["score"]
            else:
                submitted = la.to_frac(chosen)
                expected = la.to_frac(question["answer"])
                if submitted is not None and near_equal(submitted, expected):
                    score += question["score"]

    return {
        "score": score,
        "full": full,
        "answered": answered,
        "total": total,
    }
