package com.crypto.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * Tick行情DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TickDTO {

    private String exchange;
    private String symbol;
    private String marketType;
    /** 最新成交价 */
    private BigDecimal lastPrice;
    /** 最优买一价 */
    private BigDecimal bestBidPrice;
    /** 最优买一量 */
    private BigDecimal bestBidQty;
    /** 最优卖一价 */
    private BigDecimal bestAskPrice;
    /** 最优卖一量 */
    private BigDecimal bestAskQty;
    /** 24h成交量 */
    private BigDecimal volume24h;
    /** 24h成交额 */
    private BigDecimal quoteVolume24h;
    /** 24h最高价 */
    private BigDecimal high24h;
    /** 24h最低价 */
    private BigDecimal low24h;
    /** 24h开盘价 */
    private BigDecimal open24h;
    /** 价格变化 */
    private BigDecimal priceChange;
    /** 价格变化百分比 */
    private BigDecimal priceChangePct;
    /** 事件时间(ms) */
    private Long eventTime;
}
