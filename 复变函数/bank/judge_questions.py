# -*- coding: utf-8 -*-
"""
文件名：judge_questions.py
作者：Worker
日期：2026-11-08
版本：1.0
文件说明：
复变函数（§2.1）判断题题库，纯数据模块。
共 20 题，id 形如 j_cv_01 ~ j_cv_20，每题 2 分。
answer 必须是 Python 布尔值。
"""

JUDGE = [
    {
        "id": "j_cv_01",
        "score": 2,
        "stem": "复数 z 与它的共轭复数 z̄ 在复平面上关于实轴对称。",
        "answer": True,
        "kp": "复数的表示",
        "explain": "z = x + yi 对应点 (x, y)，z̄ = x - yi 对应点 (x, -y)，两点关于实轴对称。"
                   "相应地 |z̄| = |z|。",
    },
    {
        "id": "j_cv_02",
        "score": 2,
        "stem": "复数 z = 3 + 4i 在复平面上对应的点是 (3, 4)。",
        "answer": True,
        "kp": "复数的表示",
        "explain": "实轴为横轴、虚轴为纵轴，实部 3 对应横坐标，虚部 4 对应纵坐标，故对应点为 (3, 4)。",
    },
    {
        "id": "j_cv_03",
        "score": 2,
        "stem": "arg z 与 Arg z 是同一个概念。",
        "answer": False,
        "kp": "模与辐角",
        "explain": "arg z 是多值的：arg z = Arg z + 2kπ (k ∈ Z)；Arg z 是主值，"
                   "取在 (-π, π] 内。两者含义不同，不能混用。",
    },
    {
        "id": "j_cv_04",
        "score": 2,
        "stem": "主值辐角 Arg z 的取值范围是 (-π, π]。",
        "answer": True,
        "kp": "模与辐角",
        "explain": "定义 Arg z 为 arg z 中落在 (-π, π] 内的那个值。注意负实轴上的点"
                   "（如 z = -1）取 Arg z = π 而不是 -π。",
    },
    {
        "id": "j_cv_05",
        "score": 2,
        "stem": "对任意复数 z = x + yi，都有 |z| = √(x² + y²)。",
        "answer": True,
        "kp": "模与辐角",
        "explain": "|z|² = z·z̄ = (x + yi)(x - yi) = x² + y²，故 |z| = √(x² + y²) ≥ 0。",
    },
    {
        "id": "j_cv_06",
        "score": 2,
        "stem": "(1 + i)(1 - i) = 2i。",
        "answer": False,
        "kp": "四则运算",
        "explain": "(1+i)(1-i) = 1 - i + i - i² = 1 + 1 = 2，即 |1+i|² = 2，不是 2i。",
    },
    {
        "id": "j_cv_07",
        "score": 2,
        "stem": "复数除法必须先把分母有理化，即分子分母同乘分母的共轭复数。",
        "answer": True,
        "kp": "四则运算",
        "explain": "对 a/b，分子分母同乘 b̄ 得 a·b̄/|b|²，这正是 1/b = b̄/|b|² 的应用。"
                   "只适用于 b ≠ 0。",
    },
    {
        "id": "j_cv_08",
        "score": 2,
        "stem": "当 z ≠ 0 时，1/z = z̄/|z|²。",
        "answer": True,
        "kp": "共轭与倒数",
        "explain": "由 z·z̄ = |z|²，两边同除 |z|² 得 z̄/|z|² = 1/z。"
                   "该式是复数除法有理化的依据。",
    },
    {
        "id": "j_cv_09",
        "score": 2,
        "stem": "|z̄| = |z| 对任何复数 z 都成立。",
        "answer": True,
        "kp": "共轭与倒数",
        "explain": "|z̄|² = x² + (-y)² = x² + y² = |z|²，两者非负故 |z̄| = |z|。",
    },
    {
        "id": "j_cv_10",
        "score": 2,
        "stem": "i⁴ = 1，且对任意整数 k 有 i^{4k+1} = i。",
        "answer": True,
        "kp": "幂与根",
        "explain": "i, i² = -1, i³ = -i, i⁴ = 1，之后按 4 循环。"
                   "i^{4k+1} = (i⁴)^k·i = i。",
    },
    {
        "id": "j_cv_11",
        "score": 2,
        "stem": "(1 + i)⁴ = -4。",
        "answer": True,
        "kp": "幂与根",
        "explain": "(1+i)² = 1 + 2i + i² = 2i，(1+i)⁴ = (2i)² = 4i² = -4，"
                   "再平方得 (1+i)⁸ = 16。",
    },
    {
        "id": "j_cv_12",
        "score": 2,
        "stem": "(cos θ + i sin θ)ⁿ = cos nθ + i sin nθ 对任意正整数 n 都成立。",
        "answer": True,
        "kp": "棣莫弗公式",
        "explain": "这就是棣莫弗公式。由它可推出 z = r(cos θ + i sin θ) 时 "
                   "zⁿ = rⁿ(cos nθ + i sin nθ)，是求幂与开方的基础工具。",
    },
    {
        "id": "j_cv_13",
        "score": 2,
        "stem": "复指数函数 e^z 是周期函数，周期为 2πi。",
        "answer": True,
        "kp": "复指数函数",
        "explain": "e^{z+2πi} = e^z·e^{2πi} = e^z·1 = e^z，故 2πi 是它的周期。",
    },
    {
        "id": "j_cv_14",
        "score": 2,
        "stem": "方程 e^z = 0 在复数域中有解。",
        "answer": False,
        "kp": "复指数函数",
        "explain": "e^z = e^x(cos y + i sin y)，其中 e^x > 0 且 cos y + i sin y ≠ 0，"
                   "故 e^z ≠ 0 恒成立，方程无解。",
    },
    {
        "id": "j_cv_15",
        "score": 2,
        "stem": "对任意 z₁ ≠ 0, z₂ ≠ 0，恒有 log(z₁z₂) = log z₁ + log z₂。",
        "answer": False,
        "kp": "复对数函数",
        "explain": "复对数多值，正确关系是 log(z₁z₂) = log z₁ + log z₂ + 2kπi，"
                   "是否相等取决于支路的选取。例如取主值时 log(-1) + log(-1) = 2iπ，"
                   "而 log((-1)(-1)) = log 1 = 0，相差 2πi。",
    },
    {
        "id": "j_cv_16",
        "score": 2,
        "stem": "取主值分支时，Log z = ln|z| + i·Arg z，其中 Arg z ∈ (-π, π]。",
        "answer": True,
        "kp": "复对数函数",
        "explain": "由 e^{ln|z| + i Arg z} = |z|(cos Arg z + i sin Arg z) = z 可得。"
                   "以负实轴为割线切开复平面即得主值分支。",
    },
    {
        "id": "j_cv_17",
        "score": 2,
        "stem": "幂律 (z^α)^β = z^{αβ} 对任意 z ≠ 0 和任意复数 α、β 恒成立。",
        "answer": False,
        "kp": "复幂函数",
        "explain": "反例：按主值定义 ((-1)²)^{1/2} = 1^{1/2} = 1，而 (-1)^{2·(1/2)} = -1，"
                   "两者不等。原因是取 Log 时引入了 2kπi 的多值性。",
    },
    {
        "id": "j_cv_18",
        "score": 2,
        "stem": "sin z = 0 当且仅当 z = nπ (n ∈ Z)。",
        "answer": True,
        "kp": "复三角与双曲函数",
        "explain": "sin z = (e^{iz} - e^{-iz})/(2i) = 0 ⟺ e^{2iz} = 1 ⟺ 2iz = 2kπi ⟺ z = kπ。"
                   "这与实数情形一致，是棣莫弗公式的推论。",
    },
    {
        "id": "j_cv_19",
        "score": 2,
        "stem": "sin z 在虚轴上有界。",
        "answer": False,
        "kp": "复三角与双曲函数",
        "explain": "由 |sin z|² = sin²x + sinh²y，在 x = 0 处 |sin(iy)| = |sinh y| → ∞ (y → +∞)，"
                   "故 sin z 在虚轴上无界，确界为 ∞。",
    },
    {
        "id": "j_cv_20",
        "score": 2,
        "stem": "确定一个复变函数 w = f(z)，必须同时说明其定义域 D 与对应关系。",
        "answer": True,
        "kp": "复变函数概念",
        "explain": "复变函数是定义在复平面某区域 D 上、取值于复平面的对应关系，"
                   "记作 w = f(z)，z ∈ D。其值域为 f(D) = {f(z) : z ∈ D}。",
    },
]
