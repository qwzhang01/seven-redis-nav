# API对接说明文档

## 概述

本文档说明如何在前端项目中对接量化交易系统的用户管理API。

## 已完成的工作

### 1. 创建的文件

#### `/src/utils/request.ts`
- 封装了基于fetch的HTTP请求工具
- 支持请求拦截、响应拦截
- 自动处理JWT认证
- 统一错误处理
- 支持401自动跳转登录

#### `/src/utils/userApi.ts`
- 封装了所有用户管理相关的API接口
- 包含完整的TypeScript类型定义
- 支持的接口：
  - 用户注册 `register()`
  - 用户登录 `login()`
  - 获取用户信息 `getProfile()`
  - 更新用户信息 `updateProfile()`
  - 修改密码 `changePassword()`
  - 获取交易所列表 `getExchanges()`
  - 添加API密钥 `addApiKey()`
  - 获取API密钥列表 `getApiKeys()`
  - 删除API密钥 `deleteApiKey()`
  - 启用/禁用API密钥 `toggleApiKey()`

#### `/src/stores/auth.ts`
- 更新了认证状态管理
- 集成真实API调用
- 自动处理token存储
- 支持用户信息持久化

#### 更新的页面
- `/src/views/auth/LoginPage.vue` - 登录页面
- `/src/views/auth/RegisterPage.vue` - 注册页面

#### 环境配置
- `/.env` - 环境变量配置文件

## 使用方法

### 1. 环境配置

确保 `.env` 文件中配置了正确的API地址：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 2. 用户注册

```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 注册新用户
try {
  await authStore.register({
    username: 'testuser',
    nickname: '测试用户',
    email: 'test@example.com',
    password: 'password123',
    phone: '13800138000', // 可选
  })
  console.log('注册成功')
} catch (error) {
  console.error('注册失败:', error)
}
```

### 3. 用户登录

```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 用户登录
try {
  await authStore.login('testuser', 'password123')
  console.log('登录成功')
  console.log('用户信息:', authStore.user)
} catch (error) {
  console.error('登录失败:', error)
}
```

### 4. 获取用户信息

```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 获取最新的用户信息
try {
  const userInfo = await authStore.fetchUserProfile()
  console.log('用户信息:', userInfo)
} catch (error) {
  console.error('获取用户信息失败:', error)
}
```

### 5. 更新用户信息

```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 更新用户信息
try {
  await authStore.updateProfile({
    nickname: '新昵称',
    email: 'newemail@example.com',
    phone: '13900139000',
  })
  console.log('更新成功')
} catch (error) {
  console.error('更新失败:', error)
}
```

### 6. 修改密码

```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 修改密码
try {
  await authStore.changePassword('oldpassword', 'newpassword')
  console.log('密码修改成功')
} catch (error) {
  console.error('密码修改失败:', error)
}
```

### 7. 获取交易所列表

```typescript
import * as userApi from '@/utils/userApi'

// 获取交易所列表
try {
  const exchanges = await userApi.getExchanges()
  console.log('交易所列表:', exchanges)
} catch (error) {
  console.error('获取交易所列表失败:', error)
}
```

### 8. 添加API密钥

```typescript
import * as userApi from '@/utils/userApi'

// 添加API密钥
try {
  const apiKey = await userApi.addApiKey({
    exchange_id: 'exchange-uuid',
    label: '币安主账户',
    api_key: 'your_api_key',
    secret_key: 'your_secret_key',
    passphrase: 'your_passphrase', // 可选
    permissions: {
      spot_trading: true,
      margin_trading: false,
      futures_trading: false,
      withdraw: false,
    },
  })
  console.log('API密钥添加成功:', apiKey)
} catch (error) {
  console.error('添加API密钥失败:', error)
}
```

## 测试步骤

### 1. 启动后端服务

确保后端服务运行在 `http://127.0.0.1:8000`

### 2. 启动前端开发服务器

```bash
npm run dev
```

### 3. 测试注册

1. 访问 http://localhost:5173/register
2. 填写注册表单
3. 提交注册
4. 检查是否成功跳转到首页

### 4. 测试登录

1. 访问 http://localhost:5173/login
2. 输入注册的用户名和密码
3. 点击登录
4. 检查是否成功跳转

## 常见问题

### 1. CORS跨域问题

如果遇到CORS错误，需要在后端配置允许跨域：

```python
# FastAPI配置
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 401错误循环

如果遇到401错误后不断重定向，检查：
- token是否正确保存
- 后端是否正确验证token
- 是否有死循环的路由守卫

### 3. 环境变量不生效

确保：
- `.env` 文件在项目根目录
- 环境变量以 `VITE_` 开头
- 修改后重启开发服务器

## 下一步工作

### 1. 完善用户中心页面

在 `UserCenter.vue` 中集成API：
- 获取并显示真实的用户策略
- 获取并显示真实的API密钥
- 实现添加/删除API密钥功能

### 2. 添加更多API接口

根据需要添加其他业务API：
- 策略管理API
- 信号管理API
- 交易记录API

## 参考资料

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Fetch API文档](https://developer.mozilla.org/zh-CN/docs/Web/API/Fetch_API)
- [Pinia文档](https://pinia.vuejs.org/)
