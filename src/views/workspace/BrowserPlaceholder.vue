<template>
  <div class="workspace-placeholder">
    <i class="ri-file-list-3-line placeholder-icon" />
    <h3>键浏览器</h3>
    <p>浏览和管理 Redis 键值数据</p>
  </div>
</template>

<style scoped>
.workspace-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--srn-color-text-3);
  gap: 8px;
}
.placeholder-icon { font-size: 48px; opacity: 0.3; }
h3 { font-size: 16px; font-weight: 500; color: var(--srn-color-text-2); }
p { font-size: 13px; }
</style>
