# -*- coding: utf-8 -*-
"""
文件名：choice_questions.py
作者：Worker
日期：2026-11-08
版本：1.0
文件说明：
复变函数（§2.1）选择题题库，纯数据模块。
共 24 题，id 形如 c_cv_01 ~ c_cv_24，每题 3 分。
知识点标签见 bank/FORMAT.md 的受控词表。
"""

CHOICE = [
    {
        "id": "c_cv_01",
        "score": 3,
        "stem": "复数 z = 1 + i 在复平面上的位置如 [[P]] 所示，它的三角形式是（　　）。",
        "options": [
            "√2(cos π/4 + i sin π/4)",
            "√2(cos π/3 + i sin π/3)",
            "2(cos π/4 + i sin π/4)",
            "√2(cos π/4 - i sin π/4)",
        ],
        "answer": 0,
        "kp": "复数的表示",
        "figures": {
            "P": {"kind": "point", "z": "1+i", "label": "z",
                  "show": ["radius", "angle", "proj"]},
        },
        "explain": "|z| = √(1² + 1²) = √2。z 在第一象限且 tan θ = 1/1 = 1，故 θ = π/4，"
                   "于是 z = √2(cos π/4 + i sin π/4)。常见错误是把模写成 2，或把虚部符号取反。",
    },
    {
        "id": "c_cv_02",
        "score": 3,
        "stem": "复数 z = 3 + 4i 的指数形式是（　　）。",
        "options": [
            "5e^{i arctan(4/3)}",
            "4e^{i arctan(3/4)}",
            "5e^{i arctan(3/4)}",
            "5e^{-i arctan(4/3)}",
        ],
        "answer": 0,
        "kp": "复数的表示",
        "explain": "|z| = √(3² + 4²) = 5，arg z = arctan(4/3)。故 z = 5e^{i·arctan(4/3)}。"
                   "易错点是把模算成 4，或把 arctan 的分子分母颠倒。",
    },
    {
        "id": "c_cv_03",
        "score": 3,
        "stem": "复数 z = 2(cos π/3 + i sin π/3) 的代数形式是（　　）。",
        "options": ["1+√3i", "√3+i", "1-√3i", "2+√3i"],
        "answer": 0,
        "kp": "复数的表示",
        "explain": "实部 = 2cos π/3 = 2 × (1/2) = 1，虚部 = 2sin π/3 = 2 × (√3/2) = √3，"
                   "所以 z = 1 + √3i。",
    },
    {
        "id": "c_cv_04",
        "score": 3,
        "stem": "在复平面上，复数 z = x + yi 对应的点是（　　）。",
        "options": ["点 (x, y)", "点 (y, x)", "点 (-x, -y)", "点 (x, -y)"],
        "answer": 0,
        "kp": "复数的表示",
        "explain": "取实轴为横轴、虚轴为纵轴建立复坐标系，则 z = x + yi 对应点 (x, y)："
                   "实部对应横坐标，虚部对应纵坐标。",
    },
    {
        "id": "c_cv_05",
        "score": 3,
        "stem": "复数 z = 3 + 4i 的模 |z| 是（　　）。",
        "options": ["5", "7", "25", "√7"],
        "answer": 0,
        "kp": "模与辐角",
        "verify": {"kind": "modulus", "z": "3+4i", "option": 0},
        "explain": "|z| = √(x² + y²) = √(3² + 4²) = √25 = 5。注意模要开方，"
                   "把 x² + y² = 25 直接当模是典型错误。",
    },
    {
        "id": "c_cv_06",
        "score": 3,
        "stem": "复数 z = -1 - i 的主值辐角 Arg z 是（　　）。",
        "options": ["-3π/4", "3π/4", "5π/4", "-π/4"],
        "answer": 0,
        "kp": "模与辐角",
        "verify": {"kind": "arg", "z": "-1-i", "option": 0},
        "explain": "z 在第三象限，tan θ = (-1)/(-1) = 1。主值范围是 (-π, π]，"
                   "第三象限对应 -3π/4，故 Arg z = -3π/4。写成 5π/4 就超出了主值范围。",
    },
    {
        "id": "c_cv_07",
        "score": 3,
        "stem": "复数 z = i（如 [[P]]）的所有辐角组成的集合是（　　）。",
        "options": [
            "{π/2 + 2kπ | k ∈ Z}",
            "{π/2 + kπ | k ∈ Z}",
            "{π/2}",
            "{kπ | k ∈ Z}",
        ],
        "answer": 0,
        "kp": "模与辐角",
        "figures": {
            "P": {"kind": "point", "z": "i", "label": "z",
                  "show": ["radius", "angle"]},
        },
        "explain": "arg z 是多值的：arg z = Arg z + 2kπ = π/2 + 2kπ (k ∈ Z)。"
                   "若取 π/2 + kπ，则 k = 1 时得到 3π/2，那是 -i 的辐角，不是 z 的辐角。",
    },
    {
        "id": "c_cv_08",
        "score": 3,
        "stem": "复数 (1 + i)(1 - i) 等于（　　）。",
        "options": ["2", "2i", "0", "-2"],
        "answer": 0,
        "kp": "四则运算",
        "verify": {"kind": "op", "op": "mul", "left": "1+i", "right": "1-i", "option": 0},
        "explain": "(1+i)(1-i) = 1 - i + i - i² = 1 + 1 = 2。这也是共轭相乘的经典值 "
                   "|1+i|² = (√2)² = 2。",
    },
    {
        "id": "c_cv_09",
        "score": 3,
        "stem": "复数 (1 + i)/(1 - i) 等于（　　）。[[O]]",
        "options": ["i", "-i", "1", "2i"],
        "answer": 0,
        "kp": "四则运算",
        "verify": {"kind": "op", "op": "div", "left": "1+i", "right": "1-i", "option": 0},
        "figures": {
            "O": {"kind": "ops", "z1": "1+i", "z2": "1-i",
                  "label1": "z₁", "label2": "z₂"},
        },
        "explain": "分子分母同乘分母的共轭 (1+i)：(1+i)(1+i)/((1-i)(1+i)) = (1+2i+i²)/(1-i²) "
                   "= 2i/2 = i。关键是先有理化，直接约分是高频错点。",
    },
    {
        "id": "c_cv_10",
        "score": 3,
        "stem": "复数 1/(1 + i) 等于（　　）。",
        "options": ["1/2-1/2i", "1/2+1/2i", "1-i", "1+i"],
        "answer": 0,
        "kp": "四则运算",
        "verify": {"kind": "op", "op": "div", "left": "1", "right": "1+i", "option": 0},
        "explain": "1/(1+i) = 1·(1-i)/((1+i)(1-i)) = (1-i)/2 = 1/2 - 1/2i。"
                   "若忘记乘共轭因子就会误选 1-i。",
    },
    {
        "id": "c_cv_11",
        "score": 3,
        "stem": "复数 (2 + 3i)/(1 - i) 等于（　　）。[[O]]",
        "options": ["-1/2+5/2i", "1/2+5/2i", "-1/2-5/2i", "5/2-1/2i"],
        "answer": 0,
        "kp": "四则运算",
        "verify": {"kind": "op", "op": "div", "left": "2+3i", "right": "1-i", "option": 0},
        "figures": {
            "O": {"kind": "ops", "z1": "2+3i", "z2": "1-i",
                  "label1": "z₁", "label2": "z₂"},
        },
        "explain": "(2+3i)/(1-i) = (2+3i)(1+i)/((1-i)(1+i)) = (2+2i+3i+3i²)/(1-i²) "
                   "= (-1+5i)/2 = -1/2 + 5/2i。",
    },
    {
        "id": "c_cv_12",
        "score": 3,
        "stem": "复数 z = 3 - 4i 的共轭复数 z̄ 是（　　）。",
        "options": ["3+4i", "3-4i", "-3+4i", "-3-4i"],
        "answer": 0,
        "kp": "共轭与倒数",
        "verify": {"kind": "conj", "z": "3-4i", "option": 0},
        "explain": "共轭复数只把虚部变号：z̄ = x - yi = 3 + 4i。"
                   "它在复平面上与 z 关于实轴对称，且 |z̄| = |z| = 5。",
    },
    {
        "id": "c_cv_13",
        "score": 3,
        "stem": "复数 1/(2i) 等于（　　）。",
        "options": ["-i/2", "i/2", "-2i", "2i"],
        "answer": 0,
        "kp": "共轭与倒数",
        "verify": {"kind": "inv", "z": "2i", "option": 0},
        "explain": "1/(2i) = 1·(-2i)/((2i)(-2i)) = -2i/4 = -i/2。"
                   "用公式 1/z = z̄/|z|² 也一样：z̄ = -2i，|z|² = 4。",
    },
    {
        "id": "c_cv_14",
        "score": 3,
        "stem": "复数 i 的 2025 次幂 i^{2025} 等于（　　）。",
        "options": ["i", "-i", "-1", "1"],
        "answer": 0,
        "kp": "幂与根",
        "verify": {"kind": "pow", "z": "i", "n": 2025, "option": 0},
        "explain": "i 的幂以 4 为周期：i, -1, -i, 1, i, …。2025 = 4×506 + 1，"
                   "故 i^{2025} = (i⁴)^{506}·i = 1^{506}·i = i。",
    },
    {
        "id": "c_cv_15",
        "score": 3,
        "stem": "复数 (1 + i)^8 等于（　　）。",
        "options": ["16", "16i", "-16", "8"],
        "answer": 0,
        "kp": "幂与根",
        "verify": {"kind": "pow", "z": "1+i", "n": 8, "option": 0},
        "explain": "(1+i)² = 2i，(1+i)⁴ = (2i)² = -4，(1+i)⁸ = (-4)² = 16。"
                   "这些经典值要背下来。",
    },
    {
        "id": "c_cv_16",
        "score": 3,
        "stem": "方程 z² = -1 的一个根是（　　）。[[R]]",
        "options": ["i", "-i", "1", "-1"],
        "answer": 0,
        "kp": "幂与根",
        "verify": {"kind": "root_of", "z": "-1", "n": 2, "option": 0},
        "figures": {
            "R": {"kind": "roots", "n": 2, "radius": 1, "label": "z² = -1 的根"},
        },
        "explain": "由 i² = -1 知 z = ±i 都是方程的根；二次方程在复数域上恰有两个根，"
                   "它们互为相反数，都落在单位圆上。",
    },
    {
        "id": "c_cv_17",
        "score": 3,
        "stem": "由棣莫弗公式，(cos π/3 + i sin π/3)³ 等于（　　）。",
        "options": ["-1", "1", "i", "-i"],
        "answer": 0,
        "kp": "棣莫弗公式",
        "verify": {"kind": "pow", "z": "1/2+√3i/2", "n": 3, "option": 0},
        "explain": "(cos θ + i sin θ)³ = cos 3θ + i sin 3θ。取 θ = π/3，则 3θ = π，"
                   "cos π + i sin π = -1。",
    },
    {
        "id": "c_cv_18",
        "score": 3,
        "stem": "复数 e^{πi/2} 等于（　　）。",
        "options": ["i", "-i", "1", "-1"],
        "answer": 0,
        "kp": "复指数函数",
        "explain": "e^{iθ} = cos θ + i sin θ，故 e^{πi/2} = cos π/2 + i sin π/2 = 0 + i = i。"
                   "它是单位根之一。",
    },
    {
        "id": "c_cv_19",
        "score": 3,
        "stem": "设 z = x + yi，则 |e^z| 等于（　　）。",
        "options": ["e^x", "e^y", "e^{x+y}", "1"],
        "answer": 0,
        "kp": "复指数函数",
        "explain": "e^z = e^x(cos y + i sin y)，所以 |e^z| = e^x·√(cos²y + sin²y) = e^x。"
                   "复指数的模只由实部决定，实部为负时模也小于 1。",
    },
    {
        "id": "c_cv_20",
        "score": 3,
        "stem": "取主值分支时，Log(-1) 的值是（　　）。",
        "options": ["iπ", "-iπ", "π", "-π"],
        "answer": 0,
        "kp": "复对数函数",
        "explain": "Log z = ln|z| + i·Arg z。|-1| = 1，Arg(-1) = π ∈ (-π, π]，"
                   "故 Log(-1) = ln 1 + iπ = iπ。",
    },
    {
        "id": "c_cv_21",
        "score": 3,
        "stem": "复数 z（z ≠ 0）的对数 log z 的所有值组成的集合是（　　）。",
        "options": [
            "{ln|z| + i(arg z + 2kπ) | k ∈ Z}",
            "{ln|z| + i·Arg z}",
            "{ln|z| + 2kπ | k ∈ Z}",
            "{arg z + 2kπ | k ∈ Z}",
        ],
        "answer": 0,
        "kp": "复对数函数",
        "explain": "复对数是多值的：log z = ln|z| + i(arg z + 2kπ) = ln|z| + i(Arg z + 2kπ)，"
                   "k ∈ Z。取主值只得到其中一个值 Log z = ln|z| + i·Arg z，其余各值相差 2kπi。",
    },
    {
        "id": "c_cv_22",
        "score": 3,
        "stem": "按主值定义 z^α = e^{α Log z}，则 (-1)^{1/2} 的主值是（　　）。",
        "options": ["i", "-i", "1", "-1"],
        "answer": 0,
        "kp": "复幂函数",
        "explain": "Log(-1) = iπ，故 (-1)^{1/2} = e^{(1/2)·iπ} = e^{iπ/2} "
                   "= cos π/2 + i sin π/2 = i。全部值为 ±i，其中 i 是主值。",
    },
    {
        "id": "c_cv_23",
        "score": 3,
        "stem": "复变函数 sin z = 0 的全部解是（　　）。",
        "options": [
            "z = nπ (n ∈ Z)",
            "z = nπi (n ∈ Z)",
            "z = (n + 1/2)π (n ∈ Z)",
            "z = n (n ∈ Z)",
        ],
        "answer": 0,
        "kp": "复三角与双曲函数",
        "explain": "sin z = (e^{iz} - e^{-iz})/(2i) = 0 ⟺ e^{iz} = e^{-iz} ⟺ e^{2iz} = 1 "
                   "⟺ 2iz = 2kπi ⟺ z = kπ。所以零点恰是全体整数倍的 π。",
    },
    {
        "id": "c_cv_24",
        "score": 3,
        "stem": "设 w = f(z) = z²，z = x + yi，则 w = u(x, y) + iv(x, y) 中的 u(x, y) 与 v(x, y) 是（　　）。",
        "options": [
            "u = x² - y², v = 2xy",
            "u = x² + y², v = 2xy",
            "u = 2xy, v = x² - y²",
            "u = x² - y², v = -2xy",
        ],
        "answer": 0,
        "kp": "复变函数概念",
        "explain": "(x + yi)² = x² + 2xyi + y²i² = (x² - y²) + 2xyi，所以 u = x² - y²，"
                   "v = 2xy。复变函数 w = f(z) 本质上就是一对实值函数 u(x, y) 与 v(x, y)。",
    },
]
