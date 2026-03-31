package com.crypto.service;

import com.crypto.entity.KlineEntity;
import com.crypto.model.dto.IndicatorDTO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.ta4j.core.*;
import org.ta4j.core.indicators.*;
import org.ta4j.core.indicators.adx.ADXIndicator;
import org.ta4j.core.indicators.adx.MinusDIIndicator;
import org.ta4j.core.indicators.adx.PlusDIIndicator;
import org.ta4j.core.indicators.bollinger.BollingerBandsLowerIndicator;
import org.ta4j.core.indicators.bollinger.BollingerBandsMiddleIndicator;
import org.ta4j.core.indicators.bollinger.BollingerBandsUpperIndicator;
import org.ta4j.core.indicators.helpers.*;
import org.ta4j.core.indicators.statistics.StandardDeviationIndicator;
import org.ta4j.core.indicators.volume.OnBalanceVolumeIndicator;
import org.ta4j.core.indicators.volume.VWAPIndicator;
import org.ta4j.core.num.DecimalNum;
import org.ta4j.core.num.Num;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.*;

/**
 * 技术指标计算服务 - 基于Ta4j高性能量化交易指标计算库
 *
 * 支持指标:
 * - MA (SMA): 5/10/20/60日均线
 * - EMA: 12/26指数移动平均
 * - MACD: DIF/DEA/柱状线
 * - RSI: 6/14/24周期
 * - 布林带: 上/中/下轨
 * - KDJ: K/D/J值
 * - ATR: 14周期平均真实范围
 * - VWAP: 成交量加权平均价
 * - OBV: 能量潮指标
 * - 更多指标可按需扩展
 */
@Slf4j
@Service
public class IndicatorCalculationService {

