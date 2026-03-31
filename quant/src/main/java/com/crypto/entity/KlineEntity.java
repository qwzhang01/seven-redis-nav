package com.crypto.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * K线数据实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_kline")
public class KlineEntity {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String exchange;
    private String symbol;
    private String marketType;

    @TableField("interval_val")
    private String intervalVal;

    private Long openTime;
    private Long closeTime;
    private BigDecimal openPrice;
    private BigDecimal highPrice;
    private BigDecimal lowPrice;
    private BigDecimal closePrice;
    private BigDecimal volume;
    private BigDecimal quoteVolume;
    private Integer tradesCount;
    private BigDecimal takerBuyVol;
    private BigDecimal takerBuyQuote;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
