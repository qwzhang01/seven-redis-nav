"""
===============================================================================
第三章：项目架构详解
===============================================================================

本章详细介绍量化交易系统的项目结构和核心组件。
帮助你理解每个模块的作用，以便在面试中清晰地描述系统架构。
"""

# =============================================================================
# 1. 项目整体结构
# =============================================================================
print("=" * 70)
print("1. 项目整体结构")
print("=" * 70)

project_structure = """
quant_trading_system/
│
├── src/quant_trading_system/      # 主源码目录
│   │
│   ├── core/                      # 🔧 核心模块（基础设施层）
│   │   ├── config.py              # 配置管理
│   │   ├── events.py              # 事件引擎
│   │   ├── message_bus.py         # 消息总线
│   │   ├── logging.py             # 日志系统
│   │   └── exceptions.py          # 异常定义
│   │
│   ├── models/                    # 📦 数据模型（数据定义层）
│   │   ├── market.py              # 行情数据模型
│   │   ├── trading.py             # 交易数据模型
│   │   └── account.py             # 账户数据模型
│   │
│   ├── services/                  # ⚙️ 业务服务（核心业务层）
│   │   ├── market/                # 行情服务
│   │   │   ├── data_collector.py  # 数据采集
│   │   │   ├── kline_engine.py    # K线合成
│   │   │   └── market_service.py  # 行情分发
│   │   │
│   │   ├── indicators/            # 指标服务
│   │   │   ├── base.py            # 指标基类
│   │   │   ├── technical.py       # 技术指标
│   │   │   └── indicator_engine.py # 指标引擎
│   │   │
│   │   ├── strategy/              # 策略服务
│   │   │   ├── base.py            # 策略基类
│   │   │   ├── signal.py          # 交易信号
│   │   │   └── strategy_engine.py # 策略引擎
│   │   │
│   │   ├── backtest/              # 回测服务
│   │   │   ├── backtest_engine.py # 回测引擎
│   │   │   └── performance.py     # 绩效分析
│   │   │
│   │   ├── trading/               # 交易服务
│   │   │   ├── order_manager.py   # 订单管理
│   │   │   └── trading_engine.py  # 交易引擎
│   │   │
│   │   └── risk/                  # 风控服务
│   │       └── risk_manager.py    # 风险管理
│   │
│   ├── strategies/                # 📈 内置策略
│   │   └── examples.py            # 示例策略
│   │
│   ├── api/                       # 🌐 API服务（接口层）
│   │   ├── main.py                # FastAPI 应用
│   │   └── routers/               # API 路由
│   │
│   └── cli.py                     # 💻 命令行工具
│
├── tests/                         # 🧪 测试
├── examples/                      # 📚 示例代码
├── docs/tutorial/                 # 📖 教程文档
└── docker/                        # 🐳 Docker 配置
"""
print(project_structure)


# =============================================================================
# 2. 核心模块详解
# =============================================================================
print("\n" + "=" * 70)
print("2. 核心模块详解")
print("=" * 70)

# -----------------------------------------------------------------------------
# 2.1 事件引擎 (core/events.py)
# -----------------------------------------------------------------------------
print("\n--- 2.1 事件引擎 (Event Engine) ---")

event_engine_explanation = """
事件引擎是整个系统的"心脏"，负责协调各个模块之间的通信。

核心设计理念：
┌─────────────────────────────────────────────────────────────┐
│                      事件引擎                               │
│                                                             │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ 行情事件 │────▶│ 事件队列 │────▶│ 事件分发 │              │
│  └─────────┘     └─────────┘     └─────────┘              │
│  ┌─────────┐           │               │                   │
│  │ 订单事件 │───────────┤               │                   │
│  └─────────┘           │               ▼                   │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ 成交事件 │────▶│ 优先队列 │────▶│ 处理器1  │              │
│  └─────────┘     └─────────┘     └─────────┘              │
│                        │         ┌─────────┐              │
│                        └────────▶│ 处理器2  │              │
│                                  └─────────┘              │
└─────────────────────────────────────────────────────────────┘

关键类和方法：

1. Event（事件基类）
   - event_type: 事件类型
   - data: 事件数据
   - timestamp: 时间戳
   - priority: 优先级

2. EventEngine（事件引擎）
   - subscribe(event_type, handler): 订阅事件
   - publish(event): 发布事件
   - start(): 启动引擎
   - stop(): 停止引擎

事件类型：
- TICK: Tick 行情事件
- BAR: K线事件
- ORDER: 订单事件
- TRADE: 成交事件
- POSITION: 仓位变化事件
- SIGNAL: 交易信号事件

使用示例：
```python
from core.events import EventEngine, Event, EventType

# 创建事件引擎
engine = EventEngine()

# 定义事件处理器
async def on_tick(event: Event):
    tick = event.data
    print(f"收到行情: {tick.symbol} @ {tick.price}")

# 订阅事件
engine.subscribe(EventType.TICK, on_tick)

# 发布事件
await engine.publish(Event(
    event_type=EventType.TICK,
    data=tick_data
))
```

面试重点：
- 为什么使用事件驱动架构？
  答：解耦、异步、可扩展、响应快
- 如何保证事件的顺序？
  答：使用优先级队列，同优先级按时间排序
- 如何处理高并发？
  答：异步处理、多消费者、背压控制
"""
print(event_engine_explanation)


