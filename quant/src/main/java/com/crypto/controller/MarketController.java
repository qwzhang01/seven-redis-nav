package com.crypto.controller;

import com.crypto.entity.KlineEntity;
import com.crypto.enums.ExchangeEnum;
import com.crypto.enums.KlineInterval;
import com.crypto.enums.MarketType;
import com.crypto.exchange.ExchangeApiClient;
import com.crypto.exchange.ExchangeClientFactory;
import com.crypto.model.dto.DepthDTO;
import com.crypto.model.dto.KlineDTO;
import com.crypto.model.dto.TickDTO;
import com.crypto.model.vo.ApiResult;
import com.crypto.service.MarketDataService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Arrays;
import java.util.List;

/**
 * 行情数据API
 */
@RestController
@RequestMapping("/api/market")
@RequiredArgsConstructor
public class MarketController {

    private final ExchangeClientFactory exchangeClientFactory;
    private final MarketDataService marketDataService;

    /**
     * 获取实时K线
     */
    @GetMapping("/klines")
    public ApiResult<List<KlineDTO>> getKlines(
            @RequestParam(defaultValue = "BINANCE") String exchange,
            @RequestParam String symbol,
            @RequestParam(defaultValue = "SPOT") String marketType,
            @RequestParam(defaultValue = "1h") String interval,
            @RequestParam(required = false) Long startTime,
            @RequestParam(required = false) Long endTime,
            @RequestParam(defaultValue = "100") Integer limit) {

        ExchangeApiClient client = exchangeClientFactory.getClient(ExchangeEnum.fromCode(exchange));
        List<KlineDTO> klines = client.getKlines(
                symbol, MarketType.fromCode(marketType),
                KlineInterval.fromCode(interval),
                startTime, endTime, limit);
        return ApiResult.success(klines);
    }

    /**
     * 获取本地存储的历史K线
     */
    @GetMapping("/klines/history")
    public ApiResult<List<KlineEntity>> getHistoryKlines(
            @RequestParam(defaultValue = "BINANCE") String exchange,
            @RequestParam String symbol,
            @RequestParam(defaultValue = "SPOT") String marketType,
            @RequestParam(defaultValue = "1h") String interval,
            @RequestParam(defaultValue = "200") int limit) {

        List<KlineEntity> klines = marketDataService.getLatestKlines(
                exchange, symbol, marketType, interval, limit);
        return ApiResult.success(klines);
    }

    /**
     * 获取实时Tick
     */
    @GetMapping("/ticker")
    public ApiResult<TickDTO> getTicker(
            @RequestParam(defaultValue = "BINANCE") String exchange,
            @RequestParam String symbol,
            @RequestParam(defaultValue = "SPOT") String marketType) {

        ExchangeApiClient client = exchangeClientFactory.getClient(ExchangeEnum.fromCode(exchange));
        TickDTO tick = client.getTicker(symbol, MarketType.fromCode(marketType));
        return ApiResult.success(tick);
    }

    /**
     * 批量获取Tick
     */
    @GetMapping("/tickers")
    public ApiResult<List<TickDTO>> getTickers(
            @RequestParam(defaultValue = "BINANCE") String exchange,
            @RequestParam String symbols, // 逗号分隔
            @RequestParam(defaultValue = "SPOT") String marketType) {

        ExchangeApiClient client = exchangeClientFactory.getClient(ExchangeEnum.fromCode(exchange));
        List<String> symbolList = Arrays.asList(symbols.split(","));
        List<TickDTO> ticks = client.getTickers(symbolList, MarketType.fromCode(marketType));
        return ApiResult.success(ticks);
    }

    /**
     * 获取深度数据
     */
    @GetMapping("/depth")
    public ApiResult<DepthDTO> getDepth(
            @RequestParam(defaultValue = "BINANCE") String exchange,
            @RequestParam String symbol,
            @RequestParam(defaultValue = "SPOT") String marketType,
            @RequestParam(defaultValue = "20") int limit) {

        ExchangeApiClient client = exchangeClientFactory.getClient(ExchangeEnum.fromCode(exchange));
        DepthDTO depth = client.getDepth(symbol, MarketType.fromCode(marketType), limit);
        return ApiResult.success(depth);
    }
}
