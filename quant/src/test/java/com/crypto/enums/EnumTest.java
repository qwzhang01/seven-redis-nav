package com.crypto.enums;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 枚举类综合测试
 */
class EnumTest {

    // ===================== ActionType =====================

    @Nested
    @DisplayName("ActionType 测试")
    class ActionTypeTest {

        @Test
        @DisplayName("所有枚举值应存在")
        void allValuesShouldExist() {
            assertEquals(7, ActionType.values().length);
            assertNotNull(ActionType.OPEN_LONG);
            assertNotNull(ActionType.OPEN_SHORT);
            assertNotNull(ActionType.CLOSE_LONG);
            assertNotNull(ActionType.CLOSE_SHORT);
            assertNotNull(ActionType.PARTIAL_CLOSE_LONG);
            assertNotNull(ActionType.PARTIAL_CLOSE_SHORT);
            assertNotNull(ActionType.HOLD);
        }

        @ParameterizedTest
        @CsvSource({
                "OPEN_LONG, OPEN_LONG",
                "OPEN_SHORT, OPEN_SHORT",
                "CLOSE_LONG, CLOSE_LONG",
                "CLOSE_SHORT, CLOSE_SHORT",
                "HOLD, HOLD"
        })
        @DisplayName("fromCode 正常转换")
        void fromCodeShouldWork(String code, String expected) {
            assertEquals(ActionType.valueOf(expected), ActionType.fromCode(code));
        }

        @Test
        @DisplayName("fromCode 忽略大小写")
        void fromCodeShouldBeCaseInsensitive() {
            assertEquals(ActionType.OPEN_LONG, ActionType.fromCode("open_long"));
            assertEquals(ActionType.OPEN_SHORT, ActionType.fromCode("Open_Short"));
        }

        @Test
        @DisplayName("fromCode 未知值返回 HOLD")
        void fromCodeUnknownShouldReturnHold() {
            assertEquals(ActionType.HOLD, ActionType.fromCode("UNKNOWN"));
            assertEquals(ActionType.HOLD, ActionType.fromCode(""));
            assertEquals(ActionType.HOLD, ActionType.fromCode("xyz"));
        }

        @Test
        @DisplayName("code 和 name 属性正确")
        void codeAndNameShouldBeCorrect() {
            assertEquals("OPEN_LONG", ActionType.OPEN_LONG.getCode());
            assertEquals("开多", ActionType.OPEN_LONG.getName());
            assertEquals("HOLD", ActionType.HOLD.getCode());
            assertEquals("持有不操作", ActionType.HOLD.getName());
        }
    }

    // ===================== ExchangeEnum =====================

    @Nested
    @DisplayName("ExchangeEnum 测试")
    class ExchangeEnumTest {

        @Test
        @DisplayName("包含 BINANCE 和 OKX")
        void shouldContainAllExchanges() {
            assertEquals(2, ExchangeEnum.values().length);
            assertEquals("BINANCE", ExchangeEnum.BINANCE.getCode());
            assertEquals("币安", ExchangeEnum.BINANCE.getName());
            assertEquals("OKX", ExchangeEnum.OKX.getCode());
            assertEquals("欧易", ExchangeEnum.OKX.getName());
        }

        @Test
        @DisplayName("fromCode 正常转换")
        void fromCodeShouldWork() {
            assertEquals(ExchangeEnum.BINANCE, ExchangeEnum.fromCode("BINANCE"));
            assertEquals(ExchangeEnum.OKX, ExchangeEnum.fromCode("OKX"));
        }

        @Test
        @DisplayName("fromCode 忽略大小写")
        void fromCodeCaseInsensitive() {
            assertEquals(ExchangeEnum.BINANCE, ExchangeEnum.fromCode("binance"));
            assertEquals(ExchangeEnum.OKX, ExchangeEnum.fromCode("okx"));
        }

        @Test
        @DisplayName("fromCode 未知值应抛出异常")
        void fromCodeUnknownShouldThrow() {
            assertThrows(IllegalArgumentException.class, () -> ExchangeEnum.fromCode("HUOBI"));
            assertThrows(IllegalArgumentException.class, () -> ExchangeEnum.fromCode(""));
        }
    }

    // ===================== KlineInterval =====================

    @Nested
    @DisplayName("KlineInterval 测试")
    class KlineIntervalTest {

        @Test
        @DisplayName("所有周期值应存在")
        void allIntervalsShouldExist() {
            assertEquals(13, KlineInterval.values().length);
        }

        @ParameterizedTest
        @CsvSource({
                "1m, M1, 60000",
                "5m, M5, 300000",
                "15m, M15, 900000",
                "1h, H1, 3600000",
                "4h, H4, 14400000",
                "1d, D1, 86400000",
                "1w, W1, 604800000"
        })
        @DisplayName("code、name 和 milliseconds 属性正确")
        void propertiesShouldBeCorrect(String code, String enumName, long millis) {
            KlineInterval interval = KlineInterval.fromCode(code);
            assertEquals(code, interval.getCode());
            assertEquals(millis, interval.getMilliseconds());
        }

        @Test
        @DisplayName("fromCode 未知值应抛出异常")
        void fromCodeUnknownShouldThrow() {
            assertThrows(IllegalArgumentException.class, () -> KlineInterval.fromCode("2m"));
            assertThrows(IllegalArgumentException.class, () -> KlineInterval.fromCode(""));
        }

