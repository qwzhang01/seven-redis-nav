## MODIFIED Requirements

### Requirement: CLI 工作区架构
CLI 工作区 SHALL 从单终端架构升级为多标签页架构。`CliWorkspace.vue` SHALL 包含 `CliTabBar`（标签页栏）和 `CliTabPanel`（标签页内容）两个子组件。每个标签页 SHALL 持有独立的 `CliSession`（Redis 连接 + 命令历史 + 输出缓冲区）。

原有单 Tab 的所有功能（命令执行、历史导航、输出着色、危险命令拦截、⌘L 清屏）SHALL 在每个标签页中完整保留，行为不变。

#### Scenario: 单标签页向后兼容
- **WHEN** 用户首次打开 CLI Tab（只有一个默认标签页）
- **THEN** 界面与 Phase 1 单 Tab CLI 视觉完全一致，标签页栏仅显示一个标签，"×" 关闭按钮隐藏

#### Scenario: 多标签页并存
- **WHEN** 用户通过 ⌘T 新建了多个标签页
- **THEN** 标签页栏显示所有标签，每个标签显示名称和关闭按钮，当前激活标签高亮（白底红字，与 Toolbar Tab 风格一致）

#### Scenario: 标签页状态隔离
- **WHEN** 用户在标签页 A 执行 `SELECT 5` 切换 DB
- **THEN** 标签页 B 的 DB 状态不受影响，两个标签页的 DB 选择完全独立
