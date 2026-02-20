# 信号跟单详情页面功能

## 功能概述

新增了信号跟单详情页面，用于展示用户跟单的详细信息，包括行情数据、交易点位、收益情况、持仓信息和交易记录等用户关注的核心内容。

## 功能特性

### 1. 页面头部
- **信号基本信息**：信号名称、交易所、状态标识
- **操作按钮**：调整设置、停止跟单
- **关键指标卡片**：
  - 总收益率（带颜色区分正负）
  - 跟单资金（USDT）
  - 当前净值（USDT）
  - 最大回撤
  - 跟单天数

### 2. 行情与交易点
- **当前价格信息**：
  - 当前价格
  - 24小时涨跌幅
  - 24小时成交量
- **价格走势图**：
  - 支持多时间周期切换（1H、4H、1D、1W）
  - 使用 ECharts 图表展示
  - 根据涨跌自动调整颜色
- **最近交易点位**：
  - 买入/卖出标记
  - 交易时间
  - 交易价格和数量
  - 图标化展示（绿色上箭头=买入，红色下箭头=卖出）

### 3. 收益曲线
- **收益走势图**：
  - 展示跟单期间的收益变化
  - 根据总收益正负调整颜色
- **关键指标**：
  - 累计收益
  - 今日收益
  - 胜率

### 4. 当前持仓
- **持仓列表表格**：
  - 交易对
  - 方向（做多/做空）
  - 持仓数量
  - 开仓价格
  - 当前价格
  - 盈亏金额
  - 盈亏率
- 空仓时显示提示信息

### 5. 交易记录
- **历史交易列表**：
  - 买入/卖出标识
  - 交易对
  - 交易时间
  - 交易价格和数量
  - 成交额
  - 盈亏情况（如果已平仓）

### 6. 侧边栏信息

#### 跟单配置
- 跟单资金
- 跟单比例
- 止损设置
- 开始时间

#### 风险提示
- 当前回撤
- 距离止损距离
- 持仓风险度
- 警告提示（使用琥珀色高亮）

#### 绩效统计
- 总交易次数
- 盈利次数
- 亏损次数
- 胜率
- 平均盈利
- 平均亏损
- 盈亏比

## 访问路径

1. **从用户中心进入**：
   - 我的账户 → 信号跟单 → 点击任意跟单记录
   - URL: `/system/user/signal-follow/:id`

2. **直接访问**：
   - `/system/user/signal-follow/1`（需要登录）

## 文件结构

```
src/
├── views/
│   └── user/
│       ├── UserCenter.vue              # 用户中心（已更新，添加跳转）
│       └── SignalFollowDetail.vue      # 信号跟单详情页面（新增）
├── router/
│   └── index.ts                        # 路由配置（已更新）
└── components/
    ├── common/
    │   └── StatusDot.vue              # 状态点组件（复用）
    └── charts/
        └── ReturnCurveChart.vue       # 收益曲线图表（复用）
```

## 数据结构

### FollowDetail
```typescript
interface FollowDetail {
  id: string
  signalName: string
  exchange: string
  status: 'following' | 'stopped'
  totalReturn: number
  followAmount: number
  currentValue: number
  maxDrawdown: number
  followDays: number
  currentPrice: number
  priceChange24h: number
  volume24h: string
  todayReturn: number
  winRate: number
  followRatio: number
  stopLoss: number
  startTime: string
  currentDrawdown: number
  riskLevel: string
  totalTrades: number
  winTrades: number
  lossTrades: number
  avgWin: number
  avgLoss: number
  profitFactor: number
  priceHistory: number[]
  priceHistoryLabels: string[]
  returnCurve: number[]
  returnCurveLabels: string[]
  tradingPoints: TradingPoint[]
  positions: Position[]
  tradeHistory: Trade[]
}

interface TradingPoint {
  id: string
  type: 'buy' | 'sell'
  symbol: string
  price: number
  amount: number
  time: string
}

interface Position {
  id: string
  symbol: string
  side: 'long' | 'short'
  amount: number
  entryPrice: number
  currentPrice: number
  pnl: number
  pnlPercent: number
}

interface Trade {
  id: string
  side: 'buy' | 'sell'
  symbol: string
  price: number
  amount: number
  total: number
  pnl?: number
  time: string
}
```

