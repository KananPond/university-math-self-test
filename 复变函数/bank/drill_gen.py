# -*- coding: utf-8 -*-
"""
文件名：drill_gen.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 闪电训练的程序化题源：按随机种子即时生成「复数的表示与运算」基础题，
   答案由精确运算现算，题目无限不重复，专门用于把基本功练成肌肉记忆。
2. 生成过程完全确定：同一 seed 必得同一组题，
   因此服务端可以用 (seed, 题号) 复原题目并判分，无需保存会话状态。
3. 所有标准答案都由 bank/complex_ref.py 精确计算，不存在人工抄写错误。
"""

import random

from . import complex_ref as cr


# 主值辐角可精确表示的复数样本：(复数文本, 辐角系数)
SPECIAL_ARGUMENTS = [
    ("1", "0"),
    ("-1", "π"),
    ("i", "π/2"),
    ("-i", "-π/2"),
    ("1+i", "π/4"),
    ("1-i", "-π/4"),
    ("-1+i", "3π/4"),
    ("-1-i", "-3π/4"),
    ("√3/2+i/2", "π/6"),
    ("√3/2-i/2", "-π/6"),
    ("1/2+√3/2i", "π/3"),
    ("1/2-√3/2i", "-π/3"),
    ("-1/2+√3/2i", "2π/3"),
    ("-1/2-√3/2i", "-2π/3"),
]


def _make_complex(real_part, imag_part):
    """由有理数构造复数。"""
    return (cr.Real(real_part), cr.Real(imag_part))


def _text(value):
    """复数转显示文本。"""
    return cr.format_complex(value)


def _random_complex(rng, bound=4):
    """随机生成一个整系数复数（非零）。"""
    while True:
        real_part = rng.randint(-bound, bound)
        imag_part = rng.randint(-bound, bound)
        if real_part != 0 or imag_part != 0:
            break

    return _make_complex(real_part, imag_part)


def _random_complex_text(rng, bound=4):
    """随机生成一个整系数复数的文本（保持写法自然）。"""
    real_part = rng.randint(-bound, bound)
    imag_part = rng.randint(-bound, bound)
    if real_part == 0 and imag_part == 0:
        imag_part = 1

    if real_part == 0:
        if imag_part == 1:
            return "i"
        if imag_part == -1:
            return "-i"
        return "%di" % imag_part

    sign = "+" if imag_part >= 0 else "-"
    magnitude = abs(imag_part)
    if magnitude == 1:
        imag_text = "%si" % sign
    else:
        imag_text = "%s%di" % (sign, magnitude)

    return "%d%s%s" % (real_part, imag_text, "")


def _item(kind, kp, stem, answer, answer_type, explain, figure=None):
    """构造一条训练条目。"""
    item = {
        "kind": kind,
        "kp": kp,
        "stem": stem,
        "answer": answer,
        "answer_type": answer_type,
        "explain": explain,
    }
    if figure:
        item["figure"] = figure

    return item


# --------------------------------------------------------------------------
# 各类生成器
# --------------------------------------------------------------------------

def gen_add(rng):
    """加法。"""
    left = _random_complex(rng)
    right = _random_complex(rng)
    answer = cr.c_add(left, right)

    return _item(
        "number", "四则运算",
        "计算 (%s) + (%s) = ______" % (_text(left), _text(right)),
        _text(answer), "complex",
        "实部实部相加、虚部虚部相加：(a+bi)+(c+di) = (a+c) + (b+d)i，"
        "所以结果是 %s。" % _text(answer))


def gen_sub(rng):
    """减法。"""
    left = _random_complex(rng)
    right = _random_complex(rng)
    answer = cr.c_sub(left, right)

    return _item(
        "number", "四则运算",
        "计算 (%s) − (%s) = ______" % (_text(left), _text(right)),
        _text(answer), "complex",
        "减法先把减号变成加负数：(a+bi)−(c+di) = (a−c) + (b−d)i，"
        "所以结果是 %s。" % _text(answer))


def gen_mul(rng):
    """乘法。"""
    left = _random_complex(rng, 3)
    right = _random_complex(rng, 3)
    answer = cr.c_mul(left, right)

    return _item(
        "number", "四则运算",
        "计算 (%s) × (%s) = ______" % (_text(left), _text(right)),
        _text(answer), "complex",
        "(a+bi)(c+di) = (ac−bd) + (ad+bc)i，代入得 %s。" % _text(answer))


def gen_div(rng):
    """除法（有理化）。"""
    left = _random_complex(rng, 3)
    right = _random_complex(rng, 3)
    if right[0].is_zero and right[1].is_zero:
        right = _make_complex(1, 0)
    answer = cr.c_div(left, right)

    return _item(
        "number", "四则运算",
        "计算 (%s) ÷ (%s) = ______" % (_text(left), _text(right)),
        _text(answer), "complex",
        "分母有理化：a/b = a·b̄/|b|²，|b|² = %s，代入得 %s。"
        % (cr.format_real(cr.c_abs_sq(right)), _text(answer)))