    /**
     * 根据K线数据计算所有技术指标
     *
     * @param klines    K线数据列表(按时间正序排列)
     * @param exchange  交易所
     * @param symbol    交易对
     * @param marketType 市场类型
     * @param interval  K线周期
     * @return 最新一根K线对应的指标计算结果
     */
    public IndicatorDTO calculateIndicators(List<KlineEntity> klines, String exchange,
                                            String symbol, String marketType, String interval) {
        if (klines == null || klines.size() < 60) {
            log.warn("K线数据不足，至少需要60条: exchange={}, symbol={}, interval={}, actual={}",
                    exchange, symbol, interval, klines != null ? klines.size() : 0);
            return null;
        }

        // 构建Ta4j的BarSeries
        BarSeries series = buildBarSeries(klines, symbol);
        int lastIndex = series.getEndIndex();

        try {
            IndicatorDTO result = new IndicatorDTO();
            result.setExchange(exchange);
            result.setSymbol(symbol);
            result.setMarketType(marketType);
            result.setInterval(interval);
            result.setCalcTime(klines.get(klines.size() - 1).getOpenTime());

            // ========== 收盘价指标 ==========
            ClosePriceIndicator closePrice = new ClosePriceIndicator(series);

            // ========== 移动平均线 MA ==========
            SMAIndicator sma5 = new SMAIndicator(closePrice, 5);
            SMAIndicator sma10 = new SMAIndicator(closePrice, 10);
            SMAIndicator sma20 = new SMAIndicator(closePrice, 20);
            SMAIndicator sma60 = new SMAIndicator(closePrice, 60);

            result.setMa5(numToBigDecimal(sma5.getValue(lastIndex)));
            result.setMa10(numToBigDecimal(sma10.getValue(lastIndex)));
            result.setMa20(numToBigDecimal(sma20.getValue(lastIndex)));
            result.setMa60(numToBigDecimal(sma60.getValue(lastIndex)));

            // ========== EMA ==========
            EMAIndicator ema12 = new EMAIndicator(closePrice, 12);
            EMAIndicator ema26 = new EMAIndicator(closePrice, 26);

            result.setEma12(numToBigDecimal(ema12.getValue(lastIndex)));
            result.setEma26(numToBigDecimal(ema26.getValue(lastIndex)));

            // ========== MACD ==========
            MACDIndicator macd = new MACDIndicator(closePrice, 12, 26);
            EMAIndicator signal = new EMAIndicator(macd, 9);

            Num macdValue = macd.getValue(lastIndex);
            Num signalValue = signal.getValue(lastIndex);
            Num histogramValue = macdValue.minus(signalValue);

            result.setMacdLine(numToBigDecimal(macdValue));
            result.setMacdSignal(numToBigDecimal(signalValue));
            result.setMacdHistogram(numToBigDecimal(histogramValue));

            // ========== RSI ==========
            RSIIndicator rsi6 = new RSIIndicator(closePrice, 6);
            RSIIndicator rsi14 = new RSIIndicator(closePrice, 14);
            RSIIndicator rsi24 = new RSIIndicator(closePrice, 24);

            result.setRsi6(numToBigDecimal(rsi6.getValue(lastIndex)));
            result.setRsi14(numToBigDecimal(rsi14.getValue(lastIndex)));
            result.setRsi24(numToBigDecimal(rsi24.getValue(lastIndex)));

            // ========== 布林带 (20, 2) ==========
            BollingerBandsMiddleIndicator bbMiddle = new BollingerBandsMiddleIndicator(sma20);
            StandardDeviationIndicator stdDev = new StandardDeviationIndicator(closePrice, 20);
            BollingerBandsUpperIndicator bbUpper = new BollingerBandsUpperIndicator(bbMiddle, stdDev);
            BollingerBandsLowerIndicator bbLower = new BollingerBandsLowerIndicator(bbMiddle, stdDev);

            result.setBollUpper(numToBigDecimal(bbUpper.getValue(lastIndex)));
            result.setBollMiddle(numToBigDecimal(bbMiddle.getValue(lastIndex)));
            result.setBollLower(numToBigDecimal(bbLower.getValue(lastIndex)));

            // ========== KDJ ==========
            calculateKDJ(series, lastIndex, result);

            // ========== 成交量MA ==========
            VolumeIndicator volume = new VolumeIndicator(series);
            SMAIndicator volMa5 = new SMAIndicator(volume, 5);
            SMAIndicator volMa10 = new SMAIndicator(volume, 10);

            result.setVolMa5(numToBigDecimal(volMa5.getValue(lastIndex)));
            result.setVolMa10(numToBigDecimal(volMa10.getValue(lastIndex)));

            // ========== ATR (14) ==========
            ATRIndicator atr14 = new ATRIndicator(series, 14);
            result.setAtr14(numToBigDecimal(atr14.getValue(lastIndex)));

            // ========== VWAP ==========
            VWAPIndicator vwap = new VWAPIndicator(series, 20);
            result.setVwap(numToBigDecimal(vwap.getValue(lastIndex)));

            // ========== OBV ==========
            OnBalanceVolumeIndicator obv = new OnBalanceVolumeIndicator(series);
            result.setObv(numToBigDecimal(obv.getValue(lastIndex)));

            // ========== 额外指标 ==========
            Map<String, BigDecimal> extra = calculateExtraIndicators(series, closePrice, lastIndex);
            result.setExtraIndicators(extra);

            log.debug("指标计算完成: exchange={}, symbol={}, interval={}, calcTime={}",
                    exchange, symbol, interval, result.getCalcTime());
            return result;

        } catch (Exception e) {
            log.error("指标计算异常: exchange={}, symbol={}, interval={}", exchange, symbol, interval, e);
            return null;
        }
    }

