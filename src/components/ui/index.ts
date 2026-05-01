// UI组件库统一导出文件
// 提供一致的组件导入方式，便于维护和使用

import UiButton from './Button.vue';
import UiInput from './Input.vue';
import UiDataDisplay from './DataDisplay.vue';

export { UiButton, UiInput, UiDataDisplay };

// 组件库配置
export const UI_CONFIG = {
  // 默认主题配置
  theme: {
    primary: 'var(--srn-color-primary)',
    success: 'var(--srn-color-success)',
    warning: 'var(--srn-color-warning)',
    error: 'var(--srn-color-error)',
    info: 'var(--srn-color-info)'
  },

  // 尺寸配置
  sizes: {
    small: {
      fontSize: '12px',
      height: '24px',
      padding: '0 12px'
    },
    medium: {
      fontSize: '13px',
      height: '28px',
      padding: '0 16px'
    },
    large: {
      fontSize: '14px',
      height: '32px',
      padding: '0 20px'
    }
  },

  // 动画配置
  motion: {
    fast: 'var(--srn-motion-fast)',
    normal: 'var(--srn-motion-normal)',
    slow: 'var(--srn-motion-slow)'
  },

  // 圆角配置
  radius: {
    sm: 'var(--srn-radius-sm)',
    md: 'var(--srn-radius-md)',
    lg: 'var(--srn-radius-lg)'
  }
};

// 组件类型定义
export interface UiButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  disabled?: boolean;
  icon?: string;
  block?: boolean;
}

export interface UiInputProps {
  modelValue?: string;
  placeholder?: string;
  size?: 'small' | 'medium' | 'large';
  type?: 'text' | 'password' | 'number' | 'email' | 'search';
  disabled?: boolean;
  readonly?: boolean;
  clearable?: boolean;
  prefixIcon?: string;
  suffixIcon?: string;
  status?: 'default' | 'success' | 'warning' | 'error';
  message?: string;
}

export interface UiDataDisplayProps {
  data: any;
  editable?: boolean;
  compact?: boolean;
  maxHeight?: string;
}

// 组件库使用示例
export const USAGE_EXAMPLES = {
  button: `
// 基础使用
<UiButton variant="primary" size="medium">
  确认操作
</UiButton>

// 带图标按钮
<UiButton variant="outline" icon="ri-add-line">
  添加项目
</UiButton>

// 加载状态
<UiButton variant="primary" loading>
  提交中...
</UiButton>
  `,

  input: `
// 基础输入框
<UiInput v-model="value" placeholder="请输入内容" />

// 带状态输入框
<UiInput v-model="value" status="error" message="请输入有效内容" />

// 带图标输入框
<UiInput v-model="value" prefix-icon="ri-search-line" />
  `,

  dataDisplay: `
// 显示Redis数据
<UiDataDisplay :data="keyDetail" />

// 可编辑模式
<UiDataDisplay :data="keyDetail" editable />

// 紧凑模式
<UiDataDisplay :data="keyDetail" compact />
  `
};

// 组件库版本信息
export const UI_VERSION = '1.0.0';

// 组件库安装函数（用于全局注册）
export function installUiComponents(app: any) {
  const components = {
    UiButton,
    UiInput,
    UiDataDisplay
  };

  Object.entries(components).forEach(([name, component]) => {
    app.component(name, component);
  });

  console.log(`Redis Nav UI组件库 v${UI_VERSION} 已安装`);
}

// 默认导出组件库
export default {
  install: installUiComponents,
  version: UI_VERSION,
  UiButton,
  UiInput,
  UiDataDisplay
};
