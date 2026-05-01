<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  unit?: string;
  color?: string;
}>();
</script>

<template>
  <div class="metric-card" :style="{ '--card-accent': color || '#6366f1' }">
    <div class="card-header">
      <span class="color-dot" />
      <span class="card-label">{{ label }}</span>
    </div>
    <div class="card-value">
      {{ value }}
      <span v-if="unit" class="card-unit">{{ unit }}</span>
    </div>
  </div>
</template>

<style scoped>
.metric-card {
  background: var(--srn-color-surface-2);
  border-radius: var(--srn-radius-md, 8px);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border: 1px solid var(--srn-color-border);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--card-accent);
  flex-shrink: 0;
}

.card-label {
  font-size: 11px;
  color: var(--srn-color-text-3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--srn-color-text-1);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.card-unit {
  font-size: 12px;
  font-weight: 400;
  color: var(--srn-color-text-3);
  margin-left: 2px;
}
</style>
