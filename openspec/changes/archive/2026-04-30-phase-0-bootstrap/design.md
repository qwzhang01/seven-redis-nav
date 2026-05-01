## Context

Seven Redis Nav 是一款面向 macOS 的原生 Redis 管理工具，最终形态在 `docs/overview-and-roadmap.md` 已定义清楚（6 Tab 工作区 + Mac 窗口隐喻 + Tauri v2 + Rust + Vue 3）。当前仓库只有文档与 HTML 原型，无任何可运行代码。Phase 0 的任务是把"文档与原型"翻译为"工程基线 + 最小端到端可运行闭环"，让后续 4 个 Phase 都能在同一套规范上平行开发。

**约束**：
- macOS 12+ 单平台首发（不考虑 Windows / Linux）
- 单人节奏，Phase 0 时长目标 **1 周**
- 不引入团队级基础设施（无 Sentry、无 OTel）
- 视觉必须与 `docs/index.html` 原型 1:1 对齐（颜色、圆角、动效、布局）

**相关方**：
- 当前阶段唯一开发者（avinzhang）
- 后续 Phase 1+ 接手者（设计文档与 IPC 契约必须自解释）

## Goals / Non-Goals

**Goals**

1. 一行 `pnpm tauri dev` 启动桌面应用，看到 1:1 还原原型的主窗口
2. 一个真实可工作的 IPC 闭环：前端 Welcome 页"测试连接" → Rust 后端 → redis-rs → PING → Toast 反馈
3. 工程规范固化：lint / format / typecheck / commit / CI 五件套全部接入并强制执行
4. 4 类 capability（`app-shell` / `ipc-foundation` / `connection-ping` / `dev-toolchain`）的契约清晰，后续 Phase 不需重新讨论
5. 设计令牌（colors / spacing / radius / shadow / motion）抽离到独立文件，所有后续组件复用

**Non-Goals**

- 不实现任何业务功能（连接保存、键浏览、CLI、监控、慢查询、Pub/Sub、配置编辑）
- 不接入 macOS Keychain / SQLite（密码仅在内存中传递，不持久化）
- 不做 SSH 隧道、TLS、Sentinel、Cluster
- 不做 i18n、深色/浅色主题切换、自动更新、崩溃上报
- 不做应用签名、公证、dmg 美化、App Store 提审
- 不做单元测试覆盖率门槛（仅保留 vitest / cargo test 框架可跑）

## Decisions

### D1：Tauri v2 而非 v1 / Electron / 纯原生

**选择**：Tauri v2.x

**理由**：
- v2 比 v1 的权限模型（capabilities）更细粒度，更适合后续配置 IPC 白名单
- 包体积 ~10MB（vs Electron ~150MB），符合"轻量"产品定位
- Rust IPC 比 Node 主进程性能高一个数量级，对百万 Key SCAN 场景关键
- 原生 WKWebView 渲染，符合 macOS 视觉

**备选**：
- Electron：体积大、内存占用高，与"原生体验"定位冲突 → 否
- 纯 Swift / SwiftUI：开发效率低、复用 Vue 原型 0 收益 → 否
- Tauri v1：API 与 v2 差异大，新项目选 v2 避免后期迁移 → 否

### D2：包管理器选 pnpm

**选择**：pnpm 9.x

**理由**：
- 节点磁盘占用比 npm/yarn 小 50%+
- workspace 友好，便于后续可能拆分 `packages/components` / `packages/utils`
- Tauri 官方文档示例兼容 pnpm

**备选**：npm（默认但慢） / yarn（无显著优势） → 否

### D3：状态管理选 Pinia 而非 Vuex / 自管 ref

**选择**：Pinia 2.x

**理由**：与 Vue 3 + TS 官方推荐组合，模块化清晰，DevTools 支持好；后续 Phase 1 起 store 数量会快速增长（connection / keyBrowser / workspace / terminal / monitor 等 10+），需要规范化容器。

### D4：UI 组件库选 TDesign Vue Next

**选择**：tdesign-vue-next 1.x

**理由**：
- 用户偏好（已在 `mokoko` / `domineering_president` 等项目稳定使用）
- 表格 / 对话框 / Tooltip / Tree 等关键组件成熟，覆盖 Phase 1+ 90% 需求
- 支持 CSS 变量主题系统，便于与原型设计令牌对齐

**备选**：Element Plus（无显著优势 + 风格更"管理后台"）/ Naive UI（生态较小） → 否

### D5：CSS 方案 Tailwind + CSS 变量令牌

**选择**：Tailwind 3 + `src/styles/tokens.css`（CSS 变量）+ Tailwind 主题扩展同步映射

**理由**：
- 原型 HTML 已用 Tailwind CDN，迁移成本最低
- 设计令牌走 CSS 变量便于深色模式（v0.5 才做，提前预留）
- Tailwind 提供原子类 + tokens 提供语义层，两者互补

**目录约定**：
```
src/styles/
├── tokens.css    # --srn-color-* / --srn-radius-* / --srn-motion-* （单一来源）
├── reset.css
└── globals.css
tailwind.config.ts → theme.extend 引用 var(--srn-*)
```

