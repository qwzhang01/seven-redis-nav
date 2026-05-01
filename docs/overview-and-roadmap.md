# Seven Redis Nav · 总览：功能交互、技术架构、开发计划

> 版本：v1.0 · 日期：2026-04-30
> 本文档基于以下输入整合而成：
> - 产品文档：`product-design.md` / `ui-interaction-design.md` / `project-structure.md`
> - 高保真原型：`docs/index.html` + `docs/components/*` + `docs/data.js` + `docs/img/*`
> - 原型说明：`docs/prototype-interaction-spec.md`

---

## 0. 命名与基线说明

| 项 | 决策 |
|---|---|
| 正式产品名 | **Seven Redis Nav**（缩写：SRN） |
| Slogan | *"Navigate Redis like a Pro"* |
| 包名 / 二进制名 | `seven-redis-nav` |
| 窗口标题示例 | `Seven Redis Nav — production-cluster-01` |
| 落地形态 | **以 HTML 原型（6 Tab 工作区 + Mac 窗口隐喻）为最终视觉基线**，融合 `product-design.md` 中的功能广度（SSH/TLS、批量操作、Lua 编辑器、健康检查等） |
| 技术底座 | Tauri v2 + Rust + Vue 3 + TypeScript + TDesign Vue Next + Tailwind CSS 3 |

> 说明：旧版 `ui-interaction-design.md` 中描述的"侧栏/Key 树/内容区"三栏，是更早的方案；最终以原型图中的 **"工具栏 6 Tab + 三栏（连接 / 键 / 工作区）"** 为准。

---

## 1. 整体功能交互说明

### 1.1 一句话定位

> 一款面向开发者与 DBA 的 **macOS 原生 Redis 管理工具**：以 Mac 窗口隐喻为皮肤、以 6 个工作模式（浏览器 / CLI / 监控 / 慢查询 / Pub-Sub / 配置）为功能主线，由 Rust 提供高性能 Redis 接入与本地安全存储。

### 1.2 全局窗口结构

```
┌─────────────────────────────────────────────────────────────────────┐
│ ● ● ●   Seven Redis Nav — production-cluster-01            [↻] [↗]        │ Titlebar  38px
├─────────────────────────────────────────────────────────────────────┤
│ [浏览器][CLI][监控][慢查询][发布订阅][配置]  🔍 ⌘K   ●已连接 [+]    │ Toolbar   48px
├──────────┬──────────────┬───────────────────────────────────────────┤
│ 连接(240)│  键面板(320) │  工作区（自适应）                          │
│ 数据库   │  搜索/筛选    │  Tab 切换：                               │
│ 用户     │  键列表       │  Browser / CLI / Monitor / Slowlog / ...   │
├──────────┴──────────────┴───────────────────────────────────────────┤
│ 🟢 host:port  Redis 7.2.4  DB 0/16     CPU 12%  RAM  OPS  Uptime    │ Statusbar 28px
└─────────────────────────────────────────────────────────────────────┘
```

| 区域 | 宽度 | 主要用途 | 可调整 |
|---|---|---|---|
| Titlebar | 38px 固定 | 窗口控制（红绿灯）、窗口名、刷新/分享 | — |
| Toolbar | 48px 固定 | **6 Tab 切换**、全局搜索（⌘K）、连接状态、新建连接 | — |
| Sidebar | 240px | 连接列表 + DB 列表 + 用户信息 | 可收起（⌘1） |
| KeyPanel | 320px | 键搜索 / 类型筛选 / 键列表 / 分页 | 可收起（⌘2） |
| Workspace | 自适应 | 由当前 Tab 决定渲染哪个面板 | — |
| Statusbar | 28px | 连接信息 + 实时性能指标 | — |

### 1.3 6 个工作 Tab 概览

| # | Tab | 入口图标 | 工作区内容 | 数据来源 |
|---|---|---|---|---|
| 1 | **浏览器** | `ri-file-list-3-line` | 选中键的详情：元数据 / 数据 / 原始 / 历史 / 相关命令 | `TYPE` `OBJECT ENCODING` `MEMORY USAGE` `TTL` + 类型对应读命令 |
| 2 | **命令行** | `ri-terminal-box-line` | Redis CLI 终端：输出区 + 输入行 + 历史 + 补全 | 直接 `redis::cmd` 透传 |
| 3 | **监控** | `ri-pulse-line` | 4 指标卡（OPS/内存/客户端/命中率）+ 服务器信息 + Keyspace + Clients | `INFO` 周期采样 + `CLIENT LIST` |
| 4 | **慢查询** | `ri-timer-flash-line` | 统计卡 + 慢查询表（耗时分级、客户端） | `SLOWLOG GET/LEN/RESET` |
| 5 | **发布订阅** | `ri-broadcast-line` | 频道列表 + 发布区 + 实时消息流 | `PUBSUB CHANNELS` + `SUBSCRIBE/PUBLISH` |
| 6 | **配置** | `ri-settings-3-line` | 分组导航（内存/持久化/网络/安全/复制）+ 配置项编辑 | `CONFIG GET/SET/REWRITE` |

### 1.4 核心交互流程

#### 流程 A：首次连接

```
启动 → Welcome 引导
  ├─ [快速连接]  → host/port/auth 简表单 → PING 测试 → 进入主界面
  ├─ [新建连接] → 完整表单（含 SSH/TLS/Sentinel/Cluster）→ 测试 → 保存到 Keychain
  └─ [导入配置] → 选择 .json/.toml → 解析批量导入
```

