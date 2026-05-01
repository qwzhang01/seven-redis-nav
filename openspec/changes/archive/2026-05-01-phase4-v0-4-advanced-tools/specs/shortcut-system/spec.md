## MODIFIED Requirements

### Requirement: 快捷键绑定持久化
快捷键系统 SHALL 支持将自定义绑定持久化到 SQLite `shortcut_bindings` 表（字段：`action TEXT PRIMARY KEY, binding TEXT NOT NULL, updated_at TEXT`）。App 启动时 SHALL 自动从数据库加载自定义绑定，合并到默认绑定表，自定义绑定优先级高于默认值。

原有的默认快捷键绑定（⌘K / ⌘N / ⌘T / ⌘W / ⌘1 / ⌘2 / ⌘F / ⌘L / ⌘E / ⌘D / ⌘+Enter / ⌘+Shift+R / ⌘,）SHALL 保持不变，作为 fallback。

#### Scenario: 加载自定义绑定
- **WHEN** App 启动，SQLite `shortcut_bindings` 表中存在自定义绑定记录
- **THEN** `useShortcut` composable 将自定义绑定合并到默认绑定表，对应 action 的快捷键使用自定义值

#### Scenario: 无自定义绑定时使用默认值
- **WHEN** App 启动，SQLite `shortcut_bindings` 表为空
- **THEN** 所有快捷键使用默认绑定，行为与 Phase 1 完全一致
