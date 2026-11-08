# -*- coding: utf-8 -*-
"""
文件名：__init__.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 复变函数题库包：汇总各题型题目并对外提供统一的题库对象。
2. 题库是全站唯一数据源，样卷、答案、判分都由它派生。
3. 字段格式见同目录 FORMAT.md。
"""

from .choice_questions import CHOICE
from .judge_questions import JUDGE
from .fill_questions import FILL
from .calc_questions import CALC
from .meta import PAPER_META, DRAW_PLAN, draw_paper, bank_summary, expected_draw_count
from . import complex_ref
from . import drill_gen

BANK = {
    "choice": CHOICE,
    "judge": JUDGE,
    "fill": FILL,
    "calc": CALC,
}
