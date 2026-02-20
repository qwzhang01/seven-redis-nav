# 量化交易系统 — 生产环境 Docker 部署指南

## 一、生产环境现状

| 容器名 | 镜像 | 端口 | 说明 |
|--------|------|------|------|
| quantmeta | quantmeta:latest | 80→80 | Nginx 反向代理（已运行） |
| redis | redis:7-alpine | 6379→6379 | Redis 缓存（已运行） |
| postgres-timescaledb | timescale/timescaledb:latest-pg15 | 5432→5432 | TimescaleDB（已运行） |
| kafka | apache/kafka:latest | 9092→9092 | Kafka 消息队列（已运行） |
| minio | minio/minio:latest | 9000-9001→9000-9001 | MinIO 对象存储（已运行） |

> **注意**：以上服务已在生产环境运行，本次部署仅需部署应用服务 `quant_app`，接入已有基础设施。

---

## 二、目录结构

```
quant_trading_system/
├── publish/
│   ├── deploy.md              # 本文档
│   ├── intro.md               # 生产环境信息
│   ├── docker-compose.prod.yml  # 生产 compose 文件
│   ├── .env.prod              # 生产环境变量（不提交 git）
│   ├── Dockerfile.prod        # 生产 Dockerfile
│   ├── nginx/
│   │   └── quant_app.conf     # Nginx 应用配置片段
│   └── scripts/
│       ├── deploy.sh          # 一键部署脚本
│       ├── rollback.sh        # 回滚脚本
│       ├── health_check.sh    # 健康检查脚本
│       └── db_init.sh         # 数据库初始化脚本
├── database/
│   └── schema.sql             # 数据库建表脚本
└── Dockerfile                 # 开发 Dockerfile
```

---

## 三、部署前准备

### 3.1 服务器要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 50 GB SSD | 100 GB+ SSD |
| OS | Ubuntu 20.04+ / CentOS 8+ | Ubuntu 22.04 LTS |
| Docker | 24.0+ | 最新稳定版 |
| Docker Compose | 2.20+ | 最新稳定版 |

### 3.2 网络规划

```
外部请求 → quantmeta(Nginx:80) → quant_app(8000)
                                ↓
                         postgres-timescaledb(5432)
                         redis(6379)
                         kafka(9092)
                         minio(9000)
```

### 3.3 确认已有服务网络

```bash
# 查看已有容器所在网络
docker inspect quantmeta --format '{{json .NetworkSettings.Networks}}'
docker inspect redis --format '{{json .NetworkSettings.Networks}}'

# 记录网络名称，后续 quant_app 需加入同一网络
docker network ls
```

---

## 四、配置文件说明

### 4.1 生产环境变量 `.env.prod`

> 文件位于 `publish/.env.prod`，**严禁提交到 git**

```ini
# ===== 应用配置 =====
APP_NAME=量化交易系统
APP_VERSION=1.0.0
DEBUG=False
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# ===== 数据库配置（接入已有 postgres-timescaledb）=====
DATABASE_URL=postgresql://postgres:uOp8JgVyKQHTGaUjc7d+ZZZZVocMjSuFrfOXYswW7Bs=@postgres-timescaledb:5432/myapp
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_RECYCLE=3600
SQLALCHEMY_POOL_PRE_PING=True

# ===== Redis 配置（接入已有 redis）=====
REDIS_URL=redis://:MKdxcIJyRU57tuoUeSlulHi5OBng434F2RCY4kbOtXo=@redis:6379/0
REDIS_PASSWORD=MKdxcIJyRU57tuoUeSlulHi5OBng434F2RCY4kbOtXo=
REDIS_DB=0

# ===== Kafka 配置（接入已有 kafka）=====
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# ===== MinIO 配置（接入已有 minio）=====
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=7zUtLymW+8lJ35hW1gGl/we76iLPeL8DznOjdVyTPFw=
MINIO_SECURE=False

# ===== JWT 认证配置 =====
JWT_SECRET_KEY=<生产环境请替换为64位以上随机字符串>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7

# ===== 日志配置 =====
LOG_LEVEL=INFO
LOG_FILE=/app/logs/quant_trading.log

# ===== 安全配置 =====
CORS_ORIGINS=https://your-domain.com
ALLOWED_HOSTS=your-domain.com,localhost
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# ===== API 配置 =====
API_PREFIX=/api/v1
DOCS_URL=          # 生产环境关闭 Swagger UI
REDOC_URL=         # 生产环境关闭 ReDoc

# ===== 交易所 API =====
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
BINANCE_TESTNET=false
```

