#!/usr/bin/env python3
"""
量化交易系统配置模块
管理应用的各种配置设置
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """应用配置类"""

    # 应用配置
    APP_NAME: str = "量化交易系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "postgresql://quant_user:quant_password@localhost:5432/quant_trading"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # 密码配置
    PASSWORD_MIN_LENGTH: int = 6
    PASSWORD_HASH_ROUNDS: int = 12

    # 邮件配置（用于密码重置）
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True

    # Redis配置（用于缓存和会话）
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "/var/log/quant_trading.log"

    # 安全配置
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    # API配置
    API_PREFIX: str = "/api/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    # 交易所API配置
    EXCHANGE_API_TIMEOUT: int = 30
    EXCHANGE_API_RETRY_COUNT: int = 3
    EXCHANGE_API_RATE_LIMIT: int = 10

    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["jpg", "jpeg", "png", "gif"]
    UPLOAD_DIR: str = "/var/uploads"

    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    HEALTH_CHECK_INTERVAL: int = 30

    # 测试配置
    TEST_DATABASE_URL: str = "sqlite:///./test.db"
    TEST_MODE: bool = False

    # 应用环境配置
    APP_ENV: str = "development"

    # 交易所API配置
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    BINANCE_TESTNET: bool = True
    OKX_API_KEY: Optional[str] = None
    OKX_SECRET_KEY: Optional[str] = None
    OKX_PASSPHRASE: Optional[str] = None

    # 数据源配置
    DATA_PROVIDER: str = "binance"
    HISTORICAL_DATA_PATH: str = "./data/historical"

    # 回测配置
    BACKTEST_START_DATE: str = "2024-01-01"
    BACKTEST_END_DATE: str = "2024-12-31"
    INITIAL_CAPITAL: float = 100000

    # 风控配置
    MAX_POSITION_SIZE: float = 0.1
    MAX_DRAWDOWN: float = 0.2
    STOP_LOSS_PCT: float = 0.02

    # 通知配置
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    EMAIL_SMTP_HOST: Optional[str] = None
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """验证数据库URL格式"""
        if not v:
            raise ValueError("DATABASE_URL不能为空")
        if not v.startswith(("postgresql://", "sqlite://")):
            raise ValueError("不支持的数据库类型")
        return v

    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret_key(cls, v):
        """验证JWT密钥长度"""
        if len(v) < 32:
            raise ValueError("JWT密钥长度至少32位")
        return v

    @validator("CORS_ORIGINS", pre=True)
    def validate_cors_origins(cls, v):
        """验证CORS来源，支持字符串和列表两种格式"""
        if not v:
            return ["*"]
        # 如果是字符串（来自环境变量），按逗号分割
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @validator("PASSWORD_MIN_LENGTH")
    def validate_password_min_length(cls, v):
        """验证密码最小长度"""
        if v < 6:
            raise ValueError("密码最小长度不能小于6位")
        return v

    @validator("PASSWORD_HASH_ROUNDS")
    def validate_password_hash_rounds(cls, v):
        """验证密码哈希轮数"""
        if v < 10 or v > 15:
            raise ValueError("密码哈希轮数应在10-15之间")
        return v

    @validator("RATE_LIMIT_REQUESTS")
    def validate_rate_limit_requests(cls, v):
        """验证速率限制请求数"""
        if v < 10:
            raise ValueError("速率限制请求数不能小于10")
        return v

    @validator("RATE_LIMIT_WINDOW")
    def validate_rate_limit_window(cls, v):
        """验证速率限制窗口"""
        if v < 10:
            raise ValueError("速率限制窗口不能小于10秒")
        return v

    @validator("EXCHANGE_API_TIMEOUT")
    def validate_exchange_api_timeout(cls, v):
        """验证交易所API超时时间"""
        if v < 10 or v > 60:
            raise ValueError("交易所API超时时间应在10-60秒之间")
        return v

    @validator("EXCHANGE_API_RETRY_COUNT")
    def validate_exchange_api_retry_count(cls, v):
        """验证交易所API重试次数"""
        if v < 1 or v > 5:
            raise ValueError("交易所API重试次数应在1-5次之间")
        return v

    @validator("EXCHANGE_API_RATE_LIMIT")
    def validate_exchange_api_rate_limit(cls, v):
        """验证交易所API速率限制"""
        if v < 1 or v > 100:
            raise ValueError("交易所API速率限制应在1-100之间")
        return v

    @validator("MAX_FILE_SIZE")
    def validate_max_file_size(cls, v):
        """验证最大文件大小"""
        if v < 1024 * 1024 or v > 50 * 1024 * 1024:
            raise ValueError("最大文件大小应在1MB-50MB之间")
        return v

    @validator("HEALTH_CHECK_INTERVAL")
    def validate_health_check_interval(cls, v):
        """验证健康检查间隔"""
        if v < 10 or v > 300:
            raise ValueError("健康检查间隔应在10-300秒之间")
        return v

    class Config:
        """配置类设置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            """自定义配置源优先级"""
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )


def get_settings() -> Settings:
    """
    获取配置实例
    用于依赖注入
    """
    return settings


# 开发环境配置
def get_dev_settings() -> Settings:
    """开发环境配置"""
    return Settings(
        DEBUG=True,
        DATABASE_URL="postgresql://quant_user:quant_password@localhost:5432/quant_trading_dev",
        CORS_ORIGINS=["*"]
    )


# 测试环境配置
def get_test_settings() -> Settings:
    """测试环境配置"""
    return Settings(
        DEBUG=False,
        TEST_MODE=True,
        DATABASE_URL="sqlite:///./test.db",
        JWT_SECRET_KEY="test-secret-key-for-testing-only",
        CORS_ORIGINS=["*"]
    )


# 生产环境配置
def get_prod_settings() -> Settings:
    """生产环境配置"""
    cors_origins_env = os.getenv("CORS_ORIGINS", "")
    if cors_origins_env:
        cors_origins_list = [item.strip() for item in cors_origins_env.split(",") if item.strip()]
    else:
        cors_origins_list = ["*"]

    return Settings(
        DEBUG=False,
        DATABASE_URL=os.getenv("DATABASE_URL"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
        SMTP_SERVER=os.getenv("SMTP_SERVER"),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME"),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
        REDIS_URL=os.getenv("REDIS_URL"),
        LOG_LEVEL="WARNING",
        CORS_ORIGINS=cors_origins_list
    )


# 环境检测
def get_environment() -> str:
    """获取当前环境"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env not in ["development", "testing", "production"]:
        return "development"
    return env


# 根据环境获取配置
def get_config() -> Settings:
    """根据环境获取配置"""
    env = get_environment()

    if env == "testing":
        return get_test_settings()
    elif env == "production":
        return get_prod_settings()
    else:
        return get_dev_settings()


# 全局配置实例
settings = get_config()
