// Package indicator 指标计算服务
package indicator

import (
	"sync"

	"github.com/shopspring/decimal"
	"go.uber.org/zap"

	"github.com/quant/go-market-service/internal/kline"
	"github.com/quant/go-market-service/internal/model"
)

// IndicatorConfig 指标配置
type IndicatorConfig struct {
	// 移动平均线
	SMAPeriods []int `mapstructure:"sma_periods"` // SMA周期列表
	EMAPeriods []int `mapstructure:"ema_periods"` // EMA周期列表

	// RSI
	RSIPeriod int `mapstructure:"rsi_period"` // RSI周期

	// MACD
	MACDFast   int `mapstructure:"macd_fast"`   // MACD快线周期
	MACDSlow   int `mapstructure:"macd_slow"`   // MACD慢线周期
	MACDSignal int `mapstructure:"macd_signal"` // MACD信号线周期

	// 布林带
	BBPeriod float64 `mapstructure:"bb_period"` // 布林带周期
	BBStdDev float64 `mapstructure:"bb_stddev"` // 布林带标准差

	// ATR
	ATRPeriod int `mapstructure:"atr_period"` // ATR周期

	// ADX
	ADXPeriod int `mapstructure:"adx_period"` // ADX周期

	// KDJ
	KDJKPeriod int `mapstructure:"kdj_k_period"` // KDJ K周期
	KDJDPeriod int `mapstructure:"kdj_d_period"` // KDJ D周期
}

// DefaultConfig 默认配置
func DefaultConfig() *IndicatorConfig {
	return &IndicatorConfig{
		SMAPeriods: []int{5, 10, 20, 50, 200},
		EMAPeriods: []int{12, 26},
		RSIPeriod:  14,
		MACDFast:   12,
		MACDSlow:   26,
		MACDSignal: 9,
		BBPeriod:   20,
		BBStdDev:   2.0,
		ATRPeriod:  14,
		ADXPeriod:  14,
		KDJKPeriod: 14,
		KDJDPeriod: 3,
	}
}

// CalculatorResult 计算结果
type CalculatorResult struct {
	Exchange   model.Exchange `json:"exchange"`
	Symbol     string         `json:"symbol"`
	Timeframe  model.Timeframe `json:"timeframe"`
	Indicators map[string]decimal.Decimal `json:"indicators"`
}

// Calculator 指标计算器
type Calculator struct {
	log    *zap.Logger
	cfg    *IndicatorConfig
	buffer *kline.KlineBuffer
	mu     sync.RWMutex

	// 缓存最新指标值
	// key: exchange:symbol:timeframe
	cache map[string]*CalculatorResult
}

// NewCalculator 创建指标计算器
func NewCalculator(log *zap.Logger, cfg *IndicatorConfig, buffer *kline.KlineBuffer) *Calculator {
	if cfg == nil {
		cfg = DefaultConfig()
	}

	return &Calculator{
		log:    log.With(zap.String("component", "indicator_calculator")),
		cfg:    cfg,
		buffer: buffer,
		cache:  make(map[string]*CalculatorResult),
	}
}

// makeKey 生成缓存key
func (c *Calculator) makeKey(exchange model.Exchange, symbol string, tf model.Timeframe) string {
	return string(exchange) + ":" + symbol + ":" + string(tf)
}

