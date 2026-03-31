package com.crypto.exchange.okx;

import com.crypto.config.ExchangeProperties;
import com.crypto.enums.ExchangeEnum;
import com.crypto.enums.KlineInterval;
import com.crypto.enums.MarketType;
import com.crypto.exchange.ExchangeApiClient;
import com.crypto.exchange.util.SignatureUtil;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.KlineDTO;
import com.crypto.model.dto.TickDTO;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.apache.hc.core5.http.io.entity.StringEntity;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.*;

/**
 * OKX交易所API客户端 - 完整对接实现 (API V5)
 * 支持现货和合约的K线、Tick、Depth数据
 * 使用 Apache HttpClient 5 + Jackson 实现
 */
@Slf4j
@Component
public class OkxApiClient implements ExchangeApiClient {

    private final ExchangeProperties.OkxConfig config;
    private final CloseableHttpClient httpClient;
    private final ObjectMapper objectMapper;

    public OkxApiClient(ExchangeProperties exchangeProperties, CloseableHttpClient httpClient,
                        ObjectMapper objectMapper) {
        this.config = exchangeProperties.getOkx();
        this.httpClient = httpClient;
        this.objectMapper = objectMapper;
    }

    @Override
    public ExchangeEnum getExchange() {
        return ExchangeEnum.OKX;
    }

    // ===================== 行情接口 =====================

    @Override
    public List<KlineDTO> getKlines(String symbol, MarketType marketType, KlineInterval interval,
                                    Long startTime, Long endTime, Integer limit) {
        String instId = convertSymbol(symbol, marketType);

        boolean isHistory = startTime != null &&
                (System.currentTimeMillis() - startTime) > 2 * 24 * 60 * 60 * 1000L;

        StringBuilder urlBuilder = new StringBuilder(config.getBaseUrl())
                .append(isHistory ? "/api/v5/market/history-candles" : "/api/v5/market/candles")
                .append("?instId=").append(instId)
                .append("&bar=").append(interval.toOkxInterval());

        if (startTime != null) {
            urlBuilder.append("&after=").append(endTime != null ? endTime : System.currentTimeMillis());
            urlBuilder.append("&before=").append(startTime);
        }

        int queryLimit = limit != null ? Math.min(limit, 300) : 100;
        urlBuilder.append("&limit=").append(queryLimit);

        String responseBody = doPublicGet(urlBuilder.toString());
        if (responseBody == null) {
            return Collections.emptyList();
        }

        try {
            JsonNode respJson = objectMapper.readTree(responseBody);
            if (!"0".equals(getTextSafe(respJson, "code"))) {
                log.error("[OKX] 获取K线失败: code={}, msg={}", getTextSafe(respJson, "code"), getTextSafe(respJson, "msg"));
                return Collections.emptyList();
            }

            ArrayNode data = (ArrayNode) respJson.get("data");
            List<KlineDTO> result = new ArrayList<>(data.size());

            for (int i = 0; i < data.size(); i++) {
                ArrayNode item = (ArrayNode) data.get(i);
                long ts = item.get(0).asLong();
                result.add(KlineDTO.builder()
                        .exchange(ExchangeEnum.OKX.getCode())
                        .symbol(symbol)
                        .marketType(marketType.getCode())
                        .interval(interval.getCode())
                        .openTime(ts)
                        .closeTime(ts + interval.getMilliseconds())
                        .openPrice(new BigDecimal(item.get(1).asText()))
                        .highPrice(new BigDecimal(item.get(2).asText()))
                        .lowPrice(new BigDecimal(item.get(3).asText()))
                        .closePrice(new BigDecimal(item.get(4).asText()))
                        .volume(new BigDecimal(item.get(5).asText()))
                        .quoteVolume(safeParseBigDecimal(item.get(7).asText()))
                        .tradesCount(0)
                        .takerBuyVolume(BigDecimal.ZERO)
                        .takerBuyQuoteVolume(BigDecimal.ZERO)
                        .build());
            }

            Collections.reverse(result);

            log.debug("[OKX] 获取K线成功: symbol={}, interval={}, marketType={}, count={}",
                    symbol, interval.getCode(), marketType, result.size());
            return result;
        } catch (Exception e) {
            log.error("[OKX] 解析K线数据异常: symbol={}", symbol, e);
            return Collections.emptyList();
        }
    }

