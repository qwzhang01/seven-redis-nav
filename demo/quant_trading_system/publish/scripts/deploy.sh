#!/bin/bash
# ============================================================
# 量化交易系统 — 生产环境一键部署脚本
# 用法: ./deploy.sh [版本号]
# 示例: ./deploy.sh 1.2.0
#       INIT_DB=true ./deploy.sh 1.0.0   # 首次部署，含数据库初始化
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLISH_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$PUBLISH_DIR")"
APP_VERSION="${1:-latest}"
IMAGE_NAME="quant_app"
CONTAINER_NAME="quant_app"
LOG_FILE="/var/log/quant_deploy.log"

# ---- 日志函数 ----
log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]  $*" | tee -a "$LOG_FILE"; }
warn()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN]  $*" | tee -a "$LOG_FILE"; }
error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" | tee -a "$LOG_FILE"; exit 1; }

log "===== 开始部署 quant_app v${APP_VERSION} ====="

# ---- 1. 检查必要文件 ----
[ -f "$PUBLISH_DIR/.env.prod" ]        || error ".env.prod 不存在，请先创建（参考 deploy.md 第四章）"
[ -f "$PUBLISH_DIR/Dockerfile.prod" ]  || error "Dockerfile.prod 不存在"
[ -f "$PUBLISH_DIR/docker-compose.prod.yml" ] || error "docker-compose.prod.yml 不存在"

# ---- 2. 检查 Docker 环境 ----
docker info > /dev/null 2>&1 || error "Docker 未运行，请先启动 Docker"
docker compose version > /dev/null 2>&1 || error "docker compose 插件未安装"

# ---- 3. 自动检测生产网络 ----
# 生产环境已知网络为 script_default，优先使用；也可通过 redis 容器动态确认
PROD_NETWORK=$(docker inspect redis --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>/dev/null | awk '{print $1}' || true)
if [ -z "$PROD_NETWORK" ]; then
    warn "无法自动检测生产网络（redis 容器未运行？），使用默认网络 script_default"
    PROD_NETWORK="script_default"
fi
log "生产网络: $PROD_NETWORK"

# ---- 4. 确认网络存在，不存在则报错（生产网络应由基础设施管理，不自动创建）----
if ! docker network inspect "$PROD_NETWORK" > /dev/null 2>&1; then
    error "网络 $PROD_NETWORK 不存在，请确认基础服务（redis/postgres/kafka/minio）已正常运行"
fi

# ---- 5. 构建镜像 ----
log "构建镜像 ${IMAGE_NAME}:${APP_VERSION} ..."
docker build \
    -f "$PUBLISH_DIR/Dockerfile.prod" \
    -t "${IMAGE_NAME}:${APP_VERSION}" \
    -t "${IMAGE_NAME}:latest" \
    --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --build-arg VERSION="$APP_VERSION" \
    "$PROJECT_DIR"
log "镜像构建完成: ${IMAGE_NAME}:${APP_VERSION}"

# ---- 6. 数据库初始化（首次部署）----
if [ "${INIT_DB:-false}" = "true" ]; then
    log "执行数据库初始化..."
    "$SCRIPT_DIR/db_init.sh" || error "数据库初始化失败"
fi

# ---- 7. 优雅停止旧容器 ----
if docker ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
    log "优雅停止旧容器 $CONTAINER_NAME（等待最多30s处理中的请求）..."
    docker stop --time=30 "$CONTAINER_NAME" || true
    docker rm "$CONTAINER_NAME" || true
    log "旧容器已停止"
fi

# ---- 8. 启动新容器 ----
log "启动新容器..."
cd "$PUBLISH_DIR"
APP_VERSION="$APP_VERSION" docker compose -f docker-compose.prod.yml up -d --no-build
log "容器已启动，等待健康检查..."

# ---- 9. 等待健康检查通过 ----
MAX_WAIT=120
WAITED=0
while true; do
    HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no_healthcheck{{end}}' \
        "$CONTAINER_NAME" 2>/dev/null || echo "not_found")
    case "$HEALTH" in
        healthy)
            log "健康检查通过 ✅"
            break
            ;;
        unhealthy)
            log "健康检查失败，查看容器日志："
            docker logs --tail=50 "$CONTAINER_NAME"
            error "部署失败：服务健康检查不通过"
            ;;
        not_found)
            error "容器 $CONTAINER_NAME 未找到"
            ;;
    esac
    if [ $WAITED -ge $MAX_WAIT ]; then
        log "健康检查超时，查看容器日志："
        docker logs --tail=50 "$CONTAINER_NAME"
        error "部署失败：服务未能在 ${MAX_WAIT}s 内通过健康检查"
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    log "等待中... ${WAITED}s / ${MAX_WAIT}s (状态: $HEALTH)"
done

# ---- 10. 部署完成 ----
log "===== 部署成功！quant_app v${APP_VERSION} 已运行 ====="
log "健康检查:  curl http://localhost:8000/health"
log "查看日志:  docker logs -f $CONTAINER_NAME"
log "容器状态:  docker ps -f name=$CONTAINER_NAME"
