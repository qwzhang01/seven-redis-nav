<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="settings-overlay" @click.self="$emit('close')">
        <div class="settings-modal">
          <!-- Sidebar -->
          <div class="settings-sidebar">
            <div class="settings-title">设置</div>
            <nav class="settings-nav">
              <button
                v-for="item in navItems"
                :key="item.id"
                :class="['nav-item', { active: activeSection === item.id }]"
                @click="activeSection = item.id"
              >
                <i :class="item.icon" />
                {{ item.label }}
              </button>
            </nav>
          </div>

          <!-- Content -->
          <div class="settings-content">
            <button class="close-btn" @click="$emit('close')"><i class="ri-close-line" /></button>
            <DataMaskingPanel v-if="activeSection === 'masking'" />
            <ShortcutCustomPanel v-else-if="activeSection === 'shortcuts'" />
            <div v-else class="placeholder-section">
              <i class="ri-settings-3-line" />
              <p>选择左侧菜单项进行配置</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DataMaskingPanel from './DataMaskingPanel.vue'
import ShortcutCustomPanel from './ShortcutCustomPanel.vue'

defineProps<{ visible: boolean }>()
defineEmits<{ close: [] }>()

const activeSection = ref('masking')

const navItems = [
  { id: 'masking', icon: 'ri-shield-keyhole-line', label: '数据脱敏' },
  { id: 'shortcuts', icon: 'ri-keyboard-line', label: '快捷键' },
]
</script>

<style scoped>
.settings-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 500; }
.settings-modal { display: flex; width: 760px; height: 520px; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.settings-sidebar { width: 180px; background: var(--bg-secondary, #f9fafb); border-right: 1px solid var(--border-color, #e5e7eb); display: flex; flex-direction: column; flex-shrink: 0; }
.settings-title { padding: 16px; font-size: 14px; font-weight: 700; color: var(--text-primary, #111827); border-bottom: 1px solid var(--border-color, #e5e7eb); }
.settings-nav { padding: 8px; display: flex; flex-direction: column; gap: 2px; }
.nav-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: none; background: none; border-radius: 6px; cursor: pointer; font-size: 13px; color: var(--text-secondary, #6b7280); text-align: left; }
.nav-item:hover { background: var(--hover-bg, #f3f4f6); color: var(--text-primary, #111827); }
.nav-item.active { background: #fef2f2; color: var(--primary, #ef4444); font-weight: 600; }
.settings-content { flex: 1; position: relative; overflow: hidden; }
.close-btn { position: absolute; top: 10px; right: 10px; background: none; border: none; cursor: pointer; font-size: 18px; color: var(--text-secondary, #6b7280); z-index: 1; }
.close-btn:hover { color: var(--text-primary, #111827); }
.placeholder-section { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 8px; color: var(--text-secondary, #9ca3af); }
.placeholder-section i { font-size: 32px; }
.modal-enter-active, .modal-leave-active { transition: all 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .settings-modal, .modal-leave-to .settings-modal { transform: scale(0.95); }
</style>
