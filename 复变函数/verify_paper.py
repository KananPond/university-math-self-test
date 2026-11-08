# -*- coding: utf-8 -*-
"""
文件名：verify_paper.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 题库与抽题逻辑的自动化校验，交付前必须全部通过。
2. 检查项：
   a. 题库结构自查（题量、id 唯一、字段完整、图形规格合法、标记可解析、
      知识点标签合法、答案可被精确解析）；
   b. 答案机械复核（用 bank/complex_ref.py 的精确运算重算模、辐角、
      四则运算、幂、共轭、倒数、方程根、单位根等）；
   c. 抽题逻辑（每卷题量与分值、同种子可复现、不同种子不同卷）。
3. 用法： cd 考试服务 && python verify_paper.py
"""

import sys

from bank import BANK, DRAW_PLAN, PAPER_META, draw_paper, bank_summary
from bank import complex_ref as cr

failures = []
checks = 0

# 知识点受控词表（与 bank/FORMAT.md 一致）
VALID_KPS = {
    "复数的表示", "模与辐角", "四则运算", "共轭与倒数", "幂与根",
    "棣莫弗公式", "复指数函数", "复对数函数", "复幂函数",
    "复三角与双曲函数", "复变函数概念",
}

# 各 verify 种类对应的答案类型与所需参数
VERIFY_KINDS = {
    "op": ("complex", ("op", "left", "right")),
    "modulus": ("number", ("z",)),
    "arg": ("angle", ("z",)),
    "pow": ("complex", ("z", "n")),
    "conj": ("complex", ("z",)),
    "inv": ("complex", ("z",)),
    "root_of": ("complex", ("z", "n")),
    "roots_of_unity": ("complex", ("n",)),
    "abs_sq": ("number", ("z",)),
}


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

def figure_spec_ok(spec):
    """检查一个图形规格是否合法，返回错误信息或 None。"""
    if not isinstance(spec, dict):
        return "图形规格必须是字典"
    kind = spec.get("kind") or "point"
    if kind not in ("point", "roots", "ops", "plane"):
        return "未知图形种类 %s" % kind

    if kind == "point":
        if cr.parse_complex(spec.get("z")) is None:
            return "point 图形的 z 无法解析：%r" % spec.get("z")
        show = spec.get("show") or []
        for item in show:
            if item not in ("radius", "angle", "conj", "proj"):
                return "未知的 show 选项 %s" % item
    elif kind == "roots":
        if not isinstance(spec.get("n"), int) or spec["n"] < 1:
            return "roots 图形的 n 必须是正整数"
    elif kind == "ops":
        for key in ("z1", "z2"):
            if cr.parse_complex(spec.get(key)) is None:
                return "ops 图形的 %s 无法解析：%r" % (key, spec.get(key))
    elif kind == "plane":
        for item in spec.get("points") or []:
            if cr.parse_complex(item.get("z")) is None:
                return "plane 图形的点无法解析：%r" % item.get("z")
        for item in spec.get("circles") or []:
            if not isinstance(item.get("radius"), (int, float)):
                return "plane 图形的圆半径必须是数字"

    return None


def find_markers(text):
    """提取文本中的全部 [[key]] 标记。"""
    found = []
    index = 0
    while True:
        start = text.find("[[", index)
        if start < 0:
            break
        end = text.find("]]", start)
        if end < 0:
            break
        found.append(text[start + 2:end].strip())
        index = end + 2

    return found


def expected_answer_value(question, spec):
    """取出被机械校验的那个标准答案（字符串或字符串列表）。

    选择题取正确选项的文本；计算题按 blank 序号取小问答案。
    """
    if "blank" in spec:
        blanks = question.get("blanks") or []
        index = int(spec["blank"])
        if index >= len(blanks):
            return None
        answer = blanks[index].get("answer")
    elif "options" in question and isinstance(question.get("answer"), int):
        answer = question["options"][question["answer"]]
    else:
        answer = question.get("answer")

    if isinstance(answer, list):
        return answer

    return [answer]


def parse_expected(raw, answer_type):
    """把标准答案解析成可比较的值列表。"""
    if raw is None:
        return []
    items = raw if isinstance(raw, list) else [raw]
    values = []
    for item in items:
        if not isinstance(item, str):
            return []
        if answer_type == "complex":
            value = cr.parse_complex(item)
        elif answer_type == "angle":
            value = cr.parse_angle(item)
        else:
            value = cr.parse_real(item)
        if value is None:
            return []
        values.append(value)

    return values


