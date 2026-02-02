<template>
  <div class="drawing-tools">
    <div class="tool-group">
      <div class="group-title">线条工具</div>
      <div class="tool-grid">
        <div
          v-for="tool in lineTools"
          :key="tool.value"
          class="tool-item"
          :class="{ active: selectedTool === tool.value }"
          @click="selectTool(tool.value)"
        >
          <t-icon :name="tool.icon" size="24px" />
          <span>{{ tool.label }}</span>
        </div>
      </div>
    </div>
    
    <div class="tool-group">
      <div class="group-title">形状工具</div>
      <div class="tool-grid">
        <div
          v-for="tool in shapeTools"
          :key="tool.value"
          class="tool-item"
          :class="{ active: selectedTool === tool.value }"
          @click="selectTool(tool.value)"
        >
          <t-icon :name="tool.icon" size="24px" />
          <span>{{ tool.label }}</span>
        </div>
      </div>
    </div>
    
    <div class="tool-group">
      <div class="group-title">标注工具</div>
      <div class="tool-grid">
        <div
          v-for="tool in annotationTools"
          :key="tool.value"
          class="tool-item"
          :class="{ active: selectedTool === tool.value }"
          @click="selectTool(tool.value)"
        >
          <t-icon :name="tool.icon" size="24px" />
          <span>{{ tool.label }}</span>
        </div>
      </div>
    </div>
    
    <t-divider />
    
    <t-button block variant="outline" theme="danger" @click="clearAll">
      <t-icon name="delete" /> 清除所有画线
    </t-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

const emit = defineEmits(['select'])

const selectedTool = ref(null)

const lineTools = [
  { value: 'trendline', label: '趋势线', icon: 'chart-line' },
  { value: 'horizontal', label: '水平线', icon: 'remove' },
  { value: 'vertical', label: '垂直线', icon: 'add' },
  { value: 'ray', label: '射线', icon: 'arrow-right' },
  { value: 'channel', label: '平行通道', icon: 'layers' },
  { value: 'fib', label: '斐波那契', icon: 'chart-bubble' }
]

const shapeTools = [
  { value: 'rect', label: '矩形', icon: 'rectangle' },
  { value: 'circle', label: '圆形', icon: 'circle' },
  { value: 'triangle', label: '三角形', icon: 'caret-up' }
]

const annotationTools = [
  { value: 'text', label: '文字标注', icon: 'format-text' },
  { value: 'arrow', label: '箭头', icon: 'arrow-up' },
  { value: 'marker', label: '标记点', icon: 'map-marker' }
]

const selectTool = (tool) => {
  selectedTool.value = tool
  emit('select', tool)
  MessagePlugin.info(`已选择: ${lineTools.concat(shapeTools, annotationTools).find(t => t.value === tool)?.label}`)
}

const clearAll = () => {
  selectedTool.value = null
  MessagePlugin.success('已清除所有画线')
}
</script>

<style lang="less" scoped>
.drawing-tools {
  padding: 16px;
}

.tool-group {
  margin-bottom: 24px;
  
  .group-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--text2);
    margin-bottom: 12px;
  }
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.tool-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  span {
    font-size: 12px;
    color: var(--text2);
  }
  
  &:hover {
    border-color: var(--brand);
    background: rgba(18, 95, 255, 0.05);
  }
  
  &.active {
    border-color: var(--brand);
    background: rgba(18, 95, 255, 0.1);
    
    span {
      color: var(--brand);
    }
  }
}
</style>
