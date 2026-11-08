# -*- coding: utf-8 -*-
"""
文件名：calc_questions.py
作者：ZCode（GLM）
日期：2026-10-02
版本：1.0
文件说明：
1. 题库：计算题（矩阵 / 向量作答），共 10 题。
2. 答案是 rows × cols 的矩阵，元素可写成分数字符串。
3. 默认按“正确元素比例”给分；带 grading 字段的题目按语义判分
   （如基础解系不唯一，只要各列都是非零解且线性无关即满分）。
"""

CALC = [
    {
        "id": "x_la_01",
        "score": 5,
        "stem": "设矩阵 [[A]]，求 A 的逆矩阵 A⁻¹。",
        "matrices": {"A": {"data": [[1, 2], [3, 4]]}},
        "answer_type": "matrix",
        "rows": 2,
        "cols": 2,
        "answer": {"rows": 2, "cols": 2,
                   "data": [["-2", "1"], ["3/2", "-1/2"]]},
        "verify": {"kind": "inv", "matrix": "A"},
        "explain": "|A| = 1×4 − 2×3 = −2。A⁻¹ = (1/|A|)A* "
                   "= (1/−2)·[[4,−2],[−3,1]] = [[−2,1],[3/2,−1/2]]。",
    },
    {
        "id": "x_la_02",
        "score": 5,
        "stem": "设上三角矩阵 [[A]]，求 A⁻¹。",
        "matrices": {"A": {"data": [[1, 1, 1], [0, 1, 1], [0, 0, 1]]}},
        "answer_type": "matrix",
        "rows": 3,
        "cols": 3,
        "answer": {"rows": 3, "cols": 3,
                   "data": [["1", "-1", "0"], ["0", "1", "-1"],
                            ["0", "0", "1"]]},
        "verify": {"kind": "inv", "matrix": "A"},
        "explain": "对 (A | E) 作初等行变换化成 (E | A⁻¹)，或按 A X = E 逐列解，"
                   "得 A⁻¹ = [[1,−1,0],[0,1,−1],[0,0,1]]。"
                   "上三角矩阵的逆仍是上三角矩阵。",
    },
    {
        "id": "x_la_03",
        "score": 5,
        "stem": "设矩阵 [[A]] 与 [[B]]，求乘积 AB。",
        "matrices": {
            "A": {"data": [[1, 2], [3, 4]]},
            "B": {"data": [[2, 0], [1, 2]]},
        },
        "answer_type": "matrix",
        "rows": 2,
        "cols": 2,
        "answer": {"rows": 2, "cols": 2,
                   "data": [["4", "4"], ["10", "8"]]},
        "verify": {"kind": "mul", "left": "A", "right": "B"},
        "explain": "AB 的 (i, j) 元等于 A 第 i 行与 B 第 j 列对应乘积之和："
                   "(1,1) 元 = 1×2 + 2×1 = 4，(1,2) 元 = 1×0 + 2×2 = 4，"
                   "(2,1) 元 = 3×2 + 4×1 = 10，(2,2) 元 = 3×0 + 4×2 = 8。",
    },
    {
        "id": "x_la_04",
        "score": 5,
        "stem": "设矩阵 [[A]]，求 A 的属于特征值 λ = 4 的一个特征向量，"
                "写成 2×1 列向量（任何非零倍数均算对）。",
        "matrices": {"A": {"data": [[3, 1], [1, 3]]}},
        "answer_type": "matrix",
        "rows": 2,
        "cols": 1,
        "answer": {"rows": 2, "cols": 1, "data": [["1"], ["1"]]},
        "verify": {"kind": "eigvec", "matrix": "A", "eigen": 4},
        "grading": {"kind": "eigvec", "matrix": "A", "eigen": 4},
        "explain": "解 (A − 4E)x = 0，即 [[−1,1],[1,−1]]x = 0，得 x₁ = x₂，"
                   "取特征向量 (1,1)ᵀ；k(1,1)ᵀ（k ≠ 0）都是正确答案。",
    },
    {
        "id": "x_la_05",
        "score": 5,
        "stem": "解线性方程组 [[M]]，把解写成 3×1 列向量 (x, y, z)ᵀ。",
        "matrices": {"M": {"label": "", "style": "aug",
                           "data": [[1, 1, 1, 6], [1, 2, 3, 14],
                                    [1, 4, 9, 36]]}},
        "answer_type": "matrix",
        "rows": 3,
        "cols": 1,
        "answer": {"rows": 3, "cols": 1, "data": [["1"], ["2"], ["3"]]},
        "verify": {"kind": "solve", "matrix": "M"},
        "explain": "消元：第二式减第一式得 y + 2z = 8，第三式减第一式得 "
                   "3y + 8z = 30，解得 z = 3，y = 2，回代得 x = 1。"
                   "解向量为 (1, 2, 3)ᵀ。",
    },
    {
        "id": "x_la_06",
        "score": 5,
        "stem": "设列向量 [[alpha]] 与 [[beta]]，求外积 αβᵀ（2×2 矩阵）。",
        "matrices": {
            "alpha": {"label": "α", "data": [[1], [2]]},
            "beta": {"label": "β", "data": [[3], [4]]},
        },
        "answer_type": "matrix",
        "rows": 2,
        "cols": 2,
        "answer": {"rows": 2, "cols": 2,
                   "data": [["3", "4"], ["6", "8"]]},
        "verify": {"kind": "outer", "left": "alpha", "right": "beta"},
        "explain": "αβᵀ 的 (i, j) 元 = αᵢβⱼ，即 [[1×3, 1×4], [2×3, 2×4]] "
                   "= [[3,4],[6,8]]。注意与内积 αᵀβ = 11（1×1）的区别。",
    },
    {
        "id": "x_la_07",
        "score": 5,
        "stem": "求齐次线性方程组（系数矩阵 [[A]]）的基础解系："
                "把两个基础解向量按列排成 4×2 矩阵作答。"
                "基础解系不唯一，任何一组都按判分规则计分。",
        "matrices": {"A": {"data": [[1, 1, 1, 1], [1, 2, 3, 4]]}},
        "answer_type": "matrix",
        "rows": 4,
        "cols": 2,
        "answer": {"rows": 4, "cols": 2,
                   "data": [["1", "2"], ["-2", "-3"], ["1", "0"], ["0", "1"]]},
        "verify": {"kind": "null_basis", "matrix": "A"},
        "grading": {"kind": "null_basis", "matrix": "A"},
        "explain": "行变换得行最简形 [[1,0,−1,−2],[0,1,2,3]]，"
                   "x₃、x₄ 为自由未知量：x₁ = x₃ + 2x₄，x₂ = −2x₃ − 3x₄。"
                   "取 (x₃,x₄) = (1,0),(0,1) 得 ξ₁ = (1,−2,1,0)ᵀ，"
                   "ξ₂ = (2,−3,0,1)ᵀ。",
    },
    {
        "id": "x_la_08",
        "score": 5,
        "stem": "设列向量 [[alpha]] 与 [[beta]]，求内积 αᵀβ，"
                "结果写成 1×1 矩阵。",
        "matrices": {
            "alpha": {"label": "α", "data": [[1], [2], [3]]},
            "beta": {"label": "β", "data": [[4], [5], [6]]},
        },
        "answer_type": "matrix",
        "rows": 1,
        "cols": 1,
        "answer": {"rows": 1, "cols": 1, "data": [["32"]]},
        "verify": {"kind": "inner", "left": "alpha", "right": "beta"},
        "explain": "αᵀ 是 1×3 矩阵，αᵀβ = 1×4 + 2×5 + 3×6 = 32，"
                   "结果为 1×1 矩阵 [[32]]。与外积（3×3 矩阵）对比记忆。",
    },
    {
        "id": "x_la_09",
        "score": 5,
        "stem": "设矩阵 [[A]]（它把平面上的点逆时针旋转 90°），求 A²。",
        "matrices": {"A": {"data": [[0, 1], [-1, 0]]}},
        "answer_type": "matrix",
        "rows": 2,
        "cols": 2,
        "answer": {"rows": 2, "cols": 2,
                   "data": [["-1", "0"], ["0", "-1"]]},
        "verify": {"kind": "power", "matrix": "A", "n": 2},
        "explain": "A² = [[0,1],[−1,0]]·[[0,1],[−1,0]] = [[−1,0],[0,−1]] = −E。"
                   "连续旋转两个 90° 相当于旋转 180°，向量全部反向。",
    },
    {
        "id": "x_la_10",
        "score": 5,
        "stem": "设矩阵 [[A]]，求 A⁻¹。",
        "matrices": {"A": {"data": [[1, 0, 2], [0, 1, 0], [0, 0, 1]]}},
        "answer_type": "matrix",
        "rows": 3,
        "cols": 3,
        "answer": {"rows": 3, "cols": 3,
                   "data": [["1", "0", "-2"], ["0", "1", "0"],
                            ["0", "0", "1"]]},
        "verify": {"kind": "inv", "matrix": "A"},
        "explain": "A = E + N，N = [[0,0,2],[0,0,0],[0,0,0]] 满足 N² = O，"
                   "故 A⁻¹ = E − N = [[1,0,−2],[0,1,0],[0,0,1]]。"
                   "用初等行变换 (A | E) → (E | A⁻¹) 结果相同。",
    },
]