def apply_op(left, right, name):
    """按名称执行一次复数运算。"""
    if name == "add":
        return cr.c_add(left, right)
    if name == "sub":
        return cr.c_sub(left, right)
    if name == "mul":
        return cr.c_mul(left, right)
    if name == "div":
        return cr.c_div(left, right)

    raise ValueError("未知运算 %s" % name)


def verify_one(question):
    """机械复核一道题，返回错误信息或 None。"""
    spec = question.get("verify")
    if not spec:
        return None

    kind = spec.get("kind")
    if kind not in VERIFY_KINDS:
        return "未知的校验类型 %s" % kind

    answer_type, required = VERIFY_KINDS[kind]
    for key in required:
        if key not in spec:
            return "校验缺少参数 %s" % key

    expected = parse_expected(expected_answer_value(question, spec),
                              answer_type)
    if not expected:
        return "标准答案无法按 %s 解析" % answer_type

    if kind == "op":
        left = cr.parse_complex(spec["left"])
        right = cr.parse_complex(spec["right"])
        if left is None or right is None:
            return "运算的复数无法解析"
        try:
            actual = apply_op(left, right, spec["op"])
        except cr.ComplexValueError as error:
            return str(error)
        if not any(cr.complex_equal(actual, value) for value in expected):
            return "运算结果应为 %s" % cr.format_complex(actual)

        return None

    if kind in ("modulus", "abs_sq", "arg"):
        value = cr.parse_complex(spec["z"])
        if value is None:
            return "校验复数无法解析"
        if kind == "modulus":
            actual = cr.c_abs(value)
            if actual is None:
                return "该模无法精确表示"
            if not any(actual == item for item in expected):
                return "模应为 %s" % cr.format_real(actual)
        elif kind == "abs_sq":
            actual = cr.c_abs_sq(value)
            if not any(actual == item for item in expected):
                return "模的平方应为 %s" % cr.format_real(actual)
        else:
            actual = cr.arg_coefficient(value)
            if actual is None:
                return "该辐角无法精确表示"
            if not any(actual == item for item in expected):
                return "主值辐角应为 %s" % cr.format_angle(actual)

        return None

    if kind in ("pow", "conj", "inv"):
        value = cr.parse_complex(spec["z"])
        if value is None:
            return "校验复数无法解析"
        if kind == "pow":
            try:
                actual = cr.c_pow_int(value, int(spec["n"]))
            except cr.ComplexValueError as error:
                return str(error)
        elif kind == "conj":
            actual = cr.c_conj(value)
        else:
            try:
                actual = cr.c_div((cr.ONE, cr.ZERO), value)
            except cr.ComplexValueError as error:
                return str(error)
        if not any(cr.complex_equal(actual, item) for item in expected):
            return "结果应为 %s" % cr.format_complex(actual)

        return None

    if kind == "root_of":
        target = cr.parse_complex(spec["z"])
        if target is None:
            return "校验复数无法解析"
        count = int(spec["n"])
        for item in expected:
            power = cr.c_pow_int(item, count)
            if not cr.complex_equal(power, target):
                return "%s 不是 %s 的 %d 次根" % (
                    cr.format_complex(item), spec["z"], count)

        return None

    if kind == "roots_of_unity":
        count = int(spec["n"])
        roots = cr.roots_of_unity(count)
        if roots is None:
            return "%d 次单位根无法精确表示" % count
        for item in expected:
            hit = False
            for root in roots:
                if cr.complex_equal(root, item):
                    hit = True
                    break
            if not hit:
                return "%s 不是 %d 次单位根" % (cr.format_complex(item), count)

        return None

    return "未覆盖的校验类型 %s" % kind


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
            # 计算题的标准答案放在 blanks 里，其余题型用 answer 字段
            required = ("id", "score", "stem", "explain", "kp")
            if question.get("blanks") is not None:
                required = required + ("blanks",)
            else:
                required = required + ("answer",)
            for field in required:
                if field not in question or question[field] in (None, ""):
                    check("%s 缺少字段 %s" % (prefix, field), False)

            check("%s 知识点标签合法" % prefix,
                  question.get("kp") in VALID_KPS,
                  "kp=%r" % question.get("kp"))

            figures = question.get("figures") or {}
            for key, spec in figures.items():
                error = figure_spec_ok(spec)
                if error:
                    check("%s 图形 %s 非法" % (prefix, key), False, error)

            body = question["stem"] + "".join(question.get("options", []))
            used = set(find_markers(body))
            missing = used - set(figures)
            if missing:
                check("%s 标记缺少图形定义" % prefix, False,
                      "缺少：%s" % ", ".join(sorted(missing)))
            unused = set(figures) - used
            if unused:
                check("%s 存在未被引用的图形" % prefix, False,
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
        answer_type = question.get("answer_type") or "number"
        check("%s 答案类型合法" % question["id"],
              answer_type in ("number", "complex", "angle"),
              "answer_type=%r" % answer_type)
        answer = question["answer"]
        items = answer if isinstance(answer, list) else [answer]
        ok = True
        for item in items:
            if not isinstance(item, str):
                ok = False
                break
            if answer_type == "complex":
                ok = cr.parse_complex(item) is not None
            elif answer_type == "angle":
                ok = cr.parse_angle(item) is not None
            else:
                ok = cr.parse_real(item) is not None
            if not ok:
                break
        check("%s 数值答案可解析" % question["id"], ok,
              "answer=%r" % (answer,))

    for question in BANK["calc"]:
        blanks = question.get("blanks") or []
        check("%s 至少有一个小问" % question["id"], len(blanks) > 0)
        ok = True
        for blank in blanks:
            answer = blank.get("answer")
            items = answer if isinstance(answer, list) else [answer]
            answer_type = blank.get("answer_type") or "number"
            for item in items:
                if not isinstance(item, str):
                    ok = False
                    break
                if answer_type == "complex":
                    parsed = cr.parse_complex(item)
                elif answer_type == "angle":
                    parsed = cr.parse_angle(item)
                else:
                    parsed = cr.parse_real(item)
                if parsed is None:
                    ok = False
                    break
            if not ok:
                break
        check("%s 小问答案全部可解析" % question["id"], ok)


def check_answers():
    """用精确运算机械复核所有带 verify 的答案。"""
    print("【检查 2】答案机械复核（精确运算）")
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
    seeds = [1, 42, 20261108, 999999999]
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

    ok = True
    for seed in range(1000, 1020):
        paper = draw_paper(seed, BANK)
        total = sum(question["score"] for section in paper["sections"]
                    for question in section["questions"])
        if total != PAPER_META["total_score"]:
            ok = False
    check("随机 20 个种子得分均为 100 分", ok)


def check_drill():
    """闪电训练题源自查：答案可解析且与题面一致。"""
    print("【检查 4】闪电训练题源")
    from bank import drill_gen

    generated = 0
    for seed in (1, 7, 20261108, 99999):
        for item in drill_gen.generate_items(seed, 40):
            generated += 1
            if item.get("kind") == "blanks":
                ok = True
                for blank in item.get("blanks") or []:
                    answer_type = blank.get("answer_type") or "number"
                    if answer_type == "complex":
                        ok = cr.parse_complex(blank.get("answer")) is not None
                    elif answer_type == "angle":
                        ok = cr.parse_angle(blank.get("answer")) is not None
                    else:
                        ok = cr.parse_real(blank.get("answer")) is not None
                    if not ok:
                        break
                check("种子 %s 训练题 %s 答案可解析" % (seed, item["id"]), ok)
            else:
                answer_type = item.get("answer_type") or "number"
                answer = item.get("answer")
                if answer_type == "complex":
                    ok = cr.parse_complex(answer) is not None
                elif answer_type == "angle":
                    ok = cr.parse_angle(answer) is not None
                else:
                    ok = cr.parse_real(answer) is not None
                check("种子 %s 训练题 %s 答案可解析" % (seed, item["id"]), ok)

    check("训练题生成数量充足", generated >= 120)


def main():
    print("题库规模：%s" % bank_summary(BANK))
    check_structure()
    check_answers()
    check_draw()
    check_drill()

    print("")
    if failures:
        print("校验未通过，共 %d 项失败（执行 %d 项检查）："
              % (len(failures), checks))
        for item in failures:
            print("  - %s" % item)

        return 1

    print("校验全部通过（执行 %d 项检查）。" % checks)

    return 0


if __name__ == "__main__":
    sys.exit(main())
