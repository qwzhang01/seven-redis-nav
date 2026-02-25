<template>
  <v-chart :option="chartOption" :autoresize="true" class="w-full" :style="{ height: height + 'px' }" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])

const props = withDefaults(defineProps<{
  data: number[]
  labels: string[]
  height?: number
}>(), {
  height: 220,
})

const chartOption = computed(() => ({
  grid: { top: 10, right: 10, bottom: 24, left: 45 },
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#1a2035',
    borderColor: 'rgba(255,255,255,0.06)',
    textStyle: { color: '#e2e8f0', fontSize: 12 },
    formatter: (params: any[]) => {
      const p = params[0]
      return `${p.name}<br/>收益: <span style="color:${p.value >= 0 ? '#10b981' : '#ef4444'}">${p.value >= 0 ? '+' : ''}${p.value.toFixed(2)}%</span>`
    },
  },
  xAxis: {
    type: 'category',
    data: props.labels,
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    axisTick: { show: false },
    axisLabel: { color: '#64748b', fontSize: 10, rotate: 30 },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
    axisLabel: { color: '#64748b', fontSize: 11, formatter: '{value}%' },
  },
  series: [
    {
      type: 'bar',
      data: props.data.map(v => ({
        value: v,
        itemStyle: {
          color: v >= 0 ? '#10b981' : '#ef4444',
          borderRadius: v >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3],
        },
      })),
      barWidth: '60%',
    },
  ],
}))
</script>
