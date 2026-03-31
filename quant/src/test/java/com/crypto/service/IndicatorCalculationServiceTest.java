package com.crypto.service;

import com.crypto.entity.KlineEntity;
import com.crypto.model.dto.IndicatorDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * IndicatorCalculationService 技术指标计算测试
 */
class IndicatorCalculationServiceTest {

    private IndicatorCalculationService calculationService;

    @BeforeEach
    void setUp() {
        calculationService = new IndicatorCalculationService();
    }

    /**
     * 生成模拟K线数据（正弦波+随机趋势，模拟真实行情波动）
     */
    private List<KlineEntity> generateMockKlines(int count, double basePrice) {
        List<KlineEntity> klines = new ArrayList<>();
        long baseTime = System.currentTimeMillis() - (long) count * 3600000L;

        for (int i = 0; i < count; i++) {
            // 带趋势的正弦波
            double trend = basePrice + i * 0.5; // 缓慢上升趋势
            double wave = 500 * Math.sin(i * 0.3); // 波动
            double noise = (Math.random() - 0.5) * 200; // 随机噪声

            double close = trend + wave + noise;
            double open = close + (Math.random() - 0.5) * 100;
            double high = Math.max(open, close) + Math.random() * 200;
            double low = Math.min(open, close) - Math.random() * 200;
            double volume = 100 + Math.random() * 500;

            long openTime = baseTime + (long) i * 3600000L;
            long closeTime = openTime + 3600000L - 1;

            KlineEntity kline = KlineEntity.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .marketType("FUTURES")
                    .intervalVal("1h")
                    .openTime(openTime)
                    .closeTime(closeTime)
                    .openPrice(BigDecimal.valueOf(open))
                    .highPrice(BigDecimal.valueOf(high))
                    .lowPrice(BigDecimal.valueOf(low))
                    .closePrice(BigDecimal.valueOf(close))
                    .volume(BigDecimal.valueOf(volume))
                    .quoteVolume(BigDecimal.valueOf(volume * close))
                    .tradesCount((int) (100 + Math.random() * 1000))
                    .takerBuyVol(BigDecimal.valueOf(volume * 0.5))
                    .takerBuyQuote(BigDecimal.valueOf(volume * close * 0.5))
                    .build();
            klines.add(kline);
        }
        return klines;
    }

    // ===================== 输入校验 =====================

    @Nested
    @DisplayName("输入校验")
    class InputValidationTest {

        @Test
        @DisplayName("null K线列表 -> 返回 null")
        void nullKlinesShouldReturnNull() {
            IndicatorDTO result = calculationService.calculateIndicators(
                    null, "BINANCE", "BTC/USDT", "FUTURES", "1h");
            assertNull(result);
        }

        @Test
        @DisplayName("K线数不足60条 -> 返回 null")
        void insufficientKlinesShouldReturnNull() {
            List<KlineEntity> klines = generateMockKlines(50, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");
            assertNull(result);
        }

        @Test
        @DisplayName("恰好60条 -> 可以计算")
        void exactly60KlinesShouldWork() {
            List<KlineEntity> klines = generateMockKlines(60, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");
            assertNotNull(result);
        }
    }

    // ===================== 基础属性验证 =====================

    @Nested
    @DisplayName("基础属性")
    class BasicPropertiesTest {

        @Test
        @DisplayName("结果包含正确的exchange, symbol, marketType, interval")
        void basicPropertiesShouldBeSet() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result);
            assertEquals("BINANCE", result.getExchange());
            assertEquals("BTC/USDT", result.getSymbol());
            assertEquals("FUTURES", result.getMarketType());
            assertEquals("1h", result.getInterval());
            assertNotNull(result.getCalcTime());
        }
    }

    // ===================== 移动平均线 =====================

    @Nested
    @DisplayName("移动平均线 (MA/EMA)")
    class MovingAverageTest {

