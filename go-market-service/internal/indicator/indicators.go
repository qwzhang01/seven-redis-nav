/*
Package indicator 技术指标计算库

本包提供了量化交易中常用的技术指标计算函数。
所有函数使用高精度 decimal.Decimal 类型进行计算，避免浮点精度问题。

========== 指标分类 ==========

1. 趋势指标（Moving Averages）：
   - SMA: 简单移动平均线
   - EMA: 指数移动平均线
   - WMA: 加权移动平均线
   - DEMA: 双指数移动平均线

2. 震荡指标（Oscillators）：
   - RSI: 相对强弱指标
   - Stochastic (KDJ): 随机指标
   - CCI: 商品通道指数
   - Williams %R: 威廉指标

3. 趋势强度指标：
   - ADX: 平均趋向指数
   - Aroon: 阿隆指标

4. 波动性指标：
   - ATR: 平均真实波幅
   - Bollinger Bands: 布林带
   - Keltner Channels: 肯特纳通道

5. 量价指标：
   - OBV: 能量潮指标
   - VWAP: 成交量加权平均价
   - MFI: 资金流量指标

6. 复合指标：
   - MACD: 移动平均收敛/发散指标
   - Ichimoku: 一目均衡表
   - Pivot Points: 枢轴点

========== 设计原则 ==========

1. 高精度计算：
   - 使用 shopspring/decimal 库
   - 避免浮点数精度损失

2. 数组输入输出：
   - 输入：价格序列（时间正序，旧在前）
   - 输出：指标值序列（与输入等长）
   - 前 period-1 个值为零值

3. 边界处理：
   - 数据不足返回 nil
   - 内部函数自动处理边界

========== 使用示例 ==========

	// 获取K线收盘价
	closes := buffer.GetPrices(exchange, symbol, tf, 100)

	// 计算20日SMA
	sma20 := indicator.SMA(closes, 20)

	// 计算MACD
	macd, signal, histogram := indicator.MACD(closes, 12, 26, 9)

	// 计算布林带
	upper, middle, lower := indicator.BollingerBands(closes, 20, 2.0)

	// 计算RSI
	rsi := indicator.RSI(closes, 14)
	lastRSI := rsi[len(rsi)-1]
	if lastRSI.GreaterThan(decimal.NewFromInt(70)) {
	    fmt.Println("RSI 超买信号")
	}

========== 参考资料 ==========

- Investopedia Technical Analysis: https://www.investopedia.com/technical-analysis-4689657
- TradingView Indicators: https://www.tradingview.com/wiki/Category:Technical_analysis
- TA-Lib: https://ta-lib.org/
*/
package indicator

import (
	"math"

	"github.com/shopspring/decimal"
)

/*
toFloat64 将 decimal 切片转换为 float64 切片

内部辅助函数，用于需要使用浮点运算的计算（如开方、三角函数）。

参数：
  - prices: decimal.Decimal 价格切片

返回：
  - float64 切片

注意：
  - 可能损失精度
  - 仅在必要时使用
*/
func toFloat64(prices []decimal.Decimal) []float64 {
	result := make([]float64, len(prices))
	for i, p := range prices {
		result[i], _ = p.Float64()
	}
	return result
}

/*
toDecimal 将 float64 切片转换为 decimal 切片

内部辅助函数，用于将浮点计算结果转回高精度类型。

参数：
  - values: float64 切片

返回：
  - decimal.Decimal 切片
*/
func toDecimal(values []float64) []decimal.Decimal {
	result := make([]decimal.Decimal, len(values))
	for i, v := range values {
		result[i] = decimal.NewFromFloat(v)
	}
	return result
}

// ==================== 移动平均线 ====================

