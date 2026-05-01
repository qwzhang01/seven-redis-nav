## 1. 工程基线与版本锁定（dev-toolchain）

- [ ] 1.1 创建 `.nvmrc` 写入 `20`
- [ ] 1.2 创建 `rust-toolchain.toml` 锁定 `channel = "stable"` + `components = ["rustfmt", "clippy"]`
- [ ] 1.3 创建 `.editorconfig`：缩进 2 空格、LF、UTF-8、`insert_final_newline = true`
- [ ] 1.4 创建 `.gitignore`：覆盖 `node_modules/` / `dist/` / `target/` / `.DS_Store` / `.idea/` / `.vscode/*` / `*.log` / `src-tauri/gen/`
- [ ] 1.5 验证：`nvm use && rustup show` 返回正确版本

## 2. Tauri + Vue 脚手架初始化

- [ ] 2.1 在仓库根目录执行 `pnpm create tauri-app .`，模板选 `vue-ts`、包管理器选 `pnpm`（注意：选择"在当前空目录创建"，避免覆盖 `docs/` 与 `openspec/`）
- [ ] 2.2 在 `package.json` 加入 `"packageManager": "pnpm@9.x.x"`、`"engines": { "node": ">=20" }`
- [ ] 2.3 删除 Tauri 模板自带的占位 `App.vue`、`HelloWorld` 组件、默认样式，留空 `App.vue` 与 `main.ts` 框架
- [ ] 2.4 验证：`pnpm install` 成功、`pnpm tauri dev` 启动空白窗口

## 3. 前端依赖接入

- [ ] 3.1 安装 UI / 状态 / 路由：`pnpm add tdesign-vue-next pinia vue-router@4`
- [ ] 3.2 安装样式：`pnpm add -D tailwindcss@3 postcss autoprefixer && npx tailwindcss init -p`
- [ ] 3.3 安装可视化与编辑器（提前安装，Phase 0 不使用）：`pnpm add echarts codemirror @codemirror/lang-json`
- [ ] 3.4 安装类型与工具：`pnpm add -D @types/node vue-tsc`
- [ ] 3.5 在 `src/main.ts` 注册：TDesign 全局组件、Pinia、Router、引入 `styles/tokens.css`
- [ ] 3.6 配置 `tailwind.config.ts`：`content` 扫描 `index.html` + `src/**/*.{vue,ts,tsx}`，`theme.extend` 通过 `var(--srn-*)` 引用 tokens
- [ ] 3.7 验证：`pnpm typecheck` 通过

## 4. 设计令牌与基础样式（app-shell · 设计令牌单一来源）

- [ ] 4.1 通读 `docs/style.css` + `docs/style-ext.css`，列出所有出现过的色值/圆角/字号/动效时长
- [ ] 4.2 创建 `src/styles/tokens.css`，定义 `--srn-color-*`（含原型 6 类型徽章色 + 7 个语义色 + 4 暗 / 3 浅背景色）、`--srn-radius-*`（4/6/8/12px）、`--srn-shadow-*`、`--srn-motion-fast/normal/slow`（150/200/400ms）
- [ ] 4.3 创建 `src/styles/reset.css` 与 `src/styles/globals.css`（字体栈、桌面壁纸、`-webkit-font-smoothing` 等）
- [ ] 4.4 在 `tailwind.config.ts` 的 `theme.extend.colors` 等字段映射 tokens，验证 Tailwind 类如 `bg-[var(--srn-color-bg-1)]` 可用
- [ ] 4.5 验证：grep 确认 `src/components/` 与 `src/views/` 中**无任何**硬编码 `#xxxxxx` 色值

## 5. 主窗口外壳骨架（app-shell · 布局 / 标题栏 / 状态栏）

- [ ] 5.1 创建 `src/views/MainLayout.vue`，按 38/48/240/320/auto/28 px 严格布局
- [ ] 5.2 创建 `src/components/window/Titlebar.vue`：渐变背景 + 三个红绿灯（带 hover `× − +` + 关闭抖动 / 最小化 / 最大化切换）+ 居中标题"Seven Redis Nav"
- [ ] 5.3 创建 `src/components/window/Toolbar.vue`：6 Tab 按钮（图标 + 文案 + `data-tab`）+ 全局搜索（max-width 360px + ⌘K chip）+ 连接状态脉冲 + `+` 新建按钮
- [ ] 5.4 创建 `src/components/window/Statusbar.vue`：左侧静态服务器信息 + 右侧 4 个静态指标
- [ ] 5.5 创建 `src/components/window/DesktopWallpaper.vue`：fixed 定位 + 多层径向渐变背景
- [ ] 5.6 创建 `@keyframes pulse / window-shake / window-minimize` 动画到 `globals.css`
- [ ] 5.7 验证：浏览器/Tauri 中视觉与 `docs/index.html` 原型并排对比 ≥95% 相似

