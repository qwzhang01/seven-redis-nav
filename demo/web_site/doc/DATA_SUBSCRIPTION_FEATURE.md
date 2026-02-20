# 实时数据订阅管理功能

## 功能概述

在后台管理系统中新增了实时数据订阅管理功能，用于管理各交易所的实时数据订阅状态，支持启动、暂停、恢复、新增订阅以及手动同步指定区间的历史数据。

## 功能特性

### 1. 订阅管理
- **新增订阅**：创建新的数据订阅，支持配置交易所、数据类型、交易对等参数
- **启动订阅**：启动已停止或暂停的订阅
- **暂停订阅**：暂时停止数据接收，保留订阅配置
- **停止订阅**：完全停止订阅
- **编辑订阅**：修改订阅配置
- **删除订阅**：删除不需要的订阅

### 2. 数据类型支持
- K线数据（支持多种时间周期：1m, 5m, 15m, 1h, 4h, 1d）
- Ticker数据
- 深度数据
- 成交数据
- 订单簿数据

### 3. 交易所支持
- Binance
- OKX
- Bybit
- Bitget

### 4. 手动同步功能
- 支持指定时间范围手动同步历史数据
- 实时显示同步进度
- 支持多个同步任务并行执行
- 显示同步任务状态（等待中、同步中、已完成、失败）

### 5. 监控与统计
- 实时显示运行中、已暂停、已停止的订阅数量
- 显示总记录数统计
- 显示每个订阅的错误计数
- 显示最后同步时间

### 6. 筛选与搜索
- 按订阅名称搜索
- 按状态筛选
- 按交易所筛选
- 按数据类型筛选

## 访问路径

管理后台 → 实时数据订阅
URL: `/admin/data-subscription`

## 文件结构

```
src/
├── views/
│   └── admin/
│       └── AdminDataSubscription.vue  # 实时数据订阅管理页面
├── types/
│   └── index.ts                       # 新增类型定义
├── router/
│   └── index.ts                       # 路由配置
└── views/
    └── layout/
        └── AdminLayout.vue            # 管理后台布局（新增菜单项）
```

## 类型定义

### DataSubscription
```typescript
interface DataSubscription {
  id: string
  name: string
  exchange: string
  dataType: 'kline' | 'ticker' | 'depth' | 'trade' | 'orderbook'
  symbols: string[]
  interval?: string
  status: 'running' | 'paused' | 'stopped'
  createdAt: string
  updatedAt: string
  lastSyncTime?: string
  totalRecords: number
  errorCount: number
  config: {
    autoRestart: boolean
    maxRetries: number
    batchSize: number
    syncInterval: number
  }
}
```

### SyncTask
```typescript
interface SyncTask {
  id: string
  subscriptionId: string
  subscriptionName: string
  exchange: string
  symbols: string[]
  dataType: string
  startTime: string
  endTime: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  totalRecords: number
  syncedRecords: number
  errorMessage?: string
  createdAt: string
  completedAt?: string
}
```

## 使用说明

### 新增订阅
1. 点击右上角"新增订阅"按钮
2. 填写订阅名称、选择交易所和数据类型
3. 输入交易对（多个用逗号分隔，如：BTC/USDT,ETH/USDT）
4. 如果是K线数据，选择时间周期
5. 选择是否自动重启
6. 点击"保存"创建订阅

### 控制订阅状态
- **启动**：点击播放图标启动订阅
- **暂停**：点击暂停图标暂停订阅
- **停止**：点击停止图标完全停止订阅

### 手动同步历史数据
1. 点击订阅行的刷新图标
2. 选择开始时间和结束时间
3. 点击"开始同步"创建同步任务
4. 在下方的同步任务列表中查看进度

### 编辑和删除
- 点击铅笔图标编辑订阅配置
- 点击垃圾桶图标删除订阅

## 后续开发建议

1. **后端API集成**：当前使用模拟数据，需要对接实际的后端API
2. **WebSocket实时更新**：使用WebSocket实时更新订阅状态和同步进度
3. **错误日志详情**：点击错误计数可查看详细的错误日志
4. **批量操作**：支持批量启动、暂停、停止订阅
5. **导出功能**：支持导出订阅配置和同步记录
6. **告警通知**：订阅出现错误时发送告警通知
7. **性能监控**：添加数据接收速率、延迟等性能指标
8. **数据质量检查**：检查接收数据的完整性和准确性

## 技术栈

- Vue 3 + TypeScript
- TDesign Vue Next（UI组件库）
- Vue Router（路由管理）
- Lucide Vue Next（图标库）
- Tailwind CSS（样式）

## 注意事项

1. 当前为前端实现，使用模拟数据
2. 需要管理员权限才能访问此功能
3. 实际使用时需要对接后端API
4. 建议添加权限控制，限制敏感操作