    @Override
    public TickDTO getTicker(String symbol, MarketType marketType) {
        String instId = convertSymbol(symbol, marketType);
        String url = config.getBaseUrl() + "/api/v5/market/ticker?instId=" + instId;

        String responseBody = doPublicGet(url);
        if (responseBody == null) {
            return null;
        }

        try {
            JsonNode respJson = objectMapper.readTree(responseBody);
            if (!"0".equals(getTextSafe(respJson, "code"))) {
                log.error("[OKX] 获取Tick失败: {}", getTextSafe(respJson, "msg"));
                return null;
            }

            JsonNode data = respJson.get("data");
            if (data == null || !data.isArray() || data.size() == 0) {
                return null;
            }

            return parseTickFromJson(data.get(0), symbol, marketType);
        } catch (Exception e) {
            log.error("[OKX] 解析Tick数据异常: symbol={}", symbol, e);
            return null;
        }
    }

    @Override
    public List<TickDTO> getTickers(List<String> symbols, MarketType marketType) {
        String instType = marketType == MarketType.SPOT ? "SPOT" : "SWAP";
        String url = config.getBaseUrl() + "/api/v5/market/tickers?instType=" + instType;

        String responseBody = doPublicGet(url);
        if (responseBody == null) {
            return Collections.emptyList();
        }

        try {
            JsonNode respJson = objectMapper.readTree(responseBody);
            if (!"0".equals(getTextSafe(respJson, "code"))) {
                return Collections.emptyList();
            }

            JsonNode data = respJson.get("data");
            Map<String, String> instIdToSymbol = new HashMap<>();
            for (String s : symbols) {
                instIdToSymbol.put(convertSymbol(s, marketType), s);
            }

            List<TickDTO> result = new ArrayList<>();
            for (int i = 0; i < data.size(); i++) {
                JsonNode json = data.get(i);
                String instId = json.get("instId").asText();
                if (instIdToSymbol.containsKey(instId)) {
                    result.add(parseTickFromJson(json, instIdToSymbol.get(instId), marketType));
                }
            }
            return result;
        } catch (Exception e) {
            log.error("[OKX] 解析Tickers数据异常", e);
            return Collections.emptyList();
        }
    }

    @Override
    public DepthDTO getDepth(String symbol, MarketType marketType, int limit) {
        String instId = convertSymbol(symbol, marketType);
        String url = config.getBaseUrl() + "/api/v5/market/books?instId=" + instId + "&sz=" + limit;

        String responseBody = doPublicGet(url);
        if (responseBody == null) {
            return null;
        }

        try {
            JsonNode respJson = objectMapper.readTree(responseBody);
            if (!"0".equals(getTextSafe(respJson, "code"))) {
                return null;
            }

            JsonNode data = respJson.get("data");
            if (data == null || !data.isArray() || data.size() == 0) {
                return null;
            }

            JsonNode book = data.get(0);
            return DepthDTO.builder()
                    .exchange(ExchangeEnum.OKX.getCode())
                    .symbol(symbol)
                    .marketType(marketType.getCode())
                    .lastUpdateId(book.has("ts") ? book.get("ts").asLong() : 0L)
                    .bids(parseOkxDepthEntries(book.get("bids")))
                    .asks(parseOkxDepthEntries(book.get("asks")))
                    .eventTime(book.has("ts") ? book.get("ts").asLong() : System.currentTimeMillis())
                    .build();
        } catch (Exception e) {
            log.error("[OKX] 解析Depth数据异常: symbol={}", symbol, e);
            return null;
        }
    }

    // ===================== 交易接口 =====================

    @Override
    public String placeOrder(String symbol, MarketType marketType, String side, String positionSide,
                             String orderType, String price, String quantity) {
        String instId = convertSymbol(symbol, marketType);

        try {
            ObjectNode body = objectMapper.createObjectNode();
            body.put("instId", instId);
            body.put("tdMode", marketType == MarketType.SPOT ? "cash" : "cross");
            body.put("side", side.toLowerCase());
            body.put("ordType", convertOrderType(orderType));
            body.put("sz", quantity);

            if (marketType == MarketType.FUTURES && positionSide != null) {
                body.put("posSide", positionSide.toLowerCase());
            }

            if ("LIMIT".equalsIgnoreCase(orderType) && price != null) {
                body.put("px", price);
            }

            String requestPath = "/api/v5/trade/order";
            String bodyStr = objectMapper.writeValueAsString(body);
            String responseBody = doPrivatePost(requestPath, bodyStr);

            if (responseBody == null) {
                throw new RuntimeException("[OKX] 下单失败: " + symbol);
            }

            JsonNode respJson = objectMapper.readTree(responseBody);
            if (!"0".equals(getTextSafe(respJson, "code"))) {
                String msg = getTextSafe(respJson, "msg");
                JsonNode dataArr = respJson.get("data");
                if (dataArr != null && dataArr.isArray() && dataArr.size() > 0) {
                    msg = getTextSafe(dataArr.get(0), "sMsg");
                }
                log.error("[OKX] 下单失败: symbol={}, error={}", symbol, msg);
                throw new RuntimeException("[OKX] 下单失败: " + msg);
            }

            JsonNode data = respJson.get("data");
            String orderId = data.get(0).get("ordId").asText();
            log.info("[OKX] 下单成功: symbol={}, side={}, type={}, qty={}, orderId={}",
                    symbol, side, orderType, quantity, orderId);
            return orderId;

        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            log.error("[OKX] 下单异常: symbol={}", symbol, e);
            throw new RuntimeException("[OKX] 下单异常: " + e.getMessage(), e);
        }
    }

