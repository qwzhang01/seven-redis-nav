"""
TimescaleDB 数据库连接和表结构定义

提供实时行情数据存储和回测数据查询功能
"""

import asyncio
import structlog
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logger = structlog.get_logger(__name__)


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

                # 将kline_data表转换为时序表
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

                # 将tick_data表转换为时序表
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

                # 将depth_data表转换为时序表
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