---

## 五、部署文件

### 5.1 生产 Dockerfile（`publish/Dockerfile.prod`）

多阶段构建，最终镜像不含构建工具，体积更小、更安全。

```dockerfile
# ---- 构建阶段 ----
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- 运行阶段 ----
FROM python:3.11-slim AS runtime

WORKDIR /app

# 仅安装运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的包
COPY --from=builder /install /usr/local

# 复制应用代码
COPY src/ ./src/
COPY database/ ./database/
COPY pyproject.toml .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app

USER appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.quant_trading_system.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info", \
     "--access-log"]
```

### 5.2 生产 Docker Compose（`publish/docker-compose.prod.yml`）

只部署应用服务，接入已有基础设施网络。

```yaml
version: '3.8'

services:
  quant_app:
    image: quant_app:${APP_VERSION:-latest}
    build:
      context: ..
      dockerfile: publish/Dockerfile.prod
    container_name: quant_app
    restart: unless-stopped
    env_file:
      - .env.prod
    ports:
      - "127.0.0.1:8000:8000"   # 仅监听本地，由 Nginx 代理
    volumes:
      - ../logs:/app/logs
    networks:
      - prod_network             # 加入已有生产网络
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

networks:
  prod_network:
    external: true
    name: <已有容器所在的网络名>   # 执行 docker network ls 确认后填写
```

### 5.3 Nginx 配置片段（`publish/nginx/quant_app.conf`）

将此配置加入已有 `quantmeta` 容器的 Nginx 配置中。

```nginx
upstream quant_app_backend {
    server quant_app:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;

    # 强制跳转 HTTPS（有证书时启用）
    # return 301 https://$host$request_uri;

    location /api/ {
        proxy_pass         http://quant_app_backend;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   Connection        "";

        proxy_connect_timeout  10s;
        proxy_send_timeout     60s;
        proxy_read_timeout     60s;

        # 限流
        limit_req zone=api_limit burst=20 nodelay;
    }

    location /health {
        proxy_pass http://quant_app_backend/health;
        access_log off;
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass         http://quant_app_backend;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host       $host;
        proxy_read_timeout 3600s;
    }
}
```

---

## 六、部署脚本

### 6.1 一键部署脚本（`publish/scripts/deploy.sh`）

```bash
#!/bin/bash
# 生产环境一键部署脚本
# 用法: ./deploy.sh [版本号]  例如: ./deploy.sh 1.2.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLISH_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$PUBLISH_DIR")"
APP_VERSION="${1:-latest}"
IMAGE_NAME="quant_app"
CONTAINER_NAME="quant_app"
LOG_FILE="/var/log/quant_deploy.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
error() { log "ERROR: $*"; exit 1; }

log "===== 开始部署 quant_app v${APP_VERSION} ====="

# 1. 检查必要文件
[ -f "$PUBLISH_DIR/.env.prod" ] || error ".env.prod 不存在，请先创建"
[ -f "$PUBLISH_DIR/Dockerfile.prod" ] || error "Dockerfile.prod 不存在"

# 2. 确认生产网络存在
PROD_NETWORK=$(docker inspect redis --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null | head -1)
[ -n "$PROD_NETWORK" ] || error "无法获取生产网络名，请确认 redis 容器正在运行"
log "检测到生产网络: $PROD_NETWORK"

# 3. 更新 docker-compose.prod.yml 中的网络名
sed -i "s|name: <已有容器所在的网络名>|name: $PROD_NETWORK|g" \
    "$PUBLISH_DIR/docker-compose.prod.yml"

# 4. 构建镜像
log "构建镜像 ${IMAGE_NAME}:${APP_VERSION} ..."
docker build \
    -f "$PUBLISH_DIR/Dockerfile.prod" \
    -t "${IMAGE_NAME}:${APP_VERSION}" \
    -t "${IMAGE_NAME}:latest" \
    "$PROJECT_DIR"
log "镜像构建完成"

# 5. 初始化数据库（首次部署时执行）
if [ "${INIT_DB:-false}" = "true" ]; then
    log "执行数据库初始化..."
    "$SCRIPT_DIR/db_init.sh"
fi

# 6. 优雅停止旧容器（保留30s处理中的请求）
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    log "停止旧容器 $CONTAINER_NAME ..."
    docker stop --time=30 "$CONTAINER_NAME" || true
    docker rm "$CONTAINER_NAME" || true
fi

# 7. 启动新容器
log "启动新容器..."
cd "$PUBLISH_DIR"
APP_VERSION="$APP_VERSION" docker compose -f docker-compose.prod.yml up -d

# 8. 等待健康检查通过
log "等待服务健康检查..."
MAX_WAIT=120
WAITED=0
until docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null | grep -q "healthy"; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        log "健康检查超时，查看容器日志："
        docker logs --tail=50 "$CONTAINER_NAME"
        error "部署失败：服务未能在 ${MAX_WAIT}s 内通过健康检查"
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    log "等待中... ${WAITED}s / ${MAX_WAIT}s"
done

log "===== 部署成功！quant_app v${APP_VERSION} 已运行 ====="
log "健康检查: curl http://localhost:8000/health"
```

