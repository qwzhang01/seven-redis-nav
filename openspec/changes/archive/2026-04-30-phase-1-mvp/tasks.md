## 1. Rust 后端 — 数据库与依赖

- [x] 1.1 Cargo.toml 添加 sqlx（sqlite + runtime-tokio + migrate）、security-framework、uuid 依赖
- [x] 1.2 创建 `src-tauri/migrations/001_init.sql`（connections 表 + cli_history 表）
- [x] 1.3 实现 `src-tauri/src/utils/db.rs`：初始化 SQLite 连接池、运行 migration
- [x] 1.4 实现 `src-tauri/src/utils/keychain.rs`：macOS Keychain 密码存取（save/get/delete）
- [x] 1.5 更新 `utils/mod.rs` 导出新模块

## 2. Rust 后端 — IpcError 扩展

- [x] 2.1 `error.rs` 新增 `AuthFailed`、`NotFound`、`DangerousCommand` 变体
- [x] 2.2 `DangerousCommand` 携带 `command: String` 和 `confirm_token: String`
- [x] 2.3 前端 `src/types/ipc.d.ts` 同步更新 IpcErrorKind 和 IpcError 类型

## 3. Rust 后端 — 连接管理服务

- [x] 3.1 定义 `models/connection.rs`：ConnectionConfig / ConnectionMeta / ConnId / SessionId / DbStat / ConnectionState
- [x] 3.2 实现 `services/connection_manager.rs`：ConnectionMultiplexer 会话池（HashMap<ConnId, MultiplexedConnection>）
- [x] 3.3 实现 `connection_open`：创建 MultiplexedConnection、AUTH、存入会话池
- [x] 3.4 实现 `connection_close`：从会话池移除、drop 连接
- [x] 3.5 实现心跳 PING（30s 间隔）+ 断连检测 + `connection:state` Event 推送
- [x] 3.6 实现 `db_select`：发送 SELECT 命令 + 解析 INFO keyspace 返回 DbStat
- [x] 3.7 实现 `connection_save`：SQLite 写入 + Keychain 密码存储
- [x] 3.8 实现 `connection_list`：SQLite 查询 + Keychain 密码读取
- [x] 3.9 实现 `connection_delete`：SQLite 删除 + Keychain 条目删除
- [x] 3.10 更新 `commands/connection.rs`：注册新命令（connection_open/close/save/list/delete/db_select）
- [x] 3.11 更新 `lib.rs` invoke_handler 注册新命令

## 4. Rust 后端 — 键浏览服务

- [x] 4.1 定义 `models/data.rs`：ScanPage / KeyMeta / KeyDetail / RedisValue / KeyType
- [x] 4.2 实现 `services/key_browser.rs`：SCAN 分页（cursor/MATCH/COUNT）、TYPE/TTL/MEMORY USAGE/OBJECT ENCODING
- [x] 4.3 实现 `commands/data.rs`：keys_scan / key_get IPC 入口
- [x] 4.4 更新 `models/mod.rs` 和 `commands/mod.rs` 导出新模块

## 5. Rust 后端 — 数据操作服务

- [x] 5.1 实现 `services/data_ops.rs`：key_set（按类型分发 SET/HSET/LPUSH/SADD/ZADD）/ key_delete / key_rename / key_ttl_set
- [x] 5.2 实现 `commands/data.rs`：key_set / key_delete / key_rename / key_ttl_set IPC 入口

## 6. Rust 后端 — CLI 终端服务

- [x] 6.1 定义 `models/terminal.rs`：CliReply / CliHistoryEntry / DangerousCommandWhitelist
- [x] 6.2 实现 `services/terminal.rs`：cli_exec（原始命令解析 + redis::cmd 透传 + 危险命令白名单拦截 + confirm_token 校验）
- [x] 6.3 实现 `commands/terminal.rs`：cli_exec / cli_history_get IPC 入口
- [x] 6.4 危险命令白名单：FLUSHDB / FLUSHALL / SHUTDOWN / DEBUG / CONFIG SET requirepass
- [x] 6.5 cli_history SQLite 持久化（写入 + 查询最近 200 条）

## 7. 前端 — IPC 层扩展

- [x] 7.1 `src/types/connection.d.ts` 新增：ConnectionConfig / ConnectionMeta / ConnId / SessionId / DbStat / ConnectionState
- [x] 7.2 `src/types/data.d.ts` 新增：ScanPage / KeyMeta / KeyDetail / RedisValue / KeyType
- [x] 7.3 `src/types/terminal.d.ts` 新增：CliReply / CliHistoryEntry
- [x] 7.4 `src/ipc/connection.ts` 扩展：connectionList / connectionSave / connectionDelete / connectionOpen / connectionClose / dbSelect
- [x] 7.5 `src/ipc/data.ts` 新建：keysScan / keyGet / keySet / keyDelete / keyRename / keyTtlSet
- [x] 7.6 `src/ipc/terminal.ts` 新建：cliExec / cliHistoryGet
- [x] 7.7 `src/ipc/event.ts` 新建：listenConnectionState（Tauri Event 监听封装）

## 8. 前端 — Pinia Stores

- [x] 8.1 `src/stores/connection.ts`：连接列表 / 当前连接 / 会话状态 / DB 列表 / 连接 CRUD / open/close
- [x] 8.2 `src/stores/keyBrowser.ts`：SCAN 状态 / 当前页键列表 / cursor 栈 / 过滤条件(pattern+type) / 选中键
- [x] 8.3 `src/stores/data.ts`：当前键详情 / 查看器数据 / 编辑状态 / CRUD 操作
- [x] 8.4 `src/stores/terminal.ts`：CLI 历史记录 / 输出行 / 当前输入 / 命令执行
- [x] 8.5 更新 `src/stores/workspace.ts`：connected 状态改为由 connection store 驱动