### D6：IPC 协议规范

**命令命名**：`{domain}_{verb}`（snake_case）
- 示例：`connection_test` / `keys_scan` / `cli_exec`
- 拒绝示例：`testConnection`（驼峰）/ `connection.test`（点号）

**返回类型**：所有 commands 返回 `Result<T, IpcError>`，前端用 `try/catch` 接住

**错误模型**：
```rust
#[derive(thiserror::Error, serde::Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum IpcError {
    #[error("redis error: {message}")]
    Redis { message: String },
    #[error("connection refused: {target}")]
    ConnectionRefused { target: String },
    #[error("timeout after {ms}ms")]
    Timeout { ms: u64 },
    #[error("invalid argument: {field}")]
    InvalidArgument { field: String, reason: String },
    #[error("internal error: {message}")]
    Internal { message: String },
}
```

**前端封装**（`src/ipc/`）：
```typescript
// src/ipc/connection.ts
export async function connectionTest(req: ConnectionTestReq): Promise<PingResult> {
  return invoke<PingResult>('connection_test', { req });
}
```
**规则**：禁止在组件中直接 `import { invoke } from '@tauri-apps/api'`；必须经过 `src/ipc/` 类型化封装。这条规则由 ESLint 自定义规则强制（Phase 0 先放 PR review，Phase 1 加 lint）。

**事件命名**：`{domain}:{event}` —— 例：`monitor:tick` / `pubsub:msg`（Phase 0 不使用，仅约定）

### D7：连接复用策略（仅 Phase 0 占位）

Phase 0 的 `connection_test` 每次新建短连接、PING 完即关闭、不做池化。Phase 1 引入 `ConnectionManager` 持有 `ConnectionMultiplexer` 池时再补设计文档。

### D8：错误信息本地化策略

**Phase 0**：`IpcError` 在 Rust 侧只携带英文 `message` + 结构化 `kind`；前端根据 `kind` 映射到中文提示（i18n 表）。

**理由**：避免后端日志/监控被中文字符串污染，前端单独负责展示翻译。

### D9：CI 选 GitHub Actions 而非本地 hooks 强制

**选择**：husky pre-commit 跑 `lint-staged`（轻量），GitHub Actions PR 跑全量 `lint + typecheck + cargo clippy + tauri build`

**理由**：本地 hook 易被 `--no-verify` 绕过，但能给即时反馈；CI 是最后一道闸门，PR 不绿不让合。

### D10：目录结构最终版

冻结 `docs/overview-and-roadmap.md` §3 中的目录骨架，Phase 0 创建到一级目录与 README 占位文件，二级文件随各 Phase 落地。

## Risks / Trade-offs

| 风险 | 影响 | 缓解 |
|---|---|---|
| Tauri v2 文档比 v1 不全，部分 API 在升级中 | 开发遇到坑搜不到答案 | 锁定 v2 稳定版（≥ 2.0.0），关键 API 用官方示例验证 |
| redis-rs 0.27 与 tokio 1 集成需启用 features，新人易漏 | `cargo build` 一次失败 | `Cargo.toml` 注释清楚 features，README 写明 |
| pnpm + Tauri 在某些版本组合下符号链接报错 | `pnpm tauri dev` 启动失败 | 锁定 pnpm 9.x + Node 20 LTS，`.nvmrc` + `packageManager` 字段强约束 |
| 原型用 Tailwind CDN 体积小但生产不可用 | 直接复制样式会丢失 | 走 Tailwind CLI 构建，扫 `src/**/*.{vue,ts}` 生成精简 CSS |
| Conventional Commits 对单人项目偏重 | 写提交摸索成本 | 提供 `git commit -m` 示例 + commitlint 自动校验，前 1 周允许 `chore: bootstrap` 这类宽松提交 |
| macOS 13+ 才默认装 Xcode 16 CLT，老 Mac 需手动 | 新人首次构建失败 | README 显式列出 `xcode-select --install` 步骤 |
| 设计令牌一开始定义不全，Phase 1+ 反复改 | 视觉漂移 | 先把原型出现的所有具体色值/圆角/字号全部抽出（一次性穷举） |

## Migration Plan

Phase 0 是首次落地，不涉及迁移。**部署即"开发者本地能跑"**，无线上环境。

**回滚策略**：所有改动均为新增文件，回滚 = `git revert` 整个 PR。

## Open Questions

1. **应用图标**是否在 Phase 0 出？暂定占位 Tauri 默认图标，Phase 5 才做正式 icon set。
2. **应用菜单栏（macOS NSMenu）**是否在 Phase 0 接入？暂定不接入，由 Tauri 默认菜单先撑场，Phase 1 引入 `tauri::menu::Menu` 自定义。
3. **CI runner 选择**：macos-14（M1）vs macos-13（Intel）？Phase 0 选 `macos-14`（默认且更快），多架构构建留 Phase 5。
4. **是否在 Phase 0 引入 Storybook / Histoire 做组件预览**？暂不引入，避免脚手架膨胀；原型 HTML 就是最权威的视觉参考。
