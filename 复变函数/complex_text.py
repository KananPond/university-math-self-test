# -*- coding: utf-8 -*-
"""
文件名：complex_text.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 把图形规格渲染成 Markdown / 纯文本环境可读的描述。
2. 供 build_paper.py（样卷、答案）、verify_paper.py 与
   web_exam/review.py（错题精讲）共同使用。
3. 复平面图解在纸面上画不出来，这里改写成
   「复数 = 模 + 辐角」的文字描述，保证信息不丢。
"""

from bank import complex_ref as cr

MARKER_START = "[["
MARKER_END = "]]"


def complex_text(value):
    """复数转可读文本。"""
    if value is None:
        return "（无法解析）"

    return cr.format_complex(value)


def modulus_text(value):
    """模的可读文本。"""
    radius = cr.c_abs(value)
    if radius is None:
        return "（不可精确表示）"

    return cr.format_real(radius)


def argument_text(value):
    """主值辐角的可读文本。"""
    angle = cr.arg_coefficient(value)
    if angle is None:
        return "（不可精确表示）"

    return cr.format_angle(angle)


def describe_figure(spec):
    """把图形规格转成一段可读描述。"""
    if not isinstance(spec, dict):
        return "（图解）"

    kind = spec.get("kind") or "point"

    if kind == "point":
        value = cr.parse_complex(spec.get("z"))
        if value is None:
            return "（图解：%s）" % spec.get("z")
        label = spec.get("label") or "z"
        parts = ["%s = %s" % (label, complex_text(value)),
                 "|%s| = %s" % (label, modulus_text(value)),
                 "Arg %s = %s" % (label, argument_text(value))]
        if spec.get("show") and "conj" in spec["show"]:
            parts.append("共轭 %s̄ = %s"
                         % (label, complex_text(cr.c_conj(value))))

        return "复平面图解： " + "；".join(parts)

    if kind == "roots":
        count = spec.get("n")
        radius = spec.get("radius", 1)
        roots = cr.roots_of_unity(count) if count else None
        if roots:
            values = "、".join(complex_text(root) for root in roots)
        else:
            values = "（%s 个等分根）" % count

        return "复平面图解： 半径为 %s 的圆上的 %s 次单位根：%s" \
            % (radius, count, values)

    if kind == "ops":
        z1 = cr.parse_complex(spec.get("z1"))
        z2 = cr.parse_complex(spec.get("z2"))
        if z1 is None or z2 is None:
            return "复平面图解： 乘法的旋转与伸缩"
        product = cr.c_mul(z1, z2)

        return "复平面图解： %s = %s，%s = %s，%s%s = %s" \
            % (spec.get("label1") or "z₁", complex_text(z1),
               spec.get("label2") or "z₂", complex_text(z2),
               spec.get("label1") or "z₁", spec.get("label2") or "z₂",
               complex_text(product))

    if kind == "plane":
        pieces = []
        for item in spec.get("points") or []:
            value = cr.parse_complex(item.get("z"))
            pieces.append("%s = %s" % (item.get("label") or "z",
                                       complex_text(value)))
        for item in spec.get("circles") or []:
            pieces.append("圆：|z| = %s %s"
                          % (item.get("radius"),
                             item.get("label") or ""))

        return "复平面图解： " + "；".join(pieces)

    return "（图解）"


def render_text(text, figures):
    """把含 [[key]] 标记的文本渲染成带图解描述的 Markdown 片段。"""
    figures = figures or {}
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
        spec = figures.get(key)
        if spec is None:
            buffer.append(MARKER_START + key + MARKER_END)
        else:
            parts.append("".join(buffer))
            buffer = []
            parts.append(("figure", spec))
        index = end + len(MARKER_END)
    parts.append("".join(buffer))

    rendered = []
    for part in parts:
        if isinstance(part, tuple) and part[0] == "figure":
            rendered.append("\n\n> %s" % describe_figure(part[1]))
        else:
            rendered.append(part)

    return "".join(rendered)