/*
SMA 简单移动平均线（Simple Moving Average）

最基础的移动平均线，计算最近 N 个周期的价格算术平均值。

公式：
	SMA = (P1 + P2 + ... + Pn) / n

参数：
  - prices: 价格序列
  - period: 计算周期

返回：
  - SMA序列，前 period-1 个值为零值

特点：
  - 计算简单，对所有价格权重相等
  - 对价格变化反应较慢
  - 适合识别长期趋势

使用场景：
  - MA5、MA10 短期趋势
  - MA20、MA60 中期趋势
  - MA120、MA250 长期趋势

技术要点：
  - 价格在均线上方为上升趋势
  - 价格在均线下方为下降趋势
  - 多条均线金叉/死叉产生交易信号
*/
func SMA(prices []decimal.Decimal, period int) []decimal.Decimal {
	if len(prices) < period {
		return nil
	}

	result := make([]decimal.Decimal, len(prices))

	// 计算初始SMA：前 period 个价格的平均值
	sum := decimal.Zero
	for i := 0; i < period; i++ {
		sum = sum.Add(prices[i])
	}
	result[period-1] = sum.Div(decimal.NewFromInt(int64(period)))

	// 滑动窗口计算后续SMA
	// 优化：不重新计算所有值，而是减去最旧的，加上最新的
	for i := period; i < len(prices); i++ {
		sum = sum.Sub(prices[i-period]).Add(prices[i])
		result[i] = sum.Div(decimal.NewFromInt(int64(period)))
	}

	return result
}

/*
EMA 指数移动平均线（Exponential Moving Average）

对近期价格赋予更高权重的移动平均线，对价格变化反应更灵敏。

公式：
	EMA = Price * k + EMA(yesterday) * (1 - k)
	k = 2 / (period + 1)  -- 平滑系数

参数：
  - prices: 价格序列
  - period: 计算周期

返回：
  - EMA序列

特点：
  - 对近期价格更敏感
  - 比SMA更快反映价格变化
  - 适合短期交易决策

平滑系数 k：
  - period=12 → k≈0.154
  - period=26 → k≈0.074
  - k 越大，EMA 越接近当前价格

使用场景：
  - EMA12、EMA26 用于 MACD 计算
  - 短期交易者常用 EMA
*/
func EMA(prices []decimal.Decimal, period int) []decimal.Decimal {
	if len(prices) < period {
		return nil
	}

	result := make([]decimal.Decimal, len(prices))

	// 计算平滑系数 k = 2 / (period + 1)
	multiplier := decimal.NewFromFloat(2.0 / float64(period+1))
	oneMinusMultiplier := decimal.NewFromInt(1).Sub(multiplier)

	// 使用SMA作为初始EMA值
	sma := SMA(prices[:period], period)
	result[period-1] = sma[period-1]

	// 递推计算EMA
	// EMA[i] = Price[i] * k + EMA[i-1] * (1-k)
	for i := period; i < len(prices); i++ {
		result[i] = prices[i].Mul(multiplier).Add(result[i-1].Mul(oneMinusMultiplier))
	}

	return result
}

/*
WMA 加权移动平均线（Weighted Moving Average）

对不同时间点的价格赋予不同权重，近期价格权重更高。

公式：
	WMA = (P1*1 + P2*2 + ... + Pn*n) / (1+2+...+n)
	分母 = n*(n+1)/2

参数：
  - prices: 价格序列
  - period: 计算周期

返回：
  - WMA序列

权重分布（period=5为例）：
  - 最旧价格权重: 1
  - 第二旧权重: 2
  - ...
  - 最新价格权重: 5
  - 总权重: 1+2+3+4+5 = 15
*/
func WMA(prices []decimal.Decimal, period int) []decimal.Decimal {
	if len(prices) < period {
		return nil
	}

	result := make([]decimal.Decimal, len(prices))

	// 计算权重总和 = period * (period + 1) / 2
	weights := decimal.NewFromInt(int64(period * (period + 1) / 2))

	for i := period - 1; i < len(prices); i++ {
		sum := decimal.Zero
		for j := 0; j < period; j++ {
			// 权重从1递增到period
			weight := decimal.NewFromInt(int64(j + 1))
			sum = sum.Add(prices[i-period+1+j].Mul(weight))
		}
		result[i] = sum.Div(weights)
	}

	return result
}

/*
DEMA 双指数移动平均线（Double Exponential Moving Average）

通过双重EMA减少滞后性，对价格变化反应更快。

公式：
	DEMA = 2 * EMA(price) - EMA(EMA(price))

参数：
  - prices: 价格序列
  - period: 计算周期

返回：
  - DEMA序列

特点：
  - 比普通EMA滞后更小
  - 更紧密跟随价格
  - 适合捕捉趋势反转
*/
func DEMA(prices []decimal.Decimal, period int) []decimal.Decimal {
	// 计算第一层EMA
	ema1 := EMA(prices, period)
	if ema1 == nil {
		return nil
	}

	// 计算EMA的EMA（第二层）
	ema2 := EMA(ema1, period)
	if ema2 == nil {
		return nil
	}

	result := make([]decimal.Decimal, len(prices))
	two := decimal.NewFromInt(2)

	// DEMA = 2 * EMA - EMA(EMA)
	for i := 0; i < len(prices); i++ {
		if !ema1[i].IsZero() && !ema2[i].IsZero() {
			result[i] = ema1[i].Mul(two).Sub(ema2[i])
		}
	}

	return result
}

