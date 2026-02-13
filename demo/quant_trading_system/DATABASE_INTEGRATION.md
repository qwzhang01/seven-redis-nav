# TimescaleDB 集成和实时数据采集系统

## 概述

本项目已成功实现TimescaleDB数据库集成，支持实时数据采集和从数据库进行回测的功能。

## 已完成的功能

### 1. 数据库模块
- **数据库连接管理** (`database.py`)
  - DatabaseManager类管理TimescaleDB连接
  - 创建klines、ticks、depth_data等时序表
  - 支持超表(hypertable)和索引优化

- **数据存储服务** (`data_store.py`)
  - DataStore类实现批量数据存储
  - 支持K线、Tick、深度数据的存储
  - 提供数据查询接口用于回测

- **数据查询服务** (`data_query.py`)
  - DataQueryService类提供数据查询功能
  - 支持K线数据查询、历史数据获取
  - 为回测引擎提供数据库数据源

### 2. 实时数据采集
- **数据收集器增强** (`data_collector.py`)
  - BinanceDataCollector和OKXDataCollector支持数据存储
  - 实时将WebSocket数据存储到TimescaleDB
  - 支持Tick数据和深度数据的存储

- **实时采集服务** (`real_time_collector.py`)
  - RealTimeCollector类集成多个交易所数据采集
  - 统一管理数据存储和采集流程
  - 支持动态订阅/取消订阅交易对

### 3. 回测引擎增强
- **数据库回测支持** (`backtest_engine.py`)
  - 新增`run_from_database`方法
  - 支持从TimescaleDB获取历史数据进行回测
  - 保持原有回测功能兼容性

## 使用示例

### 1. 启动实时数据采集

```python
import asyncio
from quant_trading_system.services.market.real_time_collector import start_real_time_collection

async def main():
    # 配置要采集的交易对
    config = {
        "exchanges": {
            "binance": {
                "enabled": True,
                "market_type": "spot",
                "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
            },
            "okx": {
                "enabled": True,
                "symbols": ["BTC-USDT", "ETH-USDT", "BNB-USDT"]
            }
        }
    }
    
    # 启动实时采集服务
    collector = await start_real_time_collection(config)
    
    # 运行一段时间后停止
    await asyncio.sleep(60)
    
    # 停止采集服务
    await stop_real_time_collection()

asyncio.run(main())
```

### 2. 从数据库进行回测

```python
import asyncio
from datetime import datetime, timedelta
from quant_trading_system.services.backtest.backtest_engine import BacktestEngine, BacktestConfig
from quant_trading_system.models.market import TimeFrame
from quant_trading_system.services.strategy.base import Strategy

# 创建回测引擎（启用数据库模式）
backtest_config = BacktestConfig(
    initial_capital=100000.0,
    commission_rate=0.0004,
    slippage_rate=0.0001
)

engine = BacktestEngine(config=backtest_config, use_database=True)

# 创建策略
strategy = YourStrategy()

# 从数据库运行回测
result = await engine.run_from_database(
    strategy=strategy,
    symbols=["BTC/USDT", "ETH/USDT"],
    timeframes=[TimeFrame.M5, TimeFrame.M15],
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    limit=10000
)

print(f"总收益率: {result.total_return:.2%}")
print(f"年化收益率: {result.annual_return:.2%}")
print(f"最大回撤: {result.max_drawdown:.2%}")
```

### 3. 查询数据库数据

```python
from quant_trading_system.services.database.data_query import get_data_query_service

async def query_data():
    query_service = get_data_query_service()
    
    # 查询可用的交易对
    symbols = await query_service.get_available_symbols()
    print("可用交易对:", symbols)
    
    # 查询可用的时间框架
    timeframes = await query_service.get_available_timeframes()
    print("可用时间框架:", timeframes)
    
    # 查询数据时间范围
    time_range = await query_service.get_data_time_range(
        symbol="BTC/USDT", 
        timeframe=TimeFrame.M5
    )
    print("数据时间范围:", time_range)

asyncio.run(query_data())
```

## 数据库表结构

### kline_data (K线数据表)
- `id`: 主键
- `symbol`: 交易对符号
- `timeframe`: 时间框架
- `timestamp`: 时间戳
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `turnover`: 成交额

### tick_data (实时行情表)
- `id`: 主键
- `symbol`: 交易对符号
- `timestamp`: 时间戳
- `price`: 最新价格
- `volume`: 成交量
- `bid_price`: 买一价
- `ask_price`: 卖一价

### depth_data (深度数据表)
- `id`: 主键
- `symbol`: 交易对符号
- `timestamp`: 时间戳
- `bids`: 买盘深度
- `asks`: 卖盘深度

## 配置要求

### Docker Compose 配置
确保 `docker-compose.yml` 中包含TimescaleDB服务：

```yaml
services:
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: quant_trading
      POSTGRES_USER: quant_user
      POSTGRES_PASSWORD: quant_password
    ports:
      - "5432:5432"
    volumes:
      - timescaledb_data:/var/lib/postgresql/data
```

### 环境变量
```bash
DATABASE_URL=postgresql://quant_user:quant_password@localhost:5432/quant_trading
```

## 性能优化

- **超表(hypertable)**: 所有时序表都配置为超表，支持自动分区
- **索引优化**: 为常用查询字段创建索引
- **批量写入**: 数据存储服务支持批量写入，提高性能
- **连接池**: 数据库连接池管理，避免频繁连接开销

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查TimescaleDB服务是否启动
   - 验证环境变量配置

2. **数据查询为空**
   - 确认实时数据采集已启动
   - 检查交易对和时间范围是否正确

3. **回测性能慢**
   - 减少查询数据量（使用limit参数）
   - 优化策略逻辑

## 下一步计划

- [ ] 支持更多交易所数据源
- [ ] 添加数据质量监控
- [ ] 实现数据备份和恢复
- [ ] 优化查询性能
- [ ] 添加数据可视化界面
