# -*- coding: utf-8 -*-
"""
文件名：checker.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 服务端判分内核：把前端提交的作答解析成精确复数 / 精确实数后比对。
2. 与模板中 gcc 编译判分（judge.py）对应：这里不需要编译，
   复变函数的判分核心是「精确代数比较 + 逐空比例给分」。
3. 全部运算走 bank/complex_ref.py 的 Fraction 实现，无浮点误差。
"""

import os
import sys

WEB_EXAM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(WEB_EXAM_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from bank import complex_ref as cr  # noqa: E402

# 判分不设容差：所有比较都是有理数 / 根式 / π 的精确比较
ANSWER_TYPES = ("number", "complex", "angle")


def answer_type_of(question):
    """取题目的答案类型，缺省为 number。"""
    answer_type = question.get("answer_type") or "number"
    if answer_type not in ANSWER_TYPES:
        return "number"

    return answer_type


def parse_submission(text, answer_type):
    """把作答文本解析成可比较的值，非法返回 None。"""
    if not isinstance(text, str):
        return None
    cleaned = text.strip()
    if not cleaned:
        return None

    if answer_type == "complex":
        return cr.parse_complex(cleaned)
    if answer_type == "angle":
        return cr.parse_angle(cleaned)

    return cr.parse_real(cleaned)


def expected_values(answer, answer_type):
    """把标准答案（字符串或字符串列表）解析成一组可比较的值。"""
    if isinstance(answer, list):
        items = answer
    else:
        items = [answer]

    values = []
    for item in items:
        value = parse_submission(item, answer_type)
        if value is not None:
            values.append(value)

    return values


def values_equal(left, right, answer_type):
    """两个解析结果是否精确相等。"""
    if left is None or right is None:
        return False
    if answer_type == "complex":
        return cr.complex_equal(left, right)

    return left == right


def matches_any(submitted, expected, answer_type):
    """作答是否命中标准答案中的任意一项。"""
    for value in expected:
        if values_equal(submitted, value, answer_type):
            return True

    return False


# --------------------------------------------------------------------------
# 客观题
# --------------------------------------------------------------------------

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
    """填空题判分：作答解析成精确值后与标准答案比对。"""
    answer_type = answer_type_of(question)
    expected = expected_values(question["answer"], answer_type)
    submitted = parse_submission(text, answer_type)
    answered = submitted is not None
    right = answered and matches_any(submitted, expected, answer_type)

    return {
        "answered": answered,
        "right": right,
        "score": question["score"] if right else 0,
        "answer": question["answer"],
        "answer_text": question["answer"] if isinstance(question["answer"], str)
        else "、".join(question["answer"]),
        "submitted": text if answered else None,
        "chosen": text if isinstance(text, str) else None,
    }


# --------------------------------------------------------------------------
# 计算题：逐空精确比对，按正确空数比例给分
# --------------------------------------------------------------------------

def blank_list(question):
    """取题目的小问列表。"""
    blanks = question.get("blanks") or []

    return blanks


def grade_blanks(question, payload):
    """计算题判分：逐空精确比对，按答对小问比例给分。"""
    blanks = blank_list(question)
    total = len(blanks)
    if total == 0:
        return {
            "answered": False,
            "right": False,
            "score": 0,
            "correct": 0,
            "total": 0,
            "answer": [],
            "answer_text": None,
            "submitted": None,
        }

    submitted_map = {}
    if isinstance(payload, dict):
        # 兼容两种传法：{"blanks": {...}} 或直接给 {"0": "...", ...}
        source = payload.get("blanks")
        if not isinstance(source, dict):
            source = payload
        for key, value in source.items():
            submitted_map[str(key)] = value

    correct = 0
    details = []
    for index, blank in enumerate(blanks):
        answer_type = blank.get("answer_type") or "number"
        expected = expected_values(blank.get("answer"), answer_type)
        text = submitted_map.get(str(index))
        value = parse_submission(text, answer_type)
        hit = value is not None and matches_any(value, expected, answer_type)
        if hit:
            correct += 1
        details.append({
            "label": blank.get("label", "第 %d 空" % (index + 1)),
            "answered": value is not None,
            "right": hit,
            "answer": blank.get("answer"),
            "submitted": text if isinstance(text, str) else None,
        })

    ratio = correct / float(total)
    score = int(question["score"] * ratio + 0.5)
    answered = any(item["answered"] for item in details)

    return {
        "answered": answered,
        "right": score == question["score"],
        "score": score,
        "correct": correct,
        "total": total,
        "answer": [{"label": item["label"], "answer": item["answer"]}
                   for item in details],
        "answer_text": None,
        "submitted": details,
    }


# --------------------------------------------------------------------------
# 闪电训练：单题即时判定
# --------------------------------------------------------------------------

def check_single(item, response):
    """闪电训练的单题判定。

    item 需要提供 answer / answer_type（数值题）或 answer（选项题）。
    返回正确与否、标准答案文本与解析。
    """
    kind = item.get("kind") or "number"

    if kind == "choice":
        chosen = response if isinstance(response, int) else None
        right = chosen == item["answer"]
        expected_text = item.get("answer_text") or ""
        return {
            "correct": right,
            "answered": chosen is not None,
            "expected": expected_text,
            "explain": item.get("explain", ""),
            "figure": item.get("figure"),
        }

    if kind == "judge":
        chosen = response if isinstance(response, bool) else None
        right = chosen == item["answer"]
        return {
            "correct": right,
            "answered": chosen is not None,
            "expected": "对" if item["answer"] else "错",
            "explain": item.get("explain", ""),
            "figure": item.get("figure"),
        }

    if kind == "blanks":
        blanks = item.get("blanks") or []
        submitted_map = response if isinstance(response, dict) else {}
        details = []
        correct = 0
        for index, blank in enumerate(blanks):
            answer_type = blank.get("answer_type") or "number"
            expected = expected_values(blank.get("answer"), answer_type)
            text = submitted_map.get(str(index))
            value = parse_submission(text, answer_type)
            hit = value is not None and matches_any(value, expected, answer_type)
            if hit:
                correct += 1
            details.append({
                "label": blank.get("label", "第 %d 空" % (index + 1)),
                "answered": value is not None,
                "right": hit,
                "answer": blank.get("answer"),
                "submitted": text if isinstance(text, str) else None,
            })

        total = len(blanks)
        return {
            "correct": total > 0 and correct == total,
            "partial": correct,
            "total": total,
            "answered": any(item["answered"] for item in details),
            "expected": "；".join(
                "%s = %s" % (item["label"], item["answer"]) for item in details),
            "details": details,
            "explain": item.get("explain", ""),
            "figure": item.get("figure"),
        }

    answer_type = item.get("answer_type") or "number"
    expected = expected_values(item.get("answer"), answer_type)
    submitted = parse_submission(response, answer_type)
    right = submitted is not None and matches_any(submitted, expected, answer_type)
    answer = item.get("answer")
    if isinstance(answer, list):
        expected_text = " 或 ".join(answer)
    else:
        expected_text = answer

    return {
        "correct": right,
        "answered": submitted is not None,
        "expected": expected_text,
        "explain": item.get("explain", ""),
        "figure": item.get("figure"),
    }


# --------------------------------------------------------------------------
# 实时得分
# --------------------------------------------------------------------------

def score_objective(paper, answers):
    """实时统计全部作答的当前得分（只返回总分，不下发答案）。

    复变函数试卷没有需要编译的代码题，四类题目都是客观题，
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
            elif section["mode"] == "blanks":
                chosen = calc_answers.get(question_id)
                valid = isinstance(chosen, dict) \
                    and isinstance(chosen.get("blanks"), dict)
            else:
                chosen = fill_answers.get(question_id)
                valid = isinstance(chosen, str) \
                    and parse_submission(chosen,
                                         answer_type_of(question)) is not None

            if not valid:
                continue

            answered += 1
            if section["type"] == "choice":
                if chosen == question["answer"]:
                    score += question["score"]
            elif section["type"] == "judge":
                if chosen == question["answer"]:
                    score += question["score"]
            elif section["mode"] == "blanks":
                outcome = grade_blanks(question, chosen.get("blanks"))
                score += outcome["score"]
            else:
                outcome = grade_number(question, chosen)
                score += outcome["score"]

    return {
        "score": score,
        "full": full,
        "answered": answered,
        "total": total,
    }
