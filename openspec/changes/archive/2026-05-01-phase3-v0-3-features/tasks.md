## 1. 基础设施：IPC 命令扩展与依赖安装

- [x] 1.1 Rust 后端：新增 models — StreamEntry, StreamGroup, PendingEntry, BitmapChunk, HllStats 数据结构
- [x] 1.2 Rust 后端：新增 commands/stream.rs，注册 stream_range / stream_rev_range / stream_add / stream_del / stream_groups / stream_pending IPC 命令
- [x] 1.3 Rust 后端：新增 commands/bitmap.rs，注册 bitmap_get_range / bitcount / bitpos / setbit IPC 命令
- [x] 1.4 Rust 后端：新增 commands/hll.rs，注册 hll_pfcount / hll_pfadd / hll_pfmerge IPC 命令
- [x] 1.5 Rust 后端：commands/pubsub.rs 扩展 pubsub_publish IPC 命令
- [x] 1.6 Rust 后端：commands/config.rs 扩展 config_rewrite / config_resetstat / config_get_notify_keyspace_events IPC 命令
- [x] 1.7 Rust 后端：lib.rs 注册所有新增 IPC 命令到 Tauri Builder；commands/mod.rs 和 services/mod.rs 导出新增模块
- [x] 1.8 前端：安装 CodeMirror 6 依赖（codemirror / @codemirror/lang-json / @codemirror/search / @codemirror/state / @codemirror/view / @codemirror/commands），配置 Vite code splitting 懒加载
- [x] 1.9 前端：新增 IPC 函数绑定 — stream_*, bitmap_*, hll_*, pubsub_publish, config_rewrite, config_resetstat, config_get_notify_keyspace_events

## 2. Stream 查看器

- [x] 2.1 前端：新增 stores/streamBrowser.ts（条目列表、分页状态、Consumer Groups、Pending 列表、排序方向）
- [x] 2.2 前端：新增 StreamViewer.vue 组件 — 条目表格（ID / 字段-值 / 时间戳）、分页控件、"倒序"切换
- [x] 2.3 前端：实现 Consumer Groups 标签页 — 表格（Group Name / Consumers / Pending / Last-delivered-ID）
- [x] 2.4 前端：实现 Pending 列表展开 — 点击 Consumer Group 行展开 Pending 表格
- [x] 2.5 前端：实现添加条目表单（ID: auto/manual 切换 + 字段-值编辑器）+ XADD 调用
- [x] 2.6 前端：实现删除条目确认弹窗 + XDEL 调用
- [x] 2.7 前端：Stream 元数据显示栏（类型: Stream / XLEN / Radix nodes / Last-ID / Max-length / Groups count）

## 3. Bitmap 查看器

- [x] 3.1 前端：新增 BitmapViewer.vue 组件 — 32×N 位网格可视化（每 bit 一个色块，1=亮/0=暗）
- [x] 3.2 前端：实现位网格虚拟化（只渲染可视区域行，大 Key > 1MB 按需加载）
- [x] 3.3 前端：实现快捷操作按钮 — BITCOUNT / BITPOS / SETBIT
- [x] 3.4 前端：实现按字节预览模式（与位网格可切换）
- [x] 3.5 前端：Bitmap 元数据显示栏（类型: Bitmap / 总 bit 数 / set bit 数 / 大小）

## 4. HyperLogLog 查看器

- [x] 4.1 前端：新增 HyperLogLogViewer.vue 组件 — 基数估算结果展示 + PFADD 输入 + PFMERGE 下拉选择器
- [x] 4.2 前端：实现 PFADD 操作 — 输入框（逗号分隔多个元素）+ 提交按钮 + 结果刷新
- [x] 4.3 前端：实现 PFMERGE 操作 — 目标 key 多选下拉 + 执行按钮 + 合并结果展示
- [x] 4.4 前端：HyperLogLog 元数据显示栏（类型: HyperLogLog / 估算基数 / 编码方式）

## 5. JSON 智能识别与编辑器

- [x] 5.1 前端：新增 JsonEditor.vue 组件 — 基于 CodeMirror 6 的 JSON 编辑器（语法高亮 + 代码折叠 + 搜索）
- [x] 5.2 前端：实现 JSON 自动检测逻辑（JSON.parse() 成功 + ≤ 1MB → 自动切换；> 1MB → 手动切换按钮）
- [x] 5.3 前端：实现美化/压缩按钮 — "美化"（格式化缩进）+ "压缩"（单行无空白）
- [x] 5.4 前端：实现 JSON 编辑保存 — ⌘+Enter 保存 + 语法校验（无效 JSON 阻止保存 + 内联错误提示）
- [x] 5.5 前端：将 JSON 检测与 JsonEditor 集成到 StringViewer / HashViewer / ListViewer

## 6. 二进制三视图

