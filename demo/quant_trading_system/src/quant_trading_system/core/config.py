"""
系统配置模块
============

使用 Pydantic Settings 进行配置管理，支持：
- 环境变量配置
- .env 文件配置
- 默认值配置
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    model_config = SettingsConfigDict()  # 移除env_prefix，直接读取环境变量

    # TimescaleDB 配置
    timescale_host: str = "localhost"
    timescale_port: int = 5432
    timescale_user: str = "quant"
    timescale_password: str = "quant123"
    timescale_database: str = "quant_trading"
    timescale_pool_size: int = 20
    timescale_max_overflow: int = 10

    # PostgreSQL 配置（关系数据）
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_user: str = "quant"
    postgres_password: str = "quant123"
    postgres_database: str = "quant_meta"

    @property
    def timescale_url(self) -> str:
        """优先使用DATABASE_URL环境变量，否则使用配置参数构建URL"""
        import os
        from urllib.parse import quote_plus

        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # 对URL中的密码进行编码
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            if parsed.password:
                # 对密码进行URL编码
                encoded_password = quote_plus(parsed.password)
                # 重新构建编码后的URL
                encoded_url = f"{parsed.scheme}://{parsed.username}:{encoded_password}@{parsed.hostname}:{parsed.port}{parsed.path}"
                return encoded_url.replace("postgresql://", "postgresql+asyncpg://")
            return database_url.replace("postgresql://", "postgresql+asyncpg://")

        return (
            f"postgresql+asyncpg://{self.timescale_user}:{self.timescale_password}"
            f"@{self.timescale_host}:{self.timescale_port}/{self.timescale_database}"
        )

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )


class RedisSettings(BaseSettings):
    """Redis 配置"""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    max_connections: int = 100

    # Redis Cluster 配置
    cluster_enabled: bool = False
    cluster_nodes: list[str] = Field(default_factory=list)

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class KafkaSettings(BaseSettings):
    """Kafka 配置"""

    model_config = SettingsConfigDict(env_prefix="KAFKA_")

    bootstrap_servers: str = "localhost:9092"
    client_id: str = "quant-trading-system"
    group_id: str = "quant-trading-group"

    # Topic 配置
    topic_tick: str = "market.tick"
    topic_kline: str = "market.kline"
    topic_order: str = "trading.order"
    topic_trade: str = "trading.trade"
    topic_signal: str = "strategy.signal"

    # 生产者配置
    producer_acks: str = "all"
    producer_retries: int = 3
    producer_batch_size: int = 16384
    producer_linger_ms: int = 5

    # 消费者配置
    consumer_auto_offset_reset: str = "latest"
    consumer_enable_auto_commit: bool = False
    consumer_max_poll_records: int = 500

    @property
    def bootstrap_servers_list(self) -> list[str]:
        return [s.strip() for s in self.bootstrap_servers.split(",")]


class StorageSettings(BaseSettings):
    """存储配置"""

    model_config = SettingsConfigDict(env_prefix="STORAGE_")

    # S3/MinIO 配置
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_data: str = "quant-data"
    s3_bucket_backup: str = "quant-backup"
    s3_region: str = "us-east-1"

    # 本地存储配置
    data_dir: Path = Path("./data")
    cache_dir: Path = Path("./cache")
    log_dir: Path = Path("./logs")

    # Parquet 配置
    parquet_compression: str = "snappy"
    parquet_row_group_size: int = 100000


class TradingSettings(BaseSettings):
    """交易配置"""

    model_config = SettingsConfigDict(env_prefix="TRADING_")

    # 订单配置
    order_timeout: int = 30  # 订单超时时间（秒）
    order_retry_times: int = 3
    order_retry_delay: float = 0.5

    # 滑点配置
    default_slippage: float = 0.0001
    max_slippage: float = 0.01

    # 手续费配置
    default_commission_rate: float = 0.0004
    min_commission: float = 0.0

    # 风控配置
    max_position_ratio: float = 0.8  # 最大仓位比例
    max_single_order_ratio: float = 0.1  # 单笔订单最大比例
    max_daily_loss_ratio: float = 0.05  # 日最大亏损比例
    max_drawdown_ratio: float = 0.2  # 最大回撤比例


class StrategySettings(BaseSettings):
    """策略配置"""

    model_config = SettingsConfigDict(env_prefix="STRATEGY_")

    # 策略目录
    strategy_dir: Path = Path("./strategies")

    # 回测配置
    backtest_start_capital: float = 1000000.0
    backtest_commission_rate: float = 0.0004
    backtest_slippage: float = 0.0001

    # 策略运行配置
    max_concurrent_strategies: int = 100
    strategy_heartbeat_interval: int = 10


class APISettings(BaseSettings):
    """API 配置"""

    model_config = SettingsConfigDict(env_prefix="API_")

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # JWT 配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24小时

    # CORS 配置
    cors_origins: list[str] = Field(default=["*"])

    # 限流配置
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # 秒


class MonitorSettings(BaseSettings):
    """监控配置"""

    model_config = SettingsConfigDict(env_prefix="MONITOR_")

    # Prometheus 配置
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"
    log_retention_days: int = 30

    # 告警配置
    alert_webhook_url: str = ""
    alert_email_enabled: bool = False
    alert_email_smtp_host: str = ""
    alert_email_smtp_port: int = 587
    alert_email_from: str = ""
    alert_email_to: list[str] = Field(default_factory=list)


class Settings(BaseSettings):
    """主配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 环境配置
    env: str = "development"  # development, testing, production
    debug: bool = True

    # 系统名称
    app_name: str = "量化交易系统"
    app_version: str = "1.0.0"

    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    strategy: StrategySettings = Field(default_factory=StrategySettings)
    api: APISettings = Field(default_factory=APISettings)
    monitor: MonitorSettings = Field(default_factory=MonitorSettings)

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if v not in ("development", "testing", "production"):
            raise ValueError("env must be one of: development, testing, production")
        return v

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