    @Override
    public boolean cancelOrder(String symbol, MarketType marketType, String orderId) {
        String instId = convertSymbol(symbol, marketType);

        try {
            ObjectNode body = objectMapper.createObjectNode();
            body.put("instId", instId);
            body.put("ordId", orderId);

            String requestPath = "/api/v5/trade/cancel-order";
            String responseBody = doPrivatePost(requestPath, objectMapper.writeValueAsString(body));

            if (responseBody != null) {
                JsonNode respJson = objectMapper.readTree(responseBody);
                return "0".equals(getTextSafe(respJson, "code"));
            }
        } catch (Exception e) {
            log.error("[OKX] 撤单异常: symbol={}, orderId={}", symbol, orderId, e);
        }
        return false;
    }

    @Override
    public String getOrderStatus(String symbol, MarketType marketType, String orderId) {
        String instId = convertSymbol(symbol, marketType);
        String requestPath = "/api/v5/trade/order?instId=" + instId + "&ordId=" + orderId;

        String timestamp = getIsoTimestamp();
        String sign = signRequest(timestamp, "GET", requestPath, "");

        try {
            HttpGet httpGet = new HttpGet(config.getBaseUrl() + requestPath);
            httpGet.setHeader("OK-ACCESS-KEY", config.getApiKey());
            httpGet.setHeader("OK-ACCESS-SIGN", sign);
            httpGet.setHeader("OK-ACCESS-TIMESTAMP", timestamp);
            httpGet.setHeader("OK-ACCESS-PASSPHRASE", config.getPassphrase());
            httpGet.setHeader("Content-Type", "application/json");

            return httpClient.execute(httpGet, response -> {
                if (response.getCode() >= 200 && response.getCode() < 300 && response.getEntity() != null) {
                    String body = EntityUtils.toString(response.getEntity());
                    JsonNode respJson = objectMapper.readTree(body);
                    if ("0".equals(getTextSafe(respJson, "code"))) {
                        JsonNode data = respJson.get("data");
                        return convertOkxOrderStatus(data.get(0).get("state").asText());
                    }
                }
                EntityUtils.consume(response.getEntity());
                return null;
            });
        } catch (Exception e) {
            log.error("[OKX] 查询订单状态异常", e);
        }
        return null;
    }

    @Override
    public String getBalance(String asset) {
        String requestPath = "/api/v5/account/balance?ccy=" + asset;

        String timestamp = getIsoTimestamp();
        String sign = signRequest(timestamp, "GET", requestPath, "");

        try {
            HttpGet httpGet = new HttpGet(config.getBaseUrl() + requestPath);
            httpGet.setHeader("OK-ACCESS-KEY", config.getApiKey());
            httpGet.setHeader("OK-ACCESS-SIGN", sign);
            httpGet.setHeader("OK-ACCESS-TIMESTAMP", timestamp);
            httpGet.setHeader("OK-ACCESS-PASSPHRASE", config.getPassphrase());
            httpGet.setHeader("Content-Type", "application/json");

            return httpClient.execute(httpGet, response -> {
                if (response.getCode() >= 200 && response.getCode() < 300 && response.getEntity() != null) {
                    String body = EntityUtils.toString(response.getEntity());
                    JsonNode respJson = objectMapper.readTree(body);
                    if ("0".equals(getTextSafe(respJson, "code"))) {
                        JsonNode data = respJson.get("data");
                        if (data.isArray() && data.size() > 0) {
                            JsonNode details = data.get(0).get("details");
                            if (details != null && details.isArray()) {
                                for (int i = 0; i < details.size(); i++) {
                                    JsonNode detail = details.get(i);
                                    if (asset.equalsIgnoreCase(detail.get("ccy").asText())) {
                                        return detail.get("availBal").asText();
                                    }
                                }
                            }
                        }
                    }
                }
                EntityUtils.consume(response.getEntity());
                return "0";
            });
        } catch (Exception e) {
            log.error("[OKX] 查询余额异常", e);
        }
        return "0";
    }

    // ===================== 工具方法 =====================

    @Override
    public String convertSymbol(String symbol, MarketType marketType) {
        String base = symbol.replace("/", "-");
        if (marketType == MarketType.FUTURES) {
            return base + "-SWAP";
        }
        return base;
    }

