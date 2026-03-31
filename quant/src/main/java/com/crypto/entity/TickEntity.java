package com.crypto.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Tick行情实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_tick")
public class TickEntity {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String exchange;
    private String symbol;
    private String marketType;
    private BigDecimal lastPrice;
    private BigDecimal bestBidPrice;
    private BigDecimal bestBidQty;
    private BigDecimal bestAskPrice;
    private BigDecimal bestAskQty;
    private BigDecimal volume24h;
    private BigDecimal quoteVol24h;
    private BigDecimal high24h;
    private BigDecimal low24h;
    private BigDecimal open24h;
    private BigDecimal priceChange;
    private BigDecimal priceChangePct;
    private Long eventTime;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
