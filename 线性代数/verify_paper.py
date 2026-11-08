# -*- coding: utf-8 -*-
"""
文件名：verify_paper.py
作者：ZCode（GLM）
日期：2026-10-02
版本：1.0
文件说明：
1. 题库与抽题逻辑的自动化校验，交付前必须全部通过。
2. 检查项：
   a. 题库结构自查（题量、id 唯一、字段完整、矩阵规格合法、标记可解析）；
   b. 答案机械复核（用 bank/linalg_ref.py 的精确分数运算重算行列式、
      秩、逆、乘积、方程组解、特征值、特征向量、基础解系等）；
   c. 抽题逻辑（每卷 32 题 100 分、同种子可复现、不同种子不同卷）。
3. 用法： cd 考试服务 && python verify_paper.py
"""

import sys
from fractions import Fraction

from bank import BANK, DRAW_PLAN, PAPER_META, draw_paper, bank_summary
from bank import linalg_ref as la
from matrix_text import MARKER_START, MARKER_END, format_matrix_ascii

failures = []
checks = 0


def check(name, condition, detail=""):
    """记录一条检查结果。"""
    global checks
    checks += 1
    if condition:
        print("  [通过] %s" % name)
    else:
        message = "  [失败] %s" % name
        if detail:
            message += " —— %s" % detail
        print(message)
        failures.append("%s %s" % (name, detail))


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------

def matrix_spec_ok(spec):
    """检查一个矩阵规格是否合法，返回错误信息或 None。"""
    if not isinstance(spec, dict):
        return "矩阵规格必须是字典"
    data = spec.get("data")
    if not isinstance(data, list) or not data or not data[0]:
        return "矩阵 data 不能为空"
    width = len(data[0])
    if any(not isinstance(row, list) or len(row) != width for row in data):
        return "矩阵各行长度不一致"
    style = spec.get("style", "matrix")
    if style not in ("matrix", "det", "aug"):
        return "未知样式 %s" % style
    if style == "aug" and width < 2:
        return "增广矩阵至少要 2 列"
    for row in data:
        for cell in row:
            if la.to_frac(cell) is None and not str(cell).isalpha():
                return "非法元素 %r" % (cell,)

    return None


def find_markers(text):
    """提取文本中的全部 [[key]] 标记。"""
    found = []
    index = 0
    while True:
        start = text.find(MARKER_START, index)
        if start < 0:
            break
        end = text.find(MARKER_END, start)
        if end < 0:
            break
        found.append(text[start + len(MARKER_START):end].strip())
        index = end + len(MARKER_END)

    return found


def resolve_matrix(question, key):
    """取题目里的矩阵规格；key 缺失返回 None。"""
    return (question.get("matrices") or {}).get(key)


def spec_matrix(question, spec_key="matrix"):
    """按 verify 规格里记录的键名取题目矩阵，转成分数矩阵。"""
    key = (question.get("verify") or {}).get(spec_key)
    spec = resolve_matrix(question, key)
    if spec is None:
        return None

    return la.parse_matrix(spec.get("data"))


def answer_value(question):
    """把题目的标准答案转成分数或分数矩阵。"""
    raw = question["answer"]
    if question.get("answer_type") == "matrix":
        return la.parse_matrix(raw.get("data"))

    return la.to_frac(raw)


# --------------------------------------------------------------------------
# verify 各类复核
# --------------------------------------------------------------------------

