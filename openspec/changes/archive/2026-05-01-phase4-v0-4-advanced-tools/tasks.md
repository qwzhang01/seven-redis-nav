## 1. 基础设施：依赖安装与数据库迁移

- [x] 1.1 `Cargo.toml` 新增依赖：`rdb`（rdb-rs）、`csv`（CSV 导出）
- [x] 1.2 `package.json` 新增依赖：`@codemirror/lang-lua`、`file-saver`、`@types/file-saver`
- [x] 1.3 新增 SQLite 迁移文件：`lua_scripts` 表（id, name, script, created_at, last_used_at）
- [x] 1.4 新增 SQLite 迁移文件：`shortcut_bindings` 表（action, binding, updated_at）
- [x] 1.5 新增 SQLite 迁移文件：`masking_rules` 表（id, pattern, mask_char, enabled, sort_order）
- [x] 1.6 新增 SQLite 迁移文件：`health_reports` 表（id, connection_id, score, report_json, created_at）
- [x] 1.7 在 `utils/config_store.rs` 中实现 lua_scripts / shortcut_bindings / masking_rules / health_reports 的 CRUD 操作
- [x] 1.8 扩展 `workspace.ts` 的 `WorkspaceTab` 枚举，新增 `lua` 和 `tools` 两个值
- [x] 1.9 新增 `src/ipc/phase4.ts`，定义所有 Phase 4 IPC 函数的类型签名与封装

## 2. Lua 脚本编辑器：后端实现

- [x] 2.1 新增 `src-tauri/src/models/lua.rs`：`LuaScript`、`LuaEvalResult` 数据模型
- [x] 2.2 新增 `src-tauri/src/commands/lua.rs`：`lua_eval`（EVAL 执行）命令
- [x] 2.3 实现 `lua_evalsha`（EVALSHA 执行）命令
- [x] 2.4 实现 `lua_script_load`（SCRIPT LOAD，返回 SHA1）命令
- [x] 2.5 实现 `lua_script_exists`（SCRIPT EXISTS，检查 SHA1 是否存在）命令
- [x] 2.6 实现 `lua_history_save`（保存脚本到 SQLite）命令
- [x] 2.7 实现 `lua_history_list`（列出历史脚本）命令
- [x] 2.8 实现 `lua_history_delete`（删除历史脚本）命令
- [x] 2.9 实现 `lua_history_rename`（重命名历史脚本）命令
- [x] 2.10 在 `lib.rs` 中注册所有 lua_* IPC 命令

## 3. Lua 脚本编辑器：前端实现

- [x] 3.1 新增 `src/stores/lua.ts`：脚本内容、历史列表、执行结果、KEYS/ARGV 参数状态
- [x] 3.2 新增 `src/components/workspaces/lua/LuaWorkspace.vue`：整体布局（左侧历史列表 200px + 右侧编辑器主区）
- [x] 3.3 新增 `src/components/workspaces/lua/LuaScriptList.vue`：历史脚本列表，支持点击加载、双击重命名、删除
- [x] 3.4 新增 `src/components/workspaces/lua/LuaEditor.vue`：CodeMirror 6 + `@codemirror/lang-lua` 编辑器，含默认模板
- [x] 3.5 新增 `src/components/workspaces/lua/LuaArgsForm.vue`：KEYS + ARGV 动态参数表单（支持增减行）
- [x] 3.6 新增 `src/components/workspaces/lua/LuaResultPanel.vue`：执行结果面板（RESP 类型着色：整数橙/字符串绿/数组缩进/错误红）
- [x] 3.7 在 `LuaWorkspace.vue` 中实现 ⌘+Enter 执行快捷键
- [x] 3.8 在 `MainLayout.vue` Toolbar 中新增 "Lua" Tab 按钮（`ri-code-s-slash-line`）

## 4. 数据导入导出：后端实现

