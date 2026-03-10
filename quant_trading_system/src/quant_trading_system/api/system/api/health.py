#!/usr/bin/env python3
"""
健康检查路由模块
提供系统健康状态检查接口，用于监控和运维
"""

from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from quant_trading_system.core.database import get_async_database
from quant_trading_system.core.config import settings


class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: HealthStatus
    message: str
    timestamp: datetime
    version: str = ""  # 从配置中读取
    checks: Optional[Dict[str, Dict[str, Any]]] = None

# 创建路由
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    基础健康检查
    检查API服务是否正常运行
    """
    return HealthResponse(
        status=HealthStatus.HEALTHY,
        message="服务运行正常",
        timestamp=datetime.now(),
        version=settings.app_version,
        checks={
            "api": {"status": "healthy", "message": "API服务正常"}
        }
    )


@router.get("/db", response_model=HealthResponse)
async def database_health_check() -> HealthResponse:
    """
    数据库健康检查
    检查数据库连接是否正常
    """
    try:
        # 使用异步数据库实例进行健康检查
        db = get_async_database()
        db_status = await db.health_check()

        if db_status:
            return HealthResponse(
                status=HealthStatus.HEALTHY,
                message="数据库连接正常",
                timestamp=datetime.now(),
                checks={
                    "database": {"status": "healthy", "message": "数据库连接正常"}
                }
            )
        else:
            return HealthResponse(
                status=HealthStatus.UNHEALTHY,
                message="数据库连接异常",
                timestamp=datetime.now(),
                checks={
                    "database": {"status": "unhealthy", "message": "数据库查询失败"}
                }
            )

    except Exception as e:
        return HealthResponse(
            status=HealthStatus.UNHEALTHY,
            message=f"数据库连接失败: {str(e)}",
            timestamp=datetime.now(),
            checks={
                "database": {"status": "unhealthy", "message": f"数据库连接异常: {str(e)}"}
            }
        )


@router.get("/full", response_model=HealthResponse)
async def full_health_check() -> HealthResponse:
    """
    完整健康检查
    检查所有关键组件的健康状态
    """
    checks: Dict[str, Dict[str, Any]] = {}
    overall_status = HealthStatus.HEALTHY

    # 检查API服务
    checks["api"] = {"status": "healthy", "message": "API服务正常"}

    # 检查数据库
    db = get_async_database()
    try:
        db_status = await db.health_check()
        checks["database"] = {
            "status": "healthy" if db_status else "unhealthy",
            "message": "数据库连接正常" if db_status else "数据库查询失败"
        }
        if not db_status:
            overall_status = HealthStatus.UNHEALTHY
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "message": f"数据库连接异常: {str(e)}"
        }
        overall_status = HealthStatus.UNHEALTHY

    # 检查关键表是否存在（通过异步查询）
    table_checks = [
        ("user_table", "user_info", "用户表"),
        ("exchange_table", "exchange_info", "交易所表"),
        ("api_key_table", "user_exchange_api", "API密钥表"),
    ]
    for check_key, table_name, label in table_checks:
        try:
            rows = await db.execute_raw(f"SELECT COUNT(*) FROM {table_name} LIMIT 1")
            checks[check_key] = {
                "status": "healthy",
                "message": f"{label}正常"
            }
        except Exception as e:
            checks[check_key] = {
                "status": "unhealthy",
                "message": f"{label}检查失败: {str(e)}"
            }
            overall_status = HealthStatus.UNHEALTHY

    # 系统信息
    import psutil
    import os

    # 内存使用情况
    memory = psutil.virtual_memory()
    checks["memory"] = {
        "status": "healthy" if memory.percent < 90 else "warning",
        "message": f"内存使用率: {memory.percent:.1f}%",
        "details": {
            "total": f"{memory.total // (1024**3)}GB",
            "used": f"{memory.used // (1024**3)}GB",
            "percent": memory.percent
        }
    }

    # CPU使用率
    cpu_percent = psutil.cpu_percent(interval=0.1)
    checks["cpu"] = {
        "status": "healthy" if cpu_percent < 80 else "warning",
        "message": f"CPU使用率: {cpu_percent:.1f}%",
        "details": {
            "cores": psutil.cpu_count(),
            "percent": cpu_percent
        }
    }

    # 磁盘使用情况
    disk = psutil.disk_usage('/')
    checks["disk"] = {
        "status": "healthy" if disk.percent < 90 else "warning",
        "message": f"磁盘使用率: {disk.percent:.1f}%",
        "details": {
            "total": f"{disk.total // (1024**3)}GB",
            "used": f"{disk.used // (1024**3)}GB",
            "percent": disk.percent
        }
    }

    # 进程信息
    process = psutil.Process(os.getpid())
    checks["process"] = {
        "status": "healthy",
        "message": "进程运行正常",
        "details": {
            "pid": process.pid,
            "memory_mb": process.memory_info().rss // (1024**2),
            "cpu_percent": process.cpu_percent()
        }
    }

    message = "系统运行正常" if overall_status == HealthStatus.HEALTHY else "系统存在异常"

    return HealthResponse(
        status=overall_status,
        message=message,
        timestamp=datetime.now(),
        version=settings.app_version,
        checks=checks
    )


@router.get("/ready")
async def readiness_probe() -> JSONResponse:
    """
    就绪检查
    用于Kubernetes就绪探针
    """
    try:
        # 简单的就绪检查，可以添加更多逻辑
        return JSONResponse(
            content={
                "status": "ready",
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )
    except Exception:
        return JSONResponse(
            content={
                "status": "not ready",
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )


@router.get("/live")
async def liveness_probe() -> JSONResponse:
    """
    存活检查
    用于Kubernetes存活探针
    """
    try:
        # 简单的存活检查
        return JSONResponse(
            content={
                "status": "alive",
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )
    except Exception:
        return JSONResponse(
            content={
                "status": "dead",
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )


@router.get("/metrics")
async def metrics_endpoint() -> Dict[str, Any]:
    """
    系统指标接口
    返回系统运行指标，可用于监控系统
    """
    import psutil
    import platform

    # 系统信息
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "uptime": psutil.boot_time()
    }

    # CPU信息
    cpu_info = {
        "cores": psutil.cpu_count(),
        "usage_percent": psutil.cpu_percent(interval=0.1),
        "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
    }

    # 内存信息
    memory = psutil.virtual_memory()
    memory_info = {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "percent": memory.percent
    }

    # 磁盘信息
    disk = psutil.disk_usage('/')
    disk_info = {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent
    }

    # 网络信息
    net_io = psutil.net_io_counters()
    network_info = {
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv
    }

    return {
        "timestamp": datetime.now().isoformat(),
        "system": system_info,
        "cpu": cpu_info,
        "memory": memory_info,
        "disk": disk_info,
        "network": network_info
    }
