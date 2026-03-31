package com.crypto.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 持仓实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_position")
public class PositionEntity {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String exchange;
    private String symbol;
    private String marketType;
    /** 持仓方向: LONG / SHORT */
    private String positionSide;
    /** 开仓均价 */
    private BigDecimal entryPrice;
    /** 持仓数量 */
    private BigDecimal quantity;
    /** 未实现盈亏 */
    private BigDecimal unrealizedPnl;
    /** 已实现盈亏 */
    private BigDecimal realizedPnl;
    /** 杠杆 */
    private Integer leverage;
    /** 保证金 */
    private BigDecimal margin;
    /** 止损价 */
    private BigDecimal stopLoss;
    /** 止盈价 */
    private BigDecimal takeProfit;
    /** 状态: OPEN / CLOSED */
    private String status;

    private LocalDateTime openedAt;
    private LocalDateTime closedAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
