package com.crypto.service;

import com.crypto.config.OrderProperties;
import com.crypto.entity.AiAnalysisEntity;
import com.crypto.entity.OrderEntity;
import com.crypto.entity.PositionEntity;
import com.crypto.enums.*;
import com.crypto.exchange.ExchangeApiClient;
import com.crypto.exchange.ExchangeClientFactory;
import com.crypto.mapper.AiAnalysisMapper;
import com.crypto.mapper.OrderMapper;
import com.crypto.mapper.PositionMapper;
import com.crypto.model.dto.TickDTO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * 交易执行服务 - 根据AI分析结果执行交易操作
 *
 * 职责:
 * 1. 监听AI分析结果
 * 2. 风控检查
 * 3. 计算仓位大小
 * 4. 执行开仓/平仓/部分平仓操作
 * 5. 管理订单和持仓
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TradeExecutionService {

    private final ExchangeClientFactory exchangeClientFactory;
    private final AiAnalysisService aiAnalysisService;
    private final RiskControlService riskControlService;
    private final OrderMapper orderMapper;
    private final PositionMapper positionMapper;
    private final AiAnalysisMapper aiAnalysisMapper;
    private final OrderProperties orderProperties;

    /**
     * 定时检查未执行的AI建议并执行交易 (每30秒)
     */
    @Scheduled(fixedDelay = 30000, initialDelay = 120000)
    public void scheduleExecuteAiSuggestions() {
        if (!orderProperties.isAutoTradeEnabled()) {
            return;
        }

        List<AiAnalysisEntity> unexecuted = aiAnalysisService.getUnexecutedAnalyses(10);
        for (AiAnalysisEntity analysis : unexecuted) {
            try {
                executeAnalysis(analysis);
            } catch (Exception e) {
                log.error("执行AI交易建议异常: id={}, symbol={}", analysis.getId(), analysis.getSymbol(), e);
            }
        }
    }

    /**
     * 执行AI分析建议
     */
    @Transactional(rollbackFor = Exception.class)
    public OrderEntity executeAnalysis(AiAnalysisEntity analysis) {
        ActionType action = ActionType.fromCode(analysis.getSuggestedAction());
        String exchange = analysis.getExchange();
        String symbol = analysis.getSymbol();
        String marketType = analysis.getMarketType();

        log.info("开始执行AI交易建议: id={}, exchange={}, symbol={}, action={}, confidence={}",
                analysis.getId(), exchange, symbol, action, analysis.getConfidence());

        // 如果建议是HOLD，直接标记为已执行
        if (action == ActionType.HOLD) {
            markAnalysisExecuted(analysis.getId());
            log.info("AI建议HOLD，不执行交易: {}/{}", exchange, symbol);
            return null;
        }

        // 风控检查
        if (!riskControlService.preTradeCheck(analysis)) {
            markAnalysisExecuted(analysis.getId());
            log.warn("风控检查未通过，取消交易: {}/{}", exchange, symbol);
            return null;
        }

        // 获取交易所客户端
        ExchangeApiClient client = exchangeClientFactory.getClient(ExchangeEnum.fromCode(exchange));

        // 获取当前价格
        MarketType mt = MarketType.fromCode(marketType);
        TickDTO tick = client.getTicker(symbol, mt);
        if (tick == null) {
            log.error("获取当前价格失败: {}/{}", exchange, symbol);
            return null;
        }

        BigDecimal currentPrice = tick.getLastPrice();
        OrderEntity order = null;

        switch (action) {
            case OPEN_LONG:
                order = executeOpenPosition(client, analysis, currentPrice, PositionSide.LONG, OrderSide.BUY);
                break;
            case OPEN_SHORT:
                order = executeOpenPosition(client, analysis, currentPrice, PositionSide.SHORT, OrderSide.SELL);
                break;
            case CLOSE_LONG:
                order = executeClosePosition(client, analysis, currentPrice, PositionSide.LONG, 100);
                break;
            case CLOSE_SHORT:
                order = executeClosePosition(client, analysis, currentPrice, PositionSide.SHORT, 100);
                break;
            case PARTIAL_CLOSE_LONG:
                order = executeClosePosition(client, analysis, currentPrice, PositionSide.LONG, 50);
                break;
            case PARTIAL_CLOSE_SHORT:
                order = executeClosePosition(client, analysis, currentPrice, PositionSide.SHORT, 50);
                break;
            default:
                log.warn("未知交易动作: {}", action);
        }

        // 标记AI分析为已执行
        markAnalysisExecuted(analysis.getId());

        return order;
    }

    /**
     * 执行开仓
     */
    private OrderEntity executeOpenPosition(ExchangeApiClient client, AiAnalysisEntity analysis,
                                            BigDecimal currentPrice, PositionSide positionSide,
                                            OrderSide orderSide) {
        String exchange = analysis.getExchange();
        String symbol = analysis.getSymbol();
        MarketType marketType = MarketType.fromCode(analysis.getMarketType());

        // 检查是否已有同方向持仓
        PositionEntity existingPos = positionMapper.getOpenPosition(
                exchange, symbol, analysis.getMarketType(), positionSide.getCode());
        if (existingPos != null) {
            log.warn("已有{}持仓，不重复开仓: {}/{}, entryPrice={}", positionSide, exchange, symbol,
                    existingPos.getEntryPrice());
            return null;
        }

        // 计算下单数量
        BigDecimal balance = new BigDecimal(client.getBalance("USDT"));
        BigDecimal positionPct = analysis.getPositionPct() != null ?
                analysis.getPositionPct().divide(BigDecimal.valueOf(100), 4, RoundingMode.HALF_UP) :
                BigDecimal.valueOf(orderProperties.getMaxPositionPct() / 100.0);

        // 限制最大仓位
        BigDecimal maxPctDecimal = BigDecimal.valueOf(orderProperties.getMaxPositionPct() / 100.0);
        if (positionPct.compareTo(maxPctDecimal) > 0) {
            positionPct = maxPctDecimal;
        }

        BigDecimal orderValue = balance.multiply(positionPct);
        BigDecimal quantity = orderValue.divide(currentPrice, 6, RoundingMode.DOWN);

        if (quantity.compareTo(BigDecimal.ZERO) <= 0) {
            log.warn("计算下单数量为0: balance={}, positionPct={}", balance, positionPct);
            return null;
        }

        // 创建订单记录
        String clientOrderId = UUID.randomUUID().toString().replace("-", "");
        OrderEntity order = OrderEntity.builder()
                .exchange(exchange)
                .symbol(symbol)
                .marketType(analysis.getMarketType())
                .clientOrderId(clientOrderId)
                .analysisId(analysis.getId())
                .side(orderSide.getCode())
                .positionSide(positionSide.getCode())
                .orderType(OrderType.MARKET.getCode())
                .actionType(positionSide == PositionSide.LONG ?
                        ActionType.OPEN_LONG.getCode() : ActionType.OPEN_SHORT.getCode())
                .price(currentPrice)
                .quantity(quantity)
                .filledQty(BigDecimal.ZERO)
                .stopLoss(analysis.getStopLoss())
                .takeProfit(analysis.getTakeProfit())
                .status(OrderStatus.CREATED.getCode())
                .build();
        orderMapper.insert(order);

        try {
            // 执行下单
            String orderId = client.placeOrder(
                    symbol, marketType,
                    orderSide.getCode(),
                    marketType == MarketType.FUTURES ? positionSide.getCode() : null,
                    OrderType.MARKET.getCode(),
                    null,
                    quantity.toPlainString()
            );

            // 更新订单状态
            order.setOrderId(orderId);
            order.setStatus(OrderStatus.SUBMITTED.getCode());
            orderMapper.updateById(order);

            // 创建持仓记录
            PositionEntity position = PositionEntity.builder()
                    .exchange(exchange)
                    .symbol(symbol)
                    .marketType(analysis.getMarketType())
                    .positionSide(positionSide.getCode())
                    .entryPrice(currentPrice)
                    .quantity(quantity)
                    .unrealizedPnl(BigDecimal.ZERO)
                    .realizedPnl(BigDecimal.ZERO)
                    .leverage(1)
                    .stopLoss(analysis.getStopLoss())
                    .takeProfit(analysis.getTakeProfit())
                    .status("OPEN")
                    .openedAt(LocalDateTime.now())
                    .build();
            positionMapper.insert(position);

            log.info("开仓成功: exchange={}, symbol={}, side={}, qty={}, price={}, orderId={}",
                    exchange, symbol, positionSide, quantity, currentPrice, orderId);
            return order;

        } catch (Exception e) {
            order.setStatus(OrderStatus.REJECTED.getCode());
            order.setErrorMsg(e.getMessage());
            orderMapper.updateById(order);
            log.error("开仓失败: {}/{}", exchange, symbol, e);
            return order;
        }
    }

    /**
     * 执行平仓/部分平仓
     *
     * @param closePct 平仓百分比 (100=全部平仓, 50=平一半)
     */
    private OrderEntity executeClosePosition(ExchangeApiClient client, AiAnalysisEntity analysis,
                                             BigDecimal currentPrice, PositionSide positionSide,
                                             int closePct) {
        String exchange = analysis.getExchange();
        String symbol = analysis.getSymbol();
        MarketType marketType = MarketType.fromCode(analysis.getMarketType());

        // 查找持仓
        PositionEntity position = positionMapper.getOpenPosition(
                exchange, symbol, analysis.getMarketType(), positionSide.getCode());

        if (position == null) {
            log.warn("无{}持仓可平: {}/{}", positionSide, exchange, symbol);
            return null;
        }

        // 计算平仓数量
        BigDecimal closeQty;
        if (closePct >= 100) {
            closeQty = position.getQuantity();
        } else {
            closeQty = position.getQuantity()
                    .multiply(BigDecimal.valueOf(closePct))
                    .divide(BigDecimal.valueOf(100), 6, RoundingMode.DOWN);
        }

        // 确定平仓方向
        OrderSide closeSide = positionSide == PositionSide.LONG ? OrderSide.SELL : OrderSide.BUY;
        String actionType = closePct >= 100 ?
                (positionSide == PositionSide.LONG ?
                        ActionType.CLOSE_LONG.getCode() : ActionType.CLOSE_SHORT.getCode()) :
                (positionSide == PositionSide.LONG ?
                        ActionType.PARTIAL_CLOSE_LONG.getCode() : ActionType.PARTIAL_CLOSE_SHORT.getCode());

        // 创建订单记录
        OrderEntity order = OrderEntity.builder()
                .exchange(exchange)
                .symbol(symbol)
                .marketType(analysis.getMarketType())
                .clientOrderId(UUID.randomUUID().toString().replace("-", ""))
                .analysisId(analysis.getId())
                .side(closeSide.getCode())
                .positionSide(positionSide.getCode())
                .orderType(OrderType.MARKET.getCode())
                .actionType(actionType)
                .price(currentPrice)
                .quantity(closeQty)
                .filledQty(BigDecimal.ZERO)
                .status(OrderStatus.CREATED.getCode())
                .build();
        orderMapper.insert(order);

        try {
            String orderId = client.placeOrder(
                    symbol, marketType,
                    closeSide.getCode(),
                    marketType == MarketType.FUTURES ? positionSide.getCode() : null,
                    OrderType.MARKET.getCode(),
                    null,
                    closeQty.toPlainString()
            );

            order.setOrderId(orderId);
            order.setStatus(OrderStatus.SUBMITTED.getCode());

            // 计算盈亏
            BigDecimal pnl;
            if (positionSide == PositionSide.LONG) {
                pnl = currentPrice.subtract(position.getEntryPrice()).multiply(closeQty);
            } else {
                pnl = position.getEntryPrice().subtract(currentPrice).multiply(closeQty);
            }
            order.setPnl(pnl);
            orderMapper.updateById(order);

            // 更新持仓
            BigDecimal remainingQty = position.getQuantity().subtract(closeQty);
            if (remainingQty.compareTo(BigDecimal.ZERO) <= 0) {
                // 全部平仓
                position.setQuantity(BigDecimal.ZERO);
                position.setStatus("CLOSED");
                position.setClosedAt(LocalDateTime.now());
                position.setRealizedPnl(position.getRealizedPnl().add(pnl));
            } else {
                // 部分平仓
                position.setQuantity(remainingQty);
                position.setRealizedPnl(position.getRealizedPnl().add(pnl));
            }
            positionMapper.updateById(position);

            log.info("平仓成功: exchange={}, symbol={}, side={}, qty={}, pnl={}, orderId={}",
                    exchange, symbol, positionSide, closeQty, pnl, orderId);
            return order;

        } catch (Exception e) {
            order.setStatus(OrderStatus.REJECTED.getCode());
            order.setErrorMsg(e.getMessage());
            orderMapper.updateById(order);
            log.error("平仓失败: {}/{}", exchange, symbol, e);
            return order;
        }
    }

    private void markAnalysisExecuted(Long analysisId) {
        AiAnalysisEntity entity = aiAnalysisMapper.selectById(analysisId);
        if (entity != null) {
            entity.setExecuted(true);
            aiAnalysisMapper.updateById(entity);
        }
    }
}
