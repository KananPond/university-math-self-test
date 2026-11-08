# -*- coding: utf-8 -*-
"""
文件名：grader.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 服务端判分编排：按种子抽取试卷、剥离答案后下发，回收作答并评分。
2. 标准答案、解析与复核规则都不下发给前端，避免直接看答案。
3. 数值 / 复数作答的比对规则在 checker.py 中实现。
"""

import os
import sys

WEB_EXAM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(WEB_EXAM_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from bank import BANK, PAPER_META, draw_paper  # noqa: E402
import checker  # noqa: E402

# 下发给前端时允许保留的字段，其余（答案、解析、复核规则）一律剥离
PUBLIC_FIELDS = (
    "id", "no", "score", "stem", "options", "figures",
    "answer_type", "kp",
)


def load_paper(seed):
    """按种子抽取试卷（含答案与解析，仅限服务端使用）。"""
    return draw_paper(int(seed), BANK)


def public_question(question):
    """剥离单题的答案与解析。"""
    item = {}
    for field in PUBLIC_FIELDS:
        if field in question:
            item[field] = question[field]

    blanks = question.get("blanks")
    if blanks:
        item["blanks"] = [
            {"label": blank.get("label", "第 %d 空" % (index + 1)),
             "answer_type": blank.get("answer_type") or "number"}
            for index, blank in enumerate(blanks)
        ]

    return item


def public_paper(paper):
    """剥离答案与解析，生成可以下发给前端的试卷数据。"""
    sections = []
    for section in paper["sections"]:
        questions = [public_question(question) for question in section["questions"]]
        sections.append({
            "id": section["id"],
            "type": section["type"],
            "mode": section["mode"],
            "title": section["title"],
            "desc": section["desc"],
            "score": section["score"],
            "questions": questions,
        })

    return {
        "id": paper["id"],
        "title": paper["title"],
        "course": paper["course"],
        "total_score": paper["total_score"],
        "duration_minutes": paper["duration_minutes"],
        "instructions": paper["instructions"],
        "seed": paper["seed"],
        "sections": sections,
    }


def find_question(paper, question_id):
    """在试卷中按题号查找题目。"""
    for section in paper["sections"]:
        for question in section["questions"]:
            if question["id"] == question_id:
                return section, question

    return None, None


def normalize_answers(raw):
    """规范化前端提交的作答内容。"""
    if not isinstance(raw, dict):
        return {"choice": {}, "judge": {}, "fill": {}, "calc": {}}

    choice = {}
    for key, value in (raw.get("choice") or {}).items():
        if isinstance(value, int) and not isinstance(value, bool):
            choice[str(key)] = value

    judge = {}
    for key, value in (raw.get("judge") or {}).items():
        if isinstance(value, bool):
            judge[str(key)] = value

    fill = {}
    for key, value in (raw.get("fill") or {}).items():
        if isinstance(value, str):
            fill[str(key)] = value[:200]

    calc = {}
    for key, value in (raw.get("calc") or {}).items():
        if isinstance(value, dict) and isinstance(value.get("blanks"), dict):
            blanks = {}
            for index, text in value["blanks"].items():
                if isinstance(text, str):
                    blanks[str(index)] = text[:200]
            calc[str(key)] = {"blanks": blanks}

    return {"choice": choice, "judge": judge,
            "fill": fill, "calc": calc}


def grade_paper(paper, answers):
    """按题判分，返回总分与逐题结果。"""
    normalized = normalize_answers(answers)
    choice_answers = normalized["choice"]
    judge_answers = normalized["judge"]
    fill_answers = normalized["fill"]
    calc_answers = normalized["calc"]

    results = []
    total_score = 0

    for section in paper["sections"]:
        for question in section["questions"]:
            question_id = question["id"]
            full = question["score"]

            if section["type"] == "choice":
                outcome = checker.grade_choice(
                    question, choice_answers.get(question_id))
            elif section["type"] == "judge":
                outcome = checker.grade_judge(
                    question, judge_answers.get(question_id))
            elif section["mode"] == "blanks":
                outcome = checker.grade_blanks(
                    question, calc_answers.get(question_id))
            else:
                outcome = checker.grade_number(
                    question, fill_answers.get(question_id))

            total_score += outcome["score"]
            entry = {
                "id": question_id,
                "no": question["no"],
                "type": section["type"],
                "mode": section.get("mode"),
                "section": section["title"],
                "kp": question.get("kp"),
                "title": question["stem"][:60],
                "score": outcome["score"],
                "full": full,
                "answered": outcome["answered"],
                "right": outcome["right"],
                "explain": question["explain"],
                "answer": outcome["answer"],
                "answer_text": outcome.get("answer_text"),
                "chosen": outcome.get("chosen"),
            }
            for field in ("correct", "total", "submitted"):
                if field in outcome:
                    entry[field] = outcome[field]

            results.append(entry)

    return {
        "score": total_score,
        "total_score": paper["total_score"],
        "seed": paper["seed"],
        "results": results,
    }


def default_meta():
    """返回试卷元信息，供前端在抽题失败时兜底显示。"""
    return dict(PAPER_META)
