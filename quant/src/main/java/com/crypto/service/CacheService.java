package com.crypto.service;

import com.crypto.entity.IndicatorEntity;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.TickDTO;
import com.github.benmanes.caffeine.cache.Cache;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.util.Optional;

/**
 * 全局缓存服务 - 基于 Caffeine 的内存缓存
 *
 * 缓存区域:
 * - tickCache: 实时Tick行情, 5s过期
 * - klineCache: K线数据, 60s过期
 * - depthCache: 深度数据, 10s过期
 * - indicatorCache: 技术指标, 2min过期
 * - analysisCache: AI分析结果, 15min过期
 *
 * 使用场景:
 * 1. 行情查询API直接从缓存获取，减少数据库查询
 * 2. WebSocket同步的实时数据写入缓存，供快速读取
 * 3. 指标计算结果缓存，避免重复计算
 */
@Slf4j
@Service
public class CacheService {

    private final Cache<String, Object> tickCache;
    private final Cache<String, Object> klineCache;
    private final Cache<String, Object> depthCache;
    private final Cache<String, Object> indicatorCache;
    private final Cache<String, Object> analysisCache;

    public CacheService(@Qualifier("tickCache") Cache<String, Object> tickCache,
                        @Qualifier("klineCache") Cache<String, Object> klineCache,
                        @Qualifier("depthCache") Cache<String, Object> depthCache,
                        @Qualifier("indicatorCache") Cache<String, Object> indicatorCache,
                        @Qualifier("analysisCache") Cache<String, Object> analysisCache) {
        this.tickCache = tickCache;
        this.klineCache = klineCache;
        this.depthCache = depthCache;
        this.indicatorCache = indicatorCache;
        this.analysisCache = analysisCache;
    }

    // ===================== Tick 缓存 =====================

    /**
     * 缓存Tick行情
     * Key格式: {exchange}:{symbol}:{marketType}
     */
    public void putTick(String exchange, String symbol, String marketType, TickDTO tick) {
        String key = buildKey(exchange, symbol, marketType);
        tickCache.put(key, tick);
    }

    /**
     * 获取缓存的Tick行情
     */
    public Optional<TickDTO> getTick(String exchange, String symbol, String marketType) {
        String key = buildKey(exchange, symbol, marketType);
        Object val = tickCache.getIfPresent(key);
        return val instanceof TickDTO ? Optional.of((TickDTO) val) : Optional.empty();
    }

    // ===================== Depth 缓存 =====================

    /**
     * 缓存深度数据
     */
    public void putDepth(String exchange, String symbol, String marketType, DepthDTO depth) {
        String key = buildKey(exchange, symbol, marketType);
        depthCache.put(key, depth);
    }

    /**
     * 获取缓存的深度数据
     */
    public Optional<DepthDTO> getDepth(String exchange, String symbol, String marketType) {
        String key = buildKey(exchange, symbol, marketType);
        Object val = depthCache.getIfPresent(key);
        return val instanceof DepthDTO ? Optional.of((DepthDTO) val) : Optional.empty();
    }

    // ===================== Indicator 缓存 =====================

    /**
     * 缓存指标数据
     * Key格式: {exchange}:{symbol}:{marketType}:{interval}
     */
    public void putIndicator(String exchange, String symbol, String marketType,
                             String interval, IndicatorEntity indicator) {
        String key = buildKey(exchange, symbol, marketType) + ":" + interval;
        indicatorCache.put(key, indicator);
    }

    /**
     * 获取缓存的指标
     */
    public Optional<IndicatorEntity> getIndicator(String exchange, String symbol,
                                                  String marketType, String interval) {
        String key = buildKey(exchange, symbol, marketType) + ":" + interval;
        Object val = indicatorCache.getIfPresent(key);
        return val instanceof IndicatorEntity ? Optional.of((IndicatorEntity) val) : Optional.empty();
    }

    // ===================== Analysis 缓存 =====================

    /**
     * 缓存AI分析结果
     */
    public void putAnalysis(String exchange, String symbol, String marketType, Object analysis) {
        String key = buildKey(exchange, symbol, marketType);
        analysisCache.put(key, analysis);
    }

    /**
     * 获取缓存的AI分析
     */
    @SuppressWarnings("unchecked")
    public <T> Optional<T> getAnalysis(String exchange, String symbol, String marketType, Class<T> type) {
        String key = buildKey(exchange, symbol, marketType);
        Object val = analysisCache.getIfPresent(key);
        if (val != null && type.isInstance(val)) {
            return Optional.of((T) val);
        }
        return Optional.empty();
    }

    // ===================== 通用操作 =====================

    /**
     * 使所有缓存失效（慎用）
     */
    public void invalidateAll() {
        tickCache.invalidateAll();
        klineCache.invalidateAll();
        depthCache.invalidateAll();
        indicatorCache.invalidateAll();
        analysisCache.invalidateAll();
        log.info("所有缓存已清除");
    }

    /**
     * 获取缓存统计信息
     */
    public String getCacheStats() {
        StringBuilder sb = new StringBuilder("=== 缓存统计 ===\n");
        sb.append("Tick缓存: ").append(tickCache.stats()).append("\n");
        sb.append("K线缓存: ").append(klineCache.stats()).append("\n");
        sb.append("深度缓存: ").append(depthCache.stats()).append("\n");
        sb.append("指标缓存: ").append(indicatorCache.stats()).append("\n");
        sb.append("分析缓存: ").append(analysisCache.stats()).append("\n");
        return sb.toString();
    }

    private String buildKey(String exchange, String symbol, String marketType) {
        return exchange + ":" + symbol + ":" + marketType;
    }
}
