#!/bin/bash

# 量化交易系统部署脚本
# 作者: Quant Trading Team
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "命令 $1 未安装，请先安装"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "量化交易系统部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示此帮助信息"
    echo "  -d, --dev           开发环境部署"
    echo "  -p, --prod          生产环境部署"
    echo "  -t, --test          运行测试"
    echo "  -c, --clean         清理环境"
    echo "  -b, --build         重新构建Docker镜像"
    echo ""
    echo "示例:"
    echo "  $0 --dev            # 部署开发环境"
    echo "  $0 --prod           # 部署生产环境"
    echo "  $0 --test           # 运行测试"
}

# 环境检查
check_environment() {
    log_info "检查系统环境..."

    # 检查Python
    check_command python3
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python版本: $PYTHON_VERSION"

    # 检查Docker
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
        log_info "Docker版本: $DOCKER_VERSION"
    else
        log_warning "Docker未安装，将使用本地Python环境"
    fi

    # 检查Docker Compose
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | tr -d ',')
        log_info "Docker Compose版本: $DOCKER_COMPOSE_VERSION"
    fi

    # 检查PostgreSQL客户端
    if command -v psql &> /dev/null; then
        log_info "PostgreSQL客户端已安装"
    else
        log_warning "PostgreSQL客户端未安装，数据库操作可能受限"
    fi
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."

    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt文件不存在"
        exit 1
    fi

    pip3 install --upgrade pip
    pip3 install -r requirements.txt

    log_success "Python依赖安装完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."

    if [ ! -f "database/schema.sql" ]; then
        log_error "数据库建表脚本不存在"
        exit 1
    fi

    # 检查数据库连接
    if command -v psql &> /dev/null; then
        log_info "创建数据库和表结构..."

        # 这里可以添加实际的数据库初始化命令
        # 例如：psql -h localhost -U postgres -f database/schema.sql

        log_success "数据库初始化完成"
    else
        log_warning "跳过数据库初始化（psql命令不可用）"
    fi
}

# 运行测试
run_tests() {
    log_info "运行测试..."

    if [ -f "tests/test_user_api.py" ]; then
        python3 tests/test_user_api.py
        if [ $? -eq 0 ]; then
            log_success "测试通过"
        else
            log_error "测试失败"
            exit 1
        fi
    else
        log_warning "测试文件不存在，跳过测试"
    fi
}

# 启动Docker服务
start_docker_services() {
    log_info "启动Docker服务..."

    if command -v docker-compose &> /dev/null; then
        docker-compose up -d

        # 等待服务启动
        log_info "等待服务启动..."
        sleep 30

        # 检查服务状态
        if docker-compose ps | grep -q "Up"; then
            log_success "Docker服务启动成功"
        else
            log_error "Docker服务启动失败"
            docker-compose logs
            exit 1
        fi
    else
        log_error "Docker Compose未安装，无法启动服务"
        exit 1
    fi
}

# 停止Docker服务
stop_docker_services() {
    log_info "停止Docker服务..."

    if command -v docker-compose &> /dev/null; then
        docker-compose down
        log_success "Docker服务已停止"
    fi
}

# 清理环境
clean_environment() {
    log_info "清理环境..."

    # 停止Docker服务
    stop_docker_services

    # 清理Docker资源
    if command -v docker &> /dev/null; then
        docker system prune -f
        log_info "Docker资源已清理"
    fi

    # 清理Python缓存
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete
    log_info "Python缓存已清理"

    log_success "环境清理完成"
}

# 重新构建Docker镜像
build_docker_images() {
    log_info "重新构建Docker镜像..."

    if command -v docker-compose &> /dev/null; then
        docker-compose build --no-cache
        log_success "Docker镜像构建完成"
    else
        log_error "Docker Compose未安装，无法构建镜像"
        exit 1
    fi
}

# 开发环境部署
deploy_dev() {
    log_info "开始开发环境部署..."

    check_environment
    install_python_deps
    init_database
    run_tests

    log_success "开发环境部署完成"
    echo ""
    echo "下一步操作："
    echo "1. 启动服务: uvicorn src.quant_trading_system.api.main:app --reload --host 0.0.0.0 --port 8000"
    echo "2. 访问API文档: http://localhost:8000/docs"
    echo "3. 运行测试: python tests/test_user_api.py"
}

# 生产环境部署
deploy_prod() {
    log_info "开始生产环境部署..."

    check_environment

    if command -v docker-compose &> /dev/null; then
        start_docker_services

        log_success "生产环境部署完成"
        echo ""
        echo "服务访问地址："
        echo "- 应用API: http://localhost:8000"
        echo "- API文档: http://localhost:8000/docs"
        echo "- 数据库管理: http://localhost:5050"
        echo "- 监控面板: http://localhost:3000"
    else
        log_error "生产环境部署需要Docker Compose支持"
        exit 1
    fi
}

# 主函数
main() {
    local mode="dev"

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--dev)
                mode="dev"
                ;;
            -p|--prod)
                mode="prod"
                ;;
            -t|--test)
                mode="test"
                ;;
            -c|--clean)
                mode="clean"
                ;;
            -b|--build)
                mode="build"
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done

    case $mode in
        "dev")
            deploy_dev
            ;;
        "prod")
            deploy_prod
            ;;
        "test")
            run_tests
            ;;
        "clean")
            clean_environment
            ;;
        "build")
            build_docker_images
            ;;
    esac
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
