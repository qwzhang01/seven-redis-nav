package com.crypto.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * 订单/风控配置属性
 */
@Data
@Component
@ConfigurationProperties(prefix = "order")
public class OrderProperties {

    /** 是否启用自动交易 */
    private boolean autoTradeEnabled = false;
    /** 单笔最大仓位百分比 */
    private double maxPositionPct = 10;
    /** 最大持仓数量 */
    private int maxPositions = 5;
    /** 默认止损百分比 */
    private double defaultStopLossPct = 3;
    /** 默认止盈百分比 */
    private double defaultTakeProfitPct = 6;
    /** 最大日亏损百分比 */
    private double maxDailyLossPct = 5;
}
