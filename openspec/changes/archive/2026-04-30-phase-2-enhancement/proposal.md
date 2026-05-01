## Why

Phase 1 MVP 已实现连接管理、键浏览、5 种数据类型查看/编辑、CLI 终端等核心功能，应用达到"能用"状态。但 Toolbar 中的 Monitor、Slowlog、Pub/Sub、Config 四个 Tab 仍为占位组件，点击后只显示空白页面。Phase 2 将这些占位功能全部实现为真实可用的工作区，同时引入虚拟滚动以支持大规模 Key 浏览场景，使产品从"能用"进化到"好用"（对应 v0.2）。

## What Changes

- **Pub/Sub 工作区**：订阅/取消订阅频道（支持 pattern），实时消息流展示（时间戳 + 频道 + 消息体），消息过滤/搜索，暂停/恢复接收，消息计数统计
- **Slowlog 工作区**：获取 Redis SLOWLOG GET 数据，表格展示（ID/时间/耗时/命令/客户端），按耗时排序，自动刷新/手动刷新，SLOWLOG RESET 清空，阈值配置提示
- **Monitor 工作区**：实时 MONITOR 命令流，命令着色（读/写/管理），暂停/恢复，关键字过滤，自动滚动到底部，性能保护（缓冲区上限）
- **Server Config 工作区**：CONFIG GET * 获取全部配置，分组展示（网络/内存/持久化/复制/安全等），搜索过滤，行内编辑 CONFIG SET，修改确认，INFO 概览面板（内存/连接数/命中率等）
- **虚拟滚动**：KeyPanel 键列表引入虚拟滚动，支持 10 万+ Key 流畅浏览，保持 SCAN 游标分页加载机制

## Capabilities

### New Capabilities

- `pubsub-workspace`: Pub/Sub 实时消息订阅与展示工作区，支持 SUBSCRIBE/PSUBSCRIBE/UNSUBSCRIBE，消息流实时渲染，过滤与暂停
- `slowlog-workspace`: 慢查询日志查看工作区，SLOWLOG GET/RESET/LEN 命令封装，表格展示与排序
- `monitor-workspace`: 实时命令监控工作区，MONITOR 命令流，命令分类着色，性能保护机制
- `server-config-workspace`: 服务器配置查看与编辑工作区，CONFIG GET/SET 封装，INFO 概览面板，分组展示
- `virtual-scroll`: 虚拟滚动能力，为 KeyPanel 提供大数据量列表渲染支持

### Modified Capabilities

- `app-shell`: Toolbar 中 Monitor/Slowlog/Pub/Sub/Config Tab 从占位组件替换为真实工作区组件
- `ipc-foundation`: 新增 IPC 命令——pubsub_subscribe / pubsub_unsubscribe / slowlog_get / slowlog_reset / monitor_start / monitor_stop / config_get_all / config_set；新增 Tauri Event——pubsub:message / monitor:command
- `key-browser`: KeyPanel 列表渲染从普通列表切换为虚拟滚动列表

## Impact

- **Rust 后端**：新增 services/pubsub.rs（订阅管理）、services/slowlog.rs（慢查询）、services/monitor.rs（MONITOR 流）、services/server_config.rs（配置管理）；commands/ 新增 4 个模块；需要处理 MONITOR/SUBSCRIBE 的长连接流式推送（Tauri Event）
- **前端**：4 个占位组件替换为完整工作区实现；新增 3 个 Pinia Store（pubsub/slowlog/monitor）；KeyPanel 引入虚拟滚动组件；新增前端依赖（虚拟滚动库，如 @tanstack/vue-virtual）
- **IPC 层**：新增 8 个 IPC 命令 + 2 个 Tauri Event 流式推送通道
- **性能**：Monitor 和 Pub/Sub 涉及高频消息推送，需要前端缓冲区管理和后端背压控制，避免内存溢出
- **连接资源**：MONITOR 和 SUBSCRIBE 需要独立连接（不能复用 Multiplexed 连接），ConnectionManager 需支持辅助连接分配
