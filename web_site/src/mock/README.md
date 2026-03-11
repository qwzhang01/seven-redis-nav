# 图表组件Mock数据测试指南

## 概述

本目录包含用于测试深度图和成交量图表的mock数据结构和API接口规范。这些文件为后端开发提供了参考格式，并支持前端在无后端服务的情况下进行组件测试。

## 文件说明

### marketApiMock.ts
- **功能**: 市场API的mock数据结构和模拟服务
- **包含**:
  - 深度数据mock (DepthData)
  - 成交量数据mock (VolumeData)
  - K线数据mock (KlineData)
  - Mock API服务类
  - WebSocket模拟服务
  - API接口规范文档

## 测试方法

### 1. 使用Mock数据测试图表组件

在TradingPage.vue中，mock数据已经自动初始化：

```javascript
// 在onMounted中自动初始化mock数据
onMounted(async () => {
  // ... 其他数据加载
  
  // 初始化mock数据用于测试
  depthData.value = generateMockDepthData()
  volumeData.value = generateMockVolumeData()
  
  // ...
})
```

### 2. 手动触发mock数据更新

可以在浏览器控制台中手动更新mock数据：

```javascript
// 更新深度数据
const newDepthData = {
  bids: Array.from({ length: 20 }, (_, i) => ({
    price: 91476 * (1 - (i + 1) * 0.001),
    amount: Math.random() * 100 + 50
  })).sort((a, b) => b.price - a.price),
  asks: Array.from({ length: 20 }, (_, i) => ({
    price: 91476 * (1 + (i + 1) * 0.001),
    amount: Math.random() * 100 + 50
  })).sort((a, b) => a.price - b.price)
}

// 更新成交量数据
const newVolumeData = Array.from({ length: 60 }, (_, i) => ({
  time: Math.floor(Date.now() / 1000) - (60 - i) * 60,
  value: Math.random() * 1000 + 500
}))
```

## API接口规范

### 深度数据接口

**请求**:
```
GET /api/v1/market/depth?symbol=BTC/USDT&limit=20
```

**响应**:
```json
{
  "bids": [
    {"price": 91400.00, "amount": 2.5},
    {"price": 91350.00, "amount": 1.8}
  ],
  "asks": [
    {"price": 91500.00, "amount": 1.8},
    {"price": 91550.00, "amount": 2.4}
  ],
  "timestamp": 1672531200000
}
```

### 成交量数据接口

**请求**:
```
GET /api/v1/market/volume?symbol=BTC/USDT&interval=1m&limit=60
```

**响应**:
```json
[
  {"time": 1672531200, "value": 1250},
  {"time": 1672531260, "value": 980}
]
```

### WebSocket实时数据

**订阅深度数据**:
```javascript
// 订阅消息
{
  "action": "subscribe",
  "channel": "depth",
  "symbol": "BTC/USDT"
}

// 接收消息
{
  "channel": "depth",
  "symbol": "BTC/USDT",
  "data": {
    "bids": [...],
    "asks": [...],
    "timestamp": 1672531200000
  }
}
```

**订阅成交量数据**:
```javascript
// 订阅消息
{
  "action": "subscribe",
  "channel": "volume",
  "symbol": "BTC/USDT",
  "interval": "1m"
}

// 接收消息
{
  "channel": "volume",
  "symbol": "BTC/USDT",
  "data": {
    "time": 1672531200,
    "value": 1250
  }
}
```

## 数据结构说明

### 深度图数据结构

深度图需要展示买卖双方的挂单情况：

- **bids**: 买单深度，按价格降序排列
- **asks**: 卖单深度，按价格升序排列
- **price**: 价格（精确到小数点后2位）
- **amount**: 数量（精确到小数点后4位）

### 成交量数据结构

成交量图表展示时间序列的成交量数据：

- **time**: Unix时间戳（秒）
- **value**: 成交量数值

## 常见问题排查

### 深度图显示异常
1. 检查数据格式是否正确
2. 确认bids按价格降序排列，asks按价格升序排列
3. 验证价格和数量字段类型为number

### 成交量图无数据显示
1. 检查volumeData数组是否为空
2. 确认时间戳格式为Unix时间戳（秒）
3. 验证value字段为有效数值

### 图表交互问题
1. 检查十字线事件处理函数是否正确绑定
2. 确认组件高度设置合理
3. 验证数据更新机制正常工作

## 性能优化建议

1. **数据量控制**: 深度数据建议不超过50档，成交量数据不超过1000个点
2. **更新频率**: 实时数据更新建议1-5秒间隔
3. **内存管理**: 及时清理不再使用的图表实例

## 后端开发参考

后端API应遵循以下规范：

1. **响应格式**: 使用JSON格式，包含必要的状态码和错误信息
2. **数据精度**: 价格保留2位小数，数量保留4位小数
3. **时间戳**: 使用Unix时间戳（毫秒或秒，需统一）
4. **错误处理**: 提供清晰的错误码和错误信息

## 下一步工作

1. 集成真实后端API
2. 实现WebSocket实时数据推送
3. 添加数据缓存和本地存储
4. 优化图表性能和用户体验