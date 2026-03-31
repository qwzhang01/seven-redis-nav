package com.crypto.controller;

import com.crypto.entity.AiAnalysisEntity;
import com.crypto.model.vo.ApiResult;
import com.crypto.service.AiAnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * AI分析API
 */
@RestController
@RequestMapping("/api/analysis")
@RequiredArgsConstructor
public class AnalysisController {

    private final AiAnalysisService aiAnalysisService;

    /**
     * 获取最新AI分析
     */
    @GetMapping("/latest")
    public ApiResult<AiAnalysisEntity> getLatestAnalysis(
            @RequestParam(defaultValue = "BINANCE") String exchange,
            @RequestParam String symbol,
            @RequestParam(defaultValue = "FUTURES") String marketType) {

        AiAnalysisEntity analysis = aiAnalysisService.getLatestAnalysis(
                exchange, symbol, marketType);
        return ApiResult.success(analysis);
    }

    /**
     * 手动触发AI分析
     */
    @PostMapping("/trigger")
    public ApiResult<AiAnalysisEntity> triggerAnalysis(
            @RequestParam(defaultValue = "BINANCE") String exchange,
            @RequestParam String symbol,
            @RequestParam(defaultValue = "FUTURES") String marketType) {

        AiAnalysisEntity result = aiAnalysisService.analyzeSymbol(exchange, symbol, marketType);
        if (result != null) {
            return ApiResult.success(result);
        }
        return ApiResult.error("AI分析失败");
    }

    /**
     * 获取未执行的AI建议
     */
    @GetMapping("/unexecuted")
    public ApiResult<List<AiAnalysisEntity>> getUnexecutedAnalyses(
            @RequestParam(defaultValue = "20") int limit) {
        return ApiResult.success(aiAnalysisService.getUnexecutedAnalyses(limit));
    }
}