def verify_one(question):
    """机械复核一道题，返回错误信息或 None。"""
    spec = question.get("verify")
    if not spec:
        return None

    kind = spec.get("kind")
    answer = answer_value(question)
    if "options" in question and isinstance(question.get("answer"), int):
        # 数值型校验时，选择题的答案取对应选项文本；矩阵选项题保持原样
        option_value = la.to_frac(question["options"][question["answer"]])
        if option_value is not None:
            answer = option_value
    if answer is None:
        return "标准答案无法解析"

    if kind == "det":
        matrix = spec_matrix(question) \
            if "matrix" in spec else la.parse_matrix(spec["matrix_literal"])
        if matrix is None:
            return "校验矩阵无法解析"
        return None if la.det(matrix) == answer \
            else "行列式应为 %s，答案为 %s" % (la.det(matrix), answer)

    if kind == "rank":
        matrix = spec_matrix(question) \
            if "matrix" in spec else la.parse_matrix(spec["matrix_literal"])
        if matrix is None:
            return "校验矩阵无法解析"
        return None if la.rank(matrix) == answer \
            else "秩应为 %s，答案为 %s" % (la.rank(matrix), answer)

    if kind == "det_scale":
        matrix = spec_matrix(question)
        if matrix is None:
            return "校验矩阵无法解析"
        k = la.to_frac(spec["k"])
        n = la.dims(matrix)[0]
        expected = (k ** n) * la.det(matrix)
        return None if expected == answer \
            else "|%sA| 应为 %s，答案为 %s" % (k, expected, answer)

    if kind == "adj":
        matrix = spec_matrix(question)
        if matrix is None:
            return "校验矩阵无法解析"
        option = resolve_matrix(question, spec.get("option"))
        if option is None:
            return "找不到选项矩阵 %s" % spec.get("option")
        expected = la.adjugate(matrix)
        actual = la.parse_matrix(option["data"])
        return None if actual == expected \
            else "伴随矩阵应为 %s" % format_matrix_ascii(
                {"data": [[str(v) for v in row] for row in expected]})

    if kind == "power":
        matrix = spec_matrix(question)
        if matrix is None:
            return "校验矩阵无法解析"
        n = int(spec["n"])
        result = matrix
        for _ in range(n - 1):
            result = la.mat_mul(result, matrix)
        option_key = spec.get("option")
        if option_key:
            option = resolve_matrix(question, option_key)
            if option is None:
                return "找不到选项矩阵 %s" % option_key
            actual = la.parse_matrix(option["data"])
            return None if actual == result \
                else "A^%d 应为 %s" % (n, result)
        return None if result == answer else "A^%d 不等于答案" % n

    if kind in ("mul", "outer", "inner"):
        left = resolve_matrix(question, spec["left"])
        right = resolve_matrix(question, spec["right"])
        if left is None or right is None:
            return "找不到运算矩阵"
        left_m = la.parse_matrix(left["data"])
        right_m = la.parse_matrix(right["data"])
        if kind == "outer":
            right_m = la.mat_transpose(right_m)
        if kind == "inner":
            left_m = la.mat_transpose(left_m)
        if left_m is None or right_m is None:
            return "运算矩阵无法解析"
        expected = la.mat_mul(left_m, right_m)
        return None if expected == answer \
            else "乘积应为 %s" % format_matrix_ascii(
                {"data": [[str(v) for v in row] for row in expected]})

    if kind == "inv":
        matrix = spec_matrix(question)
        if matrix is None:
            return "校验矩阵无法解析"
        try:
            expected = la.inverse(matrix)
        except ValueError:
            return "校验矩阵不可逆"
        return None if expected == answer \
            else "逆矩阵应为 %s" % format_matrix_ascii(
                {"data": [[str(v) for v in row] for row in expected]})

    if kind == "solve":
        matrix = spec_matrix(question)
        if matrix is None:
            return "校验矩阵无法解析"
        solution = la.solve_square(matrix)
        if solution is None:
            return "方程组没有唯一解，无法机械校验"
        expected = [[v] for v in solution]
        return None if expected == answer \
            else "解向量应为 %s" % expected

    if kind == "solve_component":
        aug = la.parse_matrix(spec["aug_literal"])
        if aug is None:
            return "校验矩阵无法解析"
        solution = la.solve_square(aug)
        if solution is None:
            return "方程组没有唯一解"
        component = int(spec["component"])
        return None if solution[component] == answer \
            else "第 %d 个分量应为 %s" % (component, solution[component])

    if kind == "eigvec":
        matrix = spec_matrix(question)
        if matrix is None:
            return "校验矩阵无法解析"
        eigen = la.to_frac(spec["eigen"])
        product = la.mat_vec(matrix, [row[0] for row in answer])
        expected = [[eigen * row[0]] for row in answer]
        if all(v == 0 for row in answer for v in row):
            return "特征向量不能是零向量"
        return None if product == expected \
            else "Av ≠ λv（λ=%s）" % eigen

    if kind == "eigs_option":
        matrix = spec_matrix(question)
        if matrix is None:
            return "校验矩阵无法解析"
        option = resolve_matrix(question, spec.get("option"))
        if option is None:
            return "找不到选项矩阵 %s" % spec.get("option")
        diagonal = la.parse_matrix(option["data"])
        if la.dims(diagonal) != la.dims(matrix):
            return "选项矩阵与 A 不同阶"
        diag_values = [diagonal[i][i] for i in range(la.dims(diagonal)[0])]
        try:
            eigenvalues = la.eigenvalues(matrix)
        except ValueError as error:
            return str(error)
        diagonal_ok = len(eigenvalues) == len(diag_values) \
            and sorted(eigenvalues) == sorted(diag_values)
        return None if diagonal_ok \
            else "对角元 %s 与特征值 %s 不符" % (diag_values, eigenvalues)

    if kind == "eigs_semidefinite":
        matrix = spec_matrix(question)
        if matrix is None:
            return "校验矩阵无法解析"
        try:
            eigenvalues = la.eigenvalues(matrix)
        except ValueError as error:
            return str(error)
        if len(eigenvalues) < la.dims(matrix)[0]:
            return "特征值含无理根，无法机械校验半正定性"
        if any(v < 0 for v in eigenvalues):
            return "存在负特征值 %s，不是半正定" % eigenvalues
        if all(v > 0 for v in eigenvalues):
            return "特征值全正，应为正定而非半正定"

        return None

    if kind == "sub_det_zero":
        spec_raw = resolve_matrix(question, spec["matrix"])
        if spec_raw is None:
            return "找不到校验矩阵 %s" % spec["matrix"]
        var = spec.get("var", "a")
        value = answer
        substituted = []
        for row in spec_raw["data"]:
            converted_row = []
            for cell in row:
                if str(cell) == var:
                    converted_row.append(value)
                else:
                    cell_value = la.to_frac(cell)
                    if cell_value is None:
                        return "代入后矩阵无法解析"
                    converted_row.append(cell_value)
            substituted.append(converted_row)
        eigen = la.to_frac(spec["eigen"])
        shifted = [[substituted[i][j] - (eigen if i == j else 0)
                    for j in range(len(substituted[0]))]
                   for i in range(len(substituted))]
        return None if la.det(shifted) == 0 \
            else "代入 %s=%s 后 det(A − λE) ≠ 0" % (var, value)

    if kind == "free_count":
        matrix = spec["matrix_literal"] if "matrix_literal" in spec \
            else (resolve_matrix(question, spec["matrix"]) or {}).get("data")
        matrix = la.parse_matrix(matrix)
        if matrix is None:
            return "校验矩阵无法解析"
        n = la.dims(matrix)[1]
        expected = n - la.rank(matrix)
        return None if expected == answer \
            else "基础解系应含 %s 个向量，答案为 %s" % (expected, answer)

    if kind == "null_basis":
        matrix = spec_matrix(question)
        if matrix is None:
            return "校验矩阵无法解析"
        _, n = la.dims(matrix)
        expected_count = n - la.rank(matrix)
        if len(answer[0]) != expected_count:
            return "基础解系应含 %d 个向量，答案给了 %d 个" \
                % (expected_count, len(answer[0]))
        for column in range(len(answer[0])):
            vector = [answer[i][column] for i in range(len(answer))]
            if all(v == 0 for v in vector):
                return "第 %d 列是零向量" % (column + 1)
            product = la.mat_vec(matrix, vector)
            if any(v != 0 for row in product for v in row):
                return "第 %d 列不是 Ax = 0 的解" % (column + 1)

        return None

    if kind == "single_invertible":
        invertible = resolve_matrix(question, spec["invertible"])
        if invertible is None:
            return "找不到可逆矩阵 %s" % spec["invertible"]
        if la.det(la.parse_matrix(invertible["data"])) == 0:
            return "%s 应可逆但行列式为 0" % spec["invertible"]
        for key in spec.get("singular", []):
            singular = resolve_matrix(question, key)
            if singular is None:
                return "找不到矩阵 %s" % key
            if la.det(la.parse_matrix(singular["data"])) != 0:
                return "%s 应奇异但行列式不为 0" % key

        return None

    return "未知的校验类型 %s" % kind


