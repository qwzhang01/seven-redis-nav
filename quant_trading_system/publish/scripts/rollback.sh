#!/bin/bash
# ============================================================
# 量化交易系统 — 回滚脚本
# 用法: ./rollback.sh <版本号>
# 示例: ./rollback.sh 1.1.0
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLISH_DIR="$(dirname "$SCRIPT_DIR")"
TARGET_VERSION="${1:-}"
IMAGE_NAME="quant_app"
CONTAINER_NAME="quant_app"

log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]  $*"; }
warn()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN]  $*"; }
error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*"; exit 1; }

# ---- 检测生产网络 ----
PROD_NETWORK=$(docker inspect redis --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>/dev/null | awk '{print $1}' || true)
if [ -z "$PROD_NETWORK" ]; then
    warn "无法自动检测生产网络（redis 容器未运行？），使用默认网络 script_default"
    PROD_NETWORK="script_default"
fi
if ! docker network inspect "$PROD_NETWORK" > /dev/null 2>&1; then
    error "网络 $PROD_NETWORK 不存在，请确认基础服务已正常运行"
fi
log "生产网络: $PROD_NETWORK"

# ---- 参数检查 ----
if [ -z "$TARGET_VERSION" ]; then
    echo "用法: $0 <版本号>"
    echo ""
    echo "可用镜像版本："
    docker images "$IMAGE_NAME" --format "  {{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" | sort -V
    exit 1
fi

# ---- 检查目标镜像是否存在 ----
if ! docker image inspect "${IMAGE_NAME}:${TARGET_VERSION}" > /dev/null 2>&1; then
    echo "错误：镜像 ${IMAGE_NAME}:${TARGET_VERSION} 不存在"
    echo ""
    echo "可用镜像版本："
    docker images "$IMAGE_NAME" --format "  {{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" | sort -V
    exit 1
fi

# ---- 记录当前版本（用于回滚失败时恢复）----
CURRENT_VERSION=$(docker inspect --format='{{index .Config.Labels "version"}}' \
    "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
log "当前版本: $CURRENT_VERSION → 回滚目标: $TARGET_VERSION"

log "===== 开始回滚到 ${IMAGE_NAME}:${TARGET_VERSION} ====="

# ---- 停止当前容器 ----
if docker ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
    log "停止当前容器（等待最多30s）..."
    docker stop --time=30 "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

# ---- 重新打 latest 标签 ----
docker tag "${IMAGE_NAME}:${TARGET_VERSION}" "${IMAGE_NAME}:latest"
log "已将 ${IMAGE_NAME}:${TARGET_VERSION} 标记为 latest"

# ---- 启动回滚版本 ----
log "启动回滚版本..."
cd "$PUBLISH_DIR"
APP_VERSION="$TARGET_VERSION" PROD_NETWORK="$PROD_NETWORK" docker compose -f docker-compose.prod.yml up -d --no-build

# ---- 等待健康检查 ----
MAX_WAIT=120
WAITED=0
while true; do
    HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no_healthcheck{{end}}' \
        "$CONTAINER_NAME" 2>/dev/null || echo "not_found")
    if [ "$HEALTH" = "healthy" ]; then
        log "健康检查通过 ✅"
        break
    fi
    if [ "$HEALTH" = "unhealthy" ] || [ $WAITED -ge $MAX_WAIT ]; then
        log "回滚后健康检查失败，容器日志："
        docker logs --tail=30 "$CONTAINER_NAME"
        error "回滚失败：服务未能通过健康检查"
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    log "等待中... ${WAITED}s / ${MAX_WAIT}s"
done

log "===== 回滚成功！当前运行版本: ${TARGET_VERSION} ====="
