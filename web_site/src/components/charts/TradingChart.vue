<template>
  <div class="trading-chart-wrapper" :style="{ height: height + 'px' }">
    <!-- K线主图 -->
    <div ref="mainChartRef" class="main-chart-container" :style="{ height: mainChartHeight + 'px' }"></div>
    <!-- 成交量副图 -->
    <div ref="volumeChartRef" class="volume-chart-container" :style="{ height: volumeChartHeight + 'px' }" v-if="showVolume"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type LineData,
  type HistogramData,
  type SeriesMarker,
  type Time,
  type LogicalRange,
  ColorType,
  CrosshairMode,
} from 'lightweight-charts'
import type { KlineDataPoint, IndicatorData, TradeMarkData } from '@/types'

// 重新导出类型，方便外部从组件导入（保持向后兼容）
export type { KlineDataPoint, IndicatorData, TradeMarkData }

const props = withDefaults(defineProps<{
  klineData: KlineDataPoint[]
  indicators?: IndicatorData[]
  tradeMarks?: TradeMarkData[]
  height?: number
  showVolume?: boolean
}>(), {
  indicators: () => [],
  tradeMarks: () => [],
  height: 520,
  showVolume: true,
})

const emit = defineEmits<{
  (e: 'loadMore', endTime: number): void
  (e: 'timeRangeChange', from: number, to: number): void
}>()

// ==================== 高度计算 ====================

const mainChartHeight = computed(() => props.showVolume ? Math.floor(props.height * 0.75) : props.height)
const volumeChartHeight = computed(() => props.showVolume ? props.height - mainChartHeight.value : 0)

// ==================== Refs ====================

const mainChartRef = ref<HTMLElement>()
const volumeChartRef = ref<HTMLElement>()

let mainChart: IChartApi | null = null
let volumeChart: IChartApi | null = null
let candlestickSeries: ISeriesApi<'Candlestick'> | null = null
let volumeSeries: ISeriesApi<'Histogram'> | null = null
const indicatorSeriesMap = new Map<string, ISeriesApi<any>>()
let markersPlugin: any = null
let isLoadingMore = false
let earliestTime = Infinity

// 防止同步死循环的标志
let isSyncingTimeScale = false

// ==================== 通用配置 ====================

/** 东八区时间格式化 */
function formatTime(time: number) {
  const d = new Date((time + 8 * 3600) * 1000)
  const Y = d.getUTCFullYear()
  const M = String(d.getUTCMonth() + 1).padStart(2, '0')
  const D = String(d.getUTCDate()).padStart(2, '0')
  const h = String(d.getUTCHours()).padStart(2, '0')
  const m = String(d.getUTCMinutes()).padStart(2, '0')
  return { Y, M, D, h, m }
}

function timeFormatter(time: number) {
  const { Y, M, D, h, m } = formatTime(time)
  return `${Y}-${M}-${D} ${h}:${m}`
}

function tickMarkFormatter(time: number, tickMarkType: number) {
  const { Y, M, D, h, m } = formatTime(time)
  if (tickMarkType <= 1) return `${Y}-${M}`
  if (tickMarkType === 2) return `${M}-${D}`
  return `${M}-${D} ${h}:${m}`
}

/** 通用图表布局配置 */
function getCommonOptions() {
  return {
    layout: {
      background: { type: ColorType.Solid as const, color: 'transparent' },
      textColor: 'rgba(255, 255, 255, 0.6)',
      fontSize: 11,
    },
    grid: {
      vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
      horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
    },
    crosshair: {
      mode: CrosshairMode.Normal,
      vertLine: {
        color: 'rgba(255, 255, 255, 0.2)',
        labelBackgroundColor: '#1a1a2e',
      },
      horzLine: {
        color: 'rgba(255, 255, 255, 0.2)',
        labelBackgroundColor: '#1a1a2e',
      },
    },
    rightPriceScale: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
    },
    handleScroll: {
      vertTouchDrag: false,
    },
  }
}

// ==================== 时间轴同步 ====================

/** 同步两个图表的时间轴（X轴联动） */
function syncTimeScales(source: IChartApi, target: IChartApi) {
  source.timeScale().subscribeVisibleLogicalRangeChange((logicalRange: LogicalRange | null) => {
    if (isSyncingTimeScale || !logicalRange) return
    isSyncingTimeScale = true
    target.timeScale().setVisibleLogicalRange(logicalRange)
    isSyncingTimeScale = false
  })
}