def gen_conj(rng):
    """共轭。"""
    value = _random_complex(rng)
    answer = cr.c_conj(value)

    return _item(
        "number", "共轭与倒数",
        "复数 z = %s 的共轭复数 z̄ = ______" % _text(value),
        _text(answer), "complex",
        "共轭就是把虚部变号：z̄ = a − bi，所以 z̄ = %s。" % _text(answer))


def gen_inv(rng):
    """倒数。"""
    value = _random_complex(rng, 3)
    if value[0].is_zero and value[1].is_zero:
        value = _make_complex(1, 1)
    answer = cr.c_div(_make_complex(1, 0), value)

    return _item(
        "number", "共轭与倒数",
        "复数 z = %s 的倒数 1/z = ______" % _text(value),
        _text(answer), "complex",
        "1/z = z̄/|z|²，|z|² = %s，所以 1/z = %s。"
        % (cr.format_real(cr.c_abs_sq(value)), _text(answer)))


def gen_modulus(rng):
    """模。"""
    value = _random_complex(rng, 4)
    radius = cr.c_abs(value)
    answer = cr.format_real(radius)

    return _item(
        "number", "模与辐角",
        "复数 z = %s 的模 |z| = ______" % _text(value),
        answer, "number",
        "|z| = √(x²+y²) = √(%s) = %s。"
        % (cr.format_real(cr.c_abs_sq(value)), answer),
        {"kind": "point", "z": _text(value), "label": "z",
         "show": ["radius", "proj"]})


def gen_argument(rng):
    """主值辐角。"""
    text, angle = rng.choice(SPECIAL_ARGUMENTS)
    value = cr.parse_complex(text)
    radius = cr.c_abs(value)

    return _item(
        "number", "模与辐角",
        "复数 z = %s 的主值辐角 Arg z = ______（用 π 的倍数表示）" % _text(value),
        angle, "angle",
        "z 的模是 %s，辐角落在 %s 象限，主值取 (−π, π] 内的那个值，即 %s。"
        % (cr.format_real(radius), _quadrant(value), angle),
        {"kind": "point", "z": _text(value), "label": "z",
         "show": ["radius", "angle", "proj"]})


def _real_sign(value):
    """实数的符号：-1 / 0 / 1（带根式时按近似值判符号，仅用于描述文字）。"""
    if value.is_zero:
        return 0
    total = float(value.rat)
    for radicand, coef in value.surds.items():
        total += float(coef) * (radicand ** 0.5)
    total += float(value.pi) * 3.141592653589793
    if total > 0:
        return 1
    if total < 0:
        return -1

    return 0


def _quadrant(value):
    """判断复数所在象限（用于解析文字）。"""
    real_part, imag_part = value
    if real_part.is_zero and imag_part.is_zero:
        return "原点"
    if real_part.is_zero:
        return "虚轴"
    if imag_part.is_zero:
        return "实轴"
    real_sign = _real_sign(real_part)
    imag_sign = _real_sign(imag_part)
    if real_sign > 0:
        return "第一" if imag_sign > 0 else "第四"

    return "第二" if imag_sign > 0 else "第三"


def gen_from_polar(rng):
    """由指数形式求代数形式。"""
    radius = rng.randint(1, 4)
    # 只取模为 1 的样本，保证 r·e^{iθ} 的写法成立
    unit = [pair for pair in SPECIAL_ARGUMENTS
            if cr.c_abs(cr.parse_complex(pair[0])) == cr.ONE]
    text, angle = rng.choice(unit)
    base = cr.parse_complex(text)
    answer = cr.c_scale(base, radius)
    answer_text = _text(answer)

    return _item(
        "number", "复数的表示",
        "把复数 %se^{i%s} 写成代数形式 a + bi = ______"
        % (radius, angle),
        answer_text, "complex",
        "%se^{i%s} = %s(%s + i·%s) = %s。"
        % (radius, angle, radius, cr.format_real(base[0]),
           cr.format_real(base[1]), answer_text),
        {"kind": "point", "z": answer_text, "label": "z",
         "show": ["radius", "angle"]})


def gen_to_polar(rng):
    """由代数形式求模与辐角（两个小问）。"""
    text, angle = rng.choice(SPECIAL_ARGUMENTS)
    value = cr.parse_complex(text)
    radius = cr.c_abs(value)

    return {
        "kind": "blanks",
        "kp": "复数的表示",
        "stem": "复数 z = %s 的模是 ______，主值辐角 Arg z 是 ______"
                "（角度用 π 的倍数表示）" % _text(value),
        "blanks": [
            {"label": "|z|", "answer": cr.format_real(radius),
             "answer_type": "number"},
            {"label": "Arg z", "answer": angle, "answer_type": "angle"},
        ],
        "explain": "|z| = √(x²+y²) = %s；Arg z 取 (−π, π] 内的值，为 %s。"
                   % (cr.format_real(radius), angle),
        "figure": {"kind": "point", "z": _text(value), "label": "z",
                   "show": ["radius", "angle", "proj"]},
    }