#### 流程 B：浏览与编辑键

```
侧栏选连接 → 选 DB → 键面板 SCAN 加载（懒加载/虚拟滚动）
  → 键面板搜索（pattern 走 SCAN MATCH，模糊走客户端过滤）
  → 选中某 Key → 工作区"浏览器" Tab 渲染对应类型查看器
      ├─ 查看：String/Hash/List/Set/ZSet/Stream/JSON 智能渲染
      ├─ 编辑：行内编辑 / 弹窗编辑 → ⌘+Enter 提交 → Toast 反馈
      ├─ TTL：⏱ 设置/移除/批量调整
      ├─ 重命名：RENAME 弹窗
      └─ 删除：⚠️ 模态确认（大批量需输入键名/数字确认）
```

#### 流程 C：CLI 终端

```
切到"命令行" Tab → 自动聚焦输入框
  → 输入命令（实时补全：本地命令字典 + Tab 接受）
  → Enter 执行 → 后端透传 → 输出着色（错误红/字符串绿/整数橙/数组缩进）
  → ↑↓ 历史 / ⌘L 清屏 / ⌘+T 新开 Tab / 危险命令二次确认
```

#### 流程 D：监控

```
切到"监控" Tab → 后端开启周期采样任务（默认 2s）
  → INFO 解析 → 4 个指标卡 + 4 张趋势图（前端 ECharts，后端推送 Tauri Event）
  → 时间范围切换：1h/6h/24h/7d（按粒度采样/聚合）
  → 切走 Tab → 暂停采样以省资源
```

#### 流程 E：危险操作护栏

| 操作 | 护栏 |
|---|---|
| `FLUSHDB` / `FLUSHALL` | 输入指令名全文 + 二次确认 |
| 批量删除 ≥ 100 | 显示数量 + 输入"DELETE" 确认 |
| `KEYS *` / `MONITOR` 长命令 | CLI 弹出"建议改用 SCAN / 是否继续" |
| `CONFIG SET` 持久化项 | 提示是否同时 `CONFIG REWRITE` |

### 1.5 全局快捷键

| 快捷键 | 功能 |
|---|---|
| ⌘K | 聚焦全局搜索 |
| ⌘N | 新建连接 |
| ⌘T | 新开 CLI Tab |
| ⌘W | 关闭当前 CLI Tab |
| ⌘1 / ⌘2 | 收起/展开 Sidebar / KeyPanel |
| ⌘F | 聚焦键搜索 |
| ⌘L | CLI 清屏 |
| ⌘E | 进入编辑模式 |
| ⌘D | 复制选中键名 |
| ⌘+Enter | 保存编辑 |
| ⌘+Shift+R | 刷新当前数据 |
| ⌘, | 打开设置 |

### 1.6 关键状态机

```
Connection: Disconnected ─ connect() ─▶ Connecting ─ ok ─▶ Connected
                ▲             │                            │
                │             └─ err ─▶ Error              │
                └────────── disconnect() / lost ◀──────────┘

KeyBrowser:    Idle ─ scan() ─▶ Loading ─ done ─▶ Loaded
                                            └─ more ─▶ Loading
```

### 1.7 原型视觉规范（与 HTML 原型 1:1 对齐）

> 落地时这是 **Vue 组件复刻的硬性参考**，不可随意偏离。

#### 1.7.1 桌面壁纸与窗口

| 属性 | 值 |
|---|---|
| 桌面背景 | 多层径向渐变叠加：左上 `#ff6b9d`、右上 `#7c5cff`、底部 `#00d4ff`，基底 `linear-gradient(135deg, #1a1a2e → #16213e → #0f3460)` |
| 窗口最大宽 | 1400px |
| 窗口最小高 | 720px；默认高 `calc(100vh - 80px)` |
| 圆角 | 12px |
| 阴影 | `0 20px 60px rgba(0,0,0,0.4)` + 内描边 0.5px |

#### 1.7.2 标题栏（Titlebar 38px）

- 背景渐变 `#e8e8ed → #d8d8dc`，底部 1px 边框
- **红绿灯**：12×12px、圆角 50%、0.5px 深色边框
  - 关闭 `#ff5f57` → 触发 `window-shake`（0.4s）
  - 最小化 `#febc2e` → 触发 `window-minimize`（0.5s）
  - 最大化 `#28c840` → 切换 `window-maximize`
  - 悬停红绿灯组时按钮内显示 `× − +`
- **标题**：居中绝对定位，红色 Redis 图标 + "Seven Redis Nav" + 灰色副标 "— production-cluster-01"
- **右侧操作**：刷新 `ri-refresh-line` / 分享 `ri-share-line`

#### 1.7.3 工具栏（Toolbar 48px）

- 背景 `#fbfbfd`，底部 1px 边框
- **6 个 Tab 按钮**：未激活灰色文字，激活态白底 + 红字 + 阴影；切换 transition 0.15s
- **全局搜索**：弹性中区，最大 360px，placeholder `搜索键、命令或设置...`，右侧快捷键 chip `⌘K`，聚焦时蓝色光晕
- **连接状态指示**：绿色脉冲圆点（@keyframes pulse 2s 循环）+ "已连接" + `+` 新建连接

#### 1.7.4 侧边栏（Sidebar 240px）

