package com.crypto.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.List;

/**
 * 交易配置属性
 */
@Data
@Component
@ConfigurationProperties(prefix = "trading")
public class TradingProperties {

    private SymbolConfig symbols = new SymbolConfig();
    private List<String> klineIntervals = Arrays.asList("1m", "5m", "15m", "1h", "4h", "1d");
    private SyncConfig sync = new SyncConfig();

    @Data
    public static class SymbolConfig {
        private List<String> spot = Arrays.asList("BTC/USDT", "ETH/USDT");
        private List<String> futures = Arrays.asList("BTC/USDT", "ETH/USDT");
    }

    @Data
    public static class SyncConfig {
        /** K线同步间隔(毫秒) */
        private long klineInterval = 60000;
        /** Tick同步间隔(毫秒) */
        private long tickInterval = 5000;
        /** 深度同步间隔(毫秒) */
        private long depthInterval = 10000;
        /** 历史数据天数 */
        private int historyDays = 30;
        /** 是否启用WebSocket实时同步 (启用后Tick和Depth走WS, K线走WS+HTTP补漏) */
        private boolean wsEnabled = false;
    }
}
