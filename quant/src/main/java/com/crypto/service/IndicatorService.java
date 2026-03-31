package com.crypto.service;

import com.crypto.config.TradingProperties;
import com.crypto.entity.IndicatorEntity;
import com.crypto.entity.KlineEntity;
import com.crypto.enums.ExchangeEnum;
import com.crypto.enums.MarketType;
import com.crypto.exchange.ExchangeClientFactory;
import com.crypto.mapper.IndicatorMapper;
import com.crypto.model.dto.IndicatorDTO;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * 指标管理服务 - 定时计算并持久化技术指标
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class IndicatorService {

    private final IndicatorCalculationService calculationService;
    private final MarketDataService marketDataService;
    private final IndicatorMapper indicatorMapper;
    private final ExchangeClientFactory exchangeClientFactory;
    private final TradingProperties tradingProperties;
    private final ObjectMapper objectMapper;

    /**
     * 定时计算技术指标 (每2分钟)
     */
    @Scheduled(fixedDelay = 120000, initialDelay = 30000)
    public void scheduleCalculateIndicators() {
        log.info("========== 开始计算技术指标 ==========");

        for (ExchangeEnum exchange : exchangeClientFactory.getAllClients().keySet()) {
            String exchangeCode = exchange.getCode();

            // 现货
            for (String symbol : tradingProperties.getSymbols().getSpot()) {
                for (String interval : tradingProperties.getKlineIntervals()) {
                    calculateAndSave(exchangeCode, symbol, MarketType.SPOT.getCode(), interval);
                }
            }

            // 合约
            for (String symbol : tradingProperties.getSymbols().getFutures()) {
                for (String interval : tradingProperties.getKlineIntervals()) {
                    calculateAndSave(exchangeCode, symbol, MarketType.FUTURES.getCode(), interval);
                }
            }
        }

        log.info("========== 技术指标计算完成 ==========");
    }

    /**
     * 计算并保存指标
     */
    public IndicatorDTO calculateAndSave(String exchange, String symbol, String marketType, String interval) {
        try {
            // 获取最近的K线数据（至少需要200根来计算长期指标）
            List<KlineEntity> klines = marketDataService.getLatestKlines(
                    exchange, symbol, marketType, interval, 300);

            if (klines.isEmpty()) {
                return null;
            }

            // Ta4j需要正序排列
            Collections.reverse(klines);

            // 计算指标
            IndicatorDTO dto = calculationService.calculateIndicators(
                    klines, exchange, symbol, marketType, interval);

            if (dto == null) {
                return null;
            }

            // 保存到数据库
            saveIndicator(dto);
            return dto;

        } catch (Exception e) {
            log.error("计算指标异常: {}/{}/{}/{}", exchange, symbol, marketType, interval, e);
            return null;
        }
    }

    /**
     * 获取最新指标
     */
    public IndicatorEntity getLatestIndicator(String exchange, String symbol,
                                              String marketType, String interval) {
        return indicatorMapper.getLatestIndicator(exchange, symbol, marketType, interval);
    }

    private void saveIndicator(IndicatorDTO dto) {
        IndicatorEntity entity = IndicatorEntity.builder()
                .exchange(dto.getExchange())
                .symbol(dto.getSymbol())
                .marketType(dto.getMarketType())
                .intervalVal(dto.getInterval())
                .calcTime(dto.getCalcTime())
                .ma5(dto.getMa5())
                .ma10(dto.getMa10())
                .ma20(dto.getMa20())
                .ma60(dto.getMa60())
                .ema12(dto.getEma12())
                .ema26(dto.getEma26())
                .macdLine(dto.getMacdLine())
                .macdSignal(dto.getMacdSignal())
                .macdHistogram(dto.getMacdHistogram())
                .rsi6(dto.getRsi6())
                .rsi14(dto.getRsi14())
                .rsi24(dto.getRsi24())
                .bollUpper(dto.getBollUpper())
                .bollMiddle(dto.getBollMiddle())
                .bollLower(dto.getBollLower())
                .kdjK(dto.getKdjK())
                .kdjD(dto.getKdjD())
                .kdjJ(dto.getKdjJ())
                .volMa5(dto.getVolMa5())
                .volMa10(dto.getVolMa10())
                .atr14(dto.getAtr14())
                .vwap(dto.getVwap())
                .obv(dto.getObv())
                .extraIndicators(toJson(dto.getExtraIndicators()))
                .build();

        indicatorMapper.insert(entity);
    }

    private String toJson(Object obj) {
        if (obj == null) return null;
        try {
            return objectMapper.writeValueAsString(obj);
        } catch (Exception e) {
            log.warn("JSON序列化失败", e);
            return obj.toString();
        }
    }
}
