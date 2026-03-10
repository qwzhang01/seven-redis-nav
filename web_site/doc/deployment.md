# Quant Meta 部署文档

## 目录

- [项目概览](#项目概览)
- [环境要求](#环境要求)
- [本地开发](#本地开发)
- [生产构建](#生产构建)
- [部署方案](#部署方案)
  - [方案一：Nginx 部署（推荐）](#方案一nginx-部署推荐)
  - [方案二：Docker 部署](#方案二docker-部署)
  - [方案三：Docker Compose 部署](#方案三docker-compose-部署)
  - [方案四：Node.js 静态服务部署](#方案四nodejs-静态服务部署)
  - [方案五：云平台部署](#方案五云平台部署)
- [HTTPS / SSL 配置](#https--ssl-配置)
- [CI/CD 自动化部署](#cicd-自动化部署)
- [常见问题](#常见问题)

---

## 项目概览

| 项目 | 说明 |
|------|------|
| 名称 | Quant Meta - 量化策略广场 |
| 框架 | Vue 3.5 + TypeScript |
| 构建工具 | Vite 5.4 |
| UI 组件库 | TDesign Vue Next 1.13 |
| CSS 框架 | TailwindCSS 3.4 |
| 路由模式 | HTML5 History Mode |
| 构建产物 | 纯静态文件 (`dist/`) |

## 环境要求

| 软件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Node.js | 18.x | 20.x LTS |
| npm | 9.x | 10.x |
| Nginx | 1.18+ | 1.24+ |
| Docker | 20.10+ | 24.x+ |

---

## 本地开发

```bash
# 克隆仓库后进入项目目录
cd web_site

# 安装依赖
npm install

# 启动开发服务器 (默认 http://localhost:3000)
npm run dev

# 类型检查
npx vue-tsc --noEmit
```

## 生产构建

```bash
# 构建生产版本
npm run build
```

构建完成后，静态文件输出到 `dist/` 目录，结构如下：

```
dist/
├── index.html
├── favicon.svg
└── assets/
    ├── index-xxxx.js        # 主 JS bundle
    ├── index-xxxx.css       # 主 CSS
    ├── HomePage-xxxx.js     # 按页面 code-split 的 chunks
    ├── StrategyList-xxxx.js
    ├── SignalList-xxxx.js
    └── ...
```

### 构建环境变量（可选）

如需自定义 API 地址等配置，可创建 `.env.production` 文件：

```env
# .env.production
VITE_API_BASE_URL=https://api.quantmeta.com
VITE_APP_TITLE=Quant Meta
```

在代码中通过 `import.meta.env.VITE_API_BASE_URL` 访问。

---

## 部署方案

### 方案一：Nginx 部署（推荐）

**适用场景**：自有服务器、VPS、云主机

#### 1. 安装 Nginx

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y nginx

# CentOS / RHEL
sudo yum install -y nginx

# macOS
brew install nginx
```

#### 2. 上传构建产物

```bash
# 在本地构建
npm run build

# 上传 dist 目录到服务器
scp -r dist/* user@your-server:/var/www/quantmeta/
```

或使用 rsync（推荐，增量同步）：

```bash
rsync -avz --delete dist/ user@your-server:/var/www/quantmeta/
```

#### 3. Nginx 配置文件

创建 `/etc/nginx/conf.d/quantmeta.conf`：

```nginx
server {
    listen 80;
    server_name quantmeta.com www.quantmeta.com;  # 替换为你的域名

    root /var/www/quantmeta;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 1000;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
        application/json
        application/xml
        image/svg+xml;

    # 静态资源缓存 (Vite 构建的文件名含 hash，可长期缓存)
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # favicon 和其他静态文件
    location ~* \.(svg|ico|png|jpg|jpeg|gif|webp|woff2?|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public";
    }

    # Vue Router HTML5 History Mode 关键配置
    # 所有非文件请求都回退到 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # 如果有后端 API，配置反向代理
    # location /api/ {
    #     proxy_pass http://127.0.0.1:8080/;
    #     proxy_set_header Host $host;
    #     proxy_set_header X-Real-IP $remote_addr;
    #     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #     proxy_set_header X-Forwarded-Proto $scheme;
    # }
}
```

#### 4. 验证并重载

```bash
# 测试配置语法
sudo nginx -t

# 重载配置
sudo systemctl reload nginx

# 或重启
sudo systemctl restart nginx
```

---

### 方案二：Docker 部署

#### 1. 创建 Dockerfile

在项目根目录创建 `Dockerfile`：

```dockerfile
# ---- Build Stage ----
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build

# ---- Production Stage ----
FROM nginx:1.24-alpine AS production

# 复制自定义 Nginx 配置
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 2. 创建 Nginx 配置

创建 `docker/nginx.conf`：

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/javascript application/javascript application/json image/svg+xml;

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

#### 3. 构建并运行

```bash
# 构建镜像
docker build -t quantmeta:latest .

# 运行容器
docker run -d \
  --name quantmeta \
  -p 80:80 \
  --restart unless-stopped \
  quantmeta:latest

# 查看日志
docker logs -f quantmeta
```

#### 4. 更新部署

```bash
# 重新构建并替换
docker build -t quantmeta:latest .
docker stop quantmeta && docker rm quantmeta
docker run -d --name quantmeta -p 80:80 --restart unless-stopped quantmeta:latest
```

---

### 方案三：Docker Compose 部署

适合需要同时管理多个服务的场景。

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: quantmeta
    ports:
      - "80:80"
      - "443:443"
    volumes:
      # 如需挂载 SSL 证书
      # - ./ssl/cert.pem:/etc/nginx/ssl/cert.pem:ro
      # - ./ssl/key.pem:/etc/nginx/ssl/key.pem:ro
      - ./docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost/"]
      interval: 30s
      timeout: 5s
      retries: 3
```

```bash
# 启动
docker compose up -d

# 查看状态
docker compose ps

# 更新重新部署
docker compose up -d --build

# 停止
docker compose down
```

---

### 方案四：Node.js 静态服务部署

适合轻量场景或搭配 PM2 使用。

#### 1. 安装 serve

```bash
npm install -g serve
```

#### 2. 直接运行

```bash
# 构建
npm run build

# 启动静态服务 (-s 启用 SPA 模式，自动回退到 index.html)
serve -s dist -l 3000
```

#### 3. 使用 PM2 守护进程

```bash
# 安装 PM2
npm install -g pm2

# 启动
pm2 start "serve -s dist -l 3000" --name quantmeta

# 开机自启
pm2 startup
pm2 save

# 查看状态
pm2 status

# 查看日志
pm2 logs quantmeta

# 重启
pm2 restart quantmeta
```

---

### 方案五：云平台部署

#### Vercel

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署 (首次会引导配置)
vercel

# 生产部署
vercel --prod
```

项目根目录创建 `vercel.json` 处理 SPA 路由：

```json
{
  "rewrites": [
    { "source": "/((?!assets/).*)", "destination": "/index.html" }
  ]
}
```

#### Netlify

项目根目录创建 `netlify.toml`：

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

#### 腾讯云 COS + CDN

```bash
# 安装 COSCMD
pip install coscmd

# 配置
coscmd config -a <SecretId> -s <SecretKey> -b <bucket-name> -r ap-guangzhou

# 上传
npm run build
coscmd upload -r dist/ /

# 然后在腾讯云 CDN 控制台配置：
# - 源站类型：COS 源
# - 回源 Host：<bucket>.cos.ap-guangzhou.myqcloud.com
# - 错误页面：404 → /index.html (状态码 200) ← 关键！
```

---

## HTTPS / SSL 配置

### 使用 Let's Encrypt（免费）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 自动申请证书并配置 Nginx
sudo certbot --nginx -d quantmeta.com -d www.quantmeta.com

# 自动续期 (Certbot 默认已设置定时任务)
sudo certbot renew --dry-run
```

### 手动 Nginx HTTPS 配置

```nginx
server {
    listen 80;
    server_name quantmeta.com www.quantmeta.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name quantmeta.com www.quantmeta.com;

    ssl_certificate     /etc/letsencrypt/live/quantmeta.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/quantmeta.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    root /var/www/quantmeta;
    index index.html;

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## CI/CD 自动化部署

### GitHub Actions 示例

创建 `.github/workflows/deploy.yml`：

```yaml
name: Build & Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - run: npm ci
      - run: npm run build

      # 方式 A：部署到自有服务器
      - name: Deploy via SSH
        uses: easingthemes/ssh-deploy@v5
        with:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          REMOTE_HOST: ${{ secrets.SERVER_HOST }}
          REMOTE_USER: ${{ secrets.SERVER_USER }}
          SOURCE: dist/
          TARGET: /var/www/quantmeta/
          ARGS: "-avz --delete"

      # 方式 B：部署到 Docker Registry
      # - name: Build & Push Docker Image
      #   run: |
      #     docker build -t registry.example.com/quantmeta:${{ github.sha }} .
      #     docker push registry.example.com/quantmeta:${{ github.sha }}
```

### 所需 Secrets 配置

在 GitHub 仓库 → Settings → Secrets 中添加：

| Secret 名 | 说明 |
|-----------|------|
| `SSH_PRIVATE_KEY` | 服务器 SSH 私钥 |
| `SERVER_HOST` | 服务器 IP / 域名 |
| `SERVER_USER` | SSH 用户名 |

---

## 常见问题

### 1. 刷新页面 404

**原因**：项目使用 Vue Router 的 `History` 模式，刷新时浏览器向服务器请求实际路径（如 `/strategies`），但服务器上不存在该文件。

**解决**：确保 Nginx 配置了 `try_files $uri $uri/ /index.html;`，将所有不匹配的请求回退到 `index.html`。

### 2. 静态资源 404

**检查**：
- `dist/` 目录内容是否完整上传
- Nginx 的 `root` 路径是否正确指向 `dist/` 内容所在目录
- 文件权限是否允许 Nginx 用户读取（`chmod -R 755 /var/www/quantmeta`）

### 3. 部署到子路径（非根路径）

如果项目部署在 `https://example.com/quant/` 下：

**vite.config.ts**：
```ts
export default defineConfig({
  base: '/quant/',
  // ...
})
```

**router/index.ts**：
```ts
const router = createRouter({
  history: createWebHistory('/quant/'),
  // ...
})
```

**Nginx**：
```nginx
location /quant/ {
    alias /var/www/quantmeta/;
    try_files $uri $uri/ /quant/index.html;
}
```

### 4. 构建时 TypeScript 报错

```bash
# 跳过类型检查直接构建（临时方案）
npx vite build

# 正式构建（含类型检查）
npm run build
```

### 5. 字体加载慢

项目通过 Google Fonts CDN 加载 Inter 和 Noto Sans SC 字体。如果服务器在国内，建议：

1. 下载字体文件放到 `public/fonts/` 目录
2. 修改 `index.html`，移除 Google Fonts 链接
3. 在 CSS 中使用本地 `@font-face` 声明

### 6. 生产环境性能优化建议

- 开启 Nginx Gzip/Brotli 压缩
- 配置 CDN 加速静态资源
- Vite 构建产物已自动进行 code-split 和 tree-shaking
- 所有页面使用 `() => import(...)` 懒加载
- 图表库 (ECharts) 通过 vue-echarts 按需加载
