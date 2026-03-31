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

/**
 * OKX WebSocket 客户端
 *
 * 支持订阅:
 * - 实时Tick行情 (tickers)
 * - 深度数据 (books5)
 * - K线数据 (candle)
 *
 * 公共频道: wss://ws.okx.com:8443/ws/v5/public
 */
@Slf4j
public class OkxWebSocketClient extends AbstractExchangeWebSocketClient {

    private final MarketType marketType;
    private final List<String> symbols;
    private final List<String> klineIntervals;
    private final ObjectMapper objectMapper;
    private final CacheService cacheService;
    private final MarketDataService marketDataService;

    public OkxWebSocketClient(ExchangeProperties.OkxConfig config,
                              MarketType marketType,
                              List<String> symbols,
                              List<String> klineIntervals,
                              ObjectMapper objectMapper,
                              CacheService cacheService,
                              MarketDataService marketDataService) {
        super(
                config.getWsPublicUrl(),
                "OKX-WS-" + marketType.getCode(),
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
            subscribeMsg.put("op", "subscribe");

            ArrayNode args = objectMapper.createArrayNode();

            for (String symbol : symbols) {
                String instId = convertToInstId(symbol);

                // 订阅Ticker
                ObjectNode tickerArg = objectMapper.createObjectNode();
                tickerArg.put("channel", "tickers");
                tickerArg.put("instId", instId);
                args.add(tickerArg);

                // 订阅深度5档
                ObjectNode depthArg = objectMapper.createObjectNode();
                depthArg.put("channel", "books5");
                depthArg.put("instId", instId);
                args.add(depthArg);

                // 订阅K线
                for (String interval : klineIntervals) {
                    ObjectNode klineArg = objectMapper.createObjectNode();
                    klineArg.put("channel", "candle" + convertInterval(interval));
                    klineArg.put("instId", instId);
                    args.add(klineArg);
                }
            }

            subscribeMsg.set("args", args);
            return objectMapper.writeValueAsString(subscribeMsg);
        } catch (Exception e) {
            log.error("[OKX-WS] 构建订阅消息异常", e);
            return null;
        }
    }

    @Override
    protected void handlePingPong(String message) {
        // OKX发送 "ping" 时需要回复 "pong"
        if ("ping".equals(message)) {
            send("pong");
        }
    }

    @Override
    protected void onConnected() {
        log.info("[OKX-WS] 连接成功, marketType={}, symbols={}", marketType, symbols);
    }

    /**
     * 处理收到的WebSocket消息
     */
    public void handleMessage(String message) {
        try {
            // ping/pong 文本
            if ("pong".equals(message)) {
                return;
            }

            JsonNode json = objectMapper.readTree(message);

            // 订阅确认
            if (json.has("event")) {
                String event = json.get("event").asText();
                if ("subscribe".equals(event)) {
                    log.debug("[OKX-WS] 订阅确认: {}", json.has("arg") ? json.get("arg") : "");
                } else if ("error".equals(event)) {
                    log.error("[OKX-WS] 订阅错误: code={}, msg={}",
                            json.has("code") ? json.get("code").asText() : "",
                            json.has("msg") ? json.get("msg").asText() : "");
                }
                return;
            }

            // 数据推送
            if (json.has("arg") && json.has("data")) {
                JsonNode arg = json.get("arg");
                String channel = arg.get("channel").asText();
                JsonNode data = json.get("data");

                if ("tickers".equals(channel)) {
                    handleTickMessage(arg, data);
                } else if ("books5".equals(channel)) {
                    handleDepthMessage(arg, data);
                } else if (channel.startsWith("candle")) {
                    handleKlineMessage(arg, data, channel);
                }
            }
        } catch (Exception e) {
            log.debug("[OKX-WS] 消息解析异常: {}", message, e);
        }
    }

    private void handleTickMessage(JsonNode arg, JsonNode data) {
        try {
            String instId = arg.get("instId").asText();
            String originalSymbol = reverseInstId(instId);

            for (int i = 0; i < data.size(); i++) {
                JsonNode item = data.get(i);

                BigDecimal lastPrice = safeDecimal(item, "last");
                BigDecimal open24h = safeDecimal(item, "open24h");
                BigDecimal priceChange = lastPrice.subtract(open24h);
                BigDecimal priceChangePct = BigDecimal.ZERO;
                if (open24h.compareTo(BigDecimal.ZERO) > 0) {
                    priceChangePct = priceChange.multiply(new BigDecimal("100"))
                            .divide(open24h, 4, BigDecimal.ROUND_HALF_UP);
                }

                TickDTO tick = TickDTO.builder()
                        .exchange(ExchangeEnum.OKX.getCode())
                        .symbol(originalSymbol)
                        .marketType(marketType.getCode())
                        .lastPrice(lastPrice)
                        .bestBidPrice(safeDecimal(item, "bidPx"))
                        .bestBidQty(safeDecimal(item, "bidSz"))
                        .bestAskPrice(safeDecimal(item, "askPx"))
                        .bestAskQty(safeDecimal(item, "askSz"))
                        .volume24h(safeDecimal(item, "vol24h"))
                        .quoteVolume24h(safeDecimal(item, "volCcy24h"))
                        .high24h(safeDecimal(item, "high24h"))
                        .low24h(safeDecimal(item, "low24h"))
                        .open24h(open24h)
                        .priceChange(priceChange)
                        .priceChangePct(priceChangePct)
                        .eventTime(item.has("ts") ? item.get("ts").asLong() : System.currentTimeMillis())
                        .build();

                cacheService.putTick(ExchangeEnum.OKX.getCode(), originalSymbol, marketType.getCode(), tick);
                marketDataService.saveTick(tick);
            }
        } catch (Exception e) {
            log.debug("[OKX-WS] Tick消息处理异常", e);
        }
    }

