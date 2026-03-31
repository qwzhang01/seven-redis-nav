package com.crypto.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 订单实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_order")
public class OrderEntity {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String exchange;
    private String symbol;
    private String marketType;
    /** 交易所订单ID */
    private String orderId;
    /** 客户端订单ID */
    private String clientOrderId;
    /** 关联的AI分析ID */
    private Long analysisId;
    /** 买卖方向: BUY / SELL */
    private String side;
    /** 持仓方向: LONG / SHORT */
    private String positionSide;
    /** 订单类型 */
    private String orderType;
    /** 动作类型 */
    private String actionType;
    /** 委托价格 */
    private BigDecimal price;
    /** 委托数量 */
    private BigDecimal quantity;
    /** 已成交数量 */
    private BigDecimal filledQty;
    /** 成交均价 */
    private BigDecimal avgPrice;
    /** 止损价 */
    private BigDecimal stopLoss;
    /** 止盈价 */
    private BigDecimal takeProfit;
    /** 状态 */
    private String status;
    /** 手续费 */
    private BigDecimal fee;
    /** 手续费币种 */
    private String feeAsset;
    /** 盈亏 */
    private BigDecimal pnl;
    /** 错误信息 */
    private String errorMsg;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
