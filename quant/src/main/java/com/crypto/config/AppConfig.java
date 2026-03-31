package com.crypto.config;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.github.benmanes.caffeine.cache.Caffeine;
import org.apache.hc.client5.http.config.ConnectionConfig;
import org.apache.hc.client5.http.config.RequestConfig;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManagerBuilder;
import org.apache.hc.core5.http.io.SocketConfig;
import org.apache.hc.core5.util.Timeout;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;

/**
 * 应用全局Bean配置
 */
@Configuration
@EnableCaching
public class AppConfig {

    /**
     * 全局 Jackson ObjectMapper
     */
    @Bean
    @Primary
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        mapper.configure(SerializationFeature.FAIL_ON_EMPTY_BEANS, false);
        return mapper;
    }

    /**
     * Apache HttpClient 5 - 替代 OkHttp
     * 支持连接池、超时设置、自动重试
     */
    @Bean
    public CloseableHttpClient httpClient(ExchangeProperties exchangeProperties) {
        // Socket配置
        SocketConfig socketConfig = SocketConfig.custom()
                .setSoTimeout(Timeout.ofSeconds(30))
                .build();

        // 连接配置
        ConnectionConfig connectionConfig = ConnectionConfig.custom()
                .setConnectTimeout(Timeout.ofSeconds(15))
                .setSocketTimeout(Timeout.ofSeconds(30))
                .build();

        // 连接池管理器
        PoolingHttpClientConnectionManager connectionManager = PoolingHttpClientConnectionManagerBuilder.create()
                .setDefaultSocketConfig(socketConfig)
                .setDefaultConnectionConfig(connectionConfig)
                .setMaxConnTotal(100)
                .setMaxConnPerRoute(20)
                .build();

        // 请求配置
        RequestConfig requestConfig = RequestConfig.custom()
                .setConnectionRequestTimeout(Timeout.ofSeconds(10))
                .setResponseTimeout(Timeout.ofSeconds(30))
                .build();

        return HttpClients.custom()
                .setConnectionManager(connectionManager)
                .setDefaultRequestConfig(requestConfig)
                .evictIdleConnections(Timeout.ofSeconds(60))
                .build();
    }

    @Bean
    public WebClient webClient(AiProperties aiProperties) {
        return WebClient.builder()
                .baseUrl(aiProperties.getOpenai().getBaseUrl())
                .defaultHeader("Authorization", "Bearer " + aiProperties.getOpenai().getApiKey())
                .defaultHeader("Content-Type", "application/json")
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(10 * 1024 * 1024))
                .build();
    }

    // ===================== Caffeine 缓存配置 =====================

    /**
     * 缓存管理器 - Caffeine
     * 各缓存区域使用不同的过期策略
     */
    @Bean
    public CacheManager cacheManager() {
        CaffeineCacheManager cacheManager = new CaffeineCacheManager();
        cacheManager.setCaffeine(Caffeine.newBuilder()
                .maximumSize(10000)
                .expireAfterWrite(5, TimeUnit.MINUTES)
                .recordStats());
        return cacheManager;
    }

    /**
     * Tick行情缓存 - 5秒过期（实时行情，短时缓存）
     */
    @Bean("tickCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> tickCache() {
        return Caffeine.newBuilder()
                .maximumSize(500)
                .expireAfterWrite(5, TimeUnit.SECONDS)
                .recordStats()
                .build();
    }

    /**
     * K线缓存 - 60秒过期
     */
    @Bean("klineCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> klineCache() {
        return Caffeine.newBuilder()
                .maximumSize(5000)
                .expireAfterWrite(60, TimeUnit.SECONDS)
                .recordStats()
                .build();
    }

    /**
     * 深度数据缓存 - 10秒过期
     */
    @Bean("depthCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> depthCache() {
        return Caffeine.newBuilder()
                .maximumSize(200)
                .expireAfterWrite(10, TimeUnit.SECONDS)
                .recordStats()
                .build();
    }

    /**
     * 指标缓存 - 2分钟过期
     */
    @Bean("indicatorCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> indicatorCache() {
        return Caffeine.newBuilder()
                .maximumSize(2000)
                .expireAfterWrite(2, TimeUnit.MINUTES)
                .recordStats()
                .build();
    }

    /**
     * AI分析缓存 - 15分钟过期
     */
    @Bean("analysisCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> analysisCache() {
        return Caffeine.newBuilder()
                .maximumSize(500)
                .expireAfterWrite(15, TimeUnit.MINUTES)
                .recordStats()
                .build();
    }

    /**
     * 行情同步线程池
     */
    @Bean("marketSyncExecutor")
    public Executor marketSyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(8);
        executor.setMaxPoolSize(16);
        executor.setQueueCapacity(1000);
        executor.setThreadNamePrefix("market-sync-");
        executor.setKeepAliveSeconds(60);
        executor.initialize();
        return executor;
    }

    /**
     * 交易执行线程池
     */
    @Bean("tradeExecutor")
    public Executor tradeExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(8);
        executor.setQueueCapacity(200);
        executor.setThreadNamePrefix("trade-exec-");
        executor.setKeepAliveSeconds(60);
        executor.initialize();
        return executor;
    }
}