- 背景 `#f2f2f4`，右边框 1px
- 三个区：**连接列表 / 数据库列表 / 用户信息**（底部固定）
- 连接项：状态圆点（online 绿 / warning 黄 / offline 灰）+ 名称 + `host:port`（等宽）+ 版本徽章（红底白字）
- DB 项：`ri-database-line` 图标 + `DB n` + 键数量（千分位等宽）
- **用户头像加载**：尝试 `/ts:auth/tauth/info.ashx`，失败回退到红橙渐变 SVG "R" 占位

#### 1.7.5 键面板（KeyPanel 320px）

- 背景白，右边框 1px
- 顶部：等宽搜索框 `键匹配模式 (例: user:*)` + 类型下拉 + `+` / 刷新 / `⋯`
- 统计行：`🔑 N 个键 · 内存 X · 扫描 100%`
- **键项**：5 列布局 — 类型徽章 / 键名（等宽超长省略）/ TTL / 大小
- **类型颜色**（与原型 `style.css` 一致）：

| 类型 | 背景 | 文字 |
|---|---|---|
| String | `#dbeafe` | `#1e40af` |
| Hash   | `#fef3c7` | `#92400e` |
| List   | `#dcfce7` | `#166534` |
| Set    | `#f3e8ff` | `#6b21a8` |
| ZSet   | `#fce7f3` | `#9f1239` |
| Stream | `#cffafe` | `#155e75` |

- 选中：浅红背景 + 红色左边框
- 空态：`ri-inbox-line` 大图标 + "没有匹配的键"
- 底部分页：`< 第 1 / N 页 >`

#### 1.7.6 状态栏（Statusbar 28px）

- 背景 `#e8e8ed`，顶部 1px 边框
- 左：`🟢 host:port · Redis 7.2.4 · DB 0 / 16`
- 右：`CPU % · RAM used/total · ⚡ ops/s · ⏱ Uptime`

#### 1.7.8 品牌色与数据类型色

- Primary：Redis 红 `#DC382D`
- Success/Warning/Danger/Info：`#34C759 / #FF9500 / #FF3B30 / #007AFF`
- 暗色背景：`#1E1E2E / #252536 / #2D2D44 / #363650`
- 浅色背景：`#F5F5F7 / #FFFFFF / #EEF0F4`

### 1.8 6 Tab 工作区详细交互

#### 1.8.1 浏览器（Browser）— 键详情

```
┌ 详情头：[类型图标] 键名(等宽粗) [类型徽章] [📋复制键名][⏱TTL][✏️重命名][🗑️删除] ┐
├ 元数据栏（6 项浅灰背景）：类型 / TTL / 大小 / 编码 / 元素数 / DB                ┤
├ 子 Tab：[数据] [原始] [历史] [相关命令]                                       ┤
└ Tab 内容区：                                                                  ┘
```

- **TTL 格式化规则**（与原型 `formatTTL` 完全一致）：
  - `< 0` → "永久（无过期）"
  - `> 86400` → "X 天 X 小时"
  - `> 3600` → "X 小时 X 分钟"
  - `> 60` → "X 分钟 X 秒"
  - 其他 → "X 秒"
- **数据 Tab**：三列网格 `200px 1fr 100px`（字段/索引｜值｜操作）。操作按钮 hover 才显（opacity 0→1）
- **原始 Tab**：深色代码块，JSON 高亮（`.json-key/.json-str/.json-num/.json-bool/.json-null`）
- **历史 Tab**：`70px 70px 140px 1fr`（时间｜操作徽章 CREATE/UPDATE/EXPIRE/DELETE｜字段｜描述）
- **相关命令 Tab**：卡片网格 `minmax(280px,1fr)`，根据当前 Key 类型动态生成（Hash → HGET/HSET/HGETALL/HDEL/HKEYS/HLEN）；卡片悬停红边

#### 1.8.2 命令行（CLI）

| 区域 | 背景 | 文字 |
|---|---|---|
| 头部 | `#2c2c2e` | `#f5f5f7` |
| 输出 | `#1d1d1f` | `#f5f5f7` |
| 输入 | `#252527` | `#fff`（光标 `#34c759`） |
| 快捷键提示 | `#f9f9fb` | `#8e8e93` |

- 自动聚焦；Enter 执行；`CLEAR` 清屏；预置 3 组 PING/INFO/DBSIZE 历史
- Phase 1+ 真实接入：后端 `cli_exec` 透传，输出按 RESP 类型着色（错误红 / 简单字符串绿 / 整数橙 / 批量数组缩进）
- 危险命令拦截：`KEYS * / MONITOR / FLUSHDB / FLUSHALL / SHUTDOWN / DEBUG SLEEP` 弹"是否继续"

#### 1.8.3 监控（Monitor）

- 头部：脉冲图标 + "实时监控" + 时间范围切换 `1h / 6h(默认) / 24h / 7d`
- **4 张指标卡**（4 列自适应网格）：

| 指标 | 名称 | 颜色 | 数据源 |
|---|---|---|---|
| 每秒操作数 | OPS/S | `#3b82f6` | `INFO stats.instantaneous_ops_per_sec` |
| 已使用内存 | MB | `#a855f7` | `INFO memory.used_memory` |
| 客户端连接数 | conns | `#10b981` | `INFO clients.connected_clients` |
| 命中率 | % | `#f59e0b` | `keyspace_hits / (hits+misses)` |

- 趋势图采样 40 点（HiDPI Retina + 渐变填充 + 末端圆点），与原型 Canvas 视觉一致；落地时改用 ECharts 但**视觉风格 1:1 复刻**
- **服务器信息卡**：版本 / OS / PID / 端口 / Uptime / 角色（绿）/ 从节点数 / AOF / 最近 RDB
- **键空间统计卡**（2×4 网格）：DB0~3 键数 / 带 TTL / 永久 / 今日过期 / 未命中率
- **客户端列表**：地址 / 最近命令 / 时长（6 条）

