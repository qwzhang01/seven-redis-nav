<template>
  <span
    class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium"
    :class="classes"
  >
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  level: 'low' | 'medium' | 'high'
}>()

const label = computed(() => {
  switch (props.level) {
    case 'low': return '低风险'
    case 'medium': return '中风险'
    case 'high': return '高风险'
  }
})

const classes = computed(() => {
  switch (props.level) {
    case 'low': return 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20'
    case 'medium': return 'bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20'
    case 'high': return 'bg-red-500/10 text-red-400 ring-1 ring-red-500/20'
  }
})
</script>
