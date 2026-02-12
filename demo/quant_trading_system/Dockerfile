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
    # ta-lib依赖
    libta-lib-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd --gid 1000 quant \
    && useradd --uid 1000 --gid quant --shell /bin/bash --create-home quant

WORKDIR /app

# 构建阶段
FROM base as builder

# 复制依赖文件
COPY pyproject.toml ./

# 分批次安装依赖，避免超时和冲突
RUN pip install --upgrade pip

# 先安装基础依赖
RUN pip install --timeout=300 --retries=3 fastapi uvicorn websockets python-multipart numpy pandas

# 安装数据库和消息队列依赖
RUN pip install --timeout=300 --retries=3 sqlalchemy redis kafka-python asyncpg aioredis

# 安装配置和安全依赖
RUN pip install --timeout=300 --retries=3 pydantic pydantic-settings python-dotenv pyyaml \
    python-jose[cryptography] passlib[bcrypt] cryptography

# 安装工具和监控依赖
RUN pip install --timeout=300 --retries=3 httpx orjson msgpack cachetools tenacity click \
    structlog prometheus-client

# 最后安装可选依赖（可能较慢或需要编译）
RUN pip install --timeout=600 --retries=5 pyarrow boto3

# 安装项目本身（可编辑模式），不安装可选依赖
RUN pip install --timeout=300 --retries=3 -e . --no-deps

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
