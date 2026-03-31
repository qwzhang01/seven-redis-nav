package com.crypto.exchange.binance;

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
import lombok.extern.slf4j.Slf4j;
import org.apache.hc.client5.http.classic.methods.HttpDelete;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.apache.hc.core5.http.io.entity.StringEntity;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 币安交易所API客户端 - 完整对接实现
 * 支持现货和合约的K线、Tick、Depth数据
 * 使用 Apache HttpClient 5 + Jackson 实现
 */
@Slf4j
@Component
public class BinanceApiClient implements ExchangeApiClient {

    private final ExchangeProperties.BinanceConfig config;
    private final CloseableHttpClient httpClient;
    private final ObjectMapper objectMapper;

    public BinanceApiClient(ExchangeProperties exchangeProperties, CloseableHttpClient httpClient,
                            ObjectMapper objectMapper) {
        this.config = exchangeProperties.getBinance();
        this.httpClient = httpClient;
        this.objectMapper = objectMapper;
    }

    @Override
    public ExchangeEnum getExchange() {
        return ExchangeEnum.BINANCE;
    }

    // ===================== 行情接口 =====================

    @Override
    public List<KlineDTO> getKlines(String symbol, MarketType marketType, KlineInterval interval,
                                    Long startTime, Long endTime, Integer limit) {
        String convertedSymbol = convertSymbol(symbol, marketType);
        String baseUrl = getBaseUrl(marketType);

        StringBuilder urlBuilder = new StringBuilder(baseUrl)
                .append(marketType == MarketType.SPOT ? "/api/v3/klines" : "/fapi/v1/klines")
                .append("?symbol=").append(convertedSymbol)
                .append("&interval=").append(interval.toBinanceInterval());

        if (startTime != null) {
            urlBuilder.append("&startTime=").append(startTime);
        }
        if (endTime != null) {
            urlBuilder.append("&endTime=").append(endTime);
        }
        if (limit != null) {
            urlBuilder.append("&limit=").append(Math.min(limit, 1500));
        } else {
            urlBuilder.append("&limit=500");
        }

        String responseBody = doGet(urlBuilder.toString());
        if (responseBody == null) {
            return Collections.emptyList();
        }

        try {
            ArrayNode array = (ArrayNode) objectMapper.readTree(responseBody);
            List<KlineDTO> result = new ArrayList<>(array.size());

            for (int i = 0; i < array.size(); i++) {
                ArrayNode item = (ArrayNode) array.get(i);
                result.add(KlineDTO.builder()
                        .exchange(ExchangeEnum.BINANCE.getCode())
                        .symbol(symbol)
                        .marketType(marketType.getCode())
                        .interval(interval.getCode())
                        .openTime(item.get(0).asLong())
                        .openPrice(new BigDecimal(item.get(1).asText()))
                        .highPrice(new BigDecimal(item.get(2).asText()))
                        .lowPrice(new BigDecimal(item.get(3).asText()))
                        .closePrice(new BigDecimal(item.get(4).asText()))
                        .volume(new BigDecimal(item.get(5).asText()))
                        .closeTime(item.get(6).asLong())
                        .quoteVolume(new BigDecimal(item.get(7).asText()))
                        .tradesCount(item.get(8).asInt())
                        .takerBuyVolume(new BigDecimal(item.get(9).asText()))
                        .takerBuyQuoteVolume(new BigDecimal(item.get(10).asText()))
                        .build());
            }

            log.debug("[Binance] 获取K线成功: symbol={}, interval={}, marketType={}, count={}",
                    symbol, interval.getCode(), marketType, result.size());
            return result;
        } catch (Exception e) {
            log.error("[Binance] 解析K线数据异常: symbol={}", symbol, e);
            return Collections.emptyList();
        }
    }

    @Override
    public TickDTO getTicker(String symbol, MarketType marketType) {
        String convertedSymbol = convertSymbol(symbol, marketType);
        String baseUrl = getBaseUrl(marketType);
        String url;

        if (marketType == MarketType.SPOT) {
            url = baseUrl + "/api/v3/ticker/24hr?symbol=" + convertedSymbol;
        } else {
            url = baseUrl + "/fapi/v1/ticker/24hr?symbol=" + convertedSymbol;
        }

        String responseBody = doGet(url);
        if (responseBody == null) {
            return null;
        }

        try {
            JsonNode json = objectMapper.readTree(responseBody);
            return parseTickFromJson(json, symbol, marketType);
        } catch (Exception e) {
            log.error("[Binance] 解析Tick数据异常: symbol={}", symbol, e);
            return null;
        }
    }