// ==================== 震荡指标 ====================

/*
RSI 相对强弱指标（Relative Strength Index）

衡量价格上涨和下跌力度对比的动量指标。

公式：
	RSI = 100 - 100 / (1 + RS)
	RS = 平均涨幅 / 平均跌幅

参数：
  - prices: 价格序列
  - period: 计算周期（常用14）

返回：
  - RSI序列（0-100之间）

使用方法：
  - RSI > 70: 超买区，考虑卖出
  - RSI < 30: 超卖区，考虑买入
  - RSI 从下向上突破50: 上升趋势
  - RSI 从上向下跌破50: 下降趋势

注意：
  - 强势市场中RSI可能长期处于超买区
  - 应结合其他指标使用
*/
func RSI(prices []decimal.Decimal, period int) []decimal.Decimal {
	if len(prices) < period+1 {
		return nil
	}

	result := make([]decimal.Decimal, len(prices))
	gains := make([]decimal.Decimal, len(prices))
	losses := make([]decimal.Decimal, len(prices))

	// 计算涨跌幅
	for i := 1; i < len(prices); i++ {
		change := prices[i].Sub(prices[i-1])
		if change.GreaterThan(decimal.Zero) {
			gains[i] = change
		} else {
			losses[i] = change.Abs()
		}
	}

	// 计算初始平均涨跌幅
	avgGain := decimal.Zero
	avgLoss := decimal.Zero
	for i := 1; i <= period; i++ {
		avgGain = avgGain.Add(gains[i])
		avgLoss = avgLoss.Add(losses[i])
	}
	avgGain = avgGain.Div(decimal.NewFromInt(int64(period)))
	avgLoss = avgLoss.Div(decimal.NewFromInt(int64(period)))

	// 计算RSI
	hundred := decimal.NewFromInt(100)
	periodDec := decimal.NewFromInt(int64(period))
	periodMinusOne := decimal.NewFromInt(int64(period - 1))

	if avgLoss.IsZero() {
		result[period] = hundred
	} else {
		rs := avgGain.Div(avgLoss)
		result[period] = hundred.Sub(hundred.Div(decimal.NewFromInt(1).Add(rs)))
	}

	// 平滑计算
	for i := period + 1; i < len(prices); i++ {
		avgGain = avgGain.Mul(periodMinusOne).Add(gains[i]).Div(periodDec)
		avgLoss = avgLoss.Mul(periodMinusOne).Add(losses[i]).Div(periodDec)

		if avgLoss.IsZero() {
			result[i] = hundred
		} else {
			rs := avgGain.Div(avgLoss)
			result[i] = hundred.Sub(hundred.Div(decimal.NewFromInt(1).Add(rs)))
		}
	}

	return result
}

// MACDResult MACD结果
type MACDResult struct {
	MACD      []decimal.Decimal // MACD线
	Signal    []decimal.Decimal // 信号线
	Histogram []decimal.Decimal // 柱状图
}

// MACD 指数平滑异同移动平均线
// fastPeriod: 快线周期 (默认12)
// slowPeriod: 慢线周期 (默认26)
// signalPeriod: 信号线周期 (默认9)
func MACD(prices []decimal.Decimal, fastPeriod, slowPeriod, signalPeriod int) *MACDResult {
	if len(prices) < slowPeriod {
		return nil
	}

	fastEMA := EMA(prices, fastPeriod)
	slowEMA := EMA(prices, slowPeriod)

	if fastEMA == nil || slowEMA == nil {
		return nil
	}

	// 计算MACD线
	macdLine := make([]decimal.Decimal, len(prices))
	for i := 0; i < len(prices); i++ {
		if !fastEMA[i].IsZero() && !slowEMA[i].IsZero() {
			macdLine[i] = fastEMA[i].Sub(slowEMA[i])
		}
	}

	// 计算信号线
	signalLine := EMA(macdLine[slowPeriod-1:], signalPeriod)
	
	// 补齐前面的零
	fullSignal := make([]decimal.Decimal, len(prices))
	if signalLine != nil {
		for i, v := range signalLine {
			fullSignal[slowPeriod-1+i] = v
		}
	}

	// 计算柱状图
	histogram := make([]decimal.Decimal, len(prices))
	for i := 0; i < len(prices); i++ {
		if !macdLine[i].IsZero() && !fullSignal[i].IsZero() {
			histogram[i] = macdLine[i].Sub(fullSignal[i])
		}
	}

	return &MACDResult{
		MACD:      macdLine,
		Signal:    fullSignal,
		Histogram: histogram,
	}
}

