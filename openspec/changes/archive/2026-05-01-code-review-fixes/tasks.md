## 1. Rust 后端 - 死锁与锁顺序修复

- [x] 1.1 重构 `export_keys_json`：在获取 session 锁之前先通过 manager 获取并克隆 config，释放 manager 锁后再获取 session 锁
- [x] 1.2 验证 `export_keys_json` 中不存在任何"持有 session 锁期间再次锁 manager"的代码路径
- [x] 1.3 重构 `export_db_json`：将 SCAN 循环和 key 导出循环合并为持锁一次完成，移除逐 key 加锁逻辑

## 2. Rust 后端 - 序列化与事件修复

- [x] 2.1 在 `ConnectionState` 枚举上添加 `#[serde(rename_all = "snake_case")]` 标注
- [x] 2.2 验证 heartbeat 发出的 `connection:state` 事件中 `state` 字段值为全小写（`connected` / `disconnected`）
- [x] 2.3 确认前端 `types/connection.d.ts` 中的状态类型定义与修复后的序列化值一致

## 3. Rust 后端 - key_analyzer Pipeline 改造

- [x] 3.1 参照 `key_browser.rs` 中 `get_key_metas` 的 pipeline 实现，重构 `key_analyzer.rs` 中的 key 分析循环
- [x] 3.2 将每批 key（100 个）的 MEMORY USAGE、TYPE、OBJECT ENCODING、元素数量命令合并为一个 pipeline 批量发送
- [x] 3.3 确保 pipeline 中单个命令失败时错误被正确收集，不中断整批处理

## 4. Rust 后端 - CSV 导出实现

- [x] 4.1 实现 `key_scan_memory_export_csv` 命令：从任务状态存储中读取已完成扫描的 top_keys 数据
- [x] 4.2 将 top_keys 数据格式化为完整 CSV 内容（键名、类型、内存字节数、编码、元素数量）
- [x] 4.3 移除占位实现（仅返回表头的 `Ok(format!(...))` 代码）

## 5. Rust 后端 - 事务保护

- [x] 5.1 在 `config_store.rs` 的 `masking_rule_reorder` 函数中，使用 `sqlx` 事务包裹所有 UPDATE 操作
- [x] 5.2 确保事务失败时自动回滚，函数返回错误

## 6. 前端 - 自定义快捷键修复

- [x] 6.1 在 `useShortcut.ts` 的 `handleKeydown` 函数中，优先在 `customBindings` 中查找当前按键对应的 action
- [x] 6.2 仅当 `customBindings` 中无匹配时，回退到默认绑定表查找
- [x] 6.3 编写手动测试：加载自定义绑定后，按下自定义键确认 action 被触发

## 7. 前端 - serverVersion 更新

- [x] 7.1 在 `connection.ts` store 的连接成功回调中，调用 IPC 获取 Redis `INFO server` 信息
- [x] 7.2 解析 `INFO server` 响应中的 `redis_version` 字段，更新 `serverVersion.value`
- [x] 7.3 连接断开时将 `serverVersion.value` 重置为 `null`

## 8. 前端 - IPC 封装补全

- [x] 8.1 在 `src/ipc/phase4.ts` 中添加 `cliHistoryGetTab(tabId: string)` 封装函数，调用后端 `cli_history_get_tab` 命令
- [x] 8.2 修复 `healthCheckExportMarkdown` 函数签名，添加 `connId: string` 参数，并在 `invoke` 调用中传入

## 9. 前端 - 多 Tab CLI 历史持久化

- [x] 9.1 确认 `cli_history` 表已有 `tab_id` 字段（或通过 migration 添加可空的 `tab_id` 字段）
- [x] 9.2 在 `terminal.ts` store 中，多 Tab 模式下执行命令时将历史写入 SQLite（携带 `tab_id`）
- [x] 9.3 在 `terminal.ts` store 中，创建/恢复 CLI 标签页时调用 `cliHistoryGetTab` 加载持久化历史
- [x] 9.4 确保单 Tab 模式的历史持久化行为不受影响（向后兼容）

## 10. 验证与回归测试

- [x] 10.1 手动测试：导出选中键（`export_keys_json`）正常完成，无死锁或超时
- [x] 10.2 手动测试：导出整个 DB（`export_db_json`）正常完成，进度条正常更新
- [x] 10.3 手动测试：大 Key 扫描完成后点击"导出 CSV"，确认 CSV 包含实际数据行
- [x] 10.4 手动测试：断开并重连 Redis，确认 Sidebar 连接状态图标正确切换（依赖 heartbeat 序列化修复）
- [x] 10.5 手动测试：设置自定义快捷键后，按下新组合键确认功能触发
- [x] 10.6 手动测试：连接 Redis 后，确认 UI 中显示正确的 Redis 版本号
- [x] 10.7 手动测试：多 Tab CLI 中执行命令，重启 App 后确认历史记录可通过 ↑↓ 导航访问
- [x] 10.8 手动测试：点击健康报告"导出报告"按钮，确认导出成功无报错
- [x] 10.9 手动测试：拖拽调整脱敏规则顺序，确认顺序持久化且重启后保持
