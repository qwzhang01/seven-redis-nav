package com.crypto.service;

import com.crypto.config.AiProperties;
import com.crypto.config.TradingProperties;
import com.crypto.entity.AiAnalysisEntity;
import com.crypto.entity.IndicatorEntity;
import com.crypto.entity.KlineEntity;
import com.crypto.entity.PositionEntity;
import com.crypto.enums.ActionType;
import com.crypto.enums.ExchangeEnum;
import com.crypto.enums.MarketType;
import com.crypto.enums.TrendDirection;
import com.crypto.exchange.ExchangeClientFactory;
import com.crypto.mapper.AiAnalysisMapper;
import com.crypto.mapper.PositionMapper;
import com.crypto.model.dto.AiAnalysisDTO;
import com.crypto.model.dto.TickDTO;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.*;

/**
 * AI分析服务 - 使用Spring AI(WebClient)调用大模型分析投资指标
 *
 * 功能:
 * 1. 汇总多周期技术指标
 * 2. 构建结构化Prompt发送给大模型
 * 3. 解析大模型返回的结构化投资建议
 * 4. 持久化分析结果
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AiAnalysisService {

    private final WebClient webClient;
    private final ObjectMapper objectMapper;
    private final AiProperties aiProperties;
    private final TradingProperties tradingProperties;
    private final IndicatorService indicatorService;
    private final MarketDataService marketDataService;
    private final ExchangeClientFactory exchangeClientFactory;
    private final AiAnalysisMapper aiAnalysisMapper;
    private final PositionMapper positionMapper;

    /**
     * 定时AI分析 (默认每15分钟)
     */
    @Scheduled(fixedDelayString = "#{${ai.analysis.interval-minutes:15} * 60000}", initialDelay = 60000)
    public void scheduleAiAnalysis() {
        if (!aiProperties.getAnalysis().isEnabled()) {
            return;
        }

        log.info("========== 开始AI投资分析 ==========");

        for (ExchangeEnum exchange : exchangeClientFactory.getAllClients().keySet()) {
            for (String symbol : tradingProperties.getSymbols().getFutures()) {
                try {
                    analyzeSymbol(exchange.getCode(), symbol, MarketType.FUTURES.getCode());
                } catch (Exception e) {
                    log.error("AI分析异常: exchange={}, symbol={}", exchange, symbol, e);
                }
            }
        }

        log.info("========== AI投资分析完成 ==========");
    }

    /**
     * 分析指定交易对
     */
    public AiAnalysisEntity analyzeSymbol(String exchange, String symbol, String marketType) {
        // 1. 收集多周期指标数据
        Map<String, IndicatorEntity> indicators = new LinkedHashMap<>();
        for (String interval : aiProperties.getAnalysis().getAnalysisIntervals()) {
            IndicatorEntity indicator = indicatorService.getLatestIndicator(
                    exchange, symbol, marketType, interval);
            if (indicator != null) {
                indicators.put(interval, indicator);
            }
        }

        if (indicators.isEmpty()) {
            log.warn("无可用指标数据: {}/{}/{}", exchange, symbol, marketType);
            return null;
        }

        // 2. 获取最近的K线数据(1h)作为价格参考
        List<KlineEntity> recentKlines = marketDataService.getLatestKlines(
                exchange, symbol, marketType, "1h", 24);

        // 3. 获取当前持仓信息
        PositionEntity longPosition = positionMapper.getOpenPosition(
                exchange, symbol, marketType, "LONG");
        PositionEntity shortPosition = positionMapper.getOpenPosition(
                exchange, symbol, marketType, "SHORT");

        // 4. 构建Prompt
        String prompt = buildAnalysisPrompt(exchange, symbol, marketType,
                indicators, recentKlines, longPosition, shortPosition);

        // 5. 调用大模型
        String aiResponse = callAiModel(prompt);
        if (aiResponse == null) {
            log.error("AI模型调用失败: {}/{}", exchange, symbol);
            return null;
        }

        // 6. 解析AI响应
        AiAnalysisDTO analysisDTO = parseAiResponse(aiResponse);
        if (analysisDTO == null) {
            log.error("AI响应解析失败: {}/{}", exchange, symbol);
            return null;
        }

        // 7. 持久化分析结果
        AiAnalysisEntity entity = saveAnalysis(exchange, symbol, marketType,
                analysisDTO, indicators, aiResponse);

        log.info("AI分析完成: exchange={}, symbol={}, action={}, confidence={}, trend={}",
                exchange, symbol, analysisDTO.getSuggestedAction(),
                analysisDTO.getConfidence(), analysisDTO.getTrendDirection());

        return entity;
    }

    /**
     * 构建AI分析Prompt
     */
    private String buildAnalysisPrompt(String exchange, String symbol, String marketType,
                                       Map<String, IndicatorEntity> indicators,
                                       List<KlineEntity> recentKlines,
                                       PositionEntity longPosition,
                                       PositionEntity shortPosition) {
        StringBuilder sb = new StringBuilder();
        sb.append("你是一个专业的加密货币量化交易分析师。请根据以下技术指标数据，给出专业的投资建议。\n\n");
        sb.append("## 交易对信息\n");
        sb.append("- 交易所: ").append(exchange).append("\n");
        sb.append("- 交易对: ").append(symbol).append("\n");
        sb.append("- 市场类型: ").append(marketType).append("\n");
        sb.append("- 分析时间: ").append(new Date()).append("\n\n");

        if (!recentKlines.isEmpty()) {
            sb.append("## 最近24小时K线数据(1小时)\n");
            sb.append("| 时间 | 开盘 | 最高 | 最低 | 收盘 | 成交量 |\n");
            sb.append("|------|------|------|------|------|--------|\n");
            Collections.reverse(recentKlines);
            for (int i = 0; i < Math.min(recentKlines.size(), 24); i++) {
                KlineEntity k = recentKlines.get(i);
                sb.append(String.format("| %d | %s | %s | %s | %s | %s |\n",
                        k.getOpenTime(), k.getOpenPrice(), k.getHighPrice(),
                        k.getLowPrice(), k.getClosePrice(), k.getVolume()));
            }
            sb.append("\n");
        }

        sb.append("## 多周期技术指标\n\n");
        for (Map.Entry<String, IndicatorEntity> entry : indicators.entrySet()) {
            String interval = entry.getKey();
            IndicatorEntity ind = entry.getValue();

            sb.append("### ").append(interval).append(" 周期指标\n");
            sb.append("**移动平均线:**\n");
            sb.append("- MA5=").append(ind.getMa5()).append(", MA10=").append(ind.getMa10());
            sb.append(", MA20=").append(ind.getMa20()).append(", MA60=").append(ind.getMa60()).append("\n");
            sb.append("- EMA12=").append(ind.getEma12()).append(", EMA26=").append(ind.getEma26()).append("\n\n");

            sb.append("**MACD:**\n");
            sb.append("- DIF=").append(ind.getMacdLine()).append(", DEA=").append(ind.getMacdSignal());
            sb.append(", MACD柱=").append(ind.getMacdHistogram()).append("\n\n");

            sb.append("**RSI:**\n");
            sb.append("- RSI6=").append(ind.getRsi6()).append(", RSI14=").append(ind.getRsi14());
            sb.append(", RSI24=").append(ind.getRsi24()).append("\n\n");

            sb.append("**布林带:**\n");
            sb.append("- Upper=").append(ind.getBollUpper()).append(", Middle=").append(ind.getBollMiddle());
            sb.append(", Lower=").append(ind.getBollLower()).append("\n\n");

            sb.append("**KDJ:**\n");
            sb.append("- K=").append(ind.getKdjK()).append(", D=").append(ind.getKdjD());
            sb.append(", J=").append(ind.getKdjJ()).append("\n\n");

            sb.append("**其他指标:**\n");
            sb.append("- ATR14=").append(ind.getAtr14()).append(", VWAP=").append(ind.getVwap());
            sb.append(", OBV=").append(ind.getObv()).append("\n");

            if (ind.getExtraIndicators() != null) {
                sb.append("- 额外指标: ").append(ind.getExtraIndicators()).append("\n");
            }
            sb.append("\n");
        }

        sb.append("## 当前持仓状态\n");
        if (longPosition != null) {
            sb.append("- 多头持仓: 入场价=").append(longPosition.getEntryPrice());
            sb.append(", 数量=").append(longPosition.getQuantity());
            sb.append(", 未实现盈亏=").append(longPosition.getUnrealizedPnl()).append("\n");
        } else {
            sb.append("- 无多头持仓\n");
        }

        if (shortPosition != null) {
            sb.append("- 空头持仓: 入场价=").append(shortPosition.getEntryPrice());
            sb.append(", 数量=").append(shortPosition.getQuantity());
            sb.append(", 未实现盈亏=").append(shortPosition.getUnrealizedPnl()).append("\n");
        } else {
            sb.append("- 无空头持仓\n");
        }

        sb.append("\n## 请严格按以下JSON格式返回分析结果:\n");
        sb.append("```json\n");
        sb.append("{\n");
        sb.append("  \"trendDirection\": \"BULLISH/BEARISH/NEUTRAL\",\n");
        sb.append("  \"confidence\": 0-100的数字,\n");
        sb.append("  \"suggestedAction\": \"OPEN_LONG/OPEN_SHORT/CLOSE_LONG/CLOSE_SHORT/PARTIAL_CLOSE_LONG/PARTIAL_CLOSE_SHORT/HOLD\",\n");
        sb.append("  \"entryPrice\": 建议入场价格(数字),\n");
        sb.append("  \"stopLoss\": 止损价格(数字),\n");
        sb.append("  \"takeProfit\": 止盈价格(数字),\n");
        sb.append("  \"positionPct\": 建议仓位百分比(1-100的数字),\n");
        sb.append("  \"riskLevel\": \"LOW/MEDIUM/HIGH\",\n");
        sb.append("  \"timeHorizon\": \"SHORT_TERM/MEDIUM_TERM/LONG_TERM\",\n");
        sb.append("  \"analysisSummary\": \"50字以内的分析摘要\",\n");
        sb.append("  \"detailedAnalysis\": \"详细的技术分析说明，包括各指标解读和交易逻辑\"\n");
        sb.append("}\n");
        sb.append("```\n\n");
        sb.append("重要提示:\n");
        sb.append("1. 请综合多个周期的指标进行分析，短周期判断入场时机，长周期判断趋势方向\n");
        sb.append("2. 如果指标信号冲突或不明确，建议HOLD操作，不要强行交易\n");
        sb.append("3. 止损止盈价格要合理，考虑ATR波动范围\n");
        sb.append("4. 如果已有持仓且盈利达到预期，建议部分平仓锁利\n");
        sb.append("5. 只返回JSON，不要返回其他内容\n");

        return sb.toString();
    }

    /**
     * 调用AI大模型 (OpenAI兼容接口) - 使用 Jackson 构建请求体
     */
    private String callAiModel(String prompt) {
        try {
            ObjectNode requestBody = objectMapper.createObjectNode();
            requestBody.put("model", aiProperties.getOpenai().getModel());
            requestBody.put("temperature", aiProperties.getOpenai().getTemperature());
            requestBody.put("max_tokens", aiProperties.getOpenai().getMaxTokens());

            ArrayNode messages = objectMapper.createArrayNode();

            ObjectNode systemMsg = objectMapper.createObjectNode();
            systemMsg.put("role", "system");
            systemMsg.put("content", "你是一个专业的加密货币量化交易分析师，擅长技术指标分析。请严格按要求的JSON格式返回分析结果。");
            messages.add(systemMsg);

            ObjectNode userMsg = objectMapper.createObjectNode();
            userMsg.put("role", "user");
            userMsg.put("content", prompt);
            messages.add(userMsg);

            requestBody.set("messages", messages);

            String requestJson = objectMapper.writeValueAsString(requestBody);

            String response = webClient.post()
                    .uri("/v1/chat/completions")
                    .bodyValue(requestJson)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(60))
                    .onErrorResume(e -> {
                        log.error("AI模型调用失败", e);
                        return Mono.empty();
                    })
                    .block();

            if (response != null) {
                JsonNode respJson = objectMapper.readTree(response);
                JsonNode choices = respJson.get("choices");
                if (choices != null && choices.isArray() && choices.size() > 0) {
                    JsonNode choice = choices.get(0);
                    return choice.get("message").get("content").asText();
                }
            }

        } catch (Exception e) {
            log.error("AI模型调用异常", e);
        }
        return null;
    }

    /**
     * 解析AI模型返回的JSON结果 - 使用 Jackson 解析
     */
    private AiAnalysisDTO parseAiResponse(String response) {
        try {
            String json = response;
            if (json.contains("```json")) {
                json = json.substring(json.indexOf("```json") + 7);
                json = json.substring(0, json.indexOf("```"));
            } else if (json.contains("```")) {
                json = json.substring(json.indexOf("```") + 3);
                json = json.substring(0, json.indexOf("```"));
            }
            json = json.trim();

            JsonNode obj = objectMapper.readTree(json);

            return AiAnalysisDTO.builder()
                    .trendDirection(TrendDirection.fromCode(getTextSafe(obj, "trendDirection")))
                    .confidence(safeGetBigDecimal(obj, "confidence"))
                    .suggestedAction(ActionType.fromCode(getTextSafe(obj, "suggestedAction")))
                    .entryPrice(safeGetBigDecimal(obj, "entryPrice"))
                    .stopLoss(safeGetBigDecimal(obj, "stopLoss"))
                    .takeProfit(safeGetBigDecimal(obj, "takeProfit"))
                    .positionPct(safeGetBigDecimal(obj, "positionPct"))
                    .riskLevel(getTextSafe(obj, "riskLevel"))
                    .timeHorizon(getTextSafe(obj, "timeHorizon"))
                    .analysisSummary(getTextSafe(obj, "analysisSummary"))
                    .detailedAnalysis(getTextSafe(obj, "detailedAnalysis"))
                    .build();

        } catch (Exception e) {
            log.error("解析AI响应失败: response={}", response, e);
            return null;
        }
    }

    /**
     * 持久化AI分析结果
     */
    private AiAnalysisEntity saveAnalysis(String exchange, String symbol, String marketType,
                                          AiAnalysisDTO dto, Map<String, IndicatorEntity> indicators,
                                          String rawResponse) {
        String signalType;
        switch (dto.getSuggestedAction()) {
            case OPEN_LONG:
                signalType = "BUY";
                break;
            case OPEN_SHORT:
            case CLOSE_LONG:
                signalType = "SELL";
                break;
            default:
                signalType = "HOLD";
        }

        String indicatorsUsed;
        try {
            indicatorsUsed = objectMapper.writeValueAsString(indicators.keySet());
        } catch (Exception e) {
            indicatorsUsed = indicators.keySet().toString();
        }

        AiAnalysisEntity entity = AiAnalysisEntity.builder()
                .exchange(exchange)
                .symbol(symbol)
                .marketType(marketType)
                .analysisTime(System.currentTimeMillis())
                .trendDirection(dto.getTrendDirection().getCode())
                .confidence(dto.getConfidence())
                .signalType(signalType)
                .suggestedAction(dto.getSuggestedAction().getCode())
                .entryPrice(dto.getEntryPrice())
                .stopLoss(dto.getStopLoss())
                .takeProfit(dto.getTakeProfit())
                .positionPct(dto.getPositionPct())
                .riskLevel(dto.getRiskLevel())
                .timeHorizon(dto.getTimeHorizon())
                .analysisSummary(dto.getAnalysisSummary())
                .detailedAnalysis(dto.getDetailedAnalysis())
                .indicatorsUsed(indicatorsUsed)
                .modelName(aiProperties.getOpenai().getModel())
                .rawResponse(rawResponse)
                .executed(false)
                .build();

        aiAnalysisMapper.insert(entity);
        return entity;
    }

    private String getTextSafe(JsonNode node, String field) {
        if (node == null || !node.has(field) || node.get(field).isNull()) {
            return "";
        }
        return node.get(field).asText();
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

    /**
     * 获取最新分析
     */
    public AiAnalysisEntity getLatestAnalysis(String exchange, String symbol, String marketType) {
        return aiAnalysisMapper.getLatestAnalysis(exchange, symbol, marketType);
    }

    /**
     * 获取未执行的分析
     */
    public List<AiAnalysisEntity> getUnexecutedAnalyses(int limit) {
        return aiAnalysisMapper.getUnexecutedAnalyses(limit);
    }
}