    @Override
    public List<TickDTO> getTickers(List<String> symbols, MarketType marketType) {
        String baseUrl = getBaseUrl(marketType);
        String url;

        if (marketType == MarketType.SPOT) {
            String symbolsParam = symbols.stream()
                    .map(s -> "\"" + convertSymbol(s, marketType) + "\"")
                    .collect(Collectors.joining(",", "[", "]"));
            url = baseUrl + "/api/v3/ticker/24hr?symbols=" + symbolsParam;
        } else {
            url = baseUrl + "/fapi/v1/ticker/24hr";
        }

        String responseBody = doGet(url);
        if (responseBody == null) {
            return Collections.emptyList();
        }

        try {
            ArrayNode array = (ArrayNode) objectMapper.readTree(responseBody);
            Set<String> symbolSet = symbols.stream()
                    .map(s -> convertSymbol(s, marketType))
                    .collect(Collectors.toSet());

            Map<String, String> reverseMap = new HashMap<>();
            for (String s : symbols) {
                reverseMap.put(convertSymbol(s, marketType), s);
            }

            List<TickDTO> result = new ArrayList<>();
            for (int i = 0; i < array.size(); i++) {
                JsonNode json = array.get(i);
                String tickSymbol = json.get("symbol").asText();
                if (symbolSet.contains(tickSymbol)) {
                    String originalSymbol = reverseMap.get(tickSymbol);
                    result.add(parseTickFromJson(json, originalSymbol, marketType));
                }
            }
            return result;
        } catch (Exception e) {
            log.error("[Binance] 解析Tickers数据异常", e);
            return Collections.emptyList();
        }
    }

    @Override
    public DepthDTO getDepth(String symbol, MarketType marketType, int limit) {
        String convertedSymbol = convertSymbol(symbol, marketType);
        String baseUrl = getBaseUrl(marketType);
        String url;

        if (marketType == MarketType.SPOT) {
            url = baseUrl + "/api/v3/depth?symbol=" + convertedSymbol + "&limit=" + limit;
        } else {
            url = baseUrl + "/fapi/v1/depth?symbol=" + convertedSymbol + "&limit=" + limit;
        }

        String responseBody = doGet(url);
        if (responseBody == null) {
            return null;
        }

        try {
            JsonNode json = objectMapper.readTree(responseBody);
            return DepthDTO.builder()
                    .exchange(ExchangeEnum.BINANCE.getCode())
                    .symbol(symbol)
                    .marketType(marketType.getCode())
                    .lastUpdateId(json.get("lastUpdateId").asLong())
                    .bids(parseDepthEntries(json.get("bids")))
                    .asks(parseDepthEntries(json.get("asks")))
                    .eventTime(System.currentTimeMillis())
                    .build();
        } catch (Exception e) {
            log.error("[Binance] 解析Depth数据异常: symbol={}", symbol, e);
            return null;
        }
    }

    // ===================== 交易接口 =====================

    @Override
    public String placeOrder(String symbol, MarketType marketType, String side, String positionSide,
                             String orderType, String price, String quantity) {
        String convertedSymbol = convertSymbol(symbol, marketType);
        String baseUrl = getBaseUrl(marketType);
        String endpoint = marketType == MarketType.SPOT ? "/api/v3/order" : "/fapi/v1/order";

        TreeMap<String, String> params = new TreeMap<>();
        params.put("symbol", convertedSymbol);
        params.put("side", side);
        params.put("type", orderType);
        params.put("quantity", quantity);
        params.put("timestamp", String.valueOf(System.currentTimeMillis()));
        params.put("recvWindow", "5000");

        if (marketType == MarketType.FUTURES && positionSide != null) {
            params.put("positionSide", positionSide);
        }

        if ("LIMIT".equals(orderType) && price != null) {
            params.put("price", price);
            params.put("timeInForce", "GTC");
        }

        String queryString = buildQueryString(params);
        String signature = SignatureUtil.hmacSha256(queryString, config.getSecretKey());
        queryString += "&signature=" + signature;

        String url = baseUrl + endpoint;
        String responseBody = doPost(url, queryString);
        if (responseBody == null) {
            throw new RuntimeException("[Binance] 下单失败: " + symbol);
        }

        try {
            JsonNode json = objectMapper.readTree(responseBody);
            if (json.has("orderId")) {
                String orderId = json.get("orderId").asText();
                log.info("[Binance] 下单成功: symbol={}, side={}, type={}, qty={}, orderId={}",
                        symbol, side, orderType, quantity, orderId);
                return orderId;
            } else {
                String msg = json.has("msg") ? json.get("msg").asText() : "unknown error";
                log.error("[Binance] 下单失败: symbol={}, error={}", symbol, msg);
                throw new RuntimeException("[Binance] 下单失败: " + msg);
            }
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            log.error("[Binance] 解析下单响应异常", e);
            throw new RuntimeException("[Binance] 下单响应解析失败", e);
        }
    }

