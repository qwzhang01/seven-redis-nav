package com.crypto.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.crypto.entity.*;
import com.crypto.mapper.*;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.KlineDTO;
import com.crypto.model.dto.TickDTO;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

/**
 * 行情数据持久化服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MarketDataService {

    private final KlineMapper klineMapper;
    private final TickMapper tickMapper;
    private final DepthMapper depthMapper;
    private final ObjectMapper objectMapper;

    /**
     * 保存K线数据 - 使用UPSERT避免重复
     */
    @Transactional(rollbackFor = Exception.class)
    public int saveKlines(List<KlineDTO> klines) {
        int count = 0;
        for (KlineDTO dto : klines) {
            // 检查是否已存在
            LambdaQueryWrapper<KlineEntity> wrapper = new LambdaQueryWrapper<KlineEntity>()
                    .eq(KlineEntity::getExchange, dto.getExchange())
                    .eq(KlineEntity::getSymbol, dto.getSymbol())
                    .eq(KlineEntity::getMarketType, dto.getMarketType())
                    .eq(KlineEntity::getIntervalVal, dto.getInterval())
                    .eq(KlineEntity::getOpenTime, dto.getOpenTime());

            KlineEntity existing = klineMapper.selectOne(wrapper);

            if (existing != null) {
                // 更新
                existing.setClosePrice(dto.getClosePrice());
                existing.setHighPrice(dto.getHighPrice());
                existing.setLowPrice(dto.getLowPrice());
                existing.setVolume(dto.getVolume());
                existing.setQuoteVolume(dto.getQuoteVolume());
                existing.setTradesCount(dto.getTradesCount());
                existing.setTakerBuyVol(dto.getTakerBuyVolume());
                existing.setTakerBuyQuote(dto.getTakerBuyQuoteVolume());
                klineMapper.updateById(existing);
            } else {
                // 插入
                KlineEntity entity = KlineEntity.builder()
                        .exchange(dto.getExchange())
                        .symbol(dto.getSymbol())
                        .marketType(dto.getMarketType())
                        .intervalVal(dto.getInterval())
                        .openTime(dto.getOpenTime())
                        .closeTime(dto.getCloseTime())
                        .openPrice(dto.getOpenPrice())
                        .highPrice(dto.getHighPrice())
                        .lowPrice(dto.getLowPrice())
                        .closePrice(dto.getClosePrice())
                        .volume(dto.getVolume())
                        .quoteVolume(dto.getQuoteVolume())
                        .tradesCount(dto.getTradesCount() != null ? dto.getTradesCount() : 0)
                        .takerBuyVol(dto.getTakerBuyVolume() != null ? dto.getTakerBuyVolume() : BigDecimal.ZERO)
                        .takerBuyQuote(dto.getTakerBuyQuoteVolume() != null ? dto.getTakerBuyQuoteVolume() : BigDecimal.ZERO)
                        .build();
                klineMapper.insert(entity);
                count++;
            }
        }
        return count;
    }

    /**
     * 保存Tick数据
     */
    public void saveTick(TickDTO dto) {
        if (dto == null) return;

        TickEntity entity = TickEntity.builder()
                .exchange(dto.getExchange())
                .symbol(dto.getSymbol())
                .marketType(dto.getMarketType())
                .lastPrice(dto.getLastPrice())
                .bestBidPrice(dto.getBestBidPrice())
                .bestBidQty(dto.getBestBidQty())
                .bestAskPrice(dto.getBestAskPrice())
                .bestAskQty(dto.getBestAskQty())
                .volume24h(dto.getVolume24h())
                .quoteVol24h(dto.getQuoteVolume24h())
                .high24h(dto.getHigh24h())
                .low24h(dto.getLow24h())
                .open24h(dto.getOpen24h())
                .priceChange(dto.getPriceChange())
                .priceChangePct(dto.getPriceChangePct())
                .eventTime(dto.getEventTime())
                .build();
        tickMapper.insert(entity);
    }

    /**
     * 保存深度数据
     */
    public void saveDepth(DepthDTO dto) {
        if (dto == null) return;

        String bidsJson;
        String asksJson;
        try {
            bidsJson = objectMapper.writeValueAsString(dto.getBids());
            asksJson = objectMapper.writeValueAsString(dto.getAsks());
        } catch (Exception e) {
            bidsJson = "[]";
            asksJson = "[]";
        }

        DepthEntity entity = DepthEntity.builder()
                .exchange(dto.getExchange())
                .symbol(dto.getSymbol())
                .marketType(dto.getMarketType())
                .bids(bidsJson)
                .asks(asksJson)
                .lastUpdateId(dto.getLastUpdateId())
                .eventTime(dto.getEventTime())
                .build();
        depthMapper.insert(entity);
    }

    /**
     * 获取最新的K线开盘时间，用于增量同步
     */
    public Long getLatestKlineOpenTime(String exchange, String symbol, String marketType, String interval) {
        return klineMapper.getLatestOpenTime(exchange, symbol, marketType, interval);
    }

    /**
     * 获取最近N根K线
     */
    public List<KlineEntity> getLatestKlines(String exchange, String symbol, String marketType,
                                             String interval, int limit) {
        return klineMapper.getLatestKlines(exchange, symbol, marketType, interval, limit);
    }
}
