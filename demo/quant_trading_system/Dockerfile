# 多阶段构建 - 量化交易系统
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_TIMEOUT=300 \
    PIP_RETRIES=3

# 安装系统依赖（包括ta-lib所需的依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd --gid 1000 quant \
    && useradd --uid 1000 --gid quant --shell /bin/bash --create-home quant

WORKDIR /app

# 构建阶段
FROM base as builder

# 复制依赖文件
COPY pyproject.toml ./

# 分批次安装依赖，避免超时
RUN pip install --upgrade pip \
    && pip install --timeout=300 --retries=3 fastapi uvicorn websockets python-multipart \
    && pip install --timeout=300 --retries=3 numpy pandas sqlalchemy redis \
    && pip install --timeout=300 --retries=3 kafka-python pyarrow boto3 \
    && pip install --timeout=300 --retries=3 -e .

# 运行阶段
FROM base as runner

# 复制源码
COPY --chown=quant:quant src/ ./src/

# 复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 切换到非root用户
USER quant

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "quant_trading_system.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