/** 同步两个图表的十字线 */
function syncCrosshair(source: IChartApi, target: IChartApi, targetSeries: ISeriesApi<any> | null) {
  source.subscribeCrosshairMove((param) => {
    if (!param || !param.time) {
      target.clearCrosshairPosition()
      return
    }
    if (targetSeries) {
      const dataPoint = param.seriesData.get(targetSeries as any)
      if (dataPoint) {
        target.setCrosshairPosition((dataPoint as any).value ?? (dataPoint as any).close ?? 0, param.time, targetSeries)
        return
      }
    }
    // 如果目标系列没数据点，仍然设置十字线的时间位置
    target.clearCrosshairPosition()
  })
}

// ==================== 初始化图表 ====================

function initChart() {
  if (!mainChartRef.value) return

  // === 主图（K线） ===
  mainChart = createChart(mainChartRef.value, {
    ...getCommonOptions(),
    localization: {
      timeFormatter,
    },
    timeScale: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
      timeVisible: true,
      secondsVisible: false,
      barSpacing: 8,
      tickMarkFormatter,
    },
  })

  // 蜡烛图系列
  candlestickSeries = mainChart.addSeries(CandlestickSeries, {
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderUpColor: '#26a69a',
    borderDownColor: '#ef5350',
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
  })

  // 创建标记插件
  markersPlugin = createSeriesMarkers(candlestickSeries, [])

  // 监听可见范围变化，支持拖动加载历史
  mainChart.timeScale().subscribeVisibleLogicalRangeChange((logicalRange) => {
    if (!logicalRange || isLoadingMore) return
    if (logicalRange.from < 10 && earliestTime < Infinity) {
      isLoadingMore = true
      emit('loadMore', earliestTime)
      setTimeout(() => { isLoadingMore = false }, 1000)
    }
  })

  // 监听可见时间范围变化
  mainChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
    if (timeRange) {
      emit('timeRangeChange', timeRange.from as number, timeRange.to as number)
    }
  })

  // === 副图（成交量） ===
  if (props.showVolume && volumeChartRef.value) {
    volumeChart = createChart(volumeChartRef.value, {
      ...getCommonOptions(),
      localization: {
        timeFormatter,
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: true,
        secondsVisible: false,
        barSpacing: 8,
        tickMarkFormatter,
        // 隐藏副图的X轴标签（由主图展示）
        visible: false,
      },
    })

    volumeSeries = volumeChart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'right',
    })

    // 同步两个图表的时间轴
    syncTimeScales(mainChart, volumeChart)
    syncTimeScales(volumeChart, mainChart)

    // 同步十字线
    syncCrosshair(mainChart, volumeChart, volumeSeries)
    syncCrosshair(volumeChart, mainChart, candlestickSeries)
  }

  // === 自适应大小 ===
  const resizeObserver = new ResizeObserver(() => {
    if (mainChart && mainChartRef.value) {
      mainChart.applyOptions({ width: mainChartRef.value.clientWidth })
    }
    if (volumeChart && volumeChartRef.value) {
      volumeChart.applyOptions({ width: volumeChartRef.value.clientWidth })
    }
  })
  if (mainChartRef.value) resizeObserver.observe(mainChartRef.value)
}

// ==================== 数据更新方法 ====================

function updateKlineData(data: KlineDataPoint[]) {
  if (!candlestickSeries || !mainChart || data.length === 0) return

  try {
    const candleData: CandlestickData[] = data.map((d) => ({
      time: d.time as Time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }))
    candlestickSeries.setData(candleData)

    // 更新最早时间
    if (data.length > 0) {
      earliestTime = Math.min(earliestTime, data[0].time)
    }

    // 更新成交量
    if (volumeSeries) {
      const volData: HistogramData[] = data.map((d) => ({
        time: d.time as Time,
        value: d.volume,
        color: d.close >= d.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
      }))
      volumeSeries.setData(volData)
    }
  } catch (e) {
    console.warn('[TradingChart] updateKlineData 异常（可能由周期切换竞态引起）:', e)
  }
}

