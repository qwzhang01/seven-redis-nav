package com.crypto.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * K线数据DTO - 交易所统一返回的K线数据结构
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class KlineDTO {

    /** 交易所 */
    private String exchange;
    /** 交易对 */
    private String symbol;
    /** 市场类型 */
    private String marketType;
    /** K线周期 */
    private String interval;
    /** 开盘时间(ms) */
    private Long openTime;
    /** 收盘时间(ms) */
    private Long closeTime;
    /** 开盘价 */
    private BigDecimal openPrice;
    /** 最高价 */
    private BigDecimal highPrice;
    /** 最低价 */
    private BigDecimal lowPrice;
    /** 收盘价 */
    private BigDecimal closePrice;
    /** 成交量 */
    private BigDecimal volume;
    /** 成交额 */
    private BigDecimal quoteVolume;
    /** 成交笔数 */
    private Integer tradesCount;
    /** 主动买入成交量 */
    private BigDecimal takerBuyVolume;
    /** 主动买入成交额 */
    private BigDecimal takerBuyQuoteVolume;
}
