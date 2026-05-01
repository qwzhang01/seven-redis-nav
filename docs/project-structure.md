# Seven Redis Nav - 项目目录结构

> 技术栈：Rust + Tauri v2 + Vue 3 + TypeScript + TDesign + Tailwind CSS

```
redis-nav/
├── docs/                          # 项目文档
│   ├── product-design.md          # 产品设计文档
│   └── ui-interaction-design.md   # UI 交互设计文档
│
├── src-tauri/                     # Rust 后端（Tauri Core）
│   ├── Cargo.toml                 # Rust 依赖配置
│   ├── tauri.conf.json            # Tauri 配置
│   ├── icons/                     # 应用图标
│   ├── src/
│   │   ├── main.rs                # 入口
│   │   ├── lib.rs                 # 模块注册
│   │   ├── commands/              # Tauri 命令（IPC 接口）
│   │   │   ├── mod.rs
│   │   │   ├── connection.rs      # 连接管理命令
│   │   │   ├── data.rs            # 数据操作命令
│   │   │   ├── monitor.rs         # 监控相关命令
│   │   │   ├── terminal.rs        # 终端命令
│   │   │   └── tools.rs           # 工具命令
│   │   ├── services/              # 业务逻辑层
│   │   │   ├── mod.rs
│   │   │   ├── connection.rs      # 连接池管理
│   │   │   ├── key_browser.rs     # Key 浏览服务
│   │   │   ├── data_ops.rs        # 数据 CRUD
│   │   │   ├── monitor.rs         # 监控服务
│   │   │   └── ssh_tunnel.rs      # SSH 隧道
│   │   ├── models/                # 数据模型
│   │   │   ├── mod.rs
│   │   │   ├── connection.rs      # 连接配置模型
│   │   │   ├── redis_data.rs      # Redis 数据类型模型
│   │   │   └── monitor.rs         # 监控数据模型
│   │   └── utils/                 # 工具函数
│   │       ├── mod.rs
│   │       ├── crypto.rs          # 加密工具
│   │       └── config.rs          # 配置管理
│   └── capabilities/              # Tauri 权限配置
│
├── src/                           # Vue 3 前端
│   ├── App.vue                    # 根组件
│   ├── main.ts                    # 入口
│   ├── router/                    # 路由
│   │   └── index.ts
│   ├── stores/                    # Pinia Store
│   │   ├── connection.ts          # 连接管理状态
│   │   ├── keyBrowser.ts          # Key 浏览状态
│   │   ├── dataView.ts            # 数据查看状态
│   │   ├── terminal.ts            # 终端状态
│   │   ├── monitor.ts             # 监控状态
│   │   └── settings.ts            # 设置状态
│   ├── composables/               # 组合式函数
│   │   ├── useConnection.ts       # 连接操作
│   │   ├── useRedisCommand.ts     # Redis 命令封装
│   │   ├── useKeyTree.ts          # Key 树逻辑
│   │   ├── useTerminal.ts         # 终端逻辑
│   │   └── useShortcut.ts         # 快捷键
│   ├── views/                     # 页面
│   │   ├── MainLayout.vue         # 主布局（三栏）
│   │   ├── Welcome.vue            # 欢迎页
│   │   └── Settings.vue           # 设置页
│   ├── components/                # 组件
│   │   ├── layout/                # 布局组件
│   │   │   ├── Sidebar.vue        # 侧栏
│   │   │   ├── KeyTree.vue        # Key 树浏览器
│   │   │   └── ContentArea.vue    # 内容区容器
│   │   ├── connection/            # 连接相关
│   │   │   ├── ConnectionList.vue # 连接列表
│   │   │   ├── ConnectionForm.vue # 连接表单
│   │   │   └── DbSelector.vue     # DB 选择器
│   │   ├── data-viewer/           # 数据查看器
│   │   │   ├── StringViewer.vue   # String 查看器
│   │   │   ├── HashViewer.vue     # Hash 查看器
│   │   │   ├── ListViewer.vue     # List 查看器
│   │   │   ├── SetViewer.vue      # Set 查看器
│   │   │   ├── ZSetViewer.vue     # ZSet 查看器
│   │   │   ├── StreamViewer.vue   # Stream 查看器
│   │   │   └── JsonViewer.vue     # JSON 格式化查看
│   │   ├── editor/                # 编辑器
│   │   │   ├── StringEditor.vue   # String 编辑
│   │   │   ├── HashEditor.vue     # Hash 编辑
│   │   │   ├── ListEditor.vue     # List 编辑
│   │   │   └── KeyDetailBar.vue   # Key 详情栏
│   │   ├── terminal/              # 终端
│   │   │   ├── TerminalTab.vue    # 终端标签页
│   │   │   └── CommandInput.vue   # 命令输入框
│   │   ├── monitor/               # 监控
│   │   │   ├── ServerInfo.vue     # 服务器信息
│   │   │   ├── MemoryChart.vue    # 内存图表
│   │   │   ├── CommandStats.vue   # 命令统计
│   │   │   ├── SlowLog.vue        # 慢查询
│   │   │   └── ClientList.vue     # 客户端列表
│   │   └── common/                # 通用组件
│   │       ├── StatCard.vue       # 统计卡片
│   │       ├── SearchInput.vue    # 搜索输入
│   │       ├── ConfirmDialog.vue  # 确认对话框
│   │       ├── EmptyState.vue     # 空状态
│   │       └── TypeTag.vue        # 类型标签
│   ├── styles/                    # 样式
│   │   ├── variables.css          # CSS 变量（颜色/圆角/间距）
│   │   ├── dark.css               # 深色模式
│   │   └── light.css              # 浅色模式
│   └── types/                     # TypeScript 类型
│       ├── connection.d.ts
│       ├── redis.d.ts
│       └── monitor.d.ts
│
├── public/                        # 静态资源
│   └── favicon.png
│
├── index.html                     # HTML 入口
├── vite.config.ts                 # Vite 配置
├── tsconfig.json                  # TypeScript 配置
├── tailwind.config.ts             # Tailwind 配置
├── package.json                   # 前端依赖
└── README.md                      # 项目说明
```