    private void handleDepthMessage(JsonNode arg, JsonNode data) {
        try {
            String instId = arg.get("instId").asText();
            String originalSymbol = reverseInstId(instId);

            for (int i = 0; i < data.size(); i++) {
                JsonNode item = data.get(i);

                DepthDTO depth = DepthDTO.builder()
                        .exchange(ExchangeEnum.OKX.getCode())
                        .symbol(originalSymbol)
                        .marketType(marketType.getCode())
                        .lastUpdateId(item.has("ts") ? item.get("ts").asLong() : 0L)
                        .bids(parseOkxDepthEntries(item.get("bids")))
                        .asks(parseOkxDepthEntries(item.get("asks")))
                        .eventTime(item.has("ts") ? item.get("ts").asLong() : System.currentTimeMillis())
                        .build();

                cacheService.putDepth(ExchangeEnum.OKX.getCode(), originalSymbol, marketType.getCode(), depth);
            }
        } catch (Exception e) {
            log.debug("[OKX-WS] Depth消息处理异常", e);
        }
    }

    private void handleKlineMessage(JsonNode arg, JsonNode data, String channel) {
        try {
            String instId = arg.get("instId").asText();
            String originalSymbol = reverseInstId(instId);
            // candle1m -> 1m
            String interval = channel.replace("candle", "");

            for (int i = 0; i < data.size(); i++) {
                JsonNode item = data.get(i);
                // OKX WS K线: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
                if (!item.isArray() || item.size() < 9) continue;

                boolean isConfirmed = "1".equals(item.get(8).asText());
                long ts = item.get(0).asLong();

                KlineDTO klineDTO = KlineDTO.builder()
                        .exchange(ExchangeEnum.OKX.getCode())
                        .symbol(originalSymbol)
                        .marketType(marketType.getCode())
                        .interval(interval)
                        .openTime(ts)
                        .closeTime(ts) // OKX doesn't provide explicit closeTime in WS
                        .openPrice(new BigDecimal(item.get(1).asText()))
                        .highPrice(new BigDecimal(item.get(2).asText()))
                        .lowPrice(new BigDecimal(item.get(3).asText()))
                        .closePrice(new BigDecimal(item.get(4).asText()))
                        .volume(new BigDecimal(item.get(5).asText()))
                        .quoteVolume(safeParseBigDecimal(item.get(7).asText()))
                        .tradesCount(0)
                        .takerBuyVolume(BigDecimal.ZERO)
                        .takerBuyQuoteVolume(BigDecimal.ZERO)
                        .build();

                // 只有K线确认时才写入数据库
                if (isConfirmed) {
                    marketDataService.saveKlines(Collections.singletonList(klineDTO));
                    log.debug("[OKX-WS] K线已确认并保存: {}/{}/{}", originalSymbol, interval, marketType);
                }
            }
        } catch (Exception e) {
            log.debug("[OKX-WS] K线消息处理异常", e);
        }
    }

    private List<BigDecimal[]> parseOkxDepthEntries(JsonNode entries) {
        List<BigDecimal[]> result = new ArrayList<>();
        if (entries == null || !entries.isArray()) return result;
        for (int i = 0; i < entries.size(); i++) {
            JsonNode entry = entries.get(i);
            if (entry.isArray() && entry.size() >= 2) {
                result.add(new BigDecimal[]{
                        new BigDecimal(entry.get(0).asText()),
                        new BigDecimal(entry.get(1).asText())
                });
            }
        }
        return result;
    }

    /**
     * BTC/USDT -> BTC-USDT 或 BTC-USDT-SWAP
     */
    private String convertToInstId(String symbol) {
        String base = symbol.replace("/", "-");
        if (marketType == MarketType.FUTURES) {
            return base + "-SWAP";
        }
        return base;
    }

    /**
     * BTC-USDT -> BTC/USDT, BTC-USDT-SWAP -> BTC/USDT
     */
    private String reverseInstId(String instId) {
        String cleaned = instId.replace("-SWAP", "");
        for (String s : symbols) {
            if (s.replace("/", "-").equalsIgnoreCase(cleaned)) {
                return s;
            }
        }
        return cleaned.replace("-", "/");
    }

    /**
     * 1m -> 1m, 5m -> 5m, 1h -> 1H, 4h -> 4H, 1d -> 1D
     */
    private String convertInterval(String interval) {
        if (interval.endsWith("h")) {
            return interval.replace("h", "H");
        } else if (interval.endsWith("d")) {
            return interval.replace("d", "D");
        }
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

    private BigDecimal safeParseBigDecimal(String value) {
        if (value == null || value.isEmpty() || "null".equalsIgnoreCase(value)) {
            return BigDecimal.ZERO;
        }
        try {
            return new BigDecimal(value);
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }
}