function updateIndicators(indicators: IndicatorData[]) {
  if (!mainChart) return

  try {
    // 清除旧的指标系列
    indicatorSeriesMap.forEach((series) => {
      mainChart?.removeSeries(series)
    })
    indicatorSeriesMap.clear()

    for (const indicator of indicators) {
      if (indicator.pane === 'main') {
        // 主图叠加指标
        if (indicator.type === 'line') {
          const series = mainChart.addSeries(LineSeries, {
            color: indicator.color,
            lineWidth: 1,
            title: indicator.name,
            priceScaleId: 'right',
          })
          const lineData: LineData[] = indicator.data.map((d) => ({
            time: d.time as Time,
            value: d.value,
          }))
          series.setData(lineData)
          indicatorSeriesMap.set(indicator.name, series)
        }
      } else {
        // 副图指标（仍然叠加在主图底部区域）
        const priceScaleId = indicator.pane === 'sub' ? 'indicator_sub' : 'indicator_sub2'

        if (indicator.type === 'line') {
          const series = mainChart.addSeries(LineSeries, {
            color: indicator.color,
            lineWidth: 1,
            title: indicator.name,
            priceScaleId,
          })
          mainChart.priceScale(priceScaleId).applyOptions({
            scaleMargins: { top: 0.75, bottom: 0.02 },
          })
          const lineData: LineData[] = indicator.data.map((d) => ({
            time: d.time as Time,
            value: d.value,
          }))
          series.setData(lineData)
          indicatorSeriesMap.set(indicator.name, series)
        } else if (indicator.type === 'histogram') {
          const series = mainChart.addSeries(HistogramSeries, {
            color: indicator.color,
            title: indicator.name,
            priceScaleId,
          })
          mainChart.priceScale(priceScaleId).applyOptions({
            scaleMargins: { top: 0.75, bottom: 0.02 },
          })
          const histData: HistogramData[] = indicator.data.map((d) => ({
            time: d.time as Time,
            value: d.value,
            color: d.value >= 0 ? '#26a69a' : '#ef5350',
          }))
          series.setData(histData)
          indicatorSeriesMap.set(indicator.name, series)
        }
      }
    }
  } catch (e) {
    console.warn('[TradingChart] updateIndicators 异常（可能由周期切换竞态引起）:', e)
  }
}

function updateTradeMarks(marks: TradeMarkData[]) {
  if (!candlestickSeries || !markersPlugin || marks.length === 0) return

  const markers: SeriesMarker<Time>[] = marks.map((m) => ({
    time: m.time as Time,
    position: m.position,
    color: m.color,
    shape: m.shape,
    text: m.text,
  }))

  // 按时间排序
  markers.sort((a, b) => (a.time as number) - (b.time as number))
  markersPlugin.setMarkers(markers)
}

/**
 * 追加实时K线数据（WebSocket推送）
 */
function appendKline(kline: KlineDataPoint) {
  if (!candlestickSeries || !mainChart) return

  try {
    candlestickSeries.update({
      time: kline.time as Time,
      open: kline.open,
      high: kline.high,
      low: kline.low,
      close: kline.close,
    })

    if (volumeSeries) {
      volumeSeries.update({
        time: kline.time as Time,
        value: kline.volume,
        color: kline.close >= kline.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
      })
    }
  } catch (e) {
    console.warn('[TradingChart] appendKline 异常（WebSocket kline推送触发，周期切换竞态）:', e)
  }
}

/**
 * 追加实时指标数据（WebSocket推送）
 */
function appendIndicator(name: string, point: { time: number; value: number }) {
  const series = indicatorSeriesMap.get(name)
  if (!series) return

  series.update({
    time: point.time as Time,
    value: point.value,
  })
}

/**
 * 前置插入历史K线数据（拖动加载）
 */
function prependKlineData(data: KlineDataPoint[]) {
  if (!candlestickSeries || data.length === 0) return

  const existingData = props.klineData
  const merged = [...data, ...existingData]

  const uniqueMap = new Map<number, KlineDataPoint>()
  merged.forEach((d) => uniqueMap.set(d.time, d))
  const sorted = Array.from(uniqueMap.values()).sort((a, b) => a.time - b.time)

  updateKlineData(sorted)

  if (data.length > 0) {
    earliestTime = Math.min(earliestTime, data[0].time)
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  nextTick(() => {
    initChart()
    if (props.klineData.length > 0) {
      updateKlineData(props.klineData)
    }
    if (props.indicators.length > 0) {
      updateIndicators(props.indicators)
    }
    if (props.tradeMarks.length > 0) {
      updateTradeMarks(props.tradeMarks)
    }
  })
})

onBeforeUnmount(() => {
  if (mainChart) {
    mainChart.remove()
    mainChart = null
  }
  if (volumeChart) {
    volumeChart.remove()
    volumeChart = null
  }
  indicatorSeriesMap.clear()
})

// ==================== Watch ====================

watch(
  () => props.klineData,
  (data) => {
    if (data.length > 0) updateKlineData(data)
  },
  { deep: true }
)

watch(
  () => props.indicators,
  (data) => {
    updateIndicators(data)
  },
  { deep: true }
)

watch(
  () => props.tradeMarks,
  (data) => {
    if (data.length > 0) updateTradeMarks(data)
  },
  { deep: true }
)

// ==================== 暴露方法 ====================

defineExpose({
  appendKline,
  appendIndicator,
  prependKlineData,
  updateTradeMarks,
})
</script>

<style scoped>
.trading-chart-wrapper {
  width: 100%;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.main-chart-container {
  width: 100%;
  position: relative;
  /* 主图与成交量图之间的分隔线 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.volume-chart-container {
  width: 100%;
  position: relative;
}

/* lightweight-charts 容器内部样式覆盖 */
.trading-chart-wrapper :deep(table) {
  border: none !important;
}
</style>
