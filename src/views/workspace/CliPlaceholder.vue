<template>
  <div class="workspace-placeholder">
    <i class="ri-terminal-box-line placeholder-icon" />
    <h3>命令行</h3>
    <p>执行 Redis 命令，支持自动补全</p>
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