// StochResult 随机指标结果
type StochResult struct {
	K []decimal.Decimal // %K线
	D []decimal.Decimal // %D线
}

// Stochastic KDJ/随机指标
// kPeriod: K线周期 (默认14)
// dPeriod: D线周期 (默认3)
func Stochastic(highs, lows, closes []decimal.Decimal, kPeriod, dPeriod int) *StochResult {
	n := len(closes)
	if n < kPeriod {
		return nil
	}

	kValues := make([]decimal.Decimal, n)
	hundred := decimal.NewFromInt(100)

	// 计算%K
	for i := kPeriod - 1; i < n; i++ {
		highest := lows[i]
		lowest := highs[i]
		for j := i - kPeriod + 1; j <= i; j++ {
			if highs[j].GreaterThan(highest) {
				highest = highs[j]
			}
			if lows[j].LessThan(lowest) {
				lowest = lows[j]
			}
		}

		diff := highest.Sub(lowest)
		if diff.IsZero() {
			kValues[i] = decimal.NewFromInt(50)
		} else {
			kValues[i] = closes[i].Sub(lowest).Div(diff).Mul(hundred)
		}
	}

	// 计算%D (K的SMA)
	dValues := SMA(kValues[kPeriod-1:], dPeriod)
	
	// 补齐
	fullD := make([]decimal.Decimal, n)
	if dValues != nil {
		for i, v := range dValues {
			fullD[kPeriod-1+i] = v
		}
	}

	return &StochResult{
		K: kValues,
		D: fullD,
	}
}

// ========== 波动率指标 ==========

// BollingerBandsResult 布林带结果
type BollingerBandsResult struct {
	Upper  []decimal.Decimal // 上轨
	Middle []decimal.Decimal // 中轨
	Lower  []decimal.Decimal // 下轨
}

// BollingerBands 布林带
// period: 周期 (默认20)
// stdDev: 标准差倍数 (默认2)
func BollingerBands(prices []decimal.Decimal, period int, stdDev float64) *BollingerBandsResult {
	if len(prices) < period {
		return nil
	}

	n := len(prices)
	middle := SMA(prices, period)
	upper := make([]decimal.Decimal, n)
	lower := make([]decimal.Decimal, n)

	floatPrices := toFloat64(prices)
	stdDevDec := decimal.NewFromFloat(stdDev)

	for i := period - 1; i < n; i++ {
		// 计算标准差
		var sum float64
		mean, _ := middle[i].Float64()
		for j := i - period + 1; j <= i; j++ {
			diff := floatPrices[j] - mean
			sum += diff * diff
		}
		std := math.Sqrt(sum / float64(period))
		stdDecimal := decimal.NewFromFloat(std)

		upper[i] = middle[i].Add(stdDecimal.Mul(stdDevDec))
		lower[i] = middle[i].Sub(stdDecimal.Mul(stdDevDec))
	}

	return &BollingerBandsResult{
		Upper:  upper,
		Middle: middle,
		Lower:  lower,
	}
}

// ATR 真实波动幅度均值
// period: 周期 (默认14)
func ATR(highs, lows, closes []decimal.Decimal, period int) []decimal.Decimal {
	n := len(closes)
	if n < period+1 {
		return nil
	}

	tr := make([]decimal.Decimal, n)
	result := make([]decimal.Decimal, n)

	// 计算True Range
	for i := 1; i < n; i++ {
		hl := highs[i].Sub(lows[i])
		hc := highs[i].Sub(closes[i-1]).Abs()
		lc := lows[i].Sub(closes[i-1]).Abs()

		tr[i] = hl
		if hc.GreaterThan(tr[i]) {
			tr[i] = hc
		}
		if lc.GreaterThan(tr[i]) {
			tr[i] = lc
		}
	}

	// 计算初始ATR
	sum := decimal.Zero
	for i := 1; i <= period; i++ {
		sum = sum.Add(tr[i])
	}
	result[period] = sum.Div(decimal.NewFromInt(int64(period)))

	// 平滑计算
	periodDec := decimal.NewFromInt(int64(period))
	periodMinusOne := decimal.NewFromInt(int64(period - 1))
	for i := period + 1; i < n; i++ {
		result[i] = result[i-1].Mul(periodMinusOne).Add(tr[i]).Div(periodDec)
	}

	return result
}

