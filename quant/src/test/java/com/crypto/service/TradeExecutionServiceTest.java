package com.crypto.service;

import com.crypto.config.OrderProperties;
import com.crypto.entity.AiAnalysisEntity;
import com.crypto.entity.OrderEntity;
import com.crypto.entity.PositionEntity;
import com.crypto.enums.*;
import com.crypto.exchange.ExchangeApiClient;
import com.crypto.exchange.ExchangeClientFactory;
import com.crypto.mapper.AiAnalysisMapper;
import com.crypto.mapper.OrderMapper;
import com.crypto.mapper.PositionMapper;
import com.crypto.model.dto.TickDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * TradeExecutionService 交易执行服务测试
 */
@ExtendWith(MockitoExtension.class)
class TradeExecutionServiceTest {

    @Mock
    private ExchangeClientFactory exchangeClientFactory;

    @Mock
    private AiAnalysisService aiAnalysisService;

    @Mock
    private RiskControlService riskControlService;

    @Mock
    private OrderMapper orderMapper;

    @Mock
    private PositionMapper positionMapper;

    @Mock
    private AiAnalysisMapper aiAnalysisMapper;

    @Mock
    private OrderProperties orderProperties;

    @Mock
    private ExchangeApiClient mockClient;

    @InjectMocks
    private TradeExecutionService tradeExecutionService;

    private AiAnalysisEntity buildAnalysis(String action) {
        return AiAnalysisEntity.builder()
                .id(1L)
                .exchange("BINANCE")
                .symbol("BTC/USDT")
                .marketType("FUTURES")
                .suggestedAction(action)
                .confidence(new BigDecimal("85"))
                .positionPct(new BigDecimal("5"))
                .stopLoss(new BigDecimal("48000"))
                .takeProfit(new BigDecimal("55000"))
                .riskLevel("LOW")
                .executed(false)
                .build();
    }

    // ===================== HOLD 操作 =====================

    @Nested
    @DisplayName("HOLD 操作")
    class HoldTest {

        @Test
        @DisplayName("HOLD 建议直接标记已执行，不下单")
        void holdShouldMarkExecutedWithoutOrder() {
            AiAnalysisEntity analysis = buildAnalysis("HOLD");
            when(aiAnalysisMapper.selectById(1L)).thenReturn(analysis);

            OrderEntity result = tradeExecutionService.executeAnalysis(analysis);

            assertNull(result);
            verify(aiAnalysisMapper).updateById(any());
            verify(exchangeClientFactory, never()).getClient(any());
        }
    }

    // ===================== 风控拒绝 =====================

    @Nested
    @DisplayName("风控检查")
    class RiskCheckTest {

        @Test
        @DisplayName("风控未通过 -> 不下单")
        void shouldNotTradeWhenRiskCheckFails() {
            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG");
            when(riskControlService.preTradeCheck(analysis)).thenReturn(false);
            when(aiAnalysisMapper.selectById(1L)).thenReturn(analysis);

            OrderEntity result = tradeExecutionService.executeAnalysis(analysis);

            assertNull(result);
            verify(exchangeClientFactory, never()).getClient(any());
        }
    }

    // ===================== 开仓操作 =====================

    @Nested
    @DisplayName("开仓操作")
    class OpenPositionTest {

        @BeforeEach
        void setUp() {
            when(riskControlService.preTradeCheck(any())).thenReturn(true);
            when(exchangeClientFactory.getClient(any())).thenReturn(mockClient);
        }

