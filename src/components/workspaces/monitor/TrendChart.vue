<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, shallowRef } from 'vue';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

const props = defineProps<{
  data: number[];
  color?: string;
  label?: string;
}>();

const chartRef = ref<HTMLDivElement | null>(null);
const chart = shallowRef<echarts.ECharts | null>(null);

onMounted(() => {
  if (chartRef.value) {
    chart.value = echarts.init(chartRef.value);
    updateChart();
  }

  const ro = new ResizeObserver(() => {
    chart.value?.resize();
  });
  if (chartRef.value) {
    ro.observe(chartRef.value);
  }

  onUnmounted(() => {
    ro.disconnect();
    chart.value?.dispose();
    chart.value = null;
  });
});

watch(() => props.data, updateChart, { deep: true });

function updateChart() {
  if (!chart.value) return;

  const color = props.color || '#6366f1';
  const labels = props.data.map((_, i) => i + 1);

  chart.value.setOption({
    grid: {
      top: 8,
      right: 8,
      bottom: 20,
      left: 36,
    },
    tooltip: {
      trigger: 'axis',
      confine: true,
      textStyle: { fontSize: 11 },
    },
    xAxis: {
      type: 'category',
      data: labels,
      show: false,
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: {
        fontSize: 10,
        color: '#999',
        formatter: (val: number) => formatCompact(val),
      },
    },
    series: [
      {
        type: 'line',
        data: props.data,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color + '40' },
            { offset: 1, color: color + '05' },
          ]),
        },
        emphasis: {
          itemStyle: {
            color,
            borderColor: '#fff',
            borderWidth: 2,
          },
        },
      },
    ],
  }, true);
}

function formatCompact(val: number): string {
  if (val >= 1_000_000_000) return (val / 1_000_000_000).toFixed(1) + 'G';
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + 'M';
  if (val >= 1_000) return (val / 1_000).toFixed(1) + 'K';
  return String(val);
}
</script>

<template>
  <div ref="chartRef" class="trend-chart" />
</template>

<style scoped>
.trend-chart {
  width: 100%;
  height: 100%;
  min-height: 100px;
}
</style>
