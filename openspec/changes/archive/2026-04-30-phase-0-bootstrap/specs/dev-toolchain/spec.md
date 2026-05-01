## ADDED Requirements

### Requirement: 运行时版本锁定

仓库 SHALL 锁定开发所需的运行时版本，避免不同开发者环境差异引入的问题。

- Node.js：20.x LTS（通过 `.nvmrc` 与 `package.json` 的 `engines` 字段双重声明）
- pnpm：9.x（通过 `package.json` 的 `packageManager` 字段声明，例如 `"packageManager": "pnpm@9.0.0"`）
- Rust：stable 1.79+（通过根目录 `rust-toolchain.toml` 锁定 channel = stable）

#### Scenario: 版本不匹配的明确报错

- **WHEN** 开发者使用 Node 18 执行 `pnpm install`
- **THEN** pnpm 输出 engines 警告，README 明确指引使用 Node 20

#### Scenario: Rust 工具链自动安装

- **WHEN** 开发者首次进入仓库执行 `cargo build`
- **THEN** rustup 自动按 `rust-toolchain.toml` 安装 stable 工具链

### Requirement: 项目目录骨架

仓库根目录 SHALL 至少包含以下顶层目录与文件：

```
redis-nav/
├── docs/                  # 已存在
├── openspec/              # 已存在
├── src-tauri/             # Rust 后端
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── capabilities/
│   ├── icons/
│   └── src/
│       ├── main.rs
│       ├── lib.rs
│       ├── commands/
│       ├── services/
│       ├── models/
│       ├── utils/
│       └── error.rs
├── src/                   # Vue 前端
│   ├── App.vue
│   ├── main.ts
│   ├── ipc/
│   ├── stores/
│   ├── composables/
│   ├── views/
│   ├── components/
│   ├── styles/
│   │   ├── tokens.css
│   │   ├── reset.css
│   │   └── globals.css
│   └── types/
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── package.json
├── pnpm-lock.yaml
├── rust-toolchain.toml
├── .nvmrc
├── .gitignore
├── .editorconfig
├── README.md
└── CONTRIBUTING.md
```

#### Scenario: 目录完整性校验

- **WHEN** 在仓库根目录执行 `ls`
- **THEN** 上述所有顶层目录与文件均存在

### Requirement: Lint / Format / Typecheck 工具链

仓库 SHALL 配置以下工具并在 `package.json` `scripts` 中暴露统一命令：

- `pnpm lint`：运行 ESLint（含 `@vue/eslint-config-typescript` + `eslint-plugin-vue`）
- `pnpm format`：运行 Prettier 格式化
- `pnpm typecheck`：运行 `vue-tsc --noEmit`
- `cargo fmt --check`：Rust 格式检查
- `cargo clippy -- -D warnings`：Rust 静态检查（warnings 即视为错误）

#### Scenario: 一键全量校验

- **WHEN** 开发者执行 `pnpm verify`（约定脚本，串联 lint + typecheck + cargo fmt + cargo clippy）
- **THEN** 任意一项失败时整个命令以非零退出码结束

### Requirement: 提交规范与本地钩子

仓库 SHALL 强制使用 Conventional Commits 规范，并通过 husky + commitlint + lint-staged 在本地 pre-commit 阶段执行轻量校验。

- pre-commit：仅对 staged 文件运行 `lint-staged`（Prettier + ESLint --fix）
- commit-msg：运行 commitlint（`@commitlint/config-conventional`）

#### Scenario: 不合规提交被拒

- **WHEN** 开发者执行 `git commit -m "fix bug"`（无 type 前缀）
- **THEN** commitlint 阻止该提交并输出错误说明

#### Scenario: 合规提交通过

- **WHEN** 开发者执行 `git commit -m "feat(connection-ping): add timeout option"`
- **THEN** 提交成功

### Requirement: GitHub Actions CI 流水线

仓库 SHALL 在 `.github/workflows/ci.yml` 配置 PR 触发的 CI 流水线，使用 `macos-14` runner，至少执行以下步骤并全部通过才允许合并：

1. Checkout
2. Setup Node 20 + pnpm 9
3. Setup Rust stable + cache
4. `pnpm install --frozen-lockfile`
5. `pnpm lint`
6. `pnpm typecheck`
7. `cargo fmt --check`
8. `cargo clippy -- -D warnings`
9. `pnpm tauri build`（仅校验编译产物，不上传）

#### Scenario: PR 不绿不让合

- **WHEN** PR 中任意 CI 步骤失败
- **THEN** GitHub 仓库设置（branch protection）阻止该 PR 合并

#### Scenario: CI 时长目标

- **WHEN** CI 在缓存命中状态下运行
- **THEN** 总时长 SHOULD 控制在 8 分钟以内

### Requirement: README 启动指南

`README.md` SHALL 包含以下章节，确保新人 5 分钟内能本地运行：

1. 项目简介（一段话定位 + Logo）
2. 系统要求（macOS 12+、Node 20、pnpm 9、Rust stable、Xcode CLT）
3. 快速开始（4 个命令：`xcode-select --install` / `nvm use` / `pnpm install` / `pnpm tauri dev`）
4. 常用脚本表（dev / build / lint / typecheck / verify）
5. 目录结构概览（链接到 `docs/overview-and-roadmap.md` §3）
6. 故障排查（至少 3 个常见问题：Xcode 未装 / Node 版本错 / Rust 未装）
7. 文档链接（指向 `docs/` 与 `openspec/`）

#### Scenario: README 完整性

- **WHEN** 检查 `README.md`
- **THEN** 上述 7 个章节全部存在且每个章节非空

### Requirement: 贡献指南

`CONTRIBUTING.md` SHALL 说明：

1. 分支策略（main 受保护，feature/* 分支开发）
2. Conventional Commits 规范与示例（type 列表：`feat` / `fix` / `docs` / `style` / `refactor` / `test` / `chore` / `ci`）
3. PR 模板要点（关联 OpenSpec change ID、自测清单、是否同步前后端类型）
4. OpenSpec 工作流入口（链接 `openspec/` 与 propose / apply / archive 三个 skill）

#### Scenario: 贡献指南完整性

- **WHEN** 检查 `CONTRIBUTING.md`
- **THEN** 上述 4 项内容均有覆盖

### Requirement: 编辑器与 Git 配置

仓库 SHALL 提供 `.editorconfig`（统一缩进 = 2 空格、LF 行尾、UTF-8、保留尾部空行）与 `.gitignore`（覆盖 Node、Rust、Tauri、macOS、IDE 至少 5 类常见忽略项）。

#### Scenario: editorconfig 生效

- **WHEN** 开发者用支持 EditorConfig 的编辑器打开任意 .ts / .vue / .rs 文件
- **THEN** 缩进自动按 2 空格展开

#### Scenario: gitignore 覆盖

- **WHEN** 执行 `git status`
- **THEN** `node_modules/` / `target/` / `dist/` / `.DS_Store` / `.idea/` 等均不出现在未跟踪列表
