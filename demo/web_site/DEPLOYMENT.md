# ========================================
# Quant Meta 生产环境部署文档
# ========================================

## 📋 目录
- [快速开始](#快速开始)
- [部署方式](#部署方式)
- [配置说明](#配置说明)
- [运维管理](#运维管理)
- [故障排查](#故障排查)

## 🚀 快速开始

### 前置要求
- Docker >= 20.10
- Docker Compose >= 2.0
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

### 一键部署
```bash
# 1. 克隆项目
git clone <repository-url>
cd web_site

# 2. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件根据需要修改配置

# 3. 执行部署
chmod +x deploy.sh
./deploy.sh
```

## 📦 部署方式

### 方式一：使用部署脚本（推荐）
```bash
# 标准部署
./deploy.sh

# 自定义端口部署
HOST_PORT=8080 ./deploy.sh

# 指定版本部署
IMAGE_TAG=v1.0.0 ./deploy.sh
```

**脚本特性：**
- ✅ 零停机部署
- ✅ 自动健康检查
- ✅ 失败自动回滚
- ✅ 镜像备份管理
- ✅ 详细日志记录

### 方式二：使用 Docker Compose
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

### 方式三：手动 Docker 命令
```bash
# 构建镜像
docker build -t quantmeta:latest .

# 运行容器
docker run -d \
  --name quantmeta \
  -p 80:8080 \
  --restart unless-stopped \
  quantmeta:latest
```

## ⚙️ 配置说明

### 环境变量
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HOST_PORT` | 80 | 宿主机端口 |
| `IMAGE_NAME` | quantmeta | 镜像名称 |
| `IMAGE_TAG` | latest | 镜像标签 |
| `CONTAINER_NAME` | quantmeta | 容器名称 |
| `NODE_ENV` | production | 运行环境 |
| `TZ` | Asia/Shanghai | 时区设置 |

### 资源限制
在 `docker-compose.yml` 中配置：
```yaml
deploy:
  resources:
    limits:
      cpus: '2'          # CPU 限制
      memory: 1G         # 内存限制
    reservations:
      cpus: '0.5'        # CPU 预留
      memory: 256M       # 内存预留
```

### Nginx 配置
主配置文件：`docker/nginx.conf`

**关键配置项：**
- 监听端口：8080（容器内部）
- Gzip 压缩：已启用
- 静态资源缓存：1年（assets）、30天（图片）
- API 代理：`/api/` -> `http://host.docker.internal:8000`
- 健康检查：`/health`

## 🔧 运维管理

### 查看服务状态
```bash
# 查看容器状态
docker ps -f name=quantmeta

# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' quantmeta

# 查看资源使用
docker stats quantmeta
```

### 日志管理
```bash
# 查看实时日志
docker logs -f quantmeta

# 查看最近100行日志
docker logs --tail 100 quantmeta

# 查看部署日志
cat deploy-$(date +%Y%m%d).log

# 查看 Nginx 日志
docker exec quantmeta tail -f /var/log/nginx/access.log
docker exec quantmeta tail -f /var/log/nginx/error.log
```

### 容器管理
```bash
# 重启容器
docker restart quantmeta

# 停止容器
docker stop quantmeta

# 启动容器
docker start quantmeta

# 进入容器
docker exec -it quantmeta sh
```

### 镜像管理
```bash
# 查看镜像列表
docker images quantmeta

# 查看镜像历史
docker history quantmeta:latest

# 清理未使用的镜像
docker image prune -a
```

### 备份与恢复
```bash
# 导出镜像
docker save quantmeta:latest -o quantmeta-backup.tar

# 导入镜像
docker load -i quantmeta-backup.tar

# 查看备份镜像
docker images | grep backup
```

### 更新部署
```bash
# 拉取最新代码
git pull

# 重新部署
./deploy.sh

# 或使用 docker-compose
docker-compose up -d --build
```

## 🔍 故障排查

### 容器无法启动
```bash
# 1. 查看容器日志
docker logs quantmeta

# 2. 检查端口占用
lsof -i :80
netstat -tuln | grep 80

# 3. 检查 Docker 服务
docker info

# 4. 检查磁盘空间
df -h
```

### 健康检查失败
```bash
# 1. 手动测试健康检查
docker exec quantmeta curl -f http://localhost:8080/

# 2. 查看 Nginx 错误日志
docker exec quantmeta cat /var/log/nginx/error.log

# 3. 检查 Nginx 配置
docker exec quantmeta nginx -t

# 4. 重启容器
docker restart quantmeta
```

### 访问 502/504 错误
```bash
# 1. 检查后端 API 服务是否运行
curl http://localhost:8000/api/

# 2. 检查 host.docker.internal 解析
docker exec quantmeta ping -c 3 host.docker.internal

# 3. 查看 Nginx 代理日志
docker exec quantmeta tail -f /var/log/nginx/error.log
```

### 内存/CPU 使用过高
```bash
# 1. 查看资源使用情况
docker stats quantmeta

# 2. 调整资源限制（编辑 docker-compose.yml）
# 修改 deploy.resources.limits 配置

# 3. 重启服务
docker-compose up -d
```

### 回滚到上一个版本
```bash
# 1. 查看备份镜像
docker images | grep backup

# 2. 手动回滚
docker stop quantmeta
docker rm quantmeta
docker tag quantmeta:backup-YYYYMMDD-HHMMSS quantmeta:latest
docker run -d --name quantmeta -p 80:8080 quantmeta:latest

# 或者重新运行部署脚本（会自动回滚失败的部署）
./deploy.sh
```

## 📊 监控指标

### 关键指标
- **容器状态**：running / healthy
- **CPU 使用率**：< 80%
- **内存使用率**：< 80%
- **磁盘使用率**：< 85%
- **响应时间**：< 500ms
- **错误率**：< 1%

### 监控命令
```bash
# 实时监控
watch -n 1 'docker stats quantmeta --no-stream'

# 健康检查
watch -n 5 'docker inspect --format="{{.State.Health.Status}}" quantmeta'
```

## 🔒 安全建议

1. **定期更新**：及时更新基础镜像和依赖包
2. **最小权限**：容器以非 root 用户运行
3. **网络隔离**：使用 Docker 网络隔离
4. **日志审计**：定期检查访问日志
5. **备份策略**：定期备份镜像和数据
6. **HTTPS**：生产环境建议配置 SSL/TLS

## 📞 支持

如遇问题，请：
1. 查看部署日志：`cat deploy-$(date +%Y%m%d).log`
2. 查看容器日志：`docker logs quantmeta`
3. 提交 Issue 或联系运维团队

---

**最后更新**：2026-02-21
**维护团队**：Quant Meta DevOps
