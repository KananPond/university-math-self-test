# -*- coding: utf-8 -*-
"""
文件名：complex_ref.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 基于 Fraction 的精确复数运算参考实现，供判分（web_exam/checker.py）、
   题库校验（verify_paper.py）与闪电训练题生成器（bank/drill_gen.py）共用。
2. 精确实数域 = 有理数 + 根式 + π：
       Real = Fraction(有理部分) + Σ c·√d + c·π
   根式的 d 取无平方因子的正整数；π 作为一个形式常数参与加、减，以及与
   有理数 / 根式的乘法（π² 与 π·√d 无法表示，抛 ComplexValueError）。
3. 复数用 (re, im) 二元组表示，re / im 均为上述精确实数。
   全部运算精确完成，不存在浮点误差；只覆盖教材常考的小规模情形。
"""

from fractions import Fraction


class ComplexValueError(ValueError):
    """精确运算无法表示时抛出。"""


# --------------------------------------------------------------------------
# 精确实数
# --------------------------------------------------------------------------

class Real(object):
    """精确实数：有理部分 + 根式部分 + π 部分。"""

    __slots__ = ("rat", "surds", "pi")

    def __init__(self, rat=0, surds=None, pi=0):
        self.rat = Fraction(rat)
        self.pi = Fraction(pi)
        self.surds = {}
        for key, value in (surds or {}).items():
            key = int(key)
            value = Fraction(value)
            if value == 0:
                continue
            if key == 1:
                # √1 = 1，折进有理部分
                self.rat += value
                continue
            self.surds[key] = value

    # -- 基本属性 ---------------------------------------------------------

    @property
    def is_rational(self):
        """是否是不含根式与 π 的有理数。"""
        return not self.surds and self.pi == 0

    @property
    def is_zero(self):
        """是否为零。"""
        return self.rat == 0 and self.pi == 0 and not self.surds

    def as_fraction(self):
        """转成 Fraction；含根式或 π 时抛 ComplexValueError。"""
        if not self.is_rational:
            raise ComplexValueError("该实数不是有理数：%s" % format_real(self))

        return self.rat

    def __eq__(self, other):
        if not isinstance(other, Real):
            return NotImplemented
        if self.rat != other.rat or self.pi != other.pi:
            return False
        if set(self.surds) != set(other.surds):
            return False
        for key, value in self.surds.items():
            if other.surds[key] != value:
                return False

        return True

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result

        return not result

    def __hash__(self):
        return hash((self.rat, self.pi,
                     tuple(sorted(self.surds.items()))))

    def __repr__(self):
        return "Real(%s)" % format_real(self)


ZERO = Real()
ONE = Real(1)


def real(rat=0, surds=None, pi=0):
    """构造精确实数。"""
    return Real(rat, surds, pi)


def radd(left, right):
    """实数加法。"""
    surds = dict(left.surds)
    for key, value in right.surds.items():
        surds[key] = surds.get(key, Fraction(0)) + value

    return Real(left.rat + right.rat, surds, left.pi + right.pi)


def rsub(left, right):
    """实数减法。"""
    return radd(left, rneg(right))


def rneg(value):
    """实数取负。"""
    surds = {key: -coef for key, coef in value.surds.items()}

    return Real(-value.rat, surds, -value.pi)


def rscale(value, factor):
    """实数乘以有理数。"""
    factor = Fraction(factor)
    surds = {key: coef * factor for key, coef in value.surds.items()}

    return Real(value.rat * factor, surds, value.pi * factor)


def rmul(left, right):
    """实数乘法：支持有理数、根式、π 的组合；π² 与 π·√d 不支持。"""
    if left.pi != 0 and right.pi != 0:
        raise ComplexValueError("π² 无法精确表示")
    if left.pi != 0 and right.surds:
        raise ComplexValueError("π 与根式的乘积无法精确表示")
    if right.pi != 0 and left.surds:
        raise ComplexValueError("π 与根式的乘积无法精确表示")

    rat = left.rat * right.rat
    surds = {key: coef * right.rat for key, coef in left.surds.items()}
    for key, coef in right.surds.items():
        surds[key] = surds.get(key, Fraction(0)) + coef * left.rat

    # 根式 × 根式：√d1 · √d2 = √(d1·d2)，再化为 c·√d
    for d1, c1 in left.surds.items():
        for d2, c2 in right.surds.items():
            root, radicand = squarefree_int(d1 * d2)
            if radicand == 1:
                rat += c1 * c2 * root
            else:
                surds[radicand] = surds.get(radicand, Fraction(0)) + c1 * c2 * root

    pi = left.pi * right.rat + right.pi * left.rat

    return Real(rat, surds, pi)


