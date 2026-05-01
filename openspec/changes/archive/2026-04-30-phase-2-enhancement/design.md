## Context

Phase 1 MVP 已建立完整的 Tauri + Vue 3 + Rust 架构，包含：
- **ConnectionManager**：基于 `redis::aio::MultiplexedConnection` 的连接池，支持多连接会话管理
- **IPC 层**：Tauri command + event 双向通信机制已就绪
- **前端框架**：Sidebar → KeyPanel → Workspace 三栏布局，Toolbar Tab 切换，Pinia 状态管理
- **4 个占位 Tab**：Monitor / Slowlog / Pub/Sub / Config 已有路由和占位组件，但无实际功能

关键约束：
- Redis 的 MONITOR 和 SUBSCRIBE 命令会独占连接（进入特殊模式后不能执行其他命令），不能复用现有的 MultiplexedConnection
- 高频消息推送（Monitor/PubSub）需要前后端协同的背压控制
- macOS 原生标题栏 + 无自定义 Titlebar 的窗口风格需保持

## Goals / Non-Goals

**Goals:**
- 实现 4 个占位工作区的完整功能（Pub/Sub、Slowlog、Monitor、Server Config）
- 为 KeyPanel 引入虚拟滚动，支持 10 万+ Key 流畅浏览
- 保持架构一致性：新功能遵循现有的 IPC command/event 模式
- 流式数据推送使用 Tauri Event 机制，前端通过 store 管理消息缓冲

**Non-Goals:**
- 不做 Redis Cluster 模式支持（留给 Phase 3）
- 不做 Redis Sentinel 支持
- 不做导出/报表功能
- 不做 Pub/Sub 消息持久化（仅内存中保留最近 N 条）
- 不做 Monitor 命令录制/回放

## Decisions

### D1: MONITOR/SUBSCRIBE 使用独立连接

**选择**：为 Monitor 和 Pub/Sub 各分配独立的 `Connection`（非 Multiplexed），生命周期与工作区 Tab 绑定。

**理由**：Redis 协议规定 MONITOR 和 SUBSCRIBE 进入后连接进入特殊模式，无法执行其他命令。MultiplexedConnection 不支持这类模式切换。

**替代方案**：
- 复用 MultiplexedConnection → 不可行，协议限制
- 每次切换 Tab 创建/销毁连接 → 延迟高，用户体验差

**实现**：ConnectionManager 新增 `acquire_dedicated_connection(conn_id)` 方法，返回独立 `Connection`，Tab 关闭时释放。

### D2: 流式消息推送使用 Tauri Event

**选择**：Monitor 和 Pub/Sub 的实时消息通过 `app_handle.emit()` 推送到前端，前端通过 `listen()` 接收。

**理由**：Tauri command 是请求-响应模式，不适合持续流式数据。Tauri Event 是天然的服务端推送通道，已在 Phase 1 的 `connection:state` 事件中验证过。

**替代方案**：
- WebSocket → Tauri 已提供 Event 机制，无需额外引入
- 轮询 → 延迟高，资源浪费

### D3: 前端消息缓冲区 + 环形队列

**选择**：前端 Store 使用固定大小环形队列（默认 Monitor 10000 条，PubSub 5000 条），超出后丢弃最旧消息。

**理由**：Monitor 在高负载 Redis 上可能每秒产生数千条消息，无限制存储会导致浏览器内存溢出。环形队列 O(1) 插入，内存可控。

**替代方案**：
- 无限制数组 + 手动清理 → 容易忘记清理，OOM 风险
- 分页加载历史 → 增加复杂度，Monitor 数据本身无持久化价值

### D4: 虚拟滚动选型 @tanstack/vue-virtual

**选择**：使用 `@tanstack/vue-virtual`（原 vue-virtual-scroller 的继任者）。

**理由**：
- 与 Vue 3 Composition API 完美集成
- 支持动态行高
- 社区活跃，TypeScript 原生支持
- 轻量（~5KB gzipped）

**替代方案**：
- `vue-virtual-scroller` → 维护不活跃，Vue 3 支持不完善
- 自研 → 开发成本高，边界情况多
- `recyclist` → 功能较少

### D5: Slowlog 和 Config 使用普通 IPC Command

**选择**：Slowlog 和 Config 使用标准的 Tauri command（请求-响应），不需要 Event 推送。

**理由**：这两个功能是"查询-展示"模式，不涉及持续流式数据。手动/定时刷新即可满足需求。

### D6: Server Config 分组策略

**选择**：前端硬编码 Redis 配置分组映射表（网络/内存/持久化/复制/安全/客户端/Lua/集群/慢查询/其他）。

**理由**：Redis CONFIG 参数相对稳定，硬编码分组比动态分析更可靠、更快。新版本新增参数归入"其他"组即可。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| Monitor 高频消息导致前端卡顿 | 环形队列限制条数 + requestAnimationFrame 批量渲染 + 暂停按钮 |
| 独立连接增加 Redis 连接数 | Tab 关闭时立即释放；同一时间最多 2 个独立连接（Monitor + PubSub） |
| Pub/Sub 订阅 pattern 过于宽泛导致消息洪水 | 前端提示警告 + 后端限流（每秒最多推送 1000 条，超出丢弃并计数） |
| @tanstack/vue-virtual 引入新依赖 | 库体积小（~5KB），无子依赖，风险可控 |
| CONFIG SET 误操作导致 Redis 异常 | 修改前二次确认弹窗 + 显示当前值与新值对比 |