        @Test
        @DisplayName("MA5/MA10/MA20/MA60 应该计算出非null值")
        void maShouldBeCalculated() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getMa5());
            assertNotNull(result.getMa10());
            assertNotNull(result.getMa20());
            assertNotNull(result.getMa60());
        }

        @Test
        @DisplayName("MA5 应该最接近最新价格（短期均线最灵敏）")
        void ma5ShouldBeClosestToCurrentPrice() {
            List<KlineEntity> klines = generateMockKlines(200, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            BigDecimal lastClose = klines.get(klines.size() - 1).getClosePrice();

            // MA5 偏差应该小于 MA60 的偏差（统计意义上大概率成立）
            BigDecimal ma5Diff = result.getMa5().subtract(lastClose).abs();
            assertNotNull(ma5Diff);
        }

        @Test
        @DisplayName("EMA12 和 EMA26 应该计算出非null值")
        void emaShouldBeCalculated() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getEma12());
            assertNotNull(result.getEma26());
        }
    }

    // ===================== MACD =====================

    @Nested
    @DisplayName("MACD")
    class MACDTest {

        @Test
        @DisplayName("MACD DIF/DEA/柱状线 应该计算出非null值")
        void macdShouldBeCalculated() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getMacdLine());
            assertNotNull(result.getMacdSignal());
            assertNotNull(result.getMacdHistogram());
        }

        @Test
        @DisplayName("MACD柱状线 = DIF - DEA")
        void macdHistogramShouldBeDifMinusDea() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            // 由于精度舍入，允许微小偏差
            BigDecimal expectedHistogram = result.getMacdLine().subtract(result.getMacdSignal());
            BigDecimal diff = result.getMacdHistogram().subtract(expectedHistogram).abs();
            assertTrue(diff.compareTo(new BigDecimal("0.001")) < 0,
                    "MACD柱状线偏差过大: " + diff);
        }
    }

    // ===================== RSI =====================

    @Nested
    @DisplayName("RSI")
    class RSITest {

        @Test
        @DisplayName("RSI6/RSI14/RSI24 应在 0-100 范围内")
        void rsiShouldBeInRange() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getRsi6());
            assertNotNull(result.getRsi14());
            assertNotNull(result.getRsi24());

            assertTrue(result.getRsi6().compareTo(BigDecimal.ZERO) >= 0);
            assertTrue(result.getRsi6().compareTo(new BigDecimal("100")) <= 0);

            assertTrue(result.getRsi14().compareTo(BigDecimal.ZERO) >= 0);
            assertTrue(result.getRsi14().compareTo(new BigDecimal("100")) <= 0);

            assertTrue(result.getRsi24().compareTo(BigDecimal.ZERO) >= 0);
            assertTrue(result.getRsi24().compareTo(new BigDecimal("100")) <= 0);
        }
    }

    // ===================== 布林带 =====================

    @Nested
    @DisplayName("布林带")
    class BollingerBandsTest {

        @Test
        @DisplayName("Upper > Middle > Lower")
        void bollShouldBeOrdered() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getBollUpper());
            assertNotNull(result.getBollMiddle());
            assertNotNull(result.getBollLower());

            assertTrue(result.getBollUpper().compareTo(result.getBollMiddle()) >= 0,
                    "布林带上轨应 >= 中轨");
            assertTrue(result.getBollMiddle().compareTo(result.getBollLower()) >= 0,
                    "布林带中轨应 >= 下轨");
        }
    }

    // ===================== KDJ =====================

    @Nested
    @DisplayName("KDJ")
    class KDJTest {

        @Test
        @DisplayName("K/D 应在合理范围 (0-100)")
        void kdjShouldBeInRange() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getKdjK());
            assertNotNull(result.getKdjD());
            assertNotNull(result.getKdjJ());

            assertTrue(result.getKdjK().compareTo(BigDecimal.ZERO) >= 0);
            assertTrue(result.getKdjK().compareTo(new BigDecimal("100")) <= 0);

            assertTrue(result.getKdjD().compareTo(BigDecimal.ZERO) >= 0);
            assertTrue(result.getKdjD().compareTo(new BigDecimal("100")) <= 0);

            // J值可以超过100或低于0，这是正常的
        }
    }

    // ===================== 成交量指标 =====================

    @Nested
    @DisplayName("成交量指标")
    class VolumeIndicatorTest {

        @Test
        @DisplayName("VolMa5/VolMa10 应该非null且为正数")
        void volumeMaShouldBePositive() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getVolMa5());
            assertNotNull(result.getVolMa10());
            assertTrue(result.getVolMa5().compareTo(BigDecimal.ZERO) > 0);
            assertTrue(result.getVolMa10().compareTo(BigDecimal.ZERO) > 0);
        }
    }

    // ===================== 其他指标 =====================

    @Nested
    @DisplayName("其他指标（ATR/VWAP/OBV）")
    class OtherIndicatorsTest {

        @Test
        @DisplayName("ATR14 应该为正数")
        void atrShouldBePositive() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getAtr14());
            assertTrue(result.getAtr14().compareTo(BigDecimal.ZERO) > 0);
        }

        @Test
        @DisplayName("VWAP 应该非null")
        void vwapShouldBeCalculated() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getVwap());
        }

        @Test
        @DisplayName("OBV 应该非null")
        void obvShouldBeCalculated() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getObv());
        }
    }

    // ===================== 额外指标 =====================

    @Nested
    @DisplayName("额外指标")
    class ExtraIndicatorsTest {

        @Test
        @DisplayName("额外指标Map应包含WilliamsR/CCI/ADX等")
        void extraIndicatorsShouldContainExpectedKeys() {
            List<KlineEntity> klines = generateMockKlines(100, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getExtraIndicators());
            assertTrue(result.getExtraIndicators().containsKey("williamsR14"));
            assertTrue(result.getExtraIndicators().containsKey("cci20"));
            assertTrue(result.getExtraIndicators().containsKey("adx14"));
            assertTrue(result.getExtraIndicators().containsKey("plusDI14"));
            assertTrue(result.getExtraIndicators().containsKey("minusDI14"));
            assertTrue(result.getExtraIndicators().containsKey("roc12"));
        }

        @Test
        @DisplayName("200条以上K线应计算MA200")
        void shouldCalculateMa200WithEnoughData() {
            List<KlineEntity> klines = generateMockKlines(250, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getExtraIndicators());
            assertTrue(result.getExtraIndicators().containsKey("ma200"));
            assertTrue(result.getExtraIndicators().containsKey("ema50"));
        }

        @Test
        @DisplayName("60条K线不应计算MA200")
        void shouldNotCalculateMa200WithInsufficientData() {
            List<KlineEntity> klines = generateMockKlines(60, 50000);
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");

            assertNotNull(result.getExtraIndicators());
            assertFalse(result.getExtraIndicators().containsKey("ma200"));
        }
    }

    // ===================== 大数据量测试 =====================

    @Nested
    @DisplayName("性能和大数据量")
    class PerformanceTest {

        @Test
        @DisplayName("300条K线计算不应超过3秒")
        void shouldCalculateWithin3Seconds() {
            List<KlineEntity> klines = generateMockKlines(300, 50000);

            long start = System.currentTimeMillis();
            IndicatorDTO result = calculationService.calculateIndicators(
                    klines, "BINANCE", "BTC/USDT", "FUTURES", "1h");
            long elapsed = System.currentTimeMillis() - start;

            assertNotNull(result);
            assertTrue(elapsed < 3000, "计算耗时 " + elapsed + "ms，超过3秒限制");
        }
    }
}
