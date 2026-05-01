## Context

Phase 0 已交付：Tauri v2 + Vue 3 + Rust 工程脚手架、`connection_test` IPC 端到端闭环、6 区域窗口布局（Titlebar/Toolbar/Sidebar/KeyPanel/Workspace/Statusbar）、Design Token 系统、Pinia workspace store。

当前状态：
- Sidebar 和 KeyPanel 使用硬编码 mock 数据，无法操作真实 Redis
- Welcome 页仅能测试连接，无法保存或管理连接
- 6 个 Workspace Tab 全部为占位组件
- Rust 后端仅有 `services/connection.rs`（短连接 ping），无会话池、无持久化
- 前端 IPC 层仅封装了 `connection_test` 一条命令

Phase 1 需要将应用从"能 PING"推进到"能浏览/编辑/执行"，涉及 6 个新 capability 和 3 个已有 capability 的修改，是整个项目中变更量最大的单个阶段。

## Goals / Non-Goals

**Goals:**

- 用户可创建/编辑/删除连接配置，密码安全存储于 Keychain，配置持久化到 SQLite
- 用户可浏览真实 Redis 键数据（SCAN 分页、搜索、类型筛选）
- 用户可查看 5 种基础类型（String/Hash/List/Set/ZSet）的数据内容
- 用户可执行 CRUD 操作（编辑值、删除键、重命名、TTL 管理）
- 用户可通过 CLI Tab 执行任意 Redis 命令并查看着色输出
- 全局快捷键体系可用（⌘K/⌘N/⌘F/⌘1/⌘2/⌘L/⌘+Enter）
- Sidebar/KeyPanel 从 mock 切换为真实数据驱动

**Non-Goals:**

- SSH 隧道 / TLS 连接（Phase 2）
- Sentinel / Cluster 模式（Phase 2）
- 批量操作（多选/批量删除/批量 TTL）（Phase 2）
- Stream / Bitmap / HyperLogLog / JSON 智能识别查看器（Phase 3）
- 监控/慢查询/Pub-Sub/配置 Tab 实现（Phase 2-3）
- 虚拟滚动（百万级 Key 性能优化留 Phase 2，Phase 1 用常规分页）
- 主题/深色模式/i18n（Phase 5）

## Decisions

### D1. 连接会话管理：ConnectionMultiplexer 池

**选择**：使用 `redis-rs` 的 `MultiplexedConnection`，每个打开的连接在 `ConnectionManager` 中持有一个 `MultiplexedConnection` 实例，所有命令复用同一连接。

**理由**：
- `MultiplexedConnection` 是 redis-rs 官方推荐的单连接复用模式，支持并发命令而不需连接池
- CLI Tab 需要独立连接（避免阻塞订阅/长命令），用 `separate_connection` 方法派生
- 比 Standalone 连接池更简单，比每命令新建连接更高效

**替代方案**：
- 每次命令新建连接：延迟高，无法保持 AUTH 状态
- 多连接池（r2d2-redis）：额外依赖，Phase 1 并发量不需要
- 死连接池（deadpool-redis）：tokio 生态好但引入更多依赖

### D2. 持久化：SQLite (sqlx) + Keychain

**选择**：
- 连接配置元数据（host/port/name/group）→ SQLite
- 密码 → macOS Keychain（`security-framework` crate）
- CLI 历史 → SQLite

**理由**：
- SQLite 是 Tauri 桌面应用的标准本地存储方案，sqlx 是 Rust 异步 SQLite 驱动
- 密码不应落盘明文，macOS Keychain 是原生安全存储
- Phase 0 已在 Cargo.toml 规划 sqlx 和 security-framework

**替代方案**：
- 全量 JSON/TOML 文件：无法安全存储密码，无查询能力
- 全量 Keychain：Keychain 不适合存储结构化数据，查询受限
- 文件加密（AES-GCM 自管理）：需要自行管理密钥，不如 Keychain 安全

### D3. SCAN 分页策略：游标 + 固定 COUNT

**选择**：使用 `SCAN cursor MATCH pattern COUNT 200`，前端维护 cursor 栈实现分页。

**理由**：
- SCAN 是 Redis 官方推荐的遍历方式，不阻塞服务器
- COUNT 200 在大多数场景下单次返回 50-150 条，平衡延迟和次数
- 前端 cursor 栈（Array<u64>）支持"上一页"操作（重放游标）
- 类型筛选在前端过滤（SCAN TYPE 需要 Redis 6.0+，且不能和 MATCH 同时用）

**替代方案**：
- `KEYS *`：生产环境禁止，O(N) 阻塞
- 全量 SCAN 到前端再分页：大量 Key 时内存爆炸
- HSCAN/SSCAN/ZSCAN：用于大 Hash/Set 内部分页，不属于键列表场景

### D4. 数据查看器：类型分发 + 独立组件

**选择**：`KeyDetail` 组件根据 `TYPE` 返回值分发到 5 个类型专用查看器（StringViewer / HashViewer / ListViewer / SetViewer / ZSetViewer），每个查看器独立 Vue 组件。

**理由**：
- 5 种类型数据结构差异大（String 是单值、Hash 是字段-值对、List 是有序列表…），统一渲染器过于复杂
- 独立组件便于维护和测试，符合单一职责
- 原型设计本身就是每种类型不同布局

**替代方案**：
- 通用表格渲染器：无法表达 String 单值编辑、List 推入等类型特有操作
- 动态 JSON 渲染：丢失类型语义，无法提供类型特定操作按钮

### D5. CLI 命令执行：透传 + 危险命令白名单拦截

