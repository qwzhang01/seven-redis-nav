## Context

Phase 3 (v0.3) 建立在 Phase 1（MVP：连接 + 浏览 + CRUD + CLI）和 Phase 2（SSH/TLS + 批量 + 监控 + 慢查询）的基础上。当前架构已有：
- **Rust 后端**：`connection_manager` / `key_browser` / `data_ops` / `terminal` / `monitor` / `slowlog` / `pubsub` / `config_ops` / `ssh_tunnel` 等服务模块
- **Vue 前端**：6 Tab 工作区（Browser / CLI / Monitor / Slowlog / Pubsub / Config）
- **IPC 合约**：`pubsub_subscribe` / `pubsub_unsubscribe` / `slowlog_get` / `slowlog_reset` / `config_get_all` / `config_set` / `server_info` / `monitor_start` / `monitor_stop` 等

Phase 3 要在此基础上扩展：Pub/Sub 增强、Config 增强、扩展类型（Stream/Bitmap/HyperLogLog）、JSON 智能识别、二进制三视图。

## Goals / Non-Goals

**Goals:**
- 为运维场景补全 Pub/Sub 和 Config Tab 的核心操作能力
- 支持 Redis 5 种扩展数据类型的可视化查看与基本操作
- 自动识别 JSON 内容，提供 CodeMirror 6 编辑器体验
- 对二进制内容提供 Hex/Base64/文本三视图

**Non-Goals:**
- 不实现 Stream 的 XREAD/XREADGROUP 消费者阻塞等待（仅用 XRANGE/XREVRANGE 分页）
- 不实现 Bitmap 的逐 bit 编辑（仅可视化和快捷查询）
- 不实现 HyperLogLog 的实时合并预览
- 不实现 JSON Schema 校验
- 不实现全文搜索索引（JSON 搜索仅限 CodeMirror 6 内置搜索）

## Decisions

### 1. 扩展类型查看器采用独立组件而非通用 Viewer 扩展

**选择**：为 Stream/Bitmap/HyperLogLog 各建独立 Viewer 组件（`StreamViewer.vue` / `BitmapViewer.vue` / `HyperLogLogViewer.vue`）

**理由**：
- 每种扩展类型的数据结构和展示需求差异极大（Stream 是时间序列条目、Bitmap 是位网格、HyperLogLog 是基数 + 内部寄存器）
- 独立组件遵循单一职责，避免 `StringViewer.vue` 过度膨胀
- 后端 IPC 命令也各自独立（`stream_*` / `bitmap_*` / `hll_*`），前后端一一对应

**替代方案**：在 `StringViewer.vue` 中用 `v-if` 切换 → 违反开闭原则，每次加类型都要改同一个文件

### 2. JSON 检测使用轻量解析而非正则

**选择**：尝试 `JSON.parse()` 成功即判定为 JSON；对超大字符串（>1MB）跳过自动检测

**理由**：
- `JSON.parse()` 是确定性的，不存在正则误判
- 性能开销可接受（数据已从后端拿到，纯前端操作）
- 超大字符串跳过检测避免解析阻塞 UI

**替代方案**：正则预判 `^\s*[\{\[]` → 可能有注释、尾逗号等伪 JSON 导致误判

### 3. 二进制检测基于不可打印字符比例

**选择**：当字符串中 > 30% 字符不在 ASCII 32-126 范围内时，判定为二进制内容，激活三视图

**理由**：
- 30% 阈值能有效区分正常多语言文本（含 CJK 字符虽 > 127 但仍是文本）和真正的二进制数据
- 对于包含零字节（`\0`）的内容直接判定为二进制，无需比例检测

**替代方案**：固定字节范围判断（如出现 0x00）→ 某些编码的合法文本也包含高字节

### 4. Pub/Sub 发布使用独立 IPC 而非复用 cli_exec

**选择**：新增 `pubsub_publish` IPC 命令，专用于 Pub/Sub 发布

**理由**：
- `cli_exec` 返回值是通用 `RedisReply`，需要前端自行解析
- `pubsub_publish` 直接返回接收者数量（`u64`），类型安全
- 发布操作与 CLI 执行是不同的交互场景，解耦更清晰

**替代方案**：复用 `cli_exec` 返回通用结果 → 缺少类型安全，前端需要额外解析

### 5. Config Tab 采用前端 diff 而非后端追踪

**选择**：前端维护 `originalValues` Map，编辑时实时对比，提交时生成 diff

**理由**：
- 后端无需维护变更状态，保持无状态
- 前端可以实时高亮差异，提供即时反馈
- 提交时只发送变更项，减少网络开销

**替代方案**：后端缓存原始值 → 增加后端复杂度，且前端需要额外 IPC 获取 diff

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| CodeMirror 6 包体积（≈250KB）可能影响加载性能 | 使用 Vite code splitting，仅在使用 JSON 编辑器时懒加载；gzip 后约 80KB |
| Stream 分页在大数据集（>100万条目）下 XRANGE 性能下降 | 后端限制每页最大 500 条；前端提供"跳转到时间戳"快捷定位 |
| Bitmap 可视化对大 Key（>1MB）渲染慢 | 按需加载：只渲染可视区域的网格行，类似虚拟滚动 |
| JSON 自动检测对超大字符串可能阻塞 UI | >1MB 跳过自动检测，改为手动切换按钮 |
| Pub/Sub 定时重复发送可能导致服务器洪泛 | 后端限流（最大 10 次/秒）；前端显示倒计时和剩余次数 |
| 二进制检测 30% 阈值可能误判 | 对包含零字节的内容直接判定为二进制，无需比例检测 |

## Migration Plan

1. **阶段一**：新增扩展类型查看器 + JSON/二进制检测（纯前端变更，无破坏性）
2. **阶段二**：增强 Pub/Sub 和 Config Tab（新增 IPC + 前端组件，向后兼容）
3. **阶段三**：集成测试 + 性能调优
4. **回滚**：所有变更通过 feature flag 控制；新组件不加载时回退到原有 fallback 行为

## Open Questions

1. HyperLogLog 的 `PFMERGE` 操作是否需要目标 key 选择器？（倾向于：是，用下拉选择现有 key）
2. Stream 的 Consumer Groups 列表是否需要支持 `XGROUP CREATE`？（倾向于：v0.3 仅查看，v0.4 增加创建）
3. 二进制三视图是否也需要覆盖 Hash 字段和 List 元素？（倾向于：是，统一检测逻辑）
