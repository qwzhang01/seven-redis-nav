#!/bin/bash
# ============================================================
# 量化交易系统 — 数据库初始化脚本
# 用法: ./db_init.sh
# 说明: 首次部署时执行，已初始化则自动跳过
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUBLISH_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$PUBLISH_DIR")"
ENV_FILE="$PUBLISH_DIR/.env.prod"
SCHEMA_FILE="$PROJECT_DIR/database/schema.sql"

log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]  $*"; }
error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*"; exit 1; }

log "===== 数据库初始化 ====="

# ---- 检查文件 ----
[ -f "$ENV_FILE" ]    || error ".env.prod 不存在"
[ -f "$SCHEMA_FILE" ] || error "schema.sql 不存在: $SCHEMA_FILE"

# ---- 从 .env.prod 读取数据库配置 ----
DB_CONTAINER="postgres-timescaledb"

# 解析 DATABASE_URL: postgresql://user:password@host:port/dbname
DATABASE_URL=$(grep '^DATABASE_URL=' "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
if [ -z "$DATABASE_URL" ]; then
    error "DATABASE_URL 未在 .env.prod 中配置"
fi

# 提取数据库名和用户名
DB_USER=$(echo "$DATABASE_URL" | sed 's|postgresql://||' | cut -d':' -f1)
DB_NAME=$(echo "$DATABASE_URL" | sed 's|.*/||' | cut -d'?' -f1)

log "数据库容器: $DB_CONTAINER"
log "数据库用户: $DB_USER"
log "数据库名称: $DB_NAME"

# ---- 检查容器是否运行 ----
docker ps -q -f name="^${DB_CONTAINER}$" | grep -q . \
    || error "容器 $DB_CONTAINER 未运行，请确认 PostgreSQL/TimescaleDB 已启动"

# ---- 等待数据库就绪 ----
log "等待数据库就绪..."
MAX_WAIT=60
WAITED=0
until docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        error "数据库在 ${MAX_WAIT}s 内未就绪"
    fi
    sleep 3
    WAITED=$((WAITED + 3))
    log "等待数据库... ${WAITED}s"
done
log "数据库已就绪"

# ---- 检查是否已初始化（幂等保护）----
TABLE_EXISTS=$(docker exec "$DB_CONTAINER" \
    psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT COUNT(*) FROM information_schema.tables \
     WHERE table_schema='public' AND table_name='user_info';" 2>/dev/null || echo "0")

if [ "$TABLE_EXISTS" = "1" ]; then
    log "数据库已初始化（user_info 表已存在），跳过"
    log "如需重新初始化，请手动执行："
    log "  docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME < $SCHEMA_FILE"
    exit 0
fi

# ---- 执行建表脚本 ----
log "执行建表脚本: $SCHEMA_FILE"
docker exec -i "$DB_CONTAINER" \
    psql -U "$DB_USER" -d "$DB_NAME" < "$SCHEMA_FILE"

# ---- 验证初始化结果 ----
TABLES=$(docker exec "$DB_CONTAINER" \
    psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT string_agg(table_name, ', ' ORDER BY table_name) \
     FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "")

log "已创建的表: $TABLES"
log "===== 数据库初始化完成 ====="
