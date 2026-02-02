"""
===============================================================================
第一章：Python 基础知识回顾
===============================================================================

这是为量化交易准备的 Python 基础教程。
即使你对 Python 不太熟悉，通过这个教程也能快速上手。

运行方式：直接执行此文件，会看到每个示例的输出
"""

# =============================================================================
# 1. 类型注解 (Type Hints) - Python 3.5+ 引入
# =============================================================================
# 类型注解让代码更清晰，IDE 能更好地提示错误

from typing import List, Dict, Optional, Union, Callable, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


def greet(name: str) -> str:
    """函数参数和返回值的类型注解"""
    return f"Hello, {name}"


def calculate_average(numbers: List[float]) -> float:
    """列表类型注解"""
    return sum(numbers) / len(numbers) if numbers else 0.0


def get_price(symbol: str, default: Optional[float] = None) -> Optional[float]:
    """Optional 表示可能为 None"""
    prices = {"BTCUSDT": 50000.0, "ETHUSDT": 3000.0}
    return prices.get(symbol, default)


# 运行示例
print("=" * 60)
print("1. 类型注解示例")
print("=" * 60)
print(f"greet('Trader') = {greet('Trader')}")
print(f"calculate_average([1, 2, 3, 4, 5]) = {calculate_average([1, 2, 3, 4, 5])}")
print(f"get_price('BTCUSDT') = {get_price('BTCUSDT')}")
print(f"get_price('UNKNOWN') = {get_price('UNKNOWN')}")


# =============================================================================
# 2. 枚举类 (Enum) - 定义固定的选项集合
# =============================================================================
# 量化交易中大量使用枚举来表示订单类型、方向等

class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"      # 买入
    SELL = "sell"    # 卖出


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"  # 市价单：立即以当前市场价格成交
    LIMIT = "limit"    # 限价单：指定价格，等待成交


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"      # 等待中
    SUBMITTED = "submitted"  # 已提交
    FILLED = "filled"        # 已成交
    CANCELLED = "cancelled"  # 已取消


print("\n" + "=" * 60)
print("2. 枚举类示例")
print("=" * 60)
print(f"OrderSide.BUY = {OrderSide.BUY}")
print(f"OrderSide.BUY.value = {OrderSide.BUY.value}")
print(f"OrderSide.BUY.name = {OrderSide.BUY.name}")


# =============================================================================
# 3. 数据类 (dataclass) - Python 3.7+ 引入
# =============================================================================
# 数据类自动生成 __init__, __repr__, __eq__ 等方法
# 非常适合定义数据模型

@dataclass
class Tick:
    """Tick 数据 - 最小粒度的行情数据
    
    什么是 Tick？
    - 每一笔成交都会产生一个 Tick
    - 包含成交价格、数量、时间等信息
    - 是最原始的行情数据
    """
    symbol: str          # 交易对，如 "BTCUSDT"
    price: float         # 成交价格
    volume: float        # 成交数量
    timestamp: datetime  # 成交时间
    side: OrderSide      # 买卖方向


@dataclass
class Bar:
    """K线数据 - 一定时间周期内的价格汇总
    
    什么是 K 线（蜡烛图）？
    - 将一段时间内的交易汇总为一根 "蜡烛"
    - 包含：开盘价、最高价、最低价、收盘价、成交量
    - 常见周期：1分钟、5分钟、15分钟、1小时、4小时、日线
    
    OHLCV 的含义：
    - O (Open): 开盘价 - 这段时间第一笔成交价
    - H (High): 最高价 - 这段时间内的最高成交价
    - L (Low): 最低价 - 这段时间内的最低成交价
    - C (Close): 收盘价 - 这段时间最后一笔成交价
    - V (Volume): 成交量 - 这段时间内的总成交数量
    """
    symbol: str
    open: float      # 开盘价
    high: float      # 最高价
    low: float       # 最低价
    close: float     # 收盘价
    volume: float    # 成交量
    timestamp: datetime


# 创建示例数据
tick = Tick(
    symbol="BTCUSDT",
    price=50000.0,
    volume=0.1,
    timestamp=datetime.now(),
    side=OrderSide.BUY
)

bar = Bar(
    symbol="BTCUSDT",
    open=49000.0,
    high=51000.0,
    low=48500.0,
    close=50000.0,
    volume=1000.0,
    timestamp=datetime.now()
)

print("\n" + "=" * 60)
print("3. 数据类示例")
print("=" * 60)
print(f"Tick: {tick}")
print(f"Bar: {bar}")


# =============================================================================
# 4. 异步编程 (async/await) - 量化交易的核心技术
# =============================================================================
# 为什么需要异步？
# - 量化交易需要同时处理多个任务：接收行情、处理订单、计算指标等
# - 异步让程序在等待网络响应时可以做其他事情，不会阻塞

import asyncio