- [x] 4.1 新增 `src-tauri/src/models/import_export.rs`：`RedisExport`、`ExportKey`、`ImportResult` 数据模型
- [x] 4.2 新增 `src-tauri/src/commands/import_export.rs`：`export_keys_json`（导出选中键为 JSON）命令
- [x] 4.3 实现 `export_db_json`（导出整个 DB 为 JSON，含进度 Event 推送）命令
- [x] 4.4 实现 `import_keys_json`（从 JSON 文件导入键值对，含冲突处理选项）命令
- [x] 4.5 实现 `rdb_parse_file`（只读解析 RDB 文件，返回键列表）命令，使用 rdb-rs
- [x] 4.6 在 `lib.rs` 中注册所有 import_export_* IPC 命令

## 5. 数据导入导出：前端实现

- [x] 5.1 新增 `src/components/workspaces/tools/ImportExportPanel.vue`：导入/导出操作面板
- [x] 5.2 实现导出选中键功能：键面板多选后工具栏显示"导出"按钮，点击弹出导出确认对话框（含预估大小）
- [x] 5.3 实现导出整个 DB 功能：键面板工具栏"导出全部"按钮 + 进度条对话框
- [x] 5.4 实现 JSON 导入功能：文件选择 → 格式验证 → 预览对话框（键数量/类型分布/冲突列表）→ 执行导入 → 导入报告
- [x] 5.5 实现 RDB 文件解析功能：文件选择 → 解析 → 只读 Browser Workspace 展示（标注"只读模式"）
- [x] 5.6 使用 `file-saver` 实现 JSON 文件下载（浏览器端触发保存对话框）

## 6. 大 Key 扫描与 TTL 分析：后端实现

- [x] 6.1 新增 `src-tauri/src/models/key_analyzer.rs`：`KeyMemoryStat`、`TtlDistribution`、`ScanProgress` 数据模型
- [x] 6.2 新增 `src-tauri/src/services/key_analyzer.rs`：后台异步扫描任务
- [x] 6.3 新增 `src-tauri/src/commands/tools.rs`：`key_scan_memory_start`命令
- [x] 6.4 实现 `key_scan_memory_stop`（取消扫描任务）命令
- [x] 6.5 实现 `key_ttl_distribution`（SCAN + TTL 抽样，最多 10000 键，返回 TTL 分布数据）命令
- [x] 6.6 实现 `key_scan_memory_export_csv`（将扫描结果导出为 CSV）命令
- [x] 6.7 在 `lib.rs` 中注册所有 tools_* IPC 命令

## 7. 大 Key 扫描与 TTL 分析：前端实现

- [x] 7.1 新增 `src/stores/keyAnalyzer.ts`：扫描进度、Top 100 列表、TTL 分布数据状态
- [x] 7.2 新增 `src/components/workspaces/tools/KeyScanPanel.vue`：大 Key 扫描面板（进度条 + Top 100 表格 + 低影响模式开关）
- [x] 7.3 实现 Top 100 表格：键名/类型/内存大小/编码/元素数，支持列排序
- [x] 7.4 实现"跳转到键"功能：点击键名切换到 Browser Tab 并定位该键
- [x] 7.5 实现导出 CSV 功能（调用 `key_scan_memory_export_csv` + file-saver）
- [x] 7.6 新增 `src/components/workspaces/tools/TtlDistributionPanel.vue`：TTL 分布直方图（ECharts 柱状图）+ 即将过期警告

## 8. 健康检查报告：后端实现

- [x] 8.1 新增 `src-tauri/src/models/health_check.rs`：`HealthReport`、`HealthIndicator`、`HealthLevel`（Normal/Warning/Danger）数据模型
- [x] 8.2 新增 `src-tauri/src/services/health_check.rs`：聚合 INFO all / SLOWLOG GET 128 / CONFIG GET 多项，计算 10 项指标评分，生成 `HealthReport`
- [x] 8.3 新增 `src-tauri/src/commands/tools.rs`（扩展）：`health_check_generate`（生成健康报告，保存到 SQLite）命令
- [x] 8.4 实现 `health_check_history_list`（列出历史报告）命令
- [x] 8.5 实现 `health_check_history_get`（获取某条历史报告详情）命令
- [x] 8.6 实现 `health_check_export_markdown`（将报告导出为 Markdown 文本）命令