def rdiv(left, right):
    """实数除法；除数必须是有理数。"""
    if isinstance(right, Real):
        if not right.is_rational:
            raise ComplexValueError("除数必须是有理数")
        divisor = right.rat
    else:
        divisor = Fraction(right)
    if divisor == 0:
        raise ComplexValueError("除数为零")

    return rscale(left, Fraction(1) / divisor)


def squarefree_int(number):
    """把正整数拆成 root²·radicand（radicand 无平方因子，可能为 1）。"""
    if number <= 0:
        raise ComplexValueError("根式的被开方数必须为正整数")
    root = 1
    rest = number
    factor = 2
    while factor * factor <= rest:
        while rest % (factor * factor) == 0:
            rest //= factor * factor
            root *= factor
        factor += 1

    return root, rest


def sqrt_rational(value):
    """非负有理数的精确平方根，返回精确实数。"""
    value = Fraction(value)
    if value < 0:
        raise ComplexValueError("负数没有实平方根")
    if value == 0:
        return ZERO
    root, radicand = squarefree_int(value.numerator * value.denominator)
    coef = Fraction(root, value.denominator)
    if radicand == 1:
        return Real(coef)

    return Real(0, {radicand: coef}, 0)


def rsqrt(value):
    """精确实数的平方根；只支持非负有理数。"""
    if not value.is_rational:
        raise ComplexValueError("只能对有理数开平方")

    return sqrt_rational(value.rat)


def frac_text(value):
    """Fraction 转可读文本。"""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)

    return "%d/%d" % (value.numerator, value.denominator)


def format_real(value):
    """精确实数转可读文本，例如 3 + √3/2 + π。"""
    pieces = []

    def push(sign, body):
        if not pieces:
            pieces.append(("-" if sign < 0 else "") + body)
        else:
            pieces.append((" - " if sign < 0 else " + ") + body)

    if value.rat != 0:
        push(1 if value.rat > 0 else -1, frac_text(abs(value.rat)))

    for radicand in sorted(value.surds):
        coef = value.surds[radicand]
        if coef == 0:
            continue
        push(1 if coef > 0 else -1, _surd_body(abs(coef), radicand))

    if value.pi != 0:
        push(1 if value.pi > 0 else -1, _pi_body(abs(value.pi)))

    if not pieces:
        return "0"

    return "".join(pieces)


def _surd_body(coef, radicand):
    """根式项的文本体（不含正负号）。

    √3 → "√3"；2√3 → "2√3"；√3/2 → "√3/2"；3√3/2 → "3√3/2"。
    """
    coef = Fraction(coef)
    if coef == 1:
        return "√%d" % radicand
    if coef.denominator == 1:
        return "%d√%d" % (coef.numerator, radicand)
    if coef.numerator == 1:
        return "√%d/%d" % (radicand, coef.denominator)

    return "%d√%d/%d" % (coef.numerator, radicand, coef.denominator)


def _pi_body(coef):
    """π 系数转文本体（不含外层正负号）。

    π → "π"；π/2 → "π/2"；3π/4 → "3π/4"；-π/2 → "-π/2"。
    """
    coef = Fraction(coef)
    if coef == 0:
        return "0"
    if coef == 1:
        return "π"
    if coef == -1:
        return "-π"
    numerator = coef.numerator
    denominator = coef.denominator
    sign = "-" if numerator < 0 else ""
    magnitude = abs(numerator)
    if denominator == 1:
        return "%s%dπ" % (sign, magnitude)
    if magnitude == 1:
        return "%sπ/%d" % (sign, denominator)

    return "%s%dπ/%d" % (sign, magnitude, denominator)


# --------------------------------------------------------------------------
# 文本解析
# --------------------------------------------------------------------------