    private TickDTO parseTickFromJson(JsonNode json, String symbol, MarketType marketType) {
        BigDecimal lastPrice = safeParseBigDecimal(getTextSafe(json, "last"));
        BigDecimal open24h = safeParseBigDecimal(getTextSafe(json, "open24h"));
        BigDecimal priceChange = lastPrice.subtract(open24h);
        BigDecimal priceChangePct = BigDecimal.ZERO;
        if (open24h.compareTo(BigDecimal.ZERO) > 0) {
            priceChangePct = priceChange.multiply(new BigDecimal("100"))
                    .divide(open24h, 4, BigDecimal.ROUND_HALF_UP);
        }

        return TickDTO.builder()
                .exchange(ExchangeEnum.OKX.getCode())
                .symbol(symbol)
                .marketType(marketType.getCode())
                .lastPrice(lastPrice)
                .bestBidPrice(safeParseBigDecimal(getTextSafe(json, "bidPx")))
                .bestBidQty(safeParseBigDecimal(getTextSafe(json, "bidSz")))
                .bestAskPrice(safeParseBigDecimal(getTextSafe(json, "askPx")))
                .bestAskQty(safeParseBigDecimal(getTextSafe(json, "askSz")))
                .volume24h(safeParseBigDecimal(getTextSafe(json, "vol24h")))
                .quoteVolume24h(safeParseBigDecimal(getTextSafe(json, "volCcy24h")))
                .high24h(safeParseBigDecimal(getTextSafe(json, "high24h")))
                .low24h(safeParseBigDecimal(getTextSafe(json, "low24h")))
                .open24h(open24h)
                .priceChange(priceChange)
                .priceChangePct(priceChangePct)
                .eventTime(json.has("ts") ? json.get("ts").asLong() : System.currentTimeMillis())
                .build();
    }

    private List<BigDecimal[]> parseOkxDepthEntries(JsonNode entries) {
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

    private String convertOrderType(String orderType) {
        switch (orderType.toUpperCase()) {
            case "MARKET": return "market";
            case "LIMIT": return "limit";
            case "STOP_MARKET": return "market";
            default: return "market";
        }
    }

    private String convertOkxOrderStatus(String state) {
        switch (state) {
            case "live": return "SUBMITTED";
            case "partially_filled": return "PARTIALLY_FILLED";
            case "filled": return "FILLED";
            case "canceled": return "CANCELLED";
            default: return state.toUpperCase();
        }
    }

    private String getIsoTimestamp() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'");
        sdf.setTimeZone(TimeZone.getTimeZone("UTC"));
        return sdf.format(new Date());
    }

    private String signRequest(String timestamp, String method, String requestPath, String body) {
        String preSign = timestamp + method.toUpperCase() + requestPath + (body != null ? body : "");
        return SignatureUtil.hmacSha256Base64(preSign, config.getSecretKey());
    }

    private String getTextSafe(JsonNode node, String field) {
        if (node == null || !node.has(field) || node.get(field).isNull()) {
            return "";
        }
        return node.get(field).asText();
    }

    private String doPublicGet(String url) {
        try {
            HttpGet httpGet = new HttpGet(url);

            return httpClient.execute(httpGet, response -> {
                String body = response.getEntity() != null ? EntityUtils.toString(response.getEntity()) : "";
                if (response.getCode() >= 200 && response.getCode() < 300) {
                    return body;
                } else {
                    log.error("[OKX] GET请求失败: url={}, code={}, body={}", url, response.getCode(), body);
                    return null;
                }
            });
        } catch (Exception e) {
            log.error("[OKX] GET请求异常: url={}", url, e);
        }
        return null;
    }

    private String doPrivatePost(String requestPath, String body) {
        String timestamp = getIsoTimestamp();
        String sign = signRequest(timestamp, "POST", requestPath, body);

        try {
            HttpPost httpPost = new HttpPost(config.getBaseUrl() + requestPath);
            httpPost.setHeader("OK-ACCESS-KEY", config.getApiKey());
            httpPost.setHeader("OK-ACCESS-SIGN", sign);
            httpPost.setHeader("OK-ACCESS-TIMESTAMP", timestamp);
            httpPost.setHeader("OK-ACCESS-PASSPHRASE", config.getPassphrase());
            httpPost.setHeader("Content-Type", "application/json");

            if (config.isSimulated()) {
                httpPost.setHeader("x-simulated-trading", "1");
            }

            httpPost.setEntity(new StringEntity(body, ContentType.APPLICATION_JSON));

            return httpClient.execute(httpPost, response -> {
                if (response.getEntity() != null) {
                    return EntityUtils.toString(response.getEntity());
                }
                return null;
            });
        } catch (Exception e) {
            log.error("[OKX] POST请求异常: path={}", requestPath, e);
        }
        return null;
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
