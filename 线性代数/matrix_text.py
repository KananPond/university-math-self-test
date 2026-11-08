# -*- coding: utf-8 -*-
"""
文件名：matrix_text.py
作者：ZCode（GLM）
日期：2026-10-02
版本：1.0
文件说明：
1. 把图形矩阵规格渲染成 Markdown / 纯文本环境可读的字符画。
2. 供 build_paper.py（样卷、答案）、verify_paper.py 与
   web_exam/review.py（错题精讲）共同使用。
3. 生成物中的矩阵都是文本画，方便打印与复制粘贴。
"""

MARKER_START = "[["
MARKER_END = "]]"


def frac_text(value):
    """把数字 / 分数字符串统一显示成分数或整数文本。"""
    text = str(value).strip()
    if not text:
        return "0"

    if "/" in text:
        top, _, bottom = text.partition("/")
        return "%s/%s" % (top.strip() or "0", bottom.strip() or "1")

    try:
        number = float(text)
    except ValueError:
        # 未知数等符号原样保留
        return text
    if number == int(number):
        return str(int(number))

    return ("%.4f" % number).rstrip("0").rstrip(".")


def format_matrix_ascii(spec):
    """把矩阵规格渲染成多行字符画（方括号 / 行列式竖线 / 增广分隔线）。"""
    data = spec.get("data") or []
    style = spec.get("style", "matrix")
    if not data:
        return "[]"

    cells = [[frac_text(v) for v in row] for row in data]
    width = max(len(cell) for row in cells for cell in row)
    height = len(cells)
    gutter = max(1, width - 1)

    def bracket_left(row_index):
        if style == "det":
            return "|"
        if row_index == 0:
            return "⎡" + " " * gutter
        if row_index == height - 1:
            return "⎣" + " " * gutter
        return "⎢" + " " * gutter

    def bracket_right(row_index):
        if style == "det":
            return "|"
        if row_index == 0:
            return " " * gutter + "⎤"
        if row_index == height - 1:
            return " " * gutter + "⎦"
        return " " * gutter + "⎥"

    lines = []
    for i, row in enumerate(cells):
        pieces = []
        for j, cell in enumerate(row):
            if style == "aug" and j == len(row) - 1:
                pieces.append("│ " + cell.rjust(width))
            else:
                pieces.append(cell.rjust(width))
        lines.append("%s%s%s" % (bracket_left(i),
                                 "  ".join(pieces),
                                 bracket_right(i)))

    return "\n".join(lines)


def render_text(text, matrices):
    """把含 [[key]] 标记的文本渲染成带字符画矩阵的 Markdown 片段。"""
    matrices = matrices or {}
    parts = []
    buffer = []
    index = 0
    while index < len(text):
        start = text.find(MARKER_START, index)
        if start < 0:
            buffer.append(text[index:])
            break
        buffer.append(text[index:start])
        end = text.find(MARKER_END, start + len(MARKER_START))
        if end < 0:
            buffer.append(text[start:])
            break
        key = text[start + len(MARKER_START):end].strip()
        spec = matrices.get(key)
        if spec is None:
            buffer.append(MARKER_START + key + MARKER_END)
        else:
            parts.append("".join(buffer))
            buffer = []
            parts.append(("matrix", spec))
        index = end + len(MARKER_END)
    parts.append("".join(buffer))

    rendered = []
    for part in parts:
        if isinstance(part, tuple) and part[0] == "matrix":
            spec = part[1]
            label = spec.get("label") or ""
            prefix = ("%s = " % label) if label else ""
            rendered.append("%s\n\n```\n%s\n```\n" % (prefix,
                                                      format_matrix_ascii(spec)))
        else:
            rendered.append(part)

    return "".join(rendered)
