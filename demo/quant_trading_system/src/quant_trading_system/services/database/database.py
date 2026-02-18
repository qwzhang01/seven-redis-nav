"""
TimescaleDB 数据库连接和表结构定义

提供实时行情数据存储和回测数据查询功能
"""

import asyncio
import structlog
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 加载环境变量
load_dotenv()

logger = structlog.get_logger(__name__)

# 创建数据库引擎和会话工厂
engine = create_engine(
    os.getenv("DATABASE_URL", "postgresql://quant:quant123@localhost:5432/quant_trading")
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖函数

    返回:
        Generator[Session]: 数据库会话生成器
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TimescaleDB:
    """TimescaleDB 数据库连接管理器"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "quant_trading",
        user: str = "quant",
        password: str = "quant123",
        min_conn: int = 1,
        max_conn: int = 10
    ):
        # 优先使用环境变量中的DATABASE_URL
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # 解析数据库URL
            parsed_url = urlparse(database_url)
            self.host = parsed_url.hostname or "localhost"
            self.port = parsed_url.port or 5432
            self.database = parsed_url.path.lstrip('/') or "quant_trading"
            self.user = parsed_url.username or "quant"
            # 处理密码中的引号
            password = parsed_url.password or "quant123"
            if password and password.startswith("'") and password.endswith("'"):
                password = password[1:-1]
            self.password = password
        else:
            # 使用默认参数
            self.host = host
            self.port = port
            self.database = database
            self.user = user
            self.password = password

        self.min_conn = min_conn
        self.max_conn = max_conn
        self._connection_pool: Optional[Any] = None

    async def connect(self) -> None:
        """连接到TimescaleDB数据库"""
        try:
            import psycopg2.pool

            self._connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=self.min_conn,
                maxconn=self.max_conn,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )

            # 测试连接
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]

            logger.info("TimescaleDB connected successfully", version=version)

        except Exception as e:
            logger.error("Failed to connect to TimescaleDB", error=str(e))
            raise

    async def disconnect(self) -> None:
        """断开数据库连接"""
        if self._connection_pool:
            self._connection_pool.closeall()
            self._connection_pool = None
            logger.info("TimescaleDB disconnected")

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        if not self._connection_pool:
            raise RuntimeError("Database connection pool not initialized")

        conn = self._connection_pool.getconn()
        try:
            yield conn
        finally:
            self._connection_pool.putconn(conn)

    async def initialize_tables(self) -> None:
        """初始化数据库表结构"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 检查TimescaleDB扩展是否可用
                cursor.execute("SELECT * FROM pg_extension WHERE extname = 'timescaledb'")
                timescaledb_available = cursor.fetchone() is not None

                if timescaledb_available:
                    logger.info("TimescaleDB扩展可用，将创建超表")
                else:
                    logger.info("TimescaleDB扩展不可用，将创建普通PostgreSQL表")

                # 创建K线数据表（时序表）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS kline_data (
                        id BIGSERIAL PRIMARY KEY,
                        symbol VARCHAR(32) NOT NULL,
                        exchange VARCHAR(32) NOT NULL,
                        timeframe VARCHAR(8) NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        open DECIMAL(20, 8) NOT NULL,
                        high DECIMAL(20, 8) NOT NULL,
                        low DECIMAL(20, 8) NOT NULL,
                        close DECIMAL(20, 8) NOT NULL,
                        volume DECIMAL(30, 8) NOT NULL,
                        turnover DECIMAL(30, 8),
                        is_closed BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)

                # 如果TimescaleDB可用，将kline_data表转换为时序表
                if timescaledb_available:
                    try:
                        cursor.execute("""
                            SELECT create_hypertable('kline_data', 'timestamp',
                            if_not_exists => TRUE);
                        """)
                    except Exception as e:
                        # 如果创建超表失败，可能是由于唯一索引问题
                        # 先回滚事务，然后重新创建表，再创建超表
                        logger.warning("创建超表失败，重新创建表", error=str(e))
                        conn.rollback()

                        # 重新创建kline_data表
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS kline_data (
                                id BIGSERIAL,
                                symbol VARCHAR(32) NOT NULL,
                                exchange VARCHAR(32) NOT NULL,
                                timeframe VARCHAR(8) NOT NULL,
                                timestamp TIMESTAMPTZ NOT NULL,
                                open DECIMAL(20, 8) NOT NULL,
                                high DECIMAL(20, 8) NOT NULL,
                                low DECIMAL(20, 8) NOT NULL,
                                close DECIMAL(20, 8) NOT NULL,
                                volume DECIMAL(30, 8) NOT NULL,
                                turnover DECIMAL(30, 8),
                                is_closed BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMPTZ DEFAULT NOW()
                            );
                        """)

                        cursor.execute("""
                            SELECT create_hypertable('kline_data', 'timestamp',
                            if_not_exists => TRUE);
                        """)

                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_kline_symbol_timeframe
                    ON kline_data (symbol, timeframe, timestamp DESC);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_kline_timestamp
                    ON kline_data (timestamp DESC);
                """)

                # 创建实时行情数据表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tick_data (
                        id BIGSERIAL PRIMARY KEY,
                        symbol VARCHAR(32) NOT NULL,
                        exchange VARCHAR(32) NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        price DECIMAL(20, 8) NOT NULL,
                        volume DECIMAL(30, 8) NOT NULL,
                        bid_price DECIMAL(20, 8),
                        ask_price DECIMAL(20, 8),
                        bid_size DECIMAL(30, 8),
                        ask_size DECIMAL(30, 8),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)

                # 如果TimescaleDB可用，将tick_data表转换为时序表
                if timescaledb_available:
                    try:
                        cursor.execute("""
                            SELECT create_hypertable('tick_data', 'timestamp',
                            if_not_exists => TRUE);
                        """)
                    except Exception as e:
                        # 如果创建超表失败，可能是由于唯一索引问题
                        # 先回滚事务，然后重新创建表，再创建超表
                        logger.warning("创建超表失败，重新创建表", error=str(e))
                        conn.rollback()

                        # 重新创建tick_data表
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS tick_data (
                                id BIGSERIAL,
                                symbol VARCHAR(32) NOT NULL,
                                exchange VARCHAR(32) NOT NULL,
                                timestamp TIMESTAMPTZ NOT NULL,
                                price DECIMAL(20, 8) NOT NULL,
                                volume DECIMAL(30, 8) NOT NULL,
                                bid_price DECIMAL(20, 8),
                                ask_price DECIMAL(20, 8),
                                bid_size DECIMAL(30, 8),
                                ask_size DECIMAL(30, 8),
                                created_at TIMESTAMPTZ DEFAULT NOW()
                            );
                        """)

                        cursor.execute("""
                            SELECT create_hypertable('tick_data', 'timestamp',
                            if_not_exists => TRUE);
                        """)

                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tick_symbol
                    ON tick_data (symbol, timestamp DESC);
                """)

                # 创建深度数据表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS depth_data (
                        id BIGSERIAL PRIMARY KEY,
                        symbol VARCHAR(32) NOT NULL,
                        exchange VARCHAR(32) NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        bids JSONB NOT NULL,
                        asks JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)

                # 如果TimescaleDB可用，将depth_data表转换为时序表
                if timescaledb_available:
                    try:
                        cursor.execute("""
                            SELECT create_hypertable('depth_data', 'timestamp',
                            if_not_exists => TRUE);
                        """)
                    except Exception as e:
                        # 如果创建超表失败，可能是由于唯一索引问题
                        # 先回滚事务，然后重新创建表，再创建超表
                        logger.warning("创建超表失败，重新创建表", error=str(e))
                        conn.rollback()

                        # 重新创建depth_data表
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS depth_data (
                                id BIGSERIAL,
                                symbol VARCHAR(32) NOT NULL,
                                exchange VARCHAR(32) NOT NULL,
                                timestamp TIMESTAMPTZ NOT NULL,
                                bids JSONB NOT NULL,
                                asks JSONB NOT NULL,
                                created_at TIMESTAMPTZ DEFAULT NOW()
                            );
                        """)

                        cursor.execute("""
                            SELECT create_hypertable('depth_data', 'timestamp',
                            if_not_exists => TRUE);
                        """)

                # 创建回测结果表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS backtest_results (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        strategy_name VARCHAR(128) NOT NULL,
                        start_time TIMESTAMPTZ NOT NULL,
                        end_time TIMESTAMPTZ NOT NULL,
                        initial_capital DECIMAL(20, 2) NOT NULL,
                        final_capital DECIMAL(20, 2) NOT NULL,
                        total_return DECIMAL(10, 6) NOT NULL,
                        annual_return DECIMAL(10, 6),
                        max_drawdown DECIMAL(10, 6),
                        sharpe_ratio DECIMAL(10, 6),
                        total_trades INTEGER NOT NULL,
                        win_rate DECIMAL(10, 6),
                        total_commission DECIMAL(20, 2),
                        total_slippage DECIMAL(20, 2),
                        equity_curve JSONB,
                        trades JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)

                # 创建用户管理相关表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_info (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        username VARCHAR(64) NOT NULL,
                        nickname VARCHAR(128) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        email_verified BOOLEAN DEFAULT FALSE,
                        phone VARCHAR(32),
                        phone_verified BOOLEAN DEFAULT FALSE,
                        avatar_url VARCHAR(512),
                        user_type VARCHAR(32) DEFAULT 'customer', -- customer/admin
                        registration_time TIMESTAMPTZ DEFAULT NOW(),
                        last_login_time TIMESTAMPTZ,
                        status VARCHAR(32) DEFAULT 'active', -- active/inactive/locked
                        create_by VARCHAR(64) DEFAULT 'system',
                        create_time TIMESTAMPTZ DEFAULT NOW(),
                        update_by VARCHAR(64),
                        update_time TIMESTAMPTZ DEFAULT NOW(),
                        enable_flag BOOLEAN DEFAULT TRUE
                    );
                """)

                # 创建交易所信息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS exchange_info (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        exchange_code VARCHAR(32) NOT NULL, -- binance/okx/huobi
                        exchange_name VARCHAR(128) NOT NULL,
                        exchange_type VARCHAR(32) DEFAULT 'spot', -- spot/futures/margin
                        base_url VARCHAR(512) NOT NULL,
                        api_doc_url VARCHAR(512),
                        status VARCHAR(32) DEFAULT 'active', -- active/inactive
                        supported_pairs JSONB,
                        rate_limits JSONB,
                        create_by VARCHAR(64) DEFAULT 'system',
                        create_time TIMESTAMPTZ DEFAULT NOW(),
                        update_by VARCHAR(64),
                        update_time TIMESTAMPTZ DEFAULT NOW(),
                        enable_flag BOOLEAN DEFAULT TRUE
                    );
                """)

                # 创建用户交易所API表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_exchange_api (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_info(id),
                        exchange_id UUID NOT NULL REFERENCES exchange_info(id),
                        label VARCHAR(128) NOT NULL,
                        api_key VARCHAR(512) NOT NULL,
                        secret_key VARCHAR(512) NOT NULL,
                        passphrase VARCHAR(512), -- 部分交易所需要
                        permissions JSONB, -- 权限配置
                        status VARCHAR(32) DEFAULT 'pending', -- pending/approved/rejected/disabled
                        review_reason TEXT, -- 审核原因
                        approved_by VARCHAR(64),
                        approved_time TIMESTAMPTZ,
                        last_used_time TIMESTAMPTZ,
                        create_by VARCHAR(64),
                        create_time TIMESTAMPTZ DEFAULT NOW(),
                        update_by VARCHAR(64),
                        update_time TIMESTAMPTZ DEFAULT NOW(),
                        enable_flag BOOLEAN DEFAULT TRUE
                    );
                """)

                # 创建索引
                cursor.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_user_info_username_unique
                    ON user_info (username);
                """)

                cursor.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_user_info_email_unique
                    ON user_info (email);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_exchange_api_user_id
                    ON user_exchange_api (user_id);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_exchange_api_exchange_id
                    ON user_exchange_api (exchange_id);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_exchange_api_status
                    ON user_exchange_api (status);
                """)

                conn.commit()
                logger.info("Database tables initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize database tables", error=str(e))
            raise

    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                return True
        except Exception:
            return False

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connection_pool is not None


# 全局数据库实例
db_instance: Optional[TimescaleDB] = None


def get_database() -> TimescaleDB:
    """获取数据库实例（单例模式）"""
    global db_instance
    if db_instance is None:
        db_instance = TimescaleDB()
    return db_instance


async def init_database() -> TimescaleDB:
    """初始化数据库连接"""
    db = get_database()
    await db.connect()
    await db.initialize_tables()
    return db


async def close_database() -> None:
    """关闭数据库连接"""
    global db_instance
    if db_instance:
        await db_instance.disconnect()
        db_instance = None
