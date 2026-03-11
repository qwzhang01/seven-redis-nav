<template>
  <div class="volume-chart-wrapper" :style="{ height: height + 'px' }">
    <div ref="chartRef" class="volume-chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import {
  createChart,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
  type HistogramData,
  type Time,
  ColorType,
  CrosshairMode,
} from 'lightweight-charts'

const props = defineProps<{
  volumeData: Array<{ time: number; value: number }>
  height?: number
}>()

const emit = defineEmits<{
  (e: 'crosshairMove', time: number, value: number): void
}>()

const chartRef = ref<HTMLElement>()
let chart: IChartApi | null = null
let volumeSeries: ISeriesApi<'Histogram'> | null = null

// 初始化图表
function initChart() {
  if (!chartRef.value) return

  chart = createChart(chartRef.value, {
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
    rightPriceScale: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
    },
    leftPriceScale: {
      visible: false,
    },
    timeScale: {
      borderColor: 'rgba(255, 255, 255, 0.08)',
      timeVisible: true,
      secondsVisible: false,
    },
  })

  // 创建成交量柱状图系列
  volumeSeries = chart.addSeries(HistogramSeries, {
    color: '#26a69a',
    priceFormat: {
      type: 'volume',
    },
    priceScaleId: 'volume',
  })

  // 设置成交量价格刻度
  chart.priceScale('volume').applyOptions({
    scaleMargins: {
      top: 0.8,
      bottom: 0,
    },
  })

  // 处理十字线移动事件
  chart.subscribeCrosshairMove(param => {
    if (param.time && volumeSeries) {
      const volumePoint = param.seriesData.get(volumeSeries)
      if (volumePoint) {
        emit('crosshairMove', param.time as number, (volumePoint as HistogramData).value)
      }
    }
  })

  // 自适应大小
  const resizeObserver = new ResizeObserver(() => {
    if (chart && chartRef.value) {
      chart.applyOptions({ width: chartRef.value.clientWidth })
    }
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
}

// 更新成交量数据
function updateVolumeData() {
  if (!volumeSeries || !props.volumeData) return

  const volumeData: HistogramData[] = props.volumeData.map(item => ({
    time: item.time as Time,
    value: item.value,
    color: item.value >= 0 ? '#26a69a' : '#ef5350',
  }))

  volumeSeries.setData(volumeData)
}

// 生命周期
onMounted(async () => {
  await nextTick()
  initChart()
  updateVolumeData()
})

onBeforeUnmount(() => {
  if (chart) {
    chart.remove()
    chart = null
  }
})

// 监听数据变化
watch(() => props.volumeData, () => {
  updateVolumeData()
}, { deep: true })

// 监听高度变化
watch(() => props.height, (newHeight) => {
  if (chart && newHeight) {
    chart.applyOptions({ height: newHeight })
  }
})
</script>

<style scoped>
.volume-chart-wrapper {
  width: 100%;
  position: relative;
}

.volume-chart-container {
  width: 100%;
  height: 100%;
}
</style>