// ========== 成交量指标 ==========

// OBV 能量潮指标
func OBV(closes, volumes []decimal.Decimal) []decimal.Decimal {
	n := len(closes)
	if n < 2 || len(volumes) != n {
		return nil
	}

	result := make([]decimal.Decimal, n)
	result[0] = volumes[0]

	for i := 1; i < n; i++ {
		if closes[i].GreaterThan(closes[i-1]) {
			result[i] = result[i-1].Add(volumes[i])
		} else if closes[i].LessThan(closes[i-1]) {
			result[i] = result[i-1].Sub(volumes[i])
		} else {
			result[i] = result[i-1]
		}
	}

	return result
}

// VWAP 成交量加权平均价
func VWAP(highs, lows, closes, volumes []decimal.Decimal) []decimal.Decimal {
	n := len(closes)
	if n == 0 {
		return nil
	}

	result := make([]decimal.Decimal, n)
	cumVolume := decimal.Zero
	cumVolumePrice := decimal.Zero
	three := decimal.NewFromInt(3)

	for i := 0; i < n; i++ {
		typicalPrice := highs[i].Add(lows[i]).Add(closes[i]).Div(three)
		cumVolume = cumVolume.Add(volumes[i])
		cumVolumePrice = cumVolumePrice.Add(typicalPrice.Mul(volumes[i]))

		if cumVolume.IsZero() {
			result[i] = typicalPrice
		} else {
			result[i] = cumVolumePrice.Div(cumVolume)
		}
	}

	return result
}

// ========== 趋势指标 ==========

// ADX 平均趋向指标
// period: 周期 (默认14)
func ADX(highs, lows, closes []decimal.Decimal, period int) []decimal.Decimal {
	n := len(closes)
	if n < period*2 {
		return nil
	}

	plusDM := make([]decimal.Decimal, n)
	minusDM := make([]decimal.Decimal, n)
	tr := make([]decimal.Decimal, n)

	// 计算DM和TR
	for i := 1; i < n; i++ {
		upMove := highs[i].Sub(highs[i-1])
		downMove := lows[i-1].Sub(lows[i])

		if upMove.GreaterThan(downMove) && upMove.GreaterThan(decimal.Zero) {
			plusDM[i] = upMove
		}
		if downMove.GreaterThan(upMove) && downMove.GreaterThan(decimal.Zero) {
			minusDM[i] = downMove
		}

		hl := highs[i].Sub(lows[i])
		hc := highs[i].Sub(closes[i-1]).Abs()
		lc := lows[i].Sub(closes[i-1]).Abs()

		tr[i] = hl
		if hc.GreaterThan(tr[i]) {
			tr[i] = hc
		}
		if lc.GreaterThan(tr[i]) {
			tr[i] = lc
		}
	}

	// 计算平滑DI
	smoothPlusDM := smoothAverage(plusDM, period)
	smoothMinusDM := smoothAverage(minusDM, period)
	smoothTR := smoothAverage(tr, period)

	// 计算DI
	plusDI := make([]decimal.Decimal, n)
	minusDI := make([]decimal.Decimal, n)
	dx := make([]decimal.Decimal, n)
	hundred := decimal.NewFromInt(100)

	for i := period; i < n; i++ {
		if !smoothTR[i].IsZero() {
			plusDI[i] = smoothPlusDM[i].Div(smoothTR[i]).Mul(hundred)
			minusDI[i] = smoothMinusDM[i].Div(smoothTR[i]).Mul(hundred)
		}

		diSum := plusDI[i].Add(minusDI[i])
		if !diSum.IsZero() {
			dx[i] = plusDI[i].Sub(minusDI[i]).Abs().Div(diSum).Mul(hundred)
		}
	}

	// 计算ADX
	result := smoothAverage(dx[period:], period)
	
	// 补齐前面
	fullResult := make([]decimal.Decimal, n)
	for i, v := range result {
		fullResult[period+i] = v
	}

	return fullResult
}

