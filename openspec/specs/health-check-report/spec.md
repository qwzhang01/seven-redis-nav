## MODIFIED Requirements

### Requirement: 健康报告导出
系统 SHALL 支持将健康报告导出为 Markdown 格式文本文件。前端调用 `healthCheckExportMarkdown` IPC 时 SHALL 同时传入 `connId` 和 `report` 参数，与后端命令签名保持一致。

#### Scenario: 导出 Markdown
- **WHEN** 用户点击报告面板的"导出报告"按钮
- **THEN** 生成 Markdown 文件，包含：报告标题（含连接信息和生成时间）、总体健康分、4 个维度评分表格、10 项指标详情表格、改进建议列表，通过系统文件保存对话框保存

#### Scenario: 导出文件命名
- **WHEN** 导出对话框打开
- **THEN** 默认文件名为 `redis-health-report-{host}-{YYYY-MM-DD}.md`

#### Scenario: 导出 IPC 参数完整
- **WHEN** 前端调用 `healthCheckExportMarkdown` IPC
- **THEN** 调用携带 `connId`（当前连接 ID）和 `report`（健康报告数据）两个参数，后端命令正常执行，不报参数缺失错误
