package com.crypto.service;

import com.crypto.config.ExchangeProperties;
import com.crypto.config.TradingProperties;
import com.crypto.enums.MarketType;
import com.crypto.exchange.websocket.BinanceWebSocketClient;
import com.crypto.exchange.websocket.OkxWebSocketClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.util.ArrayList;
import java.util.List;

/**
 * WebSocket 行情同步管理服务
 *
 * 管理币安和OKX两家交易所的WebSocket连接:
 * - 现货和合约各一个连接
 * - 自动订阅配置的交易对
 * - 接收实时行情更新到缓存和数据库
 *
 * 默认通过配置开关控制是否启用WS同步
 */
@Slf4j
@Service
public class WebSocketSyncService {

    private final ExchangeProperties exchangeProperties;
    private final TradingProperties tradingProperties;
    private final ObjectMapper objectMapper;
    private final CacheService cacheService;
    private final MarketDataService marketDataService;

    private final List<BinanceWebSocketClient> binanceClients = new ArrayList<>();
    private final List<OkxWebSocketClient> okxClients = new ArrayList<>();

    public WebSocketSyncService(ExchangeProperties exchangeProperties,
                                TradingProperties tradingProperties,
                                ObjectMapper objectMapper,
                                CacheService cacheService,
                                MarketDataService marketDataService) {
        this.exchangeProperties = exchangeProperties;
        this.tradingProperties = tradingProperties;
        this.objectMapper = objectMapper;
        this.cacheService = cacheService;
        this.marketDataService = marketDataService;
    }

    /**
     * 启动时初始化WebSocket连接
     */
    @PostConstruct
    public void init() {
        if (!tradingProperties.getSync().isWsEnabled()) {
            log.info("[WebSocket] WebSocket同步未启用, 使用HTTP轮询模式");
            return;
        }

        log.info("========== 初始化WebSocket行情同步 ==========");

        // 等待Spring完全初始化后再启动WS
        new Thread(() -> {
            try {
                Thread.sleep(8000);
                startBinanceWebSockets();
                startOkxWebSockets();
                log.info("========== WebSocket行情同步已启动 ==========");
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "ws-init").start();
    }

    /**
     * 关闭时断开所有WebSocket
     */
    @PreDestroy
    public void destroy() {
        log.info("========== 关闭所有WebSocket连接 ==========");
        binanceClients.forEach(client -> {
            try {
                client.disconnect();
            } catch (Exception e) {
                log.warn("关闭Binance WS异常", e);
            }
        });
        okxClients.forEach(client -> {
            try {
                client.disconnect();
            } catch (Exception e) {
                log.warn("关闭OKX WS异常", e);
            }
        });
    }

    /**
     * 启动币安WebSocket
     */
    private void startBinanceWebSockets() {
        ExchangeProperties.BinanceConfig config = exchangeProperties.getBinance();
        List<String> klineIntervals = tradingProperties.getKlineIntervals();

        // 现货WebSocket
        List<String> spotSymbols = tradingProperties.getSymbols().getSpot();
        if (!spotSymbols.isEmpty()) {
            BinanceWebSocketClient spotClient = new BinanceWebSocketClient(
                    config, MarketType.SPOT, spotSymbols, klineIntervals,
                    objectMapper, cacheService, marketDataService);
            spotClient.connect();
            binanceClients.add(spotClient);
            log.info("[Binance-WS] 现货WS已启动, symbols={}", spotSymbols);
        }

        // 合约WebSocket
        List<String> futuresSymbols = tradingProperties.getSymbols().getFutures();
        if (!futuresSymbols.isEmpty()) {
            BinanceWebSocketClient futuresClient = new BinanceWebSocketClient(
                    config, MarketType.FUTURES, futuresSymbols, klineIntervals,
                    objectMapper, cacheService, marketDataService);
            futuresClient.connect();
            binanceClients.add(futuresClient);
            log.info("[Binance-WS] 合约WS已启动, symbols={}", futuresSymbols);
        }
    }

    /**
     * 启动OKX WebSocket
     */
    private void startOkxWebSockets() {
        ExchangeProperties.OkxConfig config = exchangeProperties.getOkx();
        List<String> klineIntervals = tradingProperties.getKlineIntervals();

        // 现货WebSocket
        List<String> spotSymbols = tradingProperties.getSymbols().getSpot();
        if (!spotSymbols.isEmpty()) {
            OkxWebSocketClient spotClient = new OkxWebSocketClient(
                    config, MarketType.SPOT, spotSymbols, klineIntervals,
                    objectMapper, cacheService, marketDataService);
            spotClient.connect();
            okxClients.add(spotClient);
            log.info("[OKX-WS] 现货WS已启动, symbols={}", spotSymbols);
        }

        // 合约WebSocket
        List<String> futuresSymbols = tradingProperties.getSymbols().getFutures();
        if (!futuresSymbols.isEmpty()) {
            OkxWebSocketClient futuresClient = new OkxWebSocketClient(
                    config, MarketType.FUTURES, futuresSymbols, klineIntervals,
                    objectMapper, cacheService, marketDataService);
            futuresClient.connect();
            okxClients.add(futuresClient);
            log.info("[OKX-WS] 合约WS已启动, symbols={}", futuresSymbols);
        }
    }

    /**
     * 获取WebSocket连接状态
     */
    public String getConnectionStatus() {
        StringBuilder sb = new StringBuilder("=== WebSocket连接状态 ===\n");
        for (BinanceWebSocketClient client : binanceClients) {
            sb.append("Binance: connected=").append(client.isConnected()).append("\n");
        }
        for (OkxWebSocketClient client : okxClients) {
            sb.append("OKX: connected=").append(client.isConnected()).append("\n");
        }
        return sb.toString();
    }

    /**
     * 手动重连所有WebSocket
     */
    public void reconnectAll() {
        log.info("手动重连所有WebSocket");
        binanceClients.forEach(client -> {
            client.disconnect();
            client.connect();
        });
        okxClients.forEach(client -> {
            client.disconnect();
            client.connect();
        });
    }
}
