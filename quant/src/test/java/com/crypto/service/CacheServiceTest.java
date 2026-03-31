package com.crypto.service;

import com.crypto.entity.IndicatorEntity;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.TickDTO;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/**
 * CacheService 缓存服务测试
 */
class CacheServiceTest {

    private CacheService cacheService;
    private Cache<String, Object> tickCache;
    private Cache<String, Object> klineCache;
    private Cache<String, Object> depthCache;
    private Cache<String, Object> indicatorCache;
    private Cache<String, Object> analysisCache;

    @BeforeEach
    void setUp() {
        tickCache = Caffeine.newBuilder()
                .maximumSize(100)
                .expireAfterWrite(5, TimeUnit.SECONDS)
                .recordStats()
                .build();
        klineCache = Caffeine.newBuilder()
                .maximumSize(100)
                .expireAfterWrite(60, TimeUnit.SECONDS)
                .recordStats()
                .build();
        depthCache = Caffeine.newBuilder()
                .maximumSize(100)
                .expireAfterWrite(10, TimeUnit.SECONDS)
                .recordStats()
                .build();
        indicatorCache = Caffeine.newBuilder()
                .maximumSize(100)
                .expireAfterWrite(2, TimeUnit.MINUTES)
                .recordStats()
                .build();
        analysisCache = Caffeine.newBuilder()
                .maximumSize(100)
                .expireAfterWrite(15, TimeUnit.MINUTES)
                .recordStats()
                .build();

        cacheService = new CacheService(tickCache, klineCache, depthCache, indicatorCache, analysisCache);
    }

    // ===================== Tick 缓存测试 =====================

    @Nested
    @DisplayName("Tick 缓存")
    class TickCacheTest {

        @Test
        @DisplayName("put 和 get 正常工作")
        void putAndGetShouldWork() {
            TickDTO tick = TickDTO.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .marketType("SPOT")
                    .lastPrice(new BigDecimal("50000.00"))
                    .build();

            cacheService.putTick("BINANCE", "BTC/USDT", "SPOT", tick);

            Optional<TickDTO> result = cacheService.getTick("BINANCE", "BTC/USDT", "SPOT");
            assertTrue(result.isPresent());
            assertEquals(new BigDecimal("50000.00"), result.get().getLastPrice());
        }

        @Test
        @DisplayName("缓存未命中返回 empty")
        void getMissShouldReturnEmpty() {
            Optional<TickDTO> result = cacheService.getTick("BINANCE", "ETH/USDT", "SPOT");
            assertFalse(result.isPresent());
        }

        @Test
        @DisplayName("不同交易对互不影响")
        void differentSymbolsShouldNotInterfere() {
            TickDTO btcTick = TickDTO.builder()
                    .symbol("BTC/USDT")
                    .lastPrice(new BigDecimal("50000"))
                    .build();
            TickDTO ethTick = TickDTO.builder()
                    .symbol("ETH/USDT")
                    .lastPrice(new BigDecimal("3000"))
                    .build();

            cacheService.putTick("BINANCE", "BTC/USDT", "SPOT", btcTick);
            cacheService.putTick("BINANCE", "ETH/USDT", "SPOT", ethTick);

            assertEquals(new BigDecimal("50000"),
                    cacheService.getTick("BINANCE", "BTC/USDT", "SPOT").get().getLastPrice());
            assertEquals(new BigDecimal("3000"),
                    cacheService.getTick("BINANCE", "ETH/USDT", "SPOT").get().getLastPrice());
        }

        @Test
        @DisplayName("覆盖写入应返回最新值")
        void putShouldOverwrite() {
            TickDTO tick1 = TickDTO.builder().lastPrice(new BigDecimal("50000")).build();
            TickDTO tick2 = TickDTO.builder().lastPrice(new BigDecimal("51000")).build();

            cacheService.putTick("BINANCE", "BTC/USDT", "SPOT", tick1);
            cacheService.putTick("BINANCE", "BTC/USDT", "SPOT", tick2);

            Optional<TickDTO> result = cacheService.getTick("BINANCE", "BTC/USDT", "SPOT");
            assertTrue(result.isPresent());
            assertEquals(new BigDecimal("51000"), result.get().getLastPrice());
        }
    }

    // ===================== Depth 缓存测试 =====================

    @Nested
    @DisplayName("Depth 缓存")
    class DepthCacheTest {

        @Test
        @DisplayName("put 和 get 正常工作")
        void putAndGetShouldWork() {
            DepthDTO depth = DepthDTO.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .marketType("SPOT")
                    .bids(new ArrayList<>())
                    .asks(new ArrayList<>())
                    .lastUpdateId(12345L)
                    .build();

            cacheService.putDepth("BINANCE", "BTC/USDT", "SPOT", depth);

            Optional<DepthDTO> result = cacheService.getDepth("BINANCE", "BTC/USDT", "SPOT");
            assertTrue(result.isPresent());
            assertEquals(12345L, result.get().getLastUpdateId());
        }

