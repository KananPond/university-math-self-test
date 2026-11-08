# -*- coding: utf-8 -*-
"""
文件名：calc_questions.py
作者：Worker
日期：2026-11-08
版本：1.0
文件说明：
复变函数（§2.1）计算题题库，纯数据模块。
共 12 题，id 形如 x_cv_01 ~ x_cv_12，每题 5 分。
blanks 为多空答案，判分按正确空数比例给分。
"""

CALC = [
    {
        "id": "x_cv_01",
        "score": 5,
        "stem": "设 z₁ = 1 + 2i，z₂ = 3 - i，求 z₁ + z₂、z₁z₂、z₁/z₂。",
        "blanks": [
            {"label": "z₁ + z₂", "answer": "4+i", "answer_type": "complex"},
            {"label": "z₁z₂", "answer": "5+5i", "answer_type": "complex"},
            {"label": "z₁/z₂", "answer": "1/10+7/10i", "answer_type": "complex"},
        ],
        "kp": "四则运算",
        "verify": {"kind": "op", "op": "add", "left": "1+2i", "right": "3-i", "blank": 0},
        "explain": "加减只做实部实部、虚部虚部：z₁ + z₂ = (1+2i) + (3-i) = 4 + i。"
                   "乘法按 (a+bi)(c+di) = (ac - bd) + (ad + bc)i：z₁z₂ = (1+2i)(3-i) = 3 - i + 6i - 2i² "
                   "= 3 + 5i + 2 = 5 + 5i。"
                   "除法先有理化：z₁/z₂ = (1+2i)(3+i)/((3-i)(3+i)) = (3 + i + 6i + 2i²)/(9 + 1) "
                   "= (3 + 7i - 2)/10 = (1 + 7i)/10 = 1/10 + 7/10i。",
    },
    {
        "id": "x_cv_02",
        "score": 5,
        "stem": "设 z = 2 + 3i，求 z + z̄、z·z̄、1/z。",
        "blanks": [
            {"label": "z + z̄", "answer": "4", "answer_type": "number"},
            {"label": "z·z̄", "answer": "13", "answer_type": "number"},
            {"label": "1/z", "answer": "2/13-3/13i", "answer_type": "complex"},
        ],
        "kp": "共轭与倒数",
        "verify": {"kind": "op", "op": "add", "left": "2+3i", "right": "2-3i", "blank": 0},
        "explain": "z̄ = 2 - 3i。z + z̄ = (2+3i) + (2-3i) = 4（相当于 2Re z）。"
                   "z·z̄ = (2+3i)(2-3i) = 4 - 6i + 6i - 9i² = 4 + 9 = 13 = |z|²。"
                   "1/z = z̄/|z|² = (2-3i)/13 = 2/13 - 3/13i。",
    },
    {
        "id": "x_cv_03",
        "score": 5,
        "stem": "设 z = 1 + i，求 z²、z⁴、z⁸。",
        "blanks": [
            {"label": "z²", "answer": "2i", "answer_type": "complex"},
            {"label": "z⁴", "answer": "-4", "answer_type": "number"},
            {"label": "z⁸", "answer": "16", "answer_type": "number"},
        ],
        "kp": "幂与根",
        "verify": {"kind": "pow", "z": "1+i", "n": 2, "blank": 0},
        "explain": "z² = (1+i)² = 1 + 2i + i² = 2i；"
                   "z⁴ = (z²)² = (2i)² = 4i² = -4；"
                   "z⁸ = (z⁴)² = (-4)² = 16。也可以用棣莫弗公式：1+i = √2(cos π/4 + i sin π/4)，"
                   "故 zⁿ = 2^{n/2}(cos nπ/4 + i sin nπ/4)。",
    },
    {
        "id": "x_cv_04",
        "score": 5,
        "stem": "求方程 z³ = 1 的三个根。",
        "blanks": [
            {"label": "w₁", "answer": "1", "answer_type": "complex"},
            {"label": "w₂", "answer": "-1/2+√3i/2", "answer_type": "complex"},
            {"label": "w₃", "answer": "-1/2-√3i/2", "answer_type": "complex"},
        ],
        "kp": "幂与根",
        "verify": {"kind": "root_of", "z": "1", "n": 3, "blank": 0},
        "explain": "z = r(cos θ + i sin θ)，由 z³ = 1 = 1·(cos 0 + i sin 0) 得 r³ = 1 即 r = 1，"
                   "3θ = 2kπ，即 θ = 2kπ/3 (k = 0, 1, 2)。"
                   "故三个根为 1，cos(2π/3) + i sin(2π/3) = -1/2 + (√3/2)i，"
                   "以及 cos(4π/3) + i sin(4π/3) = -1/2 - (√3/2)i。",
    },
    {
        "id": "x_cv_05",
        "score": 5,
        "stem": "设 z = 1 + i，求 |z|、|z|²、Arg z。[[P]]",
        "blanks": [
            {"label": "|z|", "answer": "√2", "answer_type": "number"},
            {"label": "|z|²", "answer": "2", "answer_type": "number"},
            {"label": "Arg z", "answer": "π/4", "answer_type": "angle"},
        ],
        "kp": "模与辐角",
        "figures": {
            "P": {"kind": "point", "z": "1+i", "label": "z",
                  "show": ["radius", "angle", "proj"]},
        },
        "verify": {"kind": "modulus", "z": "1+i", "blank": 0},
        "explain": "|z| = √(x² + y²) = √(1² + 1²) = √2；|z|² = x² + y² = 2；"
                   "z 在第一象限且 tan θ = 1，故主值 Arg z = π/4。",
    },
    {
        "id": "x_cv_06",
        "score": 5,
        "stem": "设 z = cos π/6 + i sin π/6 = √3/2 + i/2，求 z³、z⁶、z¹²。",
        "blanks": [
            {"label": "z³", "answer": "i", "answer_type": "complex"},
            {"label": "z⁶", "answer": "-1", "answer_type": "number"},
            {"label": "z¹²", "answer": "1", "answer_type": "number"},
        ],
        "kp": "棣莫弗公式",
        "verify": {"kind": "pow", "z": "√3/2+i/2", "n": 3, "blank": 0},
        "explain": "由棣莫弗公式 zⁿ = cos nθ + i sin nθ，θ = π/6："
                   "z³ = cos π/2 + i sin π/2 = i；z⁶ = cos π + i sin π = -1；"
                   "z¹² = cos 2π + i sin 2π = 1。",
    },
    {
        "id": "x_cv_07",
        "score": 5,
        "stem": "设 z = 2(cos π/6 + i sin π/6)，求 z 的代数形式、|z| 与 Arg z。",
        "blanks": [
            {"label": "z 的代数形式", "answer": "√3+i", "answer_type": "complex"},
            {"label": "|z|", "answer": "2", "answer_type": "number"},
            {"label": "Arg z", "answer": "π/6", "answer_type": "angle"},
        ],
        "kp": "复数的表示",
        "verify": {"kind": "modulus", "z": "√3+i", "blank": 1},
        "explain": "实部 = 2cos π/6 = 2 × (√3/2) = √3，虚部 = 2sin π/6 = 2 × (1/2) = 1，"
                   "故 z = √3 + i。|z| = √(3 + 1) = 2，与三角形式中的系数一致；"
                   "z 在第一象限，Arg z = π/6。",
    },
    {
        "id": "x_cv_08",
        "score": 5,
        "stem": "设 z₁ = 2 + i，z₂ = 1 - i，求 z₁ + z₂、z₁ - z₂、z₁z₂。",
        "blanks": [
            {"label": "z₁ + z₂", "answer": "3", "answer_type": "number"},
            {"label": "z₁ - z₂", "answer": "1+2i", "answer_type": "complex"},
            {"label": "z₁z₂", "answer": "3-i", "answer_type": "complex"},
        ],
        "kp": "四则运算",
        "verify": {"kind": "op", "op": "add", "left": "2+i", "right": "1-i", "blank": 0},
        "explain": "z₁ + z₂ = (2+i) + (1-i) = 3（虚部相消）；"
                   "z₁ - z₂ = (2+i) - (1-i) = 1 + 2i；"
                   "z₁z₂ = (2+i)(1-i) = 2 - 2i + i - i² = 2 - i + 1 = 3 - i。",
    },
    {
        "id": "x_cv_09",
        "score": 5,
        "stem": "求方程 z² = 4i 的两个根。",
        "blanks": [
            {"label": "w₁", "answer": "√2+√2i", "answer_type": "complex"},
            {"label": "w₂", "answer": "-√2-√2i", "answer_type": "complex"},
        ],
        "kp": "幂与根",
        "verify": {"kind": "root_of", "z": "4i", "n": 2, "blank": 0},
        "explain": "把 4i 写成 4(cos π/2 + i sin π/2)。由 z = r(cos θ + i sin θ) 与 "
                   "z² = 4(cos π/2 + i sin π/2) 比较系数得 r² = 4 即 r = 2，"
                   "2θ = π/2 + 2kπ 即 θ = π/4 或 θ = π/4 + π。"
                   "故 w₁ = 2(cos π/4 + i sin π/4) = √2 + √2i，w₂ = -√2 - √2i。"
                   "验证：(√2 + √2i)² = 2 + 4i + 2i² = 4i ✓。",
    },
    {
        "id": "x_cv_10",
        "score": 5,
        "stem": "求复正弦函数 sin z 与双曲正弦函数 sinh z 的周期。",
        "blanks": [
            {"label": "sin z 的周期", "answer": "2π", "answer_type": "angle"},
            {"label": "sinh z 的周期", "answer": "2πi", "answer_type": "complex"},
        ],
        "kp": "复三角与双曲函数",
        "explain": "sin z = (e^{iz} - e^{-iz})/(2i)。由 e^{i(z+2π)} = e^{iz} 得 sin(z+2π) = sin z，"
                   "而 sin(z+π) = -sin z ≠ sin z，故 sin z 的（最小正）周期是 2π。"
                   "sinh z = (e^z - e^{-z})/2，sinh(z + 2πi) = (e^z·e^{2πi} - e^{-z}·e^{-2πi})/2 "
                   "= (e^z - e^{-z})/2 = sinh z（因为 e^{2πi} = 1），故 sinh z 的周期是 2πi。",
    },
    {
        "id": "x_cv_11",
        "score": 5,
        "stem": "按主值定义 z^α = e^{α Log z}，计算 ((-1)²)^{1/2} 与 (-1)^{2·(1/2)} 的值，"
                "并据此说明幂律 (z^α)^β = z^{αβ} 是否成立。",
        "blanks": [
            {"label": "((-1)²)^{1/2}", "answer": "1", "answer_type": "number"},
            {"label": "(-1)^{2·(1/2)}", "answer": "-1", "answer_type": "number"},
        ],
        "kp": "复幂函数",
        "verify": {"kind": "pow", "z": "-1", "n": 1, "blank": 1},
        "explain": "先算内层：(-1)² = 1，再取 1/2 次幂得 1/2 次根 1^{1/2} = 1。"
                   "而按幂律直接算：(-1)^{2·(1/2)} = (-1)^1 = -1。"
                   "1 ≠ -1，说明复数域中幂律 (z^α)^β = z^{αβ} 并不总成立——"
                   "因为 Log(-1) = i(2k+1)π 是多值的，取不同 k 会得到不同的结果。",
    },
    {
        "id": "x_cv_12",
        "score": 5,
        "stem": "设复变函数 w = f(z) = z²，z = x + yi。求 u(x, y)、v(x, y) 在点 z = 1 + i 处的值，"
                "以及 f(1 + i)。",
        "blanks": [
            {"label": "u(1, 1)", "answer": "0", "answer_type": "number"},
            {"label": "v(1, 1)", "answer": "2", "answer_type": "number"},
            {"label": "f(1 + i)", "answer": "2i", "answer_type": "complex"},
        ],
        "kp": "复变函数概念",
        "verify": {"kind": "op", "op": "mul", "left": "1+i", "right": "1+i", "blank": 2},
        "explain": "(x + yi)² = x² + 2xyi + y²i² = (x² - y²) + 2xyi，所以 u = x² - y²，v = 2xy。"
                   "代入 x = 1, y = 1：u(1, 1) = 1 - 1 = 0，v(1, 1) = 2×1×1 = 2，"
                   "于是 f(1 + i) = 0 + 2i = 2i（与直接算 (1+i)² = 2i 一致）。",
    },
]
