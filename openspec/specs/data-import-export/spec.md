## MODIFIED Requirements

### Requirement: JSON 格式导出选中键
系统 SHALL 支持将 Browser Workspace 中选中的一个或多个键导出为 JSON 文件，格式为标准化的 `RedisExport` 结构。导出操作 SHALL 先获取 connection config，再获取 session 锁，不得在持有 session 锁期间再次获取 manager 锁。

#### Scenario: 导出选中键
- **WHEN** 用户在键面板多选若干键后，点击工具栏"导出"按钮
- **THEN** 弹出导出对话框，显示预估文件大小和键数量，用户确认后触发 `export_keys_json` IPC，后端生成 JSON 文件并通过系统文件保存对话框保存到用户指定路径

#### Scenario: 导出格式
- **WHEN** 导出操作完成
- **THEN** 生成的 JSON 文件结构为：`{ "version": "1.0", "connection": { "host": "...", "port": 6379, "db": 0 }, "exported_at": "ISO8601", "keys": [{ "key": "...", "type": "string|hash|list|set|zset|stream", "ttl": -1, "value": {...} }] }`

#### Scenario: 大 value 截断
- **WHEN** 某个键的 value 大小超过 1MB
- **THEN** 该键的 value 字段替换为 `{ "truncated": true, "size_bytes": N, "preview": "前100字节..." }`，并在导出完成后显示截断警告

#### Scenario: 导出无死锁
- **WHEN** `export_keys_json` 命令执行
- **THEN** 后端先通过 manager 获取 config 并释放 manager 锁，再获取 session 锁执行 Redis 命令，不产生锁嵌套

### Requirement: JSON 格式导出整个 DB
系统 SHALL 支持导出当前连接的整个 DB 中所有键，导出前显示预估大小和键数量。导出操作 SHALL 持锁完成整个 SCAN + GET 循环，避免逐 key 加锁的性能开销。

#### Scenario: 导出整个 DB
- **WHEN** 用户在键面板工具栏点击"导出全部"
- **THEN** 显示确认对话框，包含当前 DB 键数量和预估文件大小（基于 MEMORY USAGE 抽样），用户确认后开始导出，显示进度条（每 100 个键更新一次）

#### Scenario: 导出超大 DB 警告
- **WHEN** 当前 DB 键数量超过 10000 或预估文件大小超过 100MB
- **THEN** 显示警告："数据量较大，建议使用键过滤后分批导出"，提供"继续"和"取消"选项

#### Scenario: 导出性能
- **WHEN** 导出包含 1000 个键的 DB
- **THEN** 后端持锁完成整个导出循环（不逐 key 加锁），导出时间相比逐 key 加锁方式显著缩短

### Requirement: 大 Key 内存分析 CSV 导出
系统 SHALL 支持将大 Key 扫描结果导出为真实的 CSV 文件，CSV 内容 SHALL 包含所有已扫描到的 Top Key 数据，不得返回仅含表头的占位内容。

#### Scenario: 导出 CSV
- **WHEN** 用户点击"导出 CSV"按钮
- **THEN** 生成包含所有扫描结果的 CSV 文件（键名、类型、内存字节数、编码、元素数），通过系统文件保存对话框保存

#### Scenario: CSV 内容完整性
- **WHEN** 扫描任务已完成或已有部分结果
- **THEN** 导出的 CSV 文件包含实际的键数据行，不得仅返回表头行或注释行

#### Scenario: 表格排序
- **WHEN** 用户点击表格列头（内存大小 / 类型 / 键名）
- **THEN** 表格按该列升序/降序排序

#### Scenario: 跳转到键
- **WHEN** 用户点击大 Key 报告中某行的键名
- **THEN** 切换到 Browser Tab，键面板定位并选中该键，工作区显示键详情
