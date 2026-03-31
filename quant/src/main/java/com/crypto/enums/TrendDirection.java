package com.crypto.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 趋势方向
 */
@Getter
@AllArgsConstructor
public enum TrendDirection {

    BULLISH("BULLISH", "看涨"),
    BEARISH("BEARISH", "看跌"),
    NEUTRAL("NEUTRAL", "中性");

    private final String code;
    private final String name;

    public static TrendDirection fromCode(String code) {
        for (TrendDirection t : values()) {
            if (t.code.equalsIgnoreCase(code)) {
                return t;
            }
        }
        return NEUTRAL;
    }
}
