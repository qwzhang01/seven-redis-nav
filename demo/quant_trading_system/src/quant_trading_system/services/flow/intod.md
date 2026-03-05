## Flow 跟单包架构说明

### 数据加载
1. **signal 大佬账户监听**：`flow_signal_stream.py` 使用 WebSocket 监听大佬账户数据，启动时拉取历史仓位信息，将仓位消息发送到消息总线
2. **signal_follow_orders 跟单数据**：`follow_trade_subscriber.py` 启动时扫描 `signal_follow_orders` 表加载活跃跟单配置到内存

### 订阅器
1. **SignalRecordSubscriber** (`signal_record_subscriber.py`)：信号记录落库，保存仓位信息到 `signal_trade_record`
2. **SignalWsSubscriber** (`signal_ws_subscriber.py`)：将最新仓位变化推送到前端订阅的 WebSocket
3. **FollowTradeSubscriber** (`follow_trade_subscriber.py`)：按跟单逻辑发起下单操作，保存订单状态变化

### 引擎
- **SignalStreamEngine** (`signal_stream_engine.py`)：统一管理信号流生命周期和所有订阅器注册

### 数据流
```
WebSocket(大佬账户) → FlowSignalStream → SignalEventBus
                                            ├── SignalRecordSubscriber  → DB(signal_trade_record)
                                            ├── SignalWsSubscriber      → WebSocket(前端)
                                            └── FollowTradeSubscriber   → 交易所下单 → DB(signal_follow_*)
```
