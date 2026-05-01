## ADDED Requirements

### Requirement: 大 Key 扫描任务
系统 SHALL 提供后台异步大 Key 扫描功能，通过 SCAN 全量遍历 + `MEMORY USAGE key SAMPLES 0` 精确计算每个键的内存占用，生成 Top 100 大 Key 报告。

#### Scenario: 启动大 Key 扫描
- **WHEN** 用户在 Tools Tab 点击"开始扫描"按钮
- **THEN** 后端启动异步扫描任务，前端显示进度条（已扫描键数 / 总键数估算），扫描按钮变为"停止扫描"

#### Scenario: 扫描进度推送
- **WHEN** 扫描任务每处理 1000 个键
- **THEN** 后端通过 Tauri Event `key_analyzer:progress` 推送 `{ scanned: N, total_estimate: M, top_keys: [...] }`，前端实时更新进度条和 Top 列表

#### Scenario: 扫描完成
- **WHEN** 扫描任务遍历完所有键（SCAN cursor 返回 0）
- **THEN** 前端显示最终 Top 100 大 Key 报告，包含：键名、类型、内存大小（格式化为 KB/MB）、编码方式、元素数量

#### Scenario: 停止扫描
- **WHEN** 用户点击"停止扫描"按钮
- **THEN** 后端取消扫描任务，前端显示当前已扫描到的 Top 列表（标注"扫描已中止"）

#### Scenario: 低影响模式
- **WHEN** 用户开启"低影响模式"开关
- **THEN** 扫描任务在每批 SCAN（count=100）后 sleep 10ms，降低对 Redis 服务器的压力

### Requirement: 大 Key 报告展示与导出
系统 SHALL 以表格形式展示 Top 100 大 Key，支持按内存大小/类型排序，支持导出为 CSV。

#### Scenario: 表格排序
- **WHEN** 用户点击表格列头（内存大小 / 类型 / 键名）
- **THEN** 表格按该列升序/降序排序

#### Scenario: 导出 CSV
- **WHEN** 用户点击"导出 CSV"按钮
- **THEN** 生成包含所有扫描结果的 CSV 文件（键名、类型、内存字节数、编码、元素数），通过系统文件保存对话框保存

#### Scenario: 跳转到键
- **WHEN** 用户点击大 Key 报告中某行的键名
- **THEN** 切换到 Browser Tab，键面板定位并选中该键，工作区显示键详情

### Requirement: 过期 Key TTL 分布分析
系统 SHALL 提供 TTL 分布直方图，展示当前 DB 中键的过期时间分布情况。

#### Scenario: 生成 TTL 分布
- **WHEN** 用户在 Tools Tab 点击"分析 TTL 分布"按钮
- **THEN** 后端通过 `key_ttl_distribution` IPC 执行 SCAN + TTL 抽样（最多 10000 个键），返回分布数据

#### Scenario: 直方图展示
- **WHEN** TTL 分布数据返回
- **THEN** 前端以 ECharts 柱状图展示：X 轴为时间区间（永久 / < 1h / 1h-24h / 1d-7d / > 7d），Y 轴为键数量，每个柱子显示百分比

#### Scenario: 即将过期警告
- **WHEN** TTL < 1h 的键数量超过总键数的 10%
- **THEN** 直方图顶部显示橙色警告："有 N 个键将在 1 小时内过期，请注意"

### Requirement: 数据脱敏规则配置
系统 SHALL 提供数据脱敏规则的配置界面，支持 glob 模式匹配键名，对匹配的键值进行掩码显示。

#### Scenario: 添加脱敏规则
- **WHEN** 用户在设置面板的"数据脱敏"页面点击"添加规则"
- **THEN** 新增一行规则输入：键名模式（glob，如 `*token*`）+ 掩码字符（默认 `***`）+ 启用开关

#### Scenario: 规则生效
- **WHEN** 用户保存脱敏规则后，在 Browser Workspace 查看匹配规则的键
- **THEN** 键的 value 显示为掩码（如 `***`），元数据栏显示"已脱敏"标识，编辑按钮仍可用（编辑时显示原始值）

#### Scenario: 规则禁用
- **WHEN** 用户关闭某条规则的启用开关
- **THEN** 该规则立即失效，Browser Workspace 中对应键恢复显示原始值（无需刷新）
