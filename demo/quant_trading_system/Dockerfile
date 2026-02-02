# 多阶段构建 - 量化交易系统
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd --gid 1000 quant \
    && useradd --uid 1000 --gid quant --shell /bin/bash --create-home quant

WORKDIR /app

# 构建阶段
FROM base as builder

# 安装依赖
COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip wheel --no-deps --wheel-dir /app/wheels -e .

# 运行阶段
FROM base as runner

# 复制wheels并安装
COPY --from=builder /app/wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/*.whl \
    && rm -rf /wheels

# 复制源码
COPY --chown=quant:quant src/ ./src/

# 切换到非root用户
USER quant

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "quant_trading_system.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
