## Context

Phase 2（v0.2）已完成 SSH 隧道、TLS、MONITOR 命令流、慢查询、Pub/Sub、配置 Tab 等核心功能。当前遗留三项：

1. **批量操作**：键面板目前仅支持单键操作，缺少多选机制与批量命令
2. **Sentinel/Cluster 模式**：`ConnectionConfig` 仅支持 Standalone；redis-rs 的 `sentinel` 和 `cluster-async` feature 已在依赖树中但未启用
3. **监控仪表盘**：`MonitorWorkspace` 当前实现的是 MONITOR 命令流（实时命令追踪），路线图要求的是 INFO 周期采样 + 4 指标卡 + ECharts 趋势图（性能仪表盘）；两者定位不同，应共存

约束：
- 不引入新的前端依赖（ECharts 已有）
- 不破坏现有 SSH/TLS 连接流程
- 批量操作需在前端维护选中状态，不依赖后端 session 状态

## Goals / Non-Goals

**Goals:**
- 键面板支持 ⌘+点击、Shift 范围选、⌘A 全选，选中后可批量删除/改 TTL/复制键名
- 批量删除支持进度反馈（逐批次执行，每批 100 个）和失败列表
- `ConnectionConfig` 扩展 Sentinel 和 Cluster 模式字段；后端 `connection_manager` 按模式建立对应连接
- 监控 Tab 新增"指标仪表盘"子 Tab：INFO 周期采样（默认 2s）、4 指标卡、ECharts 趋势图（40 点滑动窗口）、服务器信息卡、Keyspace 统计卡、客户端列表
- 现有 MONITOR 命令流保留为"命令追踪"子 Tab

**Non-Goals:**
- Cluster 跨节点 SCAN 归并（留 Phase 3）
- Sentinel 故障转移事件推送（留 Phase 3）
- 批量操作的撤销/重做（留 Phase 4）
- 监控历史数据持久化（留 Phase 4）

## Decisions

### 决策 1：批量操作的选中状态放在 `useKeyBrowserStore`

**选择**：在 Pinia `keyBrowserStore` 中维护 `selectedKeys: Set<string>`，键面板组件通过 store 读写选中状态。

**理由**：选中状态需要跨组件共享（键列表 + 批量操作栏），放 store 比 props/emit 链路更清晰。

**备选**：在 `KeyList.vue` 内部维护 → 批量操作栏无法直接访问，需 emit 冒泡，层级过深。

### 决策 2：批量删除分批执行，每批 100 个

**选择**：前端将选中键分批（每批 100 个），依次调用 `keys_bulk_delete`，后端单次调用 `DEL key1 key2 ...`（redis-rs 支持多参数 DEL）。

**理由**：单次 DEL 1000 个键可能阻塞 Redis 主线程（尤其大 Key）；分批可在前端展示进度，并在部分失败时给出失败列表而不是全量回滚。

**备选**：全量一次 DEL → 无进度反馈，大批量时 Redis 阻塞风险高。

### 决策 3：Sentinel/Cluster 通过 `ConnectionMode` 枚举扩展 `ConnectionConfig`

**选择**：在 `ConnectionConfig` 中新增 `mode: ConnectionMode`（`Standalone | Sentinel | Cluster`）和对应的可选字段（`sentinel_nodes`, `master_name`, `cluster_nodes`）。`connection_manager` 按 mode 分支建立连接。

**理由**：枚举扩展比新增独立结构体更易序列化/反序列化，前端表单也可按 mode 动态渲染字段。

**备选**：三种模式各自独立结构体 → 前端需要 union type，IPC 序列化复杂。

### 决策 4：监控 Tab 用子 Tab 区分"命令追踪"与"指标仪表盘"

**选择**：`MonitorWorkspace.vue` 顶部增加两个子 Tab：`命令追踪`（现有 MONITOR 流）和 `指标仪表盘`（新增 INFO 采样）。两者共用同一个工作区容器，互不干扰。

**理由**：两种模式定位不同（调试 vs 运维监控），合并为一个 Tab 会导致 UI 混乱；独立为两个顶层 Tab 又会占用工具栏位置（工具栏已有 6 个 Tab）。

**备选**：仅保留指标仪表盘，移除命令追踪 → 破坏已有功能，且命令追踪对调试场景有独立价值。

### 决策 5：ECharts 趋势图使用前端滑动窗口，不持久化

**选择**：`useMonitorStore` 维护每个指标的最近 40 个采样点（滑动数组），ECharts 直接绑定该数组。切换 Tab 时暂停采样任务（`monitor_metrics_stop`），回来时重新启动。

**理由**：无需后端存储，内存占用可控（40 点 × 4 指标 × 8 字节 ≈ 1.3KB）；与路线图"切走 Tab 暂停采样"要求一致。

## Risks / Trade-offs

- **[风险] Cluster 模式下 SCAN 只扫描单节点** → 当前 Phase 仅支持连接建立和基础命令；跨节点 SCAN 归并标记为 Phase 3 TODO，UI 上给出提示"Cluster 模式下键浏览仅显示当前节点数据"
- **[风险] Sentinel 主节点切换后连接失效** → redis-rs sentinel 客户端会自动重新发现主节点；但切换期间约 1-3s 命令会失败，前端需处理 `ConnectionLost` 错误并触发重连逻辑（已有重连机制）
- **[风险] 批量删除大量大 Key 时 Redis 阻塞** → 每批 100 个 + 批次间 10ms 延迟，可缓解但不能完全消除；UI 上提示"批量删除可能短暂影响 Redis 性能"
- **[风险] INFO 采样与 MONITOR 命令流同时运行时连接数翻倍** → 两者使用独立连接；用户不太可能同时开启两个子 Tab，且切换子 Tab 时会停止另一个的后台任务
