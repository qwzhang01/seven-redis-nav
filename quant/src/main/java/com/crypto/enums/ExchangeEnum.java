package com.crypto.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 交易所枚举
 */
@Getter
@AllArgsConstructor
public enum ExchangeEnum {

    BINANCE("BINANCE", "币安"),
    OKX("OKX", "欧易");

    private final String code;
    private final String name;

    public static ExchangeEnum fromCode(String code) {
        for (ExchangeEnum e : values()) {
            if (e.code.equalsIgnoreCase(code)) {
                return e;
            }
        }
        throw new IllegalArgumentException("Unknown exchange: " + code);
    }
}
