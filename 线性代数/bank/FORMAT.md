# 线性代数题库数据格式（bank 包）

本文件是题库的唯一格式契约。所有题库文件都必须严格遵守，否则
`build_paper.py` / `verify_paper.py` / 抽题服务会报错。

## 总规则

- 每个题库文件是一个 Python 模块，只包含数据，不写逻辑。
- 所有字符串使用 UTF-8；答案统一写成字符串（如 `"-3"`、`"3/4"`）。
- 所有 id 在整份题库中必须唯一，前缀区分题型：
  `c_la_` 选择题、`j_la_` 判断题、`f_la_` 填空题、`x_la_` 计算题。
- 解析、题目说明一律使用中文。
- 题干、选项中的矩阵用 `[[key]]` 标记占位，`key` 对应本题
  `matrices` 字典里的一个图形矩阵；下发后由前端 canvas 渲染。
- 矩阵规格（matrix spec）统一为：
  ```python
  {
      "label": "A",      # 可选，显示在矩阵左侧的标签
      "style": "matrix", # 可选：matrix 方括号 | det 行列式竖线 | aug 增广分隔线
      "data": [[1, 2], [3, 4]],  # 二维数据；元素是 int / float / 字符串
  }
  ```
  元素字符串支持分数 `"3/2"`、小数 `"0.5"`、未知数字母 `"a"`。

## 题库文件与导出变量

| 文件 | 导出变量 | 含义 |
|------|----------|------|
| `bank/choice_questions.py` | `CHOICE` | 选择题列表 |
| `bank/judge_questions.py` | `JUDGE` | 判断题列表 |
| `bank/fill_questions.py` | `FILL` | 填空题（数值答案）列表 |
| `bank/calc_questions.py` | `CALC` | 计算题（矩阵答案）列表 |

## 抽题方案（meta.py）

| 大题 | 入库 | 每卷抽取 | 每题 | 每卷分值 |
|------|------|----------|------|----------|
| 一、选择题 | 20 | 10 | 3 分 | 30 |
| 二、判断题 | 16 | 8 | 2 分 | 16 |
| 三、填空题 | 16 | 8 | 3 分 | 24 |
| 四、计算题 | 10 | 6 | 5 分 | 30 |

每卷 32 题、100 分、120 分钟。

---

## 一、选择题（CHOICE）

```python
{
    "id": "c_la_03",
    "score": 3,
    "stem": "行列式 [[D]] 的值是（　　）。",
    "options": ["-2", "2", "-10", "10"],  # 恰好 4 个；可含 [[key]] 标记
    "answer": 0,                          # 正确选项下标 0~3
    "matrices": {"D": {"style": "det", "data": [[1, 2], [3, 4]]}},  # 可选
    "verify": {"kind": "det", "matrix": "D"},  # 可选，verify_paper 机械复核
    "explain": "1×4 − 2×3 = −2。",
}
```

## 二、判断题（JUDGE）

```python
{
    "id": "j_la_04",
    "score": 2,
    "stem": "对任意 n 阶方阵 A，都有 |Aᵀ| = |A|。",
    "answer": True,     # 必须是 Python 布尔值
    "explain": "行列式与其转置的值相等。",
}
```

## 三、填空题（FILL，数值答案）

```python
{
    "id": "f_la_03",
    "score": 3,
    "stem": "…则 |A⁻¹| = ______。",
    "answer": "1/3",    # 字符串：整数、小数或分数
    "matrices": {...},  # 可选
    "verify": {...},    # 可选
    "explain": "|A⁻¹| = 1/|A| = 1/3。",
}
```

判分：把作答解析成精确分数后与标准答案比对，全对得分，否则零分。

## 四、计算题（CALC，矩阵答案）

```python
{
    "id": "x_la_01",
    "score": 5,
    "stem": "设矩阵 [[A]]，求 A 的逆矩阵 A⁻¹。",
    "matrices": {"A": {"data": [[1, 2], [3, 4]]}},
    "answer_type": "matrix",
    "rows": 2, "cols": 2,                       # 作答矩阵的固定形状
    "answer": {"rows": 2, "cols": 2,
               "data": [["-2", "1"], ["3/2", "-1/2"]]},
    "verify": {"kind": "inv", "matrix": "A"},   # verify_paper 机械复核
    "grading": {"kind": "eigvec", ...},         # 可选：语义判分（默认按元素比例）
    "explain": "…",
}
```

默认判分：把作答解析成分数矩阵后逐元素比对，
得分 = round(满分 × 正确元素数 / 元素总数)。

`grading.kind` 目前支持：

- `eigvec`：答案列向量满足 Av = λv 且 v ≠ 0 即满分（特征向量不唯一）。
- `null_basis`：答案各列都是 Ax = 0 的非零解、彼此线性无关且列数等于
  n − r(A) 时满分；单个正确列得该列份额的一半。

## verify 校验说明（供 verify_paper.py 机械复核答案）

| kind | 参数 | 复核内容 |
|------|------|----------|
| `det` | `matrix` 或 `matrix_literal` | 答案/指定矩阵的行列式与答案一致 |
| `rank` | `matrix` 或 `matrix_literal` | 秩与答案一致 |
| `det_scale` | `matrix`, `k` | 答案 = kⁿ·det(A) |
| `adj` | `matrix`, `option` | 选项矩阵 = 伴随矩阵 |
| `power` | `matrix`, `n`, `option?` | 选项矩阵 = Aⁿ |
| `mul` | `left`, `right` | 答案 = A·B |
| `outer` | `left`, `right` | 答案 = α·βᵀ |
| `inner` | `left`, `right` | 答案 = αᵀβ |
| `inv` | `matrix` | 答案 = A⁻¹ |
| `solve` | `matrix`（增广） | 答案 = 唯一解向量 |
| `solve_component` | `aug_literal`, `component` | 指定分量与答案一致 |
| `eigvec` | `matrix`, `eigen` | Av = λv 且 v ≠ 0 |
| `eigs_option` | `matrix`, `option` | 对角矩阵对角元 = A 的特征值（重数计） |
| `eigs_semidefinite` | `matrix` | 特征值全 ≥ 0 且含 0（半正定） |
| `sub_det_zero` | `matrix`, `var`, `eigen` | 代入答案后 det(A − λE) = 0 |
| `free_count` | `matrix` 或 `matrix_literal` | 答案 = n − rank(A) |
| `null_basis` | `matrix` | 答案列构成基础解系 |
| `single_invertible` | `invertible`, `singular` | 指定矩阵可逆、其余奇异 |

答案为数值的题目，复核结果与 `answer` 字段比对；答案为选项矩阵的题目，
复核结果与 `matrices[option]` 比对。
