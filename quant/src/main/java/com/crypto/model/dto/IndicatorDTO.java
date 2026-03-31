package com.crypto.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.Map;

/**
 * 技术指标计算结果DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IndicatorDTO {

    private String exchange;
    private String symbol;
    private String marketType;
    private String interval;
    private Long calcTime;

    // 移动平均线
    private BigDecimal ma5;
    private BigDecimal ma10;
    private BigDecimal ma20;
    private BigDecimal ma60;
    private BigDecimal ema12;
    private BigDecimal ema26;

    // MACD
    private BigDecimal macdLine;
    private BigDecimal macdSignal;
    private BigDecimal macdHistogram;

    // RSI
    private BigDecimal rsi6;
    private BigDecimal rsi14;
    private BigDecimal rsi24;

    // 布林带
    private BigDecimal bollUpper;
    private BigDecimal bollMiddle;
    private BigDecimal bollLower;

    // KDJ
    private BigDecimal kdjK;
    private BigDecimal kdjD;
    private BigDecimal kdjJ;

    // 成交量指标
    private BigDecimal volMa5;
    private BigDecimal volMa10;

    // ATR
    private BigDecimal atr14;

    // VWAP
    private BigDecimal vwap;

    // OBV
    private BigDecimal obv;

    // 额外指标
    private Map<String, BigDecimal> extraIndicators;
}
