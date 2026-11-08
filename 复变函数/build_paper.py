# -*- coding: utf-8 -*-
"""
文件名：build_paper.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 由题库派生三份文档：paper.md 样卷、answer_key.md 参考答案与解析、
   bank_overview.md 题库总览。
2. 生成物不要手改，改题请改 bank/ 下的数据文件后重新运行本脚本。
3. 用法： cd 考试服务 && python build_paper.py [种子]
"""

import os
import sys

from bank import BANK, PAPER_META, DRAW_PLAN, draw_paper
from complex_text import render_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SEED = 20261108


def answer_text(question):
    """把一道题的标准答案转成可读文本。"""
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


def blank_text(blank):
    """计算题里一个小问的答案文本。"""
    answer = blank.get("answer")
    if isinstance(answer, list):
        return " 或 ".join("`%s`" % item for item in answer)

    return "`%s`" % answer


def choice_answer_text(question):
    """选择题答案：字母 + 选项内容。"""
    letters = "ABCD"

    return "`%s`（%s）" % (letters[question["answer"]],
                           question["options"][question["answer"]])


def judge_answer_text(question):
    """判断题答案文本。"""
    return "对" if question["answer"] else "错"


def write_file(name, content):
    """把生成物写入项目根目录，返回路径。"""
    path = os.path.join(BASE_DIR, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    print("已生成 %s" % name)

    return path


def build_paper_md(paper):
    """生成样卷正文。"""
    lines = []
    lines.append("# %s" % paper["title"])
    lines.append("")
    lines.append("- 抽题种子：%s（同一种子必得同一份卷）" % paper["seed"])
    lines.append("- 满分 %d 分，考试时间 %d 分钟"
                 % (paper["total_score"], paper["duration_minutes"]))
    lines.append("")
    lines.append("## 考生须知")
    lines.append("")
    for index, note in enumerate(paper["instructions"], start=1):
        lines.append("%d. %s" % (index, note))
    lines.append("")

    for section in paper["sections"]:
        lines.append("---")
        lines.append("")
        lines.append("## %s（共 %d 分）" % (section["title"], section["score"]))
        lines.append("")
        lines.append("%s" % section["desc"])
        lines.append("")
        for question in section["questions"]:
            lines.append("**%s.** %s" % (question["no"],
                                         render_text(question["stem"],
                                                     question.get("figures"))))
            lines.append("")
            if question.get("kp"):
                lines.append("`知识点：%s`" % question["kp"])
                lines.append("")
            if section["type"] == "choice":
                letters = "ABCD"
                for index, option in enumerate(question["options"]):
                    lines.append("- %s. %s" % (letters[index],
                                               render_text(option,
                                                           question.get("figures"))))
                lines.append("")
            elif section["type"] == "judge":
                lines.append("（　）对　　（　）错")
                lines.append("")
            elif section["mode"] == "blanks":
                for blank in question.get("blanks") or []:
                    lines.append("- %s：____________"
                                 % (blank.get("label") or "（未命名小问）"))
                lines.append("")
            else:
                lines.append("答案：____________")
                lines.append("")

    return "\n".join(lines)


def build_answer_key_md(paper):
    """生成参考答案与解析。"""
    lines = []
    lines.append("# %s · 参考答案与解析（种子 %s）" % (paper["title"],
                                                      paper["seed"]))
    lines.append("")
    for section in paper["sections"]:
        lines.append("## %s" % section["title"])
        lines.append("")
        for question in section["questions"]:
            if section["type"] == "choice":
                answer = choice_answer_text(question)
            elif section["type"] == "judge":
                answer = judge_answer_text(question)
            elif section["mode"] == "blanks":
                answer = "；".join(
                    "%s = %s" % (blank.get("label") or "小问",
                                 blank_text(blank))
                    for blank in question.get("blanks") or [])
            else:
                answer = answer_text(question)
            lines.append("**%s.** %s" % (question["no"], answer))
            lines.append("")
            lines.append("> 解析：%s" % question["explain"])
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("判分规则：选择题、判断题、填空题按标准答案精确比对（全对得分）；"
                 "计算题逐个小问精确比对，按答对小问的比例给分"
                 "（见 bank/FORMAT.md）。")
    lines.append("")

    return "\n".join(lines)


def build_bank_overview_md():
    """生成题库总览：每道题的题面与答案。"""
    lines = []
    lines.append("# 题库总览")
    lines.append("")
    summary = " · ".join("%s %d 题" % (plan["title"], len(BANK[plan["key"]]))
                         for plan in DRAW_PLAN)
    lines.append("入库规模：%s。" % summary)
    lines.append("")

    for plan in DRAW_PLAN:
        lines.append("## %s（入库 %d 题）" % (plan["title"], len(BANK[plan["key"]])))
        lines.append("")
        for question in BANK[plan["key"]]:
            lines.append("### %s（%s，%d 分）"
                         % (question["id"], question.get("kp", "-"),
                            question["score"]))
            lines.append("")
            lines.append(render_text(question["stem"],
                                     question.get("figures")))
            lines.append("")
            if plan["key"] == "choice":
                letters = "ABCD"
                for index, option in enumerate(question["options"]):
                    lines.append("- %s. %s" % (letters[index],
                                               render_text(option,
                                                           question.get("figures"))))
                lines.append("")
                lines.append("**答案：%s**" % choice_answer_text(question))
            elif plan["key"] == "judge":
                lines.append("**答案：%s**" % judge_answer_text(question))
            elif plan["key"] == "calc":
                lines.append("**答案：**%s"
                             % "；".join(
                                 "%s = %s" % (blank.get("label") or "小问",
                                              blank_text(blank))
                                 for blank in question.get("blanks") or []))
            else:
                lines.append("**答案：**%s" % answer_text(question))
            lines.append("")
            lines.append("> 解析：%s" % question["explain"])
            lines.append("")

    return "\n".join(lines)


def main():
    seed = DEFAULT_SEED
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
        except ValueError:
            print("种子参数不是整数，使用默认种子 %d。" % DEFAULT_SEED)

    paper = draw_paper(seed, BANK)
    write_file("paper.md", build_paper_md(paper))
    write_file("answer_key.md", build_answer_key_md(paper))
    write_file("bank_overview.md", build_bank_overview_md())
    print("题库元信息：%s，满分 %d 分" % (PAPER_META["title"],
                                        PAPER_META["total_score"]))

    return 0


if __name__ == "__main__":
    sys.exit(main())
