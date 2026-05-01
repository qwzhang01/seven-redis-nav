# Redis Nav UI 组件库

统一的设计系统和组件库，为Redis导航工具提供一致的视觉风格和交互体验。

## 🚀 快速开始

### 安装和导入

```typescript
// 在main.ts中全局安装
import { createApp } from 'vue';
import App from './App.vue';
import { installUiComponents } from '@/components/ui';

const app = createApp(App);
installUiComponents(app);
app.mount('#app');

// 或者按需导入
import { UiButton, UiInput, UiDataDisplay } from '@/components/ui';
```

### 设计令牌系统

组件库使用CSS自定义属性作为设计令牌：

```css
/* 颜色系统 */
--srn-color-primary: #1677ff;      /* 主色 */
--srn-color-success: #52c41a;       /* 成功色 */
--srn-color-warning: #faad14;      /* 警告色 */
--srn-color-error: #ff4d4f;        /* 错误色 */
--srn-color-info: #1890ff;         /* 信息色 */

/* 文字颜色 */
--srn-color-text-1: #262626;       /* 主要文字 */
--srn-color-text-2: #595959;       /* 次要文字 */
--srn-color-text-3: #8c8c8c;       /* 辅助文字 */

/* 背景颜色 */
--srn-color-surface-1: #ffffff;    /* 主要背景 */
--srn-color-surface-2: #fafafa;    /* 次要背景 */
--srn-color-surface-3: #f5f5f5;    /* 辅助背景 */

/* 间距系统 */
--srn-spacing-xs: 4px;
--srn-spacing-sm: 8px;
--srn-spacing-md: 12px;
--srn-spacing-lg: 16px;
--srn-spacing-xl: 24px;

/* 圆角系统 */
--srn-radius-sm: 4px;
--srn-radius-md: 6px;
--srn-radius-lg: 8px;

/* 动画速度 */
--srn-motion-fast: 0.15s;
--srn-motion-normal: 0.3s;
--srn-motion-slow: 0.5s;
```

## 📚 组件文档

### UiButton 按钮组件

基础按钮组件，支持多种样式和状态。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| variant | 'primary' \| 'secondary' \| 'outline' \| 'ghost' \| 'danger' | 'primary' | 按钮样式 |
| size | 'small' \| 'medium' \| 'large' | 'medium' | 按钮尺寸 |
| loading | boolean | false | 加载状态 |
| disabled | boolean | false | 禁用状态 |
| icon | string | - | 图标名称 |
| block | boolean | false | 块级按钮 |

#### 使用示例

```vue
<template>
  <div class="button-demo">
    <!-- 基础按钮 -->
    <UiButton variant="primary" @click="handleClick">
      主要按钮
    </UiButton>
    
    <!-- 带图标按钮 -->
    <UiButton variant="outline" icon="ri-add-line">
      添加项目
    </UiButton>
    
    <!-- 加载状态 -->
    <UiButton variant="primary" loading>
      提交中...
    </UiButton>
    
    <!-- 禁用状态 -->
    <UiButton variant="secondary" disabled>
      禁用按钮
    </UiButton>
  </div>
</template>
```

### UiInput 输入框组件

统一的输入框组件，支持多种状态和验证。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| modelValue | string | - | 绑定值 |
| placeholder | string | - | 占位文本 |
| size | 'small' \| 'medium' \| 'large' | 'medium' | 输入框尺寸 |
| type | 'text' \| 'password' \| 'number' \| 'email' \| 'search' | 'text' | 输入类型 |
| disabled | boolean | false | 禁用状态 |
| readonly | boolean | false | 只读状态 |
| clearable | boolean | false | 可清空 |
| prefixIcon | string | - | 前缀图标 |
| suffixIcon | string | - | 后缀图标 |
| status | 'default' \| 'success' \| 'warning' \| 'error' | 'default' | 状态 |
| message | string | - | 提示信息 |

#### 使用示例

```vue
<template>
  <div class="input-demo">
    <!-- 基础输入框 -->
    <UiInput v-model="value" placeholder="请输入内容" />
    
    <!-- 带状态输入框 -->
    <UiInput v-model="value" status="error" message="请输入有效内容" />
    
    <!-- 搜索框 -->
    <UiInput v-model="search" type="search" prefix-icon="ri-search-line" />
    
    <!-- 密码框 -->
    <UiInput v-model="password" type="password" placeholder="请输入密码" />
  </div>
</template>
```

