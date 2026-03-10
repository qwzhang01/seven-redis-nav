.PHONY: help build deploy deploy-compose up down restart logs clean health status

# 默认目标
.DEFAULT_GOAL := help

# 变量定义
IMAGE_NAME ?= quantmeta
IMAGE_TAG ?= latest
CONTAINER_NAME ?= quantmeta

# 帮助信息
help:
	@echo "========================================="
	@echo "  Quant Meta 部署管理"
	@echo "========================================="
	@echo ""
	@echo "可用命令："
	@echo "  make build          - 构建 Docker 镜像"
	@echo "  make deploy         - 执行生产环境部署（零停机）"
	@echo "  make deploy-compose - 使用 docker-compose 部署"
	@echo "  make up             - 启动服务（docker-compose）"
	@echo "  make down           - 停止服务（docker-compose）"
	@echo "  make restart        - 重启服务"
	@echo "  make logs           - 查看日志"
	@echo "  make health         - 健康检查"
	@echo "  make status         - 查看服务状态"
	@echo "  make clean          - 清理资源"
	@echo "  make shell          - 进入容器 shell"
	@echo ""

# 构建镜像
build:
	@echo "构建镜像..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

# 生产环境部署
deploy:
	@echo "执行生产环境部署..."
	chmod +x deploy.sh
	./deploy.sh

# Docker Compose 部署
deploy-compose:
	@echo "使用 docker-compose 部署..."
	chmod +x deploy-compose.sh
	./deploy-compose.sh

# 启动服务
up:
	@echo "启动服务..."
	docker-compose up -d

# 停止服务
down:
	@echo "停止服务..."
	docker-compose down

# 重启服务
restart:
	@echo "重启服务..."
	docker-compose restart

# 查看日志
logs:
	docker-compose logs -f

# 健康检查
health:
	@echo "执行健康检查..."
	@docker inspect --format='{{.State.Health.Status}}' $(CONTAINER_NAME) 2>/dev/null || echo "容器未运行"

# 查看状态
status:
	@echo "服务状态："
	@docker ps -f name=$(CONTAINER_NAME)
	@echo ""
	@echo "资源使用："
	@docker stats $(CONTAINER_NAME) --no-stream 2>/dev/null || echo "容器未运行"

# 清理资源
clean:
	@echo "清理资源..."
	docker-compose down -v
	docker system prune -f
	@echo "清理完成"

# 进入容器
shell:
	docker exec -it $(CONTAINER_NAME) sh

# 查看 Nginx 配置
nginx-test:
	docker exec $(CONTAINER_NAME) nginx -t

# 重载 Nginx 配置
nginx-reload:
	docker exec $(CONTAINER_NAME) nginx -s reload

# 导出镜像
export:
	@echo "导出镜像..."
	docker save $(IMAGE_NAME):$(IMAGE_TAG) -o $(IMAGE_NAME)-$(IMAGE_TAG).tar
	@echo "镜像已导出到 $(IMAGE_NAME)-$(IMAGE_TAG).tar"

# 导入镜像
import:
	@echo "导入镜像..."
	docker load -i $(IMAGE_NAME)-$(IMAGE_TAG).tar
	@echo "镜像导入完成"
