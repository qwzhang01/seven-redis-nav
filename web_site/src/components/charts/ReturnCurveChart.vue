<template>
  <v-chart :option="chartOption" :autoresize="true" class="w-full" :style="{ height: height + 'px' }" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const props = withDefaults(defineProps<{
  data: number[]
  labels?: string[]
  height?: number
  color?: string
  showArea?: boolean
}>(), {
  height: 200,
  color: '#00d4ff',
  showArea: true,
})

const chartOption = computed(() => ({
  grid: { top: 10, right: 10, bottom: 20, left: 40 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#1a2035',
    borderColor: 'rgba(255,255,255,0.06)',
    textStyle: { color: '#e2e8f0', fontSize: 12 },
    formatter: (params: { value: number; dataIndex: number }[]) => {
      const value = params[0]?.value
      const label = props.labels?.[params[0]?.dataIndex] || `D${params[0]?.dataIndex}`
      return `时间: ${label}<br/>收益率: ${value?.toFixed(2)}%`
    },
  },
  xAxis: {
    type: 'category',
    data: props.labels || props.data.map((_, i) => `D${i}`),
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    axisTick: { show: false },
    axisLabel: { 
      show: true, 
      color: '#64748b', 
      fontSize: 11,
      formatter: (value: string) => {
        // 如果是时间格式的标签，显示更简洁的格式
        if (value.includes('-')) {
          const date = new Date(value)
          return `${date.getMonth() + 1}/${date.getDate()}`
        }
        return value
      }
    },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
    axisLabel: { color: '#64748b', fontSize: 11, formatter: '{value}%' },
  },
  series: [
    {
      type: 'line',
      data: props.data,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: props.color },
      areaStyle: props.showArea
        ? {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: `${props.color}33` },
                { offset: 1, color: `${props.color}00` },
              ],
            },
          }
        : undefined,
    },
  ],
}))
</script>