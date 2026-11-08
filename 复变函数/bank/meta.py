# -*- coding: utf-8 -*-
"""
文件名：meta.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 定义复变函数模拟卷的元信息与抽题方案。
2. 抽题以随机种子为唯一依据，同一 seed 必得同一份试卷，
   刷新页面或重启服务都不会换卷。
3. 字段格式见同目录 FORMAT.md。
"""

import random

PAPER_META = {
    "id": "cv_exam",
    "title": "复变函数考试模拟卷",
    "course": "复变函数 §2.1（复数的表示与运算 · 复变函数的概念 · 初等函数）",
    "total_score": 100,
    "duration_minutes": 120,
    "instructions": [
        "本卷从题库中随机抽取，满分 100 分，考试时间 120 分钟，"
        "时间到系统自动交卷。",
        "题面中的复数图解用图形方式呈现，鼠标悬停可查看模、辐角与坐标。",
        "填空题答案支持整数、小数、分数、根式与 π 的倍数，"
        "如 2、0.75、3/4、√13、π/4 均可。",
        "计算题按题目给出的每一小问分别作答，交卷时按答对小问的比例给分。",
        "作答实时保存在本机浏览器中，中途刷新页面不丢答案、不重置倒计时。",
        "交卷后系统自动判分：客观题比对标准答案，计算题按小问逐个精确比对，"
        "并给出逐题解析。",
        "想先把复数的基本运算练成肌肉记忆，可先到「闪电训练」页做针对性练习。",
    ],
}

# 每大题的抽题方案：从题库中抽 draw 道，按 no_format 重新编号
DRAW_PLAN = [
    {
        "key": "choice",
        "type": "choice",
        "title": "一、选择题",
        "draw": 10,
        "score": 3,
        "no_format": "1-%d",
        "desc": "本大题共 10 小题，每小题 3 分，共 30 分。"
                "每小题只有一个正确答案。",
    },
    {
        "key": "judge",
        "type": "judge",
        "title": "二、判断题",
        "draw": 8,
        "score": 2,
        "no_format": "2-%d",
        "desc": "本大题共 8 小题，每小题 2 分，共 16 分。"
                "说法正确选“对”，错误选“错”。",
    },
    {
        "key": "fill",
        "type": "fill",
        "mode": "number",
        "title": "三、填空题",
        "draw": 8,
        "score": 3,
        "no_format": "3-%d",
        "desc": "本大题共 8 小题，每小题 3 分，共 24 分。"
                "答案支持整数、小数、分数、根式（√13）与 π 的倍数（π/4）。",
    },
    {
        "key": "calc",
        "type": "fill",
        "mode": "blanks",
        "title": "四、计算题",
        "draw": 6,
        "score": 5,
        "no_format": "4-%d",
        "desc": "本大题共 6 小题，每小题 5 分，共 30 分。"
                "每题分若干小问分别作答，"
                "交卷时按答对小问的比例给分。",
    },
]


def draw_paper(seed, bank):
    """按种子从题库中抽取一份试卷，返回可直接下发的试卷数据。"""
    rng = random.Random(seed)
    sections = []

    for plan in DRAW_PLAN:
        pool = list(bank[plan["key"]])
        draw_count = min(plan["draw"], len(pool))
        picked = rng.sample(pool, draw_count)

        questions = []
        for index, question in enumerate(picked, start=1):
            item = dict(question)
            item["no"] = plan["no_format"] % index
            item["score"] = plan["score"]
            questions.append(item)

        sections.append({
            "id": "sec_%s" % plan["key"],
            "type": plan["type"],
            "mode": plan.get("mode"),
            "title": plan["title"],
            "desc": plan["desc"],
            "score": plan["score"] * len(questions),
            "questions": questions,
        })

    paper = dict(PAPER_META)
    paper["seed"] = seed
    paper["sections"] = sections

    return paper


def bank_summary(bank):
    """返回题库各题型的数量，供自检脚本与服务状态使用。"""
    return {key: len(value) for key, value in bank.items()}


def expected_draw_count():
    """返回各大题的抽题数量。"""
    return {plan["key"]: plan["draw"] for plan in DRAW_PLAN}
