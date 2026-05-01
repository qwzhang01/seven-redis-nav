## 1. 基础设施：独立连接与 IPC 扩展

- [x] 1.1 ConnectionManager 新增 `acquire_dedicated_connection(conn_id)` 和 `release_dedicated_connection(conn_id, purpose)` 方法，支持为 Monitor/PubSub 分配独立非复用连接
- [x] 1.2 新增 Rust models：PubSubMessage、MonitorCommand、SlowlogEntry、ServerConfigItem、ServerInfo 数据结构
- [x] 1.3 前端新增 IPC 函数：pubsub_subscribe / pubsub_unsubscribe / monitor_start / monitor_stop / slowlog_get / slowlog_reset / config_get_all / config_set / server_info
- [x] 1.4 前端新增 Tauri Event 监听类型定义：pubsub:message / monitor:command
- [x] 1.5 安装前端依赖 @tanstack/vue-virtual

## 2. Pub/Sub 工作区

- [x] 2.1 Rust 后端：新增 services/pubsub.rs，实现订阅管理（独立连接 + SUBSCRIBE/PSUBSCRIBE + 消息转发为 Tauri Event）
- [x] 2.2 Rust 后端：新增 commands/pubsub.rs，注册 pubsub_subscribe / pubsub_unsubscribe IPC 命令
- [x] 2.3 前端：新增 stores/pubsub.ts（环形队列 5000 条、订阅列表、统计数据、暂停/恢复状态）
- [x] 2.4 前端：新增 PubsubWorkspace.vue 组件（订阅输入框、活跃订阅列表、消息流、统计面板、控制按钮）
- [x] 2.5 前端：实现消息过滤（关键字搜索）和清空功能
- [x] 2.6 集成测试：验证订阅/取消订阅/消息接收完整流程

## 3. Monitor 工作区

- [x] 3.1 Rust 后端：新增 services/monitor.rs，实现 MONITOR 流式读取（独立连接 + 逐行解析 + Tauri Event 推送）
- [x] 3.2 Rust 后端：新增 commands/monitor.rs，注册 monitor_start / monitor_stop IPC 命令
- [x] 3.3 前端：新增 stores/monitor.ts（环形队列 10000 条、运行状态、暂停/恢复、过滤关键字）
- [x] 3.4 前端：新增 MonitorWorkspace.vue 组件（Start/Stop 按钮、命令流列表、命令着色、过滤输入、自动滚动）
- [x] 3.5 前端：实现命令分类着色（读=绿、写=橙、管理=红）和 requestAnimationFrame 批量渲染
- [x] 3.6 前端：实现自动滚动逻辑（底部跟随 + 手动滚动暂停 + "Scroll to bottom" 按钮）

## 4. Slowlog 工作区

- [x] 4.1 Rust 后端：新增 services/slowlog.rs，封装 SLOWLOG GET / SLOWLOG RESET / SLOWLOG LEN
- [x] 4.2 Rust 后端：新增 commands/slowlog.rs，注册 slowlog_get / slowlog_reset IPC 命令
- [x] 4.3 前端：新增 stores/slowlog.ts（条目列表、排序状态、自动刷新定时器）
- [x] 4.4 前端：新增 SlowlogWorkspace.vue 组件（表格、排序列头、刷新按钮、自动刷新开关、Reset 按钮 + 确认弹窗）
- [x] 4.5 前端：实现耗时颜色编码（>100ms 红色、>10ms 橙色、<10ms 默认）

## 5. Server Config 工作区

- [x] 5.1 Rust 后端：新增 services/server_config.rs，封装 CONFIG GET * / CONFIG SET / INFO
- [x] 5.2 Rust 后端：新增 commands/config.rs，注册 config_get_all / config_set / server_info IPC 命令
- [x] 5.3 前端：新增 stores/serverConfig.ts（配置列表、分组映射、搜索状态、INFO 数据）
- [x] 5.4 前端：新增 ServerConfigWorkspace.vue 组件（INFO 概览面板 + 分组配置列表 + 搜索框 + 分组筛选）
- [x] 5.5 前端：实现行内编辑（点击编辑图标 → 输入新值 → 确认弹窗 → CONFIG SET）
- [x] 5.6 前端：实现只读参数标识（lock 图标 + 禁用编辑）和数值类型校验

## 6. 虚拟滚动集成

- [x] 6.1 前端：KeyPanel.vue 引入 @tanstack/vue-virtual，替换现有 v-for 列表为虚拟滚动列表
- [x] 6.2 前端：实现无限滚动加载（滚动到底部附近自动触发下一批 SCAN）
- [x] 6.3 前端：保持选中状态在虚拟化/反虚拟化过程中的一致性
- [x] 6.4 前端：实现 scrollToKey 方法（搜索结果定位）

## 7. App Shell 集成与清理

- [x] 7.1 MainLayout.vue：将 MonitorPlaceholder / SlowlogPlaceholder / PubsubPlaceholder / ConfigPlaceholder 替换为真实工作区组件
- [x] 7.2 删除 views/workspace/ 下的 4 个 Placeholder 组件文件
- [x] 7.3 lib.rs：注册新增的 IPC 命令到 Tauri Builder
- [x] 7.4 services/mod.rs 和 commands/mod.rs：导出新增模块

## 8. 验证与收尾

- [x] 8.1 编译验证：cargo build 无 error，npm run build 无 error
- [x] 8.2 运行验证：启动应用，逐个 Tab 切换验证基本功能可用
- [x] 8.3 处理编译 warning（dead_code 等）