## UI/UX 设计特点

### 1. 视觉层次
- **三栏布局**：主内容区（2/3宽度）+ 侧边栏（1/3宽度）
- **卡片式设计**：使用 glass-card 样式
- **深色主题**：与整体系统保持一致

### 2. 颜色语义
- **绿色（emerald）**：盈利、买入、正向指标
- **红色（red）**：亏损、卖出、负向指标
- **琥珀色（amber）**：警告、风险提示
- **蓝色（blue）**：信息、中性状态
- **紫色（purple）**：特殊标识

### 3. 交互设计
- **响应式布局**：支持桌面和移动端
- **悬停效果**：表格行、卡片悬停高亮
- **时间周期切换**：价格图表支持多周期切换
- **面包屑导航**：方便返回上级页面

### 4. 数据可视化
- **ECharts 图表**：价格走势、收益曲线
- **图标化展示**：买卖方向、交易类型
- **状态标签**：颜色区分不同状态
- **进度指标**：风险度、距离止损

## 核心功能实现

### 1. 价格走势图
```vue
<ReturnCurveChart
  v-if="followDetail.priceHistory?.length"
  :data="followDetail.priceHistory"
  :labels="followDetail.priceHistoryLabels"
  :height="280"
  :color="followDetail.priceChange24h >= 0 ? '#10b981' : '#ef4444'"
/>
```

### 2. 交易点位标记
- 使用 `ArrowUpCircle` 和 `ArrowDownCircle` 图标
- 绿色背景表示买入，红色背景表示卖出
- 显示交易时间、价格、数量

### 3. 持仓表格
- 实时显示当前持仓
- 计算盈亏金额和盈亏率
- 颜色区分盈利和亏损

### 4. 风险监控
- 实时显示当前回撤
- 计算距离止损的距离
- 风险等级评估

## 后续集成步骤

### 1. 后端 API 对接
```typescript
// 获取跟单详情
GET /api/user/signal-follows/:id

// 更新跟单配置
PUT /api/user/signal-follows/:id/config

// 停止跟单
POST /api/user/signal-follows/:id/stop
```

### 2. WebSocket 实时更新
- 价格实时更新
- 持仓盈亏实时计算
- 新交易推送通知

### 3. 增强功能
- 导出交易记录
- 分享跟单绩效
- 设置价格提醒
- 自定义图表指标
- 交易分析报告

## 使用示例

### 从用户中心跳转
```vue
<div
  @click="$router.push(`/system/user/signal-follow/${item.id}`)"
  class="glass-card-hover p-6 cursor-pointer"
>
  <!-- 跟单信息 -->
</div>
```

### 路由配置
```typescript
{
  path: 'user/signal-follow/:id',
  name: 'SignalFollowDetail',
  component: () => import('@/views/user/SignalFollowDetail.vue'),
  meta: { title: '跟单详情', requiresAuth: true },
}
```

## 权限要求

- 需要登录（requiresAuth: true）
- 只能查看自己的跟单记录

## 响应式设计

- **桌面端（lg+）**：三栏布局，主内容 2/3，侧边栏 1/3
- **平板端（md）**：两栏布局，部分卡片堆叠
- **移动端（sm）**：单栏布局，所有内容垂直堆叠

## 性能优化

1. **懒加载**：图表组件按需加载
2. **数据缓存**：历史数据本地缓存
3. **虚拟滚动**：交易记录列表支持虚拟滚动（大量数据时）
4. **防抖节流**：实时数据更新使用节流

## 相关文档

- [USER_MANAGEMENT_FEATURE.md](USER_MANAGEMENT_FEATURE.md) - 用户管理功能
- [API_INTEGRATION.md](API_INTEGRATION.md) - API 集成文档
