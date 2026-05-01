## Context

Seven Redis Nav 当前处于 Phase 3 末期（v0.3），已实现 6 个工作 Tab（Browser / CLI / Monitor / Slowlog / Pubsub / Config）。Phase 4 需要在现有架构基础上新增 2 个工作 Tab（Lua / Tools），并对 CLI Tab 进行多 Tab 改造，同时新增数据脱敏与快捷键自定义两个设置面板。

**当前架构约束：**
- 后端：Tauri 2 + Rust，services 层持有连接池（`ConnectionMultiplexer`），commands 层做参数校验与转发
- 前端：Vue 3 + Pinia，`workspace.ts` store 管理当前激活 Tab，`MainLayout.vue` 渲染 Toolbar 6 个 Tab 按钮
- IPC：按 Phase 分文件（`ipc/phase1.ts` ~ `ipc/phase3.ts`），新增 `ipc/phase4.ts`
- 数据持久化：SQLite（sqlx），现有表：`connections`、`cli_history`、`lua_scripts`（待建）

## Goals / Non-Goals

**Goals:**
- 新增 Lua 脚本编辑器（CodeMirror 6 + Lua mode），支持 EVAL/EVALSHA 执行与脚本历史
- 新增 Tools 工作区：大 Key 扫描（MEMORY USAGE 抽样）+ 过期 Key TTL 分布 + 健康检查报告
- CLI Tab 改造为多 Tab 架构，⌘T 新开、⌘W 关闭，每 Tab 独立会话与历史
- 数据导入导出：JSON 格式导出选中键/整个 DB，JSON 导入，只读解析 RDB 文件
- 数据脱敏规则：设置面板配置 key pattern → 掩码，Browser Workspace 实时生效
- 快捷键自定义：设置面板可视化绑定，持久化到 SQLite

**Non-Goals:**
- 不实现 RDB 文件写入（只读解析）
- 不实现 Cluster 跨节点数据导出（仅 Standalone/Sentinel 模式）
- 不实现 Lua 调试器（断点/单步），仅执行与结果查看
- 不实现健康报告的 PDF 导出（仅 Markdown 文本导出）
- 不实现数据脱敏的正则表达式模式（仅 glob 模式，如 `*token*`）

## Decisions

### D1：Toolbar 从 6 Tab 扩展到 8 Tab

**决策**：在现有 6 个 Tab 后追加 `Lua`（`ri-code-s-slash-line`）和 `Tools`（`ri-tools-line`）两个 Tab 按钮。

**理由**：
- 与现有 Tab 架构完全一致，`workspace.ts` 的 `activeTab` 枚举扩展两个值即可
- 不引入二级导航，保持工具栏扁平化，符合原型视觉规范
- 替代方案：将 Lua 和 Tools 合并为一个"高级工具"Tab，但会导致 Tab 内容过于复杂，不如分开清晰

### D2：多 Tab CLI 的会话管理策略

**决策**：每个 CLI Tab 持有独立的 Redis 连接（非共享 `ConnectionMultiplexer`），通过 `HashMap<TabId, CliSession>` 管理。

**理由**：
- CLI 可能执行阻塞命令（如 `SUBSCRIBE`、`BLPOP`），独立连接避免阻塞其他 Tab
- 与现有 `connection_manager.rs` 的设计一致（Pubsub 已采用独立连接）
- 替代方案：共享连接 + 命令队列，但实现复杂且无法支持阻塞命令
- **限制**：每个 CLI Tab 消耗一个 Redis 连接，建议最多允许 8 个 Tab（可配置）

### D3：大 Key 扫描的实现策略

**决策**：后台异步任务，SCAN 全量遍历 + `MEMORY USAGE key SAMPLES 0` 精确计算，通过 Tauri Event 推送进度（每 1000 个 key 推送一次）。

**理由**：
- `MEMORY USAGE` 是 Redis 4.0+ 的原生命令，精确且无需额外依赖
- 异步任务 + 进度推送，避免 UI 阻塞，用户可随时取消
- 替代方案：仅抽样（每 N 个 key 取一个），速度更快但结果不精确；对于 DBA 场景需要精确数据
- **性能预估**：100w key 实例，SCAN + MEMORY USAGE 约 30-60s（取决于 key 大小分布）

### D4：数据导出格式设计