// smoothAverage 平滑平均
func smoothAverage(data []decimal.Decimal, period int) []decimal.Decimal {
	n := len(data)
	if n < period {
		return nil
	}

	result := make([]decimal.Decimal, n)
	periodDec := decimal.NewFromInt(int64(period))

	// 初始平均
	sum := decimal.Zero
	for i := 0; i < period; i++ {
		sum = sum.Add(data[i])
	}
	result[period-1] = sum.Div(periodDec)

	// 平滑
	for i := period; i < n; i++ {
		result[i] = result[i-1].Sub(result[i-1].Div(periodDec)).Add(data[i])
	}

	return result
}

// Ichimoku 一目均衡表
type IchimokuResult struct {
	TenkanSen   []decimal.Decimal // 转换线
	KijunSen    []decimal.Decimal // 基准线
	SenkouSpanA []decimal.Decimal // 先行带A
	SenkouSpanB []decimal.Decimal // 先行带B
	ChikouSpan  []decimal.Decimal // 迟行带
}

// Ichimoku 计算一目均衡表
func Ichimoku(highs, lows, closes []decimal.Decimal, tenkanPeriod, kijunPeriod, senkouBPeriod, displacement int) *IchimokuResult {
	n := len(closes)
	if n < senkouBPeriod+displacement {
		return nil
	}

	// 计算高低价中点
	midPrice := func(h, l []decimal.Decimal, period, idx int) decimal.Decimal {
		highest := h[idx]
		lowest := l[idx]
		for i := idx - period + 1; i <= idx; i++ {
			if h[i].GreaterThan(highest) {
				highest = h[i]
			}
			if l[i].LessThan(lowest) {
				lowest = l[i]
			}
		}
		return highest.Add(lowest).Div(decimal.NewFromInt(2))
	}

	tenkan := make([]decimal.Decimal, n)
	kijun := make([]decimal.Decimal, n)
	spanA := make([]decimal.Decimal, n+displacement)
	spanB := make([]decimal.Decimal, n+displacement)
	chikou := make([]decimal.Decimal, n)

	// 计算转换线
	for i := tenkanPeriod - 1; i < n; i++ {
		tenkan[i] = midPrice(highs, lows, tenkanPeriod, i)
	}

	// 计算基准线
	for i := kijunPeriod - 1; i < n; i++ {
		kijun[i] = midPrice(highs, lows, kijunPeriod, i)
	}

	// 计算先行带A
	for i := kijunPeriod - 1; i < n; i++ {
		if !tenkan[i].IsZero() && !kijun[i].IsZero() {
			spanA[i+displacement] = tenkan[i].Add(kijun[i]).Div(decimal.NewFromInt(2))
		}
	}

	// 计算先行带B
	for i := senkouBPeriod - 1; i < n; i++ {
		spanB[i+displacement] = midPrice(highs, lows, senkouBPeriod, i)
	}

	// 计算迟行带
	for i := displacement; i < n; i++ {
		chikou[i-displacement] = closes[i]
	}

	return &IchimokuResult{
		TenkanSen:   tenkan,
		KijunSen:    kijun,
		SenkouSpanA: spanA[:n],
		SenkouSpanB: spanB[:n],
		ChikouSpan:  chikou,
	}
}

// ========== 支撑阻力 ==========

// PivotPoints 轴心点
type PivotPointsResult struct {
	Pivot decimal.Decimal // 轴心点
	R1    decimal.Decimal // 阻力位1
	R2    decimal.Decimal // 阻力位2
	R3    decimal.Decimal // 阻力位3
	S1    decimal.Decimal // 支撑位1
	S2    decimal.Decimal // 支撑位2
	S3    decimal.Decimal // 支撑位3
}

// PivotPoints 计算轴心点
func PivotPoints(high, low, close decimal.Decimal) *PivotPointsResult {
	three := decimal.NewFromInt(3)
	two := decimal.NewFromInt(2)
	
	pivot := high.Add(low).Add(close).Div(three)
	
	return &PivotPointsResult{
		Pivot: pivot,
		R1:    pivot.Mul(two).Sub(low),
		R2:    pivot.Add(high.Sub(low)),
		R3:    high.Add(pivot.Sub(low).Mul(two)),
		S1:    pivot.Mul(two).Sub(high),
		S2:    pivot.Sub(high.Sub(low)),
		S3:    low.Sub(high.Sub(pivot).Mul(two)),
	}
}
