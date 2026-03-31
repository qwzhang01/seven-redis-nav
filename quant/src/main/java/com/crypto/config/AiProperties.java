package com.crypto.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.List;

/**
 * AI配置属性
 */
@Data
@Component
@ConfigurationProperties(prefix = "ai")
public class AiProperties {

    private String provider = "openai";
    private OpenAiConfig openai = new OpenAiConfig();
    private AnalysisConfig analysis = new AnalysisConfig();

    @Data
    public static class OpenAiConfig {
        private String apiKey;
        private String baseUrl = "https://api.openai.com";
        private String model = "gpt-4";
        private int maxTokens = 4096;
        private double temperature = 0.3;
    }

    @Data
    public static class AnalysisConfig {
        private boolean enabled = true;
        private int intervalMinutes = 15;
        private List<String> analysisIntervals = Arrays.asList("15m", "1h", "4h");
    }
}
