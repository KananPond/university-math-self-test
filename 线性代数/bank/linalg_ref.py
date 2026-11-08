# -*- coding: utf-8 -*-
"""
文件名：linalg_ref.py
作者：ZCode（GLM）
日期：2026-10-02
版本：1.0
文件说明：
1. 基于 Fraction 的精确线性代数参考实现，供判分（checker.py）与
   题库校验（verify_paper.py）共同使用。
2. 全部运算在分数域完成，不存在浮点误差；只覆盖 n ≤ 4 的小规模情形。
3. 矩阵一律表示为“行的列表”，元素为 Fraction 或可转 Fraction 的数。
"""

from fractions import Fraction


def to_frac(value):
    """把数字或字符串转成 Fraction，失败返回 None。"""
    if isinstance(value, bool):
        return None
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(value).limit_denominator(10 ** 9)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return Fraction(text)
        except (ValueError, ZeroDivisionError):
            pass
        try:
            return Fraction(float(text))
        except (ValueError, OverflowError):
            return None

    return None


def parse_matrix(data):
    """把二维列表整体转成分数矩阵，任一元素非法返回 None。"""
    if not isinstance(data, list) or not data:
        return None

    rows = []
    for row in data:
        if not isinstance(row, list):
            return None
        converted = []
        for cell in row:
            value = to_frac(cell)
            if value is None:
                return None
            converted.append(value)
        rows.append(converted)

    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        return None

    return rows


def dims(matrix):
    """返回矩阵的 (行数, 列数)。"""
    return len(matrix), len(matrix[0])


def mat_mul(left, right):
    """矩阵乘法，要求左列数等于右行数。"""
    m, k = dims(left)
    k2, n = dims(right)
    if k != k2:
        raise ValueError("形状不匹配")

    result = []
    for i in range(m):
        row = []
        for j in range(n):
            total = Fraction(0)
            for t in range(k):
                total += left[i][t] * right[t][j]
            row.append(total)
        result.append(row)

    return result


def mat_transpose(matrix):
    """矩阵转置。"""
    m, n = dims(matrix)

    return [[matrix[i][j] for i in range(m)] for j in range(n)]


def mat_vec(matrix, vector):
    """矩阵乘列向量。"""
    return mat_mul(matrix, [[v] for v in vector])


def det(matrix):
    """按第一列展开递归求行列式（n ≤ 4 足够）。"""
    m, n = dims(matrix)
    if m != n:
        raise ValueError("行列式只对方阵有定义")
    if n == 1:
        return matrix[0][0]
    if n == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]

    total = Fraction(0)
    for j in range(n):
        minor = [[matrix[i][k] for k in range(n) if k != j]
                 for i in range(1, n)]
        cofactor = matrix[0][j] * det(minor)
        if j % 2 == 0:
            total += cofactor
        else:
            total -= cofactor

    return total


def adjugate(matrix):
    """伴随矩阵：代数余子式按转置摆放。"""
    n, _ = dims(matrix)
    if n == 1:
        return [[Fraction(1)]]

    result = []
    for i in range(n):
        row = []
        for j in range(n):
            minor = [[matrix[r][c] for c in range(n) if c != j]
                     for r in range(n) if r != i]
            sign = -1 if (i + j) % 2 else 1
            row.append(Fraction(sign) * det(minor))
        result.append(row)

    return mat_transpose(result)


def inverse(matrix):
    """方阵求逆，行列式为零抛 ValueError。"""
    d = det(matrix)
    if d == 0:
        raise ValueError("奇异矩阵不可逆")
    adj = adjugate(matrix)
    m, n = dims(adj)

    return [[adj[i][j] / d for j in range(n)] for i in range(m)]


def rref(matrix):
    """行最简形（不整除也保持分数精确），同时返回主元列下标。"""
    result = [row[:] for row in matrix]
    m, n = dims(result)
    pivot_cols = []
    row = 0
    for col in range(n):
        if row >= m:
            break
        found = None
        for i in range(row, m):
            if result[i][col] != 0:
                found = i
                break
        if found is None:
            continue
        result[row], result[found] = result[found], result[row]
        pivot = result[row][col]
        result[row] = [v / pivot for v in result[row]]
        for i in range(m):
            if i != row and result[i][col] != 0:
                factor = result[i][col]
                result[i] = [a - factor * b
                             for a, b in zip(result[i], result[row])]
        pivot_cols.append(col)
        row += 1

    return result, pivot_cols


