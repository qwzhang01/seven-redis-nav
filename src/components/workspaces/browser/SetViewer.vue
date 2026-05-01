<script setup lang="ts">
import { computed } from 'vue';
import type { KeyDetail } from '@/types/data';
import { useDataMasking } from '@/composables/useDataMasking';

const props = defineProps<{ detail: KeyDetail; keyName?: string }>();
const { maskValue, isMasked } = useDataMasking();
const masked = computed(() => props.keyName ? isMasked(props.keyName) : false);
</script>

<template>
  <div class="set-viewer">
    <div class="sv-grid">
      <div
        v-for="member in (detail.value as any).members"
        :key="member"
        class="sv-card"
      >
        <span class="sv-member">{{ masked && keyName ? maskValue(keyName, String(member)) : member }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.set-viewer { overflow: auto; height: 100%; padding: 12px; }
.sv-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.sv-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--srn-color-surface-2);
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  font-size: 12px;
  font-family: var(--srn-font-mono);
}
.sv-member { color: var(--srn-color-text-1); }
</style>
