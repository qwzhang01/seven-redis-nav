package com.crypto.controller;

import com.crypto.entity.IndicatorEntity;
import com.crypto.model.dto.IndicatorDTO;
import com.crypto.model.vo.ApiResult;
import com.crypto.service.IndicatorService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 技术指标API
 */
@RestController
@RequestMapping("/api/indicator")
@RequiredArgsConstructor
public class IndicatorController {

    private final IndicatorService indicatorService;

    /**
     * 获取最新技术指标
     */
    @GetMapping("/latest")
    public ApiResult<IndicatorEntity> getLatestIndicator(
            @RequestParam(defaultValue = "BINANCE") String exchange,
            @RequestParam String symbol,
            @RequestParam(defaultValue = "FUTURES") String marketType,
            @RequestParam(defaultValue = "1h") String interval) {

        IndicatorEntity indicator = indicatorService.getLatestIndicator(
                exchange, symbol, marketType, interval);
        return ApiResult.success(indicator);
    }

    /**
     * 手动触发指标计算
     */
    @PostMapping("/calculate")
    public ApiResult<IndicatorDTO> calculateIndicator(
            @RequestParam(defaultValue = "BINANCE") String exchange,
            @RequestParam String symbol,
            @RequestParam(defaultValue = "FUTURES") String marketType,
            @RequestParam(defaultValue = "1h") String interval) {

        IndicatorDTO result = indicatorService.calculateAndSave(exchange, symbol, marketType, interval);
        if (result != null) {
            return ApiResult.success(result);
        }
        return ApiResult.error("指标计算失败，可能K线数据不足");
    }
}
