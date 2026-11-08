# -*- coding: utf-8 -*-
"""
文件名：answer_key.py
作者：ZCode（GLM）
日期：2026-10-02
版本：1.0
文件说明：
1. 端到端测试专用：按种子从服务端题库取标准答案并输出 JSON。
2. 正常考试流程中答案只留在服务端，前端拿不到；本脚本仅供测试使用。
3. 用法： python tests/answer_key.py <种子>
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# tests → web_exam → 考试服务（bank 所在的项目根）
PROJECT_DIR = os.path.dirname(os.path.dirname(HERE))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from bank import draw_paper, BANK  # noqa: E402


def answer_key(seed):
    """按种子输出全卷标准答案。"""
    paper = draw_paper(seed, BANK)
    key = {"choice": {}, "judge": {}, "fill": {}, "calc": {}}
    for section in paper["sections"]:
        for question in section["questions"]:
            kind = section["type"]
            if kind == "choice":
                key["choice"][question["id"]] = question["answer"]
            elif kind == "judge":
                key["judge"][question["id"]] = question["answer"]
            elif section["mode"] == "matrix":
                key["calc"][question["id"]] = question["answer"]
            else:
                key["fill"][question["id"]] = question["answer"]

    return key


def main():
    if len(sys.argv) < 2:
        print("用法： python answer_key.py <种子>", file=sys.stderr)
        return 1

    key = answer_key(int(sys.argv[1]))
    json.dump(key, sys.stdout, ensure_ascii=False)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
