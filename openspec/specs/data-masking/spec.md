## MODIFIED Requirements

### Requirement: 脱敏规则排序
系统 SHALL 支持用户通过拖拽调整脱敏规则的显示和匹配顺序。排序操作 SHALL 在数据库事务中执行，确保所有规则的 `sort_order` 原子性更新，部分失败时全部回滚。

#### Scenario: 拖拽排序
- **WHEN** 用户拖拽某条规则到新位置
- **THEN** 所有受影响规则的 `sort_order` 在同一事务中更新，操作成功后列表按新顺序显示

#### Scenario: 排序持久化
- **WHEN** 排序操作成功
- **THEN** 新顺序写入 SQLite `masking_rules` 表的 `sort_order` 字段，App 重启后规则按新顺序加载

#### Scenario: 排序失败回滚
- **WHEN** 排序更新过程中发生数据库错误
- **THEN** 事务回滚，所有规则的 `sort_order` 恢复到操作前的状态，前端显示错误提示，规则列表恢复原顺序

#### Scenario: 多规则匹配优先级
- **WHEN** 某个键名同时匹配多条脱敏规则
- **THEN** 使用 `sort_order` 最小（排序最靠前）的规则的掩码字符