# --------------------------------------------------------------------------
# 检查项
# --------------------------------------------------------------------------

def check_structure():
    """题库结构自查。"""
    print("【检查 1】题库结构")

    for plan in DRAW_PLAN:
        pool = BANK[plan["key"]]
        check("%s 入库 %d 题（抽题需要 %d 题）" % (plan["title"], len(pool),
                                                plan["draw"]),
              len(pool) >= plan["draw"])

    all_ids = []
    for plan in DRAW_PLAN:
        for question in BANK[plan["key"]]:
            all_ids.append(question["id"])

    check("题目 id 全库唯一", len(all_ids) == len(set(all_ids)),
          "重复 id：%s" % sorted(set(all_ids)))

    for plan in DRAW_PLAN:
        for question in BANK[plan["key"]]:
            prefix = "%s（%s）" % (question["id"], question.get("stem", "")[:16])
            for field in ("id", "score", "stem", "answer", "explain"):
                if field not in question or question[field] in (None, ""):
                    check("%s 缺少字段 %s" % (prefix, field), False)
            matrices = question.get("matrices") or {}
            for key, spec in matrices.items():
                error = matrix_spec_ok(spec)
                if error:
                    check("%s 矩阵 %s 非法" % (prefix, key), False, error)

            body = question["stem"] + "".join(question.get("options", []))
            used = set(find_markers(body))
            missing = used - set(matrices)
            if missing:
                check("%s 标记缺少矩阵定义" % prefix, False,
                      "缺少：%s" % ", ".join(sorted(missing)))
            unused = set(matrices) - used
            if unused:
                check("%s 存在未被引用的矩阵" % prefix, False,
                      "未引用：%s" % ", ".join(sorted(unused)))

    for question in BANK["choice"]:
        options = question["options"]
        check("%s 选项恰好 4 个" % question["id"], len(options) == 4)
        check("%s 答案下标合法" % question["id"],
              isinstance(question["answer"], int) and 0 <= question["answer"] < 4)

    for question in BANK["judge"]:
        check("%s 答案是布尔值" % question["id"],
              isinstance(question["answer"], bool))

    for question in BANK["fill"]:
        check("%s 数值答案可解析" % question["id"],
              la.to_frac(question["answer"]) is not None,
              "answer=%r" % question["answer"])

    for question in BANK["calc"]:
        answer = question["answer"]
        shape_ok = answer.get("rows") == question["rows"] \
            and answer.get("cols") == question["cols"] \
            and len(answer["data"]) == question["rows"] \
            and all(len(row) == question["cols"] for row in answer["data"])
        check("%s 答案形状与声明一致（%d×%d）" % (question["id"],
                                                question["rows"], question["cols"]),
              shape_ok)
        matrix = la.parse_matrix(answer["data"])
        check("%s 答案元素全部可解析" % question["id"], matrix is not None)


