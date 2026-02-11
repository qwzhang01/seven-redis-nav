#!/bin/bash
set -e

# ========================================
#  Quant Meta 一键部署脚本
# ========================================

IMAGE_NAME="quantmeta"
IMAGE_TAG="latest"
CONTAINER_NAME="quantmeta"
PORT="80"

echo "========================================="
echo "  Quant Meta 一键部署"
echo "========================================="
echo ""

# Step 1: 停止容器
echo "[1/5] 停止旧容器 ${CONTAINER_NAME} ..."
if docker ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
    docker stop "${CONTAINER_NAME}"
    echo "  ✔ 容器已停止"
else
    echo "  - 容器未运行，跳过"
fi

# Step 2: 删除容器
echo "[2/5] 删除旧容器 ${CONTAINER_NAME} ..."
if docker ps -aq -f name="^${CONTAINER_NAME}$" | grep -q .; then
    docker rm "${CONTAINER_NAME}"
    echo "  ✔ 容器已删除"
else
    echo "  - 容器不存在，跳过"
fi

# Step 3: 删除旧镜像
echo "[3/5] 删除旧镜像 ${IMAGE_NAME}:${IMAGE_TAG} ..."
if docker images -q "${IMAGE_NAME}:${IMAGE_TAG}" | grep -q .; then
    docker rmi "${IMAGE_NAME}:${IMAGE_TAG}"
    echo "  ✔ 镜像已删除"
else
    echo "  - 镜像不存在，跳过"
fi

# Step 4: 构建新镜像
echo "[4/5] 构建镜像 ${IMAGE_NAME}:${IMAGE_TAG} ..."
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
echo "  ✔ 镜像构建完成"

# Step 5: 运行容器
echo "[5/5] 启动容器 ${CONTAINER_NAME} (端口 ${PORT}) ..."
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${PORT}:80" \
    --restart unless-stopped \
    "${IMAGE_NAME}:${IMAGE_TAG}"
echo "  ✔ 容器已启动"

echo ""
echo "========================================="
echo "  部署完成！"
echo "  访问地址: http://localhost:${PORT}"
echo "========================================="
