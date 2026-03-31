package com.crypto.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 订单类型
 */
@Getter
@AllArgsConstructor
public enum OrderType {

    MARKET("MARKET", "市价单"),
    LIMIT("LIMIT", "限价单"),
    STOP_MARKET("STOP_MARKET", "止损市价单"),
    TAKE_PROFIT_MARKET("TAKE_PROFIT_MARKET", "止盈市价单");

    private final String code;
    private final String name;
}
