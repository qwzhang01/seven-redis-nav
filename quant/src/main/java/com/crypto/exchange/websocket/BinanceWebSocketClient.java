package com.crypto.exchange.websocket;

import com.crypto.config.ExchangeProperties;
import com.crypto.enums.ExchangeEnum;
import com.crypto.enums.MarketType;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.KlineDTO;
import com.crypto.model.dto.TickDTO;
import com.crypto.service.CacheService;
import com.crypto.service.MarketDataService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 币安 WebSocket 客户端
 *
 * 支持订阅:
 * - 实时Tick行情 (miniTicker)
 * - 深度数据 (depth)
 * - K线数据 (kline)
 *
 * 现货: wss://stream.binance.com:9443/ws
 * 合约: wss://fstream.binance.com/ws
 */
@Slf4j
public class BinanceWebSocketClient extends AbstractExchangeWebSocketClient {

    private final MarketType marketType;
    private final List<String> symbols;
    private final List<String> klineIntervals;
    private final ObjectMapper objectMapper;
    private final CacheService cacheService;
    private final MarketDataService marketDataService;

    public BinanceWebSocketClient(ExchangeProperties.BinanceConfig config,
                                  MarketType marketType,
                                  List<String> symbols,
                                  List<String> klineIntervals,
                                  ObjectMapper objectMapper,
                                  CacheService cacheService,
                                  MarketDataService marketDataService) {
        super(
                marketType == MarketType.SPOT ? config.getWsBaseUrl() : config.getFuturesWsBaseUrl(),
                "Binance-WS-" + marketType.getCode(),
                null
        );
        this.marketType = marketType;
        this.symbols = symbols;
        this.klineIntervals = klineIntervals;
        this.objectMapper = objectMapper;
        this.cacheService = cacheService;
        this.marketDataService = marketDataService;
    }

    @Override
    protected String buildSubscribeMessage() {
        try {
            ObjectNode subscribeMsg = objectMapper.createObjectNode();
            subscribeMsg.put("method", "SUBSCRIBE");

            ArrayNode params = objectMapper.createArrayNode();

            for (String symbol : symbols) {
                // 币安WS符号格式: btcusdt (小写, 无分隔符)
                String wsSymbol = symbol.replace("/", "").toLowerCase();

                // 订阅miniTicker (实时Tick简报)
                params.add(wsSymbol + "@miniTicker");

                // 订阅深度 (增量, 每100ms)
                params.add(wsSymbol + "@depth20@100ms");

                // 订阅K线
                for (String interval : klineIntervals) {
                    String binanceInterval = convertInterval(interval);
                    params.add(wsSymbol + "@kline_" + binanceInterval);
                }
            }

            subscribeMsg.set("params", params);
            subscribeMsg.put("id", System.currentTimeMillis());

            return objectMapper.writeValueAsString(subscribeMsg);
        } catch (Exception e) {
            log.error("[Binance-WS] 构建订阅消息异常", e);
            return null;
        }
    }

    @Override
    protected void handlePingPong(String message) {
        // 币安WS会发送ping帧，Java-WebSocket库会自动处理
        // 无需额外处理
    }

    @Override
    protected void onConnected() {
        log.info("[Binance-WS] 连接成功, marketType={}, symbols={}", marketType, symbols);
    }

    /**
     * 处理收到的WebSocket消息（由MarketSyncService调用）
     */
    public void handleMessage(String message) {
        try {
            JsonNode json = objectMapper.readTree(message);

            // 订阅确认消息
            if (json.has("result") || json.has("id")) {
                return;
            }

            // 获取事件类型
            String eventType = json.has("e") ? json.get("e").asText() : "";

            switch (eventType) {
                case "24hrMiniTicker":
                    handleTickMessage(json);
                    break;
                case "depthUpdate":
                    handleDepthMessage(json);
                    break;
                case "kline":
                    handleKlineMessage(json);
                    break;
                default:
                    // 可能是组合消息格式
                    if (json.has("stream") && json.has("data")) {
                        handleMessage(objectMapper.writeValueAsString(json.get("data")));
                    }
                    break;
            }
        } catch (Exception e) {
            log.debug("[Binance-WS] 消息解析异常: {}", message, e);
        }
    }

