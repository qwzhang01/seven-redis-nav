# 贡献指南

感谢你对 **Seven Redis Nav** 的关注！我们欢迎任何形式的贡献，包括但不限于 Bug 报告、功能建议、文档改进和代码提交。

---

## 📜 行为准则

本项目采用 [贡献者公约](CODE_OF_CONDUCT.md) 作为行为准则。参与本项目即表示你同意遵守其条款。

---

## 🐛 报告 Bug

如果发现了 Bug，请通过 [GitHub Issues](../../issues) 提交，并包含以下信息：

- **Bug 描述**：清晰描述问题现象
- **复现步骤**：逐步说明如何复现
- **期望行为**：你期望的正确行为是什么
- **实际行为**：实际发生了什么
- **环境信息**：
  - macOS 版本
  - Seven Redis Nav 版本
  - Redis 服务器版本
- **截图/日志**：如有请附上

提交前请先搜索已有 Issue，避免重复。

---

## 💡 功能建议

我们同样欢迎功能建议！请在 Issue 中描述：

- **使用场景**：你遇到了什么问题？
- **期望方案**：你希望怎样解决？
- **替代方案**：你考虑过哪些替代方式？

---

## 🔧 开发贡献

### 环境准备

请确保本地已安装：

- **Node.js** ≥ 20（推荐使用 `.nvmrc` 指定的版本）
- **pnpm** 9.15.9
- **Rust** Stable（通过 rustup 安装）
- **Xcode Command Line Tools**（macOS）

```bash
# 克隆仓库
git clone https://github.com/qwzhang01/seven-redis-nav.git
cd seven-redis-nav

# 安装前端依赖
pnpm install

# 启动开发模式
pnpm tauri dev
```

详细的开发环境搭建请参考 [README.md](README.md)。

### 开发流程

1. **Fork** 本仓库
2. 从 `main` 分支创建新分支：`git checkout -b feature/your-feature` 或 `fix/your-fix`
3. 进行开发并确保：
   - 代码通过 Lint 检查：`pnpm lint`
   - 类型检查通过：`pnpm typecheck`
   - 单元测试通过：`pnpm test:run`
   - Rust 代码格式化：`cd src-tauri && cargo fmt --check`
   - Rust Clippy 检查：`cd src-tauri && cargo clippy -- -D warnings`
   - 也可以一键全量校验：`pnpm verify`
4. 提交代码，Commit 信息遵循下方规范
5. 推送到你的 Fork 并创建 **Pull Request**

### Commit 规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

[optional body]
```

**Type 类型：**

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构（非新功能、非修复） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具链变更 |
| `ci` | CI/CD 配置变更 |

**示例：**

```
feat(browser): add key pattern search support
fix(ssh): fix tunnel connection timeout on retry
docs: update contributing guide
```

### 分支命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 新功能 | `feature/<name>` | `feature/lua-editor` |
| Bug 修复 | `fix/<name>` | `fix/ssh-reconnect` |
| 文档 | `docs/<name>` | `docs/api-reference` |
| 重构 | `refactor/<name>` | `refactor/key-browser` |

### 代码风格

项目通过以下工具自动维护代码风格，提交前请确保通过检查：

- **前端**：ESLint + Prettier（`pnpm lint && pnpm format`）
- **Rust**：rustfmt + clippy（`cargo fmt && cargo clippy`）
- **EditorConfig**：统一编辑器配置（`.editorconfig`）

**关键规则：**

- TypeScript/Vue 文件使用 **2 空格** 缩进
- Rust 文件使用 **4 空格** 缩进
- 行尾使用 **LF**（非 CRLF）
- 文件末尾保留空行

### 测试要求

- 新功能需附带单元测试
- Bug 修复需附带回归测试
- 测试覆盖率要求：branches / functions / lines / statements 均 ≥ 70%

```bash
# 运行单元测试
pnpm test:run

# 查看覆盖率
pnpm test:coverage

# 运行 E2E 测试
pnpm test:e2e
```

---

## 📝 文档贡献

文档改进同样重要！你可以：

- 修复拼写错误或表述不清的地方
- 补充缺失的文档内容
- 改进示例代码
- 翻译文档

---

## 🔀 Pull Request 指南

### PR 标题

遵循与 Commit 相同的 Conventional Commits 格式：

```
feat(browser): add key pattern search support
```

### PR 描述模板

```markdown
## 变更类型
- [ ] feat: 新功能
- [ ] fix: Bug 修复
- [ ] docs: 文档变更
- [ ] refactor: 重构
- [ ] perf: 性能优化
- [ ] test: 测试
- [ ] chore: 构建/工具链

## 变更说明
<!-- 描述你的变更内容 -->

## 关联 Issue
<!-- 如 Closes #123 -->

## 测试
<!-- 说明如何测试你的变更 -->

## 检查清单
- [ ] 代码通过 `pnpm verify` 检查
- [ ] 新功能已添加测试
- [ ] 文档已更新（如需要）
```

### Review 流程

1. 提交 PR 后，维护者会进行代码审查
2. 根据反馈修改代码（追加提交即可，无需 squash）
3. 通过审查后，维护者会合并你的 PR

---

## ❓ 疑问？

如有任何疑问，可以通过以下方式联系：

- [GitHub Issues](https://github.com/qwzhang01/seven-redis-nav/issues) — 提问或反馈
- [GitHub Discussions](https://github.com/qwzhang01/seven-redis-nav/discussions) — 交流讨论

感谢你的贡献！🎉
