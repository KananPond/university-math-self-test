# -*- coding: utf-8 -*-
"""
文件名：fill_questions.py
作者：Worker
日期：2026-11-08
版本：1.0
文件说明：
复变函数（§2.1）填空题题库，纯数据模块。
共 20 题，id 形如 f_cv_01 ~ f_cv_20，每题 3 分。
answer 为字符串或字符串列表（列表表示答出其中任意一个即算对）。
"""

FILL = [
    {
        "id": "f_cv_01",
        "score": 3,
        "stem": "复数 z = 2(cos π/3 + i sin π/3) 的实部是 ______。",
        "answer": "1",
        "answer_type": "number",
        "kp": "复数的表示",
        "explain": "实部 = r cos θ = 2cos π/3 = 2 × (1/2) = 1。",
    },
    {
        "id": "f_cv_02",
        "score": 3,
        "stem": "复数 z = 2(cos π/3 + i sin π/3) 的代数形式是 ______。",
        "answer": "1+√3i",
        "answer_type": "complex",
        "kp": "复数的表示",
        "explain": "实部 = 2cos π/3 = 1，虚部 = 2sin π/3 = 2 × (√3/2) = √3，"
                   "所以 z = 1 + √3i。",
    },
    {
        "id": "f_cv_03",
        "score": 3,
        "stem": "复数 z = 1 + 2i 的模是 ______。[[P]]",
        "answer": "√5",
        "answer_type": "number",
        "kp": "模与辐角",
        "figures": {
            "P": {"kind": "point", "z": "1+2i", "label": "z",
                  "show": ["radius", "proj"]},
        },
        "verify": {"kind": "modulus", "z": "1+2i"},
        "explain": "|z| = √(x² + y²) = √(1² + 2²) = √5。",
    },
    {
        "id": "f_cv_04",
        "score": 3,
        "stem": "复数 z = 3 + 4i 的模的平方 |z|² 是 ______。",
        "answer": "25",
        "answer_type": "number",
        "kp": "模与辐角",
        "verify": {"kind": "abs_sq", "z": "3+4i"},
        "explain": "|z|² = x² + y² = 3² + 4² = 25；相应的 |z| = 5。",
    },
    {
        "id": "f_cv_05",
        "score": 3,
        "stem": "复数 z = 1 + i 的主值辐角 Arg z 是 ______（用 π 的倍数表示）。",
        "answer": "π/4",
        "answer_type": "angle",
        "kp": "模与辐角",
        "verify": {"kind": "arg", "z": "1+i"},
        "explain": "z 在第一象限，tan θ = 1/1 = 1，故主值 Arg z = π/4 ∈ (-π, π]。",
    },
    {
        "id": "f_cv_06",
        "score": 3,
        "stem": "复数 z = -1 - i 的主值辐角 Arg z 是 ______（用 π 的倍数表示）。",
        "answer": "-3π/4",
        "answer_type": "angle",
        "kp": "模与辐角",
        "verify": {"kind": "arg", "z": "-1-i"},
        "explain": "z 在第三象限，tan θ = 1。主值范围 (-π, π]，故 Arg z = -3π/4"
                   "（写成 5π/4 就不是主值了）。",
    },
    {
        "id": "f_cv_07",
        "score": 3,
        "stem": "复数 z = cos π/6 + i sin π/6 的主值辐角 Arg z 是 ______（用 π 的倍数表示）。",
        "answer": "π/6",
        "answer_type": "angle",
        "kp": "模与辐角",
        "verify": {"kind": "arg", "z": "√3/2+i/2"},
        "explain": "z 的模为 1，辐角为 π/6（第一象限内 tan θ = (1/2)/(√3/2) = 1/√3），"
                   "故 Arg z = π/6。",
    },
    {
        "id": "f_cv_08",
        "score": 3,
        "stem": "复数 (1 + i)/(1 - i) 等于 ______。",
        "answer": "i",
        "answer_type": "complex",
        "kp": "四则运算",
        "verify": {"kind": "op", "op": "div", "left": "1+i", "right": "1-i"},
        "explain": "(1+i)/(1-i) = (1+i)(1+i)/((1-i)(1+i)) = (1+2i+i²)/(1-i²) = 2i/2 = i。"
                   "除法先乘分母的共轭有理化是关键步骤。",
    },
    {
        "id": "f_cv_09",
        "score": 3,
        "stem": "复数 1/(1 + i) 等于 ______。",
        "answer": "1/2-1/2i",
        "answer_type": "complex",
        "kp": "四则运算",
        "verify": {"kind": "op", "op": "div", "left": "1", "right": "1+i"},
        "explain": "1/(1+i) = 1·(1-i)/((1+i)(1-i)) = (1-i)/2 = 1/2 - 1/2i。",
    },
    {
        "id": "f_cv_10",
        "score": 3,
        "stem": "复数 (2 + 3i)/(1 - i) 等于 ______。",
        "answer": "-1/2+5/2i",
        "answer_type": "complex",
        "kp": "四则运算",
        "verify": {"kind": "op", "op": "div", "left": "2+3i", "right": "1-i"},
        "explain": "(2+3i)/(1-i) = (2+3i)(1+i)/((1-i)(1+i)) = (2+2i+3i+3i²)/(1-i²) "
                   "= (-1+5i)/2 = -1/2 + 5/2i。",
    },
    {
        "id": "f_cv_11",
        "score": 3,
        "stem": "复数 z = 3 - 4i 的共轭复数 z̄ 是 ______。",
        "answer": "3+4i",
        "answer_type": "complex",
        "kp": "共轭与倒数",
        "verify": {"kind": "conj", "z": "3-4i"},
        "explain": "共轭复数把虚部变号：z̄ = x - yi = 3 + 4i；它与 z 关于实轴对称。",
    },
    {
        "id": "f_cv_12",
        "score": 3,
        "stem": "复数 z = 2i 的倒数 1/z 等于 ______。",
        "answer": "-i/2",
        "answer_type": "complex",
        "kp": "共轭与倒数",
        "verify": {"kind": "inv", "z": "2i"},
        "explain": "1/(2i) = 1·(-2i)/((2i)(-2i)) = -2i/4 = -i/2；"
                   "也可用 1/z = z̄/|z|² = (-2i)/4 = -i/2。",
    },
    {
        "id": "f_cv_13",
        "score": 3,
        "stem": "复数 (1 + i)^8 等于 ______。",
        "answer": "16",
        "answer_type": "number",
        "kp": "幂与根",
        "verify": {"kind": "pow", "z": "1+i", "n": 8},
        "explain": "(1+i)² = 2i，(1+i)⁴ = (2i)² = -4，(1+i)⁸ = (-4)² = 16。",
    },
    {
        "id": "f_cv_14",
        "score": 3,
        "stem": "(cos π/4 + i sin π/4)⁴ 等于 ______。",
        "answer": "-1",
        "answer_type": "number",
        "kp": "棣莫弗公式",
        "verify": {"kind": "pow", "z": "√2/2+√2i/2", "n": 4},
        "explain": "由棣莫弗公式 (cos θ + i sin θ)⁴ = cos 4θ + i sin 4θ，取 θ = π/4 得 "
                   "cos π + i sin π = -1。也可直接算：(√2/2 + √2/2 i)² = i，再平方得 i² = -1。",
    },
    {
        "id": "f_cv_15",
        "score": 3,
        "stem": "(cos π/6 + i sin π/6)³ 等于 ______。",
        "answer": "i",
        "answer_type": "complex",
        "kp": "棣莫弗公式",
        "verify": {"kind": "pow", "z": "√3/2+i/2", "n": 3},
        "explain": "(cos θ + i sin θ)³ = cos 3θ + i sin 3θ，θ = π/6 时 3θ = π/2，"
                   "故值为 cos π/2 + i sin π/2 = i。",
    },
    {
        "id": "f_cv_16",
        "score": 3,
        "stem": "复指数函数 e^z 的一个周期是 ______。",
        "answer": "2πi",
        "answer_type": "complex",
        "kp": "复指数函数",
        "explain": "e^{z+2πi} = e^z·e^{2πi} = e^z·1 = e^z，所以 2πi 是 e^z 的周期"
                   "（也是它的基本周期）。",
    },
    {
        "id": "f_cv_17",
        "score": 3,
        "stem": "取主值分支时，Log i 的值是 ______。",
        "answer": "iπ/2",
        "answer_type": "complex",
        "kp": "复对数函数",
        "explain": "Log z = ln|z| + i·Arg z。对 z = i：|i| = 1，Arg i = π/2，"
                   "故 Log i = ln 1 + i·π/2 = iπ/2。",
    },
    {
        "id": "f_cv_18",
        "score": 3,
        "stem": "按主值定义 z^α = e^{α Log z}，则 (-1)^{1/2} 的全部值是 ______（写出任意一个即可）。",
        "answer": ["i", "-i"],
        "answer_type": "complex",
        "kp": "复幂函数",
        "explain": "log(-1) = ln 1 + i(π + 2kπ) = i(2k+1)π，故 (-1)^{1/2} = e^{(1/2)i(2k+1)π} "
                   "= ±i。答 i 或 -i 均可。",
    },
    {
        "id": "f_cv_19",
        "score": 3,
        "stem": "复变函数 sin z = 0 的最小正实数解是 ______（用 π 的倍数表示）。",
        "answer": "π",
        "answer_type": "angle",
        "kp": "复三角与双曲函数",
        "explain": "sin z = (e^{iz} - e^{-iz})/(2i) = 0 ⟺ e^{2iz} = 1 ⟺ 2iz = 2kπi ⟺ z = kπ，"
                   "故零点为全体整数倍的 π，最小正实数解是 π。",
    },
    {
        "id": "f_cv_20",
        "score": 3,
        "stem": "设复变函数 w = f(z) = z²，z = x + yi，则 f 的实部 u(x, y) 在点 z = 1 + i 处的值是 ______。",
        "answer": "0",
        "answer_type": "number",
        "kp": "复变函数概念",
        "explain": "(x + yi)² = (x² - y²) + 2xyi，所以 u = x² - y²，v = 2xy。"
                   "代入 x = 1, y = 1 得 u(1, 1) = 1 - 1 = 0，v(1, 1) = 2。",
    },
]
