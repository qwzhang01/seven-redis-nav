## ADDED Requirements

### Requirement: 快捷键自定义配置面板
系统 SHALL 在设置页面提供"快捷键"配置面板，以可视化列表展示所有可自定义的快捷键，支持重新绑定和重置为默认值。

#### Scenario: 打开快捷键配置面板
- **WHEN** 用户在设置页面点击"快捷键"菜单项（或按 ⌘,）
- **THEN** 右侧显示快捷键列表，按功能分组（全局 / 键浏览 / CLI / 编辑），每行显示：功能描述、当前绑定、编辑按钮

#### Scenario: 重新绑定快捷键
- **WHEN** 用户点击某行的编辑按钮
- **THEN** 该行进入录制模式（显示"请按下新快捷键..."），用户按下组合键后自动记录，显示新绑定预览

#### Scenario: 确认新绑定
- **WHEN** 用户在录制模式下按下组合键后点击"确认"
- **THEN** 新绑定保存到 SQLite `shortcut_bindings` 表，立即生效，列表更新显示新绑定

#### Scenario: 取消录制
- **WHEN** 用户在录制模式下按 Escape
- **THEN** 取消录制，恢复显示原有绑定，不做任何修改

### Requirement: 快捷键冲突检测
系统 SHALL 在用户录制新快捷键时，实时检测与现有绑定的冲突，给出警告。

#### Scenario: 检测到冲突
- **WHEN** 用户录制的新快捷键与另一个功能的绑定相同
- **THEN** 录制区域显示橙色警告："此快捷键已被「功能名称」使用，继续保存将覆盖原绑定"，提供"继续覆盖"和"重新录制"两个选项

#### Scenario: 系统级快捷键冲突
- **WHEN** 用户录制的快捷键与 macOS 系统级快捷键冲突（如 ⌘Space、⌘Tab）
- **THEN** 显示警告："此快捷键可能与系统快捷键冲突，建议更换"，但允许用户强制保存

### Requirement: 重置快捷键
系统 SHALL 支持将单个快捷键或所有快捷键重置为默认值。

#### Scenario: 重置单个快捷键
- **WHEN** 用户点击某行的"重置"按钮（仅在该行已被自定义时显示）
- **THEN** 该快捷键恢复为默认绑定，从 SQLite `shortcut_bindings` 表删除该记录，立即生效

#### Scenario: 重置所有快捷键
- **WHEN** 用户点击面板顶部的"重置全部为默认"按钮
- **THEN** 弹出确认对话框，确认后清空 SQLite `shortcut_bindings` 表，所有快捷键恢复默认值

### Requirement: 快捷键持久化加载
系统 SHALL 在 App 启动时从 SQLite 加载自定义快捷键绑定，覆盖默认绑定。

#### Scenario: App 启动加载自定义绑定
- **WHEN** App 启动
- **THEN** `useShortcut` composable 从 SQLite `shortcut_bindings` 表读取自定义绑定，合并到默认绑定表中，自定义绑定优先级高于默认绑定
