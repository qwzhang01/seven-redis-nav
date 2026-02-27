/**
 * 图表组件相关类型定义
 * 用于 TradingChart 等图表组件的 Props 类型
 * 
 * 注意：KlineDataPoint 已在 types/api/signal.ts 中定义并通过 types/index.ts 统一导出
 */

/**
 * 指标数据（用于图表叠加显示技术指标）
 */
export interface IndicatorData {
  /** 指标名称 */
  name: string
  /** 图表展示类型 */
  type: 'line' | 'histogram' | 'area'
  /** 指标颜色 */
  color: string
  /** 指标绘制面板：主图/副图/副图2 */
  pane: 'main' | 'sub' | 'sub2'
  /** 指标数据点 */
  data: Array<{ time: number; value: number }>
}

/**
 * 交易标记数据（用于图表上标记买卖点）
 */
export interface TradeMarkData {
  /** 时间戳 */
  time: number
  /** 标记位置：柱线上方/下方 */
  position: 'aboveBar' | 'belowBar'
  /** 标记颜色 */
  color: string
  /** 标记形状 */
  shape: 'arrowUp' | 'arrowDown' | 'circle' | 'square'
  /** 标记文字 */
  text: string
}