### 6.2 回滚脚本（`publish/scripts/rollback.sh`）

```bash
#!/bin/bash
# 回滚到上一个版本
# 用法: ./rollback.sh <版本号>  例如: ./rollback.sh 1.1.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLISH_DIR="$(dirname "$SCRIPT_DIR")"
TARGET_VERSION="${1:-}"
IMAGE_NAME="quant_app"
CONTAINER_NAME="quant_app"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
error() { log "ERROR: $*"; exit 1; }

[ -n "$TARGET_VERSION" ] || error "请指定回滚版本号，例如: ./rollback.sh 1.1.0"

# 检查目标镜像是否存在
docker image inspect "${IMAGE_NAME}:${TARGET_VERSION}" > /dev/null 2>&1 \
    || error "镜像 ${IMAGE_NAME}:${TARGET_VERSION} 不存在，可用镜像："

log "===== 回滚到 ${IMAGE_NAME}:${TARGET_VERSION} ====="

# 停止当前容器
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    log "停止当前容器..."
    docker stop --time=30 "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

# 重新打 latest 标签
docker tag "${IMAGE_NAME}:${TARGET_VERSION}" "${IMAGE_NAME}:latest"

# 启动回滚版本
cd "$PUBLISH_DIR"
APP_VERSION="$TARGET_VERSION" docker compose -f docker-compose.prod.yml up -d

log "===== 回滚完成！当前运行版本: ${TARGET_VERSION} ====="
```

### 6.3 数据库初始化脚本（`publish/scripts/db_init.sh`）

```bash
#!/bin/bash
# 数据库初始化脚本（首次部署时执行）
# 用法: ./db_init.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 从 .env.prod 读取数据库配置
source "$(dirname "$SCRIPT_DIR")/.env.prod" 2>/dev/null || true

DB_CONTAINER="postgres-timescaledb"
DB_NAME="${POSTGRES_DB:-myapp}"
DB_USER="${POSTGRES_USER:-postgres}"
SCHEMA_FILE="$PROJECT_DIR/database/schema.sql"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
error() { log "ERROR: $*"; exit 1; }

log "===== 数据库初始化 ====="

# 检查容器是否运行
docker ps -q -f name="$DB_CONTAINER" | grep -q . \
    || error "容器 $DB_CONTAINER 未运行"

# 检查数据库是否已初始化（检查核心表是否存在）
TABLE_EXISTS=$(docker exec "$DB_CONTAINER" \
    psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='user_info';" 2>/dev/null || echo "0")

if [ "$TABLE_EXISTS" = "1" ]; then
    log "数据库已初始化，跳过（如需重新初始化请手动执行）"
    exit 0
fi

log "执行建表脚本: $SCHEMA_FILE"
docker exec -i "$DB_CONTAINER" \
    psql -U "$DB_USER" -d "$DB_NAME" < "$SCHEMA_FILE"

log "===== 数据库初始化完成 ====="
```

### 6.4 健康检查脚本（`publish/scripts/health_check.sh`）

