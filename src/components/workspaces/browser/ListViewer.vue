<script setup lang="ts">
import { computed } from 'vue';
import type { KeyDetail } from '@/types/data';
import { useDataMasking } from '@/composables/useDataMasking';

const props = defineProps<{ detail: KeyDetail; keyName?: string }>();
const { maskValue, isMasked } = useDataMasking();
const masked = computed(() => props.keyName ? isMasked(props.keyName) : false);
</script>

<template>
  <div class="list-viewer">
    <table class="lv-table">
      <thead>
        <tr>
          <th style="width: 60px;">索引</th>
          <th>值</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(item, index) in (detail.value as any).items"
          :key="index"
        >
          <td class="index-cell">{{ index }}</td>
          <td class="value-cell">{{ masked && keyName ? maskValue(keyName, String(item)) : item }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.list-viewer { overflow: auto; height: 100%; }
.lv-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.lv-table th {
  padding: 6px 12px;
  text-align: left;
  font-size: 10px;
  font-weight: 600;
  color: var(--srn-color-text-3);
  text-transform: uppercase;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
  position: sticky;
  top: 0;
}
.lv-table td { padding: 7px 12px; border-bottom: 1px solid rgba(0,0,0,0.04); }
.lv-table tr:hover td { background: rgba(0,0,0,0.02); }
.index-cell { font-family: var(--srn-font-mono); color: var(--srn-color-text-3); font-size: 11px; }
.value-cell { font-family: var(--srn-font-mono); color: var(--srn-color-text-1); }
</style>
