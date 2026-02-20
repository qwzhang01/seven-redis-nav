#!/bin/bash
# ============================================================
# 量化交易系统 — 生产环境健康检查脚本
# 用法: ./health_check.sh
# ============================================================

set -uo pipefail

API_URL="http://localhost:8000"
FAILED=0

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
ok()   { log "  ✅  $*"; }
fail() { log "  ❌  $*"; FAILED=1; }
info() { log "  ℹ️   $*"; }

log "===== 量化交易系统 — 生产环境健康检查 ====="
echo ""

# ---- 1. 检查所有容器状态 ----
log "【容器状态】"
for name in quantmeta redis postgres-timescaledb kafka minio quant_app; do
    STATUS=$(docker inspect --format='{{.State.Status}}' "$name" 2>/dev/null || echo "not_found")
    HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}-{{end}}' \
        "$name" 2>/dev/null || echo "unknown")
    UPTIME=$(docker inspect --format='{{.State.StartedAt}}' "$name" 2>/dev/null || echo "")

    if [ "$STATUS" = "running" ]; then
        ok "$(printf '%-25s' "$name") status=running  health=$HEALTH"
    elif [ "$STATUS" = "not_found" ]; then
        fail "$(printf '%-25s' "$name") 容器不存在"
    else
        fail "$(printf '%-25s' "$name") status=$STATUS"
    fi
done
echo ""

# ---- 2. 检查 API 健康端点 ----
log "【API 健康检查】"
HTTP_CODE=$(curl -s -o /tmp/health_resp.json -w "%{http_code}" \
    -X GET "${API_URL}/api/v1/m/health/" \
    -H 'accept: application/json' \
    --max-time 5 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    RESP=$(cat /tmp/health_resp.json 2>/dev/null || echo "")
    ok "GET /api/v1/m/health/ → HTTP $HTTP_CODE  $RESP"
else
    fail "GET /api/v1/m/health/ → HTTP $HTTP_CODE（服务不可达或异常）"
fi

# ---- 3. 检查 API 路由可达性 ----
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    "${API_URL}/api/v1/system/status" --max-time 5 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    ok "GET /api/v1/system/status → HTTP $HTTP_CODE（路由可达）"
else
    fail "GET /api/v1/system/status → HTTP $HTTP_CODE"
fi
echo ""

# ---- 4. 检查端口监听 ----
log "【端口监听检查】"
for port_info in "80:quantmeta(Nginx)" "6379:Redis" "5432:PostgreSQL" "9092:Kafka" "9000:MinIO" "8000:quant_app"; do
    PORT=$(echo "$port_info" | cut -d: -f1)
    NAME=$(echo "$port_info" | cut -d: -f2)
    if curl -s --connect-timeout 3 "http://localhost:$PORT" > /dev/null 2>&1 \
        || nc -z localhost "$PORT" 2>/dev/null; then
        ok "端口 $PORT ($NAME) 可达"
    else
        # 对于非 HTTP 端口，尝试 TCP 连接
        if timeout 3 bash -c "echo >/dev/tcp/localhost/$PORT" 2>/dev/null; then
            ok "端口 $PORT ($NAME) 可达"
        else
            fail "端口 $PORT ($NAME) 不可达"
        fi
    fi
done
echo ""

# ---- 5. 检查磁盘空间 ----
log "【磁盘空间】"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 80 ]; then
    ok "磁盘使用率: ${DISK_USAGE}%"
elif [ "$DISK_USAGE" -lt 90 ]; then
    log "  ⚠️   磁盘使用率: ${DISK_USAGE}%（警告：超过80%）"
else
    fail "磁盘使用率: ${DISK_USAGE}%（危险：超过90%）"
fi
echo ""

# ---- 6. 检查容器资源使用 ----
log "【quant_app 资源使用】"
if docker ps -q -f name="^quant_app$" | grep -q .; then
    docker stats quant_app --no-stream --format \
        "  CPU: {{.CPUPerc}}  内存: {{.MemUsage}} ({{.MemPerc}})  网络: {{.NetIO}}"
fi
echo ""

# ---- 汇总 ----
log "===== 检查完成 ====="
if [ $FAILED -eq 0 ]; then
    log "所有检查通过 ✅"
    exit 0
else
    log "存在异常，请检查上方标记 ❌ 的项目"
    exit 1
fi
