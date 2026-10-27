# 缺陷报告（中文版）

> 本文是 `bug_report.md` 的中文翻译，仅供查阅，提交时以英文版为准。

本报告记录了在存在缺陷的程序中发现的 bug，包括失败的测试用例、根因分析以及所做的代码修复。

Problem 1 使用 `doctest` 进行测试，因此下文的“失败测试用例”是 `calculate_trip_fare()` 文档字符串中的 doctest 示例。函数体中的计费逻辑已对照每一条计价规则检查过，是正确的。所有缺陷都出在预先写好的 doctest 里。运行命令：

```bash
python -m doctest -v problem1.py
```

修复前：运行了 12 个示例，6 个失败。修复后：运行了 15 个示例，全部通过。

---

## 缺陷报告 1：注释行被当成预期输出

### 1. 被测程序
- **文件：** `problem1.py`
- **类 / 函数：** `calculate_trip_fare()`（文档字符串中的 doctest）

### 2. 失败的测试用例

```python
>>> calculate_trip_fare(1.5)
3.0
# TODO: Add more doctests here
# tandard normal trip (e.g. 5.0 km adult)
```

VSCode 中的测试运行截图：

<!-- 在此插入 VSCode 测试面板截图，例如 ![doctest run](assets/problem1_doctest_run.png) -->

**测试输出 / 错误信息：**
```text
File "problem1.py", line 34, in problem1.calculate_trip_fare
Failed example:
    calculate_trip_fare(1.5)
Expected:
    3.0
    # TODO: Add more doctests here
    # tandard normal trip (e.g. 5.0 km adult)
Got:
    3.0
```

### 3. 根因分析
- **预期行为：** `calculate_trip_fare(1.5)` 返回 `3.0`，该示例应当通过。
- **实际行为：** 函数明明返回了 `3.0`，示例却失败了。
- **根本原因：** doctest 会把 `>>>` 之后、直到下一个空行或下一个 `>>>` 之前的所有行都当作预期输出。这两行 `#` 注释紧跟在 `3.0` 下面，中间没有空行，所以 doctest 认为它们也应该被打印出来。

### 4. 代码修复与 Diff
现在在预期输出和注释之间加了一个空行。

```diff
     >>> calculate_trip_fare(1.5)
     3.0
-    # TODO: Add more doctests here
-    # tandard normal trip (e.g. 5.0 km adult)
+
+    # Standard normal trips (adult, no rush hour)
     >>> calculate_trip_fare(5.0)
```

---

## 缺陷报告 2：预期值写成 `4.50`，而不是 `4.5`

### 1. 被测程序
- **文件：** `problem1.py`
- **类 / 函数：** `calculate_trip_fare()`（文档字符串中的 doctest）

### 2. 失败的测试用例

```python
>>> calculate_trip_fare(6.0, passenger_type="child")
4.50
>>> calculate_trip_fare(6.0, passenger_type="senior")
6.30
```

**测试输出 / 错误信息：**
```text
Failed example:
    calculate_trip_fare(6.0, passenger_type="child")
Expected:
    4.50
Got:
    4.5

Failed example:
    calculate_trip_fare(6.0, passenger_type="senior")
Expected:
    6.30
Got:
    6.3
```

### 3. 根因分析
- **预期行为：** 6.0 km 的儿童票价为 9.00 x 0.5 = 4.5，老年人票价为 9.00 x 0.7 = 6.3。
- **实际行为：** 函数返回的是浮点数 `4.5` 和 `6.3`。
- **根本原因：** doctest 是把结果打印出来的 `repr` 当作文本来比较的。`float` 不会打印多余的尾随零，所以 `4.50` 和 `6.30` 永远不可能匹配。数值本身是对的，错的只是书写格式。

### 4. 代码修复与 Diff

```diff
     >>> calculate_trip_fare(6.0, passenger_type="child")
-    4.50
+    4.5
     >>> calculate_trip_fare(6.0, passenger_type="senior")
-    6.30
+    6.3
```

---

## 缺陷报告 3：预期值没有考虑恰好半分钱时的“四舍六入五取偶”

### 1. 被测程序
- **文件：** `problem1.py`
- **类 / 函数：** `calculate_trip_fare()`（文档字符串中的 doctest）

### 2. 失败的测试用例