    @Override
    public boolean cancelOrder(String symbol, MarketType marketType, String orderId) {
        String convertedSymbol = convertSymbol(symbol, marketType);
        String baseUrl = getBaseUrl(marketType);
        String endpoint = marketType == MarketType.SPOT ? "/api/v3/order" : "/fapi/v1/order";

        TreeMap<String, String> params = new TreeMap<>();
        params.put("symbol", convertedSymbol);
        params.put("orderId", orderId);
        params.put("timestamp", String.valueOf(System.currentTimeMillis()));

        String queryString = buildQueryString(params);
        String signature = SignatureUtil.hmacSha256(queryString, config.getSecretKey());
        queryString += "&signature=" + signature;

        String url = baseUrl + endpoint + "?" + queryString;
        try {
            HttpDelete httpDelete = new HttpDelete(url);
            httpDelete.setHeader("X-MBX-APIKEY", config.getApiKey());

            return httpClient.execute(httpDelete, response -> {
                int statusCode = response.getCode();
                EntityUtils.consume(response.getEntity());
                return statusCode >= 200 && statusCode < 300;
            });
        } catch (Exception e) {
            log.error("[Binance] 撤单异常: symbol={}, orderId={}", symbol, orderId, e);
            return false;
        }
    }

    @Override
    public String getOrderStatus(String symbol, MarketType marketType, String orderId) {
        String convertedSymbol = convertSymbol(symbol, marketType);
        String baseUrl = getBaseUrl(marketType);
        String endpoint = marketType == MarketType.SPOT ? "/api/v3/order" : "/fapi/v1/order";

        TreeMap<String, String> params = new TreeMap<>();
        params.put("symbol", convertedSymbol);
        params.put("orderId", orderId);
        params.put("timestamp", String.valueOf(System.currentTimeMillis()));

        String queryString = buildQueryString(params);
        String signature = SignatureUtil.hmacSha256(queryString, config.getSecretKey());

        String url = baseUrl + endpoint + "?" + queryString + "&signature=" + signature;

        try {
            HttpGet httpGet = new HttpGet(url);
            httpGet.setHeader("X-MBX-APIKEY", config.getApiKey());

            return httpClient.execute(httpGet, response -> {
                if (response.getCode() >= 200 && response.getCode() < 300 && response.getEntity() != null) {
                    String body = EntityUtils.toString(response.getEntity());
                    JsonNode json = objectMapper.readTree(body);
                    return json.get("status").asText();
                }
                EntityUtils.consume(response.getEntity());
                return null;
            });
        } catch (Exception e) {
            log.error("[Binance] 查询订单状态异常", e);
        }
        return null;
    }

