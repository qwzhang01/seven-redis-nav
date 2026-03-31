package com.crypto.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * 交易所配置属性
 */
@Data
@Component
@ConfigurationProperties(prefix = "exchange")
public class ExchangeProperties {

    private String defaultExchange = "BINANCE";
    private BinanceConfig binance = new BinanceConfig();
    private OkxConfig okx = new OkxConfig();

    @Data
    public static class BinanceConfig {
        private String apiKey;
        private String secretKey;
        private String passphrase;
        private String baseUrl = "https://api.binance.com";
        private String futuresBaseUrl = "https://fapi.binance.com";
        private String wsBaseUrl = "wss://stream.binance.com:9443/ws";
        private String futuresWsBaseUrl = "wss://fstream.binance.com/ws";
        private ProxyConfig proxy = new ProxyConfig();
    }

    @Data
    public static class OkxConfig {
        private String apiKey;
        private String secretKey;
        private String passphrase;
        private String baseUrl = "https://www.okx.com";
        private String wsPublicUrl = "wss://ws.okx.com:8443/ws/v5/public";
        private String wsPrivateUrl = "wss://ws.okx.com:8443/ws/v5/private";
        private boolean simulated = false;
        private ProxyConfig proxy = new ProxyConfig();
    }

    @Data
    public static class ProxyConfig {
        private boolean enabled = false;
        private String host = "127.0.0.1";
        private int port = 7890;
    }
}
