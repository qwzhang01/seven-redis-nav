package com.crypto.service;

import com.crypto.config.OrderProperties;
import com.crypto.entity.AiAnalysisEntity;
import com.crypto.mapper.OrderMapper;
import com.crypto.mapper.PositionMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.ArrayList;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * RiskControlService 风控服务测试
 */
@ExtendWith(MockitoExtension.class)
class RiskControlServiceTest {

    @Mock
    private OrderProperties orderProperties;

    @Mock
    private PositionMapper positionMapper;

    @Mock
    private OrderMapper orderMapper;

    @InjectMocks
    private RiskControlService riskControlService;

    private AiAnalysisEntity buildAnalysis(String action, BigDecimal confidence,
                                           String riskLevel, BigDecimal positionPct) {
        return AiAnalysisEntity.builder()
                .id(1L)
                .exchange("BINANCE")
                .symbol("BTC/USDT")
                .marketType("FUTURES")
                .suggestedAction(action)
                .confidence(confidence)
                .riskLevel(riskLevel)
                .positionPct(positionPct)
                .build();
    }

    // ===================== 自动交易开关 =====================

    @Nested
    @DisplayName("自动交易开关检查")
    class AutoTradeEnabledTest {

        @Test
        @DisplayName("自动交易未开启 -> 拒绝")
        void shouldRejectWhenAutoTradeDisabled() {
            when(orderProperties.isAutoTradeEnabled()).thenReturn(false);

            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG", new BigDecimal("80"), "LOW", new BigDecimal("5"));
            assertFalse(riskControlService.preTradeCheck(analysis));
        }
    }

    // ===================== 置信度检查 =====================

    @Nested
    @DisplayName("置信度检查")
    class ConfidenceTest {

        @BeforeEach
        void setUp() {
            when(orderProperties.isAutoTradeEnabled()).thenReturn(true);
        }

        @Test
        @DisplayName("开仓操作 - 置信度不足60 -> 拒绝")
        void openActionLowConfidenceShouldReject() {
            // 置信度不足，在step2就返回false，不会到达daily loss check
            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG", new BigDecimal("50"), "LOW", new BigDecimal("5"));
            assertFalse(riskControlService.preTradeCheck(analysis));
        }

        @Test
        @DisplayName("开仓操作 - 置信度恰好60 -> 通过")
        void openActionExact60ShouldPass() {
            when(positionMapper.countOpenPositions()).thenReturn(0);
            when(orderProperties.getMaxPositions()).thenReturn(5);
            when(orderProperties.getMaxPositionPct()).thenReturn(10.0);
            when(orderProperties.getMaxDailyLossPct()).thenReturn(5.0);
            when(orderMapper.selectList(any())).thenReturn(new ArrayList<>());

            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG", new BigDecimal("60"), "LOW", new BigDecimal("5"));
            assertTrue(riskControlService.preTradeCheck(analysis));
        }

        @Test
        @DisplayName("开仓操作 - 置信度为null -> 拒绝")
        void openActionNullConfidenceShouldReject() {
            // 置信度为null，在step2就返回false，不会到达daily loss check
            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG", null, "LOW", new BigDecimal("5"));
            assertFalse(riskControlService.preTradeCheck(analysis));
        }

        @Test
        @DisplayName("平仓操作 - 置信度低也可以通过（不检查置信度）")
        void closeActionLowConfidenceShouldPass() {
            when(orderMapper.selectList(any())).thenReturn(new ArrayList<>());
            when(orderProperties.getMaxDailyLossPct()).thenReturn(5.0);

            AiAnalysisEntity analysis = buildAnalysis("CLOSE_LONG", new BigDecimal("30"), "LOW", null);
            assertTrue(riskControlService.preTradeCheck(analysis));
        }
    }

    // ===================== 持仓数量限制 =====================

    @Nested
    @DisplayName("最大持仓数量检查")
    class MaxPositionTest {

        @BeforeEach
        void setUp() {
            when(orderProperties.isAutoTradeEnabled()).thenReturn(true);
        }

        @Test
        @DisplayName("持仓数已达上限 -> 拒绝开仓")
        void shouldRejectWhenMaxPositionsReached() {
            when(positionMapper.countOpenPositions()).thenReturn(5);
            when(orderProperties.getMaxPositions()).thenReturn(5);
            // 持仓数达上限，在step3就返回false，不会到达daily loss check

            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG", new BigDecimal("80"), "LOW", new BigDecimal("5"));
            assertFalse(riskControlService.preTradeCheck(analysis));
        }

        @Test
        @DisplayName("持仓数未达上限 -> 允许开仓")
        void shouldAllowWhenPositionsBelowMax() {
            when(positionMapper.countOpenPositions()).thenReturn(3);
            when(orderProperties.getMaxPositions()).thenReturn(5);
            when(orderProperties.getMaxPositionPct()).thenReturn(10.0);
            when(orderProperties.getMaxDailyLossPct()).thenReturn(5.0);
            when(orderMapper.selectList(any())).thenReturn(new ArrayList<>());

            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG", new BigDecimal("80"), "LOW", new BigDecimal("5"));
            assertTrue(riskControlService.preTradeCheck(analysis));
        }
    }