        @Test
        @DisplayName("toBinanceInterval 返回正确格式")
        void toBinanceIntervalShouldWork() {
            assertEquals("1m", KlineInterval.M1.toBinanceInterval());
            assertEquals("1h", KlineInterval.H1.toBinanceInterval());
            assertEquals("4h", KlineInterval.H4.toBinanceInterval());
            assertEquals("1d", KlineInterval.D1.toBinanceInterval());
            assertEquals("1M", KlineInterval.MO1.toBinanceInterval());
        }

        @Test
        @DisplayName("toOkxInterval 返回正确格式")
        void toOkxIntervalShouldWork() {
            assertEquals("1m", KlineInterval.M1.toOkxInterval());
            assertEquals("1H", KlineInterval.H1.toOkxInterval());
            assertEquals("4H", KlineInterval.H4.toOkxInterval());
            assertEquals("1D", KlineInterval.D1.toOkxInterval());
            assertEquals("1W", KlineInterval.W1.toOkxInterval());
        }

        @Test
        @DisplayName("fromCode 忽略大小写")
        void fromCodeCaseInsensitive() {
            assertEquals(KlineInterval.H1, KlineInterval.fromCode("1H"));
            assertEquals(KlineInterval.D1, KlineInterval.fromCode("1D"));
        }
    }

    // ===================== MarketType =====================

    @Nested
    @DisplayName("MarketType 测试")
    class MarketTypeTest {

        @Test
        @DisplayName("包含 SPOT 和 FUTURES")
        void shouldContainAllTypes() {
            assertEquals(2, MarketType.values().length);
            assertEquals("SPOT", MarketType.SPOT.getCode());
            assertEquals("现货", MarketType.SPOT.getName());
            assertEquals("FUTURES", MarketType.FUTURES.getCode());
            assertEquals("合约", MarketType.FUTURES.getName());
        }

        @Test
        @DisplayName("fromCode 正常和异常场景")
        void fromCodeShouldWork() {
            assertEquals(MarketType.SPOT, MarketType.fromCode("SPOT"));
            assertEquals(MarketType.FUTURES, MarketType.fromCode("futures"));
            assertThrows(IllegalArgumentException.class, () -> MarketType.fromCode("OPTIONS"));
        }
    }

    // ===================== OrderStatus =====================

    @Nested
    @DisplayName("OrderStatus 测试")
    class OrderStatusTest {

        @Test
        @DisplayName("所有状态应存在")
        void allStatusesShouldExist() {
            assertEquals(7, OrderStatus.values().length);
        }

        @ParameterizedTest
        @ValueSource(strings = {"CREATED", "SUBMITTED", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "REJECTED", "EXPIRED"})
        @DisplayName("fromCode 所有已知状态")
        void fromCodeAllKnown(String code) {
            assertDoesNotThrow(() -> OrderStatus.fromCode(code));
        }

        @Test
        @DisplayName("fromCode 未知状态应抛出异常")
        void fromCodeUnknownShouldThrow() {
            assertThrows(IllegalArgumentException.class, () -> OrderStatus.fromCode("PENDING"));
        }
    }

    // ===================== TrendDirection =====================

    @Nested
    @DisplayName("TrendDirection 测试")
    class TrendDirectionTest {

        @Test
        @DisplayName("所有方向应存在")
        void allDirectionsShouldExist() {
            assertEquals(3, TrendDirection.values().length);
            assertEquals("BULLISH", TrendDirection.BULLISH.getCode());
            assertEquals("看涨", TrendDirection.BULLISH.getName());
        }

        @Test
        @DisplayName("fromCode 未知值返回 NEUTRAL")
        void fromCodeUnknownShouldReturnNeutral() {
            assertEquals(TrendDirection.NEUTRAL, TrendDirection.fromCode("UNKNOWN"));
            assertEquals(TrendDirection.NEUTRAL, TrendDirection.fromCode(""));
        }

        @Test
        @DisplayName("fromCode 正常转换")
        void fromCodeShouldWork() {
            assertEquals(TrendDirection.BULLISH, TrendDirection.fromCode("BULLISH"));
            assertEquals(TrendDirection.BEARISH, TrendDirection.fromCode("bearish"));
        }
    }

    // ===================== 简单枚举 =====================

    @Nested
    @DisplayName("简单枚举测试")
    class SimpleEnumTest {

        @Test
        @DisplayName("OrderSide 包含 BUY 和 SELL")
        void orderSideShouldWork() {
            assertEquals(2, OrderSide.values().length);
            assertEquals("BUY", OrderSide.BUY.getCode());
            assertEquals("SELL", OrderSide.SELL.getCode());
        }

        @Test
        @DisplayName("OrderType 包含所有类型")
        void orderTypeShouldWork() {
            assertEquals(4, OrderType.values().length);
            assertEquals("MARKET", OrderType.MARKET.getCode());
            assertEquals("LIMIT", OrderType.LIMIT.getCode());
        }

        @Test
        @DisplayName("PositionSide 包含 LONG 和 SHORT")
        void positionSideShouldWork() {
            assertEquals(2, PositionSide.values().length);
            assertEquals("LONG", PositionSide.LONG.getCode());
            assertEquals("SHORT", PositionSide.SHORT.getCode());
        }

        @Test
        @DisplayName("SignalType 包含所有信号类型")
        void signalTypeShouldWork() {
            assertEquals(3, SignalType.values().length);
            assertEquals("BUY", SignalType.BUY.getCode());
            assertEquals("SELL", SignalType.SELL.getCode());
            assertEquals("HOLD", SignalType.HOLD.getCode());
        }
    }
}
