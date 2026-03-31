package com.crypto.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.crypto.entity.AiAnalysisEntity;
import com.crypto.entity.OrderEntity;
import com.crypto.entity.PositionEntity;
import com.crypto.mapper.AiAnalysisMapper;
import com.crypto.mapper.OrderMapper;
import com.crypto.mapper.PositionMapper;
import com.crypto.model.vo.ApiResult;
import com.crypto.service.TradeExecutionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 交易API
 */
@RestController
@RequestMapping("/api/trade")
@RequiredArgsConstructor
public class TradeController {

    private final TradeExecutionService tradeExecutionService;
    private final OrderMapper orderMapper;
    private final PositionMapper positionMapper;
    private final AiAnalysisMapper aiAnalysisMapper;

    /**
     * 手动执行AI建议
     */
    @PostMapping("/execute/{analysisId}")
    public ApiResult<OrderEntity> executeAnalysis(@PathVariable Long analysisId) {
        AiAnalysisEntity analysis = aiAnalysisMapper.selectById(analysisId);
        if (analysis == null) {
            return ApiResult.error("未找到分析记录: " + analysisId);
        }
        if (analysis.getExecuted()) {
            return ApiResult.error("该分析已执行");
        }

        OrderEntity order = tradeExecutionService.executeAnalysis(analysis);
        return ApiResult.success(order);
    }

    /**
     * 查询订单列表
     */
    @GetMapping("/orders")
    public ApiResult<List<OrderEntity>> getOrders(
            @RequestParam(required = false) String exchange,
            @RequestParam(required = false) String symbol,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "50") int limit) {

        LambdaQueryWrapper<OrderEntity> wrapper = new LambdaQueryWrapper<OrderEntity>()
                .eq(exchange != null, OrderEntity::getExchange, exchange)
                .eq(symbol != null, OrderEntity::getSymbol, symbol)
                .eq(status != null, OrderEntity::getStatus, status)
                .orderByDesc(OrderEntity::getCreatedAt)
                .last("LIMIT " + limit);

        return ApiResult.success(orderMapper.selectList(wrapper));
    }

    /**
     * 查询持仓列表
     */
    @GetMapping("/positions")
    public ApiResult<List<PositionEntity>> getPositions(
            @RequestParam(required = false) String status) {

        LambdaQueryWrapper<PositionEntity> wrapper = new LambdaQueryWrapper<PositionEntity>()
                .eq(status != null, PositionEntity::getStatus, status)
                .orderByDesc(PositionEntity::getOpenedAt);

        return ApiResult.success(positionMapper.selectList(wrapper));
    }

    /**
     * 查询所有开仓持仓
     */
    @GetMapping("/positions/open")
    public ApiResult<List<PositionEntity>> getOpenPositions() {
        return ApiResult.success(positionMapper.getAllOpenPositions());
    }
}
