## 1. 依赖评估与环境准备

- [x] 1.1 评估 `security-framework` 2.x 是否支持 `SecAccessControlCreateWithFlags`，确认是否需要引入 `objc2` 或 `core-foundation` crate
- [x] 1.2 检查 `src-tauri/tauri.conf.json` 及 `capabilities/` 目录，确认是否需要添加 macOS entitlements（如 `com.apple.security.device.biometric`）
- [x] 1.3 更新 `Cargo.toml`，添加所需依赖（如 `objc2`、`objc2-local-authentication` 或相关 crate）

## 2. Rust 后端 — Keychain 工具层重构

- [x] 2.1 在 `src-tauri/src/utils/keychain.rs` 中新增 `save_password_with_biometric(account, password)` 函数，使用 `SecAccessControl`（`biometryAny | devicePasscode`）写入 Keychain
- [x] 2.2 新增 `is_biometric_available() -> bool` 工具函数，检测当前设备是否支持生物识别
- [x] 2.3 修改 `save_password()` 函数，内部调用 `save_password_with_biometric()`，保持对外接口不变（向后兼容）
- [x] 2.4 在 `get_password()` 中增加 legacy fallback 逻辑：先尝试带访问控制的读取，若失败（`errSecItemNotFound`）则 fallback 到旧式 `get_generic_password`
- [x] 2.5 编写单元测试验证 `is_biometric_available()` 在 CI 环境（无 Touch ID）下返回 `false` 不 panic

## 3. Rust 后端 — ConnectionConfig 模型调整

- [x] 3.1 在 `src-tauri/src/models/connection.rs` 的 `ConnectionConfig` 结构体中新增 `has_password: bool` 字段（`#[serde(default)]`）
- [x] 3.2 确认 `ConnectionConfig` 的 `password` 字段为 `Option<String>`（已有），无需修改

## 4. Rust 后端 — connection_list 修复（消除重复弹窗）

- [x] 4.1 修改 `src-tauri/src/commands/connection.rs` 中的 `connection_list` 函数：移除 `get_password()` 调用，改为设置 `has_password: meta.keychain_key.is_some()`，`password: None`
- [x] 4.2 验证修改后 `connection_list` 不再触发任何 Keychain 访问（通过日志或 macOS Console 确认无 `SecKeychainItem` 事件）

## 5. Rust 后端 — connection_save 保留密码逻辑

- [x] 5.1 修改 `connection_save` 命令：当 `config.password` 为 `None` 且数据库中已存在 `keychain_key` 时，跳过 Keychain 写入，保留原有 `keychain_key`
- [x] 5.2 当 `config.password` 为 `Some("")`（空字符串）时，删除 Keychain 条目并清空 `keychain_key`（表示用户主动移除密码）
- [x] 5.3 当 `config.password` 为 `Some(非空字符串)` 时，调用新的 `save_password_with_biometric()` 写入/覆盖 Keychain 条目

## 6. 前端 — TypeScript 类型更新

- [x] 6.1 在 `src/ipc/` 或 `src/types/` 中更新 `ConnectionConfig` TypeScript 接口，新增 `hasPassword?: boolean` 字段
- [x] 6.2 更新 `connection_list` IPC 调用处，处理 `password` 为 `undefined/null` 的情况

## 7. 前端 — 连接编辑表单调整

- [x] 7.1 在连接编辑表单组件中，当 `hasPassword === true` 且 `password` 未填写时，密码输入框显示占位符 `••••••••`（而非空白）
- [x] 7.2 表单提交时，若用户未修改密码字段（仍为占位符状态），则传递 `password: null`（不传密码，后端保留原有 Keychain 条目）
- [x] 7.3 在连接列表/卡片 UI 中，根据 `hasPassword` 字段显示锁图标（已有密码）或无图标（无密码）

## 8. 集成验证

- [ ] 8.1 手动测试：新建带密码的连接 → 保存 → 重启应用 → 打开连接，确认只弹出一次 Touch ID / 密码框
- [ ] 8.2 手动测试：编辑连接但不修改密码 → 保存 → 重启 → 打开连接，确认密码仍有效
- [ ] 8.3 手动测试：旧版本创建的连接（legacy Keychain 条目）→ 打开连接，确认 fallback 路径正常工作
- [ ] 8.4 手动测试：`connection_list` 加载时确认不弹出任何授权对话框
