## Why

Phase 3 完成了 Pub/Sub、Config、扩展类型查看器、JSON 智能识别与二进制三视图，Seven Redis Nav 已具备日常运维所需的核心能力。但面向 DBA 和架构师的高级工具（Lua 脚本执行、数据导入导出、大 Key 扫描、健康检查报告、多 Tab CLI）仍是空白，这些功能是主流竞品（RedisInsight、Another Redis Desktop Manager）的标配，也是用户从"能用"升级到"好用"的关键门槛。Phase 4 补齐这些高级工具，使产品具备 v0.4 对外发布的完整度。

## What Changes

- **新增** Lua 脚本编辑器工作区：CodeMirror 6 + Lua 语法高亮，支持 EVAL/EVALSHA 执行、KEYS+ARGV 参数表单、脚本历史管理
- **新增** 数据导入导出：选中键集合或整个 DB 导出为 JSON；从 JSON 文件导入键值对；只读解析 RDB 文件（rdb-rs）
- **新增** 大 Key 扫描器：后台异步任务，SCAN + MEMORY USAGE 抽样，生成 Top 100 大 Key 报告，支持按类型/大小排序与导出
- **新增** 过期 Key 分析：TTL 分布直方图，识别即将过期（< 1h / < 24h）与永久 Key 的比例
- **新增** 健康检查报告：综合 INFO / SLOWLOG / Keyspace / Client 数据，生成可导出的 Markdown 健康报告（10 项核心指标）
- **新增** 多 Tab CLI：⌘T 新开 CLI 标签页，标签页可关闭（⌘W）、可拖拽排序，每个 Tab 独立连接与历史
- **新增** 数据脱敏规则：设置面板配置 key 模式 → 掩码规则，Browser Workspace 实时生效
- **新增** 快捷键自定义：设置面板可视化绑定，支持重置为默认

## Capabilities

### New Capabilities

- `lua-script-editor`: Lua 脚本编辑、执行（EVAL/EVALSHA）、历史管理，含 KEYS+ARGV 参数表单
- `data-import-export`: 键集合/DB 级别的 JSON 导出与导入，只读 RDB 文件解析
- `key-analyzer`: 大 Key 扫描（MEMORY USAGE 抽样）+ 过期 Key TTL 分布分析
- `health-check-report`: 综合健康检查，生成含 10 项指标的 Markdown 报告并支持导出
- `multi-tab-cli`: CLI 工作区多标签页管理（新建/关闭/拖拽/独立历史）
- `data-masking`: 数据脱敏规则配置与 Browser Workspace 实时掩码渲染
- `shortcut-customization`: 快捷键自定义绑定与重置（扩展现有 shortcut-system spec）

### Modified Capabilities

- `cli-terminal`: 扩展为多 Tab 架构，单 Tab 行为不变，新增 Tab 管理 IPC 与 Store 层
- `shortcut-system`: 新增自定义绑定持久化（SQLite）与设置面板 UI

## Impact

**后端（Rust）**
- 新增 `commands/lua.rs`：`lua_eval`、`lua_evalsha`、`lua_script_load`、`lua_script_exists`
- 新增 `commands/tools.rs`（扩展）：`key_scan_memory`（大 Key 扫描任务）、`key_ttl_distribution`、`health_check_generate`
- 新增 `commands/import_export.rs`：`export_keys_json`、`import_keys_json`、`rdb_parse_file`
- 新增 `services/key_analyzer.rs`：后台异步扫描任务，Tauri Event 推送进度
- 新增 `services/health_check.rs`：聚合 INFO / SLOWLOG / Keyspace 数据，生成报告结构
- 扩展 `services/terminal.rs`：多 Tab 会话管理（HashMap<TabId, CliSession>）
- 扩展 `utils/config_store.rs`：新增 lua_history、shortcut_bindings、masking_rules 表
- 新增 `models/` 中 LuaScript、KeyMemoryStat、TtlDistribution、HealthReport 数据模型

**前端（Vue 3）**
- 新增 `src/components/workspaces/lua/LuaWorkspace.vue`（新增第 7 个 Tab）
- 新增 `src/components/workspaces/tools/ToolsWorkspace.vue`（大 Key 扫描 + 过期分析 + 健康检查，第 8 个 Tab）
- 扩展 `src/components/workspaces/cli/`：多 Tab 容器 + CliTabBar + CliTabPanel
- 新增 `src/components/settings/`：DataMaskingPanel + ShortcutCustomPanel
- 新增 `src/stores/lua.ts`、`src/stores/keyAnalyzer.ts`、`src/stores/healthCheck.ts`
- 扩展 `src/stores/terminal.ts`：多 Tab 状态（tabs: Map<TabId, CliTabState>）
- 新增 `src/ipc/phase4.ts`：lua_*、import_export_*、key_analyzer_*、health_check_* IPC 封装
- 扩展 `src/views/MainLayout.vue`：Toolbar 新增 Lua + Tools 两个 Tab 按钮（共 8 Tab）

**依赖**
- Rust：`rdb`（rdb-rs，RDB 解析）、`csv`（CSV 导出）
- 前端：`@codemirror/lang-lua`（Lua 语法高亮）、`file-saver`（文件下载）

**数据库 Schema**
- 新增 `lua_scripts` 表（id, name, script, created_at, last_used_at）
- 新增 `shortcut_bindings` 表（action, binding, updated_at）
- 新增 `masking_rules` 表（id, pattern, mask_char, enabled）
