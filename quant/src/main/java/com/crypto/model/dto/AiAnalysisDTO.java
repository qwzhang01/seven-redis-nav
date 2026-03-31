package com.crypto.model.dto;

import com.crypto.enums.ActionType;
import com.crypto.enums.TrendDirection;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * AI分析结果DTO - 大模型返回的结构化投资建议
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiAnalysisDTO {

    /** 趋势方向 */
    private TrendDirection trendDirection;
    /** 置信度 0-100 */
    private BigDecimal confidence;
    /** 建议动作 */
    private ActionType suggestedAction;
    /** 建议入场价 */
    private BigDecimal entryPrice;
    /** 止损价 */
    private BigDecimal stopLoss;
    /** 止盈价 */
    private BigDecimal takeProfit;
    /** 建议仓位百分比 */
    private BigDecimal positionPct;
    /** 风险等级: LOW / MEDIUM / HIGH */
    private String riskLevel;
    /** 时间范围: SHORT_TERM / MEDIUM_TERM / LONG_TERM */
    private String timeHorizon;
    /** 分析摘要 */
    private String analysisSummary;
    /** 详细分析 */
    private String detailedAnalysis;
}
