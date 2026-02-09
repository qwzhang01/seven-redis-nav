
---

## 🔧 安装步骤

### 第一步：检查Python版本
```bash
python --version
```
**要求：Python 3.11 或更高版本**

如果版本不够，需要先安装Python 3.11+

---

### 第二步：进入项目目录
```bash
cd /Users/avinzhang/git/seven-quant/demo/quant_trading_system
```

---

### 第三步：安装依赖包

**方式1：使用pip安装（推荐）**
```bash
pip install -e .
```

**方式2：如果需要AI功能**
```bash
pip install -e ".[ai]"
```

**方式3：如果是开发者**
```bash
pip install -e ".[dev]"
```

---

### 第四步：验证安装
```bash
quant --help
```

如果看到命令帮助信息，说明安装成功！

---



## 运行

### 1. 配置币安key

在.env 里面配置币安的api key

### 2. 运行回测（使用模拟数据）

```bash
uv run quant backtest \
  --strategy dual_ma \
  --symbol BTCUSDT \
  --timeframe 1h \
  --start "2024-01-01" \
  --end "2024-03-31" \
  --capital 100000 \
  --mock
```

### 3. 运行回测（使用币安真实数据）

```bash
uv run quant backtest \
  --strategy dual_ma \
  --symbol BTCUSDT \
  --timeframe 1h \
  --start "2024-01-01" \
  --end "2024-03-31" \
  --capital 100000
```



