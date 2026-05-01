## 1. Rust 后端 — 临时连接支持

- [x] 1.1 在 `services/connection_manager.rs` 的 `open` 方法中支持接收完整 `ConnectionConfig`（不要求 id 存在于 SQLite）
- [x] 1.2 新增 `commands/connection.rs` 中的 `connection_open_temp` 命令：接收 `ConnectionConfig`（host/port/password/timeout_ms），生成 `temp-{uuid}` 作为 ConnId，调用 manager.open()，返回 ConnId
- [x] 1.3 在 `lib.rs` 的 `invoke_handler` 中注册 `connection_open_temp` 命令
- [x] 1.4 验证临时连接参与心跳 PING 和 `connection:state` 事件推送

## 2. 前端 — IPC 层扩展

- [x] 2.1 在 `src/types/connection.d.ts` 中新增 `QuickConnectReq` 类型（host, port, password?, timeout_ms?）
- [x] 2.2 在 `src/ipc/connection.ts` 中新增 `connectionOpenTemp(config: QuickConnectReq): Promise<ConnId>` 函数
- [x] 2.3 确保 IPC 参数命名与 Rust 后端 snake_case 一致（camelCase → snake_case 转换）

## 3. 前端 — Connection Store 扩展

- [x] 3.1 在 `src/stores/connection.ts` 中新增 `openTempConnection(config: QuickConnectReq)` action：调用 `connectionOpenTemp` → 设置 `activeConnId` → 更新 `sessionStates`
- [x] 3.2 新增 `isTempConnection` computed：判断当前 activeConnId 是否以 `temp-` 开头
- [x] 3.3 新增 `saveTempConnection()` action：将当前临时连接配置保存为持久连接（调用 connectionSave → 关闭临时 → 打开持久）
- [x] 3.4 在 store 中缓存临时连接的 config 信息（用于后续保存时预填）

## 4. 前端 — Welcome 页面重写

- [x] 4.1 创建 `src/components/welcome/SavedConnectionList.vue`：已保存连接列表组件（分组折叠、状态指示、hover 操作按钮）
- [x] 4.2 创建 `src/components/welcome/QuickConnectForm.vue`：快速连接表单组件（host/port/password + "连接"主按钮 + "测试连接"次要链接）
- [x] 4.3 创建 `src/components/welcome/EmptyState.vue`：空状态组件（引导插画 + 文案 + "新建连接"按钮）
- [x] 4.4 重写 `src/views/WelcomePage.vue`：双区域布局（左：SavedConnectionList / 右：QuickConnectForm + 新建连接入口）；无已保存连接时居中单栏
- [x] 4.5 实现"连接"按钮逻辑：调用 `openTempConnection` → 成功后 workspace 切换 → 失败显示内联错误
- [x] 4.6 实现"测试连接"次要按钮：调用 `connectionTest` → 显示延迟和版本信息
- [x] 4.7 实现"新建连接"按钮：打开 ConnectionForm 弹窗（create 模式），保存后自动连接
- [x] 4.8 实现已保存连接点击连接：调用 `connStore.openConnection(connId)` → 成功进入工作区

## 5. 前端 — 已保存连接列表交互

- [x] 5.1 连接项 hover 显示编辑/删除图标按钮
- [x] 5.2 编辑按钮点击 → 打开 ConnectionForm（edit 模式，预填配置）
- [x] 5.3 删除按钮点击 → 确认弹窗 → 调用 `connStore.deleteConnection(connId)`
- [x] 5.4 连接项显示分组标签（group_name 非空时）
- [x] 5.5 按 group_name 分组折叠展示（可展开/收起）
- [x] 5.6 连接失败时连接项显示红色错误状态（短暂）

## 6. 前端 — 临时连接保存提示

- [x] 6.1 在 `Toolbar.vue` 或 `Statusbar.vue` 中新增条件渲染：当 `isTempConnection` 为 true 时显示"保存连接"按钮
- [x] 6.2 "保存连接"按钮点击 → 打开 ConnectionForm 预填临时连接的 host/port/password
- [x] 6.3 保存成功后隐藏提示，更新 activeConnId 为持久 connId

## 7. 样式与动效

- [x] 7.1 Welcome 页面整体样式：遵循设计规范（品牌色、圆角、阴影、字体）
- [x] 7.2 已保存连接列表项 hover/active 状态动效
- [x] 7.3 连接状态指示点动画（绿色脉冲/灰色静态）
- [x] 7.4 布局响应式适配（窗口宽度变化时的过渡）
- [x] 7.5 空状态插画/图标设计

## 8. 验证

- [ ] 8.1 首次启动（无已保存连接）→ 显示居中快速连接表单 + 新建连接按钮
- [ ] 8.2 快速连接 → 填写 localhost:6379 → 点击"连接" → 进入工作区
- [ ] 8.3 工作区 Statusbar 显示"保存连接"提示 → 点击保存 → 提示消失
- [ ] 8.4 重启应用 → 已保存连接出现在列表 → 点击一键连接
- [ ] 8.5 新建连接 → 填写完整配置 → 保存 → 自动连接进入工作区
- [ ] 8.6 编辑已保存连接 → 修改端口 → 保存 → 列表更新
- [ ] 8.7 删除已保存连接 → 确认 → 从列表移除
