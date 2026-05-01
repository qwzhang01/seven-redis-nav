## 1. 批量操作 — 后端 IPC

- [x] 1.1 在 `src-tauri/Cargo.toml` 确认 redis-rs 的 `cluster-async` 和 `sentinel` feature 已启用
- [x] 1.2 在 `src-tauri/src/commands/data.rs` 新增 `keys_bulk_delete(session_id, db, keys: Vec<String>) -> Result<BulkResult>` 命令，内部分批（每批 100 个）调用 `DEL`，返回成功数和失败键列表
- [x] 1.3 在 `src-tauri/src/commands/data.rs` 新增 `keys_bulk_ttl(session_id, db, keys: Vec<String>, ttl_secs: Option<i64>) -> Result<BulkResult>` 命令，`ttl_secs = None` 时执行 `PERSIST`，否则执行 `EXPIRE`
- [x] 1.4 在 `src/ipc/data.ts` 添加 `keysBulkDelete` 和 `keysBulkTtl` 的 TypeScript 封装函数及对应类型定义 `BulkResult { success: number; failed: string[] }`
- [x] 1.5 在 `src-tauri/src/lib.rs` 的 `invoke_handler` 中注册新命令

## 2. 批量操作 — 前端多选机制

- [x] 2.1 在 `src/stores/keyBrowser.ts` 的 `useKeyBrowserStore` 中新增 `selectedKeys: Set<string>` 状态及 `toggleSelect(key)` / `rangeSelect(from, to)` / `selectAll()` / `clearSelection()` actions
- [x] 2.2 修改 `src/components/keypanel/KeyList.vue`（或对应键列表组件），支持 ⌘+点击调用 `toggleSelect`、Shift+点击调用 `rangeSelect`、⌘A 调用 `selectAll`；选中项显示蓝色左边框 + 浅蓝背景
- [x] 2.3 新建 `src/components/keypanel/BulkActionBar.vue`：当 `selectedKeys.size > 0` 时显示在键面板底部，展示选中数量 + "删除" / "设置 TTL" / "移除 TTL" / "复制键名" 四个操作按钮
- [x] 2.4 在 `BulkActionBar.vue` 中实现"删除"操作：弹确认对话框（≥100 个时要求输入 "DELETE"），确认后调用 `keysBulkDelete`，显示进度条（已处理批次 / 总批次），完成后展示成功/失败摘要 Toast
- [x] 2.5 在 `BulkActionBar.vue` 中实现"设置 TTL"操作：弹 TTL 输入对话框，确认后调用 `keysBulkTtl`，完成后展示摘要 Toast
- [x] 2.6 在 `BulkActionBar.vue` 中实现"移除 TTL"操作：直接调用 `keysBulkTtl(keys, null)`，完成后展示摘要 Toast
- [x] 2.7 在 `BulkActionBar.vue` 中实现"复制键名"操作：将 `selectedKeys` 转为换行分隔字符串写入剪贴板，Toast 提示"已复制 N 个键名"
- [x] 2.8 批量操作完成后调用 `clearSelection()` 并触发键列表刷新

## 3. Sentinel/Cluster — 后端连接扩展

- [x] 3.1 在 `src-tauri/src/models/` 中扩展 `ConnectionConfig`：新增 `mode: ConnectionMode` 枚举（`Standalone | Sentinel | Cluster`）、`sentinel_nodes: Option<Vec<String>>`、`master_name: Option<String>`、`cluster_nodes: Option<Vec<String>>`
- [x] 3.2 在 `src-tauri/src/services/connection_manager.rs` 中按 `mode` 分支建立连接：`Sentinel` 使用 `redis::sentinel::SentinelClient`，`Cluster` 使用 `redis::cluster_async::ClusterClient`，`Standalone` 保持现有逻辑
- [x] 3.3 在 `src-tauri/src/commands/connection.rs` 的 `connection_test` 命令中支持 Sentinel/Cluster 模式：Sentinel 模式解析 master 地址后 PING，Cluster 模式 PING 所有 shard master 并返回节点数
- [x] 3.4 更新 `src/types/connection.ts` 中的 `ConnectionConfig` TypeScript 类型，新增 `mode`、`sentinelNodes`、`masterName`、`clusterNodes` 字段

## 4. Sentinel/Cluster — 前端表单扩展

- [x] 4.1 在 `src/components/dialogs/ConnectionForm.vue` 中新增"连接模式"选择器（Standalone / SSH 隧道 / TLS / Sentinel / Cluster），替换原有的连接类型选择逻辑
- [x] 4.2 新增 Sentinel 配置分组：Sentinel 节点列表（动态增减 host:port 输入行，至少一个）+ master name 必填输入框
- [x] 4.3 新增 Cluster 配置分组：Cluster 种子节点列表（动态增减 host:port 输入行，至少一个）
- [x] 4.4 在 Cluster 模式连接成功后，键面板顶部显示信息横幅："Cluster 模式：键浏览仅显示当前节点数据，跨节点 SCAN 将在后续版本支持"

