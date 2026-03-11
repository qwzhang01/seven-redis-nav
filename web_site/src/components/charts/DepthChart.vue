<template>
  <div class="depth-chart-wrapper" :style="{ height: height + 'px' }">
    <div ref="chartRef" class="depth-chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import {
  createChart,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type Time,
  ColorType,
  CrosshairMode,
} from 'lightweight-charts'

const props = defineProps<{
  depthData: {
    bids: Array<{ price: number; amount: number }>
    asks: Array<{ price: number; amount: number }>
  }
  height?: number
}>()

const emit = defineEmits<{
  (e: 'crosshairMove', price: number, amount: number): void
}>()

const chartRef = ref<HTMLElement>()
let chart: IChartApi | null = null
let bidSeries: ISeriesApi<'Line'> | null = null
let askSeries: ISeriesApi<'Line'> | null = null

// 默认高度
const height = ref(props.height || 200)

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
      timeVisible: false,
      secondsVisible: false,
    },
  })

  // 创建买单深度系列（绿色）
  bidSeries = chart.addSeries(LineSeries, {
    color: '#26a69a',
    lineWidth: 2,
    title: '买单深度',
  })

  // 创建卖单深度系列（红色）
  askSeries = chart.addSeries(LineSeries, {
    color: '#ef5350',
    lineWidth: 2,
    title: '卖单深度',
  })

  // 监听十字线移动
  chart.subscribeCrosshairMove((param) => {
    if (!param || !param.time) return
    
    const bidPoint = param.seriesData.get(bidSeries!)
    const askPoint = param.seriesData.get(askSeries!)
    
    if (bidPoint) {
      emit('crosshairMove', (bidPoint as LineData).value, param.time as number)
    } else if (askPoint) {
      emit('crosshairMove', (askPoint as LineData).value, param.time as number)
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

// 更新深度数据
function updateDepthData() {
  if (!bidSeries || !askSeries || !props.depthData) return

  const { bids, asks } = props.depthData

  // 处理买单深度数据（按价格升序排列，累加数量）
  const bidData: LineData[] = []
  let bidTotal = 0
  bids
    .sort((a, b) => a.price - b.price)
    .forEach(bid => {
      bidTotal += bid.amount
      bidData.push({
        time: bid.price as Time,
        value: bidTotal,
      })
    })

  // 处理卖单深度数据（按价格升序排列，累加数量）
  const askData: LineData[] = []
  let askTotal = 0
  asks
    .sort((a, b) => a.price - b.price)
    .forEach(ask => {
      askTotal += ask.amount
      askData.push({
        time: ask.price as Time,
        value: askTotal,
      })
    })

  bidSeries.setData(bidData)
  askSeries.setData(askData)

  // 自动调整价格范围以显示所有数据
  if (bidData.length > 0 && askData.length > 0) {
    const minPrice = Math.min(bidData[0].time as number, askData[0].time as number)
    const maxPrice = Math.max(
      bidData[bidData.length - 1].time as number,
      askData[askData.length - 1].time as number
    )
    
    chart?.timeScale().setVisibleLogicalRange({
      from: minPrice - (maxPrice - minPrice) * 0.1,
      to: maxPrice + (maxPrice - minPrice) * 0.1,
    })
  }
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    initChart()
    if (props.depthData) {
      updateDepthData()
    }
  })
})

onBeforeUnmount(() => {
  if (chart) {
    chart.remove()
    chart = null
  }
})

// 监听数据变化
watch(() => props.depthData, () => {
  updateDepthData()
}, { deep: true })

// 暴露方法供外部调用
defineExpose({
  updateDepthData,
})
</script>

<style scoped>
.depth-chart-wrapper {
  width: 100%;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
}

.depth-chart-container {
  width: 100%;
  height: 100%;
}
</style>