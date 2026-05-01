## Why

Seven Redis Nav 当前仅有产品/原型/路线图文档（`docs/*.md` + HTML 原型），尚无任何可运行代码。在进入 Phase 1（MVP：连接管理 + 数据浏览 + CRUD + CLI）之前，必须先完成 **工程脚手架与最小端到端闭环**，否则后续每一个特性都没有落地的载体。

Phase 0 的核心目标只有一句话：**让一名开发者克隆仓库后，5 分钟内能在本地启动 Seven Redis Nav 桌面应用，点一个按钮，对一个真实 Redis 实例发出 PING 命令并收到 PONG。**

完成 Phase 0 后，所有后续 Phase 都可以基于同一套工程规范（IPC 契约、错误模型、CI、目录结构、设计令牌）平行展开，避免后期重构成本。

## What Changes

> Phase 0 不交付任何用户可见业务功能，只交付**工程基线**。

- **新增** Tauri v2 + Rust 后端骨架（`src-tauri/`），含 `commands` / `services` / `models` / `utils` / `error` 五层目录与基础依赖（tokio / redis-rs / serde / tracing / sqlx / aes-gcm / security-framework / thiserror）。
- **新增** Vue 3 + TypeScript strict + Vite 5 前端骨架（`src/`），接入 TDesign Vue Next、Tailwind CSS 3、Pinia、Vue Router、ECharts、CodeMirror 6。
- **新增** 应用主窗口外壳：1:1 还原 HTML 原型的 Titlebar / Toolbar / Sidebar / KeyPanel / Workspace / Statusbar 六大区域**布局与样式**（不实现业务逻辑，组件以静态 mock 数据展示）。
- **新增** 端到端 IPC 闭环：`connection_test(host, port, password?) → PingResult`，前端用 Welcome 页的"测试连接"按钮调用，弹 Toast 反馈。
- **新增** IPC 协议规范层：在 Rust 侧定义 `IpcError` 与 `IpcResult<T>`、在前端侧定义 `src/ipc/` 类型化封装（一处维护命令名 + 入参/返回类型）。
- **新增** 设计令牌（design tokens）：把原型的颜色 / 字号 / 圆角 / 阴影 / 动效时长抽到 `src/styles/tokens.css` + Tailwind 主题扩展，保证后续组件复用时 100% 对齐原型。
- **新增** 工程化基线：
  - `pnpm` workspace（如需）+ Node 20 LTS、Rust stable 1.79+ 版本锁定（rust-toolchain.toml）
  - Lint：`eslint + @vue/eslint-config-typescript + prettier`、`cargo fmt + cargo clippy -D warnings`
  - 提交规范：Conventional Commits + commitlint + husky pre-commit
  - GitHub Actions CI：`pnpm lint && pnpm typecheck && cargo fmt --check && cargo clippy && pnpm tauri build`（macOS runner，仅校验编译）
  - `README.md`（开发启动指南）+ `CONTRIBUTING.md`（分支/提交/PR 规范）
- **新增** 本地运行命令：`pnpm dev`（Vite 启动）/ `pnpm tauri dev`（Tauri 联调）/ `pnpm tauri build`（dmg 打包）。
- **未做**：
  - 不实现连接保存（不接入 Keychain / SQLite，留给 Phase 1）
  - 不实现键浏览、CLI、监控、慢查询、Pub/Sub、配置等任何 Tab 业务逻辑
  - 不做 SSH/TLS、Sentinel/Cluster
  - 不做 i18n、主题切换、自动更新

## Capabilities

### New Capabilities

- `app-shell`: 应用主窗口的视觉骨架与布局规则——Titlebar / Toolbar / Sidebar / KeyPanel / Workspace（6 Tab 容器）/ Statusbar 六大区域的尺寸、颜色、动效、响应式断点，以及 6 个 Tab 间的切换状态机（仅前端，不含业务）。
- `ipc-foundation`: 前后端 IPC 通信的基础协议——统一的命令命名规范（`{domain}_{verb}`）、`IpcResult<T>` / `IpcError` 错误模型、Tauri Event 命名约定（`{domain}:{event}`）、前端 `src/ipc/` 类型化封装的代码组织规则。
- `connection-ping`: Phase 0 唯一的端到端业务能力——给定 host / port / 可选 password，后端使用 redis-rs 建立短连接执行 `PING`，返回响应耗时与 Redis 版本，前端在 Welcome 页"测试连接"按钮触发并以 Toast 展示结果。这是验证整个工程链路是否打通的唯一标尺。
- `dev-toolchain`: 开发者工程基线——Node / Rust 版本锁定、依赖清单、lint / format / typecheck 规则、Conventional Commits 校验、GitHub Actions CI 流水线、`README` 启动指南。规定"什么算合格的提交"。

### Modified Capabilities

<!-- 项目首次启动，无既有 spec 可修改。 -->
（无）

## Impact

- **代码**：新建 `src-tauri/`、`src/`、`public/`、`.github/workflows/`，根目录新增 `package.json` / `pnpm-lock.yaml` / `vite.config.ts` / `tsconfig.json` / `tailwind.config.ts` / `rust-toolchain.toml` / `README.md` / `CONTRIBUTING.md`。
- **依赖**：
  - 后端：`tauri@2`, `redis@0.27 (features: tokio-comp, aio)`, `tokio@1`, `serde`, `serde_json`, `thiserror`, `tracing`, `tracing-subscriber`
  - 前端：`vue@3.4`, `typescript@5`, `vite@5`, `@tauri-apps/api@2`, `tdesign-vue-next`, `tailwindcss@3`, `pinia`, `vue-router@4`, `echarts`, `codemirror@6`
- **CI/CD**：新增 GitHub Actions 构建 workflow，约 3–5 分钟 macOS runner。
- **文档**：本提案对应文档更新已完成（`docs/overview-and-roadmap.md` Phase 0 章节）；落地后需补 `README.md` 的启动步骤与故障排查。
- **风险**：
  - Tauri v2 在 macOS 12 以下可能存在 WKWebView 兼容问题 —— Phase 0 即写明系统要求 ≥ macOS 12。
  - 首次构建需安装 Xcode CLT（约 1GB），README 须提示。
- **不影响**：现有 `docs/` 全部产物保留，新代码与文档共存。
