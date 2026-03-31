package com.crypto.controller;

import com.crypto.config.AiProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/test")
@Slf4j
public class TestController {

    private final AiProperties aiProperties;
    private final WebClient webClient;

    @Autowired
    public TestController(AiProperties aiProperties) {
        this.aiProperties = aiProperties;
        this.webClient = WebClient.builder()
                .baseUrl(aiProperties.getOpenai().getBaseUrl())
                .defaultHeader("Authorization", "Bearer " + aiProperties.getOpenai().getApiKey())
                .defaultHeader("Content-Type", "application/json")
                .build();
    }

    /**
     * 测试大模型连接状态
     */
    @GetMapping("/model/status")
    public ResponseEntity<Map<String, Object>> testModelConnection() {
        Map<String, Object> response = new HashMap<>();
        
        try {
            // 发送一个简单的测试请求到OpenAI
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", aiProperties.getOpenai().getModel());
            
            Map<String, String> messageMap = new HashMap<>();
            messageMap.put("role", "user");
            messageMap.put("content", "Hello, please respond with 'OK' if you can hear me.");
            requestBody.put("messages", new Object[]{messageMap});
            requestBody.put("max_tokens", 10);

            String result = webClient.post()
                    .uri("/v1/chat/completions")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();

            response.put("status", "success");
            response.put("message", "大模型连接正常");
            response.put("model", aiProperties.getOpenai().getModel());
            response.put("baseUrl", aiProperties.getOpenai().getBaseUrl());
            response.put("response", result);
            
            log.info("大模型连接测试成功，模型: {}", aiProperties.getOpenai().getModel());
            
        } catch (Exception e) {
            response.put("status", "error");
            response.put("message", "大模型连接失败: " + e.getMessage());
            response.put("model", aiProperties.getOpenai().getModel());
            response.put("baseUrl", aiProperties.getOpenai().getBaseUrl());
            
            log.error("大模型连接测试失败: {}", e.getMessage());
        }

        return ResponseEntity.ok(response);
    }

    /**
     * 测试大模型对话功能
     */
    @PostMapping("/model/chat")
    public ResponseEntity<Map<String, Object>> testModelChat(@RequestBody Map<String, String> request) {
        String message = request.get("message");
        if (message == null || message.trim().isEmpty()) {
            message = "请介绍一下你自己";
        }

        Map<String, Object> response = new HashMap<>();
        
        try {
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", aiProperties.getOpenai().getModel());
            
            Map<String, String> messageMap = new HashMap<>();
            messageMap.put("role", "user");
            messageMap.put("content", message);
            requestBody.put("messages", new Object[]{messageMap});
            requestBody.put("max_tokens", 200);
            requestBody.put("temperature", 0.7);

            String result = webClient.post()
                    .uri("/v1/chat/completions")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();

            response.put("status", "success");
            response.put("input", message);
            response.put("response", result);
            
            log.info("大模型对话测试成功，输入: {}", message);
            
        } catch (Exception e) {
            response.put("status", "error");
            response.put("message", "大模型对话失败: " + e.getMessage());
            response.put("input", message);
            
            log.error("大模型对话测试失败: {}", e.getMessage());
        }

        return ResponseEntity.ok(response);
    }

    /**
     * 测试量化分析功能
     */
    @PostMapping("/model/analysis")
    public ResponseEntity<Map<String, Object>> testQuantitativeAnalysis(@RequestBody Map<String, Object> request) {
        String symbol = (String) request.get("symbol");
        String analysisType = (String) request.get("analysisType");
        
        if (symbol == null) symbol = "BTC/USDT";
        if (analysisType == null) analysisType = "trend";

        String prompt = String.format("请对%s进行%s分析。\n" +
                "假设当前价格数据如下：\n" +
                "- 当前价格: $45,000\n" +
                "- 24小时涨跌幅: +2.5%%\n" +
                "- 交易量: $25B\n" +
                "- RSI指标: 58\n" +
                "- MACD: 金叉向上\n" +
                "\n" +
                "请给出简要的技术分析和交易建议。", symbol, analysisType);

        Map<String, Object> response = new HashMap<>();
        
        try {
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", aiProperties.getOpenai().getModel());
            
            Map<String, String> messageMap = new HashMap<>();
            messageMap.put("role", "user");
            messageMap.put("content", prompt);
            requestBody.put("messages", new Object[]{messageMap});
            requestBody.put("max_tokens", 300);
            requestBody.put("temperature", 0.3);

            String result = webClient.post()
                    .uri("/v1/chat/completions")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();

            response.put("status", "success");
            response.put("symbol", symbol);
            response.put("analysisType", analysisType);
            response.put("analysisResult", result);
            
            log.info("量化分析测试成功，标的: {}, 分析类型: {}", symbol, analysisType);
            
        } catch (Exception e) {
            response.put("status", "error");
            response.put("message", "量化分析失败: " + e.getMessage());
            response.put("symbol", symbol);
            response.put("analysisType", analysisType);
            
            log.error("量化分析测试失败: {}", e.getMessage());
        }

        return ResponseEntity.ok(response);
    }

    /**
     * 获取大模型配置信息
     */
    @GetMapping("/model/config")
    public ResponseEntity<Map<String, Object>> getModelConfig() {
        Map<String, Object> config = new HashMap<>();
        config.put("provider", aiProperties.getProvider());
        config.put("model", aiProperties.getOpenai().getModel());
        config.put("baseUrl", aiProperties.getOpenai().getBaseUrl());
        config.put("apiKeyConfigured", aiProperties.getOpenai().getApiKey() != null && !aiProperties.getOpenai().getApiKey().equals("your-openai-api-key"));
        config.put("maxTokens", aiProperties.getOpenai().getMaxTokens());
        config.put("temperature", aiProperties.getOpenai().getTemperature());
        
        return ResponseEntity.ok(config);
    }
}
