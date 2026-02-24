"""
日志模块
========

基于 structlog 的结构化日志系统，支持：
- JSON 格式日志
- 多输出目标
- 日志级别过滤
- 上下文绑定
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import Processor


def setup_logging(
    level: str | None = None,
    log_format: str = "json",
    log_file: Path | None = None,
) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别（默认从环境变量 LOG_LEVEL 读取，未设置则为 INFO）
        log_format: 日志格式 (json/console)
        log_file: 日志文件路径（默认从环境变量 LOG_FILE 读取，未设置则不写文件）
    """

    # 从环境变量读取配置（函数参数优先）
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO")
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
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
    ]

    # 根据格式选择渲染器
    if log_format == "json":
        renderer: Processor = structlog.processors.JSONRenderer()
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

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    handlers = [console_handler]

    # 文件处理器
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

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


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """获取日志器"""
    return structlog.get_logger(name)


class LogContext:
    """日志上下文管理器"""

    @staticmethod
    def bind(**kwargs: Any) -> None:
        """绑定上下文变量"""
        structlog.contextvars.bind_contextvars(**kwargs)

    @staticmethod
    def unbind(*keys: str) -> None:
        """解绑上下文变量"""
        structlog.contextvars.unbind_contextvars(*keys)

    @staticmethod
    def clear() -> None:
        """清除所有上下文变量"""
        structlog.contextvars.clear_contextvars()
