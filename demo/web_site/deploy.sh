#!/bin/bash

# ========================================
#  Quant Meta 生产环境部署脚本
# ========================================

set -euo pipefail
IFS=$'\n\t'

# ========================================
# 配置变量
# ========================================
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly IMAGE_NAME="${IMAGE_NAME:-quantmeta}"
readonly IMAGE_TAG="${IMAGE_TAG:-latest}"
readonly CONTAINER_NAME="${CONTAINER_NAME:-quantmeta}"
readonly HOST_PORT="${HOST_PORT:-80}"
readonly CONTAINER_PORT="8080"
readonly BACKUP_TAG="${IMAGE_NAME}:backup-$(date +%Y%m%d-%H%M%S)"
readonly LOG_FILE="${SCRIPT_DIR}/deploy-$(date +%Y%m%d).log"
readonly MAX_HEALTH_CHECK_ATTEMPTS=30
readonly HEALTH_CHECK_INTERVAL=2

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# ========================================
# 工具函数
# ========================================

# 日志函数
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${LOG_FILE}"
}

# 错误处理
error_exit() {
    log_error "$1"
    log_error "部署失败，开始回滚..."
    rollback
    exit 1
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        error_exit "命令 '$1' 未找到，请先安装"
    fi
}

# 检查Docker服务
check_docker() {
    if ! docker info &> /dev/null; then
        error_exit "Docker 服务未运行或无权限访问"
    fi
}

# 健康检查
health_check() {
    local container_name="$1"
    local attempts=0
    
    log_info "开始健康检查..."
    
    while [ $attempts -lt $MAX_HEALTH_CHECK_ATTEMPTS ]; do
        if docker exec "${container_name}" curl -f http://localhost:${CONTAINER_PORT}/ &> /dev/null; then
            log_success "健康检查通过 (尝试 $((attempts + 1))/${MAX_HEALTH_CHECK_ATTEMPTS})"
            return 0
        fi
        
        attempts=$((attempts + 1))
        if [ $attempts -lt $MAX_HEALTH_CHECK_ATTEMPTS ]; then
            log_info "健康检查未通过，等待 ${HEALTH_CHECK_INTERVAL}s 后重试... ($attempts/${MAX_HEALTH_CHECK_ATTEMPTS})"
            sleep $HEALTH_CHECK_INTERVAL
        fi
    done
    
    log_error "健康检查失败，容器可能未正常启动"
    return 1
}

# 备份当前镜像
backup_image() {
    if docker images -q "${IMAGE_NAME}:${IMAGE_TAG}" | grep -q .; then
        log_info "备份当前镜像为 ${BACKUP_TAG}..."
        docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${BACKUP_TAG}" || log_warning "镜像备份失败"
        log_success "镜像已备份"
    else
        log_info "没有现有镜像需要备份"
    fi
}

# 回滚函数
rollback() {
    log_warning "开始回滚到备份版本..."
    
    # 停止并删除新容器
    if docker ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
        docker stop "${CONTAINER_NAME}" &> /dev/null || true
        docker rm "${CONTAINER_NAME}" &> /dev/null || true
    fi
    
    # 恢复备份镜像
    if docker images -q "${BACKUP_TAG}" | grep -q .; then
        docker tag "${BACKUP_TAG}" "${IMAGE_NAME}:${IMAGE_TAG}"
        
        # 启动旧版本容器
        docker run -d \
            --name "${CONTAINER_NAME}" \
            -p "${HOST_PORT}:${CONTAINER_PORT}" \
            --add-host=host.docker.internal:host-gateway \
            --restart unless-stopped \
            --health-cmd="curl -f http://localhost:${CONTAINER_PORT}/ || exit 1" \
            --health-interval=30s \
            --health-timeout=5s \
            --health-retries=3 \
            "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null || true
        
        log_success "已回滚到备份版本"
    else
        log_warning "未找到备份镜像，无法回滚"
    fi
}

# 清理旧的备份镜像（保留最近3个）
cleanup_old_backups() {
    log_info "清理旧的备份镜像..."
    local backups=$(docker images "${IMAGE_NAME}" --format "{{.Tag}}" | grep "^backup-" | sort -r | tail -n +4)
    
    if [ -n "$backups" ]; then
        echo "$backups" | while read -r tag; do
            docker rmi "${IMAGE_NAME}:${tag}" &> /dev/null || true
            log_info "已删除旧备份: ${IMAGE_NAME}:${tag}"
        done
    fi
}

# 清理悬空镜像
cleanup_dangling_images() {
    log_info "清理悬空镜像..."
    local dangling=$(docker images -f "dangling=true" -q)
    if [ -n "$dangling" ]; then
        docker rmi $dangling &> /dev/null || true
        log_success "悬空镜像已清理"
    else
        log_info "没有悬空镜像需要清理"
    fi
}

# ========================================
# 主部署流程
# ========================================