    /**
     * 计算KDJ指标
     * K = 2/3 * 前一日K值 + 1/3 * 当日RSV
     * D = 2/3 * 前一日D值 + 1/3 * 当日K值
     * J = 3K - 2D
     */
    private void calculateKDJ(BarSeries series, int lastIndex, IndicatorDTO result) {
        int period = 9;
        double k = 50.0, d = 50.0;

        int start = Math.max(0, lastIndex - 200);
        for (int i = start; i <= lastIndex; i++) {
            int startIdx = Math.max(0, i - period + 1);

            // 计算N日内的最高最低价
            double highest = Double.MIN_VALUE;
            double lowest = Double.MAX_VALUE;
            for (int j = startIdx; j <= i; j++) {
                double high = series.getBar(j).getHighPrice().doubleValue();
                double low = series.getBar(j).getLowPrice().doubleValue();
                if (high > highest) highest = high;
                if (low < lowest) lowest = low;
            }

            double close = series.getBar(i).getClosePrice().doubleValue();
            double rsv = (highest == lowest) ? 50.0 : ((close - lowest) / (highest - lowest)) * 100;

            k = 2.0 / 3.0 * k + 1.0 / 3.0 * rsv;
            d = 2.0 / 3.0 * d + 1.0 / 3.0 * k;
        }

        double j = 3.0 * k - 2.0 * d;

        result.setKdjK(BigDecimal.valueOf(k).setScale(4, RoundingMode.HALF_UP));
        result.setKdjD(BigDecimal.valueOf(d).setScale(4, RoundingMode.HALF_UP));
        result.setKdjJ(BigDecimal.valueOf(j).setScale(4, RoundingMode.HALF_UP));
    }

    /**
     * 计算额外的技术指标
     */
    private Map<String, BigDecimal> calculateExtraIndicators(BarSeries series,
                                                             ClosePriceIndicator closePrice,
                                                             int lastIndex) {
        Map<String, BigDecimal> extra = new LinkedHashMap<>();

        // Williams %R (14)
        WilliamsRIndicator williamsR = new WilliamsRIndicator(series, 14);
        extra.put("williamsR14", numToBigDecimal(williamsR.getValue(lastIndex)));

        // CCI (20)
        CCIIndicator cci = new CCIIndicator(series, 20);
        extra.put("cci20", numToBigDecimal(cci.getValue(lastIndex)));

        // ADX (14)
        ADXIndicator adx = new ADXIndicator(series, 14);
        extra.put("adx14", numToBigDecimal(adx.getValue(lastIndex)));

        // +DI, -DI
        PlusDIIndicator plusDI = new PlusDIIndicator(series, 14);
        MinusDIIndicator minusDI = new MinusDIIndicator(series, 14);
        extra.put("plusDI14", numToBigDecimal(plusDI.getValue(lastIndex)));
        extra.put("minusDI14", numToBigDecimal(minusDI.getValue(lastIndex)));

        // ROC (12) - Rate of Change
        ROCIndicator roc = new ROCIndicator(closePrice, 12);
        extra.put("roc12", numToBigDecimal(roc.getValue(lastIndex)));

        // MA200 长期趋势
        if (series.getBarCount() >= 200) {
            SMAIndicator sma200 = new SMAIndicator(closePrice, 200);
            extra.put("ma200", numToBigDecimal(sma200.getValue(lastIndex)));
        }

        // EMA50
        if (series.getBarCount() >= 50) {
            EMAIndicator ema50 = new EMAIndicator(closePrice, 50);
            extra.put("ema50", numToBigDecimal(ema50.getValue(lastIndex)));
        }

        return extra;
    }

    /**
     * 构建Ta4j BarSeries
     */
    private BarSeries buildBarSeries(List<KlineEntity> klines, String symbol) {
        BarSeries series = new BaseBarSeriesBuilder()
                .withName(symbol)
                .withNumTypeOf(DecimalNum.class)
                .build();

        for (KlineEntity kline : klines) {
            ZonedDateTime time = ZonedDateTime.ofInstant(
                    Instant.ofEpochMilli(kline.getCloseTime()),
                    ZoneId.systemDefault()
            );

            series.addBar(Duration.ofMillis(kline.getCloseTime() - kline.getOpenTime()),
                    time,
                    DecimalNum.valueOf(kline.getOpenPrice()),
                    DecimalNum.valueOf(kline.getHighPrice()),
                    DecimalNum.valueOf(kline.getLowPrice()),
                    DecimalNum.valueOf(kline.getClosePrice()),
                    DecimalNum.valueOf(kline.getVolume()),
                    DecimalNum.valueOf(kline.getQuoteVolume() != null ? kline.getQuoteVolume() : BigDecimal.ZERO));
        }

        return series;
    }

    private BigDecimal numToBigDecimal(Num num) {
        if (num == null || num.isNaN()) {
            return null;
        }
        return BigDecimal.valueOf(num.doubleValue()).setScale(10, RoundingMode.HALF_UP);
    }
}