## 9. 健康检查报告：前端实现

- [x] 9.1 新增 `src/stores/healthCheck.ts`：当前报告、历史列表、生成状态
- [x] 9.2 新增 `src/components/workspaces/tools/HealthCheckPanel.vue`：健康报告面板（总体健康分 + 4 维度卡片 + 10 项指标列表）
- [x] 9.3 实现总体健康分大数字展示（颜色：≥80 绿 / 60-79 橙 / <60 红）
- [x] 9.4 实现 10 项指标列表：每项显示指标名/当前值/评级徽章（正常绿/警告橙/危险红）/改进建议
- [x] 9.5 实现历史报告列表对话框（时间/连接名/总体健康分）
- [x] 9.6 实现导出 Markdown 功能（调用 `health_check_export_markdown` + file-saver，默认文件名含 host 和日期）

## 10. Tools 工作区容器

- [x] 10.1 新增 `src/components/workspaces/tools/ToolsWorkspace.vue`：Tools 工作区容器，包含子 Tab 导航（大 Key 扫描 / TTL 分析 / 健康检查 / 导入导出）
- [x] 10.2 在 `MainLayout.vue` Toolbar 中新增 "Tools" Tab 按钮（`ri-tools-line`）
- [x] 10.3 实现 Tools 工作区的子 Tab 切换逻辑（Pinia store 管理激活子 Tab）

## 11. 多 Tab CLI：后端实现

- [x] 11.1 扩展 `src-tauri/src/services/terminal.rs`：`CliSessionManager`，使用 `HashMap<TabId, CliSession>` 管理多个 CLI 会话
- [x] 11.2 新增 `cli_tab_create`（创建新 CLI Tab，建立独立 Redis 连接，返回 TabId）命令
- [x] 11.3 新增 `cli_tab_close`（关闭 CLI Tab，释放 Redis 连接）命令
- [x] 11.4 修改 `cli_exec` 命令：新增 `tab_id` 参数，路由到对应 CliSession
- [x] 11.5 修改 `cli_history_get` 命令：新增 `tab_id` 参数，返回对应 Tab 的历史
- [x] 11.6 实现空闲 Tab 超时检测（30 分钟无命令执行自动释放连接，推送 `cli:tab_disconnected` Event）

## 12. 多 Tab CLI：前端实现

- [x] 12.1 扩展 `src/stores/terminal.ts`：从单状态改为 `Map<TabId, CliTabState>`，保留单 Tab 向后兼容
- [x] 12.2 新增 `src/components/workspaces/cli/CliTabBar.vue`：标签页栏（标签列表 + "+" 新建按钮），支持双击重命名
- [x] 12.3 新增 `src/components/workspaces/cli/CliTabPanel.vue`：单个 CLI 标签页内容（输出区 + 输入框）
- [x] 12.4 重构 `src/components/workspaces/cli/CliWorkspace.vue`：整合 CliTabBar + CliTabPanel，实现多 Tab 容器
- [x] 12.5 实现 ⌘T 新建 Tab、⌘W 关闭 Tab 快捷键（在 CLI Tab 内生效）
- [x] 12.6 实现 Tab 数量限制（最多 8 个，超出时 "+" 按钮禁用）
- [x] 12.7 实现空闲 Tab 断开提示（监听 `cli:tab_disconnected` Event，标签显示"(已断开)"）

## 13. 数据脱敏：后端实现

- [x] 13.1 新增 `masking_rule_list`（列出所有脱敏规则）命令
- [x] 13.2 新增 `masking_rule_save`（保存/更新脱敏规则到 SQLite）命令
- [x] 13.3 新增 `masking_rule_delete`（删除脱敏规则）命令
- [x] 13.4 新增 `masking_rule_reorder`（调整规则顺序）命令

## 14. 数据脱敏：前端实现

