# 多阶段构建 - 量化交易系统
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_TIMEOUT=300 \
    PIP_RETRIES=3 \
    PYTHONPATH=/app

# 安装系统依赖（包括ta-lib所需的依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    libpq-dev \
    # ta-lib依赖
    libta-lib-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 创建非root用户
RUN groupadd --gid 1000 quant \
    && useradd --uid 1000 --gid quant --shell /bin/bash --create-home quant

WORKDIR /app

# 构建阶段
FROM base as builder

# 复制依赖文件
COPY pyproject.toml ./

# 升级pip并安装构建工具
RUN pip install --upgrade pip \
    && pip install build setuptools wheel

# 构建并安装项目依赖（使用pyproject.toml中的依赖）
RUN pip install --timeout=300 --retries=3 .

# 运行阶段
FROM base as runner

# 安装运行时的健康检查工具
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 复制源码
COPY --chown=quant:quant src/ ./src/

# 复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 创建必要的目录
RUN mkdir -p /app/logs /app/data /app/cache \
    && chown -R quant:quant /app

# 切换到非root用户
USER quant

# 暴露端口
EXPOSE 8000

# 健康检查（使用Python内置HTTP客户端）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "quant_trading_system.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