**选择**：`cli_exec` 接受原始命令字符串，后端解析为 `redis::cmd` 透传执行；同时在后端维护危险命令白名单（`FLUSHDB/FLUSHALL/SHUTDOWN/DEBUG/CONFIG SET requirepass`），命中时返回 `DangerousCommand` 错误，前端弹确认后带 `confirm_token` 重发。

**理由**：
- 透传保证 CLI 能执行任意命令，包括模块命令（RedisJSON/RediSearch 等）
- 后端拦截比前端拦截更安全（无法绕过）
- 确认 token 机制防止前端伪造确认

**替代方案**：
- 前端拦截：可被绕过，不安全
- 命令白名单（只允许特定命令）：限制过强，违背 CLI 灵活性
- 不拦截：用户可能误操作导致数据丢失

### D6. 快捷键：Tauri 全局快捷键 vs 前端 keydown

**选择**：使用前端 `keydown` 事件监听 + Vue composable `useShortcut()`，不使用 Tauri 全局快捷键 API。

**理由**：
- Phase 1 快捷键全部是应用内操作，无需系统全局热键
- 前端 keydown 更灵活，可感知当前焦点/Tab 状态做条件分发
- 避免 Tauri 全局快捷键的权限配置复杂度

**替代方案**：
- Tauri GlobalShortcut API：需配置权限，适合系统级热键（Phase 4+ 可能需要）

### D7. SQLite Schema 与 Migration

**选择**：使用 sqlx 内嵌 migration（`src-tauri/migrations/`），首次启动自动建表。

**Schema**：
```sql
CREATE TABLE connections (
  id          TEXT PRIMARY KEY,  -- UUID v4
  name        TEXT NOT NULL,
  group_name  TEXT DEFAULT '',
  host        TEXT NOT NULL,
  port        INTEGER NOT NULL DEFAULT 6379,
  auth_db     INTEGER DEFAULT 0,
  timeout_ms  INTEGER DEFAULT 5000,
  keychain_key TEXT,  -- Keychain item ID (null = no password)
  sort_order  INTEGER DEFAULT 0,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);

CREATE TABLE cli_history (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  command     TEXT NOT NULL,
  created_at  TEXT NOT NULL
);
```

**理由**：
- `keychain_key` 间接引用 Keychain，密码本身不在 SQLite 中
- `group_name` 支持未来连接分组（Phase 2 完善分组 UI）
- `sort_order` 支持拖拽排序
- sqlx compile-time check 在开发期捕获 SQL 错误

### D8. 前端 Store 拆分

**选择**：按业务域拆分 6 个新 Pinia Store：

| Store | 职责 |
|-------|------|
| `useConnectionStore` | 连接列表/当前连接/会话管理/DB 列表 |
| `useKeyBrowserStore` | SCAN 状态/当前页键列表/cursor 栈/过滤条件/选中键 |
| `useDataStore` | 当前键详情/查看器数据/编辑状态 |
| `useTerminalStore` | CLI 历史/输出行/当前输入 |
| `useShortcutStore` | 快捷键注册/分发（薄 store，主要是 composable） |
| `useSettingsStore` | 未来扩展占位（主题/字体/语言） |

**理由**：Phase 0 的 `workspace` store 仅管理 activeTab，保留不变。新 store 按业务域拆分避免单 store 膨胀，与 overview 文档的 Store 设计对齐。

## Risks / Trade-offs

| 风险 | 影响 | 缓解 |
|------|------|------|
| Keychain 首次权限弹窗 | 用户困惑 | 保存前显示说明文案；提供"仅本次会话"选项（密码不存 Keychain，仅在内存） |
| SCAN 在大库（>100w Key）较慢 | 键列表加载卡顿 | Phase 1 用 COUNT 200 + 分页；Phase 2 加虚拟滚动 + 后台预加载 |
| MultiplexedConnection 断连 | 所有操作失败 | 心跳 PING（30s）+ 指数退避重连 + connection:state Event 通知前端 |
| SQLite 文件损坏 | 连接配置丢失 | 每次写入用 WAL 模式 + 定期 checkpoint；导出功能作为备份手段 |
| 危险命令白名单遗漏 | 误操作风险 | 白名单保守（宁可多拦截）；拦截后允许用户确认执行 |
| sqlx compile-time check 增加编译时间 | 开发体验 | 使用 `sqlx::query!` 宏离线模式（`.sqlx` 缓存），CI 用在线检查 |
| 大 Key 读取（>1MB Value） | 前端卡顿/内存 | Phase 1 先限制读取大小（>1MB 弹提示）；Phase 2 加分片读取 |

## Migration Plan

1. **数据库初始化**：首次启动时 sqlx migration 自动创建 SQLite 文件和表
2. **Keychain 权限**：首次保存密码时 macOS 弹 Keychain 权限弹窗，需用户允许
3. **Phase 0 兼容**：`connection_test` 命令保持不变，新命令增量添加；workspace store 的 `connected` 状态改为由 connection store 驱动
4. **回滚**：删除 SQLite 文件即可重置连接配置；Keychain 条目可用 `security delete-keychain` 清理
5. **Welcome 页迁移**：现有 Welcome 页保留"快速连接"入口，新增"保存连接"按钮和"已有连接"列表

## Open Questions

- **连接分组 UI 深度**：Phase 1 是否需要文件夹式分组 UI？还是仅在新建连接时可选填"分组名"？
- **CLI 历史持久化数量**：SQLite cli_history 表是否需要定期清理？默认保留多少条？
- **键树视图**：Phase 1 是否实现按分隔符（`:`）的树形 Key 浏览？还是仅用平铺列表 + 搜索？
- **编辑冲突**：多用户同时编辑同一 Key 时的乐观锁策略？Phase 1 是否需要 WATCH/MULTI？
