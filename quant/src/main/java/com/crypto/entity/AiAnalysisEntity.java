package com.crypto.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * AI分析结果实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_ai_analysis")
public class AiAnalysisEntity {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String exchange;
    private String symbol;
    private String marketType;
    private Long analysisTime;

    /** 趋势方向: BULLISH / BEARISH / NEUTRAL */
    private String trendDirection;
    /** 置信度 0-100 */
    private BigDecimal confidence;
    /** 信号类型: BUY / SELL / HOLD */
    private String signalType;
    /** 建议动作 */
    private String suggestedAction;
    /** 建议入场价 */
    private BigDecimal entryPrice;
    /** 止损价 */
    private BigDecimal stopLoss;
    /** 止盈价 */
    private BigDecimal takeProfit;
    /** 建议仓位百分比 */
    private BigDecimal positionPct;
    /** 风险等级 */
    private String riskLevel;
    /** 时间范围 */
    private String timeHorizon;
    /** 分析摘要 */
    private String analysisSummary;
    /** 详细分析 */
    private String detailedAnalysis;
    /** 使用的指标JSON */
    private String indicatorsUsed;
    /** AI模型名称 */
    private String modelName;
    /** AI原始响应 */
    private String rawResponse;
    /** 是否已执行 */
    private Boolean executed;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