#### 1.8.4 慢查询（Slowlog）

- 头部：阈值信息 + 刷新 / 导出 / 清空
- 4 张统计卡：总条数 / 平均耗时 / 最长耗时 / 最频繁命令
- 表格 5 列网格 `70 80 90 1fr 180`（ID / 时间 / 耗时 / 命令 / 客户端）
- **耗时分级徽章**：

| 等级 | 阈值 | 背景 | 文字 |
|---|---|---|---|
| normal | ≤ 60ms | `#dcfce7` | 深绿 |
| warning | 60–100ms | `#fed7aa` | 深橙 |
| critical | > 100ms | `#fee2e2` | 深红 |

#### 1.8.5 发布订阅（Pub/Sub）

- 二级布局：左侧频道列表 260px + 右侧主区
- **频道列表项**：蓝色 `ri-rss-line` + 频道名（等宽）+ 订阅者数徽章（蓝边白底）+ 最近消息时间
- **发布区**：频道输入（默认 `news.tech`）+ 消息输入 + 红色 `🚀 发布` 按钮；空消息禁用
- **实时消息流**：深色 `#1d1d1f`，4 列网格 `80 150 1fr 60`（时间｜频道｜内容｜方向）
  - 接收 `↓ SUB`（绿色频道名）/ 发送 `↑ PUB`（橙色频道名）
  - HTML 内容 `escapeHtml()` 防 XSS
- 顶部状态：绿色脉冲 + "监听中" + 暂停 / 清空

#### 1.8.6 配置（Config）

- 二级布局：左侧 200px 分组导航 + 右侧配置项列表
- **5 个分组（共 17 项）**：内存(3) / 持久化(4) / 网络(5) / 安全(2) / 复制(3)
- **每个配置项行**：键名（紫色等宽粗）+ 描述 / 输入框 + 保存 ✓ + 重置 ↩
- 输入框聚焦：白底红边 + 红色光晕
- 保存动作：`CONFIG SET k v`，可选勾选 "同时持久化（CONFIG REWRITE）"

### 1.9 动效清单（与原型一致）

| 动效 | 类名 / Keyframes | 时长 | 触发 |
|---|---|---|---|
| 连接状态脉冲 | `@keyframes pulse` | 2s 无限 | 页面加载 |
| 窗口抖动 | `@keyframes window-shake` | 0.4s | 关闭按钮 |
| 窗口最小化 | `.window-minimize` | 0.5s | 最小化按钮 |
| 窗口最大化 | `.window-maximize` | 即时 | 最大化按钮 |
| Tab 高亮 | `.tool-btn.active` | 0.15s | 切 Tab |
| 键项悬停 | `.key-item:hover` | 0.12s | 鼠标悬停 |
| 字段操作显隐 | `.fr-action` opacity | 0.15s | 行 hover |
| 命令卡悬停 | `.cmd-card:hover` | 0.15s | 卡片 hover |
| 搜索聚焦光晕 | `.toolbar-search:focus-within` | 0.15s | 输入框聚焦 |
| 配置输入聚焦 | `.config-value:focus` | 0.15s | 输入框聚焦 |

### 1.10 响应式策略（与原型一致）

| 断点 | 布局 |
|---|---|
| ≥ 1100px | 三栏：240 + 320 + 自适应 |
| 900–1100px | 三栏压缩：220 + 280 + 自适应 |
| ≤ 900px | 单栏纵向；侧栏 ≤180px、键面板 ≤300px |

---

## 2. 技术架构

### 2.1 技术选型最终版

| 层 | 选型 | 关键理由 |
|---|---|---|
| 桌面壳 | **Tauri v2** | 体积小（~10MB）、原生 WebView、Rust IPC |
| 后端语言 | **Rust 2021** | 性能、内存安全、redis-rs 生态成熟 |
| Redis 驱动 | **redis-rs 0.27+**（含 `aio` `cluster-async` `tokio-comp`） | 异步、Cluster/Sentinel 支持 |
| 异步运行时 | **tokio 1.x** | Tauri / redis-rs 标准 |
| 前端框架 | **Vue 3.4 + `<script setup>` + TS strict** | 组件化、生态、TS 友好 |
| UI 库 | **TDesign Vue Next** | 企业级一致性、表格/对话框等成熟 |
| 原子化 CSS | **Tailwind CSS 3** | 与原型一致、快速对齐 |
| 状态管理 | **Pinia** | 模块化、TS 友好 |
| 构建 | **Vite 5** | Tauri 官方推荐 |
| 图表 | **ECharts 5** | 监控趋势图 |
| 代码编辑 | **CodeMirror 6** | CLI 输入、Lua 编辑器、JSON 查看 |
| SSH 隧道 | **russh** 或 **openssh** crate | 纯 Rust，跨平台 |
| 加密存储 | **macOS Keychain（security-framework）** + AES-256（aes-gcm） | 密码不落盘明文 |
| 持久化 | **SQLite（sqlx）** | 连接配置、CLI 历史、设置 |
| 日志 | **tracing + tracing-subscriber** | 结构化日志 |
| 序列化 | **serde / serde_json** | IPC 数据交换 |

### 2.2 总体架构图

