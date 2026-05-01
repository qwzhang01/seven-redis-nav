## Why

当前 Welcome 页面设计存在严重的用户体验缺陷：用户首次打开应用后，只能"测试连接"而无法直接连接进入工作区。流程要求用户先测试 → 保存为新连接 → 再从已保存列表点击连接，路径冗长且不直观。一个 Redis 管理工具的首页应该让用户在 5 秒内完成首次连接（产品设计文档 NFR 要求），当前设计远未达标。需要重新设计一个完整、直观的 Welcome 页面，覆盖首次使用和日常使用两种场景。

## What Changes

- **快速连接区域重设计**：将"测试连接"按钮改为"连接"按钮，连接成功后直接进入工作区；保留"测试连接"作为辅助功能（可选）
- **新增"新建连接"入口**：Welcome 页面直接提供"新建连接"按钮，点击打开完整的 ConnectionForm 弹窗（含名称/分组/高级配置），保存后自动连接
- **已保存连接列表增强**：显示连接状态指示、最后连接时间、右键菜单（编辑/删除/复制）；空状态时显示引导文案
- **快速连接成功后的保存提示优化**：连接成功进入工作区后，通过 Toast 或顶部横幅提示"当前为临时连接，是否保存？"，而非阻塞在 Welcome 页
- **页面布局重构**：左右分栏布局——左侧为已保存连接列表（日常使用），右侧为快速连接表单 + 新建连接入口（首次使用）；当无已保存连接时，右侧居中展示
- **连接分组展示**：已保存连接按分组折叠展示，与 Sidebar 风格一致

## Capabilities

### New Capabilities

- `welcome-page`: Welcome 页面完整交互逻辑——快速连接（直连）、新建连接入口、已保存连接列表、临时连接管理、空状态引导、连接分组展示

### Modified Capabilities

- `connection-manager`: 新增"临时连接"概念——不保存到 SQLite 但可建立会话，连接成功后提供"保存当前连接"选项；openConnection 支持传入临时 config（非 connId）

## Impact

- **前端**：重写 `src/views/WelcomePage.vue`；修改 `src/stores/connection.ts` 支持临时连接；可能新增 `src/components/welcome/` 子组件目录
- **Rust 后端**：`commands/connection.rs` 新增 `connection_open_temp` 命令（接收完整 config 而非 connId）；`services/connection_manager.rs` 支持临时会话
- **IPC 层**：`src/ipc/connection.ts` 新增 `connectionOpenTemp` 调用
- **类型定义**：`src/types/connection.d.ts` 可能新增 TempConnectionSession 类型