main() {
    echo "========================================="
    echo "  Quant Meta 生产环境部署"
    echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================="
    echo ""
    
    # 前置检查
    log_info "[1/9] 执行前置检查..."
    check_command docker
    check_command curl
    check_docker
    
    # 检查生产环境配置
    if [ ! -f "${SCRIPT_DIR}/.env.production" ]; then
        log_warning "未找到 .env.production 文件，将创建默认配置"
        cat > "${SCRIPT_DIR}/.env.production" << 'EOF'
# 生产环境配置
NODE_ENV=production
# API 使用相对路径，通过 NGINX 反向代理到宿主机的 8000 端口
VITE_API_BASE_URL=
EOF
        log_info "已创建 .env.production 文件"
    else
        log_info "使用现有的 .env.production 配置："
        cat "${SCRIPT_DIR}/.env.production" | tee -a "${LOG_FILE}"
    fi
    
    log_success "前置检查通过"
    echo ""
    
    # 备份当前镜像
    log_info "[2/9] 备份当前镜像..."
    backup_image
    echo ""
    
    # 停止旧容器（零停机部署：先不停止，等新容器启动后再停止）
    log_info "[3/9] 检查现有容器..."
    if docker ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
        log_info "发现运行中的容器，将在新容器启动后停止"
        OLD_CONTAINER_EXISTS=true
    else
        log_info "没有运行中的容器"
        OLD_CONTAINER_EXISTS=false
    fi
    echo ""
    
    # 构建新镜像
    log_info "[4/9] 构建新镜像 ${IMAGE_NAME}:${IMAGE_TAG}..."
    if docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" "${SCRIPT_DIR}" 2>&1 | tee -a "${LOG_FILE}"; then
        log_success "镜像构建完成"
    else
        error_exit "镜像构建失败"
    fi
    echo ""
    
    # 创建临时容器进行测试
    log_info "[5/9] 启动新容器..."
    local temp_container="${CONTAINER_NAME}-new"
    
    # 如果旧容器存在，使用不同的端口启动新容器
    local temp_port=$((HOST_PORT + 1000))
    
    if docker run -d \
        --name "${temp_container}" \
        -p "${temp_port}:${CONTAINER_PORT}" \
        --add-host=host.docker.internal:host-gateway \
        --restart unless-stopped \
        --health-cmd="curl -f http://localhost:${CONTAINER_PORT}/ || exit 1" \
        --health-interval=30s \
        --health-timeout=5s \
        --health-retries=3 \
        --health-start-period=10s \
        "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
        log_success "新容器已启动"
    else
        error_exit "新容器启动失败"
    fi
    echo ""
    
    # 健康检查
    log_info "[6/9] 执行健康检查..."
    if ! health_check "${temp_container}"; then
        docker logs "${temp_container}" | tail -20 | tee -a "${LOG_FILE}"
        docker stop "${temp_container}" &> /dev/null || true
        docker rm "${temp_container}" &> /dev/null || true
        error_exit "新容器健康检查失败"
    fi
    echo ""
    
    # 切换容器（零停机部署）
    log_info "[7/9] 切换到新容器..."
    
    # 停止并删除旧容器
    if [ "$OLD_CONTAINER_EXISTS" = true ]; then
        log_info "停止旧容器..."
        docker stop "${CONTAINER_NAME}" &> /dev/null || true
        docker rm "${CONTAINER_NAME}" &> /dev/null || true
        log_success "旧容器已停止"
    fi
    
    # 停止临时容器
    docker stop "${temp_container}" &> /dev/null || true
    docker rm "${temp_container}" &> /dev/null || true
    
    # 启动正式容器
    if docker run -d \
        --name "${CONTAINER_NAME}" \
        -p "${HOST_PORT}:${CONTAINER_PORT}" \
        --add-host=host.docker.internal:host-gateway \
        --restart unless-stopped \
        --health-cmd="curl -f http://localhost:${CONTAINER_PORT}/ || exit 1" \
        --health-interval=30s \
        --health-timeout=5s \
        --health-retries=3 \
        --health-start-period=10s \
        "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
        log_success "正式容器已启动"
    else
        error_exit "正式容器启动失败"
    fi
    echo ""
    
    # 最终健康检查
    log_info "[8/9] 最终健康检查..."
    if ! health_check "${CONTAINER_NAME}"; then
        error_exit "最终健康检查失败"
    fi
    echo ""
    
    # 清理工作
    log_info "[9/9] 执行清理工作..."
    cleanup_old_backups
    cleanup_dangling_images
    log_success "清理完成"
    echo ""
    
    # 部署成功
    echo "========================================="
    echo -e "${GREEN}  ✓ 部署成功！${NC}"
    echo "========================================="
    echo "  容器名称: ${CONTAINER_NAME}"
    echo "  镜像版本: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo "  访问地址: http://localhost:${HOST_PORT}"
    echo "  日志文件: ${LOG_FILE}"
    echo ""
    echo "  查看容器状态: docker ps -f name=${CONTAINER_NAME}"
    echo "  查看容器日志: docker logs -f ${CONTAINER_NAME}"
    echo "  查看健康状态: docker inspect --format='{{.State.Health.Status}}' ${CONTAINER_NAME}"
    echo "========================================="
}

# 捕获错误信号
trap 'error_exit "脚本执行被中断"' INT TERM

# 执行主函数
main "$@"