# -----------------------------------------------------------------------------
# 2.2 消息总线 (core/message_bus.py)
# -----------------------------------------------------------------------------
print("\n--- 2.2 消息总线 (Message Bus) ---")

message_bus_explanation = """
消息总线用于系统内部和跨服务的消息传递。

架构设计：
┌─────────────────────────────────────────────────────────────┐
│                      消息总线                               │
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│  │   生产者     │────▶│    Kafka    │────▶│   消费者     │  │
│  │(行情采集器)  │     │   /Redis    │     │(策略引擎)    │  │
│  └─────────────┘     └─────────────┘     └─────────────┘  │
│                            │                               │
│                            ▼                               │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│  │   生产者     │────▶│   Topic:    │────▶│   消费者     │  │
│  │(订单管理器)  │     │market.tick  │     │(风控服务)    │  │
│  └─────────────┘     │market.bar   │     └─────────────┘  │
│                      │order.update │                       │
│                      └─────────────┘                       │
└─────────────────────────────────────────────────────────────┘

支持的消息后端：
1. Redis Streams: 轻量级，适合单机部署
2. Apache Kafka: 重量级，适合分布式部署

Topic 设计：
- market.tick.{symbol}: Tick 行情
- market.bar.{symbol}.{interval}: K线数据
- order.created: 订单创建
- order.filled: 订单成交
- signal.{strategy_id}: 策略信号
- risk.alert: 风险告警
"""
print(message_bus_explanation)


# -----------------------------------------------------------------------------
# 2.3 配置管理 (core/config.py)
# -----------------------------------------------------------------------------
print("\n--- 2.3 配置管理 (Config) ---")

config_explanation = """
使用 Pydantic Settings 管理配置，支持环境变量和配置文件。

配置层级：
┌─────────────────────────────────────────────────────────────┐
│  1. 默认配置 (代码中的默认值)                               │
│         ▼                                                   │
│  2. 配置文件 (.env, config.yaml)                           │
│         ▼                                                   │
│  3. 环境变量 (QUANT_*)                                     │
│         ▼                                                   │
│  4. 命令行参数 (最高优先级)                                 │
└─────────────────────────────────────────────────────────────┘

主要配置类：
```python
class Settings(BaseSettings):
    # 系统配置
    app_name: str = "QuantTradingSystem"
    debug: bool = False
    log_level: str = "INFO"
    
    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # 数据库配置
    database_url: str = "postgresql://..."
    
    # 交易所配置
    exchange_api_key: str = ""
    exchange_secret: str = ""
    
    # 风控配置
    max_position_size: float = 0.1
    max_daily_loss: float = 0.05
```

使用方式：
```python
from core.config import get_settings

settings = get_settings()
print(settings.redis_host)
```
"""
print(config_explanation)


# =============================================================================
# 3. 业务服务详解
# =============================================================================
print("\n" + "=" * 70)
print("3. 业务服务详解")
print("=" * 70)


# -----------------------------------------------------------------------------
# 3.1 行情服务
# -----------------------------------------------------------------------------
print("\n--- 3.1 行情服务 (Market Service) ---")

