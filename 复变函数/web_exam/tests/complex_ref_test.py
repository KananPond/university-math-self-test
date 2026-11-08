# -*- coding: utf-8 -*-
"""
文件名：complex_ref_test.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 精确复数运算内核（bank/complex_ref.py）的自测脚本。
2. 覆盖解析、四则运算、模与辐角、角度解析、单位根与非法输入。
3. 用法： cd 考试服务 && python web_exam/tests/complex_ref_test.py
"""

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_EXAM_DIR = os.path.dirname(TESTS_DIR)
PROJECT_DIR = os.path.dirname(WEB_EXAM_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from bank import complex_ref as cr  # noqa: E402

fails = []


def eq(name, got, want):
    """比对一条断言。"""
    if got != want:
        fails.append("%s: got %r want %r" % (name, got, want))
        print("  [失败] %s -> %r（应为 %r）" % (name, got, want))
    else:
        print("  [通过] %s = %r" % (name, got))


def z(text):
    """解析复数文本。"""
    return cr.parse_complex(text)


def main():
    print("== 解析 ==")
    eq("3+4i", cr.format_complex(z("3+4i")), "3 + 4i")
    eq("1-i", cr.format_complex(z("1-i")), "1 - i")
    eq("4i", cr.format_complex(z("4i")), "4i")
    eq("-i", cr.format_complex(z("-i")), "-i")
    eq("i", cr.format_complex(z("i")), "i")
    eq("3", cr.format_complex(z("3")), "3")
    eq("1/2+3/4i", cr.format_complex(z("1/2+3/4i")), "1/2 + 3/4i")
    eq("√3/2+i/2", cr.format_complex(z("√3/2+i/2")), "√3/2 + 1/2i")
    eq("√3i/2", cr.format_complex(z("√3i/2")), "√3/2i")
    eq("√3/2i", cr.format_complex(z("√3/2i")), "√3/2i")
    eq("iπ", cr.format_complex(z("iπ")), "πi")
    eq("-iπ/2", cr.format_complex(z("-iπ/2")), "-π/2i")
    eq("2πi", cr.format_complex(z("2πi")), "2πi")
    eq("π/4", cr.format_complex(z("π/4")), "π/4")
    eq("0", cr.format_complex(z("0")), "0")

    print("== 运算 ==")
    eq("(1+i)(2-i)", cr.format_complex(cr.c_mul(z("1+i"), z("2-i"))), "3 + i")
    eq("1/(1+i)", cr.format_complex(cr.c_div(z("1"), z("1+i"))), "1/2 - 1/2i")
    eq("(1+i)/(1-i)", cr.format_complex(cr.c_div(z("1+i"), z("1-i"))), "i")
    eq("i^2025", cr.format_complex(cr.c_pow_int(z("i"), 2025)), "i")
    eq("(1+i)^8", cr.format_complex(cr.c_pow_int(z("1+i"), 8)), "16")
    eq("(1+i)^4", cr.format_complex(cr.c_pow_int(z("1+i"), 4)), "-4")
    eq("(√3/2+i/2)^3", cr.format_complex(cr.c_pow_int(z("√3/2+i/2"), 3)), "i")
    eq("(1+i)^2", cr.format_complex(cr.c_pow_int(z("1+i"), 2)), "2i")
    eq("3e^{iπ/6}", cr.format_complex(cr.c_mul(z("3"), z("√3/2+i/2"))),
       "3√3/2 + 3/2i")
    eq("conj", cr.format_complex(cr.c_conj(z("3+4i"))), "3 - 4i")
    eq("conj 两次", cr.format_complex(cr.c_conj(cr.c_conj(z("3+4i")))),
       "3 + 4i")
    eq("(-3-3i)/(-2-2i)", cr.format_complex(cr.c_div(z("-3-3i"), z("-2-2i"))),
       "3/2")

    print("== 模与辐角 ==")
    eq("|3+4i|", cr.format_real(cr.c_abs(z("3+4i"))), "5")
    eq("|1+i|", cr.format_real(cr.c_abs(z("1+i"))), "√2")
    eq("|3+2i|", cr.format_real(cr.c_abs(z("3+2i"))), "√13")
    eq("|√3/2+i/2|", cr.format_real(cr.c_abs(z("√3/2+i/2"))), "1")
    eq("|2i|", cr.format_real(cr.c_abs(z("2i"))), "2")
    eq("|0|", cr.format_real(cr.c_abs(z("0"))), "0")

    eq("Arg(1+i)", cr.format_angle(cr.arg_coefficient(z("1+i"))), "π/4")
    eq("Arg(-1)", cr.format_angle(cr.arg_coefficient(z("-1"))), "π")
    eq("Arg(-i)", cr.format_angle(cr.arg_coefficient(z("-i"))), "-π/2")
    eq("Arg(-1-i)", cr.format_angle(cr.arg_coefficient(z("-1-i"))), "-3π/4")
    eq("Arg(√3/2+i/2)", cr.format_angle(cr.arg_coefficient(z("√3/2+i/2"))),
       "π/6")
    eq("Arg(2)", cr.format_angle(cr.arg_coefficient(z("2"))), "0")
    eq("Arg(1+2i) 不可精确", cr.arg_coefficient(z("1+2i")), None)

    print("== 角度解析 ==")
    eq("parse π/4", cr.parse_angle("π/4"), cr.Fraction(1, 4))
    eq("parse -π/2", cr.parse_angle("-π/2"), cr.Fraction(-1, 2))
    eq("parse 3π/4", cr.parse_angle("3π/4"), cr.Fraction(3, 4))
    eq("parse π", cr.parse_angle("π"), cr.Fraction(1))
    eq("parse 0", cr.parse_angle("0"), cr.Fraction(0))
    eq("parse 5π/4", cr.parse_angle("5π/4"), cr.Fraction(5, 4))
    eq("parse 45°", cr.parse_angle("45°"), cr.Fraction(1, 4))
    eq("parse 1 非法", cr.parse_angle("1"), None)

    print("== 单位根 ==")
    roots = cr.roots_of_unity(3)
    eq("3 次单位根个数", len(roots), 3)
    eq("3 次单位根", " / ".join(cr.format_complex(r) for r in roots),
       "1 / -1/2 + √3/2i / -1/2 - √3/2i")
    roots4 = cr.roots_of_unity(4)
    eq("4 次单位根", " / ".join(cr.format_complex(r) for r in roots4),
       "1 / i / -1 / -i")
    eq("5 次单位根不可精确", cr.roots_of_unity(5), None)

    print("== 非法输入 ==")
    eq("空串", cr.parse_complex(""), None)
    eq("乱写", cr.parse_complex("abc"), None)
    eq("单个加号", cr.parse_complex("+"), None)

    print("")
    if fails:
        print("失败 %d 项：" % len(fails))
        for item in fails:
            print("  -", item)

        return 1

    print("全部通过")

    return 0


if __name__ == "__main__":
    sys.exit(main())
