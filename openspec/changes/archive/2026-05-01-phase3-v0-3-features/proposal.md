## Why

Phase 2（v0.2）交付了 SRE/后端工程师场景的核心能力（SSH/TLS/监控/慢日志/Pub/Sub 基础）。Phase 3（v0.3）的目标是把产品推向**中大型团队日常运维**：当运维人员在排查线上问题时，他们既要能精确订阅 keyspace 通知、在线下发配置变更，又要能查看 Stream / Bitmap / HyperLogLog 这类非典型数据结构，还要在面对一个 String 时看到「这其实是 JSON」的美化视图。路线图 Phase 3 章节将其对齐到 E-08 ~ E-10 三个 Epic。现在 Phase 2 主体已归档，是启动 Phase 3 的合适时机。

## What Changes

- **增强** Pub/Sub：新增「发布消息」面板（channel + payload + 定时重复发送）、per-channel 订阅暂停、消息本地导出（JSON/NDJSON），以及 keyspace 通知快捷订阅预设（`__keyspace@*__:*` / `__keyevent@*__:*`）
- **增强** 服务器配置 Tab：新增 `CONFIG REWRITE` 一键落盘按钮、`CONFIG RESETSTAT` 统计清零、修改前后差异面板（diff）、按内置分组规则（Memory/Persistence/Replication/Security/Network/Clients/Slowlog/Advanced/Other）重新分类展示、危险参数（`bind`/`protected-mode`/`requirepass` 等）二次确认
- **新增** 扩展类型查看器：
  - Stream：XRANGE/XREVRANGE 分页 + Consumer Groups 列表 + Pending 列表 + XADD/XDEL
  - Bitmap：位图可视化（32×N 网格，每 bit 一个色块）+ `BITCOUNT`/`BITPOS` 快捷按钮 + 按字节预览
  - HyperLogLog：基数估算结果 + `PFADD` 快速输入 + `PFMERGE` 多键合并
- **新增** JSON 智能识别：String 类型自动探测内容是否是合法 JSON，是则切换到 CodeMirror 6 JSON 编辑器（语法高亮 + 代码折叠 + 搜索 + 美化/压缩按钮）；否则回退到纯文本
- **新增** 二进制三视图：String / Hash 字段 / List 元素内容探测为二进制（含不可打印字符）时，提供 Hex / Base64 / 文本 三个切换视图
- **依赖新增**：CodeMirror 6（`@codemirror/state` / `@codemirror/view` / `@codemirror/lang-json` / `@codemirror/search`）

## Capabilities

### New Capabilities

- `stream-viewer`: Stream 类型的分页浏览、Consumer Groups 查看、条目增删
- `bitmap-viewer`: Bitmap 类型的可视化网格展示与位操作快捷命令
- `hyperloglog-viewer`: HyperLogLog 类型的基数展示与 PFADD/PFMERGE 操作
- `json-smart-detection`: String 内容 JSON 自动识别与 CodeMirror 6 编辑器集成
- `binary-data-views`: 二进制值的 Hex / Base64 / 文本 三视图切换机制
- `pubsub-publisher`: 频道消息发布面板（一次性 + 定时重复）
- `pubsub-export`: 消息流本地导出为 JSON/NDJSON
- `keyspace-notification-presets`: keyspace/keyevent 通知订阅的快捷预设与 `notify-keyspace-events` 配置检查

### Modified Capabilities

- `pubsub-workspace`: 新增发布/导出/暂停单频道/预设订阅等需求
- `server-config-workspace`: 新增 `CONFIG REWRITE` / `CONFIG RESETSTAT` / 危险参数确认 / 差异面板 / 重新分组等需求
- `data-viewer`: 扩展类型分派（Stream/Bitmap/HyperLogLog）从 fallback 升级为一等支持；JSON 识别与二进制视图挂接到 StringViewer
- `data-editor`: Stream 新增 XADD/XDEL；JSON 编辑模式下使用 CodeMirror 6 替代 textarea
- `ipc-foundation`: 新增 Stream/Bitmap/HyperLogLog 相关 IPC 命令族以及 `pubsub_publish` / `config_rewrite` / `config_resetstat`

## Impact

- **前端新增**：`components/workspaces/browser/StreamViewer.vue` / `BitmapViewer.vue` / `HyperLogLogViewer.vue` / `JsonEditor.vue` / `BinaryViewToggle.vue`；`components/workspaces/pubsub/PublishPanel.vue` / `MessageExporter.vue`；`components/workspaces/config/ConfigDiffPanel.vue`
- **前端修改**：`BrowserWorkspace.vue` 的类型分派表、`StringViewer.vue` 挂接 JSON/二进制识别、`PubsubWorkspace.vue` 顶部加发布/预设订阅按钮、`ServerConfigWorkspace.vue` 头部加 REWRITE/RESETSTAT 按钮与 diff 面板、`stores/pubsub.ts` 支持发布与导出、`stores/serverConfig.ts` 支持差异跟踪、新增 `stores/streamBrowser.ts`
- **后端新增**（`src-tauri/src/commands/`）：`stream.rs`（`stream_range` / `stream_rev_range` / `stream_add` / `stream_del` / `stream_groups` / `stream_pending`）、`bitmap.rs`（`bitmap_get_range` / `bitcount` / `bitpos` / `setbit`）、`hll.rs`（`pfcount` / `pfadd` / `pfmerge`）；`commands/pubsub.rs` 扩展 `pubsub_publish`；`commands/server_config.rs` 扩展 `config_rewrite` / `config_resetstat` / `config_get_notify_keyspace_events`
- **后端模型**：新增 `StreamEntry` / `StreamGroup` / `PendingEntry` / `BitmapChunk` / `HllStats`；`types/data.d.ts` 对应同步
- **依赖**：`package.json` 新增 `codemirror` / `@codemirror/lang-json` / `@codemirror/search` / `@codemirror/state` / `@codemirror/view` / `@codemirror/commands`（≈ 250KB，gzip 后 ≈ 80KB，在性能预算内）
- **IPC 新增**：`stream_*` / `bitmap_*` / `hll_*` / `pubsub_publish` / `config_rewrite` / `config_resetstat`
- **测试**：新增 `StreamViewer.test.ts` / `JsonEditor.test.ts` / `BinaryViewToggle.test.ts`；`stores/pubsub.test.ts` 覆盖 publish/export；`stores/serverConfig.test.ts` 覆盖 rewrite/resetstat；总体覆盖率阈值仍为 ≥ 70%