    private void handleTickMessage(JsonNode json) {
        try {
            String wsSymbol = json.get("s").asText(); // BTCUSDT
            String originalSymbol = reverseSymbol(wsSymbol);

            TickDTO tick = TickDTO.builder()
                    .exchange(ExchangeEnum.BINANCE.getCode())
                    .symbol(originalSymbol)
                    .marketType(marketType.getCode())
                    .lastPrice(safeDecimal(json, "c"))
                    .open24h(safeDecimal(json, "o"))
                    .high24h(safeDecimal(json, "h"))
                    .low24h(safeDecimal(json, "l"))
                    .volume24h(safeDecimal(json, "v"))
                    .quoteVolume24h(safeDecimal(json, "q"))
                    .bestBidPrice(BigDecimal.ZERO)
                    .bestBidQty(BigDecimal.ZERO)
                    .bestAskPrice(BigDecimal.ZERO)
                    .bestAskQty(BigDecimal.ZERO)
                    .priceChange(BigDecimal.ZERO)
                    .priceChangePct(BigDecimal.ZERO)
                    .eventTime(json.get("E").asLong())
                    .build();

            // 计算涨跌
            if (tick.getOpen24h().compareTo(BigDecimal.ZERO) > 0) {
                BigDecimal change = tick.getLastPrice().subtract(tick.getOpen24h());
                tick.setPriceChange(change);
                tick.setPriceChangePct(change.multiply(new BigDecimal("100"))
                        .divide(tick.getOpen24h(), 4, BigDecimal.ROUND_HALF_UP));
            }

            // 更新缓存
            cacheService.putTick(ExchangeEnum.BINANCE.getCode(), originalSymbol, marketType.getCode(), tick);

            // 异步写入数据库
            marketDataService.saveTick(tick);

        } catch (Exception e) {
            log.debug("[Binance-WS] Tick消息处理异常", e);
        }
    }

    private void handleDepthMessage(JsonNode json) {
        try {
            String wsSymbol = json.get("s").asText();
            String originalSymbol = reverseSymbol(wsSymbol);

            DepthDTO depth = DepthDTO.builder()
                    .exchange(ExchangeEnum.BINANCE.getCode())
                    .symbol(originalSymbol)
                    .marketType(marketType.getCode())
                    .lastUpdateId(json.get("u").asLong())
                    .bids(parseDepthEntries(json.get("b")))
                    .asks(parseDepthEntries(json.get("a")))
                    .eventTime(json.get("E").asLong())
                    .build();

            // 更新缓存
            cacheService.putDepth(ExchangeEnum.BINANCE.getCode(), originalSymbol, marketType.getCode(), depth);

        } catch (Exception e) {
            log.debug("[Binance-WS] Depth消息处理异常", e);
        }
    }

    private void handleKlineMessage(JsonNode json) {
        try {
            JsonNode kline = json.get("k");
            if (kline == null) return;

            String wsSymbol = kline.get("s").asText();
            String originalSymbol = reverseSymbol(wsSymbol);
            boolean isClosed = kline.get("x").asBoolean();

            KlineDTO klineDTO = KlineDTO.builder()
                    .exchange(ExchangeEnum.BINANCE.getCode())
                    .symbol(originalSymbol)
                    .marketType(marketType.getCode())
                    .interval(kline.get("i").asText())
                    .openTime(kline.get("t").asLong())
                    .closeTime(kline.get("T").asLong())
                    .openPrice(new BigDecimal(kline.get("o").asText()))
                    .highPrice(new BigDecimal(kline.get("h").asText()))
                    .lowPrice(new BigDecimal(kline.get("l").asText()))
                    .closePrice(new BigDecimal(kline.get("c").asText()))
                    .volume(new BigDecimal(kline.get("v").asText()))
                    .quoteVolume(new BigDecimal(kline.get("q").asText()))
                    .tradesCount(kline.get("n").asInt())
                    .takerBuyVolume(new BigDecimal(kline.get("V").asText()))
                    .takerBuyQuoteVolume(new BigDecimal(kline.get("Q").asText()))
                    .build();

            // 只有K线关闭时才写入数据库
            if (isClosed) {
                marketDataService.saveKlines(Collections.singletonList(klineDTO));
                log.debug("[Binance-WS] K线已关闭并保存: {}/{}/{}",
                        originalSymbol, klineDTO.getInterval(), marketType);
            }

        } catch (Exception e) {
            log.debug("[Binance-WS] K线消息处理异常", e);
        }
    }

    private List<BigDecimal[]> parseDepthEntries(JsonNode entries) {
        List<BigDecimal[]> result = new ArrayList<>();
        if (entries == null || !entries.isArray()) return result;
        for (int i = 0; i < entries.size(); i++) {
            JsonNode entry = entries.get(i);
            result.add(new BigDecimal[]{
                    new BigDecimal(entry.get(0).asText()),
                    new BigDecimal(entry.get(1).asText())
            });
        }
        return result;
    }

    /**
     * BTCUSDT -> BTC/USDT (简化处理，根据已知symbols反推)
     */
    private String reverseSymbol(String wsSymbol) {
        for (String s : symbols) {
            if (s.replace("/", "").equalsIgnoreCase(wsSymbol)) {
                return s;
            }
        }
        return wsSymbol;
    }

    private String convertInterval(String interval) {
        // 1m, 5m, 15m, 1h, 4h, 1d -> 币安格式一致
        return interval;
    }

    private BigDecimal safeDecimal(JsonNode json, String field) {
        if (json == null || !json.has(field) || json.get(field).isNull()) {
            return BigDecimal.ZERO;
        }
        try {
            return new BigDecimal(json.get(field).asText());
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }
}