        @Test
        @DisplayName("OPEN_LONG - 正常开多")
        void shouldOpenLong() {
            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG");
            when(aiAnalysisMapper.selectById(anyLong())).thenReturn(
                    AiAnalysisEntity.builder().id(1L).executed(false).build());

            TickDTO tick = TickDTO.builder().lastPrice(new BigDecimal("50000")).build();
            when(mockClient.getTicker(anyString(), any())).thenReturn(tick);
            when(mockClient.getBalance("USDT")).thenReturn("10000");
            when(positionMapper.getOpenPosition(anyString(), anyString(), anyString(), eq("LONG")))
                    .thenReturn(null);
            when(mockClient.placeOrder(anyString(), any(), anyString(), anyString(), anyString(), any(), anyString()))
                    .thenReturn("ORD12345");
            when(orderMapper.insert(any())).thenReturn(1);
            when(positionMapper.insert(any())).thenReturn(1);
            when(orderProperties.getMaxPositionPct()).thenReturn(10.0);

            OrderEntity result = tradeExecutionService.executeAnalysis(analysis);

            assertNotNull(result);
            assertEquals("ORD12345", result.getOrderId());
            assertEquals(OrderStatus.SUBMITTED.getCode(), result.getStatus());
            verify(positionMapper).insert(any(PositionEntity.class));
        }

        @Test
        @DisplayName("OPEN_LONG - 已有多头持仓不重复开仓")
        void shouldNotOpenLongWhenAlreadyHasLong() {
            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG");
            when(aiAnalysisMapper.selectById(anyLong())).thenReturn(
                    AiAnalysisEntity.builder().id(1L).executed(false).build());

            TickDTO tick = TickDTO.builder().lastPrice(new BigDecimal("50000")).build();
            when(mockClient.getTicker(anyString(), any())).thenReturn(tick);
            when(positionMapper.getOpenPosition(anyString(), anyString(), anyString(), eq("LONG")))
                    .thenReturn(PositionEntity.builder().entryPrice(new BigDecimal("49000")).build());

            OrderEntity result = tradeExecutionService.executeAnalysis(analysis);

            assertNull(result);
            verify(mockClient, never()).placeOrder(any(), any(), any(), any(), any(), any(), any());
        }

        @Test
        @DisplayName("获取价格失败 -> 不下单")
        void shouldNotTradeWhenPriceFetchFails() {
            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG");
            // tick为null时直接return，不会调用markAnalysisExecuted，所以不需要aiAnalysisMapper stub
            when(mockClient.getTicker(anyString(), any())).thenReturn(null);

            OrderEntity result = tradeExecutionService.executeAnalysis(analysis);

            assertNull(result);
        }

        @Test
        @DisplayName("开仓失败 -> 订单标记为REJECTED")
        void shouldMarkRejectedOnFailure() {
            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG");
            when(aiAnalysisMapper.selectById(anyLong())).thenReturn(
                    AiAnalysisEntity.builder().id(1L).executed(false).build());

            TickDTO tick = TickDTO.builder().lastPrice(new BigDecimal("50000")).build();
            when(mockClient.getTicker(anyString(), any())).thenReturn(tick);
            when(mockClient.getBalance("USDT")).thenReturn("10000");
            when(positionMapper.getOpenPosition(anyString(), anyString(), anyString(), eq("LONG")))
                    .thenReturn(null);
            when(mockClient.placeOrder(anyString(), any(), anyString(), anyString(), anyString(), any(), anyString()))
                    .thenThrow(new RuntimeException("Exchange API error"));
            when(orderMapper.insert(any())).thenReturn(1);
            when(orderProperties.getMaxPositionPct()).thenReturn(10.0);

            OrderEntity result = tradeExecutionService.executeAnalysis(analysis);

            assertNotNull(result);
            assertEquals(OrderStatus.REJECTED.getCode(), result.getStatus());
            assertNotNull(result.getErrorMsg());
        }
    }

    // ===================== 平仓操作 =====================

    @Nested
    @DisplayName("平仓操作")
    class ClosePositionTest {

        @BeforeEach
        void setUp() {
            when(riskControlService.preTradeCheck(any())).thenReturn(true);
            when(exchangeClientFactory.getClient(any())).thenReturn(mockClient);
            when(aiAnalysisMapper.selectById(anyLong())).thenReturn(
                    AiAnalysisEntity.builder().id(1L).executed(false).build());
        }

