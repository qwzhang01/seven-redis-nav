
## 代码结构诊断分析

先画个当前的结构图：

```
quant_trading_system/
├── api/                          # API层（HTTP入口）
│   ├── main.py                   # 503行的God File，塞了整个应用生命周期
│   ├── deps.py                   # 依赖注入 + 全局state引用
│   ├── middlewares.py
│   ├── c/__init__.py             # C端路由聚合
│   ├── m/__init__.py             # Admin端路由聚合
│   ├── signal/
│   │   ├── api/                  # 路由层
│   │   └── services/             # ⚠️ 业务service放在api下
│   ├── strategies/
│   │   ├── api/
│   │   ├── services/__init__.py  # ⚠️ 484行全塞在__init__.py里
│   │   └── repositories/__init__.py  # ⚠️ 316行全塞在__init__.py里
│   ├── users/
│   │   ├── api/
│   │   ├── models/               # ⚠️ 有的模块自带models
│   │   ├── services/
│   │   └── repositories/
│   ├── trading/api/              # ⚠️ 没有service层，直接裸调
│   ├── backtest/api/             # ⚠️ 没有service层
│   ├── market/api/               # ⚠️ 没有service层
│   ├── stats/api/
│   ├── audit_logs/api/
│   ├── leaderboard/api/
│   ├── system/api/
│   └── websocket/
├── core/                         # 核心工具
│   ├── config.py / container.py / events.py / enums.py ...
├── models/                       # 全局ORM模型
│   ├── database.py               # ⚠️ 619行，20+个Model全塞一个文件
│   ├── strategy.py / market.py / user.py ...
├── services/                     # 后台引擎服务层
│   ├── market/ / exchange/ / strategy/ / trading/ / ...
├── strategies/                   # 策略实现
```

---

## 核心问题（不夸，说实话）

### 🔴 问题一：分层混乱，api 层和业务层的边界稀碎

这是最大的问题。项目里存在**两套互相对立的分层逻辑**：

- **api 模块自带** service/repository（如 `api/signal/services/`、`api/strategies/services/`、`api/strategies/repositories/`、`api/users/services/`）
- **顶层 services 目录**里还有一套独立的引擎服务（如 `services/market/`、`services/trading/`、`services/strategy/`）

这导致：你想找"信号相关的业务逻辑"，得去 `api/signal/services/signal_service.py`（848行）；想找"策略引擎逻辑"，得去 `services/strategy/strategy_engine.py`。**同一个领域的逻辑分散在两个完全不同的位置**，而且命名上无法区分。

### 🔴 问题二：`__init__.py` 被当成正经代码文件用

- `api/strategies/services/__init__.py` — **484行**，三个完整的 Service 类全塞在里面
- `api/strategies/repositories/__init__.py` — **316行**，五个 Repository 类全塞在里面

`__init__.py` 是用来做包初始化和导出的，不是放业务代码的地方。这样做导致 IDE 跳转混乱，代码搜索困难，职责不清。

### 🔴 问题三：models/database.py — 619行的上帝模型文件

20多个 ORM 模型全部堆在一个文件里：`User`、`Exchange`、`Signal`、`SignalFollowOrder`、`SignalPosition`、`SignalTradeRecord`、`AuditLog`、`RiskAlert`... 而且项目里又有单独的 `models/strategy.py`、`models/market.py`、`models/user.py`，说明你**本来想按领域拆分模型，但没有贯彻到底**。Signal 相关的 10 几个模型全部留在了 `database.py` 里。

### 🟡 问题四：API模块的内部结构不统一

| 模块 | 有 service？ | 有 repository？ | 有 models？ |
|------|------------|----------------|------------|
| users | ✅ | ✅ | ✅ |
| strategies | ✅ | ✅ | ❌ |
| signal | ✅ | ❌ | ❌ |
| trading | ❌ | ❌ | ❌ |
| backtest | ❌ | ❌ | ❌ |
| market | ❌ | ❌ | ❌ |

有的模块走三层架构（api → service → repository），有的直接在路由里裸写业务逻辑。统一性约等于零。

### 🟡 问题五：main.py 太胖（503行）

[main.py](/Users/avinzhang/git/seven-quant/demo/quant_trading_system/src/quant_trading_system/api/main.py) 里塞了：
- 启动/关闭生命周期管理（7个函数）
- 中间件注册
- 异常处理
- 路由注册
- OpenAPI 自定义配置
- 开发服务器入口

这些本该分成独立模块。

### 🟡 问题六：signal_service.py 里直接写大量SQL查询

[signal_service.py](/Users/avinzhang/git/seven-quant/demo/quant_trading_system/src/quant_trading_system/api/signal/services/signal_service.py) 有 848 行，Service 层直接操作 `db.query(...).filter(...).join(...)`。策略模块好歹有个 Repository 层做了隔离，Signal 模块完全没有。Service 和 DAO 的职责混在一起。

