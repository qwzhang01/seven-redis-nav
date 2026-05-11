# 五一假期，我用一天时间给自己写了一个 Redis 管理工具

> 作者：avinzhang
> 关键词：AI 编程 / Tauri / Vue 3 / Rust / 规格驱动开发（Spec-Driven Development）
> 项目仓库：[seven-redis-nav](https://github.com/qwzhang01/seven-redis-nav) · MIT License

---

## 一、缘起：一个被工具困住的后端工程师

作为一个常年和 Redis 打交道的后端工程师，我对市面上的 Redis 管理工具一直有一种"将就"的感觉。

- **Redis Desktop Manager**：用着卡，新版本还要付费；
- **Another Redis Desktop Manager**：免费，但 UI 风格在 Mac 上看着别扭；
- **TablePlus / DBeaver**：通用，但对 Redis 的支持总是隔着一层；
- **官方 RedisInsight**：功能全，但启动慢、体积大、强制登录；
- **命令行 `redis-cli`**：依然最香，但浏览大量 Key 还是不方便。

我心里一直有个清单："如果我自己写一个，它应该长什么样？"——直到 2026 年五一假期，我决定动手。

**最终成果**：一款叫 `Seven Redis Nav` 的 macOS 原生 Redis 管理工具，6 大工作区、SSH 隧道、TLS 加密、批量操作、Lua 脚本、健康报告，覆盖了我个人日常 90% 的使用场景。

更让我自己都有点意外的是——**从零到 v0.4，我只花了一天**。

这一天里，我没有手敲多少行代码。真正写代码的，是 AI；我做的事情，是**当好一个产品经理 + 架构师 + Code Reviewer**。

这篇文章想分享的，不是这个工具本身有多牛（它就是个个人项目），而是我用什么样的方法和 AI 大模型协作，**把"一个想法"变成"一个能跑、能用、有测试、有文档的桌面应用"**。

---

## 二、它是什么：一个"看起来像 macOS 原生应用"的 Redis 工具

先放两张图，让大家有个直观印象：

![主界面](./snapshot/image.png)

![功能界面](./snapshot/image%20copy.png)

### 2.1 核心特性一览

| 模块                    | 能力                                                                  |
| ----------------------- | --------------------------------------------------------------------- |
| 🔌 多连接管理           | 保存、切换多个 Redis 连接，密码通过 **macOS Keychain** 加密存储       |
| 🔐 SSH 隧道             | 通过跳板机访问内网 Redis，支持密码 / 私钥（含加密私钥）认证           |
| 🔒 TLS 加密             | 支持 TLS/SSL 连接，可配 CA 证书、双向 TLS、最低 TLS 版本              |
| 🗂️ Key 浏览器           | String / Hash / List / Set / ZSet 五种类型查看与编辑，支持虚拟滚动    |
| 💻 CLI 终端             | 内置命令行，命令历史、自动补全、危险命令二次确认                      |
| 📊 实时监控             | 4 大指标卡 + ECharts 趋势图 + INFO/CLIENT LIST 周期采样               |
| 📡 Pub/Sub              | 可视化订阅频道、实时消息流                                            |
| 🐢 慢日志               | SLOWLOG 统计 + 耗时分级展示                                           |
| ⚙️ 配置中心             | 在线查看 / 修改 Redis CONFIG，支持 CONFIG REWRITE 持久化              |
| 🧰 高级工具             | Lua 脚本编辑器、批量操作、大 Key 扫描、健康检查报告、JSON/二进制视图   |
| 📤 配置导入导出         | JSON 格式，密码不导出，方便团队共享                                   |

### 2.2 技术栈

| 层级       | 技术                                                                    |
| ---------- | ----------------------------------------------------------------------- |
| 桌面框架   | **Tauri 2**（10MB 级别的原生壳，比 Electron 轻一个数量级）              |
| 前端       | **Vue 3 + TypeScript（strict）+ Vite 6**                                |
| UI 组件库  | **TDesign Vue Next**（腾讯出品，企业级，组件齐全）                      |
| 状态管理   | **Pinia**                                                               |
| 虚拟列表   | `@tanstack/vue-virtual`（百万 Key 也能丝滑滚动）                        |
| 后端语言   | **Rust（Stable）**                                                      |
| Redis 驱动 | `redis-rs`（tokio 异步、TLS、Cluster、Sentinel 全支持）                 |
| SSH 隧道   | `ssh2-rs`                                                               |
| 本地存储   | SQLite（via `sqlx`）+ macOS Keychain（via `security-framework`）        |
| 测试       | Vitest 3 + @vue/test-utils + Playwright                                 |

### 2.3 项目规模（一天的产出量）

```
src-tauri/src/   ── Rust 后端       约 10,000 行
src/             ── Vue + TS 前端   约 19,900 行
openspec/        ── 规格 & 设计文档 约  5,300 行
docs/            ── 产品 & 路线图   约  2,800 行
                                    ─────────────
                                    总计 ≈ 38,000 行
```

> 这个数字本身不重要，重要的是它背后的方法论。

---

## 三、为什么是"一天"：方法论决定上限

很多人看到"一天写一个桌面级管理工具"的第一反应是：**不可能**。

我自己一开始也不信。但当我用对了方法之后，我发现：**所谓"一天"，不是因为我打字快，而是因为我把"思考"和"执行"彻底分开了。**

我的方法论可以浓缩成三句话：

> 1. **不要一上来就让 AI 写代码。先和 AI 一起把规格写清楚。**
> 2. **不要让 AI 写一个大功能。把大功能拆成 OpenSpec 风格的"变更（change）"。**
> 3. **不要做信任型 review。每个变更都要让 AI 自己写 tasks.md，然后逐项打勾。**

这三条核心原则，让一个原本需要两个月的项目，被压缩到了 **24 小时**。

---

## 四、AI 协作开发的完整工作流

### 4.1 总体流程

```
                ┌──────────────────────────────────┐
                │  Step 1  产品设计                │
                │  我口述需求 → AI 写产品文档       │
                │  → docs/product-design.md         │
                └──────────────┬───────────────────┘
                               │
                ┌──────────────▼───────────────────┐
                │  Step 2  原型设计                │
                │  AI 写 HTML 高保真原型 + 交互规范 │
                │  → docs/prototype-interaction…   │
                └──────────────┬───────────────────┘
                               │
                ┌──────────────▼───────────────────┐
                │  Step 3  架构与路线图            │
                │  AI 输出技术架构 + Phase 0-5 计划 │
                │  → docs/overview-and-roadmap.md  │
                └──────────────┬───────────────────┘
                               │
                ┌──────────────▼───────────────────┐
                │  Step 4  规格驱动开发（核心）    │
                │  按 Phase 拆 14 个 OpenSpec 变更  │
                │  每个变更 = proposal+design+tasks │
                │              +specs                │
                └──────────────┬───────────────────┘
                               │
                ┌──────────────▼───────────────────┐
                │  Step 5  执行变更                │
                │  AI 按 tasks.md 逐项实现 → 我 review│
                │  → 通过后归档到 archive/          │
                └──────────────────────────────────┘
```

### 4.2 Step 1—3：先把"想清楚"这件事做完

很多人用 AI 写代码的姿势是这样的：

> "帮我写一个 Redis 管理工具的连接管理功能"

然后 AI 给一坨能跑但毫无章法的代码，下一次换个会话上下文丢了，又是一坨新风格的代码——**最终代码风格漂移、模块冲突、根本拼不起来**。

我的做法刚好反过来。**前 4 个小时我一行代码都不写**，只做这三件事：

1. **产品设计文档**（`product-design.md`）：明确要什么、不要什么。比如我明确写下"不要做 Web 版，只做 macOS 原生"——这一句话直接砍掉一大堆架构选择。
2. **HTML 高保真原型**：让 AI 直接给我一个能在浏览器里点击的 HTML 原型，里面 6 个 Tab 都长什么样、什么颜色、什么字体、什么动画，**全部固定下来**。这个原型后来变成了 Vue 组件落地的"硬性参考"。
3. **总览与路线图**（`overview-and-roadmap.md`）：和 AI 一起讨论清楚——
    - 命名（最终定为 Seven Redis Nav）；
    - 6 个工作 Tab 的边界；
    - IPC 命令契约（`{domain}_{verb}` 命名规范）；
    - 错误模型（`IpcError` / `IpcResult<T>`）；
    - Phase 0 → Phase 5 的拆分策略；
    - 性能策略（虚拟滚动、SCAN、心跳、采样暂停）；
    - 安全策略（Keychain、AES-256-GCM、危险命令拦截）。

这一步的输出物有 **2800 行 Markdown**，看起来很重，但它做了一件极其关键的事——**给后续所有 AI 调用提供了稳定的上下文**。

> 💡 **经验**：AI 模型最大的痛点不是"不会写代码"，而是"上下文丢失后写出风格不一致的代码"。
> 用 Markdown 把架构决策固化成文档，每次让 AI 写代码时把对应文档塞进上下文，AI 写出来的代码就跟出自同一个团队一样。

### 4.3 Step 4：规格驱动开发（OpenSpec 工作流）

这是整个方法论的**核心**。

我用了一个叫 **OpenSpec** 的轻量规格驱动开发工作流（spec-driven development）。它的核心思想是：

> **代码改动之前，先写一份规格变更（change proposal）；代码改动之后，把规格归档到正式 spec。**

每个变更的目录长这样：

```
openspec/changes/2026-04-30-phase-1-mvp/
├── proposal.md      # 为什么改、改了什么、影响什么
├── design.md        # 关键技术决策（带 tradeoffs）
├── tasks.md         # 任务清单（可勾选的 checklist）
└── specs/
    ├── connection-manager/spec.md   # 连接管理能力规格
    ├── key-browser/spec.md          # 键浏览能力规格
    ├── data-viewer/spec.md
    ├── data-editor/spec.md
    ├── cli-terminal/spec.md
    ├── shortcut-system/spec.md
    └── ...
```

整个项目我做了 **14 个变更**，每个变更对应一个明确的功能闭环：

```
2026-04-30-phase-0-bootstrap            ← 工程脚手架
2026-04-30-phase-1-mvp                  ← 连接 + 浏览 + CRUD + CLI
2026-04-30-phase-2-enhancement          ← 监控 + 慢日志 + 批量
2026-04-30-phase2-ssh-tls-connections   ← SSH 隧道 + TLS
2026-04-30-welcome-page-redesign        ← 欢迎页改版
2026-04-30-resizable-panel-splitters    ← 三栏拖拽
2026-04-30-native-titlebar-cleanup      ← 标题栏适配
2026-04-30-fix-keychain-double-prompt-and-biometric-auth  ← Keychain 双重弹窗修复
2026-04-30-optimize-ui-testing-performance
2026-04-30-remove-desktop-wallpaper-fullscreen-fix
2026-05-01-phase2-remaining-features
2026-05-01-phase3-v0-3-features         ← Pub/Sub + 配置 + 扩展类型
2026-05-01-phase4-v0-4-advanced-tools   ← Lua + 健康报告 + 大 Key
2026-05-01-code-review-fixes
```

每一个变更，我和 AI 的对话只有三回合：

| 回合 | 我做什么                              | AI 做什么                                            |
| ---- | ------------------------------------- | ---------------------------------------------------- |
| 1    | 描述要新增/修改的能力                 | 输出 `proposal.md` + `design.md` + `tasks.md` + `specs/` |
| 2    | review 规格、确认 tasks 拆分合理      | 按 `tasks.md` 逐项实现代码                           |
| 3    | review 代码、跑测试                   | 修复 review 中发现的问题，归档变更                   |

### 4.4 一个具体的例子：Phase 1 MVP 是怎么诞生的

举个最实在的例子。Phase 1 MVP 的 `tasks.md` 大致长这样（节选）：

```markdown
## 1. Rust 后端 — 数据库与依赖
- [x] 1.1 Cargo.toml 添加 sqlx、security-framework、uuid
- [x] 1.2 创建 migrations/001_init.sql（connections 表 + cli_history 表）
- [x] 1.3 实现 utils/db.rs：SQLite 连接池
- [x] 1.4 实现 utils/keychain.rs：macOS Keychain 密码存取
...

## 3. Rust 后端 — 连接管理服务
- [x] 3.1 定义 models/connection.rs
- [x] 3.2 实现 services/connection_manager.rs（ConnectionMultiplexer 池）
- [x] 3.3 实现 connection_open（AUTH + 存入会话池）
- [x] 3.4 实现 connection_close
- [x] 3.5 实现心跳 PING + 断连检测 + connection:state 事件推送
...
```

每一个 `tasks.md` 平均有 **40~80 个原子任务**。AI 拿到这个清单后做的事情非常机械：

> 实现 1.1 → 跑编译 → 打勾 → 实现 1.2 → 跑编译 → 打勾 ……

**这就是为什么 AI 能写出"工程感"很强的代码**：因为它写代码的过程已经变成了"按图施工"，而不是"自由发挥"。

而每条 spec 又用了 EARS 风格（Easy Approach to Requirements Syntax）：

```markdown
### Requirement: Connection session management
The system SHALL manage connection sessions using `MultiplexedConnection`.

#### Scenario: Connection lost recovery
- WHEN active connection drops (network error, Redis restart)
- THEN backend detects via failed command, emits `connection:state` event,
       frontend shows reconnecting indicator, backend attempts exponential
       backoff reconnection
```

**这种"WHEN/THEN"风格对 AI 极其友好**——它直接对应 AI 应该写的 if/else 逻辑分支和测试用例。

### 4.5 Step 5：归档——让 AI 永远记得"我们曾经做过什么"

每个变更实现完成后，我会让 AI 把它从 `openspec/changes/` 归档到 `openspec/changes/archive/`，并把里面新增/修改的能力规格沉淀到 `openspec/specs/<capability>/spec.md`。

最终 `openspec/specs/` 下沉淀了 **40 个能力规格**：

```
advanced-connection-config       cli-terminal              data-viewer
app-shell                        component-library         dev-toolchain
binary-data-views                connection-manager        dynamic-title
bitmap-viewer                    connection-ping           health-check-report
bulk-key-operations              connection-validation     ipc-foundation
data-editor                      data-import-export        key-analyzer
data-masking                     key-browser               keychain-biometric-auth
lua-script-editor                monitor-metrics-dashboard pubsub-workspace
performance-optimization         ...
```

下次再加新功能时，把相关 spec 喂给 AI，它对项目的理解**和我自己一样深**。

> 💡 这就是规格驱动开发的真正威力：**它让"项目知识"持久化，不再依赖某个人脑子里的记忆。**

---

## 五、AI 协作中我踩过的坑和拿到的爽点

### 5.1 三个最大的爽点

**爽点一：UI 还原能力惊人**

我的设计来源是一份 HTML 高保真原型。我直接把原型 HTML 丢给 AI，让它"用 Vue 3 + TDesign 1:1 重写"。结果出乎意料地好——红绿灯、脉冲动画、字体颜色、阴影、圆角、键类型徽章的颜色，全部对得上。

**爽点二：Rust 错误处理写得比我还规范**

我让 AI 用 `thiserror` 设计了一套 `IpcError` 错误模型：

```rust
pub enum IpcError {
    ConnectionFailed { source: String },
    AuthFailed,
    NotFound,
    DangerousCommand { command: String, confirm_token: String },
    // ...
}
```

并且让前端 TypeScript 端通过 `IpcErrorKind` 同步类型——这种细节我一个人写很容易忘，AI 在规格驱动下会自己提醒"这里需要前后端对齐"。

**爽点三：危险命令护栏是 AI 主动加的**

我只是提了一句"要安全"，AI 在 design.md 里主动设计了一整套**危险命令二次确认 token 机制**：`FLUSHDB / FLUSHALL / KEYS * / CONFIG SET requirepass / SHUTDOWN / DEBUG SLEEP` 全部走白名单拦截 + token 二次确认。这种安全感，是我用其他工具时从来没有过的。

### 5.2 三个真实的坑

**坑一：Tauri JS 和 Rust 版本不匹配**

git log 里那条 `fix: resolve tauri version conflict between rust (v2.11.0) and js (v2.10.1)` 是真实事故。AI 默认拉了最新版的 `@tauri-apps/api`，但 Rust 侧 `Cargo.toml` 是另一个版本号——编译过、跑起来 IPC 全部报错。

**教训**：依赖版本必须在 Phase 0 的 `dev-toolchain` spec 里钉死，AI 后面才不会乱升级。

**坑二：Keychain 双重弹窗**

第一版实现里，**每打开一个连接，macOS Keychain 都会弹两次密码确认**。原因是 AI 在不同代码路径里各做了一次 keychain 访问。

后来我专门起了一个 `2026-04-30-fix-keychain-double-prompt-and-biometric-auth` 变更去修，并把"Keychain 访问必须通过 utils/keychain.rs 单一入口"写进了 spec。**这就是规格驱动的好处——一旦写进 spec，AI 后面不会再犯。**

**坑三：AI 生成的测试是"考试型测试"**

第一版 AI 写的单元测试覆盖率漂亮，但很多是 `expect(true).toBe(true)` 这种走过场的——专门为了让覆盖率 ≥ 70% 凑出来的。

**解决办法**：在 spec 里强制要求"测试必须基于 spec 的 Scenario，不允许凭空捏造"。AI 立刻就老实了。

---

## 六、一些可以直接抄走的实践

如果你也想用 AI 的方式做一个属于自己的工具，下面这些是我觉得**最值得抄**的实践：

### 6.1 给 AI 一个"工程基线"，而不是"自由发挥的画布"

- 在 Phase 0 把目录结构、依赖版本、命名规范、错误模型、IPC 契约**全部写死**；
- 把 ESLint / Prettier / Clippy / Cargo fmt **强制接入 CI**，AI 写不合规的代码会被自动卡掉；
- `pnpm verify` 一键跑全套校验：`lint + typecheck + cargo fmt + cargo clippy -D warnings`。

### 6.2 用 OpenSpec 把"想法"沉淀成"可执行任务"

- **每一次大改 = 一个变更目录**，proposal/design/tasks/specs 四件套；
- 任务 ≤ 2 小时一个原子单元（实在拆不下去的标"⚠️ 大块任务"）；
- 用 EARS 语法写 spec：`The system SHALL …` + `WHEN/THEN` Scenario，AI 极其吃这一套。

### 6.3 文档也是 AI 的输入，而不只是给人看的

- README、CHANGELOG、docs/overview-and-roadmap 都不是花架子，是 AI 下一次改代码的上下文；
- 每次大改后让 AI 自己更新 README——这件事写进规则后，AI 真的会主动做。

### 6.4 留一条"逃生通道"——可以随时回到代码 review

AI 写代码再爽，最终 PR review 还是必须的。我每个变更都会做下面三件事：

1. **跑 `pnpm verify`** 看 lint/clippy 是否过；
2. **跑测试** 看新功能是否真的能跑（不是测试通过就行）；
3. **抽查 1-2 个文件**看代码风格是否符合 spec。

发现问题 → 起一个 `code-review-fixes` 变更修掉，并把"AI 容易犯的错误"沉淀进 spec。

---

## 七、回到一开始的那个问题：AI 真的能"一天写一个工具"吗？

我的答案是：**可以，但不是你想的那种"一天"。**

那"一天"里：

- **4 小时**用来想清楚要做什么、不做什么、怎么拆；
- **14 小时**用来和 AI 协作出 14 个变更，每个变更 30~90 分钟；
- **3 小时**用来 code review、跑测试、改 bug；
- **3 小时**用来打包、写文档、出截图。

**真正用来"敲代码"的时间几乎是 0**——但这绝不意味着我"什么都没做"。我做的事情是：

> 把自己**从一个"程序员"，变成了一个"AI 团队的 PM + 架构师 + Tech Lead"**。

我开始相信，未来真正高产的工程师，不是"打字最快的"，也不是"算法最强的"，而是：

- 能把模糊需求**翻译成 spec** 的人；
- 能把大问题**拆成可验证小变更**的人；
- 能在 AI 自由发挥时**踩刹车守底线**的人；
- 能把项目知识**持久化进文档**的人。

这次 Seven Redis Nav 的开发，对我个人来说，不是"做了一个工具"，而是**第一次完整跑通了"AI 大模型驱动的工程化开发流程"**。这套流程在我后来做的另外几个项目（Meta Quant 量化交易、HR Recruit Crew 智能招聘）里都被复用了，都得到了类似的效果。

---

## 八、最后

> "工具是给自己用的，方法论是可以分享的。"

如果你看到这里，欢迎：

- ⭐️ 给项目点个 Star：[github.com/qwzhang01/seven-redis-nav](https://github.com/qwzhang01/seven-redis-nav)
- 📥 下载体验（`pnpm tauri build` 自取 dmg）
- 💬 在评论区聊聊你怎么和 AI 协作开发

也欢迎把这套 **OpenSpec + Phase + 规格驱动** 的工作流抄走，**让你的下一个五一假期也能有意外的产出**。

下篇预告：《把规格驱动开发用到极致——我是怎么用 AI 同时维护 6 个项目的》。

---

> 项目信息
> · 名称：Seven Redis Nav
> · 版本：v0.4
> · 语言：Rust + TypeScript + Vue 3
> · License：MIT
> · 作者：avinzhang
> · 创建于：2026 年五一假期