    // ===================== 高风险检查 =====================

    @Nested
    @DisplayName("高风险信号检查")
    class HighRiskTest {

        @BeforeEach
        void setUp() {
            when(orderProperties.isAutoTradeEnabled()).thenReturn(true);
        }

        @Test
        @DisplayName("高风险 + 置信度不足80 -> 拒绝开仓")
        void highRiskLowConfidenceShouldReject() {
            when(positionMapper.countOpenPositions()).thenReturn(0);
            when(orderProperties.getMaxPositions()).thenReturn(5);
            when(orderProperties.getMaxDailyLossPct()).thenReturn(5.0);
            when(orderMapper.selectList(any())).thenReturn(new ArrayList<>());

            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG", new BigDecimal("75"), "HIGH", new BigDecimal("5"));
            assertFalse(riskControlService.preTradeCheck(analysis));
        }

        @Test
        @DisplayName("高风险 + 置信度80 -> 允许开仓")
        void highRiskHighConfidenceShouldPass() {
            when(positionMapper.countOpenPositions()).thenReturn(0);
            when(orderProperties.getMaxPositions()).thenReturn(5);
            when(orderProperties.getMaxPositionPct()).thenReturn(10.0);
            when(orderProperties.getMaxDailyLossPct()).thenReturn(5.0);
            when(orderMapper.selectList(any())).thenReturn(new ArrayList<>());

            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG", new BigDecimal("80"), "HIGH", new BigDecimal("5"));
            assertTrue(riskControlService.preTradeCheck(analysis));
        }

        @Test
        @DisplayName("低风险 + 低置信度60 -> 允许开仓（无高风险检查）")
        void lowRiskShouldNotCheckHighRiskThreshold() {
            when(positionMapper.countOpenPositions()).thenReturn(0);
            when(orderProperties.getMaxPositions()).thenReturn(5);
            when(orderProperties.getMaxPositionPct()).thenReturn(10.0);
            when(orderProperties.getMaxDailyLossPct()).thenReturn(5.0);
            when(orderMapper.selectList(any())).thenReturn(new ArrayList<>());

            AiAnalysisEntity analysis = buildAnalysis("OPEN_LONG", new BigDecimal("65"), "LOW", new BigDecimal("5"));
            assertTrue(riskControlService.preTradeCheck(analysis));
        }
    }

    // ===================== HOLD 操作 =====================

    @Nested
    @DisplayName("HOLD 操作")
    class HoldActionTest {

        @Test
        @DisplayName("HOLD 动作不是开仓操作 -> 跳过持仓数/置信度检查")
        void holdShouldPassWithoutOpenChecks() {
            when(orderProperties.isAutoTradeEnabled()).thenReturn(true);
            when(orderProperties.getMaxDailyLossPct()).thenReturn(5.0);
            when(orderMapper.selectList(any())).thenReturn(new ArrayList<>());

            AiAnalysisEntity analysis = buildAnalysis("HOLD", new BigDecimal("30"), "LOW", null);
            assertTrue(riskControlService.preTradeCheck(analysis));
        }
    }

    // ===================== 综合场景 =====================

    @Nested
    @DisplayName("综合场景")
    class IntegrationScenarioTest {

        @Test
        @DisplayName("完整通过 - 自动交易开启 + 高置信度 + 低风险 + 持仓未满")
        void shouldPassFullCheck() {
            when(orderProperties.isAutoTradeEnabled()).thenReturn(true);
            when(positionMapper.countOpenPositions()).thenReturn(2);
            when(orderProperties.getMaxPositions()).thenReturn(5);
            when(orderProperties.getMaxPositionPct()).thenReturn(10.0);
            when(orderProperties.getMaxDailyLossPct()).thenReturn(5.0);
            when(orderMapper.selectList(any())).thenReturn(new ArrayList<>());

            AiAnalysisEntity analysis = buildAnalysis("OPEN_SHORT", new BigDecimal("85"), "MEDIUM", new BigDecimal("8"));
            assertTrue(riskControlService.preTradeCheck(analysis));
        }

        @Test
        @DisplayName("部分平仓 - 不需要持仓数检查")
        void partialCloseShouldNotCheckPositionCount() {
            when(orderProperties.isAutoTradeEnabled()).thenReturn(true);
            when(orderProperties.getMaxDailyLossPct()).thenReturn(5.0);
            when(orderMapper.selectList(any())).thenReturn(new ArrayList<>());

            AiAnalysisEntity analysis = buildAnalysis("PARTIAL_CLOSE_LONG", new BigDecimal("70"), "MEDIUM", null);
            assertTrue(riskControlService.preTradeCheck(analysis));
        }
    }
}
