### 信号逻辑
- signal 是信号定义的表
- signal_trade_record signal与signal_trade_record 是一对多，signal
  产生信号，即操作仓位的时候，把实时的订单记录到 signal_trade_record
- 通过交易所拉取账号的历史订单，将历史订单存到 signal_trade_record

### 跟单逻辑
- signal_follow_orders 是主控表（跟谁、多少钱、什么状态）
- signal_follow_trades 是交易流水表（每笔实际成交明细）
- signal_follow_positions 是持仓快照表（当前还持有什么）

### 逻辑
- signal 中的数据是手动维护的，分2类，一类是交易所的跟单信号，一类是订阅大佬的账户。请按照这个逻辑调整signal结构，订阅大佬的账户需要api
  授权信息，表结构里面要有对应的存储字段
- 系统启动的时候，扫描 signal 表，对表里面运行中的信号，启动 websocket 订阅账号仓位变化，预留配置项，手动拉取历史仓位订单，及账户信息的变化
- websocket 收到仓位操作后，发布2个事件，一个是在 signal_trade_record 里面存储，另一个是发到跟单引擎，触发跟单账号的订单操作
- 跟单引擎：系统启动的时候扫描 signal_follow_orders 表，将跟单数据load到内存中，订阅 上一步 所跟的信号的仓位变化
- 订单引擎：跟单引擎收到仓位变化后，将事件发布到订单引擎，由订单引擎处理具体的订单操作，包括仓位操作、仓位操作结果等