## 9. 前端 — ConnectionForm 弹窗

- [x] 9.1 创建 `src/components/dialogs/ConnectionForm.vue`：名称/分组/主机/端口/密码/DB/超时表单
- [x] 9.2 表单内"测试连接"按钮集成 connectionTest IPC
- [x] 9.3 保存按钮集成 connectionSave IPC
- [x] 9.4 编辑模式：预填已有值 + 密码占位符
- [x] 9.5 Keychain 权限提示文案

## 10. 前端 — Sidebar 真实数据

- [x] 10.1 重构 `Sidebar.vue`：连接列表从 useConnectionStore 获取
- [x] 10.2 连接项右键上下文菜单（编辑/复制/删除/断开）
- [x] 10.3 连接项点击 → connectionOpen
- [x] 10.4 DB 列表从 INFO keyspace 解析渲染
- [x] 10.5 Sidebar 收起/展开动画 + ⌘1 绑定

## 11. 前端 — KeyPanel 真实数据

- [x] 11.1 重构 `KeyPanel.vue`：键列表从 useKeyBrowserStore 获取
- [x] 11.2 搜索输入 → pattern SCAN
- [x] 11.3 类型筛选下拉 → 客户端过滤
- [x] 11.4 分页 → cursor 栈前后翻页
- [x] 11.5 键项点击 → keyGet → 填充 data store
- [x] 11.6 KeyPanel 收起/展开动画 + ⌘2 绑定
- [x] 11.7 新建键按钮 → 键创建表单

## 12. 前端 — Browser Workspace (5 种类型查看器)

- [x] 12.1 创建 `src/components/workspaces/browser/BrowserWorkspace.vue`：detail header + metadata bar + sub-tabs
- [x] 12.2 创建 `StringViewer.vue`：文本区域展示 String 值
- [x] 12.3 创建 `HashViewer.vue`：字段-值对表格（字段 | 值 | 操作）
- [x] 12.4 创建 `ListViewer.vue`：索引-值列表（索引 | 值 | 操作）
- [x] 12.5 创建 `SetViewer.vue`：成员卡片列表 + 删除按钮
- [x] 12.6 创建 `ZSetViewer.vue`：成员-分数对表格（分数 | 成员 | 操作）
- [x] 12.7 类型分发逻辑：根据 KeyDetail.type 渲染对应 Viewer
- [x] 12.8 元数据栏：类型/TTL/大小/编码/元素数/DB
- [x] 12.9 子 Tab：数据/原始(JSON)/相关命令

## 13. 前端 — Data Editor 操作

- [x] 13.1 行内编辑：双击值单元格 → 编辑输入 → ⌘+Enter 提交
- [x] 13.2 删除确认弹窗：显示键名 → 输入键名确认 → keyDelete
- [x] 13.3 重命名弹窗：输入新键名 → keyRename
- [x] 13.4 TTL 编辑弹窗：设置过期时间（秒/分/时/天）→ keyTtlSet
- [x] 13.5 新建键表单：选择类型 → 输入键名和初始值 → keySet
- [x] 13.6 操作 Toast 反馈（成功绿/失败红）

## 14. 前端 — CLI Workspace

- [x] 14.1 创建 `src/components/workspaces/cli/CliWorkspace.vue`：输出区 + 输入行
- [x] 14.2 命令输入 → cliExec IPC → 输出着色渲染
- [x] 14.3 RESP 着色：错误红/字符串绿/整数橙/数组缩进
- [x] 14.4 ↑↓ 命令历史导航
- [x] 14.5 ⌘L 清屏 / CLEAR 命令
- [x] 14.6 危险命令确认弹窗（显示命令名 → 输入确认 → 带 confirm_token 重发）
- [x] 14.7 CLI Tab 激活时自动聚焦输入

## 15. 前端 — Welcome 页升级

- [x] 15.1 Welcome 页新增"已保存的连接"列表区域（从 connectionStore 获取）
- [x] 15.2 点击已有连接 → connectionOpen
- [x] 15.3 快速连接成功后显示"保存为新连接"按钮
- [x] 15.4 "保存为新连接" → 打开 ConnectionForm 预填

## 16. 前端 — 快捷键体系

- [x] 16.1 创建 `src/composables/useShortcut.ts`：全局 keydown 监听 + 条件分发
- [x] 16.2 ⌘K → 聚焦全局搜索 / ⌘N → 新建连接 / ⌘F → 聚焦键搜索
- [x] 16.3 ⌘1 → 切换 Sidebar / ⌘2 → 切换 KeyPanel
- [x] 16.4 ⌘L → CLI 清屏（仅 CLI Tab）/ ⌘+Enter → 保存编辑（仅编辑模式）
- [x] 16.5 ⌘+Shift+R → 刷新当前数据
- [x] 16.6 阻止浏览器默认快捷键行为（preventDefault）

## 17. 前端 — Statusbar 动态数据

- [x] 17.1 Statusbar 左侧：从 connectionStore 获取 host:port/version/db
- [x] 17.2 连接后更新状态栏文本

## 18. 端到端验证

- [ ] 18.1 新建连接 → 保存 → 重启 App → 连接仍存在
- [ ] 18.2 打开连接 → DB 切换 → 键列表 SCAN → 选中键 → 查看详情
- [ ] 18.3 编辑 Hash 字段 → 保存 → 刷新验证
- [ ] 18.4 删除键 → 确认弹窗 → 输入键名 → 删除成功
- [ ] 18.5 CLI 执行 PING → 看到着色输出
- [ ] 18.6 CLI 执行 FLUSHDB → 弹出危险确认
- [ ] 18.7 ⌘K/⌘N/⌘F/⌘1/⌘2 快捷键全部生效