## 6. 三栏与 6 Tab Workspace 容器（app-shell · 6 Tab 切换）

- [ ] 6.1 创建 `src/stores/workspace.ts`：`activeTab: 'browser' | 'cli' | 'monitor' | 'slowlog' | 'pubsub' | 'config'`，提供 `setActiveTab(tab)` action
- [ ] 6.2 创建 `src/components/sidebar/Sidebar.vue`：渲染静态 mock 连接列表（取自 `docs/data.js` 的 `mockConnections`）+ DB 列表 + 用户信息（占位头像 SVG）
- [ ] 6.3 创建 `src/components/keypanel/KeyPanel.vue`：搜索筛选栏 + 统计行 + 静态 mock 键列表（24 项，类型徽章按 spec 配色）+ 分页栏
- [ ] 6.4 创建 `src/views/workspaces/{Browser,Cli,Monitor,Slowlog,Pubsub,Config}Placeholder.vue`：每个仅显示 Tab 名 + 一行说明（"Phase 1 实现"）
- [ ] 6.5 在 `MainLayout.vue` 中根据 `activeTab` 切换渲染对应 placeholder
- [ ] 6.6 实现 ⌘K 聚焦全局搜索的 composable `useShortcut.ts`
- [ ] 6.7 实现响应式断点（≥1100 / 900–1100 / ≤900）通过 CSS Grid + media query
- [ ] 6.8 验证：依次点击 6 个 Tab 切换无错误，键面板搜索可即时过滤 mock 列表

## 7. Rust 后端骨架（ipc-foundation · 命令命名 / 错误模型）

- [ ] 7.1 编辑 `src-tauri/Cargo.toml`，加依赖：`tokio = { version = "1", features = ["full"] }`、`redis = { version = "0.27", features = ["tokio-comp", "aio"] }`、`serde = { version = "1", features = ["derive"] }`、`serde_json`、`thiserror = "1"`、`tracing = "0.1"`、`tracing-subscriber = { version = "0.3", features = ["env-filter"] }`、`secrecy = "0.8"`
- [ ] 7.2 创建目录：`src-tauri/src/{commands,services,models,utils}/mod.rs`
- [ ] 7.3 创建 `src-tauri/src/error.rs`：定义 `IpcError` 枚举（`Redis` / `ConnectionRefused` / `Timeout` / `InvalidArgument` / `Internal`），`#[serde(tag = "kind", rename_all = "snake_case")]`，并提供 `pub type IpcResult<T> = Result<T, IpcError>;`
- [ ] 7.4 在 `lib.rs` 注册 mod 与 `tauri::Builder::default().invoke_handler(...)`，初始化 `tracing_subscriber`（默认 INFO 级，env `RUST_LOG` 可覆盖）
- [ ] 7.5 验证：`cargo check` 通过

## 8. connection_test 命令实现（connection-ping）

- [ ] 8.1 创建 `src-tauri/src/models/connection.rs`：定义 `ConnectionTestReq { host, port, password: Option<Secret<String>>, timeout_ms: Option<u32> }` 与 `PingResult { latency_ms: u32, server_version: Option<String> }`
- [ ] 8.2 创建 `src-tauri/src/services/connection.rs`：实现 `pub async fn ping(req: &ConnectionTestReq) -> IpcResult<PingResult>` —— 用 `redis::Client::open(...)`、`get_async_connection`、`AUTH`（如有密码）、`PING` 测延迟、`INFO server` 解析版本、`tokio::time::timeout` 包裹
- [ ] 8.3 创建 `src-tauri/src/commands/connection.rs`：`#[tauri::command] pub async fn connection_test(req: ConnectionTestReq) -> IpcResult<PingResult>`，入口处用 `tracing::info!` 记录脱敏后的请求（密码 `***`）
- [ ] 8.4 在 `lib.rs` 的 `invoke_handler` 注册 `connection_test`
- [ ] 8.5 编写 `cargo test`：`tests/connection_ping.rs` —— 给定 `host="127.0.0.1"`, `port=6379` 跑通（CI 中如无 redis 用 `#[ignore]` 跳过）
- [ ] 8.6 验证：`cargo clippy -- -D warnings` 通过

## 9. 前端 IPC 封装（ipc-foundation · 类型化封装）

- [ ] 9.1 创建 `src/types/connection.d.ts`：与 Rust 模型字段一致的 `ConnectionTestReq` 与 `PingResult`（snake_case 字段名）
- [ ] 9.2 创建 `src/types/ipc.d.ts`：`IpcError`（联合类型，按 `kind` 区分）+ `IpcErrorKind` 字面量类型
- [ ] 9.3 创建 `src/ipc/index.ts`：导出统一 `invoke` 包装（捕获 Tauri 错误并 narrow 成 `IpcError`）
- [ ] 9.4 创建 `src/ipc/connection.ts`：`export async function connectionTest(req: ConnectionTestReq): Promise<PingResult>`
- [ ] 9.5 创建 `src/composables/useToast.ts`：封装 TDesign MessagePlugin，按 `IpcError.kind` 映射中文文案
- [ ] 9.6 验证：`pnpm typecheck` 通过

