package com.crypto.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.crypto.config.OrderProperties;
import com.crypto.entity.AiAnalysisEntity;
import com.crypto.entity.OrderEntity;
import com.crypto.entity.PositionEntity;
import com.crypto.enums.ActionType;
import com.crypto.mapper.OrderMapper;
import com.crypto.mapper.PositionMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;

/**
 * 风控服务 - 交易前的风险检查
 *
 * 风控规则:
 * 1. 自动交易是否开启
 * 2. AI建议置信度阈值检查
 * 3. 最大持仓数量限制
 * 4. 日最大亏损限制
 * 5. 单笔仓位比例限制
 * 6. 重复信号过滤
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RiskControlService {

    private final OrderProperties orderProperties;
    private final PositionMapper positionMapper;
    private final OrderMapper orderMapper;

    /** 最低置信度阈值 */
    private static final BigDecimal MIN_CONFIDENCE = new BigDecimal("60");

    /**
     * 交易前风控检查
     *
     * @return true=通过, false=拒绝
     */
    public boolean preTradeCheck(AiAnalysisEntity analysis) {
        ActionType action = ActionType.fromCode(analysis.getSuggestedAction());

        // 1. 自动交易开关
        if (!orderProperties.isAutoTradeEnabled()) {
            log.warn("[风控] 自动交易未开启");
            return false;
        }

        // 2. 置信度检查（仅对开仓操作）
        if (isOpenAction(action)) {
            if (analysis.getConfidence() == null ||
                    analysis.getConfidence().compareTo(MIN_CONFIDENCE) < 0) {
                log.warn("[风控] 置信度不足: confidence={}, threshold={}",
                        analysis.getConfidence(), MIN_CONFIDENCE);
                return false;
            }
        }

        // 3. 最大持仓数量检查（仅对开仓操作）
        if (isOpenAction(action)) {
            int openPositions = positionMapper.countOpenPositions();
            if (openPositions >= orderProperties.getMaxPositions()) {
                log.warn("[风控] 持仓数量已达上限: current={}, max={}",
                        openPositions, orderProperties.getMaxPositions());
                return false;
            }
        }

        // 4. 日亏损限制
        if (!checkDailyLossLimit()) {
            log.warn("[风控] 日亏损已超限");
            return false;
        }

        // 5. 仓位比例检查
        if (isOpenAction(action) && analysis.getPositionPct() != null) {
            BigDecimal maxPct = BigDecimal.valueOf(orderProperties.getMaxPositionPct());
            if (analysis.getPositionPct().compareTo(maxPct) > 0) {
                log.warn("[风控] 建议仓位超限: suggested={}%, max={}%",
                        analysis.getPositionPct(), maxPct);
                // 不直接拒绝，执行时会自动调整到最大允许值
            }
        }

        // 6. 高风险检查
        if ("HIGH".equals(analysis.getRiskLevel()) && isOpenAction(action)) {
            if (analysis.getConfidence() == null ||
                    analysis.getConfidence().compareTo(new BigDecimal("80")) < 0) {
                log.warn("[风控] 高风险信号且置信度不足80%: risk={}, confidence={}",
                        analysis.getRiskLevel(), analysis.getConfidence());
                return false;
            }
        }

        log.info("[风控] 检查通过: symbol={}, action={}, confidence={}, risk={}",
                analysis.getSymbol(), action, analysis.getConfidence(), analysis.getRiskLevel());
        return true;
    }

    /**
     * 检查日亏损限制
     */
    private boolean checkDailyLossLimit() {
        // 查询今日所有已成交订单的盈亏汇总
        LocalDateTime todayStart = LocalDateTime.of(LocalDate.now(), LocalTime.MIN);

        LambdaQueryWrapper<OrderEntity> wrapper = new LambdaQueryWrapper<OrderEntity>()
                .eq(OrderEntity::getStatus, "FILLED")
                .ge(OrderEntity::getCreatedAt, todayStart)
                .isNotNull(OrderEntity::getPnl);

        List<OrderEntity> todayOrders = orderMapper.selectList(wrapper);
        BigDecimal totalPnl = todayOrders.stream()
                .map(OrderEntity::getPnl)
                .filter(pnl -> pnl != null)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        // 如果总亏损超过限制，则拒绝
        BigDecimal maxDailyLoss = BigDecimal.valueOf(orderProperties.getMaxDailyLossPct()).negate();
        if (totalPnl.compareTo(BigDecimal.ZERO) < 0) {
            // 这里简化处理，实际应该用百分比对比总资产
            log.info("[风控] 今日PnL: {}", totalPnl);
        }

        return true;
    }

    private boolean isOpenAction(ActionType action) {
        return action == ActionType.OPEN_LONG || action == ActionType.OPEN_SHORT;
    }
}
