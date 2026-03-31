package com.crypto.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * K线周期枚举 - 统一各交易所的周期映射
 */
@Getter
@AllArgsConstructor
public enum KlineInterval {

    M1("1m", "1分钟", 60_000L),
    M3("3m", "3分钟", 180_000L),
    M5("5m", "5分钟", 300_000L),
    M15("15m", "15分钟", 900_000L),
    M30("30m", "30分钟", 1_800_000L),
    H1("1h", "1小时", 3_600_000L),
    H2("2h", "2小时", 7_200_000L),
    H4("4h", "4小时", 14_400_000L),
    H6("6h", "6小时", 21_600_000L),
    H12("12h", "12小时", 43_200_000L),
    D1("1d", "1天", 86_400_000L),
    W1("1w", "1周", 604_800_000L),
    MO1("1M", "1月", 2_592_000_000L);

    private final String code;
    private final String name;
    private final long milliseconds;

    /**
     * 获取币安对应的K线参数
     */
    public String toBinanceInterval() {
        switch (this) {
            case M1: return "1m";
            case M3: return "3m";
            case M5: return "5m";
            case M15: return "15m";
            case M30: return "30m";
            case H1: return "1h";
            case H2: return "2h";
            case H4: return "4h";
            case H6: return "6h";
            case H12: return "12h";
            case D1: return "1d";
            case W1: return "1w";
            case MO1: return "1M";
            default: return "1h";
        }
    }

    /**
     * 获取OKX对应的K线参数
     */
    public String toOkxInterval() {
        switch (this) {
            case M1: return "1m";
            case M3: return "3m";
            case M5: return "5m";
            case M15: return "15m";
            case M30: return "30m";
            case H1: return "1H";
            case H2: return "2H";
            case H4: return "4H";
            case H6: return "6H";
            case H12: return "12H";
            case D1: return "1D";
            case W1: return "1W";
            case MO1: return "1M";
            default: return "1H";
        }
    }

    public static KlineInterval fromCode(String code) {
        for (KlineInterval k : values()) {
            if (k.code.equalsIgnoreCase(code)) {
                return k;
            }
        }
        throw new IllegalArgumentException("Unknown kline interval: " + code);
    }
}
