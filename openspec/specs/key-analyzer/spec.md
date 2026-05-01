## MODIFIED Requirements

### Requirement: 大 Key 扫描任务
系统 SHALL 提供后台异步大 Key 扫描功能，通过 SCAN 全量遍历 + `MEMORY USAGE key SAMPLES 0` 精确计算每个键的内存占用，生成 Top 100 大 Key 报告。扫描过程中对每批 key 的 MEMORY USAGE、TYPE、OBJECT ENCODING、元素数量命令 SHALL 使用 Redis pipeline 批量执行，不得串行逐个发送。

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

#### Scenario: Pipeline 批量执行
- **WHEN** 扫描任务处理一批 key（默认 100 个）
- **THEN** 后端将该批 key 的 MEMORY USAGE、TYPE、OBJECT ENCODING、元素数量命令合并为一个 pipeline 批量发送，减少网络往返次数

#### Scenario: 低影响模式
- **WHEN** 用户开启"低影响模式"开关
- **THEN** 扫描任务在每批 SCAN（count=100）后 sleep 10ms，降低对 Redis 服务器的压力