- [x] 6.1 前端：新增 BinaryViewToggle.vue 组件 — Hex / Base64 / 文本 三标签切换
- [x] 6.2 前端：实现二进制检测逻辑（> 30% 不可打印字符或含 \0 → 二进制；否则 → 文本）
- [x] 6.3 前端：实现 Hex 视图 — offset + hex bytes + ASCII 三列显示（16 bytes/行）
- [x] 6.4 前端：实现 Base64 视图 — Base64 编码字符串显示
- [x] 6.5 前端：实现文本视图 — UTF-8 文本 + 不可打印字符替换为 �
- [x] 6.6 前端：实现 Hex/Base64 模式下的编辑保存 — Hex 编辑 → bytes → key_set；Base64 编辑 → decode → key_set
- [x] 6.7 前端：将 BinaryViewToggle 集成到 StringViewer / HashViewer / ListViewer

## 7. Pub/Sub 增强

- [x] 7.1 前端：新增 PublishPanel.vue — 频道输入 + 消息体 textarea + "🚀 发布" 按钮 + 定时重复发送开关
- [x] 7.2 前端：实现定时重复发送 — 间隔输入 + "开始"/"停止" 按钮 + 倒计时显示 + 最大 10次/秒限流
- [x] 7.3 前端：实现单频道暂停/恢复 — 活跃订阅列表每项增加暂停/恢复图标 + "已暂停" badge
- [x] 7.4 前端：新增 MessageExporter.vue — 导出对话框（格式选择：JSON 数组 / NDJSON + 范围选择：全部 / 筛选结果 / 指定频道）
- [x] 7.5 前端：实现消息导出逻辑 — 生成 JSON/NDJSON 内容 + 调用 Tauri 文件保存 API
- [x] 7.6 前端：实现 Keyspace/Keyevent 通知预设按钮 — 检查 notify-keyspace-events 配置 + 自动启用 + 订阅对应 pattern
- [x] 7.7 前端：更新 PubsubWorkspace.vue — 顶部加"📤 发布"按钮 + "💾 导出"按钮 + 预设按钮 + 右侧 PublishPanel 抽屉

## 8. Server Config 增强

- [x] 8.1 前端：实现 CONFIG REWRITE 按钮 + 确认弹窗 + config_rewrite IPC 调用
- [x] 8.2 前端：实现 CONFIG RESETSTAT 按钮 + 确认弹窗 + config_resetstat IPC 调用 + 刷新 INFO 面板
- [x] 8.3 前端：新增 ConfigDiffPanel.vue — 变更参数表格（参数名 / 原值 / 新值）+ 撤销按钮 + "变更 (N)" 标签 badge
- [x] 8.4 前端：实现前端 diff 追踪 — stores/serverConfig.ts 维护 originalValues Map + 编辑时实时对比 + 提交时生成 diff
- [x] 8.5 前端：实现危险参数二次确认 — 6 个危险参数（bind/protected-mode/requirepass/masterauth/cluster-announce-ip/rename-command）红色边框弹窗 + "我了解风险" 勾选框
- [x] 8.6 前端：实现配置重新分组 — 9 个内置分类（Memory/Persistence/Replication/Security/Network/Clients/Slowlog/Advanced/Other）+ 分组映射表
- [x] 8.7 前端：更新 ServerConfigWorkspace.vue — 头部加 REWRITE/RESETSTAT 按钮 + "差异"标签页 + 重新分组展示

## 9. 类型分派与集成

- [x] 9.1 前端：更新 BrowserWorkspace.vue 类型分派表 — 新增 Stream → StreamViewer 分派；String 类型增加 Bitmap/HyperLogLog 判定逻辑
- [x] 9.2 前端：实现 Bitmap 类型识别（key 名称约定 `bitmap:*` 或手动切换按钮）→ BitmapViewer
- [x] 9.3 前端：实现 HyperLogLog 类型识别（encoding 检测 `raw` + `PFCOUNT` 可执行 或手动切换）→ HyperLogLogViewer
- [x] 9.4 前端：全局 specs 同步 — 更新 openspec/specs/ 下对应 spec.md 文件标记 Phase 3 增强内容

## 10. 验证与收尾

- [x] 10.1 编译验证：cargo build 无 error，npm run build 无 error
- [ ] 10.2 运行验证：启动应用，选择 Stream/Bitmap/HyperLogLog 类型 key 验证查看器正常渲染
- [ ] 10.3 运行验证：验证 JSON 自动识别 + CodeMirror 6 编辑器 + 美化/压缩功能
- [ ] 10.4 运行验证：验证二进制三视图切换（Hex/Base64/文本）和编辑保存
- [ ] 10.5 运行验证：验证 Pub/Sub 发布面板 + 定时重复 + 暂停/恢复 + 导出 + 预设订阅
- [ ] 10.6 运行验证：验证 Config REWRITE/RESETSTAT + 差异面板 + 危险参数确认 + 重新分组
- [x] 10.7 处理编译 warning（dead_code 等）
- [x] 10.8 性能验证：CodeMirror 6 懒加载正常；大数据集 Stream 分页/Bitmap 虚拟化性能可接受
