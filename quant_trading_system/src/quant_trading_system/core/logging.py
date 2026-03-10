"""
日志模块
========

基于 structlog 的结构化日志系统，支持：
- JSON 格式日志
- 多输出目标
- 日志级别过滤
- 上下文绑定
- 按级别分文件写入（info / warning / error）
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path

import structlog
from structlog.types import Processor


class LevelRangeFilter(logging.Filter):
    """日志级别范围过滤器，只允许指定范围内的日志通过"""

    def __init__(self, min_level: int, max_level: int = logging.CRITICAL) -> None:
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return self.min_level <= record.levelno <= self.max_level


def _create_file_handler(
    log_dir: Path,
    stem: str,
    suffix: str,
    timestamp: str,
    formatter: logging.Formatter,
    level_filter: LevelRangeFilter,
) -> logging.handlers.RotatingFileHandler:
    """创建带级别过滤的文件日志处理器"""
    file_path = log_dir / f"{stem}_{timestamp}{suffix}"
    handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=500 * 1024,  # 500KB
        backupCount=100,  # 最多保留100个备份文件
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    handler.addFilter(level_filter)
    return handler


def setup_logging(
    level: str | None = None,
    log_format: str | None = None,
    log_file: Path | None = None,
) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别（默认从配置 settings.LOG_LEVEL 读取，未设置则为 INFO）
        log_format: 日志格式 (json/console)（默认从配置 settings.monitor.log_format 读取）
        log_file: 日志文件路径（默认从配置 settings.LOG_FILE 读取）

    日志文件按级别分别写入：
        - {stem}_info_{timestamp}.log    : DEBUG + INFO 级别
        - {stem}_warning_{timestamp}.log : WARNING 级别
        - {stem}_error_{timestamp}.log   : ERROR + CRITICAL 级别
    """

    # 从配置读取（函数参数优先）
    try:
        from quant_trading_system.core.config import settings as _settings
        if level is None:
            level = _settings.LOG_LEVEL
        if log_format is None:
            log_format = _settings.monitor.log_format
        if log_file is None:
            log_file_str = _settings.LOG_FILE
            if log_file_str:
                log_file = Path(log_file_str)
    except Exception:
        # 配置未初始化时回退到环境变量
        if level is None:
            level = os.environ.get("LOG_LEVEL", "INFO")
        if log_format is None:
            log_format = "json"
        if log_file is None:
            env_log_file = os.environ.get("LOG_FILE")
            if env_log_file:
                log_file = Path(env_log_file)

    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 共享处理器
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),       # 渲染 stack_info=True 的调用栈
        structlog.processors.format_exc_info,           # 渲染 exc_info 异常堆栈（logger.exception / exc_info=True）
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
    ]

    # 根据格式选择渲染器
    if log_format == "json":
        renderer: Processor = structlog.processors.JSONRenderer(ensure_ascii=False)
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.RichTracebackFormatter(),
        )

    # 配置 structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 配置标准库日志
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # 控制台处理器（输出所有级别）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [console_handler]

    # 按级别分文件写入日志
    if log_file:
        log_dir = log_file.parent
        log_dir.mkdir(parents=True, exist_ok=True)

        stem = log_file.stem
        suffix = log_file.suffix or ".log"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # INFO 文件：记录 DEBUG ~ INFO 级别
        info_handler = _create_file_handler(
            log_dir, f"{stem}_info", suffix, timestamp, formatter,
            LevelRangeFilter(min_level=logging.DEBUG, max_level=logging.INFO),
        )
        handlers.append(info_handler)

        # WARNING 文件：仅记录 WARNING 级别
        warning_handler = _create_file_handler(
            log_dir, f"{stem}_warning", suffix, timestamp, formatter,
            LevelRangeFilter(min_level=logging.WARNING, max_level=logging.WARNING),
        )
        handlers.append(warning_handler)

        # ERROR 文件：记录 ERROR ~ CRITICAL 级别
        error_handler = _create_file_handler(
            log_dir, f"{stem}_error", suffix, timestamp, formatter,
            LevelRangeFilter(min_level=logging.ERROR, max_level=logging.CRITICAL),
        )
        handlers.append(error_handler)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除已有处理器
    root_logger.handlers.clear()

    for handler in handlers:
        root_logger.addHandler(handler)

    # 降低第三方库日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("kafka").setLevel(logging.WARNING)

    # SQLAlchemy 引擎日志默认抑制，需要调试 SQL 时可手动设为 logging.DEBUG
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """获取日志器"""
    return structlog.get_logger(name)