async def fetch_price(symbol: str) -> float:
    """模拟异步获取价格
    
    async def: 定义异步函数
    await: 等待异步操作完成，但不阻塞其他任务
    """
    print(f"  开始获取 {symbol} 价格...")
    await asyncio.sleep(0.1)  # 模拟网络延迟
    prices = {"BTCUSDT": 50000.0, "ETHUSDT": 3000.0}
    price = prices.get(symbol, 0.0)
    print(f"  获取到 {symbol} 价格: {price}")
    return price


async def fetch_multiple_prices():
    """并发获取多个价格
    
    asyncio.gather: 并发执行多个异步任务
    """
    # 并发执行，总耗时约等于最慢的那个任务
    prices = await asyncio.gather(
        fetch_price("BTCUSDT"),
        fetch_price("ETHUSDT"),
    )
    return prices


print("\n" + "=" * 60)
print("4. 异步编程示例")
print("=" * 60)
# 在普通脚本中运行异步代码
prices = asyncio.run(fetch_multiple_prices())
print(f"获取到的价格: {prices}")


# =============================================================================
# 5. 装饰器 (Decorator) - 策略注册和配置的关键
# =============================================================================
# 装饰器是 Python 的高级特性，用于在不修改函数代码的情况下增强函数功能

from functools import wraps
import time


def timing_decorator(func: Callable) -> Callable:
    """计时装饰器 - 测量函数执行时间"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"  函数 {func.__name__} 执行耗时: {elapsed:.4f}秒")
        return result
    return wrapper


def retry_decorator(max_retries: int = 3):
    """重试装饰器 - 失败时自动重试
    
    这在量化交易中很常用：网络请求可能失败，需要重试
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"  第 {attempt + 1} 次尝试失败: {e}，重试中...")
                    else:
                        raise
            return None
        return wrapper
    return decorator


# 注册表模式 - 用于策略注册
strategy_registry: Dict[str, type] = {}


def register_strategy(name: str):
    """策略注册装饰器
    
    使用方法：
    @register_strategy("my_strategy")
    class MyStrategy:
        pass
    """
    def decorator(cls):
        strategy_registry[name] = cls
        return cls
    return decorator


@timing_decorator
def slow_calculation():
    """被装饰的函数"""
    total = sum(range(100000))
    return total


print("\n" + "=" * 60)
print("5. 装饰器示例")
print("=" * 60)
result = slow_calculation()
print(f"计算结果: {result}")


# =============================================================================
# 6. 上下文管理器 (Context Manager) - 资源管理
# =============================================================================
# with 语句确保资源正确释放，常用于文件、数据库连接、网络连接等

from contextlib import contextmanager


@contextmanager
def database_connection():
    """模拟数据库连接的上下文管理器
    
    使用方法：
    with database_connection() as conn:
        # 使用连接
        pass
    # 连接自动关闭
    """
    print("  打开数据库连接")
    conn = {"connected": True}  # 模拟连接对象
    try:
        yield conn  # yield 之前的代码在进入 with 时执行
    finally:
        print("  关闭数据库连接")  # yield 之后的代码在退出 with 时执行


print("\n" + "=" * 60)
print("6. 上下文管理器示例")
print("=" * 60)
with database_connection() as conn:
    print(f"  使用连接: {conn}")


# =============================================================================
# 7. 生成器 (Generator) - 高效处理大量数据
# =============================================================================
# 生成器可以逐个产出数据，不需要一次性加载所有数据到内存

def generate_ticks(symbol: str, count: int):
    """生成器函数 - 模拟产生 Tick 数据
    
    yield: 每次调用产出一个值，函数状态被保存
    """
    for i in range(count):
        yield Tick(
            symbol=symbol,
            price=50000.0 + i * 10,
            volume=0.1,
            timestamp=datetime.now(),
            side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
        )


print("\n" + "=" * 60)
print("7. 生成器示例")
print("=" * 60)
for i, tick in enumerate(generate_ticks("BTCUSDT", 3)):
    print(f"  Tick {i}: price={tick.price}, side={tick.side.value}")


# =============================================================================
# 8. 面试常见问题
# =============================================================================
print("\n" + "=" * 60)
print("8. 面试常见问题")
print("=" * 60)

questions = """
Q1: Python 中 list 和 tuple 的区别？
A: list 可变，tuple 不可变。tuple 更适合存储不应该被修改的数据。

Q2: *args 和 **kwargs 是什么？
A: *args 接收任意数量的位置参数（tuple）
   **kwargs 接收任意数量的关键字参数（dict）

Q3: 什么是 GIL？
A: Global Interpreter Lock，Python 的全局解释器锁
   它限制了多线程的并行执行，所以 CPU 密集型任务推荐用多进程

Q4: async/await 和多线程的区别？
A: async/await 是协作式多任务，单线程内切换
   多线程是抢占式多任务，由操作系统调度
   IO 密集型任务用 async 更高效

Q5: 装饰器的执行顺序？
A: 多个装饰器从下到上装饰，从上到下执行
   @a
   @b
   def f(): pass
   等价于: f = a(b(f))
"""

print(questions)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Python 基础回顾完成！")
    print("下一步：运行 02_quant_concepts.py 学习量化交易概念")
    print("=" * 60)