        @Test
        @DisplayName("缓存未命中返回 empty")
        void getMissShouldReturnEmpty() {
            Optional<DepthDTO> result = cacheService.getDepth("OKX", "BTC/USDT", "FUTURES");
            assertFalse(result.isPresent());
        }
    }

    // ===================== Indicator 缓存测试 =====================

    @Nested
    @DisplayName("Indicator 缓存")
    class IndicatorCacheTest {

        @Test
        @DisplayName("put 和 get 正常工作（含 interval）")
        void putAndGetWithIntervalShouldWork() {
            IndicatorEntity indicator = IndicatorEntity.builder()
                    .exchange("BINANCE")
                    .symbol("BTC/USDT")
                    .marketType("FUTURES")
                    .intervalVal("1h")
                    .rsi14(new BigDecimal("55.5"))
                    .build();

            cacheService.putIndicator("BINANCE", "BTC/USDT", "FUTURES", "1h", indicator);

            Optional<IndicatorEntity> result = cacheService.getIndicator("BINANCE", "BTC/USDT", "FUTURES", "1h");
            assertTrue(result.isPresent());
            assertEquals(new BigDecimal("55.5"), result.get().getRsi14());
        }

        @Test
        @DisplayName("不同周期互不影响")
        void differentIntervalsShouldNotInterfere() {
            IndicatorEntity ind1h = IndicatorEntity.builder()
                    .intervalVal("1h")
                    .rsi14(new BigDecimal("55"))
                    .build();
            IndicatorEntity ind4h = IndicatorEntity.builder()
                    .intervalVal("4h")
                    .rsi14(new BigDecimal("65"))
                    .build();

            cacheService.putIndicator("BINANCE", "BTC/USDT", "FUTURES", "1h", ind1h);
            cacheService.putIndicator("BINANCE", "BTC/USDT", "FUTURES", "4h", ind4h);

            assertEquals(new BigDecimal("55"),
                    cacheService.getIndicator("BINANCE", "BTC/USDT", "FUTURES", "1h").get().getRsi14());
            assertEquals(new BigDecimal("65"),
                    cacheService.getIndicator("BINANCE", "BTC/USDT", "FUTURES", "4h").get().getRsi14());
        }
    }

    // ===================== Analysis 缓存测试 =====================

    @Nested
    @DisplayName("Analysis 缓存")
    class AnalysisCacheTest {

        @Test
        @DisplayName("put 和 get 正常工作")
        void putAndGetShouldWork() {
            String analysis = "BULLISH with high confidence";
            cacheService.putAnalysis("BINANCE", "BTC/USDT", "FUTURES", analysis);

            Optional<String> result = cacheService.getAnalysis("BINANCE", "BTC/USDT", "FUTURES", String.class);
            assertTrue(result.isPresent());
            assertEquals("BULLISH with high confidence", result.get());
        }

        @Test
        @DisplayName("类型不匹配返回 empty")
        void wrongTypeShouldReturnEmpty() {
            cacheService.putAnalysis("BINANCE", "BTC/USDT", "FUTURES", "string value");

            Optional<Integer> result = cacheService.getAnalysis("BINANCE", "BTC/USDT", "FUTURES", Integer.class);
            assertFalse(result.isPresent());
        }
    }

    // ===================== 通用操作测试 =====================

    @Nested
    @DisplayName("通用缓存操作")
    class GeneralCacheTest {

        @Test
        @DisplayName("invalidateAll 清除所有缓存")
        void invalidateAllShouldClearAllCaches() {
            cacheService.putTick("BINANCE", "BTC/USDT", "SPOT",
                    TickDTO.builder().lastPrice(new BigDecimal("50000")).build());
            cacheService.putDepth("BINANCE", "BTC/USDT", "SPOT",
                    DepthDTO.builder().lastUpdateId(1L).build());
            cacheService.putIndicator("BINANCE", "BTC/USDT", "FUTURES", "1h",
                    IndicatorEntity.builder().rsi14(new BigDecimal("50")).build());
            cacheService.putAnalysis("BINANCE", "BTC/USDT", "FUTURES", "analysis");

            cacheService.invalidateAll();

            assertFalse(cacheService.getTick("BINANCE", "BTC/USDT", "SPOT").isPresent());
            assertFalse(cacheService.getDepth("BINANCE", "BTC/USDT", "SPOT").isPresent());
            assertFalse(cacheService.getIndicator("BINANCE", "BTC/USDT", "FUTURES", "1h").isPresent());
            assertFalse(cacheService.getAnalysis("BINANCE", "BTC/USDT", "FUTURES", String.class).isPresent());
        }

        @Test
        @DisplayName("getCacheStats 返回非空统计信息")
        void getCacheStatsShouldReturnNonEmpty() {
            String stats = cacheService.getCacheStats();
            assertNotNull(stats);
            assertTrue(stats.contains("Tick缓存"));
            assertTrue(stats.contains("K线缓存"));
            assertTrue(stats.contains("深度缓存"));
            assertTrue(stats.contains("指标缓存"));
            assertTrue(stats.contains("分析缓存"));
        }
    }
}
