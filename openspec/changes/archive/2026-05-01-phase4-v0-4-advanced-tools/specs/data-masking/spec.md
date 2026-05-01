## ADDED Requirements

### Requirement: 数据脱敏规则配置面板
系统 SHALL 在设置页面提供"数据脱敏"配置面板，支持添加、编辑、删除、启用/禁用脱敏规则。

#### Scenario: 打开脱敏配置面板
- **WHEN** 用户在设置页面点击"数据脱敏"菜单项
- **THEN** 右侧显示脱敏规则列表，包含：规则序号、键名模式（glob）、掩码字符、启用开关、删除按钮

#### Scenario: 添加脱敏规则
- **WHEN** 用户点击"添加规则"按钮
- **THEN** 列表底部新增一行空规则，键名模式输入框自动聚焦，用户填写后按 Enter 或点击保存图标确认

#### Scenario: 规则持久化
- **WHEN** 用户保存脱敏规则
- **THEN** 规则写入 SQLite `masking_rules` 表，App 重启后规则仍然生效

### Requirement: 数据脱敏实时渲染
系统 SHALL 在 Browser Workspace 的所有 Viewer 组件中，对匹配脱敏规则的键值进行掩码渲染。

#### Scenario: String 类型脱敏
- **WHEN** 用户查看一个键名匹配脱敏规则的 String 类型键
- **THEN** StringViewer 中的 value 显示为掩码字符（如 `***`），元数据栏显示"🔒 已脱敏"标识

#### Scenario: Hash 类型脱敏
- **WHEN** 用户查看一个键名匹配脱敏规则的 Hash 类型键
- **THEN** HashViewer 中所有字段的 value 列显示为掩码，字段名（field）不脱敏

#### Scenario: 编辑脱敏键
- **WHEN** 用户点击已脱敏键的编辑按钮
- **THEN** 编辑弹窗中显示原始值（不脱敏），允许正常编辑和保存

#### Scenario: 键面板脱敏
- **WHEN** 键面板中显示匹配脱敏规则的键
- **THEN** 键名正常显示（不脱敏），仅 value 在 Browser Workspace 中脱敏

### Requirement: 脱敏规则 glob 模式匹配
系统 SHALL 使用 glob 模式（`*` 匹配任意字符，`?` 匹配单个字符）对键名进行匹配。

#### Scenario: 通配符匹配
- **WHEN** 脱敏规则键名模式为 `*token*`
- **THEN** 键名包含 "token" 的所有键（如 `user:token:123`、`auth_token`）均触发脱敏

#### Scenario: 精确匹配
- **WHEN** 脱敏规则键名模式为 `secret`（无通配符）
- **THEN** 仅键名完全等于 "secret" 的键触发脱敏

#### Scenario: 多规则匹配
- **WHEN** 某个键名同时匹配多条脱敏规则
- **THEN** 使用第一条匹配规则的掩码字符（按规则列表顺序）