```
┌────────────────────────────── macOS App (Tauri) ──────────────────────────────┐
│                                                                               │
│  ┌──────────────────────── Frontend (WebView) ────────────────────────────┐  │
│  │                                                                         │  │
│  │   Vue 3 Pages                                                           │  │
│  │   ├── MainLayout.vue (Titlebar / Toolbar / 3-Pane / Statusbar)          │  │
│  │   ├── workspaces/                                                       │  │
│  │   │     ├── BrowserWorkspace.vue   (key detail + viewers/editors)       │  │
│  │   │     ├── CliWorkspace.vue       (terminal)                           │  │
│  │   │     ├── MonitorWorkspace.vue   (charts + cards)                     │  │
│  │   │     ├── SlowlogWorkspace.vue                                        │  │
│  │   │     ├── PubsubWorkspace.vue                                         │  │
│  │   │     └── ConfigWorkspace.vue                                         │  │
│  │   └── dialogs/ (ConnectionForm / TtlEdit / Rename / Confirm ...)        │  │
│  │                                                                         │  │
│  │   Pinia Stores                                                          │  │
│  │   ├── useConnectionStore   (连接列表 / 当前连接 / DB)                    │  │
│  │   ├── useKeyBrowserStore   (扫描状态 / 当前键 / 过滤)                    │  │
│  │   ├── useTerminalStore     (CLI 历史 / 多 Tab)                           │  │
│  │   ├── useMonitorStore      (采样数据 / 时间范围)                         │  │
│  │   ├── usePubsubStore       (订阅频道 / 消息流)                           │  │
│  │   └── useSettingsStore     (主题 / 字体 / 快捷键)                        │  │
│  │                                                                         │  │
│  │   Composables                                                           │  │
│  │   ├── useIpc()         统一封装 invoke + listen                          │  │
│  │   ├── useShortcut()    全局快捷键                                        │  │
│  │   ├── useKeyTree()     键树拼装 / 虚拟滚动                                │  │
│  │   └── useTypeRenderer() 数据类型 → 查看器映射                            │  │
│  └─────────────────────────────────┬───────────────────────────────────────┘  │
│                                    │ Tauri IPC (invoke / event)              │
│  ┌─────────────────────────────────▼───────────────────────────────────────┐  │
│  │                       Rust Backend (src-tauri)                          │  │
│  │                                                                         │  │
│  │   commands/   (IPC 入口 — 仅做参数校验与转发)                            │  │
│  │     connection.rs  data.rs  monitor.rs  terminal.rs  pubsub.rs          │  │
│  │     slowlog.rs     config.rs  tools.rs                                  │  │
│  │                                                                         │  │
│  │   services/   (业务逻辑 — 持有连接池、订阅句柄、采样任务)                 │  │
│  │     connection_manager   (HashMap<ConnId, ConnectionMultiplexer>)        │  │
│  │     key_browser          (SCAN 游标管理 / 类型探测)                      │  │
│  │     data_ops             (CRUD / TTL / 批量)                            │  │
│  │     monitor              (周期采样任务 / Event 推送)                     │  │
│  │     pubsub               (订阅任务 / Event 推送)                         │  │
│  │     terminal             (命令解析 / 危险命令拦截)                       │  │
│  │     ssh_tunnel           (russh 隧道 / 端口转发)                         │  │
│  │                                                                         │  │
│  │   models/     ConnectionConfig / RedisValue / Metrics / SlowlogEntry    │  │
│  │   utils/      crypto (AES-GCM) / keychain / config_store (sqlx)         │  │
│  │   error.rs    AppError + IpcError（统一错误码）                          │  │
│  │                                                                         │  │
│  │                ┌──── redis-rs (tokio aio) ────┐                          │  │
│  │                │   Standalone / Sentinel / Cluster                      │  │
│  │                └────────────┬─────────────────┘                          │  │
│  └─────────────────────────────┼─────────────────────────────────────────┘    │
└────────────────────────────────┼─────────────────────────────────────────────┘
                                 │
                          ┌──────▼──────┐
                          │ Redis Server│
                          └─────────────┘
```

### 2.3 IPC 接口契约（节选 v0.1）

> 命名约定：`{domain}_{verb}`，错误统一 `Result<T, IpcError>`。

| Command | 参数 | 返回 | 说明 |
|---|---|---|---|
| `connection_list` | — | `Vec<ConnectionMeta>` | 列出所有保存的连接 |
| `connection_save` | `ConnectionConfig` | `ConnId` | 新建/更新连接（密码进 Keychain） |
| `connection_test` | `ConnectionConfig` | `PingResult` | PING + 版本探测 |
| `connection_open` | `ConnId` | `SessionId` | 建立连接，返回会话 ID |
| `connection_close` | `SessionId` | `()` | 关闭并释放 |
| `db_select` | `SessionId, db: u8` | `DbStat { keys, expires }` | 切换 DB |
| `keys_scan` | `SessionId, db, cursor, match, count, type?` | `ScanPage { cursor, items: Vec<KeyMeta> }` | SCAN 分页 |
| `key_get` | `SessionId, db, key` | `KeyDetail { type, ttl, encoding, mem, value }` | 智能取值 |
| `key_set` | `SessionId, db, key, value, options` | `()` | 写入（按类型分发） |
| `key_delete` | `SessionId, db, keys: Vec<String>` | `u64` | 批量删除 |
| `key_rename` | `SessionId, db, src, dst` | `()` | RENAME |
| `key_ttl_set` | `SessionId, db, key, ttl_secs` | `()` | EXPIRE / PERSIST |
| `cli_exec` | `SessionId, db, command, args` | `RedisReply` | 通用命令执行 |
| `cli_history_get` | — | `Vec<String>` | 历史 |
| `monitor_start` | `SessionId, interval_ms` | `TaskId`（事件流：`monitor:tick`） | 启动采样 |
| `monitor_stop` | `TaskId` | `()` | 停止 |
| `slowlog_get` | `SessionId, count` | `Vec<SlowlogEntry>` | SLOWLOG GET |
| `slowlog_reset` | `SessionId` | `()` | SLOWLOG RESET |
| `pubsub_subscribe` | `SessionId, channels: Vec<String>` | `TaskId`（事件流：`pubsub:msg`） | SUBSCRIBE |
| `pubsub_publish` | `SessionId, channel, message` | `u64` | 接收者数 |
| `config_get` | `SessionId, pattern` | `HashMap<String,String>` | CONFIG GET |
| `config_set` | `SessionId, key, value, persist: bool` | `()` | CONFIG SET (+REWRITE) |

