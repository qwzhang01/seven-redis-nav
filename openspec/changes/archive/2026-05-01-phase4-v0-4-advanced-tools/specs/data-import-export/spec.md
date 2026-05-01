## ADDED Requirements

### Requirement: JSON 格式导出选中键
系统 SHALL 支持将 Browser Workspace 中选中的一个或多个键导出为 JSON 文件，格式为标准化的 `RedisExport` 结构。

#### Scenario: 导出选中键
- **WHEN** 用户在键面板多选若干键后，点击工具栏"导出"按钮
- **THEN** 弹出导出对话框，显示预估文件大小和键数量，用户确认后触发 `export_keys_json` IPC，后端生成 JSON 文件并通过系统文件保存对话框保存到用户指定路径

#### Scenario: 导出格式
- **WHEN** 导出操作完成
- **THEN** 生成的 JSON 文件结构为：`{ "version": "1.0", "connection": { "host": "...", "port": 6379, "db": 0 }, "exported_at": "ISO8601", "keys": [{ "key": "...", "type": "string|hash|list|set|zset|stream", "ttl": -1, "value": {...} }] }`

#### Scenario: 大 value 截断
- **WHEN** 某个键的 value 大小超过 1MB
- **THEN** 该键的 value 字段替换为 `{ "truncated": true, "size_bytes": N, "preview": "前100字节..." }`，并在导出完成后显示截断警告

### Requirement: JSON 格式导出整个 DB
系统 SHALL 支持导出当前连接的整个 DB 中所有键，导出前显示预估大小和键数量。

#### Scenario: 导出整个 DB
- **WHEN** 用户在键面板工具栏点击"导出全部"
- **THEN** 显示确认对话框，包含当前 DB 键数量和预估文件大小（基于 MEMORY USAGE 抽样），用户确认后开始导出，显示进度条（每 100 个键更新一次）

#### Scenario: 导出超大 DB 警告
- **WHEN** 当前 DB 键数量超过 10000 或预估文件大小超过 100MB
- **THEN** 显示警告："数据量较大，建议使用键过滤后分批导出"，提供"继续"和"取消"选项

### Requirement: JSON 格式导入
系统 SHALL 支持从符合 `RedisExport` 格式的 JSON 文件导入键值对到当前连接的 DB。

#### Scenario: 选择导入文件
- **WHEN** 用户点击"导入"按钮
- **THEN** 打开系统文件选择对话框，过滤 `.json` 文件，选择后解析文件头部验证格式版本

#### Scenario: 导入预览
- **WHEN** JSON 文件解析成功
- **THEN** 显示导入预览：键数量、类型分布、是否有冲突键（已存在于当前 DB），提供"跳过冲突"和"覆盖冲突"两个选项

#### Scenario: 导入执行
- **WHEN** 用户确认导入
- **THEN** 后端逐键执行写入（`key_set` 逻辑），显示进度条，完成后显示导入报告（成功数/跳过数/失败数）

#### Scenario: 导入格式不匹配
- **WHEN** 选择的 JSON 文件不符合 `RedisExport` 格式（缺少 `version` 或 `keys` 字段）
- **THEN** 显示错误："文件格式不正确，请选择由 Seven Redis Nav 导出的 JSON 文件"

### Requirement: RDB 文件只读解析
系统 SHALL 支持选择本地 RDB 文件进行只读解析，将解析结果以只读 Browser Workspace 展示。

#### Scenario: 打开 RDB 文件
- **WHEN** 用户点击"打开 RDB 文件"按钮
- **THEN** 打开系统文件选择对话框，过滤 `.rdb` 文件，选择后触发 `rdb_parse_file` IPC

#### Scenario: RDB 解析成功
- **WHEN** RDB 文件解析完成
- **THEN** 在键面板显示解析出的所有键（标注"来自 RDB 文件"），可在 Browser Workspace 查看键值（只读，不可编辑），键面板工具栏显示"只读模式"标识

#### Scenario: RDB 版本不支持
- **WHEN** RDB 文件版本超过支持范围（> v10）
- **THEN** 显示错误："不支持 RDB 版本 N（Redis 7.4+），当前仅支持 RDB v1-v10"

#### Scenario: RDB 文件过大警告
- **WHEN** 选择的 RDB 文件大小超过 500MB
- **THEN** 显示警告："文件较大（N MB），解析可能需要较长时间，是否继续？"
