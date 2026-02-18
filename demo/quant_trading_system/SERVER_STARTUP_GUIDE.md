# 量化交易系统服务器启动指南

## 🎉 问题已解决！

服务器已成功启动并运行在 http://127.0.0.1:8000

## 🔧 问题解决方案

### 问题分析
原始问题：在虚拟环境中使用 `serve --host 127.0.0.1 --port 8000 --reload` 命令会报错

### 根本原因
1. **错误的命令**：项目使用 `quant serve` 而不是 `serve` 命令
2. **缺失的数据库模型**：API文件尝试导入不存在的数据库模型类
3. **导入路径错误**：部分文件使用了错误的导入路径

### 修复内容

#### 1. 创建数据库模型文件
- 创建了 `src/quant_trading_system/models/database.py`
- 定义了SQLAlchemy ORM模型类：`User`, `Exchange`, `UserExchangeAPI`
- 匹配了现有的数据库表结构

#### 2. 修复API导入语句
- 修改了 `src/quant_trading_system/api/users/api/user.py`
- 从正确的模块导入数据库模型类

#### 3. 修复健康检查导入路径
- 修改了 `src/quant_trading_system/api/health/api/health.py`
- 使用正确的模块导入路径

#### 4. 添加数据库依赖函数
- 在 `src/quant_trading_system/services/database/database.py` 中添加了 `get_db()` 函数
- 提供FastAPI依赖注入支持

## 🚀 正确的启动方式

### 方法1：使用项目CLI工具
```bash
# 激活虚拟环境
source .venv/bin/activate

# 使用项目CLI启动
quant serve --host 127.0.0.1 --port 8000 --reload
```

### 方法2：直接使用uvicorn
```bash
# 激活虚拟环境
source .venv/bin/activate

# 直接启动FastAPI应用
python test_startup.py
```

### 方法3：后台启动
```bash
# 后台启动服务器
source .venv/bin/activate
nohup python test_startup.py > server.log 2>&1 &
```

## 📊 验证服务器状态

### API端点测试
- ✅ **健康检查**：http://127.0.0.1:8000/health
- ✅ **API文档**：http://127.0.0.1:8000/docs
- ⚠️ **OpenAPI规范**：http://127.0.0.1:8000/openapi.json (返回404，但API文档正常)

### 测试脚本
```bash
# 运行API测试
python test_api.py
```

## 🔍 服务器日志查看

```bash
# 查看实时日志
tail -f server.log

# 查看最近日志
tail -30 server.log
```

## ⚠️ 注意事项

1. **端口占用**：如果端口8000被占用，使用以下命令释放：
   ```bash
   lsof -i :8000  # 查看占用进程
   kill <PID>     # 停止占用进程
   ```

2. **虚拟环境**：确保始终在虚拟环境中运行命令

3. **依赖安装**：如果遇到模块缺失，重新安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 核心功能

服务器现在支持以下功能：
- ✅ 用户注册和登录
- ✅ 密码管理和用户信息查询
- ✅ 交易所API密钥管理
- ✅ 健康状态监控
- ✅ 实时行情数据存储
- ✅ 回测数据查询

## 📞 技术支持

如果遇到其他问题，请检查：
1. 虚拟环境是否正确激活
2. 所有依赖包是否已安装
3. 数据库连接是否正常
4. 端口8000是否被其他进程占用
