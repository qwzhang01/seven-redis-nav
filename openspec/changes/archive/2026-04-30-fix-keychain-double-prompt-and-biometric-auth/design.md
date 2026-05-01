## Context

当前应用使用 `security-framework` crate 的 `get_generic_password` / `set_generic_password` API 操作 macOS Keychain。这套 API 对应 macOS Security Framework 的 `SecKeychainItem` 接口，每次读取密码时系统会弹出授权对话框（除非用户选择"始终允许"）。

**弹出两次的根本原因**：

1. 应用启动时，前端调用 `connection_list` IPC → 后端遍历所有连接，对每个有 `keychain_key` 的连接调用 `get_generic_password()` → **第一次弹窗**
2. 用户点击连接时，前端调用 `connection_open` IPC → 后端再次调用 `get_generic_password()` 读取同一条目 → **第二次弹窗**

即使只有一个连接，也会弹出两次。如果有 N 个连接，`connection_list` 阶段就会弹出 N 次。

**现有 Keychain 条目**：使用默认访问控制（`kSecAttrAccessibleWhenUnlocked`），不支持生物识别，系统只能通过密码弹窗授权。

## Goals / Non-Goals

**Goals:**
- 消除 `connection_list` 阶段的 Keychain 访问，将密码读取收敛到 `connection_open` 单点
- 新建/编辑连接时，使用带 `SecAccessControl`（`biometryAny | devicePasscode`）的 Keychain 条目，支持 Touch ID 验证
- 旧条目向后兼容，不强制迁移，用户编辑保存时自动升级
- 前端连接列表展示 `has_password` 标志，不展示密码明文

**Non-Goals:**
- 不支持 Windows / Linux 平台的生物识别（当前仅 macOS）
- 不实现密码明文导出功能
- 不修改 Redis 连接协议本身

## Decisions

### 决策 1：`connection_list` 不读取密码明文

**选择**：`connection_list` 返回 `ConnectionConfig` 时，`password` 字段改为 `None`，新增 `has_password: bool` 字段（或复用 `password` 字段但值为固定占位符 `"__HAS_PASSWORD__"`）。

**理由**：列表页面不需要密码明文，只需知道"是否设置了密码"以便 UI 显示锁图标。避免在列表加载时触发 Keychain 授权。

**备选方案**：缓存密码到内存（`Arc<Mutex<HashMap>>`）——被否决，因为内存中存明文密码有安全风险，且增加状态管理复杂度。

---

### 决策 2：使用 `SecAccessControl` + `SecItemAdd` 替代 `set_generic_password`

**选择**：新建/更新 Keychain 条目时，使用 `security_framework` 的底层 `SecItem` API（或通过 `core-foundation` + `objc2` 调用 `SecAccessControlCreateWithFlags`），设置 `kSecAccessControlBiometryAny | kSecAccessControlOr | kSecAccessControlDevicePasscode` 访问控制。

**理由**：带访问控制的条目在读取时，系统会优先尝试 Touch ID，Touch ID 通过后不弹密码框；Touch ID 不可用时回退到设备密码。用户体验从"每次输入登录钥匙串密码"升级为"Touch ID 轻触验证"。

**备选方案**：使用 `keytar` npm 包（JS 层）——被否决，Tauri 2 推荐在 Rust 层处理敏感操作，避免密码在 JS 层暴露。

---

### 决策 3：旧条目渐进式迁移

**选择**：读取时先尝试新 API，失败则 fallback 到旧 `get_generic_password`；用户下次编辑保存连接时，自动用新 API 覆写条目（升级访问控制）。

**理由**：避免强制迁移导致用户数据丢失或需要重新输入所有密码。

---

### 决策 4：前端类型调整

**选择**：`ConnectionConfig` TypeScript 类型中，`password` 字段在列表场景下为 `undefined`，新增可选字段 `hasPassword?: boolean`。编辑表单中，若 `hasPassword === true` 且 `password === undefined`，密码输入框显示占位符 `••••••••`，提交时若用户未修改则不传 `password` 字段（后端保留原有 Keychain 条目）。

**理由**：与后端数据模型对齐，避免前端误以为密码为空而覆盖 Keychain 条目。

## Risks / Trade-offs

- **[风险] Touch ID API 在某些 macOS 配置下不可用**（如无 Touch ID 硬件、企业策略禁用）→ 缓解：始终提供设备密码作为 fallback，`kSecAccessControlOr | kSecAccessControlDevicePasscode` 保证降级路径
- **[风险] `security-framework` crate 的 `SecAccessControl` 支持不完整** → 缓解：评估使用 `objc2` 直接调用 ObjC API，或使用 `security-framework` 的 `unsafe` 底层接口
- **[风险] 旧条目迁移期间，用户可能仍会看到一次密码弹窗**（读取旧条目时）→ 缓解：在弹窗前显示提示 Toast："首次使用需授权，之后将支持 Touch ID"
- **[风险] 前端 `hasPassword` 字段引入后，编辑表单逻辑变复杂**（需区分"未设置密码"和"已设置但未修改"）→ 缓解：后端 `connection_save` 增加 `keep_existing_password: bool` 参数，前端明确传递意图

## Migration Plan

1. 后端先发布"不读取密码明文的 `connection_list`"修复，消除重复弹窗
2. 前端同步更新类型定义和编辑表单逻辑
3. 后端发布"带 `SecAccessControl` 的新 Keychain 写入"，新建/编辑连接时自动使用新格式
4. 旧条目在用户下次编辑保存时自动升级，无需额外迁移脚本

**回滚**：若 Touch ID 集成出现问题，可通过 feature flag（`ENABLE_BIOMETRIC_KEYCHAIN=false` 环境变量）回退到旧的 `set_generic_password` 写入，已升级的条目仍可通过设备密码访问。

## Open Questions

- `security-framework` 2.x 是否已暴露 `SecAccessControlCreateWithFlags`？需要评估是否需要引入 `objc2` 或 `core-foundation` 直接调用
- 是否需要在 `tauri.conf.json` capabilities 中声明额外的 macOS entitlements（如 `com.apple.security.device.biometric`）？
