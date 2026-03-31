package com.crypto.controller;

import com.crypto.entity.AiAnalysisEntity;
import com.crypto.entity.OrderEntity;
import com.crypto.entity.PositionEntity;
import com.crypto.mapper.AiAnalysisMapper;
import com.crypto.mapper.OrderMapper;
import com.crypto.mapper.PositionMapper;
import com.crypto.service.TradeExecutionService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
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
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * TradeController 交易API测试
 */
@WebMvcTest
@ContextConfiguration(classes = {TradeController.class, GlobalExceptionHandler.class})
class TradeControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private TradeExecutionService tradeExecutionService;

    @MockBean
    private OrderMapper orderMapper;

    @MockBean
    private PositionMapper positionMapper;

    @MockBean
    private AiAnalysisMapper aiAnalysisMapper;

    // ===================== POST /api/trade/execute/{analysisId} =====================

    @Nested
    @DisplayName("POST /api/trade/execute/{analysisId}")
    class ExecuteAnalysisTest {

        @Test
        @DisplayName("正常执行AI建议")
        void shouldExecuteAnalysis() throws Exception {
            AiAnalysisEntity analysis = AiAnalysisEntity.builder()
                    .id(1L)
                    .executed(false)
                    .build();
            OrderEntity order = OrderEntity.builder()
                    .id(100L)
                    .orderId("ORD001")
                    .status("SUBMITTED")
                    .build();

            when(aiAnalysisMapper.selectById(1L)).thenReturn(analysis);
            when(tradeExecutionService.executeAnalysis(any())).thenReturn(order);

            mockMvc.perform(post("/api/trade/execute/1"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data.orderId").value("ORD001"));
        }

        @Test
        @DisplayName("分析记录不存在")
        void shouldReturn404WhenNotFound() throws Exception {
            when(aiAnalysisMapper.selectById(999L)).thenReturn(null);

            mockMvc.perform(post("/api/trade/execute/999"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(500))
                    .andExpect(jsonPath("$.message").value("未找到分析记录: 999"));
        }

        @Test
        @DisplayName("分析已执行")
        void shouldReturnErrorWhenAlreadyExecuted() throws Exception {
            AiAnalysisEntity analysis = AiAnalysisEntity.builder()
                    .id(1L)
                    .executed(true)
                    .build();
            when(aiAnalysisMapper.selectById(1L)).thenReturn(analysis);

            mockMvc.perform(post("/api/trade/execute/1"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(500))
                    .andExpect(jsonPath("$.message").value("该分析已执行"));
        }
    }

    // ===================== GET /api/trade/orders =====================

    @Nested
    @DisplayName("GET /api/trade/orders")
    class GetOrdersTest {

        @Test
        @DisplayName("查询订单列表")
        void shouldReturnOrders() throws Exception {
            OrderEntity order = OrderEntity.builder()
                    .id(1L)
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .status("FILLED")
                    .build();
            when(orderMapper.selectList(any())).thenReturn(Collections.singletonList(order));

            mockMvc.perform(get("/api/trade/orders")
                            .param("exchange", "BINANCE")
                            .param("status", "FILLED"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data").isArray());
        }

        @Test
        @DisplayName("无参数查询返回所有订单")
        void shouldReturnAllOrdersWithoutFilter() throws Exception {
            when(orderMapper.selectList(any())).thenReturn(Collections.emptyList());

            mockMvc.perform(get("/api/trade/orders"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200));
        }
    }

    // ===================== GET /api/trade/positions =====================

    @Nested
    @DisplayName("GET /api/trade/positions")
    class GetPositionsTest {

        @Test
        @DisplayName("查询持仓列表")
        void shouldReturnPositions() throws Exception {
            PositionEntity position = PositionEntity.builder()
                    .id(1L)
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .status("OPEN")
                    .entryPrice(new BigDecimal("50000"))
                    .build();
            when(positionMapper.selectList(any())).thenReturn(Collections.singletonList(position));

            mockMvc.perform(get("/api/trade/positions")
                            .param("status", "OPEN"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data").isArray());
        }
    }

    // ===================== GET /api/trade/positions/open =====================

    @Nested
    @DisplayName("GET /api/trade/positions/open")
    class GetOpenPositionsTest {

        @Test
        @DisplayName("获取所有开仓持仓")
        void shouldReturnOpenPositions() throws Exception {
            when(positionMapper.getAllOpenPositions()).thenReturn(Collections.emptyList());

            mockMvc.perform(get("/api/trade/positions/open"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.code").value(200))
                    .andExpect(jsonPath("$.data").isArray());
        }
    }
}