    @Override
    public String getBalance(String asset) {
        String url = config.getBaseUrl() + "/api/v3/account";

        TreeMap<String, String> params = new TreeMap<>();
        params.put("timestamp", String.valueOf(System.currentTimeMillis()));

        String queryString = buildQueryString(params);
        String signature = SignatureUtil.hmacSha256(queryString, config.getSecretKey());

        url += "?" + queryString + "&signature=" + signature;

        try {
            HttpGet httpGet = new HttpGet(url);
            httpGet.setHeader("X-MBX-APIKEY", config.getApiKey());

            return httpClient.execute(httpGet, response -> {
                if (response.getCode() >= 200 && response.getCode() < 300 && response.getEntity() != null) {
                    String body = EntityUtils.toString(response.getEntity());
                    JsonNode json = objectMapper.readTree(body);
                    JsonNode balances = json.get("balances");
                    if (balances != null && balances.isArray()) {
                        for (int i = 0; i < balances.size(); i++) {
                            JsonNode balance = balances.get(i);
                            if (asset.equalsIgnoreCase(balance.get("asset").asText())) {
                                return balance.get("free").asText();
                            }
                        }
                    }
                }
                EntityUtils.consume(response.getEntity());
                return "0";
            });
        } catch (Exception e) {
            log.error("[Binance] 查询余额异常", e);
        }
        return "0";
    }

    // ===================== 工具方法 =====================

    @Override
    public String convertSymbol(String symbol, MarketType marketType) {
        return symbol.replace("/", "");
    }

    private String getBaseUrl(MarketType marketType) {
        return marketType == MarketType.SPOT ? config.getBaseUrl() : config.getFuturesBaseUrl();
    }

    private TickDTO parseTickFromJson(JsonNode json, String symbol, MarketType marketType) {
        return TickDTO.builder()
                .exchange(ExchangeEnum.BINANCE.getCode())
                .symbol(symbol)
                .marketType(marketType.getCode())
                .lastPrice(safeGetBigDecimal(json, "lastPrice"))
                .bestBidPrice(safeGetBigDecimal(json, "bidPrice"))
                .bestBidQty(safeGetBigDecimal(json, "bidQty"))
                .bestAskPrice(safeGetBigDecimal(json, "askPrice"))
                .bestAskQty(safeGetBigDecimal(json, "askQty"))
                .volume24h(safeGetBigDecimal(json, "volume"))
                .quoteVolume24h(safeGetBigDecimal(json, "quoteVolume"))
                .high24h(safeGetBigDecimal(json, "highPrice"))
                .low24h(safeGetBigDecimal(json, "lowPrice"))
                .open24h(safeGetBigDecimal(json, "openPrice"))
                .priceChange(safeGetBigDecimal(json, "priceChange"))
                .priceChangePct(safeGetBigDecimal(json, "priceChangePercent"))
                .eventTime(json.has("closeTime") && !json.get("closeTime").isNull()
                        ? json.get("closeTime").asLong() : System.currentTimeMillis())
                .build();
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

    private BigDecimal safeGetBigDecimal(JsonNode node, String field) {
        if (node == null || !node.has(field) || node.get(field).isNull()) {
            return BigDecimal.ZERO;
        }
        try {
            return new BigDecimal(node.get(field).asText());
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }

    private String buildQueryString(TreeMap<String, String> params) {
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, String> entry : params.entrySet()) {
            if (sb.length() > 0) sb.append("&");
            sb.append(entry.getKey()).append("=").append(entry.getValue());
        }
        return sb.toString();
    }

    private String doGet(String url) {
        try {
            HttpGet httpGet = new HttpGet(url);
            httpGet.setHeader("X-MBX-APIKEY", config.getApiKey());

            return httpClient.execute(httpGet, response -> {
                String body = response.getEntity() != null ? EntityUtils.toString(response.getEntity()) : "";
                if (response.getCode() >= 200 && response.getCode() < 300) {
                    return body;
                } else {
                    log.error("[Binance] GET请求失败: url={}, code={}, body={}", url, response.getCode(), body);
                    return null;
                }
            });
        } catch (Exception e) {
            log.error("[Binance] GET请求异常: url={}", url, e);
        }
        return null;
    }

    private String doPost(String url, String queryString) {
        try {
            HttpPost httpPost = new HttpPost(url);
            httpPost.setHeader("X-MBX-APIKEY", config.getApiKey());
            httpPost.setHeader("Content-Type", "application/x-www-form-urlencoded");
            httpPost.setEntity(new StringEntity(queryString, ContentType.APPLICATION_FORM_URLENCODED));

            return httpClient.execute(httpPost, response -> {
                if (response.getEntity() != null) {
                    return EntityUtils.toString(response.getEntity());
                }
                return null;
            });
        } catch (Exception e) {
            log.error("[Binance] POST请求异常: url={}", url, e);
        }
        return null;
    }
}
