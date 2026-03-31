package com.crypto.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 技术指标实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_indicator")
public class IndicatorEntity {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String exchange;
    private String symbol;
    private String marketType;

    @TableField("interval_val")
    private String intervalVal;

    private Long calcTime;

    // 移动平均
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

    /** 额外指标JSON */
    private String extraIndicators;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
