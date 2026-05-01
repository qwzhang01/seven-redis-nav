## MODIFIED Requirements

### Requirement: 快捷键持久化加载
系统 SHALL 在 App 启动时从 SQLite 加载自定义快捷键绑定，覆盖默认绑定。加载完成后，`handleKeydown` 函数 SHALL 优先查找自定义绑定，再回退到默认绑定，确保自定义快捷键实际生效。

#### Scenario: App 启动加载自定义绑定
- **WHEN** App 启动
- **THEN** `useShortcut` composable 从 SQLite `shortcut_bindings` 表读取自定义绑定，合并到默认绑定表中，自定义绑定优先级高于默认绑定

#### Scenario: 自定义快捷键触发
- **WHEN** 用户按下已自定义的快捷键组合
- **THEN** `handleKeydown` 优先在 `customBindings` 中查找匹配的 action，找到则执行对应操作，不再匹配默认绑定

#### Scenario: 自定义绑定覆盖默认绑定
- **WHEN** 用户将某个 action 的快捷键从默认值改为新组合
- **THEN** 按下新组合键触发该 action，按下原默认组合键不再触发该 action（已被覆盖）

#### Scenario: 无自定义绑定时回退默认
- **WHEN** 某个 action 在 `customBindings` 中无记录
- **THEN** `handleKeydown` 使用默认绑定处理该 action，行为与未自定义时一致