### 2.4 事件流（Backend → Frontend）

| Event | Payload | 用途 |
|---|---|---|
| `monitor:tick` | `MetricsSnapshot` | 监控面板 |
| `pubsub:msg` | `PubsubMessage` | 发布订阅消息流 |
| `connection:state` | `{ id, state }` | 状态点 / 状态栏更新 |
| `terminal:output` | `{ tabId, chunk }` | CLI 流式输出（如 MONITOR） |
| `app:notify` | `{ level, message }` | 全局 Toast |

### 2.5 安全设计

- **密码**：AES-256-GCM 加密 + macOS Keychain 存储，仅在内存中以 `secrecy::Secret<String>` 持有
- **连接**：TLS（rustls）+ SSH 隧道（russh），证书与私钥可指定文件或 Keychain 项
- **危险命令**：后端白名单拦截（`FLUSHDB/FLUSHALL/CONFIG SET requirepass/SHUTDOWN/DEBUG`），需前端二次确认 token
- **审计日志**：写操作落本地 SQLite（连接 ID、时间、命令、影响键数），可在设置中查看与导出
- **数据脱敏**：可在设置中按 key 模式配置掩码（如 `*token*` 默认 `***`）

### 2.6 性能与稳定性策略

| 场景 | 策略 |
|---|---|
| 百万级 Key 浏览 | 强制使用 SCAN，前端虚拟滚动（vue-virtual-scroller），按前缀懒加载子树 |
| 大 Key 读取 | `MEMORY USAGE` 预估，>1MB 弹"分片读取"提示，`HSCAN/SSCAN/ZSCAN/LRANGE` 分页 |
| 长连接 | 心跳 PING（默认 30s）+ 指数退避重连 |
| 监控采样 | 仅当 Tab 激活时运行；切走暂停；离开页面 60s 释放 |
| CLI 大输出 | 输出 > 1000 行启用虚拟滚动；> 10MB 提示"截断/导出文件" |
| 连接池 | 单连接复用 `ConnectionMultiplexer`，CLI Tab 独立连接（避免阻塞订阅） |

---

## 3. 项目目录（最终版）

> 在原 `project-structure.md` 基础上，按"6 Tab 工作区"重构 `views/components/stores`。

```
redis-nav/
├── docs/                          # 文档（含本文档与原型）
├── src-tauri/                     # Rust 后端
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── capabilities/
│   ├── icons/
│   └── src/
│       ├── main.rs / lib.rs
│       ├── commands/              # IPC 入口
│       │   ├── connection.rs
│       │   ├── data.rs
│       │   ├── terminal.rs
│       │   ├── monitor.rs
│       │   ├── slowlog.rs
│       │   ├── pubsub.rs
│       │   ├── config.rs
│       │   └── tools.rs
│       ├── services/              # 业务逻辑
│       │   ├── connection_manager.rs
│       │   ├── key_browser.rs
│       │   ├── data_ops.rs
│       │   ├── terminal.rs
│       │   ├── monitor.rs
│       │   ├── pubsub.rs
│       │   ├── slowlog.rs
│       │   ├── config_ops.rs
│       │   └── ssh_tunnel.rs
│       ├── models/
│       ├── utils/                 # crypto / keychain / config_store
│       └── error.rs
│
├── src/                           # Vue 3 前端
│   ├── App.vue / main.ts
│   ├── router/
│   ├── ipc/                       # IPC 封装层（一处维护命令名 + 类型）
│   │   ├── index.ts
│   │   ├── connection.ts
│   │   ├── data.ts
│   │   ├── monitor.ts
│   │   ├── terminal.ts
│   │   ├── pubsub.ts
│   │   ├── slowlog.ts
│   │   └── config.ts
│   ├── stores/                    # Pinia
│   │   ├── connection.ts
│   │   ├── keyBrowser.ts
│   │   ├── workspace.ts           # activeTab + workspace state
│   │   ├── terminal.ts
│   │   ├── monitor.ts
│   │   ├── pubsub.ts
│   │   ├── slowlog.ts
│   │   ├── config.ts
│   │   └── settings.ts
│   ├── composables/
│   │   ├── useIpc.ts
│   │   ├── useShortcut.ts
│   │   ├── useKeyTree.ts
│   │   ├── useToast.ts
│   │   └── useTypeRenderer.ts
│   ├── views/
│   │   ├── MainLayout.vue
│   │   ├── Welcome.vue
│   │   └── Settings.vue
│   ├── components/
│   │   ├── window/                # Titlebar / Toolbar / Statusbar
│   │   ├── sidebar/               # ConnectionList / DbList / UserCard
│   │   ├── keypanel/              # KeySearch / KeyList / KeyPagination
│   │   ├── workspaces/
│   │   │   ├── browser/           # KeyDetailHeader / Meta / Tabs / Viewers / Editors
│   │   │   ├── cli/               # CliTerminal / CliInput
│   │   │   ├── monitor/           # MetricCard / TrendChart / ServerInfo / Keyspace / Clients
│   │   │   ├── slowlog/
│   │   │   ├── pubsub/            # ChannelList / Publisher / MessageStream
│   │   │   └── config/
│   │   ├── dialogs/               # ConnectionForm / Confirm / RenameKey / TtlEdit
│   │   └── common/                # StatCard / TypeTag / EmptyState / SearchInput
│   ├── styles/                    # variables.css / dark.css / light.css
│   └── types/                     # 与 Rust 模型一一对应的 d.ts
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── package.json
└── README.md
```

