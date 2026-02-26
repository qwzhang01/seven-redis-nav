"""
Web 中间件模块
=============

提供以下全局拦截器：
- RequestIDMiddleware  : 为每个请求注入唯一 Trace ID
- LoggingMiddleware   : 记录请求/响应日志（耗时、状态码等）
- RateLimitMiddleware : 基于 IP 的滑动窗口限流
- AuthMiddleware      : 统一 JWT Token 校验（白名单路径跳过）
"""

import time
import uuid
import logging
import jwt
from collections import defaultdict, deque
from typing import Deque

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from quant_trading_system.core.config import settings
from quant_trading_system.core.jwt_utils import JWTUtils

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 认证中间件白名单（这些路径不需要 Token）
# ──────────────────────────────────────────────
_prefix = settings.API_PREFIX

AUTH_WHITELIST: set[str] = {
    "/",
    "/docs",
    "/redoc",
    f"{_prefix}/openapi.json",
    f"{_prefix}/info",
    # C 端公开接口（无需登录）
    f"{_prefix}/c/user/register",
    f"{_prefix}/c/user/login",
    f"{_prefix}/c/user/password/reset",
    f"{_prefix}/c/user/token/refresh",
    # Admin 端健康探针（供运维/K8s 使用，无需登录）
    f"{_prefix}/m/health/",
    f"{_prefix}/m/health/ready",
    f"{_prefix}/m/health/live",
    # WebSocket 接口（WebSocket 握手不携带 Authorization 头，由各路由自行验证）
    f"{_prefix}/ws/market",
    f"{_prefix}/ws/trading",
    f"{_prefix}/ws/strategy",
}

LOG_IGNORE: set[str] = {
    "/",
    "/docs",
    "/redoc",
    f"{_prefix}/openapi.json",
    f"{_prefix}/info",
    # Admin 端健康探针（供运维/K8s 使用，无需登录）
    f"{_prefix}/m/health/",
    f"{_prefix}/m/health/ready",
    f"{_prefix}/m/health/live",
}

# ──────────────────────────────────────────────
# 1. 请求 ID 中间件
# ──────────────────────────────────────────────
class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    为每个请求生成唯一的 X-Request-ID，并写入响应头。
    后续中间件和业务代码可通过 request.state.request_id 获取。
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        # 优先使用客户端传入的 ID，否则自动生成
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response


# ──────────────────────────────────────────────
# 2. 请求日志中间件
# ──────────────────────────────────────────────
class LoggingMiddleware(BaseHTTPMiddleware):
    """
    记录每个请求的方法、路径、状态码、耗时和 Trace ID。
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 白名单直接放行
        if path in LOG_IGNORE:
            return await call_next(request)

        from fastapi import HTTPException
        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", "-")

        logger.info(
            "→ 请求开始  [%s] %s %s  client=%s",
            request_id,
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                "✗ 请求异常  [%s] %s %s  耗时=%.2fms  error=%s",
                request_id,
                request.method,
                request.url.path,
                elapsed,
                exc,
            )
            raise

        elapsed = (time.perf_counter() - start) * 1000
        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            level,
            "← 请求完成  [%s] %s %s  status=%d  耗时=%.2fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response


# ──────────────────────────────────────────────
# 3. 限流中间件（滑动窗口，基于客户端 IP）
# ──────────────────────────────────────────────
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    基于 IP 的滑动窗口限流。
    默认：每个 IP 在 60 秒内最多 200 次请求。
    超限时返回 429 Too Many Requests。
    """

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = 200,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # ip -> deque of timestamps
        self._records: dict[str, Deque[float]] = defaultdict(deque)

    def _get_client_ip(self, request: Request) -> str:
        """优先读取反向代理头，否则取直连 IP"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - self.window_seconds

        dq = self._records[ip]
        # 清除窗口外的旧记录
        while dq and dq[0] < window_start:
            dq.popleft()

        if len(dq) >= self.max_requests:
            request_id = getattr(request.state, "request_id", "-")
            logger.warning(
                "⚠ 限流触发  [%s] ip=%s  count=%d/%d",
                request_id, ip, len(dq), self.max_requests,
            )
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁：每 {self.window_seconds} 秒最多允许 {self.max_requests} 次请求，请稍后再试"
            )

        dq.append(now)
        return await call_next(request)


# ──────────────────────────────────────────────
# 4. 认证中间件（统一 JWT 校验）
# ──────────────────────────────────────────────
class AuthMiddleware(BaseHTTPMiddleware):
    """
    统一 JWT Token 校验中间件。
    - 白名单路径直接放行
    - 其余路径要求 Authorization: Bearer <token>
    - 校验通过后将 username 写入 request.state.username
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 白名单直接放行
        if path in AUTH_WHITELIST:
            return await call_next(request)

        # OPTIONS 预检请求直接放行（CORS）
        if request.method == "OPTIONS":
            return await call_next(request)

        # 提取 Token
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="未提供认证凭据"
            )

        token = authorization[len("Bearer "):]

        jwt_utils = JWTUtils()
        try:
            payload = jwt_utils.verify_token(token)
            username: str = payload.get("sub")
            if not username:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=401,
                    detail="Token无效：缺少用户标识"
                )
            request.state.username = username
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail=f"Token验证失败：{str(e)}"
            )

        return await call_next(request)
