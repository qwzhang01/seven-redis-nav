package com.crypto.controller;

import com.crypto.entity.AiAnalysisEntity;
import com.crypto.service.AiAnalysisService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.Collections;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * AnalysisController AI分析API测试
 */
@WebMvcTest
@ContextConfiguration(classes = {AnalysisController.class, GlobalExceptionHandler.class})
class AnalysisControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AiAnalysisService aiAnalysisService;

    private AiAnalysisEntity buildMockAnalysis() {
        return AiAnalysisEntity.builder()
                .id(1L)
                .exchange("BINANCE")
                .symbol("BTC/USDT")
                .marketType("FUTURES")
                .trendDirection("BULLISH")
                .confidence(new BigDecimal("85"))
                .suggestedAction("OPEN_LONG")
                .riskLevel("LOW")
                .analysisSummary("看涨信号明确")
                .executed(false)
                .build();
    }

    // ===================== GET /api/analysis/latest =====================

    @Test
    @DisplayName("GET /api/analysis/latest - 获取最新AI分析")
    void shouldReturnLatestAnalysis() throws Exception {
        when(aiAnalysisService.getLatestAnalysis(anyString(), anyString(), anyString()))
                .thenReturn(buildMockAnalysis());

        mockMvc.perform(get("/api/analysis/latest")
                        .param("symbol", "BTC/USDT"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.trendDirection").value("BULLISH"))
                .andExpect(jsonPath("$.data.confidence").value(85))
                .andExpect(jsonPath("$.data.suggestedAction").value("OPEN_LONG"));
    }

    @Test
    @DisplayName("GET /api/analysis/latest - 无分析结果返回null")
    void shouldReturnNullWhenNoAnalysis() throws Exception {
        when(aiAnalysisService.getLatestAnalysis(anyString(), anyString(), anyString()))
                .thenReturn(null);

        mockMvc.perform(get("/api/analysis/latest")
                        .param("symbol", "BTC/USDT"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    // ===================== POST /api/analysis/trigger =====================

    @Test
    @DisplayName("POST /api/analysis/trigger - 触发AI分析成功")
    void shouldTriggerAnalysis() throws Exception {
        when(aiAnalysisService.analyzeSymbol(anyString(), anyString(), anyString()))
                .thenReturn(buildMockAnalysis());

        mockMvc.perform(post("/api/analysis/trigger")
                        .param("symbol", "BTC/USDT"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.suggestedAction").value("OPEN_LONG"));
    }

    @Test
    @DisplayName("POST /api/analysis/trigger - AI分析失败返回错误")
    void shouldReturnErrorWhenAnalysisFails() throws Exception {
        when(aiAnalysisService.analyzeSymbol(anyString(), anyString(), anyString()))
                .thenReturn(null);

        mockMvc.perform(post("/api/analysis/trigger")
                        .param("symbol", "BTC/USDT"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(500))
                .andExpect(jsonPath("$.message").value("AI分析失败"));
    }

    // ===================== GET /api/analysis/unexecuted =====================

    @Test
    @DisplayName("GET /api/analysis/unexecuted - 获取未执行的分析列表")
    void shouldReturnUnexecutedAnalyses() throws Exception {
        AiAnalysisEntity analysis = buildMockAnalysis();
        when(aiAnalysisService.getUnexecutedAnalyses(anyInt()))
                .thenReturn(Arrays.asList(analysis, analysis));

        mockMvc.perform(get("/api/analysis/unexecuted"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.length()").value(2));
    }

    @Test
    @DisplayName("GET /api/analysis/unexecuted - 空列表")
    void shouldReturnEmptyList() throws Exception {
        when(aiAnalysisService.getUnexecutedAnalyses(anyInt()))
                .thenReturn(Collections.emptyList());

        mockMvc.perform(get("/api/analysis/unexecuted"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").isEmpty());
    }
}