> 提示：`docs/components/*.js`、`docs/data.js`、`docs/app.js` 是**原型阶段产物**，正式开发用 Vue 3 重写到 `src/components/workspaces/*` 下，但所有 DOM 结构与样式可作为 1:1 对照参考。

---

## 4. 开发计划（Phase 0 → Phase 5）

> 总周期 **20 周**（与 product-design.md 对齐），单人节奏。每个 Phase 末交付**可运行 dmg + Demo 视频 + Release Note**。

### Phase 0 · 工程脚手架（1 周）

**目标**：跑通最小闭环 `Vue → invoke → Rust → redis-rs → PONG`。

- [ ] `pnpm create tauri-app` 初始化（vue-ts 模板）
- [ ] 接入 TDesign Vue Next + Tailwind + Pinia + Router + ECharts
- [ ] 接入 redis-rs / tokio / serde / tracing / sqlx / aes-gcm / security-framework
- [ ] 制定 `error.rs` 与 IPC 错误码规范
- [ ] CI：`cargo fmt/clippy + pnpm lint + tauri build` 在 GitHub Actions
- [ ] 完成第一个端到端命令：`connection_test`（前端按钮 → 弹 Toast）

**交付**：可在本地启动空壳 + 测试连接成功。

### Phase 1 · MVP：连接 + 浏览 + CRUD + CLI（4 周，对应 v0.1）

**对齐**：`product-design.md` P0（M-01 ~ M-07）。

- [ ] **窗口框架**：1:1 还原原型的 Titlebar/Toolbar/Sidebar/KeyPanel/Statusbar
- [ ] **连接管理**：列表 / 新建表单（含分组）/ 测试 / Keychain 存储 / 导入导出
- [ ] **DB 切换**：`DBSIZE` + `INFO keyspace`
- [ ] **键浏览**：SCAN 分页 + 虚拟滚动 + 类型筛选 + pattern 搜索
- [ ] **数据查看器**：String / Hash / List / Set / ZSet（5 种基础类型，原型同款）
- [ ] **CRUD**：行内编辑 / 弹窗编辑 / 删除（含确认）/ 重命名 / TTL 设置
- [ ] **CLI**：基础命令执行 + 命令历史（↑↓）+ ⌘L 清屏 + 输出着色
- [ ] **快捷键体系**：⌘K / ⌘N / ⌘F / ⌘1 / ⌘2 / ⌘+Enter / ⌘L

**验收用例**：
1. 新建连接 → 浏览 1k 个 Key → 编辑 Hash 字段 → CLI 执行 `KEYS *` → 全部 < 1s 响应
2. 关闭重启 App，连接配置与密码持久化
3. 误删确认弹窗触发，输入键名才能 DELETE

### Phase 2 · 进阶连接 + 批量 + Server Info + 慢查询（4 周，v0.2）

**对齐**：E-01 ~ E-07。

- [ ] **SSH 隧道**（russh）：表单字段 + 测试 + 自动重连
- [ ] **TLS**（rustls）：CA / Cert / Key 文件选择
- [ ] **Sentinel / Cluster** 模式接入（redis-rs cluster-async）
- [ ] **批量操作**：⌘+点击多选 / Shift 范围 / ⌘A 全选 → 批量删除 / 批量改 TTL / 批量复制
- [ ] **监控 Tab**：4 指标卡 + 趋势图（ECharts）+ 服务器信息 + Keyspace + ClientList
- [ ] **慢查询 Tab**：统计卡 + 表格 + 时间排序 + 导出 CSV / JSON

**验收用例**：
1. 通过跳板机 SSH 连上内网 Redis，浏览数据正常
2. 监控 Tab 持续运行 1 小时无内存泄漏（< 150MB 稳态）
3. 选中 200 个 Key 批量删除，进度条 + 失败列表

### Phase 3 · Pub/Sub + 配置 + 扩展类型 + JSON（4 周，v0.3）

**对齐**：E-08 ~ E-10 + 配置 Tab。

- [ ] **Pub/Sub Tab**：频道列表 / 订阅 / 实时消息流（Tauri Event）/ 发布 / 暂停/清空
- [ ] **配置 Tab**：`CONFIG GET *` 分组（按内置规则）/ 编辑 / 保存 / `CONFIG REWRITE`
- [ ] **扩展类型查看器**：Stream（XRANGE 分页 + Consumer Groups）/ Bitmap（位图查看）/ HyperLogLog
- [ ] **JSON 智能识别**：String 自动检测 → JSON 美化 / 折叠 / 搜索（CodeMirror 6）
- [ ] **二进制数据**：Hex / Base64 / 文本三视图