```bash
#!/bin/bash
# 服务健康检查脚本
# 用法: ./health_check.sh

set -euo pipefail

CONTAINER_NAME="quant_app"
API_URL="http://localhost:8000"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
ok()  { log "✅ $*"; }
fail(){ log "❌ $*"; FAILED=1; }

FAILED=0

log "===== 生产环境健康检查 ====="

# 检查各容器状态
for name in quantmeta redis postgres-timescaledb kafka minio quant_app; do
    STATUS=$(docker inspect --format='{{.State.Status}}' "$name" 2>/dev/null || echo "not_found")
    HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no_healthcheck{{end}}' "$name" 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "running" ]; then
        ok "容器 $name: running ($HEALTH)"
    else
        fail "容器 $name: $STATUS"
    fi
done

# 检查 API 健康端点
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health" --max-time 5 || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    ok "API /health: HTTP $HTTP_CODE"
else
    fail "API /health: HTTP $HTTP_CODE"
fi

# 检查数据库连接（通过 API）
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/v1/system/status" --max-time 5 || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    ok "API 路由可达: HTTP $HTTP_CODE"
else
    fail "API 路由不可达: HTTP $HTTP_CODE"
fi

log "===== 检查完成 ====="
[ $FAILED -eq 0 ] && log "所有服务正常 ✅" || { log "存在异常服务，请检查 ❌"; exit 1; }
```

---

## 七、完整部署流程

### 7.1 首次部署

```bash
# 1. 进入 publish 目录
cd /path/to/quant_trading_system/publish

# 2. 创建生产环境变量文件
cp .env.example .env.prod
# 编辑 .env.prod，填写真实配置（重点：JWT_SECRET_KEY、数据库密码）
vim .env.prod

# 3. 确认生产网络名称
docker network ls
# 编辑 docker-compose.prod.yml，将 <已有容器所在的网络名> 替换为实际网络名

# 4. 赋予脚本执行权限
chmod +x scripts/*.sh

# 5. 首次部署（含数据库初始化）
INIT_DB=true ./scripts/deploy.sh 1.0.0
```

### 7.2 日常更新部署

```bash
cd /path/to/quant_trading_system/publish

# 拉取最新代码
git pull origin main

# 部署新版本
./scripts/deploy.sh 1.1.0
```

### 7.3 回滚

```bash
# 查看可用镜像版本
docker images quant_app

# 回滚到指定版本
./scripts/rollback.sh 1.0.0
```

### 7.4 查看日志

```bash
# 实时日志
docker logs -f quant_app

# 最近 100 行
docker logs --tail=100 quant_app

# 应用日志文件
tail -f /path/to/quant_trading_system/logs/quant_trading.log
```

---

## 八、运维操作

### 8.1 常用命令

```bash
# 查看所有容器状态
docker ps -a

# 进入容器调试
docker exec -it quant_app bash

# 查看容器资源使用
docker stats quant_app

# 手动健康检查
./scripts/health_check.sh

# 重启应用（不重建镜像）
docker restart quant_app
```

### 8.2 数据库备份

```bash
# 备份数据库
docker exec postgres-timescaledb \
    pg_dump -U postgres myapp | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# 恢复数据库
gunzip -c backup_20260220_100000.sql.gz | \
    docker exec -i postgres-timescaledb psql -U postgres myapp
```

### 8.3 清理旧镜像

```bash
# 清理悬空镜像
docker image prune -f

# 清理指定版本之前的旧镜像（保留最近3个版本）
docker images quant_app --format "{{.Tag}}" | sort -V | head -n -3 | \
    xargs -I{} docker rmi quant_app:{}
```

---

## 九、安全注意事项

1. **`.env.prod` 严禁提交 git**，已在 `.gitignore` 中排除
2. **JWT_SECRET_KEY** 必须使用 64 位以上随机字符串：
   ```bash
   openssl rand -hex 64
   ```
3. 应用端口 `8000` 仅绑定 `127.0.0.1`，通过 Nginx 对外暴露
4. 生产环境关闭 Swagger UI（`DOCS_URL=` 留空）
5. 定期轮换数据库密码和 JWT 密钥
6. 开启服务器防火墙，仅开放 80/443 端口对外
