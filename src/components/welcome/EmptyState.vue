<script setup lang="ts">
defineEmits<{
  (e: 'new-connection'): void;
}>();
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">
      <i class="ri-database-2-line" />
    </div>
    <h3>还没有保存的连接</h3>
    <p>创建一个新连接，或使用右侧快速连接直接开始</p>
    <button class="new-conn-btn" @click="$emit('new-connection')">
      <i class="ri-add-line" />
      新建连接
    </button>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: var(--srn-color-surface-1);
  border: 1px solid var(--srn-color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: var(--srn-color-text-3);
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 14px;
  font-weight: 500;
  color: var(--srn-color-text-1);
  margin-bottom: 6px;
}

.empty-state p {
  font-size: 12px;
  color: var(--srn-color-text-3);
  margin-bottom: 20px;
  max-width: 240px;
  line-height: 1.5;
}

.new-conn-btn {
  height: 34px;
  padding: 0 16px;
  border: 1px dashed var(--srn-color-primary);
  border-radius: var(--srn-radius-sm);
  background: rgba(220, 56, 45, 0.04);
  color: var(--srn-color-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all var(--srn-motion-fast);
}
.new-conn-btn:hover {
  background: rgba(220, 56, 45, 0.08);
  border-style: solid;
}
</style>
