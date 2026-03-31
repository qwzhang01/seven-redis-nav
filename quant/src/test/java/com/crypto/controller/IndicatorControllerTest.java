package com.crypto.controller;

import com.crypto.entity.IndicatorEntity;
import com.crypto.model.dto.IndicatorDTO;
import com.crypto.service.IndicatorService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * IndicatorController 技术指标API测试
 */
@WebMvcTest
@ContextConfiguration(classes = {IndicatorController.class, GlobalExceptionHandler.class})
class IndicatorControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private IndicatorService indicatorService;

    // ===================== GET /api/indicator/latest =====================

    @Test
    @DisplayName("GET /api/indicator/latest - 正常获取最新指标")
    void shouldReturnLatestIndicator() throws Exception {
        IndicatorEntity indicator = IndicatorEntity.builder()
                .exchange("BINANCE")
                .symbol("BTC/USDT")
                .marketType("FUTURES")
                .intervalVal("1h")
                .rsi14(new BigDecimal("55.50"))
                .ma20(new BigDecimal("50000.00"))
                .build();

        when(indicatorService.getLatestIndicator(anyString(), anyString(), anyString(), anyString()))
                .thenReturn(indicator);

        mockMvc.perform(get("/api/indicator/latest")
                        .param("symbol", "BTC/USDT"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.rsi14").value(55.50));
    }

    @Test
    @DisplayName("GET /api/indicator/latest - 没有指标数据返回null data")
    void shouldReturnNullDataWhenNoIndicator() throws Exception {
        when(indicatorService.getLatestIndicator(anyString(), anyString(), anyString(), anyString()))
                .thenReturn(null);

        mockMvc.perform(get("/api/indicator/latest")
                        .param("symbol", "BTC/USDT"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").isEmpty());
    }

    // ===================== POST /api/indicator/calculate =====================

    @Test
    @DisplayName("POST /api/indicator/calculate - 计算成功")
    void shouldCalculateIndicator() throws Exception {
        IndicatorDTO dto = IndicatorDTO.builder()
                .exchange("BINANCE")
                .symbol("BTC/USDT")
                .rsi14(new BigDecimal("60"))
                .build();

        when(indicatorService.calculateAndSave(anyString(), anyString(), anyString(), anyString()))
                .thenReturn(dto);

        mockMvc.perform(post("/api/indicator/calculate")
                        .param("symbol", "BTC/USDT"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.rsi14").value(60));
    }

    @Test
    @DisplayName("POST /api/indicator/calculate - K线不足返回错误")
    void shouldReturnErrorWhenCalculationFails() throws Exception {
        when(indicatorService.calculateAndSave(anyString(), anyString(), anyString(), anyString()))
                .thenReturn(null);

        mockMvc.perform(post("/api/indicator/calculate")
                        .param("symbol", "BTC/USDT"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(500))
                .andExpect(jsonPath("$.message").value("指标计算失败，可能K线数据不足"));
    }

    @Test
    @DisplayName("GET /api/indicator/latest - 缺少symbol参数应400")
    void shouldReturn400WhenMissingSymbol() throws Exception {
        mockMvc.perform(get("/api/indicator/latest"))
                .andExpect(status().isBadRequest());
    }
}
