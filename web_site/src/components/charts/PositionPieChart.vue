<template>
  <v-chart :option="chartOption" :autoresize="true" class="w-full" :style="{ height: height + 'px' }" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent])

const props = withDefaults(defineProps<{
  data: Array<{ name: string; value: number; color?: string }>
  height?: number
}>(), {
  height: 220,
})

const defaultColors = ['#10b981', '#3b82f6', '#f59e0b', '#a855f7', '#ef4444', '#ec4899', '#06b6d4', '#84cc16']

const chartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: '#1a2035',
    borderColor: 'rgba(255,255,255,0.06)',
    textStyle: { color: '#e2e8f0', fontSize: 12 },
    formatter: (p: any) => `${p.name}<br/>占比: ${p.percent.toFixed(1)}%<br/>金额: $${p.value.toLocaleString()}`,
  },
  legend: {
    orient: 'vertical',
    right: 10,
    top: 'center',
    textStyle: { color: '#94a3b8', fontSize: 11 },
    itemWidth: 10,
    itemHeight: 10,
    itemGap: 8,
  },
  series: [
    {
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      label: {
        show: true,
        position: 'center',
        formatter: () => {
          const total = props.data.reduce((s, d) => s + d.value, 0)
          return `{total|$${total.toLocaleString()}}\n{label|总资产}`
        },
        rich: {
          total: { fontSize: 16, fontWeight: 'bold', color: '#fff', lineHeight: 24 },
          label: { fontSize: 11, color: '#64748b', lineHeight: 18 },
        },
      },
      itemStyle: { borderColor: '#0f1729', borderWidth: 2 },
      data: props.data.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: d.color || defaultColors[i % defaultColors.length] },
      })),
    },
  ],
}))
</script>
