<template>
  <div ref="chartContainerRef" class="trading-chart-container" :style="{ height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
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
  height: 500,
  showVolume: true,
})

const emit = defineEmits<{
  (e: 'loadMore', endTime: number): void
  (e: 'timeRangeChange', from: number, to: number): void
}>()

// ==================== Refs ====================

const chartContainerRef = ref<HTMLElement>()
let chart: IChartApi | null = null
let candlestickSeries: ISeriesApi<'Candlestick'> | null = null
let volumeSeries: ISeriesApi<'Histogram'> | null = null
const indicatorSeriesMap = new Map<string, ISeriesApi<any>>()
let markersPlugin: any = null
let isLoadingMore = false
let earliestTime = Infinity

// ==================== 初始化图表 ====================

function initChart() {
  if (!chartContainerRef.value) return

  chart = createChart(chartContainerRef.value, {
    layout: {
      background: { type: ColorType.Solid, color: 'transparent' },
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
    timeScale: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
      timeVisible: true,
      secondsVisible: false,
      barSpacing: 8,
    },
    rightPriceScale: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
    },
    handleScroll: {
      vertTouchDrag: false,
    },
  })

  // 蜡烛图系列
  candlestickSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderUpColor: '#26a69a',
    borderDownColor: '#ef5350',
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
  })

  // 创建标记插件
  markersPlugin = createSeriesMarkers(candlestickSeries, [])

  // 成交量系列
  if (props.showVolume) {
    volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    })

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    })
  }

  // 监听可见范围变化，支持拖动加载历史
  chart.timeScale().subscribeVisibleLogicalRangeChange((logicalRange) => {
    if (!logicalRange || isLoadingMore) return

    // 当用户向左拖动，且可见范围的左侧接近数据起始处时，触发加载更多
    if (logicalRange.from < 10 && earliestTime < Infinity) {
      isLoadingMore = true
      emit('loadMore', earliestTime)
      // 延迟重置，防止频繁触发
      setTimeout(() => {
        isLoadingMore = false
      }, 1000)
    }
  })

  // 监听可见时间范围变化
  chart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
    if (timeRange) {
      emit('timeRangeChange', timeRange.from as number, timeRange.to as number)
    }
  })

  // 自适应大小
  const resizeObserver = new ResizeObserver(() => {
    if (chart && chartContainerRef.value) {
      chart.applyOptions({
        width: chartContainerRef.value.clientWidth,
      })
    }
  })
  resizeObserver.observe(chartContainerRef.value)
}

// ==================== 数据更新方法 ====================

function updateKlineData(data: KlineDataPoint[]) {
  if (!candlestickSeries || data.length === 0) return

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
      color: d.close >= d.open ? 'rgba(38, 166, 154, 0.4)' : 'rgba(239, 83, 80, 0.4)',
    }))
    volumeSeries.setData(volData)
  }
}

function updateIndicators(indicators: IndicatorData[]) {
  if (!chart) return

  // 清除旧的指标系列
  indicatorSeriesMap.forEach((series) => {
    chart?.removeSeries(series)
  })
  indicatorSeriesMap.clear()

  for (const indicator of indicators) {
    if (indicator.pane === 'main') {
      // 主图叠加指标
      if (indicator.type === 'line') {
        const series = chart.addSeries(LineSeries, {
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
      // 副图指标
      const priceScaleId = indicator.pane === 'sub' ? 'indicator_sub' : 'indicator_sub2'

      if (indicator.type === 'line') {
        const series = chart.addSeries(LineSeries, {
          color: indicator.color,
          lineWidth: 1,
          title: indicator.name,
          priceScaleId,
        })
        chart.priceScale(priceScaleId).applyOptions({
          scaleMargins: { top: 0.75, bottom: 0.02 },
        })
        const lineData: LineData[] = indicator.data.map((d) => ({
          time: d.time as Time,
          value: d.value,
        }))
        series.setData(lineData)
        indicatorSeriesMap.set(indicator.name, series)
      } else if (indicator.type === 'histogram') {
        const series = chart.addSeries(HistogramSeries, {
          color: indicator.color,
          title: indicator.name,
          priceScaleId,
        })
        chart.priceScale(priceScaleId).applyOptions({
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
  if (!candlestickSeries) return

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
      color: kline.close >= kline.open ? 'rgba(38, 166, 154, 0.4)' : 'rgba(239, 83, 80, 0.4)',
    })
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

  // 获取当前数据并合并
  const existingData = props.klineData
  const merged = [...data, ...existingData]

  // 去重并排序
  const uniqueMap = new Map<number, KlineDataPoint>()
  merged.forEach((d) => uniqueMap.set(d.time, d))
  const sorted = Array.from(uniqueMap.values()).sort((a, b) => a.time - b.time)

  updateKlineData(sorted)

  // 更新最早时间
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
  if (chart) {
    chart.remove()
    chart = null
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
.trading-chart-container {
  width: 100%;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
}

/* lightweight-charts 容器内部样式覆盖 */
.trading-chart-container :deep(table) {
  border: none !important;
}
</style>
