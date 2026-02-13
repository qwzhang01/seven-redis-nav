# PyCharm调试指南

## 概述

本文档详细说明如何在PyCharm中运行和调试量化交易系统的CLI命令。

## 方法一：使用调试脚本（推荐）

### 1. 使用debug_cli.py脚本

我们创建了一个专门的调试脚本 `debug_cli.py`，包含所有主要功能的调试方法：

```python
# 直接运行整个调试脚本
python debug_cli.py
```

**调试脚本功能：**
- 回测功能调试
- 实时数据采集调试
- 数据库查询调试
- API服务器调试
- 策略列表查看
- 指标列表查看
- 配置检查

### 2. 在PyCharm中设置断点

1. **打开debug_cli.py文件**
2. **在感兴趣的函数中设置断点**：
   - 在函数开始处点击左侧边栏
   - 或按Ctrl+F8设置断点

3. **调试运行**：
   - 右键点击文件 → "Debug 'debug_cli.py'"
   - 或点击右上角的调试按钮（虫子图标）

## 方法二：直接调试CLI命令

### 1. 创建运行配置

1. **打开运行配置**：Run → Edit Configurations
2. **添加Python配置**：点击+号 → Python
3. **配置参数**：
   - Script path: `src/quant_trading_system/cli.py`
   - Parameters: 输入CLI命令参数

### 2. 常用CLI命令示例

**回测命令配置：**
```
Script path: src/quant_trading_system/cli.py
Parameters: backtest --strategy moving_average --symbol BTCUSDT --timeframe 1m --start "2024-01-01" --end "2024-01-31" --capital 100000 --mock
```

**API服务器配置：**
```
Script path: src/quant_trading_system/cli.py
Parameters: serve --host 127.0.0.1 --port 8000 --reload
```

**查看策略列表：**
```
Script path: src/quant_trading_system/cli.py
Parameters: list_strategies
```

### 3. 设置断点调试

1. **在CLI文件中设置断点**：
   - 打开 `src/quant_trading_system/cli.py`
   - 在目标函数中设置断点（如`backtest`函数）

2. **调试运行**：
   - 选择配置 → 点击调试按钮
   - 程序会在断点处暂停

## 方法三：使用Python模块运行

### 1. 在PyCharm终端中运行

```bash
# 回测命令
python -m src.quant_trading_system.cli backtest --strategy moving_average --symbol BTCUSDT --timeframe 1m --start "2024-01-01" --end "2024-01-31" --mock

# API服务器
python -m src.quant_trading_system.cli serve --host 127.0.0.1 --port 8000 --reload

# 查看策略
python -m src.quant_trading_system.cli list_strategies
```

### 2. 调试模式运行

```bash
# 使用pdb调试
python -m pdb -m src.quant_trading_system.cli backtest --strategy moving_average --symbol BTCUSDT --timeframe 1m --start "2024-01-01" --end "2024-01-31" --mock
```

## 调试技巧

### 1. 条件断点

在复杂逻辑中设置条件断点：
- 右键断点 → 设置条件
- 例如：`symbol == "BTCUSDT"`

### 2. 观察变量

在调试过程中：
- 使用Variables窗口查看变量值
- 在Watches窗口添加要监控的变量

### 3. 步进调试

- **Step Over (F8)**: 执行当前行，不进入函数
- **Step Into (F7)**: 进入函数内部
- **Step Out (Shift+F8)**: 跳出当前函数
- **Run to Cursor (Alt+F9)**: 运行到光标处

### 4. 异常断点

设置异常断点捕获所有异常：
- Run → View Breakpoints → Python Exception Breakpoints
- 勾选"Python Exceptions"

## 常见调试场景

### 场景1：调试回测逻辑

1. **设置断点位置**：
   - `backtest`函数开始处
   - 策略执行的关键逻辑处
   - 数据获取和处理处

2. **调试步骤**：
   - 运行回测命令
   - 观察数据加载过程
   - 检查策略计算逻辑
   - 查看回测结果

### 场景2：调试实时数据采集

1. **设置断点位置**：
   - `real_time_collector.py`中的数据处理函数
   - 数据库存储函数

2. **调试步骤**：
   - 运行实时采集脚本
   - 观察WebSocket连接和数据接收
   - 检查数据格式转换
   - 验证数据库存储

### 场景3：调试数据库操作

1. **设置断点位置**：
   - `data_query.py`中的查询函数
   - `data_store.py`中的存储函数

2. **调试步骤**：
   - 运行数据库查询命令
   - 检查SQL查询语句
   - 验证数据返回格式
   - 测试批量存储性能

## 环境配置

### 1. Python解释器
确保PyCharm使用正确的Python解释器：
- File → Settings → Project → Python Interpreter
- 选择项目使用的Python环境

### 2. 依赖包
确保所有依赖包已安装：
```bash
pip install -r requirements.txt
```

### 3. 环境变量
设置必要的环境变量：
- DATABASE_URL: TimescaleDB连接字符串
- EXCHANGE_API_KEY: 交易所API密钥
- EXCHANGE_API_SECRET: 交易所API密钥

## 故障排除

### 1. 模块导入错误
如果出现模块导入错误：
- 检查Python路径设置
- 确保项目根目录在PYTHONPATH中
- 在PyCharm中标记src目录为Sources Root

### 2. 断点不生效
如果断点不生效：
- 检查Python解释器配置
- 确保代码已重新加载
- 检查断点是否在可执行代码行

### 3. 调试器卡住
如果调试器卡住：
- 检查是否有无限循环
- 使用暂停按钮中断执行
- 检查网络请求是否超时

## 最佳实践

1. **使用调试脚本**：优先使用`debug_cli.py`进行调试
2. **设置合理的断点**：避免设置过多断点影响性能
3. **使用条件断点**：在复杂逻辑中使用条件断点
4. **记录调试过程**：使用控制台输出辅助调试
5. **版本控制**：调试前确保代码已提交

## 总结

通过以上方法，您可以在PyCharm中高效地调试量化交易系统的各个功能模块。推荐使用调试脚本方法，因为它提供了更友好的交互界面和完整的调试功能。
