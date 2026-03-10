<template>
  <v-chart :option="chartOption" :autoresize="true" class="w-full" :style="{ height: height + 'px' }" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, MarkLineComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, MarkLineComponent])

const props = withDefaults(defineProps<{
  data: number[]
  labels?: string[]
  height?: number
}>(), {
  height: 200,
})

const chartOption = computed(() => ({
  grid: { top: 10, right: 10, bottom: 20, left: 45 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#1a2035',
    borderColor: 'rgba(255,255,255,0.06)',
    textStyle: { color: '#e2e8f0', fontSize: 12 },
    formatter: (params: any[]) => {
      const p = params[0]
      const label = props.labels?.[p.dataIndex] || `D${p.dataIndex}`
      return `${label}<br/>回撤: <span style="color:#ef4444">${p.value.toFixed(2)}%</span>`
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
        if (value.includes('-')) {
          const date = new Date(value)
          return `${date.getMonth() + 1}/${date.getDate()}`
        }
        return value
      },
    },
  },
  yAxis: {
    type: 'value',
    max: 0,
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
    axisLabel: { color: '#64748b', fontSize: 11, formatter: '{value}%' },
  },
  series: [
    {
      type: 'line',
      data: props.data,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 1.5, color: '#ef4444' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(239,68,68,0.05)' },
            { offset: 1, color: 'rgba(239,68,68,0.25)' },
          ],
        },
      },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: 'rgba(239,68,68,0.3)', type: 'dashed', width: 1 },
        data: [{ yAxis: Math.min(...props.data), label: { show: true, color: '#ef4444', fontSize: 10, formatter: `最大回撤: ${Math.min(...props.data).toFixed(2)}%` } }],
      },
    },
  ],
}))
</script>