## 5. 监控仪表盘 — 后端 INFO 采样

- [x] 5.1 在 `src-tauri/src/commands/monitor.rs` 新增 `monitor_metrics_start(session_id, interval_ms: u64) -> Result<TaskId>` 命令：启动周期采样任务，每次采样执行 `INFO all` + `CLIENT LIST`，解析后通过 `monitor:metrics` 事件推送 `MetricsSnapshot`
- [x] 5.2 在 `src-tauri/src/commands/monitor.rs` 新增 `monitor_metrics_stop(task_id: TaskId) -> Result<()>` 命令：停止采样任务
- [x] 5.3 在 `src-tauri/src/models/` 中定义 `MetricsSnapshot` 结构体：`ops_per_sec: f64`、`used_memory_bytes: u64`、`connected_clients: u64`、`keyspace_hits: u64`、`keyspace_misses: u64`、`server_info: ServerInfo`、`keyspace: Vec<DbKeyspace>`、`clients: Vec<ClientEntry>`
- [x] 5.4 在 `src/ipc/monitor.ts` 添加 `monitorMetricsStart` / `monitorMetricsStop` 封装函数及 `MetricsSnapshot` TypeScript 类型
- [x] 5.5 在 `src-tauri/src/lib.rs` 的 `invoke_handler` 中注册新命令

## 6. 监控仪表盘 — 前端 UI

- [x] 6.1 在 `src/stores/monitor.ts` 的 `useMonitorStore` 中新增 `metricsTaskId`、`metricsHistory: MetricsPoint[]`（滑动窗口最多 40 点）、`latestMetrics: MetricsSnapshot | null` 状态，以及 `startMetrics()` / `stopMetrics()` actions（监听 `monitor:metrics` 事件）
- [x] 6.2 修改 `src/components/workspaces/monitor/MonitorWorkspace.vue`：顶部新增两个子 Tab（"命令追踪" / "指标仪表盘"），切换时分别启停对应的后台任务
- [x] 6.3 新建 `src/components/workspaces/monitor/MetricCard.vue`：接收 `label`、`value`、`unit`、`color` props，渲染指标卡（数值 + 单位 + 标签 + 色块）
- [x] 6.4 新建 `src/components/workspaces/monitor/TrendChart.vue`：接收 `data: number[]`、`color: string` props，使用 ECharts 渲染面积趋势图（渐变填充 + 末端圆点），数据变化时调用 `chart.setOption` 增量更新
- [x] 6.5 新建 `src/components/workspaces/monitor/MetricsDashboard.vue`：组合 4 个 `MetricCard` + 4 个 `TrendChart`（2×2 网格）+ `ServerInfoCard` + `KeyspaceCard` + `ClientListCard`
- [x] 6.6 新建 `src/components/workspaces/monitor/ServerInfoCard.vue`：展示 Redis 版本、OS、PID、端口、Uptime、角色（绿色/橙色徽章）、从节点数、AOF 状态、最近 RDB 时间
- [x] 6.7 新建 `src/components/workspaces/monitor/KeyspaceCard.vue`：展示每个 DB 的总键数、带 TTL 键数、永久键数（来自 `INFO keyspace` 解析）
- [x] 6.8 新建 `src/components/workspaces/monitor/ClientListCard.vue`：展示最多 6 条客户端记录（地址 / 最近命令 / 连接时长），数据来自 `MetricsSnapshot.clients`
- [x] 6.9 在 `MetricsDashboard.vue` 的 `onMounted` / `onUnmounted` 生命周期中调用 `startMetrics()` / `stopMetrics()`；在 `onActivated` / `onDeactivated`（`<KeepAlive>` 场景）中同样处理

## 7. 验收测试

- [ ] 7.1 批量选中 200 个键 → 批量删除 → 验证进度条显示、完成后键列表刷新、选中状态清空
- [ ] 7.2 批量选中 50 个键 → 设置 TTL 为 3600s → 验证所有键 TTL 更新；再批量移除 TTL → 验证 PERSIST 生效
- [ ] 7.3 配置 Sentinel 连接（本地测试用 redis-sentinel）→ 测试连接成功 → 浏览键数据正常
- [ ] 7.4 配置 Cluster 连接（本地测试用 redis-cluster）→ 测试连接成功 → 键面板显示 Cluster 模式横幅
- [ ] 7.5 打开监控"指标仪表盘"→ 验证 4 个指标卡数值更新、ECharts 趋势图滚动、服务器信息卡内容正确
- [ ] 7.6 切换到"命令追踪"子 Tab → 验证 INFO 采样任务停止（无 `monitor:metrics` 事件）；切回"指标仪表盘"→ 采样恢复
- [ ] 7.7 监控仪表盘持续运行 10 分钟 → 验证内存无明显增长（趋势图滑动窗口正确丢弃旧数据）
