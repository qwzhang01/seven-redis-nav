"""
TimescaleDB 数据库连接和表结构定义

提供实时行情数据存储和回测数据查询功能
"""

import structlog
from typing import Optional, Any, Generator
from contextlib import contextmanager
import os
from urllib.parse import urlparse, quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 加载环境变量
load_dotenv()

logger = structlog.get_logger(__name__)


def _build_sync_database_url() -> str:
    """构建同步数据库URL，自动对密码中的特殊字符进行URL编码"""
    database_url = os.getenv("DATABASE_URL", "postgresql://quant:quant123@localhost:5432/quant_trading")
    parsed = urlparse(database_url)
    if parsed.password:
        encoded_password = quote_plus(parsed.password)
        # 重新构建编码后的URL
        netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        database_url = f"{parsed.scheme}://{netloc}{parsed.path}"
        if parsed.query:
            database_url += f"?{parsed.query}"
    return database_url


# 创建数据库引擎和会话工厂
engine = create_engine(_build_sync_database_url())
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
        """初始化数据库表结构，直接执行 schema.sql 文件"""
        from pathlib import Path
        # parents[4]: database.py -> services/database -> services -> quant_trading_system -> src -> 项目根
        schema_path = Path(__file__).resolve().parents[4] / "database" / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"schema.sql 文件未找到: {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # 过滤掉 psql 元命令（\d、\c 等），psycopg2 不支持
        sql_lines = [
            line for line in schema_sql.splitlines()
            if not line.strip().startswith("\\")
        ]
        schema_sql = "\n".join(sql_lines)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(schema_sql)
                conn.commit()
                logger.info("Database tables initialized successfully", schema=schema_path)

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