        @Test
        @DisplayName("CLOSE_LONG - 无持仓不平仓")
        void shouldNotCloseWhenNoPosition() {
            AiAnalysisEntity analysis = buildAnalysis("CLOSE_LONG");

            TickDTO tick = TickDTO.builder().lastPrice(new BigDecimal("50000")).build();
            when(mockClient.getTicker(anyString(), any())).thenReturn(tick);
            when(positionMapper.getOpenPosition(anyString(), anyString(), anyString(), eq("LONG")))
                    .thenReturn(null);

            OrderEntity result = tradeExecutionService.executeAnalysis(analysis);

            assertNull(result);
        }

        @Test
        @DisplayName("CLOSE_LONG - 正常全平多仓")
        void shouldCloseLong() {
            AiAnalysisEntity analysis = buildAnalysis("CLOSE_LONG");

            TickDTO tick = TickDTO.builder().lastPrice(new BigDecimal("52000")).build();
            when(mockClient.getTicker(anyString(), any())).thenReturn(tick);

            PositionEntity position = PositionEntity.builder()
                    .id(1L)
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .marketType("FUTURES")
                    .positionSide("LONG")
                    .entryPrice(new BigDecimal("50000"))
                    .quantity(new BigDecimal("0.1"))
                    .realizedPnl(BigDecimal.ZERO)
                    .status("OPEN")
                    .build();
            when(positionMapper.getOpenPosition(anyString(), anyString(), anyString(), eq("LONG")))
                    .thenReturn(position);
            when(mockClient.placeOrder(anyString(), any(), anyString(), anyString(), anyString(), any(), anyString()))
                    .thenReturn("ORD_CLOSE");
            when(orderMapper.insert(any())).thenReturn(1);

            OrderEntity result = tradeExecutionService.executeAnalysis(analysis);

            assertNotNull(result);
            assertEquals("ORD_CLOSE", result.getOrderId());
            // 盈利 = (52000 - 50000) * 0.1 = 200
            assertNotNull(result.getPnl());
            assertTrue(result.getPnl().compareTo(BigDecimal.ZERO) > 0);

            // 持仓应该被关闭
            verify(positionMapper).updateById(any());
        }

        @Test
        @DisplayName("PARTIAL_CLOSE_LONG - 部分平仓只平一半")
        void shouldPartialCloseLong() {
            AiAnalysisEntity analysis = buildAnalysis("PARTIAL_CLOSE_LONG");

            TickDTO tick = TickDTO.builder().lastPrice(new BigDecimal("52000")).build();
            when(mockClient.getTicker(anyString(), any())).thenReturn(tick);

            PositionEntity position = PositionEntity.builder()
                    .id(1L)
                    .entryPrice(new BigDecimal("50000"))
                    .quantity(new BigDecimal("1.0"))
                    .realizedPnl(BigDecimal.ZERO)
                    .status("OPEN")
                    .build();
            when(positionMapper.getOpenPosition(anyString(), anyString(), anyString(), eq("LONG")))
                    .thenReturn(position);
            when(mockClient.placeOrder(anyString(), any(), anyString(), anyString(), anyString(), any(), anyString()))
                    .thenReturn("ORD_PARTIAL");
            when(orderMapper.insert(any())).thenReturn(1);

            OrderEntity result = tradeExecutionService.executeAnalysis(analysis);

            assertNotNull(result);

            // 验证下单数量应该是一半
            ArgumentCaptor<OrderEntity> orderCaptor = ArgumentCaptor.forClass(OrderEntity.class);
            verify(orderMapper).insert(orderCaptor.capture());
            OrderEntity capturedOrder = orderCaptor.getValue();
            assertEquals(new BigDecimal("0.500000"), capturedOrder.getQuantity());
        }
    }
}
