"""
通用工具模块
============

包含通用的时间处理和重试工具函数
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class TimeUtils:
    """时间工具类"""

    @staticmethod
    def parse_time_string(time_str: str) -> int:
        """
        解析时间字符串为毫秒时间戳

        Args:
            time_str: 时间字符串，格式支持：
                     - "YYYY-MM-DD"（仅日期）
                     - "YYYY-MM-DD HH:MM:SS"（完整时间）
                     - ISO 8601格式（如："YYYY-MM-DDTHH:MM:SSZ"、"YYYY-MM-DDTHH:MM:SS+HH:MM"、"YYYY-MM-DDTHH:MM:SS-05:00"）

        Returns:
            毫秒时间戳
        """
        try:
            # 统一使用 datetime.fromisoformat() 解析 ISO 8601 格式
            # 将 'Z' 后缀替换为 '+00:00' 以兼容 fromisoformat
            if "T" in time_str:
                normalized = time_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(normalized)
                # 如果带时区信息，转为 UTC 后去掉时区再取 timestamp
                if dt.tzinfo is not None:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                return int(dt.timestamp() * 1000)

            # 尝试解析完整时间
            if " " in time_str:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(time_str, "%Y-%m-%d")

            return int(dt.timestamp() * 1000)
        except Exception as e:
            logger.error("Failed to parse time", time_str=time_str, error=str(e))
            raise ValueError(f"Invalid time format: {time_str}")

    @staticmethod
    def timestamp_to_datetime(timestamp_ms: int) -> datetime:
        """
        将毫秒时间戳转换为datetime对象

        Args:
            timestamp_ms: 毫秒时间戳

        Returns:
            datetime对象
        """
        return datetime.fromtimestamp(timestamp_ms / 1000)


class RetryUtils:
    """重试工具类"""

    @staticmethod
    def execute_with_retry(
        func: callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        retry_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """
        带重试机制执行函数

        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            retry_exceptions: 需要重试的异常类型
            **kwargs: 函数参数

        Returns:
            函数执行结果
        """
        retry_count = 0

        while retry_count <= max_retries:
            try:
                return func(**kwargs)
            except retry_exceptions as e:
                retry_count += 1

                if retry_count > max_retries:
                    logger.error(
                        "Failed after all retries",
                        error=str(e),
                        error_type=type(e).__name__,
                        retries=max_retries,
                    )
                    raise

                # 根据异常类型调整延迟时间
                delay = RetryUtils._calculate_delay(retry_count, base_delay, e)

                logger.warning(
                    "Operation failed, retrying",
                    error=str(e),
                    error_type=type(e).__name__,
                    retry_count=retry_count,
                    max_retries=max_retries,
                    delay=delay,
                )

                time.sleep(delay)

        raise RuntimeError("Unexpected error in retry logic")

    @staticmethod
    def _calculate_delay(retry_count: int, base_delay: float, exception: Exception) -> float:
        """
        根据异常类型和重试次数计算延迟时间

        Args:
            retry_count: 当前重试次数
            base_delay: 基础延迟
            exception: 发生的异常

        Returns:
            计算后的延迟时间
        """
        # 指数退避基础延迟
        delay = base_delay * (2 ** (retry_count - 1))

        # 根据异常类型调整延迟
        exception_name = type(exception).__name__

        # 连接相关错误使用较短延迟
        if "Connect" in exception_name:
            delay = min(delay, 5.0)  # 连接错误最大延迟5秒
        # 超时相关错误使用中等延迟
        elif "Timeout" in exception_name:
            delay = min(delay, 10.0)  # 超时错误最大延迟10秒
        # 网络相关错误使用较长延迟
        elif any(keyword in exception_name for keyword in ["Network", "Read", "Write", "Proxy"]):
            delay = min(delay, 15.0)  # 网络错误最大延迟15秒
        # 其他错误使用标准延迟
        else:
            delay = min(delay, 30.0)  # 其他错误最大延迟30秒

        # 添加随机抖动避免同步重试
        jitter = delay * 0.1  # 10%的随机抖动
        delay += jitter * (2 * time.time() % 1 - 0.5)

        return max(0.5, delay)  # 最小延迟0.5秒

    @staticmethod
    def execute_with_progressive_retry(
        func: callable,
        max_retries: int = 5,
        base_delay: float = 1.0,
        **kwargs
    ) -> Any:
        """
        使用渐进式重试策略执行函数

        针对网络请求的智能重试策略，根据异常类型和重试次数动态调整

        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            **kwargs: 函数参数

        Returns:
            函数执行结果
        """
        # 定义网络相关的重试异常
        network_exceptions = [
            ConnectionError,
            TimeoutError,
            OSError,
            IOError,
        ]

        # 如果httpx可用，添加httpx相关的异常
        try:
            import httpx
            network_exceptions.extend([
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.ReadError,
                httpx.WriteError,
                httpx.ProxyError,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
                httpx.ProtocolError,
            ])
        except ImportError:
            logger.debug("httpx not available, using standard exceptions only")

        return RetryUtils.execute_with_retry(
            func=func,
            max_retries=max_retries,
            base_delay=base_delay,
            retry_exceptions=tuple(network_exceptions),
            **kwargs
        )

    # ── 异步重试 ──────────────────────────────────────────────

    @staticmethod
    async def async_execute_with_retry(
        func: callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        retry_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """
        带重试机制异步执行函数

        Args:
            func: 要执行的异步函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            retry_exceptions: 需要重试的异常类型
            **kwargs: 函数参数

        Returns:
            函数执行结果
        """
        retry_count = 0

        while retry_count <= max_retries:
            try:
                return await func(**kwargs)
            except retry_exceptions as e:
                retry_count += 1

                if retry_count > max_retries:
                    logger.error(
                        "Async failed after all retries",
                        error=str(e),
                        error_type=type(e).__name__,
                        retries=max_retries,
                    )
                    raise

                delay = RetryUtils._calculate_delay(retry_count, base_delay, e)

                logger.warning(
                    "Async operation failed, retrying",
                    error=str(e),
                    error_type=type(e).__name__,
                    retry_count=retry_count,
                    max_retries=max_retries,
                    delay=delay,
                )

                await asyncio.sleep(delay)

        raise RuntimeError("Unexpected error in async retry logic")

    @staticmethod
    async def async_execute_with_progressive_retry(
        func: callable,
        max_retries: int = 5,
        base_delay: float = 1.0,
        **kwargs
    ) -> Any:
        """
        使用渐进式重试策略异步执行函数

        针对网络请求的智能重试策略，根据异常类型和重试次数动态调整。

        Args:
            func: 要执行的异步函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            **kwargs: 函数参数

        Returns:
            函数执行结果
        """
        network_exceptions: list[type] = [
            ConnectionError,
            TimeoutError,
            OSError,
            IOError,
        ]

        try:
            import httpx
            network_exceptions.extend([
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.ReadError,
                httpx.WriteError,
                httpx.ProxyError,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
                httpx.ProtocolError,
            ])
        except ImportError:
            logger.debug("httpx not available, using standard exceptions only")

        try:
            import aiohttp
            network_exceptions.extend([
                aiohttp.ClientError,
                aiohttp.ServerDisconnectedError,
            ])
        except ImportError:
            logger.debug("aiohttp not available, using standard exceptions only")

        return await RetryUtils.async_execute_with_retry(
            func=func,
            max_retries=max_retries,
            base_delay=base_delay,
            retry_exceptions=tuple(network_exceptions),
            **kwargs
        )
