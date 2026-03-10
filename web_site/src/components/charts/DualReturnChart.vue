<template>
  <v-chart :option="chartOption" :autoresize="true" class="w-full" :style="{ height: height + 'px' }" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const props = withDefaults(defineProps<{
  data1: number[]
  data2: number[]
  labels?: string[]
  height?: number
  color1?: string
  color2?: string
  name1?: string
  name2?: string
}>(), {
  height: 280,
  color1: '#10b981',
  color2: '#3b82f6',
  name1: '我的跟单',
  name2: '信号源',
})

const chartOption = computed(() => ({
  grid: { top: 35, right: 10, bottom: 20, left: 45 },
  legend: {
    show: true,
    top: 0,
    right: 0,
    textStyle: { color: '#94a3b8', fontSize: 11 },
    itemWidth: 16,
    itemHeight: 2,
  },
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#1a2035',
    borderColor: 'rgba(255,255,255,0.06)',
    textStyle: { color: '#e2e8f0', fontSize: 12 },
    formatter: (params: any[]) => {
      const label = props.labels?.[params[0]?.dataIndex] || `D${params[0]?.dataIndex}`
      let html = `<div style="margin-bottom:4px">${label}</div>`
      params.forEach((p: any) => {
        html += `<div style="display:flex;align-items:center;gap:6px"><span style="width:8px;height:2px;background:${p.color};display:inline-block"></span>${p.seriesName}: ${p.value?.toFixed(2)}%</div>`
      })
      return html
    },
  },
  xAxis: {
    type: 'category',
    data: props.labels || props.data1.map((_, i) => `D${i}`),
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
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
    axisLabel: { color: '#64748b', fontSize: 11, formatter: '{value}%' },
  },
  series: [
    {
      name: props.name1,
      type: 'line',
      data: props.data1,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: props.color1 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: `${props.color1}22` },
            { offset: 1, color: `${props.color1}00` },
          ],
        },
      },
    },
    {
      name: props.name2,
      type: 'line',
      data: props.data2,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: props.color2, type: 'dashed' },
    },
  ],
}))
</script>