market_service_explanation = """
行情服务负责采集、处理和分发市场数据。

数据流：
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  交易所API ──▶ DataCollector ──▶ KlineEngine ──▶ 分发      │
│                     │                │                      │
│                     ▼                ▼                      │
│                  原始Tick        多周期K线                  │
│                     │                │                      │
│                     ▼                ▼                      │
│                  存储层          策略引擎                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

1. DataCollector（数据采集器）
   - 连接交易所 WebSocket
   - 处理断线重连
   - 数据标准化

2. KlineEngine（K线合成引擎）
   - 从 Tick 合成 K线
   - 支持多周期：1m, 5m, 15m, 1h, 4h, 1d
   - 环形缓冲区存储

3. MarketService（行情服务）
   - 订阅管理
   - 数据分发
   - 历史数据查询

K线合成算法（面试重点）：
```python
def on_tick(self, tick):
    # 判断是否需要生成新K线
    current_interval = self.get_interval_start(tick.timestamp)
    
    if current_interval != self.current_bar_start:
        # 保存当前K线
        self.save_bar(self.current_bar)
        # 开启新K线
        self.current_bar = Bar(
            open=tick.price,
            high=tick.price,
            low=tick.price,
            close=tick.price,
            volume=tick.volume
        )
        self.current_bar_start = current_interval
    else:
        # 更新当前K线
        self.current_bar.high = max(self.current_bar.high, tick.price)
        self.current_bar.low = min(self.current_bar.low, tick.price)
        self.current_bar.close = tick.price
        self.current_bar.volume += tick.volume
```
"""
print(market_service_explanation)


# -----------------------------------------------------------------------------
# 3.2 指标服务
# -----------------------------------------------------------------------------
print("\n--- 3.2 指标服务 (Indicator Service) ---")

indicator_service_explanation = """
指标服务提供各种技术指标的计算。

指标分类：
┌─────────────────────────────────────────────────────────────┐
│  趋势指标          动量指标          成交量指标             │
│  ├── SMA          ├── RSI           ├── OBV               │
│  ├── EMA          ├── KDJ           ├── VWAP              │
│  ├── MACD         ├── CCI           └── MFI               │
│  └── BOLL         └── WR                                   │
│                                                             │
│  波动率指标                                                 │
│  ├── ATR                                                   │
│  └── 标准差                                                │
└─────────────────────────────────────────────────────────────┘

指标基类设计：
```python
class Indicator(ABC):
    def __init__(self, **params):
        self.params = params
        self.values = []
    
    @abstractmethod
    def calculate(self, data: np.ndarray) -> np.ndarray:
        '''计算指标值'''
        pass
    
    def update(self, value: float) -> float:
        '''增量更新（用于实时计算）'''
        pass
```

注册器模式：
```python
# 注册指标
@register_indicator("SMA")
class SMA(Indicator):
    def calculate(self, data, period=20):
        return data.rolling(period).mean()

# 使用指标
indicator = create_indicator("SMA", period=20)
result = indicator.calculate(prices)
```

性能优化（面试重点）：
1. 向量化计算：使用 NumPy 而非循环
2. 增量更新：新数据来时只计算变化部分
3. 缓存结果：避免重复计算
4. JIT 编译：使用 Numba 加速
"""
print(indicator_service_explanation)


# -----------------------------------------------------------------------------
# 3.3 策略服务
# -----------------------------------------------------------------------------
print("\n--- 3.3 策略服务 (Strategy Service) ---")

strategy_service_explanation = """
策略服务管理策略的生命周期和执行。

策略生命周期：
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  初始化 ──▶ 加载 ──▶ 启动 ──▶ 运行 ──▶ 停止 ──▶ 清理      │
│    │                          │                             │
│    │                          ▼                             │
│    │                      ┌──────┐                          │
│    │                      │ 暂停 │                          │
│    │                      └──────┘                          │
│    │                                                        │
│    ▼                                                        │
│  参数配置                                                   │
│  数据订阅                                                   │
│  指标初始化                                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘

策略基类：
```python
class Strategy(ABC):
    def __init__(self, strategy_id: str, params: dict):
        self.strategy_id = strategy_id
        self.params = params
        self.positions = {}
        self.orders = {}
    
    @abstractmethod
    async def on_bar(self, bar: Bar):
        '''K线事件回调'''
        pass
    
    @abstractmethod  
    async def on_tick(self, tick: Tick):
        '''Tick事件回调'''
        pass
    
    async def on_order(self, order: Order):
        '''订单事件回调'''
        pass
    
    async def on_trade(self, trade: Trade):
        '''成交事件回调'''
        pass
    
    def buy(self, symbol: str, quantity: float, price: float = None):
        '''发送买入订单'''
        pass
    
    def sell(self, symbol: str, quantity: float, price: float = None):
        '''发送卖出订单'''
        pass
```

示例策略：
```python
@register_strategy("ma_cross")
class MACrossStrategy(Strategy):
    '''均线交叉策略'''
    
    def __init__(self, strategy_id, params):
        super().__init__(strategy_id, params)
        self.fast_period = params.get('fast_period', 10)
        self.slow_period = params.get('slow_period', 20)
        self.prices = []
    
    async def on_bar(self, bar: Bar):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.slow_period:
            return
        
        fast_ma = np.mean(self.prices[-self.fast_period:])
        slow_ma = np.mean(self.prices[-self.slow_period:])
        
        # 金叉买入
        if fast_ma > slow_ma and self.prev_fast_ma <= self.prev_slow_ma:
            self.buy(bar.symbol, quantity=0.1)
        
        # 死叉卖出
        elif fast_ma < slow_ma and self.prev_fast_ma >= self.prev_slow_ma:
            self.sell(bar.symbol, quantity=0.1)
        
        self.prev_fast_ma = fast_ma
        self.prev_slow_ma = slow_ma
```
"""
print(strategy_service_explanation)


