<template>
  <span
    class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium"
    :class="[
      status === 'running' || status === 'active' || status === 'following'
        ? 'bg-emerald-500/10 text-emerald-400'
        : 'bg-dark-200/20 text-dark-100',
    ]"
  >
    <span
      class="w-1.5 h-1.5 rounded-full"
      :class="[
        status === 'running' || status === 'active' || status === 'following'
          ? 'bg-emerald-400 animate-pulse'
          : 'bg-dark-200',
      ]"
    />
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const label = computed(() => {
  switch (props.status) {
    case 'running': return '运行中'
    case 'active': return '运行中'
    case 'following': return '跟随中'
    case 'stopped': return '已停止'
    case 'ended': return '已结束'
    default: return props.status
  }
})
</script>