- [x] 14.1 新增 `src/stores/masking.ts`：脱敏规则列表状态，提供 `isMasked(key)` 和 `getMask(key)` 方法
- [x] 14.2 新增 `src/composables/useDataMasking.ts`：glob 模式匹配逻辑，供所有 Viewer 组件复用
- [x] 14.3 新增 `src/components/settings/DataMaskingPanel.vue`：脱敏规则配置面板（规则列表 + 添加/删除/启用开关）
- [x] 14.4 在 `StringViewer.vue` 中集成脱敏逻辑：匹配规则时显示掩码 + "🔒 已脱敏"标识
- [x] 14.5 在 `HashViewer.vue` 中集成脱敏逻辑：所有 value 列显示掩码，field 列不脱敏
- [x] 14.6 在 `ListViewer.vue`、`SetViewer.vue`、`ZSetViewer.vue` 中集成脱敏逻辑
- [x] 14.7 确保编辑弹窗中显示原始值（不脱敏）

## 15. 快捷键自定义：后端实现

- [x] 15.1 新增 `shortcut_binding_list`（列出所有自定义绑定）命令
- [x] 15.2 新增 `shortcut_binding_save`（保存/更新单个快捷键绑定到 SQLite）命令
- [x] 15.3 新增 `shortcut_binding_delete`（删除单个自定义绑定，恢复默认）命令
- [x] 15.4 新增 `shortcut_binding_reset_all`（清空所有自定义绑定）命令

## 16. 快捷键自定义：前端实现

- [x] 16.1 扩展 `src/composables/useShortcut.ts`：App 启动时从 SQLite 加载自定义绑定，合并到默认绑定表
- [x] 16.2 新增 `src/components/settings/ShortcutCustomPanel.vue`：快捷键配置面板（按功能分组的列表 + 录制模式 + 冲突检测）
- [x] 16.3 实现录制模式：点击编辑按钮进入录制，监听 keydown 事件，显示组合键预览
- [x] 16.4 实现冲突检测：录制时实时检测与现有绑定的冲突，显示橙色警告
- [x] 16.5 实现重置单个快捷键（删除 SQLite 记录，恢复默认值）
- [x] 16.6 实现重置全部快捷键（清空 SQLite `shortcut_bindings` 表）

## 17. 设置页面集成

- [x] 17.1 扩展设置页面（`src/views/Settings.vue` 或对应组件），新增"数据脱敏"和"快捷键"两个菜单项
- [x] 17.2 实现设置页面的路由/导航逻辑，点击菜单项切换右侧面板

## 18. 验证与收尾

- [x] 18.1 编译验证：`cargo build` 无错误，`pnpm build` 无错误
- [ ] 18.2 运行验证：启动应用，打开 Lua Tab，编写并执行简单 Lua 脚本（`return redis.call('PING')`），验证结果正确
- [ ] 18.3 运行验证：验证 EVALSHA 流程（SCRIPT LOAD → 获取 SHA → EVALSHA 执行）
- [ ] 18.4 运行验证：导出选中键为 JSON，验证文件格式正确；重新导入，验证键值一致
- [ ] 18.5 运行验证：打开 RDB 文件，验证键列表正确解析并以只读模式展示
- [ ] 18.6 运行验证：启动大 Key 扫描，验证进度推送和 Top 100 报告正确
- [ ] 18.7 运行验证：生成健康检查报告，验证 10 项指标数据正确，导出 Markdown 文件格式正确
- [ ] 18.8 运行验证：⌘T 新建 CLI Tab，验证两个 Tab 的命令历史和 DB 状态互相独立
- [ ] 18.9 运行验证：配置数据脱敏规则（如 `*token*`），验证 Browser Workspace 中匹配键的 value 显示为掩码
- [ ] 18.10 运行验证：自定义快捷键绑定，重启 App 后验证绑定持久化生效
- [x] 18.11 处理编译 warning（`cargo clippy` 无新增 warning）
- [ ] 18.12 性能验证：大 Key 扫描 10w 键实例，< 30s 完成；健康报告生成 < 5s