def _read_rational(text, index):
    """从 text[index] 起读一个有理数，返回 (Fraction, 新下标) 或 (None, index)。"""
    length = len(text)
    start = index
    while index < length and text[index].isdigit():
        index += 1
    int_text = text[start:index]

    if index < length and text[index] == ".":
        index += 1
        frac_start = index
        while index < length and text[index].isdigit():
            index += 1
        frac_text_part = text[frac_start:index]
        if not int_text and not frac_text_part:
            return None, start
        digits = (int_text or "0") + frac_text_part
        numerator = Fraction(int(digits or "0"), 10 ** len(frac_text_part))
    else:
        if not int_text:
            return None, start
        numerator = Fraction(int(int_text))

    if index < length and text[index] == "/":
        index += 1
        den_start = index
        while index < length and text[index].isdigit():
            index += 1
        if index == den_start:
            return None, start
        denominator = int(text[den_start:index])
        if denominator == 0:
            return None, start
        numerator = Fraction(numerator, denominator)

    return numerator, index


def _read_int(text, index):
    """从 text[index] 起读一个正整数，返回 (int, 新下标) 或 (None, index)。"""
    start = index
    length = len(text)
    while index < length and text[index].isdigit():
        index += 1
    if index == start:
        return None, start

    return int(text[start:index]), index


def _parse_term(text, index):
    """解析一个项：可选系数 + 可选根式 / π。

    返回 (实数值, 新下标, 是否消耗了字符)。
    """
    length = len(text)
    coef = Fraction(1)
    has_number = False

    if index < length and text[index] == "(":
        depth = 1
        cursor = index + 1
        while cursor < length:
            if text[cursor] == "(":
                depth += 1
            elif text[cursor] == ")":
                depth -= 1
                if depth == 0:
                    break
            cursor += 1
        if cursor >= length:
            return None, index, False
        inner, _ = _read_rational(text[index + 1:cursor], 0)
        if inner is None:
            return None, index, False
        coef = inner
        has_number = True
        index = cursor + 1
    else:
        value, cursor = _read_rational(text, index)
        if value is not None:
            coef = value
            has_number = True
            index = cursor

    # 根式 √N / sqrt(N)
    # 注意：裸写的 √ 只取整数被开方数，"√3/2" 按惯例是 (√3)/2 而不是 √(3/2)；
    # 需要分数被开方数时写成 √(1/2)。
    if index < length and text[index] == "√":
        radicand, cursor = _read_int(text, index + 1)
        if radicand is None or radicand < 0:
            return None, index, False
        return sqrt_rational(radicand), cursor, True

    if text.startswith("sqrt(", index):
        close = text.find(")", index)
        if close < 0:
            return None, index, False
        radicand, _ = _read_rational(text[index + 5:close], 0)
        if radicand is None or radicand < 0:
            return None, index, False
        return sqrt_rational(radicand), close + 1, True

    # π
    if index < length and text[index] == "π":
        return Real(0, {}, coef), index + 1, True

    if has_number:
        return Real(coef, {}, 0), index, True

    return Real(1), index, False


def _strip(text):
    """清理待解析文本：去空白、统一减号与乘号。"""
    return "".join(text.split()).replace("−", "-").replace("·", "*")


def parse_real(text):
    """解析精确实数文本，失败返回 None。

    支持：3、-3/2、0.75、√13、2√3、(3/2)√3、√(1/2)、π、2π、π/4、3 + √3/2。
    """
    if not isinstance(text, str):
        return None
    cleaned = _strip(text)
    if not cleaned:
        return None

    total = ZERO
    index = 0
    sign = 1
    length = len(cleaned)
    while index < length:
        if cleaned[index] == "+":
            sign = 1
            index += 1
        elif cleaned[index] == "-":
            sign = -1
            index += 1
        term, cursor, consumed = _parse_term(cleaned, index)
        if term is None or not consumed:
            return None
        if cursor < length and cleaned[cursor] == "/":
            divisor, cursor = _read_rational(cleaned, cursor + 1)
            if divisor is None or divisor == 0:
                return None
            term = rdiv(term, divisor)
        total = radd(total, rscale(term, sign))
        index = cursor

    return total


def _balanced(text):
    """判断括号是否配对。"""
    depth = 0
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return False

    return depth == 0


