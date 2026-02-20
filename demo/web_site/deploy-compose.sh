#!/bin/bash

# ========================================
#  Quant Meta Docker Compose 部署脚本
# ========================================

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ENV_FILE="${SCRIPT_DIR}/.env"

# 颜色输出
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# 检查环境文件
check_env() {
    if [ ! -f "${ENV_FILE}" ]; then
        log_warning ".env 文件不存在，从示例文件创建..."
        if [ -f "${SCRIPT_DIR}/.env.example" ]; then
            cp "${SCRIPT_DIR}/.env.example" "${ENV_FILE}"
            log_info ".env 文件已创建，请根据需要修改配置"
        else
            log_error ".env.example 文件不存在"
            exit 1
        fi
    fi
}

# 主函数
main() {
    echo "========================================="
    echo "  Quant Meta Docker Compose 部署"
    echo "========================================="
    echo ""
    
    check_env
    
    log_info "启动服务..."
    docker-compose up -d --build
    
    echo ""
    log_info "等待服务启动..."
    sleep 5
    
    log_info "检查服务状态..."
    docker-compose ps
    
    echo ""
    echo "========================================="
    echo -e "${GREEN}  ✓ 部署完成！${NC}"
    echo "========================================="
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo "========================================="
}

main "$@"