**决策**：JSON 格式，结构为 `{ "version": "1.0", "connection": {...}, "exported_at": "...", "keys": [{ "key": "...", "type": "...", "ttl": -1, "value": {...} }] }`。

**理由**：
- 人类可读，便于调试和手动修改
- 与现有 `RedisValue` 模型直接对应，序列化简单
- 替代方案：CSV（不支持嵌套结构）、MessagePack（不可读）、RDB（写入复杂）
- **限制**：大 value（>1MB）导出时自动截断并标注 `"truncated": true`

### D5：健康检查报告的指标体系

**决策**：10 项核心指标，分为 4 个维度：

| 维度 | 指标 |
|------|------|
| 内存 | 内存使用率、内存碎片率、maxmemory 策略 |
| 性能 | 命中率、慢查询数量（近 1h）、OPS 峰值 |
| 连接 | 当前连接数/maxclients 比率、被拒绝连接数 |
| 持久化 | RDB 最近保存时间、AOF 状态 |

每项指标给出 `正常 / 警告 / 危险` 三级评分，汇总为总体健康分（0-100）。

### D6：数据脱敏的实现层级

**决策**：在前端 `BrowserWorkspace.vue` 的渲染层做脱敏，后端不参与。

**理由**：
- 脱敏是展示层行为，不影响实际数据，后端无需感知
- 前端 composable `useDataMasking()` 统一处理，所有 Viewer 组件复用
- 替代方案：后端脱敏（在 IPC 返回前替换），但会导致用户无法编辑原始值，且增加后端复杂度

### D7：RDB 文件解析策略

**决策**：使用 `rdb` crate（rdb-rs）进行只读解析，将解析结果转换为与 `key_get` 相同的 `KeyDetail` 结构，在前端以只读 Browser Workspace 展示。

**理由**：
- rdb-rs 是 Rust 生态中最成熟的 RDB 解析库，支持 RDB 版本 1-10
- 只读解析，不需要写入能力，风险低
- **限制**：不支持 RDB 版本 11+（Redis 7.4+），遇到不支持版本给出明确错误提示

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 大 Key 扫描对 Redis 服务器造成压力 | 扫描任务限速（每批 SCAN count=100，批间 sleep 10ms）；提供"低影响模式"开关 |
| 多 Tab CLI 连接数过多 | 硬限最多 8 个 Tab；Tab 关闭时立即释放连接；空闲 Tab 超时自动关闭（可配置） |
| RDB 文件解析内存占用 | 流式解析，不一次性加载全部数据；超过 500MB 的 RDB 文件给出警告 |
| JSON 导出大 DB 时文件过大 | 导出前显示预估大小；超过 100MB 建议分批导出；单个 value 超过 1MB 自动截断 |
| CodeMirror 6 Lua mode 包体积 | 已在 Phase 3 引入 CodeMirror 6，Lua mode 增量约 20KB（gzip），可接受 |
| 快捷键冲突检测 | 自定义绑定时实时检测与现有绑定的冲突，给出警告但允许覆盖 |

## Migration Plan

1. **数据库迁移**：新增 3 张表（`lua_scripts`、`shortcut_bindings`、`masking_rules`），通过 sqlx migrate 自动执行，向后兼容
2. **Toolbar 扩展**：`workspace.ts` 的 `WorkspaceTab` 枚举新增 `lua` 和 `tools` 两个值，`MainLayout.vue` 追加两个 Tab 按钮，不影响现有 6 个 Tab
3. **CLI 多 Tab 改造**：`terminal.ts` store 从单状态改为 `Map<TabId, CliTabState>`，现有单 Tab 行为作为 `tabs[0]` 保留，向后兼容
4. **回滚策略**：所有新功能通过独立的 IPC 命令和 Store 模块实现，不修改现有命令签名，可安全回滚

## Open Questions

- Q1：健康检查报告是否需要支持定时自动生成（如每天 00:00 自动生成并通知）？→ Phase 4 暂不实现，留 Phase 5
- Q2：数据导入时是否支持"覆盖已存在的 key"选项？→ 默认跳过，提供"强制覆盖"开关
- Q3：Lua 脚本历史是否需要支持云同步？→ Phase 4 仅本地 SQLite，云同步留企业版
- Q4：Tools Tab 中的大 Key 扫描和健康检查是否应该合并为一个"诊断"Tab？→ 当前方案合并在 Tools Tab 中，通过子 Tab 区分，待 UI 原型确认
