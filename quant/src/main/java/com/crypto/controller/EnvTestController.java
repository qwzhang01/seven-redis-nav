package com.crypto.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/**
 * .env 文件配置测试控制器
 */
@RestController
@RequestMapping("/api/env")
@Slf4j
public class EnvTestController {

    @Value("${OPENAI_API_KEY:not-found}")
    private String openaiApiKey;

    @Value("${OPENAI_BASE_URL:not-found}")
    private String openaiBaseUrl;

    @Value("${LLM_MODEL:not-found}")
    private String llmModel;

    @Value("${BINANCE_API_KEY:not-found}")
    private String binanceApiKey;

    @Value("${BINANCE_SECRET_KEY:not-found}")
    private String binanceSecretKey;

    @Value("${OKX_API_KEY:not-found}")
    private String okxApiKey;

    @Value("${OKX_SECRET_KEY:not-found}")
    private String okxSecretKey;

    @Value("${OKX_PASSPHRASE:not-found}")
    private String okxPassphrase;

    /**
     * 测试 .env 文件配置读取
     */
    @GetMapping("/test")
    public ResponseEntity<Map<String, Object>> testEnvConfig() {
        Map<String, Object> response = new HashMap<>();
        
        // 检查关键配置是否成功读取
        boolean openaiConfigOk = !openaiApiKey.equals("not-found") && !openaiApiKey.equals("your-openai-api-key");
        boolean binanceConfigOk = !binanceApiKey.equals("not-found") && !binanceApiKey.equals("your-binance-api-key");
        boolean okxConfigOk = !okxApiKey.equals("not-found") && !okxApiKey.equals("your-okx-api-key");

        response.put("status", "success");
        response.put("message", ".env 文件配置测试结果");
        response.put("openai_api_key_configured", openaiConfigOk);
        response.put("binance_api_key_configured", binanceConfigOk);
        response.put("okx_api_key_configured", okxConfigOk);
        
        // 显示配置信息（隐藏敏感信息的部分）
        response.put("openai_base_url", openaiBaseUrl);
        response.put("llm_model", llmModel);
        response.put("openai_api_key_masked", maskApiKey(openaiApiKey));
        response.put("binance_api_key_masked", maskApiKey(binanceApiKey));
        response.put("okx_api_key_masked", maskApiKey(okxApiKey));

        log.info(".env 文件配置测试完成，OpenAI配置: {}, Binance配置: {}, OKX配置: {}", 
                openaiConfigOk, binanceConfigOk, okxConfigOk);

        return ResponseEntity.ok(response);
    }

    /**
     * 显示所有环境变量（用于调试）
     */
    @GetMapping("/all")
    public ResponseEntity<Map<String, Object>> showAllEnvVars() {
        Map<String, Object> response = new HashMap<>();
        
        response.put("OPENAI_API_KEY", maskApiKey(openaiApiKey));
        response.put("OPENAI_BASE_URL", openaiBaseUrl);
        response.put("LLM_MODEL", llmModel);
        response.put("BINANCE_API_KEY", maskApiKey(binanceApiKey));
        response.put("BINANCE_SECRET_KEY", maskApiKey(binanceSecretKey));
        response.put("OKX_API_KEY", maskApiKey(okxApiKey));
        response.put("OKX_SECRET_KEY", maskApiKey(okxSecretKey));
        response.put("OKX_PASSPHRASE", maskApiKey(okxPassphrase));

        return ResponseEntity.ok(response);
    }

    /**
     * 隐藏API密钥的中间部分
     */
    private String maskApiKey(String apiKey) {
        if (apiKey == null || apiKey.equals("not-found") || apiKey.startsWith("your-")) {
            return apiKey;
        }
        
        if (apiKey.length() <= 8) {
            return "***";
        }
        
        return apiKey.substring(0, 4) + "***" + apiKey.substring(apiKey.length() - 4);
    }
}