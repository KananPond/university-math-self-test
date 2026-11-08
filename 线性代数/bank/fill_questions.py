# -*- coding: utf-8 -*-
"""
文件名：fill_questions.py
作者：ZCode（GLM）
日期：2026-10-02
版本：1.0
文件说明：
1. 题库：填空题（数值答案），共 16 题。
2. 答案统一写成字符串，支持整数、小数与分数（如 "3/4"）。
3. 凡是能由题面矩阵机械复核的题目都带 verify 校验说明。
"""

FILL = [
    {
        "id": "f_la_01",
        "score": 3,
        "stem": "计算三阶行列式 [[D]] = ______。",
        "matrices": {"D": {"style": "det",
                           "data": [[1, 2, 3], [4, 5, 6], [7, 8, 10]]}},
        "answer": "-3",
        "verify": {"kind": "det", "matrix": "D"},
        "explain": "对角线法则或按第一行展开："
                   "1·(5×10 − 6×8) − 2·(4×10 − 6×7) + 3·(4×8 − 5×7) "
                   "= 2 + 4 − 9 = −3。",
    },
    {
        "id": "f_la_02",
        "score": 3,
        "stem": "行列式 [[D]] = ______。",
        "matrices": {"D": {"style": "det",
                           "data": [[1, 1, 1], [1, 2, 3], [1, 4, 9]]}},
        "answer": "2",
        "verify": {"kind": "det", "matrix": "D"},
        "explain": "这是范德蒙德行列式，值为 (x₂−x₁)(x₃−x₁)(x₃−x₂) "
                   "= 1×2×1 = 2。也可用列变换后按定义计算。",
    },
    {
        "id": "f_la_03",
        "score": 3,
        "stem": "设 A 为 3 阶可逆矩阵且 |A| = 3，则 |A⁻¹| = ______。",
        "answer": "1/3",
        "explain": "由 AA⁻¹ = E 取行列式得 |A||A⁻¹| = 1，"
                   "故 |A⁻¹| = 1/|A| = 1/3。",
    },
    {
        "id": "f_la_04",
        "score": 3,
        "stem": "设 3 阶方阵 A 的特征值为 1, 2, 3，则 |A + E| = ______。",
        "answer": "24",
        "explain": "A + E 的特征值为 λ + 1，即 2, 3, 4，"
                   "行列式等于特征值之积 2×3×4 = 24。",
    },
    {
        "id": "f_la_05",
        "score": 3,
        "stem": "向量 [[alpha]] 的长度（模）‖α‖ = ______。",
        "matrices": {"alpha": {"label": "α", "data": [[1], [2], [2]]}},
        "answer": "3",
        "explain": "‖α‖ = √(1² + 2² + 2²) = √9 = 3。",
    },
    {
        "id": "f_la_06",
        "score": 3,
        "stem": "矩阵 [[A]] 的秩 r(A) = ______。",
        "matrices": {"A": {"data": [[1, 2], [2, 4]]}},
        "answer": "1",
        "verify": {"kind": "rank", "matrix": "A"},
        "explain": "第二行是第一行的 2 倍，行阶梯形只剩 1 个非零行，"
                   "故 r(A) = 1。",
    },
    {
        "id": "f_la_07",
        "score": 3,
        "stem": "设 [[alpha]]，[[beta]]，则内积 (α, β) = αᵀβ = ______。",
        "matrices": {
            "alpha": {"label": "α", "data": [[1], [-1], [0]]},
            "beta": {"label": "β", "data": [[2], [1], [3]]},
        },
        "answer": "1",
        "explain": "(α, β) = 1×2 + (−1)×1 + 0×3 = 1。",
    },
    {
        "id": "f_la_08",
        "score": 3,
        "stem": "齐次线性方程组 x₁ + x₂ + x₃ = 0 的基础解系含有 ______ 个"
                "解向量。",
        "answer": "2",
        "verify": {"kind": "free_count", "matrix_literal": [[1, 1, 1]]},
        "explain": "未知量个数 n = 3，系数矩阵只有一行且非零，r(A) = 1，"
                   "基础解系含 n − r = 2 个向量。",
    },
    {
        "id": "f_la_09",
        "score": 3,
        "stem": "用克莱姆法则解方程组 x + y = 3，x − y = 1，则 x = ______。",
        "answer": "2",
        "verify": {"kind": "solve_component", "aug_literal": [[1, 1, 3], [1, -1, 1]],
                   "component": 0},
        "explain": "系数行列式 D = 1×(−1) − 1×1 = −2，"
                   "Dₓ = 3×(−1) − 1×1 = −4，x = Dₓ/D = 2（y = 1）。",
    },
    {
        "id": "f_la_10",
        "score": 3,
        "stem": "设 A 为 4 阶方阵且 r(A) = 2，则 |A| = ______。",
        "answer": "0",
        "explain": "r(A) = 2 < 4，A 的所有 3、4 阶子式全为零，A 不可逆，"
                   "故 |A| = 0。",
    },
    {
        "id": "f_la_11",
        "score": 3,
        "stem": "已知 2 是矩阵 [[A]] 的一个特征值，则 a = ______。",
        "matrices": {"A": {"data": [["a", 1], [1, 1]]}},
        "answer": "1",
        "verify": {"kind": "sub_det_zero", "matrix": "A", "var": "a",
                   "eigen": 2},
        "explain": "特征值满足 |A − 2E| = 0："
                   "|a−2, 1; 1, −1| = −(a−2) − 1 = −a + 1 = 0，得 a = 1。",
    },
    {
        "id": "f_la_12",
        "score": 3,
        "stem": "设矩阵 [[A]]，则 |2A| = ______。",
        "matrices": {"A": {"data": [[1, 2], [3, 4]]}},
        "answer": "-8",
        "verify": {"kind": "det_scale", "matrix": "A", "k": 2},
        "explain": "|2A| = 2²|A| = 4 × (1×4 − 2×3) = 4 × (−2) = −8。"
                   "注意 2|A| = −4 与 |2A| = −8 的区别。",
    },
    {
        "id": "f_la_13",
        "score": 3,
        "stem": "设 2 阶方阵 A 的特征值为 2 和 3，则 |A| = ______。",
        "answer": "6",
        "explain": "方阵的行列式等于全部特征值之积：|A| = 2×3 = 6。",
    },
    {
        "id": "f_la_14",
        "score": 3,
        "stem": "二次型 f(x, y) = x² + 4xy + 2y² 的矩阵的行列式等于 ______。",
        "answer": "-2",
        "verify": {"kind": "det", "matrix_literal": [[1, 2], [2, 2]]},
        "explain": "交叉项系数 4 平分给 a₁₂ 与 a₂₁，矩阵为 [[1,2],[2,2]]，"
                   "行列式 = 1×2 − 2×2 = −2。",
    },
    {
        "id": "f_la_15",
        "score": 3,
        "stem": "齐次线性方程组 [[M]] 的系数矩阵的秩为 2，"
                "则它的基础解系含有 ______ 个解向量。",
        "matrices": {"M": {"label": "", "style": "aug",
                           "data": [[1, 2, -1, 0], [1, 2, 1, 0]]}},
        "answer": "1",
        "verify": {"kind": "free_count", "matrix_literal": [[1, 2, -1], [1, 2, 1]]},
        "explain": "未知量 n = 3，r(A) = 2，基础解系含 n − r = 1 个向量。"
                   "两式相减得 x₃ = 0，代回得 x₁ = −2x₂，基础解系如 (−2, 1, 0)ᵀ。",
    },
    {
        "id": "f_la_16",
        "score": 3,
        "stem": "设 A 为 3 阶可逆矩阵且 |A| = 1/2，则 |A*| = ______。",
        "answer": "1/4",
        "explain": "|A*| = |A|ⁿ⁻¹ = |A|² = (1/2)² = 1/4。",
    },
]