**验收用例**：
1. 订阅 `__keyspace@0__:*`，收到 keyspace 事件
2. 修改 `maxmemory` 后 `CONFIG REWRITE`，重启验证生效

### Phase 4 · 高级工具 + 多 Tab CLI + 健康检查（4 周，v0.4）

**对齐**：A-01 ~ A-08。

- [ ] **Lua 脚本编辑器**（CodeMirror 6 + Lua mode）：编辑 / `EVAL` / 历史 / KEYS+ARGV 表单
- [ ] **数据导入导出**：JSON 导出当前 DB / 选中键集合；JSON 导入；RDB 解析（只读，rdb-rs）
- [ ] **大 Key 扫描**：后台任务，`MEMORY USAGE` 抽样 + Top 100 报告
- [ ] **过期 Key 扫描**：TTL 分布直方图
- [ ] **健康检查报告**：综合 INFO / SLOWLOG / Keyspace / Client，输出 Markdown / PDF
- [ ] **多 Tab CLI**：⌘T 新开 Tab，标签页可关闭/拖拽
- [ ] **数据脱敏规则**：设置面板配置 + 实时生效
- [ ] **快捷键自定义**：设置面板可视化绑定

**验收用例**：
1. 一键生成健康报告，10 项核心指标完整
2. 大 Key 扫描 100w Key 实例，< 60s 给出 Top100

### Phase 5 · 打磨 + 国际化 + 发布（3 周，v1.0）

- [ ] **主题**：浅/深/跟随系统 完整覆盖（含 ECharts 主题）
- [ ] **i18n**：vue-i18n，中/英两套
- [ ] **更新通道**：Tauri Updater（GitHub Releases）
- [ ] **崩溃上报**：Sentry（可选）/ 本地日志导出
- [ ] **性能优化**：启动 < 1s、空闲内存 < 100MB
- [ ] **打包签名**：Apple Developer ID 签名 + 公证（notarization）
- [ ] **官网 + 文档站**（VitePress）
- [ ] **App Store 提审**（可选）

**验收**：M1/M2/Intel 三平台 dmg 全部通过 Gatekeeper 校验。

---

## 5. 里程碑总表

| 版本 | 周次 | 关键能力 | 适用人群 |
|---|---|---|---|
| v0.1 | W1-5 | 连接 + 浏览 + CRUD + CLI | 个人开发者本地 Redis |
| v0.2 | W6-9 | SSH/TLS + 批量 + Server Info + Slowlog | 后端 / SRE 接入线上 |
| v0.3 | W10-13 | Pub/Sub + 配置 + 扩展类型 + JSON | 中大型团队日常运维 |
| v0.4 | W14-17 | Lua + 导入导出 + 健康检查 + 多 Tab CLI | DBA / 架构师 |
| v1.0 | W18-20 | 主题 + i18n + 签名 + 文档 | 公开发布 |

---

## 6. 风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| 大 Key 阻塞 | App 卡死 | 后端硬限超时 + 取消 token；前端禁用同步加载 |
| MONITOR 命令洪流 | 内存爆 | CLI 默认拦截 + 弹"是否启用流式查看（含截断）" |
| Cluster 跨节点 SCAN | 数据不全 | 多节点并发 SCAN 后归并；前端进度条按节点显示 |
| Tauri WebView 兼容 | macOS 12 以下 WKWebView 较老 | 文档声明最低 macOS 12；ECharts 启用降级渲染 |
| Keychain 权限弹窗 | 用户首次困扰 | 首次保存前文案说明；提供"会话内存模式"选项 |
| russh 复杂场景 | SSH 跳板 + 公私钥多样 | 先支持密码 + 单密钥；ProxyJump 留 v0.3 |

---

## 7. 与原型的对应关系（开发对照表）

| 原型文件 | Vue 落地位置 |
|---|---|
| `index.html` 整体布局 | `src/views/MainLayout.vue` |
| Titlebar / Toolbar / Statusbar | `src/components/window/*` |
| 侧边栏连接 + DB | `src/components/sidebar/*` |
| 中间键面板 | `src/components/keypanel/*` |
| `components/keyDetail.js` | `src/components/workspaces/browser/*` |
| `components/cli.js` | `src/components/workspaces/cli/*` |
| `components/monitor.js` | `src/components/workspaces/monitor/*` |
| `components/slowlog.js` | `src/components/workspaces/slowlog/*` |
| `components/pubsub.js` | `src/components/workspaces/pubsub/*` |
| `components/config.js` | `src/components/workspaces/config/*` |
| `data.js` | 仅在 Storybook / 单元测试中保留作 fixtures |
| `style.css` + `style-ext.css` | 拆解为 Tailwind utility + 少量 `:deep` 样式覆盖 |

---

## 8. 下一步建议

1. **本周** 先完成 Phase 0：搭好工程，跑通 PING 闭环
2. **同步重构原型** 把 `docs/index.html` 抽出 1 张完整的 Figma 或截图清单（以原型图 + img 为基线）
3. **明确 v0.1 验收清单** 后开 Phase 1，建议把 7 个 P0 功能各拆成独立 PR，便于 Review

> 如需我下一步直接：① 生成 Phase 0 的 Tauri+Vue 脚手架代码；② 输出 IPC 类型 d.ts 与 Rust models 的对照骨架；③ 把原型 6 个组件转换成 Vue 3 组件；告诉我从哪个开始即可。