### UiDataDisplay 数据展示组件

专门用于显示Redis数据的组件，支持多种数据类型。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data | KeyDetail | - | Redis键值数据 |
| editable | boolean | false | 是否可编辑 |
| compact | boolean | false | 紧凑模式 |
| maxHeight | string | '400px' | 最大高度 |

#### 支持的数据类型

- **String**: 字符串类型，支持JSON格式化
- **Hash**: 哈希类型，显示字段值对
- **List**: 列表类型，显示有序元素
- **Set**: 集合类型，显示无序元素
- **ZSet**: 有序集合类型，显示分数和成员

#### 使用示例

```vue
<template>
  <div class="data-display-demo">
    <!-- 显示字符串数据 -->
    <UiDataDisplay :data="stringData" />
    
    <!-- 显示哈希数据 -->
    <UiDataDisplay :data="hashData" editable />
    
    <!-- 紧凑模式 -->
    <UiDataDisplay :data="listData" compact />
  </div>
</template>

<script setup lang="ts">
import type { KeyDetail } from '@/types/data';

const stringData: KeyDetail = {
  key: 'user:1',
  type: 'string',
  value: '{"name":"张三","age":25}'
};

const hashData: KeyDetail = {
  key: 'user:profile',
  type: 'hash',
  value: {
    fields: [
      ['name', '张三'],
      ['age', '25'],
      ['email', 'zhangsan@example.com']
    ]
  }
};
</script>
```

## 🎨 主题定制

### 自定义主题

可以通过CSS变量自定义主题：

```css
:root {
  /* 主色调 */
  --srn-color-primary: #1890ff;
  --srn-color-primary-hover: #40a9ff;
  
  /* 成功色 */
  --srn-color-success: #52c41a;
  --srn-color-success-hover: #73d13d;
  
  /* 圆角 */
  --srn-radius-sm: 6px;
  --srn-radius-md: 8px;
  --srn-radius-lg: 12px;
}
```

### 深色主题

组件库支持深色主题，只需切换CSS变量：

```css
:root[data-theme="dark"] {
  --srn-color-text-1: #ffffff;
  --srn-color-text-2: #a6a6a6;
  --srn-color-text-3: #666666;
  --srn-color-surface-1: #1a1a1a;
  --srn-color-surface-2: #2a2a2a;
  --srn-color-surface-3: #3a3a3a;
}
```

## 🔧 开发指南

### 创建新组件

1. 在 `src/components/ui/` 目录下创建组件文件
2. 遵循命名规范：`PascalCase.vue`
3. 使用设计令牌系统
4. 提供完整的TypeScript类型定义
5. 编写单元测试

```vue
<template>
  <div class="ui-component">
    <!-- 组件内容 -->
  </div>
</template>

<script setup lang="ts">
interface Props {
  // 组件属性定义
}

const props = withDefaults(defineProps<Props>(), {
  // 默认值
});
</script>

<style scoped>
.ui-component {
  /* 使用设计令牌 */
  color: var(--srn-color-text-1);
  background: var(--srn-color-surface-1);
  border-radius: var(--srn-radius-md);
}
</style>
```

### 组件测试

每个组件都应该有对应的单元测试：

```typescript
// UiButton.test.ts
import { mount } from '@vue/test-utils';
import UiButton from './UiButton.vue';

describe('UiButton', () => {
  it('renders correctly', () => {
    const wrapper = mount(UiButton, {
      props: { variant: 'primary' },
      slots: { default: 'Click me' }
    });
    
    expect(wrapper.text()).toBe('Click me');
    expect(wrapper.classes()).toContain('ui-button--primary');
  });
});
```

## 📈 性能优化

### 懒加载机制

对于大型数据展示，组件库实现了懒加载机制：

- 使用Intersection Observer检测可视区域
- 大数据集自动启用虚拟滚动
- 按需加载和渲染内容

### 虚拟滚动

对于列表类型的数据，支持虚拟滚动：

```vue
<template>
  <VirtualList :items="largeDataset" :item-height="40">
    <template #default="{ item }">
      <div class="list-item">{{ item }}</div>
    </template>
  </VirtualList>
</template>
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下规范：

1. 遵循代码风格指南
2. 编写完整的类型定义
3. 提供单元测试
4. 更新文档
5. 遵循提交信息规范

## 📄 许可证

MIT License