def gen_power(rng):
    """整数次幂。"""
    base_text = rng.choice(["1+i", "1-i", "i", "-i", "1", "-1",
                             "2+i", "1+2i", "√3/2+i/2"])
    base = cr.parse_complex(base_text)
    exponent = rng.randint(2, 6)
    answer = cr.c_pow_int(base, exponent)
    answer_text = _text(answer)

    return _item(
        "number", "幂与根",
        "计算 (%s)^{%d} = ______" % (base_text, exponent),
        answer_text, "complex",
        "用快速幂或棣莫弗公式：(%s)^{%d} = %s。"
        % (base_text, exponent, answer_text))


def gen_unit_root(rng):
    """n 次单位根中辐角为指定值的一个。"""
    count = rng.choice([2, 3, 4, 6])
    roots = cr.roots_of_unity(count)
    index = rng.randrange(len(roots))
    root = roots[index]
    turns = cr.Fraction(index, count)
    angle = cr.format_angle(turns * 2)

    return _item(
        "number", "幂与根",
        "%d 次单位根中，辐角为 %s 的那个根是 ______" % (count, angle),
        _text(root), "complex",
        "%d 次单位根为 e^{2kπi/%d}（k = 0,…,%d），辐角 %s 对应 k = %d，"
        "其值为 %s。" % (count, count, count - 1, angle, index, _text(root)),
        {"kind": "roots", "n": count, "radius": 1,
         "label": "%d 次单位根" % count})


def gen_i_power(rng):
    """i 的幂。"""
    exponent = rng.randint(5, 40)
    answer = cr.c_pow_int(cr.parse_complex("i"), exponent)
    residue = exponent % 4

    return _item(
        "number", "幂与根",
        "计算 i^{%d} = ______" % exponent,
        _text(answer), "complex",
        "i 的幂以 4 为周期：i, −1, −i, 1。%d ÷ 4 余 %d，所以 i^{%d} = %s。"
        % (exponent, residue, exponent, _text(answer)))


def gen_de_moivre(rng):
    """棣莫弗公式：三角形式的幂。"""
    pairs = [("π/3", "1/2+√3/2i"), ("π/6", "√3/2+i/2"),
             ("π/4", "√2/2+√2/2i"), ("2π/3", "-1/2+√3/2i")]
    angle_text, base_text = rng.choice(pairs)
    base = cr.parse_complex(base_text)
    exponent = rng.randint(2, 5)
    answer = cr.c_pow_int(base, exponent)
    answer_text = _text(answer)

    return _item(
        "number", "棣莫弗公式",
        "用棣莫弗公式计算 (cos %s + i sin %s)^{%d} = ______"
        % (angle_text, angle_text, exponent),
        answer_text, "complex",
        "(cosθ + i sinθ)ⁿ = cos nθ + i sin nθ，模为 1，辐角由 %s 变成 %s，"
        "故结果为 %s。" % (angle_text, cr.format_angle(
            cr.parse_angle(angle_text) * exponent), answer_text))


GENERATORS = [
    gen_add, gen_sub, gen_mul, gen_div,
    gen_conj, gen_inv, gen_modulus, gen_argument,
    gen_from_polar, gen_to_polar, gen_power,
    gen_unit_root, gen_i_power, gen_de_moivre,
]

# 知识点 → 生成器（闪电训练按知识点取题）
KP_GENERATORS = {
    "四则运算": [gen_add, gen_sub, gen_mul, gen_div],
    "共轭与倒数": [gen_conj, gen_inv],
    "模与辐角": [gen_modulus, gen_argument],
    "复数的表示": [gen_from_polar, gen_to_polar],
    "幂与根": [gen_power, gen_unit_root, gen_i_power],
    "棣莫弗公式": [gen_de_moivre],
}


def generate_items(seed, count, kps=None):
    """按种子生成一组训练条目。

    同一 seed 必得同一组题；kps 为 None 时覆盖全部基础知识点。
    """
    rng = random.Random(seed)
    pool = []
    for kp, generators in KP_GENERATORS.items():
        if kps and kp not in kps:
            continue
        for generator in generators:
            pool.append((kp, generator))

    if not pool:
        pool = [(kp, generator) for kp, generators in KP_GENERATORS.items()
                for generator in generators]

    items = []
    for index in range(count):
        kp, generator = pool[index % len(pool)]
        item = generator(rng)
        item["id"] = "drill_%d_%d" % (seed, index)
        item["seed"] = seed
        item["index"] = index
        items.append(item)

    return items


def item_by_id(seed, item_id):
    """按种子与条目 id 复原一道训练题。"""
    text = str(item_id)
    if not text.startswith("drill_"):
        return None
    parts = text.split("_")
    if len(parts) != 3:
        return None
    try:
        index = int(parts[2])
    except ValueError:
        return None

    items = generate_items(seed, index + 1)
    for item in items:
        if item["id"] == item_id:
            return item

    return None