# -----------------------------------------------------------------------------
# 3.4 回测服务
# -----------------------------------------------------------------------------
print("\n--- 3.4 回测服务 (Backtest Service) ---")

backtest_service_explanation = """
回测服务用于测试策略在历史数据上的表现。

回测引擎架构：
┌─────────────────────────────────────────────────────────────┐
│                      回测引擎                               │
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│  │  历史数据    │────▶│  事件生成器  │────▶│  策略执行    │  │
│  └─────────────┘     └─────────────┘     └─────────────┘  │
│                                                │            │
│                                                ▼            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│  │  绩效分析    │◀────│  订单撮合    │◀────│  信号生成    │  │
│  └─────────────┘     └─────────────┘     └─────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

两种回测模式：

1. 向量化回测（Vectorized Backtest）
   - 一次性处理所有数据
   - 速度快，适合简单策略
   - 不支持复杂订单逻辑

2. 事件驱动回测（Event-Driven Backtest）
   - 模拟真实交易环境
   - 逐个处理数据点
   - 支持复杂订单类型
   - 结果更真实

交易成本模拟：
```python
class CostModel:
    def __init__(self):
        self.commission_rate = 0.001  # 0.1% 手续费
        self.slippage_rate = 0.0005   # 0.05% 滑点
    
    def calculate_cost(self, price, quantity):
        commission = price * quantity * self.commission_rate
        slippage = price * quantity * self.slippage_rate
        return commission + slippage
```

绩效指标计算：
```python
class PerformanceAnalyzer:
    def analyze(self, equity_curve, trades):
        return {
            'total_return': self.calc_total_return(equity_curve),
            'annual_return': self.calc_annual_return(equity_curve),
            'max_drawdown': self.calc_max_drawdown(equity_curve),
            'sharpe_ratio': self.calc_sharpe_ratio(equity_curve),
            'win_rate': self.calc_win_rate(trades),
            'profit_factor': self.calc_profit_factor(trades),
        }
```
"""
print(backtest_service_explanation)


# -----------------------------------------------------------------------------
# 3.5 风控服务
# -----------------------------------------------------------------------------
print("\n--- 3.5 风控服务 (Risk Service) ---")

risk_service_explanation = """
风控服务是保护资金安全的最后一道防线。

风控层级：
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    事前风控                          │   │
│  │  • 订单参数验证  • 资金检查  • 仓位限制  • 频率控制  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    事中风控                          │   │
│  │  • 实时监控      • 止损触发  • 风险指标  • 熔断机制  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    事后风控                          │   │
│  │  • 交易审计      • 绩效分析  • 违规检测  • 报告生成  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

风控规则示例：
```python
class RiskManager:
    def __init__(self, config):
        self.max_position_ratio = config.max_position_ratio  # 最大仓位比例
        self.max_order_size = config.max_order_size          # 最大单笔订单
        self.max_daily_loss = config.max_daily_loss          # 每日最大亏损
        self.max_orders_per_minute = config.max_orders_per_minute
    
    def check_order(self, order: Order, account: Account) -> RiskCheckResult:
        '''订单风控检查'''
        
        # 检查订单大小
        if order.quantity > self.max_order_size:
            return RiskCheckResult(passed=False, reason="订单超过最大限制")
        
        # 检查仓位
        position_value = order.price * order.quantity
        if position_value / account.equity > self.max_position_ratio:
            return RiskCheckResult(passed=False, reason="超过最大仓位限制")
        
        # 检查每日亏损
        if account.daily_loss >= self.max_daily_loss:
            return RiskCheckResult(passed=False, reason="已达到每日亏损上限")
        
        # 检查交易频率
        if self.order_count_last_minute >= self.max_orders_per_minute:
            return RiskCheckResult(passed=False, reason="交易过于频繁")
        
        return RiskCheckResult(passed=True)
```
"""
print(risk_service_explanation)