// Calculate 计算所有指标
func (c *Calculator) Calculate(exchange model.Exchange, symbol string, tf model.Timeframe) *CalculatorResult {
	// 获取K线数据
	opens, highs, lows, closes, volumes := c.buffer.GetOHLCV(exchange, symbol, tf, 200)
	if len(closes) < 26 {
		return nil
	}

	indicators := make(map[string]decimal.Decimal)

	// 计算SMA
	for _, period := range c.cfg.SMAPeriods {
		if len(closes) >= period {
			sma := SMA(closes, period)
			if sma != nil && len(sma) > 0 {
				indicators["sma_"+string(rune('0'+period))] = sma[len(sma)-1]
			}
		}
	}

	// 计算EMA
	for _, period := range c.cfg.EMAPeriods {
		if len(closes) >= period {
			ema := EMA(closes, period)
			if ema != nil && len(ema) > 0 {
				indicators["ema_"+string(rune('0'+period))] = ema[len(ema)-1]
			}
		}
	}

	// 计算RSI
	if len(closes) >= c.cfg.RSIPeriod+1 {
		rsi := RSI(closes, c.cfg.RSIPeriod)
		if rsi != nil && len(rsi) > 0 {
			indicators["rsi"] = rsi[len(rsi)-1]
		}
	}

	// 计算MACD
	if len(closes) >= c.cfg.MACDSlow {
		macd := MACD(closes, c.cfg.MACDFast, c.cfg.MACDSlow, c.cfg.MACDSignal)
		if macd != nil {
			n := len(macd.MACD)
			if n > 0 {
				indicators["macd"] = macd.MACD[n-1]
				indicators["macd_signal"] = macd.Signal[n-1]
				indicators["macd_hist"] = macd.Histogram[n-1]
			}
		}
	}

	// 计算布林带
	bbPeriod := int(c.cfg.BBPeriod)
	if len(closes) >= bbPeriod {
		bb := BollingerBands(closes, bbPeriod, c.cfg.BBStdDev)
		if bb != nil {
			n := len(bb.Middle)
			if n > 0 {
				indicators["bb_upper"] = bb.Upper[n-1]
				indicators["bb_middle"] = bb.Middle[n-1]
				indicators["bb_lower"] = bb.Lower[n-1]
			}
		}
	}

	// 计算ATR
	if len(closes) >= c.cfg.ATRPeriod+1 {
		atr := ATR(highs, lows, closes, c.cfg.ATRPeriod)
		if atr != nil && len(atr) > 0 {
			indicators["atr"] = atr[len(atr)-1]
		}
	}

	// 计算ADX
	if len(closes) >= c.cfg.ADXPeriod*2 {
		adx := ADX(highs, lows, closes, c.cfg.ADXPeriod)
		if adx != nil && len(adx) > 0 {
			indicators["adx"] = adx[len(adx)-1]
		}
	}

	// 计算KDJ
	if len(closes) >= c.cfg.KDJKPeriod {
		stoch := Stochastic(highs, lows, closes, c.cfg.KDJKPeriod, c.cfg.KDJDPeriod)
		if stoch != nil {
			n := len(stoch.K)
			if n > 0 {
				indicators["kdj_k"] = stoch.K[n-1]
				indicators["kdj_d"] = stoch.D[n-1]
			}
		}
	}

	// 计算OBV
	if len(closes) >= 2 {
		obv := OBV(closes, volumes)
		if obv != nil && len(obv) > 0 {
			indicators["obv"] = obv[len(obv)-1]
		}
	}

	// 计算VWAP
	if len(closes) > 0 {
		vwap := VWAP(highs, lows, closes, volumes)
		if vwap != nil && len(vwap) > 0 {
			indicators["vwap"] = vwap[len(vwap)-1]
		}
	}

	// 计算Pivot Points (基于最近一根K线)
	if len(closes) > 0 {
		n := len(closes) - 1
		pp := PivotPoints(highs[n], lows[n], closes[n])
		if pp != nil {
			indicators["pivot"] = pp.Pivot
			indicators["pivot_r1"] = pp.R1
			indicators["pivot_r2"] = pp.R2
			indicators["pivot_s1"] = pp.S1
			indicators["pivot_s2"] = pp.S2
		}
	}

	// 添加价格相关指标
	if len(closes) > 0 {
		n := len(closes)
		indicators["close"] = closes[n-1]
		indicators["open"] = opens[n-1]
		indicators["high"] = highs[n-1]
		indicators["low"] = lows[n-1]
		indicators["volume"] = volumes[n-1]

		// 计算涨跌幅
		if n > 1 {
			change := closes[n-1].Sub(closes[n-2])
			changePct := change.Div(closes[n-2]).Mul(decimal.NewFromInt(100))
			indicators["change"] = change
			indicators["change_pct"] = changePct
		}
	}

	result := &CalculatorResult{
		Exchange:   exchange,
		Symbol:     symbol,
		Timeframe:  tf,
		Indicators: indicators,
	}

	// 更新缓存
	c.mu.Lock()
	c.cache[c.makeKey(exchange, symbol, tf)] = result
	c.mu.Unlock()

	return result
}

// GetCached 获取缓存的指标
func (c *Calculator) GetCached(exchange model.Exchange, symbol string, tf model.Timeframe) *CalculatorResult {
	c.mu.RLock()
	defer c.mu.RUnlock()

	return c.cache[c.makeKey(exchange, symbol, tf)]
}

// GetIndicator 获取单个指标值
func (c *Calculator) GetIndicator(exchange model.Exchange, symbol string, tf model.Timeframe, name string) (decimal.Decimal, bool) {
	result := c.GetCached(exchange, symbol, tf)
	if result == nil {
		result = c.Calculate(exchange, symbol, tf)
	}
	if result == nil {
		return decimal.Zero, false
	}

	val, ok := result.Indicators[name]
	return val, ok
}

// CalculateAll 计算所有交易对的指标
func (c *Calculator) CalculateAll(pairs []struct {
	Exchange  model.Exchange
	Symbol    string
	Timeframe model.Timeframe
}) map[string]*CalculatorResult {
	results := make(map[string]*CalculatorResult)

	var wg sync.WaitGroup
	var mu sync.Mutex

	for _, pair := range pairs {
		wg.Add(1)
		go func(ex model.Exchange, sym string, tf model.Timeframe) {
			defer wg.Done()
			result := c.Calculate(ex, sym, tf)
			if result != nil {
				mu.Lock()
				results[c.makeKey(ex, sym, tf)] = result
				mu.Unlock()
			}
		}(pair.Exchange, pair.Symbol, pair.Timeframe)
	}

	wg.Wait()
	return results
}