def rank(matrix):
    """矩阵的秩 = 行最简形主元个数。"""
    _, pivots = rref(matrix)

    return len(pivots)


def solve_square(aug):
    """解 n×(n+1) 增广矩阵对应的方程组，唯一解才返回解向量，否则 None。"""
    m, n = dims(aug)
    if n != m + 1:
        return None
    if rank([row[:-1] for row in aug]) != m:
        return None
    if rank(aug) != m:
        return None

    simplified, _ = rref(aug)
    return [row[-1] for row in simplified]


def null_basis(matrix):
    """求齐次方程组 Ax=0 的一个基础解系（自由未知量依次取 1）。"""
    m, n = dims(matrix)
    simplified, pivots = rref(matrix)
    free_cols = [c for c in range(n) if c not in pivots]

    basis = []
    for free in free_cols:
        vector = []
        pivot_iter = 0
        for col in range(n):
            if col in pivots:
                # 行最简形中主元行对应的系数取相反数
                vector.append(-simplified[pivot_iter][free])
                pivot_iter += 1
            elif col == free:
                vector.append(Fraction(1))
            else:
                vector.append(Fraction(0))
        basis.append(vector)

    return basis


def char_coeffs(matrix):
    """返回特征多项式 λ^n + c1 λ^(n-1) + ... + cn 的系数列表（n ≤ 3 精确公式）。"""
    n, _ = dims(matrix)
    if n == 2:
        # λ² - tr λ + det
        tr = matrix[0][0] + matrix[1][1]
        return [-tr, det(matrix)]
    if n == 3:
        a, b, c = matrix[0]
        d, e, f = matrix[1]
        g, h, i = matrix[2]
        tr = a + e + i
        # det = a(ei − fh) − b(di − fg) + c(dh − eg)
        d3 = (a * (e * i - f * h) - b * (d * i - f * g)
              + c * (d * h - e * g))
        # 主对角二阶子式之和
        c2 = (a * e + a * i + e * i - b * d - c * g - f * h)
        return [-tr, c2, -d3]

    raise ValueError("只支持 2、3 阶特征多项式")


def poly_eval(coeffs_desc, x):
    """按降幂系数列表（首项在前）用秦九韶法求多项式值。"""
    total = Fraction(0)
    for c in coeffs_desc:
        total = total * x + c

    return total


def rational_roots(char_coeffs_asc):
    """求首一整系数多项式的全部有理根（去重）。

    char_coeffs_asc 是升幂的次项系数 [c1, ..., cn]，
    对应首一多项式 λ^n + c1 λ^(n-1) + ... + cn。
    常数项为零时先提出 λ 的幂（0 是根），再对剩余多项式搜索。
    """
    tail = [to_frac(c) for c in char_coeffs_asc]
    if any(c is None for c in tail) or not tail:
        return []

    from math import gcd

    roots = []
    zero_multiplicity = 0
    while tail and tail[-1] == 0:
        # 列表是降幂排列，末尾的 0 是常数项 → λ 是因子，0 是根
        tail = tail[:-1]
        zero_multiplicity += 1
    if zero_multiplicity > 0:
        roots.append(Fraction(0))
    if not tail:
        return roots

    poly = [Fraction(1)] + tail
    # 通分转成整系数，便于用有理根定理枚举
    denom_lcm = 1
    for c in poly:
        denom_lcm = denom_lcm * c.denominator // gcd(denom_lcm, c.denominator)
    ints = [int(c * denom_lcm) for c in poly]

    a0, an = abs(ints[-1]), abs(ints[0])
    divisors0 = [k for k in range(1, a0 + 1) if a0 % k == 0]
    divisorsn = [k for k in range(1, an + 1) if an % k == 0]

    for p in divisors0:
        for q in divisorsn:
            if gcd(p, q) != 1:
                continue
            for candidate in (Fraction(p, q), Fraction(-p, q)):
                if poly_eval(ints, candidate) == 0 \
                        and candidate not in roots:
                    roots.append(candidate)

    return roots


def eigenvalues(matrix):
    """小方阵的全部有理特征值（去重）。非有理特征值会缺失，供校验用。"""
    n, _ = dims(matrix)
    if n not in (2, 3):
        raise ValueError("只支持 2、3 阶")

    return rational_roots(char_coeffs(matrix))