def parse_complex(text):
    """解析复数文本，返回 (实部, 虚部) 或 None。

    支持：3+4i、1-i、4i、-i、i、3、1/2+3/4i、√3/2+i/2、iπ、-iπ/2、2πi。
    """
    if not isinstance(text, str):
        return None
    cleaned = _strip(text).replace("j", "i")
    if not cleaned:
        return None

    while (len(cleaned) > 1 and cleaned[0] == "(" and cleaned[-1] == ")"
           and _balanced(cleaned[1:-1])):
        cleaned = cleaned[1:-1]

    real_part = ZERO
    imag_part = ZERO
    index = 0
    sign = 1
    length = len(cleaned)
    while index < length:
        if cleaned[index] == "+":
            sign = 1
            index += 1
        elif cleaned[index] == "-":
            sign = -1
            index += 1
        term, cursor, consumed = _parse_term(cleaned, index)
        if term is None:
            return None

        # 除法后缀（如 √3/2）：先算商，再判断是不是虚部
        if cursor < length and cleaned[cursor] == "/":
            divisor, cursor = _read_rational(cleaned, cursor + 1)
            if divisor is None or divisor == 0:
                return None
            term = rdiv(term, divisor)

        is_imaginary = cursor < length and cleaned[cursor] == "i"
        if is_imaginary:
            cursor += 1
            if cursor < length and cleaned[cursor] == "π":
                term = rmul(term, Real(0, {}, 1))
                cursor += 1
            # 虚部后缀除法（如 iπ/2）
            if cursor < length and cleaned[cursor] == "/":
                divisor, cursor = _read_rational(cleaned, cursor + 1)
                if divisor is None or divisor == 0:
                    return None
                term = rdiv(term, divisor)

        if is_imaginary:
            imag_part = radd(imag_part, rscale(term, sign))
        else:
            if not consumed:
                return None
            real_part = radd(real_part, rscale(term, sign))
        index = cursor

    return real_part, imag_part


def format_complex(value):
    """复数转可读文本，例如 3+4i、-i、2、1/2-√3/2 i。"""
    real_part, imag_part = value
    if imag_part.is_zero:
        return format_real(real_part)

    if imag_part == ONE:
        body = "i"
        sign = "+"
    elif imag_part == Real(-1):
        body = "i"
        sign = "-"
    else:
        imag_text = format_real(imag_part)
        if imag_text.startswith("-"):
            imag_text = imag_text[1:].strip()
            sign = "-"
        else:
            sign = "+"
        body = imag_text + "i"

    if real_part.is_zero:
        return "%s%s" % ("-" if sign == "-" else "", body)

    return "%s %s %s" % (format_real(real_part), sign, body)


def complex_equal(left, right):
    """两个复数是否精确相等。"""
    if left is None or right is None:
        return False

    return left[0] == right[0] and left[1] == right[1]


# --------------------------------------------------------------------------
# 复数运算
# --------------------------------------------------------------------------

def c_add(left, right):
    """复数加法。"""
    return (radd(left[0], right[0]), radd(left[1], right[1]))


def c_sub(left, right):
    """复数减法。"""
    return (rsub(left[0], right[0]), rsub(left[1], right[1]))


def c_mul(left, right):
    """复数乘法：(a+bi)(c+di) = (ac−bd) + (ad+bc)i。"""
    ac = rmul(left[0], right[0])
    bd = rmul(left[1], right[1])
    ad = rmul(left[0], right[1])
    bc = rmul(left[1], right[0])

    return (rsub(ac, bd), radd(ad, bc))


def c_div(left, right):
    """复数除法：a/b = a·conj(b)/|b|²。"""
    denominator = radd(rmul(right[0], right[0]), rmul(right[1], right[1]))
    if denominator.is_zero:
        raise ComplexValueError("除数为零")
    conjugate = (right[0], rneg(right[1]))
    numerator = c_mul(left, conjugate)

    return (rdiv(numerator[0], denominator), rdiv(numerator[1], denominator))


def c_neg(value):
    """复数取负。"""
    return (rneg(value[0]), rneg(value[1]))


def c_conj(value):
    """复数共轭。"""
    return (value[0], rneg(value[1]))


def c_scale(value, factor):
    """复数乘以实数。"""
    return (rscale(value[0], factor), rscale(value[1], factor))


def c_abs_sq(value):
    """模的平方 |z|²（精确实数）。"""
    return radd(rmul(value[0], value[0]), rmul(value[1], value[1]))


def c_abs(value):
    """复数的模；无法精确表示时返回 None。"""
    square = c_abs_sq(value)
    if square.is_rational:
        return rsqrt(square)
    if square.is_zero:
        return ZERO

    return None


