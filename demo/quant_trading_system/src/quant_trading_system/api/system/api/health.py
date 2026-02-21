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

from quant_trading_system.services.database.database import get_database


class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: HealthStatus
    message: str
    timestamp: datetime
    version: str = "1.0.0"
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
        version="1.0.0",
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
        # 使用现有的数据库实例进行健康检查
        db = get_database()
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
    try:
        db = get_database()
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

    # 检查关键表是否存在
    try:
        # 检查用户表
        db = get_database()
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_info LIMIT 1")
            checks["user_table"] = {
                "status": "healthy",
                "message": "用户表正常"
            }
    except Exception as e:
        checks["user_table"] = {
            "status": "unhealthy",
            "message": f"用户表检查失败: {str(e)}"
        }
        overall_status = HealthStatus.UNHEALTHY

    # 检查交易所表
    try:
        db = get_database()
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM exchange_info LIMIT 1")
            checks["exchange_table"] = {
                "status": "healthy",
                "message": "交易所表正常"
            }
    except Exception as e:
        checks["exchange_table"] = {
            "status": "unhealthy",
            "message": f"交易所表检查失败: {str(e)}"
        }
        overall_status = HealthStatus.UNHEALTHY

    # 检查API密钥表
    try:
        db = get_database()
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_exchange_api LIMIT 1")
            checks["api_key_table"] = {
                "status": "healthy",
                "message": "API密钥表正常"
            }
    except Exception as e:
        checks["api_key_table"] = {
            "status": "unhealthy",
            "message": f"API密钥表检查失败: {str(e)}"
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
        version="1.0.0",
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