## 10. Welcome 页与端到端联调（connection-ping · UI / Toast / Loading）

- [ ] 10.1 创建 `src/views/Welcome.vue`：TDesign 表单（host 默认 `127.0.0.1` / port 默认 `6379` / password 空）+ "测试连接" 按钮
- [ ] 10.2 在 `src/router/index.ts` 注册 `/welcome` 路由，应用启动默认进入 `/welcome`
- [ ] 10.3 实现按钮 click handler：调 `connectionTest()`、loading 态切换、按结果调用 `useToast` 弹绿/红 Toast
- [ ] 10.4 实现字段校验：host 非空 + port ∈ [1, 65535]，否则按钮禁用
- [ ] 10.5 端到端冒烟：本地启 `redis-server`，在 Welcome 页点击"测试连接" → 弹"已连接 · Redis 7.x.x · NN ms"
- [ ] 10.6 故障路径冒烟：故意填错误端口 → 弹红色"连接被拒绝"；故意填错密码 → 弹红色"Redis 错误：WRONGPASS..."

## 11. Lint / Format / Commit 钩子（dev-toolchain · Lint / 提交规范）

- [ ] 11.1 安装：`pnpm add -D eslint @vue/eslint-config-typescript eslint-plugin-vue prettier eslint-config-prettier`
- [ ] 11.2 创建 `.eslintrc.cjs` + `.prettierrc.json` + `.prettierignore`
- [ ] 11.3 安装：`pnpm add -D husky lint-staged @commitlint/cli @commitlint/config-conventional`，运行 `pnpm exec husky init`
- [ ] 11.4 配置 `package.json` 的 `lint-staged`：`*.{ts,vue,js}` 跑 `eslint --fix` + `prettier --write`，`*.rs` 跑 `cargo fmt --`
- [ ] 11.5 创建 `.husky/pre-commit` 调用 `pnpm exec lint-staged`，`.husky/commit-msg` 调用 `pnpm exec commitlint --edit $1`
- [ ] 11.6 创建 `commitlint.config.js`：`extends: ['@commitlint/config-conventional']`
- [ ] 11.7 在 `package.json` `scripts` 加 `lint` / `format` / `typecheck` / `verify`（串联 lint + typecheck + cargo fmt + cargo clippy）
- [ ] 11.8 验证：故意写一行错代码，`git commit` 被 pre-commit 阻止

## 12. GitHub Actions CI（dev-toolchain · CI 流水线）

- [ ] 12.1 创建 `.github/workflows/ci.yml`，触发器：`pull_request` + `push` 到 `main`
- [ ] 12.2 jobs：`runs-on: macos-14`，步骤按 spec 列出 9 步全部串联
- [ ] 12.3 添加缓存：`actions/setup-node@v4`（pnpm cache）、`Swatinem/rust-cache@v2`
- [ ] 12.4 在仓库 Settings 启用 Branch Protection：main 分支 require CI status check 通过
- [ ] 12.5 验证：开 PR 跑一次 CI，全绿耗时 ≤ 8 分钟

## 13. README 与贡献指南（dev-toolchain · README / CONTRIBUTING）

- [ ] 13.1 创建 `README.md`，包含 spec 列出的 7 个章节
- [ ] 13.2 在快速开始章节加四行命令：`xcode-select --install` / `nvm use` / `pnpm install` / `pnpm tauri dev`
- [ ] 13.3 添加常见问题：① Xcode CLT 未装报错处理；② Node 版本不对处理；③ `pnpm tauri dev` 启动失败排查
- [ ] 13.4 创建 `CONTRIBUTING.md`：分支策略 + Conventional Commits 示例（每种 type 给一个例子）+ PR 模板要点 + OpenSpec 工作流入口（链 `openspec/changes/`、`openspec/specs/`、三个 skill 名称）
- [ ] 13.5 创建 `.github/PULL_REQUEST_TEMPLATE.md`：勾选项含"关联 OpenSpec change ID"、"是否同步前后端类型"、"自测清单"

## 14. 文档同步与提案归档准备

- [ ] 14.1 在 `docs/overview-and-roadmap.md` Phase 0 章节末尾追加"已完成"标记，并指向本 OpenSpec change
- [ ] 14.2 校验四份 spec 中所有 `MUST` / `SHALL` 条款都有对应实现 / 验证步骤
- [ ] 14.3 跑一次 `openspec status --change phase-0-bootstrap`，确认 `Progress: 4/4 artifacts complete`
- [ ] 14.4 提交一个 `chore(phase-0): finalize bootstrap` 收尾 commit，准备 PR 合入 main
- [ ] 14.5 PR 合入后，运行 openspec-archive-change skill 归档本 change 至 `openspec/changes/archive/`
