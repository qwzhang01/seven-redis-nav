# 加密货币量化交易系统

> 基于 Spring Boot 2 + MyBatis-Plus + PostgreSQL + Ta4j + Spring AI 构建的生产级加密货币量化交易引擎

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        REST API Layer                          │
│  MarketController │ IndicatorController │ AnalysisController │ TradeController  │
├─────────────────────────────────────────────────────────────────┤
│                       Service Layer                            │
│  MarketSyncService │ IndicatorService │ AiAnalysisService │ TradeExecutionService │
│                     RiskControlService                        │
├─────────────────────────────────────────────────────────────────┤
│                    Exchange Facade Layer                        │
│  ExchangeClientFactory (门面工厂)                                │
│  ┌─────────────────┐  ┌─────────────────┐                     │
│  │ BinanceApiClient │  │   OkxApiClient   │  ←— 可扩展更多交易所  │
│  └─────────────────┘  └─────────────────┘                     │
├─────────────────────────────────────────────────────────────────┤
│                   Data Persistence Layer                        │
│  MyBatis-Plus + PostgreSQL                                      │
│  KlineMapper │ TickMapper │ DepthMapper │ IndicatorMapper │ ...  │
└─────────────────────────────────────────────────────────────────┘
```

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| JDK | Java | 1.8 |
| 框架 | Spring Boot | 2.7.18 |
| ORM | MyBatis-Plus | 3.5.5 |
| 数据库 | PostgreSQL | 14+ |
| 指标计算 | Ta4j | 0.15 |
| AI集成 | Spring WebFlux (OpenAI API) | - |
| HTTP客户端 | OkHttp | 4.12.0 |
| JSON | FastJSON2 | 2.0.47 |
| DB迁移 | Flyway | - |

## 核心功能

### 1. 交易所对接 (门面模式)
- **统一接口**: `ExchangeApiClient` 定义统一的行情和交易API
- **门面工厂**: `ExchangeClientFactory` 管理所有交易所客户端，调用方无需关心底层实现
- **已对接**: 币安(Binance)、欧易(OKX)
- **支持**: 现货(SPOT) + 合约(FUTURES)
- **数据**: KLine(K线)、Tick(逐笔行情)、Depth(深度)

### 2. 行情同步
- **定时同步**: K线(每分钟)、Tick(每5秒)、Depth(每10秒)
- **历史补全**: 首次启动自动补全配置天数的历史K线
- **增量更新**: 后续只同步新数据
- **多交易所并行**: 同时同步币安和OKX

### 3. 技术指标计算 (Ta4j)
- **MA/SMA**: 5/10/20/60日移动平均线
- **EMA**: 12/26指数移动平均
- **MACD**: DIF/DEA/柱状线
- **RSI**: 6/14/24周期相对强弱指数
- **布林带**: 上轨/中轨/下轨
- **KDJ**: K/D/J值
- **ATR**: 14周期平均真实范围
- **VWAP**: 成交量加权平均价
- **OBV**: 能量潮指标
- **扩展**: Williams %R, CCI, ADX, ROC, MA200等

### 4. AI分析 (大模型)
- 汇总多周期技术指标构建结构化Prompt
- 调用OpenAI兼容接口(GPT-4)
- 返回结构化投资建议(JSON)
- 支持自定义模型和API地址

### 5. 自动交易执行
- **开仓**: 多头/空头
- **平仓**: 全部平仓/部分平仓
- **风控**: 置信度阈值、持仓限制、日亏损限制
- **订单管理**: 完整的订单生命周期

### 6. 交易对配置
在 `application.yml` 中配置:
```yaml
trading:
  symbols:
    spot:
      - BTC/USDT
      - ETH/USDT
    futures:
      - BTC/USDT
      - ETH/USDT
  kline-intervals:
    - 1m
    - 5m
    - 15m
    - 1h
    - 4h
    - 1d
```

## 快速开始

### 1. 环境准备
- JDK 8+
- PostgreSQL 14+
- Maven 3.6+

### 2. 创建数据库
```sql
CREATE DATABASE crypto_trading;
```

### 3. 配置环境变量
```bash
export BINANCE_API_KEY=your-binance-api-key
export BINANCE_SECRET_KEY=your-binance-secret-key
export OKX_API_KEY=your-okx-api-key
export OKX_SECRET_KEY=your-okx-secret-key
export OKX_PASSPHRASE=your-okx-passphrase
export OPENAI_API_KEY=your-openai-api-key
export OPENAI_BASE_URL=https://api.openai.com  # 可替换为兼容API
```

### 4. 启动
```bash
mvn spring-boot:run
```

### 5. API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/market/klines` | GET | 获取实时K线 |
| `/api/market/klines/history` | GET | 获取历史K线 |
| `/api/market/ticker` | GET | 获取实时Tick |
| `/api/market/tickers` | GET | 批量获取Tick |
| `/api/market/depth` | GET | 获取深度数据 |
| `/api/indicator/latest` | GET | 获取最新技术指标 |
| `/api/indicator/calculate` | POST | 手动计算指标 |
| `/api/analysis/latest` | GET | 获取最新AI分析 |
| `/api/analysis/trigger` | POST | 手动触发AI分析 |
| `/api/analysis/unexecuted` | GET | 获取未执行的建议 |
| `/api/trade/execute/{id}` | POST | 执行AI建议 |
| `/api/trade/orders` | GET | 查询订单列表 |
| `/api/trade/positions` | GET | 查询持仓列表 |
| `/api/trade/positions/open` | GET | 查询开仓持仓 |

## 扩展交易所

实现 `ExchangeApiClient` 接口即可，Spring自动注册:

```java
@Component
public class NewExchangeApiClient implements ExchangeApiClient {
    @Override
    public ExchangeEnum getExchange() { return ExchangeEnum.NEW_EXCHANGE; }
    // ... 实现其他方法
}
```

## 注意事项

1. **自动交易默认关闭**: `order.auto-trade-enabled=false`，需手动开启
2. **API Key安全**: 建议通过环境变量注入，不要写在配置文件中
3. **风控参数**: 根据实际资金量调整止损止盈和仓位比例
4. **代理配置**: 需要翻墙访问交易所时配置proxy
5. **数据库表自动创建**: 通过Flyway自动执行迁移脚本