### 🟡 问题七：手动 `_to_dict` 满天飞

到处都是手工写的 `_to_dict` / `_to_detail_dict` 方法把 ORM 对象转成字典。这种事应该用 Pydantic Schema 或 dataclass 来做序列化，而不是每个 Service 都自己手搓一套。

---

## 建议的目标结构

```
quant_trading_system/
├── api/                           # 纯HTTP入口层（只做请求解析、参数校验、调用Service、返回响应）
│   ├── app.py                     # 精简的 FastAPI app 创建（< 50行）
│   ├── lifespan.py                # 生命周期管理（从main.py拆出来）
│   ├── middlewares.py
│   ├── deps.py
│   ├── routes/
│   │   ├── c/                     # C端路由
│   │   └── m/                     # Admin端路由
│   └── schemas/                   # Pydantic 请求/响应 Schema（统一管理）
│       ├── signal_schemas.py
│       ├── strategy_schemas.py
│       └── user_schemas.py
│
├── core/                          # 不变，保持当前结构
│
├── models/                        # ORM模型，按领域拆分
│   ├── base.py                    # Base = declarative_base()
│   ├── user.py                    # User + UserExchangeAPI
│   ├── exchange.py
│   ├── signal.py                  # Signal + SignalPosition + SignalTradeRecord + ...
│   ├── follow.py                  # SignalFollowOrder + SignalFollowPosition + ...
│   ├── strategy.py                # PresetStrategy + UserStrategy + Simulation*
│   ├── market.py
│   ├── audit.py                   # AuditLog + RiskAlert
│   └── leaderboard.py
│
├── repositories/                  # 统一的数据访问层（从api子模块抽出来）
│   ├── signal_repository.py
│   ├── strategy_repository.py
│   ├── user_repository.py
│   └── follow_repository.py
│
├── services/                      # 统一的业务逻辑层（合并api下的service和顶层services）
│   ├── signal_service.py          # 原 api/signal/services/signal_service.py
│   ├── follow_service.py
│   ├── strategy_service.py
│   ├── user_service.py
│   ├── market/                    # 复杂引擎模块保留子目录
│   ├── exchange/
│   ├── trading/
│   └── ...
│
├── strategies/                    # 不变
└── cli.py
```

### 核心改动思路

1. **业务逻辑统一放 services/**，api 层只负责 HTTP 协议适配（参数校验、异常转换、返回格式）
2. **数据访问统一放 repositories/**（或者在各 service 内用 repository pattern 但代码放在统一位置）
3. **database.py 按领域拆分** — Signal 体系 10+ 个模型 → `models/signal.py` + `models/follow.py`
4. **杀死 `__init__.py` 滥用** — 正经代码放正经文件里
5. **引入 Pydantic Schema** 替代手写 `_to_dict`
6. **main.py 瘦身** — 生命周期代码拆到 `lifespan.py`

---

### 改

已经模块和代码的改动思路：

1. **第一步**：先把 `models/database.py` 按领域拆分（纯文件搬迁，风险最低）
2. **第二步**：把 `api/*/services/` 和 `api/*/repositories/` 的代码挪到顶层 `services/` 和 `repositories/`
3. **第三步**：`main.py` 瘦身，拆出 `lifespan.py`
4. **第四步**：统一各 API 模块的分层风格
5. **最后**：逐步引入 Pydantic Schema 替代 `_to_dict`

### 重构思路：

#### 系统核心事件如下：
- 行情
  - kline
  - depth
  - tick data
- 账户
- 订单

#### 驱动交易的核心逻辑
- 策略
  - 回测
  - 模拟交易
  - 实盘交易
- 信号
  - 通过接口拉取的交易所跟单
  - 通过订阅某些账号的仓位操作

#### 所以
- 因为所有逻辑都是基于事件驱动，将事件引擎独立出来，不管是全局还是某些业务的事件引擎，全部独立出来单独放一个模块
    - 按照目前看，有全局的事件引擎
    - 有信号的事件引擎
    - 等等
- 所有的交互都是通过交易所操作，把交易所也单独放一个模块，最好方便以后加交易所
- 把策略引擎相关的放一个独立的模块
- 把信号引擎相关的放一个独立的模块
- 把订单引擎也独立放一个模块
- 所有的逻辑基于事件机制，发生了一件事，通过事件引擎传递出去，由关系这个事件的订阅器订阅，订阅器订阅后具体逻辑在Service
  模块实现，然后把全局的分层进行合理化的分层和整理
- 所有需要对接交易所，都要提供 mock 功能,本地无法连接交易所难以调试，所有的 mock 都放一个独立的包，通过配置可以自由切换是否使用mock 
