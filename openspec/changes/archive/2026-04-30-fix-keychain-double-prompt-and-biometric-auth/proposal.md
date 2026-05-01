## Why

macOS Keychain 授权弹窗在每次应用启动时弹出两次（甚至更多次），严重影响用户体验。根本原因是 `connection_list` 命令在加载连接列表时对每个连接都调用一次 `get_generic_password()`，随后 `connection_open` 打开连接时又再次调用，导致同一个 keychain item 被重复访问。此外，当前实现不支持 Touch ID / 指纹等生物识别验证方式，用户每次都必须手动输入登录钥匙串密码，体验落后于现代 macOS 应用标准。

## What Changes

- **修复重复弹窗**：`connection_list` 不再从 Keychain 读取密码明文，改为只返回 `has_password: bool` 标志位；密码仅在实际建立连接（`connection_open`）时读取一次，消除重复授权弹窗
- **引入生物识别验证**：使用 macOS `LocalAuthentication` 框架（通过 `security-framework` + `core-foundation` 或 `objc2` 桥接）在读取 Keychain 密码前先进行 Touch ID / Face ID 验证，通过后系统不再弹出密码输入框
- **Keychain 访问控制升级**：新保存的密码条目使用 `kSecAccessControlBiometryAny | kSecAccessControlOr | kSecAccessControlDevicePasscode` 访问控制策略，允许 Touch ID 或设备密码两种方式解锁
- **前端 ConnectionConfig 类型调整**：`password` 字段在列表场景下不再返回明文，改为 `has_password: bool`；连接编辑表单中密码字段显示占位符而非明文回填
- **渐进式迁移**：已存在的旧 Keychain 条目（无访问控制）继续可用，新建/编辑保存时自动升级为带生物识别访问控制的新条目

## Capabilities

### New Capabilities

- `keychain-biometric-auth`: 使用 macOS LocalAuthentication 进行 Touch ID / 设备密码验证后再读取 Keychain 密码，替代系统默认的密码输入弹窗

### Modified Capabilities

- `connection-manager`: 连接列表接口不再返回密码明文，改为 `has_password` 标志；密码读取时机收敛到 `connection_open` 单点

## Impact

- **Rust 后端**：`src-tauri/src/utils/keychain.rs` 重构，新增 biometric auth 逻辑；`src-tauri/src/commands/connection.rs` 中 `connection_list` 返回类型调整
- **前端**：`src/ipc/` 中 connection 相关 IPC 类型定义更新；连接列表/编辑表单组件中密码字段展示逻辑调整
- **依赖**：`Cargo.toml` 可能新增 `objc2` 或通过 `security-framework` 的高级 API 使用 `SecAccessControl`；需要在 `tauri.conf.json` / capabilities 中声明相关权限
- **macOS 版本要求**：Touch ID API 要求 macOS 10.12.2+，与现有 Tauri 2 最低系统要求兼容