def check_answers():
    """用精确运算机械复核所有带 verify 的答案。"""
    print("【检查 2】答案机械复核（分数精确运算）")
    verified = 0
    for plan in DRAW_PLAN:
        for question in BANK[plan["key"]]:
            if not question.get("verify"):
                continue
            verified += 1
            error = verify_one(question)
            check("%s 答案复核" % question["id"], error is None, error or "")

    if verified == 0:
        check("题库中存在可机械复核的题目", False)


def check_draw():
    """抽题逻辑自查。"""
    print("【检查 3】抽题逻辑")

    seeds = [1, 42, 20261002, 999999999]
    for seed in seeds:
        paper = draw_paper(seed, BANK)
        total = sum(question["score"] for section in paper["sections"]
                    for question in section["questions"])
        count = sum(len(section["questions"]) for section in paper["sections"])
        check("种子 %s：每卷 %d 题、%d 分" % (seed, count, total),
              total == PAPER_META["total_score"])

        for plan, section in zip(DRAW_PLAN, paper["sections"]):
            ids = [q["id"] for q in section["questions"]]
            check("种子 %s：%s 抽 %d 题" % (seed, plan["title"],
                                            plan["draw"]),
                  len(ids) == plan["draw"] and len(set(ids)) == len(ids))

    first = [q["id"] for q in draw_paper(seeds[0], BANK)["sections"]
             for q in q["questions"]]
    same = [q["id"] for q in draw_paper(seeds[0], BANK)["sections"]
            for q in q["questions"]]
    check("同一 seed 两次抽题完全一致", first == same)

    differing = False
    for seed_a in seeds:
        for seed_b in seeds:
            if seed_a >= seed_b:
                continue
            ids_a = [q["id"] for q in draw_paper(seed_a, BANK)["sections"]
                     for q in q["questions"]]
            ids_b = [q["id"] for q in draw_paper(seed_b, BANK)["sections"]
                     for q in q["questions"]]
            if ids_a != ids_b:
                differing = True
    check("不同种子抽出的试卷不同", differing)

    # 随机再抽 20 个种子确认分数恒为 100
    ok = True
    for seed in range(1000, 1020):
        paper = draw_paper(seed, BANK)
        total = sum(question["score"] for section in paper["sections"]
                    for question in section["questions"])
        if total != PAPER_META["total_score"]:
            ok = False
    check("随机 20 个种子得分均为 100 分", ok)


def main():
    print("题库规模：%s" % bank_summary(BANK))
    check_structure()
    check_answers()
    check_draw()

    print("")
    if failures:
        print("校验未通过，共 %d 项失败（执行 %d 项检查）："
              % (len(failures), checks))
        for item in failures:
            print(" - %s" % item)
        return 1

    print("全部校验通过（共 %d 项检查）。" % checks)

    return 0


if __name__ == "__main__":
    sys.exit(main())
