"""
数据库连接管理模块
==================

提供统一的异步数据库连接管理，基于 SQLAlchemy AsyncEngine + asyncpg 驱动。

核心组件：
- **AsyncTimescaleDB**: 异步数据库连接管理器（连接池、原始SQL查询、建表初始化、健康检查）
- **get_db()**: FastAPI 异步依赖注入，返回 AsyncSession
- **get_async_database()**: 获取 AsyncTimescaleDB 单例（供 MarketDataWriter/MarketDataReader 使用）

生命周期统一由 lifespan 管理：
    init_database()   → 初始化异步引擎 + 建表
    close_database()  → 关闭异步引擎
"""

import structlog
from typing import Optional, AsyncGenerator
from pathlib import Path
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════
# 异步数据库连接管理器
# ═══════════════════════════════════════════════════════════════════


class AsyncTimescaleDB:
    """
    异步 TimescaleDB 数据库连接管理器

    基于 SQLAlchemy AsyncEngine + asyncpg 驱动，提供：
    - 异步连接池管理
    - 异步 SQL 查询 / 批量写入
    - AsyncSession 工厂（供 ORM 操作使用）
    - 建表初始化（执行 schema.sql）
    - 健康检查
    """

    def __init__(self, min_size: int = 5, max_size: int = 20):
        self.min_size = min_size
        self.max_size = max_size
        self._engine: Optional[AsyncEngine] = None
        self._async_session_factory = None

    async def connect(self) -> None:
        """建立异步数据库连接池"""
        if self._engine is not None and not self._engine.pool.status() == "closed":
            logger.debug("异步引擎已连接，跳过重复连接")
            return

        try:
            from quant_trading_system.core.config import settings
            database_url = settings.database.timescale_url
            self._engine = create_async_engine(
                database_url,
                pool_size=self.min_size,
                max_overflow=self.max_size - self.min_size,
                echo=False,
            )
            self._async_session_factory = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # 测试连接
            async with self._engine.begin() as conn:
                result = await conn.execute(sa_text("SELECT version();"))
                version = result.scalar()

            logger.info("异步 TimescaleDB 连接成功", version=version)

        except Exception as e:
            logger.error("异步 TimescaleDB 连接失败", exc_info=True)
            raise

    async def disconnect(self) -> None:
        """关闭异步连接池"""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._async_session_factory = None
            logger.info("异步 TimescaleDB 已断开")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取异步数据库会话（异步生成器）

        供 FastAPI Depends(get_db) 和非路由代码使用。
        """
        if self._async_session_factory is None:
            raise RuntimeError("数据库未连接，请先调用 connect()")
        async with self._async_session_factory() as session:
            yield session

    async def execute_query(self, query: str, params: dict = None) -> list:
        """执行异步查询，返回字典列表"""
        try:
            async with self._engine.begin() as conn:
                stmt = sa_text(query)
                result = await conn.execute(stmt, params or {})
                rows = []
                for row in result:
                    row_dict = {}
                    for i, column in enumerate(result.keys()):
                        row_dict[column] = row[i]
                    rows.append(row_dict)
                return rows
        except Exception as e:
            logger.error("异步查询失败", query=query, exc_info=True)
            raise

    async def execute_many(self, query: str, values: list) -> int:
        """执行批量异步插入/更新"""
        try:
            async with self._engine.begin() as conn:
                stmt = sa_text(query)
                result = await conn.execute(stmt, values)
                return result.rowcount
        except Exception as e:
            logger.error("异步批量操作失败", query=query, exc_info=True)
            raise

    async def initialize_tables(self) -> None:
        """
        初始化数据库表结构

        执行 schema.sql 建表，完全基于 asyncpg。
        注意：asyncpg 不支持在一条 prepared statement 中执行多条 SQL，
        因此需要将 schema.sql 拆分为单条语句逐一执行。
        """
        schema_path = Path(__file__).resolve().parents[3] / "database" / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"schema.sql 文件未找到: {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # 过滤掉 psql 元命令（\d、\c 等），asyncpg 不支持
        sql_lines = [
            line for line in schema_sql.splitlines()
            if not line.strip().startswith("\\")
        ]
        schema_sql = "\n".join(sql_lines)

        try:
            async with self._engine.connect() as conn:
                raw_conn = await conn.get_raw_connection()
                await raw_conn.driver_connection.execute(schema_sql)
            logger.info("数据库表初始化成功", schema=str(schema_path))
        except Exception as e:
            logger.error("数据库表初始化失败", exc_info=True)
            raise

    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            async with self._engine.begin() as conn:
                await conn.execute(sa_text("SELECT 1;"))
                return True
        except Exception:
            return False

    async def execute_raw(self, query: str, params: tuple = None) -> list:
        """
        执行原始 SQL 查询（兼容 %s 占位符格式）

        将 %s 占位符转换为 :p0, :p1, ... 的命名参数格式。
        """
        try:
            converted_query = query
            named_params = {}
            if params:
                for i, val in enumerate(params):
                    converted_query = converted_query.replace("%s", f":p{i}", 1)
                    named_params[f"p{i}"] = val

            async with self._engine.begin() as conn:
                result = await conn.execute(sa_text(converted_query), named_params)
                try:
                    rows = result.fetchall()
                    return rows
                except Exception:
                    # INSERT/UPDATE 等无返回结果的语句
                    return []
        except Exception as e:
            logger.error("原始SQL查询失败", query=query, exc_info=True)
            raise

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._engine is not None


# ═══════════════════════════════════════════════════════════════════
# 全局实例 & 生命周期管理
# ═══════════════════════════════════════════════════════════════════

# 异步数据库全局单例
_async_db_instance: Optional[AsyncTimescaleDB] = None


def get_async_database() -> AsyncTimescaleDB:
    """获取异步数据库实例（单例模式）"""
    global _async_db_instance
    if _async_db_instance is None:
        _async_db_instance = AsyncTimescaleDB()
    return _async_db_instance


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话的依赖函数

    供 FastAPI 路由层通过 Depends(get_db) 注入 AsyncSession，
    也供非路由代码直接调用。

    用法（路由层）：
        @router.get("/xxx")
        async def handler(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Model))
            ...

    用法（非路由代码）：
        async for db in get_db():
            result = await db.execute(select(Model))
            ...
    """
    db_instance = get_async_database()
    async for session in db_instance.get_session():
        yield session


async def init_database() -> AsyncTimescaleDB:
    """
    初始化数据库（由 lifespan 启动时调用）

    1. 初始化异步 AsyncTimescaleDB 引擎
    2. 执行 schema.sql 建表（如配置启用）
    """
    from quant_trading_system.core.config import settings

    db = get_async_database()
    await db.connect()

    if settings.database.init_table:
        await db.initialize_tables()

    return db


async def close_database() -> None:
    """
    关闭数据库（由 lifespan 关闭时调用）
    """
    global _async_db_instance

    if _async_db_instance is not None:
        await _async_db_instance.disconnect()
        _async_db_instance = None
