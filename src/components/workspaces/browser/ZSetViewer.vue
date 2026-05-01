<script setup lang="ts">
import { computed } from 'vue';
import type { KeyDetail } from '@/types/data';
import { useDataMasking } from '@/composables/useDataMasking';

const props = defineProps<{ detail: KeyDetail; keyName?: string }>();
const { maskValue, isMasked } = useDataMasking();
const masked = computed(() => props.keyName ? isMasked(props.keyName) : false);
</script>

<template>
  <div class="zset-viewer">
    <table class="zv-table">
      <thead>
        <tr>
          <th style="width: 80px;">分数</th>
          <th>成员</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="[score, member] in (detail.value as any).members"
          :key="member"
        >
          <td class="score-cell">{{ score }}</td>
          <td class="member-cell">{{ masked && keyName ? maskValue(keyName, String(member)) : member }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.zset-viewer { overflow: auto; height: 100%; }
.zv-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.zv-table th {
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
.zv-table td { padding: 7px 12px; border-bottom: 1px solid rgba(0,0,0,0.04); }
.zv-table tr:hover td { background: rgba(0,0,0,0.02); }
.score-cell { font-family: var(--srn-font-mono); color: var(--srn-color-info); font-weight: 500; }
.member-cell { font-family: var(--srn-font-mono); color: var(--srn-color-text-1); }
</style>
