"""
系统配置模块
============

使用 Pydantic Settings 进行配置管理，支持：
- 环境变量配置
- .env 文件配置
- 默认值配置
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

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

    # 连接池配置（兼容外层配置）
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_pool_recycle: int = 3600

    @property
    def timescale_url(self) -> str:
        """优先使用DATABASE_URL环境变量，否则使用配置参数构建URL"""
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

    # 兼容外层风控字段
    max_position_size: float = 0.1
    max_drawdown: float = 0.2
    stop_loss_pct: float = 0.02


class StrategySettings(BaseSettings):
    """策略配置"""

    model_config = SettingsConfigDict(env_prefix="STRATEGY_")

    # 策略目录
    strategy_dir: Path = Path("./strategies")

    # 回测配置
    backtest_start_capital: float = 1000000.0
    backtest_commission_rate: float = 0.0004
    backtest_slippage: float = 0.0001
    backtest_start_date: str = "2024-01-01"
    backtest_end_date: str = "2024-12-31"
    initial_capital: float = 100000

    # 策略运行配置
    max_concurrent_strategies: int = 100
    strategy_heartbeat_interval: int = 10


class ExchangeSettings(BaseSettings):
    """交易所 API 配置"""

    model_config = SettingsConfigDict()  # 不使用env_prefix，直接读取环境变量

    # Binance
    binance_api_key: Optional[str] = None
    binance_secret_key: Optional[str] = None
    binance_testnet: bool = True

    # 通用交易所 API 配置
    exchange_api_timeout: int = 30
    exchange_api_retry_count: int = 3
    exchange_api_rate_limit: int = 10

    # 数据源
    data_provider: str = "binance"
    historical_data_path: str = "./data/historical"

    # 行情数据同步开关（控制是否订阅和同步对应类型的行情数据）
    sync_kline: bool = True    # 是否同步K线数据
    sync_tick: bool = False     # 是否同步Tick数据（逐笔成交/Ticker）
    sync_depth: bool = False    # 是否同步深度数据


class SecuritySettings(BaseSettings):
    """安全配置"""

    model_config = SettingsConfigDict()  # 直接读取环境变量

    # 密码配置
    password_min_length: int = 6
    password_hash_rounds: int = 12

    # 主机白名单（逗号分隔字符串）
    allowed_hosts: str = "localhost,127.0.0.1"

    @property
    def allowed_hosts_list(self) -> List[str]:
        if not self.allowed_hosts or self.allowed_hosts.strip() == "":
            return ["localhost", "127.0.0.1"]
        return [item.strip() for item in self.allowed_hosts.split(",") if item.strip()]


class NotificationSettings(BaseSettings):
    """通知配置"""

    model_config = SettingsConfigDict()  # 直接读取环境变量

    # 邮件 SMTP 配置（统一，同时用于通知和告警）
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True

    # Telegram 配置
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None


class FileUploadSettings(BaseSettings):
    """文件上传配置"""

    model_config = SettingsConfigDict()  # 直接读取环境变量

    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: str = "jpg,jpeg,png,gif"
    upload_dir: str = "/var/uploads"

    @property
    def allowed_file_types_list(self) -> List[str]:
        if not self.allowed_file_types or self.allowed_file_types.strip() == "":
            return ["jpg", "jpeg", "png", "gif"]
        return [item.strip() for item in self.allowed_file_types.split(",") if item.strip()]


class JWTSettings(BaseSettings):
    """JWT 认证配置"""

    model_config = SettingsConfigDict()  # 直接读取 JWT_* 环境变量

    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7


class CORSSettings(BaseSettings):
    """CORS 配置"""

    model_config = SettingsConfigDict()  # 直接读取 CORS_* 环境变量

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """返回CORS来源列表，供中间件使用"""
        if not self.cors_origins or self.cors_origins.strip() == "":
            return ["*"]
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


class APISettings(BaseSettings):
    """API 配置"""

    model_config = SettingsConfigDict()  # 直接读取环境变量，不加前缀

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    api_prefix: str = "/api/v1"

    # 限流配置
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # 秒

    # 文档配置
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


class MonitorSettings(BaseSettings):
    """监控配置"""

    model_config = SettingsConfigDict()  # 直接读取环境变量，不加前缀

    # Prometheus 配置
    enable_metrics: bool = True
    metrics_port: int = 9090

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "./logs/quant_trading.log"
    log_retention_days: int = 30

    # 健康检查
    health_check_interval: int = 30

    # 告警配置
    alert_webhook_url: str = ""
    alert_email_enabled: bool = False
    # 告警邮件的 SMTP 连接复用 NotificationSettings 中的统一配置
    # 此处仅保留告警特有的发件人和收件人
    alert_email_from: str = ""
    alert_email_to: list[str] = Field(default_factory=list)


class Settings(BaseSettings):
    """主配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # 环境配置
    env: str = Field(default="development", alias="ENVIRONMENT")  # development, testing, production
    debug: bool = True

    # 系统名称
    app_name: str = "量化交易系统"
    app_version: str = "1.0.0"

    # 测试配置
    test_database_url: str = "sqlite:///./test.db"
    test_mode: bool = False

    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    strategy: StrategySettings = Field(default_factory=StrategySettings)
    exchange: ExchangeSettings = Field(default_factory=ExchangeSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    file_upload: FileUploadSettings = Field(default_factory=FileUploadSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
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

    # ── 兼容属性：让旧代码中 settings.XXX 的访问方式继续工作 ──

    # JWT 相关
    @property
    def JWT_SECRET_KEY(self) -> str:
        return self.jwt.jwt_secret_key

    @property
    def JWT_ALGORITHM(self) -> str:
        return self.jwt.jwt_algorithm

    @property
    def JWT_EXPIRE_MINUTES(self) -> int:
        return self.jwt.jwt_expire_minutes

    @property
    def JWT_REFRESH_EXPIRE_DAYS(self) -> int:
        return self.jwt.jwt_refresh_expire_days

    # CORS 相关
    @property
    def CORS_ORIGINS(self) -> str:
        return self.cors.cors_origins

    @property
    def cors_origins_list(self) -> List[str]:
        return self.cors.cors_origins_list

    # 交易所 API 相关
    @property
    def BINANCE_API_KEY(self) -> Optional[str]:
        return self.exchange.binance_api_key

    @property
    def BINANCE_SECRET_KEY(self) -> Optional[str]:
        return self.exchange.binance_secret_key

    @property
    def BINANCE_TESTNET(self) -> bool:
        return self.exchange.binance_testnet

    # 行情数据同步开关
    @property
    def SYNC_KLINE(self) -> bool:
        return self.exchange.sync_kline

    @property
    def SYNC_TICK(self) -> bool:
        return self.exchange.sync_tick

    @property
    def SYNC_DEPTH(self) -> bool:
        return self.exchange.sync_depth

    # 日志相关
    @property
    def LOG_LEVEL(self) -> str:
        return self.monitor.log_level

    @property
    def LOG_FILE(self) -> str:
        return self.monitor.log_file

    # 监控相关
    @property
    def ENABLE_METRICS(self) -> bool:
        return self.monitor.enable_metrics

    @property
    def METRICS_PORT(self) -> int:
        return self.monitor.metrics_port

    @property
    def HEALTH_CHECK_INTERVAL(self) -> int:
        return self.monitor.health_check_interval

    # 安全相关
    @property
    def PASSWORD_MIN_LENGTH(self) -> int:
        return self.security.password_min_length

    @property
    def PASSWORD_HASH_ROUNDS(self) -> int:
        return self.security.password_hash_rounds

    @property
    def ALLOWED_HOSTS(self) -> str:
        return self.security.allowed_hosts

    @property
    def allowed_hosts_list(self) -> List[str]:
        return self.security.allowed_hosts_list

    # 限流相关
    @property
    def RATE_LIMIT_REQUESTS(self) -> int:
        return self.api.rate_limit_requests

    @property
    def RATE_LIMIT_WINDOW(self) -> int:
        return self.api.rate_limit_window

    # API 相关
    @property
    def API_PREFIX(self) -> str:
        return self.api.api_prefix

    @property
    def DOCS_URL(self) -> str:
        return self.api.docs_url

    @property
    def REDOC_URL(self) -> str:
        return self.api.redoc_url

    # 数据库相关
    @property
    def DATABASE_URL(self) -> str:
        return self.database.timescale_url


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
