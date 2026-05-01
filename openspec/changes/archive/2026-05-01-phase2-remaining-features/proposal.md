## Why

Phase 2（v0.2）的核心目标已基本完成（SSH 隧道、TLS、监控命令流、慢查询、Pub/Sub、配置），但路线图中仍有三项关键能力尚未实现：**批量操作**、**Sentinel/Cluster 模式**、以及**监控 Tab 升级**（当前仅实现了 MONITOR 命令流，路线图要求的是 INFO 周期采样 + 4 指标卡 + ECharts 趋势图）。这三项是 v0.2 对 SRE/后端工程师场景的核心承诺，补齐后 Phase 2 才算真正交付完整。

## What Changes

- **新增** 批量操作能力：键面板支持 ⌘+点击多选、Shift 范围选、⌘A 全选；选中后可批量删除（含进度条 + 失败列表）、批量修改 TTL、批量复制键名
- **新增** Sentinel 模式连接：连接表单新增 Sentinel 模式选项，支持配置多个 Sentinel 节点地址 + master name；后端使用 redis-rs sentinel 接入
- **新增** Cluster 模式连接：连接表单新增 Cluster 模式选项，支持配置多个 Cluster 节点地址；后端使用 redis-rs cluster-async 接入
- **升级** 监控 Tab：在现有 MONITOR 命令流基础上，新增 INFO 周期采样模式（默认 2s），提供 4 指标卡（OPS/内存/客户端/命中率）+ ECharts 趋势图 + 服务器信息卡 + Keyspace 统计卡 + 客户端列表；两种模式（命令流 / 指标采样）通过 Tab 切换

## Capabilities

### New Capabilities

- `bulk-key-operations`: 键面板多选机制 + 批量删除/改 TTL/复制键名的前后端实现
- `sentinel-cluster-connection`: Sentinel 模式与 Cluster 模式的连接配置、后端接入、以及连接表单 UI 扩展
- `monitor-metrics-dashboard`: INFO 周期采样任务、4 指标卡、ECharts 趋势图、服务器信息/Keyspace/客户端列表的完整监控仪表盘

### Modified Capabilities

- `monitor-workspace`: 现有规格仅覆盖 MONITOR 命令流；新增 INFO 采样仪表盘模式，两种模式共存于同一工作区，通过子 Tab 切换
- `advanced-connection-config`: 现有规格已有 SSH/TLS 字段；新增 Sentinel 和 Cluster 模式的表单字段与验证规则

## Impact

- **前端**：`BrowserWorkspace` 键面板（`KeyList.vue`）需支持多选状态；新增 `BulkActionBar.vue`；`MonitorWorkspace.vue` 新增子 Tab 切换与 ECharts 图表组件；`ConnectionForm.vue` 新增 Sentinel/Cluster 模式字段
- **后端**：`commands/data.rs` 新增 `keys_bulk_delete` / `keys_bulk_ttl` 命令；`commands/connection.rs` 扩展 `ConnectionConfig` 支持 Sentinel/Cluster；`services/monitor.rs` 新增 INFO 采样任务与 `monitor:metrics` 事件；`services/connection_manager.rs` 支持 Sentinel/Cluster 连接建立
- **依赖**：redis-rs 已有 `sentinel` 和 `cluster-async` feature，需在 `Cargo.toml` 中启用；ECharts 已在依赖中，无需新增
- **IPC 新增**：`keys_bulk_delete(session, db, keys[])` / `keys_bulk_ttl(session, db, keys[], ttl)` / `monitor_metrics_start(session, interval_ms)` / `monitor_metrics_stop(task_id)`
