# ========================================
# Build Stage - 构建前端资源
# ========================================
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 安装构建所需的系统依赖（Alpine musl 环境需要）
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    && ln -sf python3 /usr/bin/python

# 安装构建依赖（利用缓存层）
COPY package.json package-lock.json ./

# 关键修复：不要跳过可选依赖，Rollup 在 Alpine 环境需要 @rollup/rollup-linux-x64-musl
RUN npm ci --prefer-offline --no-audit --progress=false \
    && npm cache clean --force

# 复制源代码并构建
COPY . .

# 设置 NODE_ENV 并构建
ENV NODE_ENV=production
# 优化 Node.js 构建性能
ENV NODE_OPTIONS="--max-old-space-size=4096"

# 复制生产环境配置文件（如果存在）
# 生产环境使用空的 VITE_API_BASE_URL，让前端使用相对路径 /api/
RUN if [ -f .env.production ]; then \
        echo "使用 .env.production 配置"; \
        cat .env.production; \
    else \
        echo "创建默认 .env.production 配置"; \
        echo "VITE_API_BASE_URL=" > .env.production; \
    fi

# 使用并行构建加速
RUN npm run build \
    && ls -lah dist/ \
    && echo "✓ 构建完成"

# ========================================
# Production Stage - 生产环境
# ========================================
FROM nginx:1.24-alpine AS production

# 添加标签信息
LABEL maintainer="quantmeta@example.com" \
      version="1.0" \
      description="Quant Meta Web Application"

# 安装必要工具（用于健康检查和调试）
RUN apk add --no-cache \
    curl \
    tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apk del tzdata

# 创建非root用户
RUN addgroup -g 1001 -S nginx-app \
    && adduser -u 1001 -S nginx-app -G nginx-app

# 复制nginx配置
COPY --chown=nginx-app:nginx-app docker/nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder --chown=nginx-app:nginx-app /app/dist /usr/share/nginx/html

# 创建必要的目录并设置权限
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run \
    && chown -R nginx-app:nginx-app /var/cache/nginx /var/log/nginx /var/run \
    && chmod -R 755 /usr/share/nginx/html \
    && touch /var/run/nginx.pid \
    && chown nginx-app:nginx-app /var/run/nginx.pid

# 修改nginx配置以支持非root运行
RUN sed -i 's/listen\s*80;/listen 8080;/' /etc/nginx/conf.d/default.conf \
    && sed -i '/user\s*nginx;/d' /etc/nginx/nginx.conf \
    && sed -i 's,/var/run/nginx.pid,/var/run/nginx.pid,' /etc/nginx/nginx.conf \
    && sed -i '/^http {/a \    client_body_temp_path /tmp/client_temp;\n    proxy_temp_path /tmp/proxy_temp;\n    fastcgi_temp_path /tmp/fastcgi_temp;\n    uwsgi_temp_path /tmp/uwsgi_temp;\n    scgi_temp_path /tmp/scgi_temp;' /etc/nginx/nginx.conf

# 切换到非root用户
USER nginx-app

# 暴露端口（非特权端口）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
