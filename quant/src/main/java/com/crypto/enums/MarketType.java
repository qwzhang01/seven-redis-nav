package com.crypto.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 市场类型枚举
 */
@Getter
@AllArgsConstructor
public enum MarketType {

    SPOT("SPOT", "现货"),
    FUTURES("FUTURES", "合约");

    private final String code;
    private final String name;

    public static MarketType fromCode(String code) {
        for (MarketType m : values()) {
            if (m.code.equalsIgnoreCase(code)) {
                return m;
            }
        }
        throw new IllegalArgumentException("Unknown market type: " + code);
    }
}
