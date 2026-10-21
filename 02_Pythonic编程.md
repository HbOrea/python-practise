# 阶段二：Pythonic 编程

> 目标：从 Java 风格循环转向更自然的 Python 表达。建议 Python 3.11+。

## 题目 1：解包与 enumerate

输入 `[("张三", 95), ("李四", 87)]`，输出 `['1. 张三: 95', '2. 李四: 87']`。不要手动维护序号。

### 参考答案

```python
def ranking(rows: list[tuple[str, int]]) -> list[str]:
    return [f"{index}. {name}: {score}" for index, (name, score) in enumerate(rows, start=1)]

assert ranking([("张三", 95), ("李四", 87)]) == ["1. 张三: 95", "2. 李四: 87"]
```

## 题目 2：排序、lambda 与切片

输入商品列表，筛选有库存商品，按价格升序、同价时按商品名升序，返回前两个商品名。

```python
products = [
    {"name": "B", "price": 30, "stock": 1},
    {"name": "A", "price": 20, "stock": 0},
    {"name": "D", "price": 20, "stock": 2},
    {"name": "C", "price": 20, "stock": 4},
]
# 预期：['C', 'D']
```

### 参考答案

```python
def cheapest_in_stock(products: list[dict], limit: int = 2) -> list[str]:
    if limit < 0:
        raise ValueError("limit 不得为负数")
    available = (p for p in products if p["stock"] > 0)
    ordered = sorted(available, key=lambda p: (p["price"], p["name"]))
    return [p["name"] for p in ordered[:limit]]

assert cheapest_in_stock(products) == ["C", "D"]
```

## 题目 3：生成器与惰性处理

实现 `even_squares(n)`，使用 `yield` 依次生成 `0..n-1` 中偶数的平方，而不是一次返回列表。

### 参考答案

```python
from collections.abc import Iterator

def even_squares(n: int) -> Iterator[int]:
    for i in range(n):
        if i % 2 == 0:
            yield i * i

assert list(even_squares(7)) == [0, 4, 16, 36]
```

**思考**：生成器在遍历时才计算，适合大文件与流式处理；被遍历完后不会自动重置。

## 题目 4：装饰器统计耗时

为任意同步函数编写 `timed` 装饰器，保留函数元数据，返回值不能改变。

### 参考答案

```python
from functools import wraps
from time import perf_counter
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def timed(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            print(f"{func.__name__}: {perf_counter()-start:.4f}s")
    return wrapper

@timed
def add(a: int, b: int) -> int:
    return a + b

assert add(2, 3) == 5
assert add.__name__ == "add"
```

**注意**：该版本针对同步函数；异步函数应编写 `async def wrapper` 并 `await func(...)`。

## 题目 5：上下文管理器

使用 `contextlib.contextmanager` 写 `temporary_value(config, key, value)`：在 `with` 块中临时替换字典值，退出后恢复；不存在的键应在退出时删除。

### 参考答案

```python
from contextlib import contextmanager
from collections.abc import Iterator

_SENTINEL = object()

@contextmanager
def temporary_value(config: dict, key: str, value: object) -> Iterator[None]:
    old_value = config.get(key, _SENTINEL)
    config[key] = value
    try:
        yield
    finally:
        if old_value is _SENTINEL:
            config.pop(key, None)
        else:
            config[key] = old_value

cfg = {"timeout": 5}
with temporary_value(cfg, "timeout", 20):
    assert cfg["timeout"] == 20
assert cfg == {"timeout": 5}
```

## 阶段验收

能区分列表推导式和生成器表达式；会用 `enumerate`、`zip`、`sorted(key=...)`、`yield`、`@wraps`、`with`；知道什么时候不应该为追求简短而压缩代码。
