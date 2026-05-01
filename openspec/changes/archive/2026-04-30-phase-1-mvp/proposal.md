## Why

Phase 0 已验证最小 IPC 闭环（Vue → Tauri → Rust → Redis PONG），但应用仍处于空壳状态：Sidebar/KeyPanel 使用 mock 数据，Welcome 页仅能测试连接，无法浏览或操作真实 Redis 数据。Phase 1 是产品从"能跑"到"能用"的关键跨越——实现连接持久化、键浏览、5 种数据类型查看、CRUD 操作和 CLI 终端，达到 MVP 可用状态（对应 v0.1）。

## What Changes

- **连接管理全流程**：新建/编辑/删除连接配置，密码 Keychain 存储，连接列表持久化（SQLite），导入/导出配置文件
- **连接会话管理**：建立/关闭连接（ConnectionMultiplexer 复用），DB 切换，连接状态实时反馈
- **键浏览**：替换 mock 数据为真实 SCAN 分页加载，支持 pattern 搜索、类型筛选、DB 切换后自动刷新
- **5 种基础类型查看器**：String / Hash / List / Set / ZSet 的数据渲染，含元数据栏（类型/TTL/大小/编码/元素数/DB）
- **CRUD 操作**：行内编辑、弹窗编辑、删除（含确认）、重命名、TTL 设置/移除
- **CLI 终端**：基础命令执行 + 命令历史（↑↓）+ ⌘L 清屏 + 输出 RESP 类型着色 + 危险命令二次确认
- **快捷键体系**：⌘K 全局搜索 / ⌘N 新建连接 / ⌘F 键搜索 / ⌘1⌘2 切换面板 / ⌘+Enter 保存 / ⌘L 清屏
- **Sidebar/KeyPanel 真实数据**：连接列表从 SQLite 读取，DB 列表从 INFO keyspace 解析，键面板 SCAN 加载
- **Welcome 页升级**：快速连接后可"保存为新连接"，已有连接列表可直接点击连接

## Capabilities

### New Capabilities

- `connection-manager`: 连接配置 CRUD、SQLite 持久化、Keychain 密码存取、导入/导出、会话建立与释放（ConnectionMultiplexer）、DB 切换、连接状态机
- `key-browser`: SCAN 分页游标管理、pattern 搜索（SCAN MATCH）、类型筛选、键元数据获取（TYPE/TTL/MEMORY USAGE/OBJECT ENCODING）、DB 切换后刷新
- `data-viewer`: 5 种基础类型（String/Hash/List/Set/ZSet）数据渲染、元数据栏、子 Tab 切换（数据/原始/相关命令）
- `data-editor`: 行内编辑与弹窗编辑、删除确认（单键确认/批量输入键名）、重命名（RENAME）、TTL 设置（EXPIRE/PERSIST）、新建键
- `cli-terminal`: 通用命令执行（cli_exec）、命令历史（↑↓/持久化）、RESP 输出着色、清屏、危险命令拦截与二次确认
- `shortcut-system`: 全局快捷键注册（⌘K/⌘N/⌘F/⌘1/⌘2/⌘+Enter/⌘L/⌘+Shift+R）、快捷键与 UI 操作绑定

### Modified Capabilities

- `app-shell`: Sidebar 从 mock 改为真实连接列表（SQLite）+ DB 列表（INFO keyspace）；KeyPanel 从 mock 改为 SCAN 数据；新增连接管理弹窗（ConnectionForm Dialog）；Welcome 页增加"保存连接"与"已有连接"入口；Browser workspace 占位替换为真实 KeyDetail 组件
- `ipc-foundation`: 新增 IPC 命令——connection_save / connection_list / connection_delete / connection_open / connection_close / db_select / keys_scan / key_get / key_set / key_delete / key_rename / key_ttl_set / cli_exec / cli_history_get；新增 Tauri Event——connection:state；IpcError 新增 AuthFailed / NotFound 变体
- `connection-ping`: 测试连接从独立功能变为连接管理流程的子步骤（新建连接 → 测试 → 保存），Welcome 页快速连接增加"保存为新连接"选项

## Impact

- **Rust 后端**：新增 sqlx（SQLite）+ security-framework（Keychain）依赖；新增 services/connection_manager.rs（会话池）、services/key_browser.rs（SCAN 游标）、services/data_ops.rs（CRUD）、services/terminal.rs（CLI）；models/ 大幅扩展；commands/ 新增 8+ 个 IPC 入口
- **前端**：新增 6 个 Pinia Store（connection/keyBrowser/dataEditor/terminal/shortcut）；新增 5 个类型查看器组件；新增 ConnectionForm 弹窗；Sidebar/KeyPanel 数据源从 mock 切换为 store；BrowserPlaceholder 替换为完整 BrowserWorkspace
- **数据库**：首次引入 SQLite，需定义 schema（connections 表 + cli_history 表）+ migration 机制
- **安全**：Keychain 集成首次落地，需处理首次权限弹窗的用户引导
- **性能**：SCAN 需虚拟滚动支持百万级 Key；ConnectionMultiplexer 需正确管理生命周期避免连接泄漏
