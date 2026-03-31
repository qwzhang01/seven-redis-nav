package com.crypto.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 交易信号类型
 */
@Getter
@AllArgsConstructor
public enum SignalType {

    BUY("BUY", "买入信号"),
    SELL("SELL", "卖出信号"),
    HOLD("HOLD", "持有观望");

    private final String code;
    private final String name;
}
