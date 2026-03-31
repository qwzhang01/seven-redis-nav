package com.crypto.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 交易方向
 */
@Getter
@AllArgsConstructor
public enum OrderSide {

    BUY("BUY", "买入"),
    SELL("SELL", "卖出");

    private final String code;
    private final String name;
}