# =============================================================================
# 4. API 服务
# =============================================================================
print("\n" + "=" * 70)
print("4. API 服务")
print("=" * 70)

api_explanation = """
使用 FastAPI 构建 RESTful API 和 WebSocket 服务。

API 设计：
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  GET  /api/v1/market/klines/{symbol}      # 获取K线数据    │
│  GET  /api/v1/market/ticker/{symbol}      # 获取最新行情   │
│  WS   /api/v1/market/stream/{symbol}      # 实时行情推送   │
│                                                             │
│  POST /api/v1/strategy/                   # 创建策略       │
│  GET  /api/v1/strategy/{id}               # 获取策略信息   │
│  POST /api/v1/strategy/{id}/start         # 启动策略       │
│  POST /api/v1/strategy/{id}/stop          # 停止策略       │
│                                                             │
│  POST /api/v1/order/                      # 下单           │
│  GET  /api/v1/order/{id}                  # 查询订单       │
│  DELETE /api/v1/order/{id}                # 撤单           │
│                                                             │
│  GET  /api/v1/account/balance             # 查询余额       │
│  GET  /api/v1/account/positions           # 查询持仓       │
│                                                             │
│  POST /api/v1/backtest/                   # 运行回测       │
│  GET  /api/v1/backtest/{id}/result        # 获取回测结果   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

FastAPI 示例：
```python
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

app = FastAPI(title="Quant Trading System")

class OrderRequest(BaseModel):
    symbol: str
    side: str  # buy/sell
    order_type: str  # market/limit
    quantity: float
    price: float = None

@app.post("/api/v1/order/")
async def create_order(request: OrderRequest):
    '''创建订单'''
    order = await order_manager.create_order(
        symbol=request.symbol,
        side=request.side,
        order_type=request.order_type,
        quantity=request.quantity,
        price=request.price
    )
    return {"order_id": order.order_id, "status": order.status}

@app.websocket("/api/v1/market/stream/{symbol}")
async def market_stream(websocket: WebSocket, symbol: str):
    '''实时行情 WebSocket'''
    await websocket.accept()
    async for tick in market_service.subscribe(symbol):
        await websocket.send_json(tick.to_dict())
```
"""
print(api_explanation)


# =============================================================================
# 5. 面试重点总结
# =============================================================================
print("\n" + "=" * 70)
print("5. 面试重点总结")
print("=" * 70)

interview_summary = """
项目架构相关问题：

Q1: 描述一下系统的整体架构？
A: 分层架构：
   - API层：FastAPI 提供 RESTful API 和 WebSocket
   - 业务层：行情、策略、交易、风控等服务
   - 核心层：事件引擎、消息总线
   - 数据层：时序数据库、Redis缓存

Q2: 为什么使用事件驱动架构？
A: - 解耦：各模块独立，通过事件通信
   - 异步：非阻塞处理，提高吞吐量
   - 可扩展：容易添加新的事件处理器
   - 可追溯：事件可以被记录和回放

Q3: 如何保证系统的高可用？
A: - 多副本部署关键服务
   - 消息队列持久化
   - 数据库主从复制
   - 熔断和降级机制
   - 健康检查和自动重启

Q4: 如何处理高并发行情数据？
A: - 异步处理（asyncio）
   - 批量处理和聚合
   - 内存缓存热点数据
   - 消息队列削峰

Q5: 回测系统如何设计？
A: - 事件驱动模式模拟真实环境
   - 支持多种交易成本模型
   - 完善的绩效分析
   - 防止未来函数

Q6: 风控系统有哪些层次？
A: - 事前：参数验证、资金检查、仓位限制
   - 事中：实时监控、止损触发、熔断
   - 事后：审计、分析、报告

Q7: 如何优化指标计算性能？
A: - 向量化计算（NumPy/Pandas）
   - 增量更新
   - 结果缓存
   - JIT编译（Numba）
   
Q8: 项目中遇到的挑战和解决方案？
A: 准备 2-3 个具体例子：
   - 低延迟优化
   - 高并发处理
   - 数据一致性保证
"""
print(interview_summary)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("项目架构学习完成！")
    print("下一步：运行 04_hands_on_practice.py 进行实战练习")
    print("=" * 70)
