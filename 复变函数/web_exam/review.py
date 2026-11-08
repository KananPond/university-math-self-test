# -*- coding: utf-8 -*-
"""
文件名：review.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 考后复盘：读取 records/ 下最新的交卷记录（或指定记录），
   按抽题种子复原试卷，逐题生成错题精讲。
2. 精讲包含题面（复平面图解写成文字描述）、你的作答、正确答案、解析。
3. 用法： cd web_exam && python review.py [记录文件.json]
"""

import glob
import json
import os
import sys

WEB_EXAM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(WEB_EXAM_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from bank import draw_paper, BANK  # noqa: E402
from complex_text import render_text  # noqa: E402

RECORD_DIR = os.path.join(WEB_EXAM_DIR, "records")


def latest_record():
    """找到 records 目录下最新的一份交卷记录。"""
    files = sorted(glob.glob(os.path.join(RECORD_DIR, "*.json")))
    if not files:
        return None

    return files[-1]


def answer_markdown(question, section_type):
    """标准答案的 Markdown 文本。"""
    if section_type == "choice":
        return "`%s`（%s）" % ("ABCD"[question["answer"]],
                               question["options"][question["answer"]])
    if section_type == "judge":
        return "对" if question["answer"] else "错"
    if question.get("answer_type") == "complex":
        answer = question["answer"]
        if isinstance(answer, list):
            return " 或 ".join("`%s`" % item for item in answer)

        return "`%s`" % answer
    if question.get("answer_type") == "angle":
        answer = question["answer"]
        if isinstance(answer, list):
            return " 或 ".join("`%s`" % item for item in answer)

        return "`%s`" % answer

    return "`%s`" % question["answer"]


def calc_answer_markdown(question):
    """计算题的标准答案（逐小问）。"""
    pieces = []
    for blank in question.get("blanks") or []:
        answer = blank.get("answer")
        if isinstance(answer, list):
            text = " 或 ".join("`%s`" % item for item in answer)
        else:
            text = "`%s`" % answer
        pieces.append("%s = %s" % (blank.get("label") or "小问", text))

    return "；".join(pieces)


def submitted_markdown(detail):
    """学生作答的 Markdown 文本。"""
    submitted = detail.get("submitted")
    if isinstance(submitted, list):
        pieces = []
        for item in submitted:
            text = item.get("submitted") or "（空）"
            pieces.append("%s = %s" % (item.get("label") or "小问", text))

        return "；".join(pieces)

    if isinstance(detail.get("chosen"), str) and detail["chosen"]:
        return "`%s`" % detail["chosen"]
    if isinstance(detail.get("chosen"), bool):
        return "对" if detail["chosen"] else "错"
    if isinstance(detail.get("chosen"), int):
        return "选项 %s" % "ABCD"[detail["chosen"]]

    return "（未作答）"


def review_markdown(record):
    """由交卷记录生成错题精讲 Markdown。"""
    seed = record.get("seed")
    paper = draw_paper(seed, BANK)
    by_id = {}
    for section in paper["sections"]:
        for question in section["questions"]:
            by_id[question["id"]] = (section, question)

    details = record.get("details") or []
    wrong = [item for item in details
             if float(item.get("score", 0)) < float(item.get("full", 1))]

    lines = []
    lines.append("# %s · 错题精讲" % record.get("paperTitle", "模拟卷"))
    lines.append("")
    lines.append("- 交卷时间：%s" % record.get("savedAt", "未知"))
    lines.append("- 抽题种子：%s" % seed)
    lines.append("- 得分：%s / %s" % (record.get("score"),
                                      record.get("totalScore")))
    lines.append("- 错题数：%d / %d" % (len(wrong), len(details)))
    lines.append("")

    if not wrong:
        lines.append("本次模拟全部答对，继续保持！")
        lines.append("")
        return "\n".join(lines)

    for item in wrong:
        found = by_id.get(item.get("id"))
        if found is None:
            continue
        section, question = found
        lines.append("## %s（%s · %s，得分 %s / %s）"
                     % (item.get("no"), item.get("section"),
                        item.get("kp") or "-",
                        item.get("score"), item.get("full")))
        lines.append("")
        lines.append(render_text(question["stem"], question.get("figures")))
        lines.append("")
        if question.get("options"):
            for index, option in enumerate(question["options"]):
                lines.append("- %s. %s" % ("ABCD"[index],
                                           render_text(option,
                                                       question.get("figures"))))
            lines.append("")
        lines.append("**你的作答：**%s" % submitted_markdown(item))
        lines.append("")
        if section.get("mode") == "blanks":
            lines.append("**正确答案：**%s" % calc_answer_markdown(question))
        else:
            lines.append("**正确答案：**%s" % answer_markdown(question,
                                                              section["type"]))
        lines.append("")
        lines.append("> 解析：%s" % question["explain"])
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = latest_record()
        if path is None:
            print("records 目录下没有交卷记录。先在网页里交卷并"
                  "点击“保存答题记录”。")
            return 1

    with open(path, encoding="utf-8") as handle:
        record = json.load(handle)

    output = review_markdown(record)
    base = os.path.splitext(os.path.basename(path))[0]
    target = os.path.join(RECORD_DIR, "review_%s.md" % base)
    os.makedirs(RECORD_DIR, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(output)

    print("已生成错题精讲：%s" % target)

    return 0


if __name__ == "__main__":
    sys.exit(main())