def c_pow_int(value, exponent):
    """复数的整数次幂（快速幂，支持负指数）。"""
    if exponent < 0:
        return c_pow_int(c_div((ONE, ZERO), value), -exponent)
    result = (ONE, ZERO)
    base = value
    power = exponent
    while power:
        if power & 1:
            result = c_mul(result, base)
        base = c_mul(base, base)
        power >>= 1

    return result


# --------------------------------------------------------------------------
# 特殊角：可精确表示的单位根表（键为 π 的有理倍数）
# --------------------------------------------------------------------------

def _unit_root_table():
    """构造单位根表：键为 π 的有理倍数，值为 (cos, sin)。

    只收录余弦、正弦可精确表示的特殊角（π 的 1/6、1/4 倍数）。
    """
    half = Fraction(1, 2)
    half_real = Real(half)
    root3 = Real(0, {3: half}, 0)          # √3/2
    root2 = Real(0, {2: half}, 0)          # √2/2
    neg_root3 = Real(0, {3: -half}, 0)
    neg_root2 = Real(0, {2: -half}, 0)

    return {
        Fraction(0): (Real(1), Real(0)),
        Fraction(1, 6): (root3, half_real),
        Fraction(1, 4): (root2, root2),
        Fraction(1, 3): (half_real, root3),
        Fraction(1, 2): (Real(0), Real(1)),
        Fraction(2, 3): (Real(-half), root3),
        Fraction(3, 4): (neg_root2, root2),
        Fraction(5, 6): (neg_root3, half_real),
        Fraction(1): (Real(-1), Real(0)),
        Fraction(-1, 6): (root3, Real(-half)),
        Fraction(-1, 4): (root2, neg_root2),
        Fraction(-1, 3): (half_real, neg_root3),
        Fraction(-1, 2): (Real(0), Real(-1)),
        Fraction(-2, 3): (Real(-half), neg_root3),
        Fraction(-3, 4): (neg_root2, neg_root2),
        Fraction(-5, 6): (neg_root3, Real(-half)),
    }


UNIT_ROOTS = _unit_root_table()


def arg_coefficient(value):
    """主值辐角 Arg z（π 的有理倍数），不能精确表示时返回 None。"""
    if value is None:
        return None
    real_part, imag_part = value
    if real_part.is_zero and imag_part.is_zero:
        return None

    radius = c_abs(value)
    if radius is None:
        return None

    for angle, (cosine, sine) in UNIT_ROOTS.items():
        candidate = (rmul(radius, cosine), rmul(radius, sine))
        if complex_equal(candidate, value):
            return angle

    return None


def parse_angle(text):
    """解析「π 的有理倍数」文本，返回系数（Fraction）或 None。

    支持 π/4、3π/4、-π/2、π、0、π/6、5π/4；也接受度数写法 45°、-90°。
    """
    if not isinstance(text, str):
        return None
    cleaned = "".join(text.split()).replace("−", "-")
    if not cleaned:
        return None

    if cleaned.endswith("°"):
        value, cursor = _read_rational(cleaned[:-1], 0)
        if value is None or cursor != len(cleaned) - 1:
            return None

        return Fraction(value, 180)

    value = parse_real(text)
    if value is None:
        return None
    if not value.rat == 0 or value.surds:
        return None

    return value.pi


def format_angle(coefficient):
    """把 π 的有理倍数系数格式化成文本。"""
    return _pi_body(Fraction(coefficient))


def roots_of_unity(count):
    """n 次单位根（精确可表示时返回列表，否则返回 None）。

    仅 n ∈ {1, 2, 3, 4, 6} 的单位根可以精确表示。
    """
    if count not in (1, 2, 3, 4, 6):
        return None

    picked = {}
    for angle, (cosine, sine) in UNIT_ROOTS.items():
        turns = angle * count
        if turns.denominator != 1 or turns.numerator % 2 != 0:
            continue
        # 按 [0, 2π) 的顺序排列，主辐角在前的约定
        position = angle % 2
        picked[position] = (cosine, sine)

    if len(picked) != count:
        return None

    return [picked[key] for key in sorted(picked)]


def polar_form(value):
    """返回 (模, 主值辐角系数)；辐角不能精确表示时为 None。"""
    radius = c_abs(value)
    angle = arg_coefficient(value)

    return radius, angle
