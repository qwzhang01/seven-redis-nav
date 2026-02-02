#!/bin/bash
# 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Go行情处理系统启动脚本 ===${NC}"

# 检查Go版本
echo -e "${YELLOW}检查Go版本...${NC}"
if ! command -v go &> /dev/null; then
    echo -e "${RED}错误: 未安装Go${NC}"
    echo "请先安装Go 1.22+: https://go.dev/dl/"
    exit 1
fi

GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
echo "Go版本: $GO_VERSION"

# 检查配置文件
CONFIG_FILE="configs/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}错误: 配置文件不存在: $CONFIG_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}配置文件: $CONFIG_FILE${NC}"

# 下载依赖
echo -e "${YELLOW}下载依赖...${NC}"
go mod tidy

# 构建
echo -e "${YELLOW}构建项目...${NC}"
go build -o bin/market-service cmd/server/main.go

echo -e "${GREEN}构建完成: bin/market-service${NC}"

# 启动服务
echo -e "${GREEN}启动服务...${NC}"
./bin/market-service -config $CONFIG_FILE
