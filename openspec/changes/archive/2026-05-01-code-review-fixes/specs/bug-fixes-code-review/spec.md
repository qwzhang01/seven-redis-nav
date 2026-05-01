## ADDED Requirements

### Requirement: 导出操作无死锁保证
系统 SHALL 确保 `export_keys_json` 命令在执行过程中不产生锁嵌套，config 获取 SHALL 在 session 锁获取之前完成。

#### Scenario: 导出选中键时无死锁
- **WHEN** 用户触发 `export_keys_json` IPC
- **THEN** 后端先获取 connection config（释放 manager 锁），再获取 session 锁执行 Redis 命令，整个过程不产生锁嵌套，命令正常完成

#### Scenario: 并发导出与心跳不互相阻塞
- **WHEN** 导出操作进行中，heartbeat 同时发送 PING
- **THEN** heartbeat 使用独立连接，不受导出操作的 session 锁影响，两者并发执行

### Requirement: 连接状态事件序列化一致性
系统 SHALL 确保后端发出的 `connection:state` 事件中，`state` 字段值与前端类型定义完全一致，使用全小写格式（`connected` / `disconnected` / `reconnecting`）。

#### Scenario: 连接成功事件
- **WHEN** heartbeat 检测到连接恢复
- **THEN** 发出 `connection:state` 事件，`state` 字段值为 `"connected"`（全小写），前端状态正确更新为已连接

#### Scenario: 连接断开事件
- **WHEN** heartbeat 检测到连接断开
- **THEN** 发出 `connection:state` 事件，`state` 字段值为 `"disconnected"`（全小写），前端状态正确更新为已断开

### Requirement: 脱敏规则排序操作原子性
系统 SHALL 确保 `masking_rule_reorder` 操作在数据库事务中执行，要么全部成功，要么全部回滚。

#### Scenario: 排序操作成功
- **WHEN** 用户拖拽调整脱敏规则顺序
- **THEN** 所有规则的 `sort_order` 在同一事务中更新，操作成功后返回

#### Scenario: 排序操作部分失败回滚
- **WHEN** 排序更新过程中发生数据库错误
- **THEN** 事务回滚，所有规则的 `sort_order` 恢复到操作前的状态，不产生部分更新的不一致数据
