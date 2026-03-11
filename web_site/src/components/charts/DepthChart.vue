<template>
  <div class="depth-chart-wrapper" :style="{ height: height + 'px' }">
    <div ref="chartRef" class="depth-chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import {
  createChart,
  AreaSeries,
  type IChartApi,
  type ISeriesApi,
  type AreaData,
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
let bidSeries: ISeriesApi<'Area'> | null = null
let askSeries: ISeriesApi<'Area'> | null = null

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

  // 创建买单深度系列（绿色）- 使用面积图
  bidSeries = chart.addSeries(AreaSeries, {
    lineColor: '#26a69a',
    topColor: 'rgba(38, 166, 154, 0.4)',
    bottomColor: 'rgba(38, 166, 154, 0.1)',
    lineWidth: 2,
    title: '买单深度',
  })

  // 创建卖单深度系列（红色）- 使用面积图
  askSeries = chart.addSeries(AreaSeries, {
    lineColor: '#ef5350',
    topColor: 'rgba(239, 83, 80, 0.4)',
    bottomColor: 'rgba(239, 83, 80, 0.1)',
    lineWidth: 2,
    title: '卖单深度',
  })

  // 监听十字线移动
  chart.subscribeCrosshairMove((param) => {
    if (!param || !param.time) return
    
    const bidPoint = param.seriesData.get(bidSeries!)
    const askPoint = param.seriesData.get(askSeries!)
    
    if (bidPoint) {
      // 对于买单：Y轴是价格，X轴是累积数量
      emit('crosshairMove', (bidPoint as AreaData).value, param.time as number)
    } else if (askPoint) {
      // 对于卖单：Y轴是价格，X轴是累积数量
      emit('crosshairMove', (askPoint as AreaData).value, param.time as number)
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

  // 处理买单深度数据（按价格降序排列，累加数量）
  const bidData: AreaData[] = []
  let bidTotal = 0
  
  // 为买单创建时间戳（累积数量作为时间轴，确保升序排列）
  bids
    .sort((a, b) => b.price - a.price) // 价格降序排列（从高到低）
    .forEach((bid) => {
      bidTotal += bid.amount
      bidData.push({
        time: bidTotal as Time, // 累积数量作为时间轴（X轴）
        value: bid.price,        // 价格作为Y轴
      })
    })

  // 处理卖单深度数据（按价格升序排列，累加数量）
  const askData: AreaData[] = []
  let askTotal = 0
  
  // 为卖单创建时间戳（累积数量作为时间轴，确保升序排列）
  asks
    .sort((a, b) => a.price - b.price) // 价格升序排列（从低到高）
    .forEach((ask) => {
      askTotal += ask.amount
      askData.push({
        time: askTotal as Time, // 累积数量作为时间轴（X轴）
        value: ask.price,       // 价格作为Y轴
      })
    })

  bidSeries.setData(bidData)
  askSeries.setData(askData)

  // 自动调整数量范围以显示所有数据
  if (bidData.length > 0 && askData.length > 0) {
    const maxAmount = Math.max(
      bidData[bidData.length - 1].time as number,
      askData[askData.length - 1].time as number
    )
    
    chart?.timeScale().setVisibleLogicalRange({
      from: -maxAmount * 0.1,
      to: maxAmount + maxAmount * 0.1,
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