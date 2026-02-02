# 构建阶段
FROM golang:1.22-alpine AS builder

WORKDIR /app

# 安装依赖
RUN apk add --no-cache git

# 复制go.mod和go.sum
COPY go.mod go.sum ./
RUN go mod download

# 复制源代码
COPY . .

# 构建
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o market-service cmd/server/main.go

# 运行阶段
FROM alpine:3.19

WORKDIR /app

# 安装时区数据
RUN apk add --no-cache ca-certificates tzdata

# 复制可执行文件
COPY --from=builder /app/market-service .
COPY --from=builder /app/configs ./configs

# 设置时区
ENV TZ=Asia/Shanghai

# 暴露端口
EXPOSE 8080 50051

# 启动命令
CMD ["./market-service", "-config", "configs/config.yaml"]