```python
>>> calculate_trip_fare(11.0, is_rush_hour=True)
20.63
>>> calculate_trip_fare(6.0, is_rush_hour=True, passenger_type="child")
5.63
```

**测试输出 / 错误信息：**
```text
Failed example:
    calculate_trip_fare(11.0, is_rush_hour=True)
Expected:
    20.63
Got:
    20.62

Failed example:
    calculate_trip_fare(6.0, is_rush_hour=True, passenger_type="child")
Expected:
    5.63
Got:
    5.62
```

### 3. 根因分析
- **预期行为：** 作者假设使用普通的“四舍五入”（20.625 -> 20.63，5.625 -> 5.63）。
- **实际行为：** 函数返回 `20.62` 和 `5.62`。
- **根本原因：** 这两个票价都恰好落在半分钱上（11 km：16.5 x 1.25 = 20.625；6 km 儿童高峰：9.0 x 1.25 x 0.5 = 5.625）。这些数值在二进制浮点数中可以被精确表示，而 Python 的 `round()` 对恰好处于中间的数值会舍入到最近的偶数，因此得到 `20.62` 和 `5.62`。函数实现符合规格说明（“保留 2 位小数”），规格并没有说明遇到恰好一半时如何处理。错的是 doctest 的预期值，不是函数。现在的测试避开了这类恰好一半的数值，不再依赖具体的舍入模式。

### 4. 代码修复与 Diff
函数没有改动。这两个示例被换成了没有歧义的输入。

```diff
-    >>> calculate_trip_fare(11.0, is_rush_hour=True)
-    20.63
+    >>> calculate_trip_fare(8.0, is_rush_hour=True)
+    15.0
...
-    >>> calculate_trip_fare(6.0, is_rush_hour=True, passenger_type="child")
-    5.63
+    >>> calculate_trip_fare(8.0, is_rush_hour=True, passenger_type="child")
+    7.5
+    >>> calculate_trip_fare(8.0, is_rush_hour=True, passenger_type="senior")
+    10.5
```

---

## 缺陷报告 4：异常信息被截断（缺少结尾引号）

### 1. 被测程序
- **文件：** `problem1.py`
- **类 / 函数：** `calculate_trip_fare()`（文档字符串中的 doctest）

### 2. 失败的测试用例

```python
>>> calculate_trip_fare(500.0, passenger_type="student")
Traceback (most recent call last):
...
ValueError: invalid passenger_type: must be 'adult', 'child', or 'senior
```

**测试输出 / 错误信息：**
```text
Failed example:
    calculate_trip_fare(500.0, passenger_type="student")
Expected:
    Traceback (most recent call last):
    ...
    ValueError: invalid passenger_type: must be 'adult', 'child', or 'senior
Got:
    Traceback (most recent call last):
      (stack frames omitted)
    ValueError: invalid passenger_type: must be 'adult', 'child', or 'senior'
```

### 3. 根因分析
- **预期行为：** 异常信息与规格说明完全一致：`invalid passenger_type: must be 'adult', 'child', or 'senior'`。
- **实际行为：** 函数抛出的信息是正确的。
- **根本原因：** doctest 中的预期信息少了最后一个 `'`。doctest 会精确比较异常类型和信息文本，所以该示例失败了。

### 4. 代码修复与 Diff

```diff
-    ValueError: invalid passenger_type: must be 'adult', 'child', or 'senior
+    ValueError: invalid passenger_type: must be 'adult', 'child', or 'senior'
```

---

## 新增的 Doctest（要求：至少 6 个）

文档字符串中现在有 15 个 doctest 示例，全部通过：

| 类别 | 示例 |
|---|---|
| 标准行程 | 成人 `1.5`、`5.0`、`6.0` km |
| 边界情况 | `0.0` km、恰好 `2.0` km、`2.5` km（刚超过起步距离） |
| 高峰时段 | `is_rush_hour=True` 时的 `10.0` km 和 `8.0` km |
| 乘客折扣 | `6.0` km 儿童（4.5）、`6.0` km 老年人（6.3） |
| 高峰时段 + 折扣 | `8.0` km 儿童（7.5）、`8.0` km 老年人（10.5） |
| 异常 | `-100.0` km、`-0.1` km、无效类型 `"student"` |

`python -m doctest -v problem1.py` 的最终结果：**15 个通过，0 个失败。**
