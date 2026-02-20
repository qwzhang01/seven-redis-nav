"""
管理员用户管理 API
==================

提供管理员对系统用户的查询和管理功能：
- 获取用户列表（支持搜索、状态/类型筛选、分页）
- 获取用户详情
- 更新用户信息（昵称、邮箱、手机号、用户类型）
- 更新用户状态（锁定/解锁）
"""

from datetime import datetime, date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from quant_trading_system.models.database import User
from quant_trading_system.models.user import UserResponse, UserType, UserStatus
from quant_trading_system.services.database.database import get_db

router = APIRouter()


# ── 权限校验 ──────────────────────────────────────────────────────────────────

def _require_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    校验当前请求用户是否为管理员。
    AuthMiddleware 已将 username 写入 request.state.username。
    """
    username = getattr(request.state, "username", None)
    if not username:
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    user = db.query(User).filter(User.username == username, User.enable_flag == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.user_type != "admin":
        raise HTTPException(status_code=403, detail="权限不足，仅管理员可操作")
    return user


# ── 请求/响应模型 ─────────────────────────────────────────────────────────────

class AdminUserUpdate(BaseModel):
    """管理员更新用户信息请求体"""
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    user_type: Optional[UserType] = None


class UserStatusUpdate(BaseModel):
    """更新用户状态请求体"""
    status: UserStatus


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _user_to_response(user: User) -> dict[str, Any]:
    """将 User ORM 对象转换为响应字典"""
    return {
        "id": str(user.id),
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "user_type": user.user_type,
        "email_verified": user.email_verified,
        "phone_verified": user.phone_verified,
        "registration_time": user.registration_time,
        "last_login_time": user.last_login_time,
        "status": user.status,
        "create_time": user.create_time,
        "update_time": user.update_time,
    }


# ── 接口实现 ──────────────────────────────────────────────────────────────────

@router.get("")
async def list_users(
    search: Optional[str] = Query(None, description="按用户名、邮箱或昵称模糊搜索"),
    user_status: Optional[str] = Query(None, alias="status", description="状态筛选：active/inactive/locked"),
    user_type: Optional[str] = Query(None, description="类型筛选：customer/admin"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    获取用户列表

    支持按用户名/邮箱/昵称搜索，按状态和类型筛选，分页返回。
    同时返回顶部统计数据：总用户数、活跃用户数、今日新增、已锁定数。
    """
    query = db.query(User).filter(User.enable_flag == True)

    # 模糊搜索
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.username.ilike(like_pattern),
                User.email.ilike(like_pattern),
                User.nickname.ilike(like_pattern),
            )
        )

    # 状态筛选
    if user_status:
        query = query.filter(User.status == user_status)

    # 类型筛选
    if user_type:
        query = query.filter(User.user_type == user_type)

    total = query.count()
    users = (
        query.order_by(User.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # 统计数据（不受筛选条件影响，基于全量数据）
    base_query = db.query(User).filter(User.enable_flag == True)
    total_users = base_query.count()
    active_users = base_query.filter(User.status == "active").count()
    locked_users = base_query.filter(User.status == "locked").count()
    today = date.today()
    today_new = base_query.filter(
        func.date(User.registration_time) == today
    ).count()

    return {
        "success": True,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [_user_to_response(u) for u in users],
            "statistics": {
                "total_users": total_users,
                "active_users": active_users,
                "today_new": today_new,
                "locked_users": locked_users,
            },
        },
    }


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    获取用户详情

    根据用户 ID 返回用户的完整信息。
    """
    user = db.query(User).filter(User.id == user_id, User.enable_flag == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {"success": True, "data": _user_to_response(user)}


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    body: AdminUserUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    更新用户信息

    管理员可修改用户的昵称、邮箱、手机号和用户类型。
    """
    user = db.query(User).filter(User.id == user_id, User.enable_flag == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 邮箱唯一性校验
    if body.email is not None and body.email != user.email:
        conflict = db.query(User).filter(
            User.email == body.email,
            User.id != user_id,
            User.enable_flag == True,
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail="邮箱地址已被其他用户使用")
        user.email = body.email

    if body.nickname is not None:
        user.nickname = body.nickname
    if body.phone is not None:
        user.phone = body.phone
    if body.user_type is not None:
        user.user_type = body.user_type.value

    user.update_time = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {"success": True, "data": _user_to_response(user), "message": "用户信息更新成功"}


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: str,
    body: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    更新用户状态

    管理员可将用户状态设置为 active（解锁）、inactive 或 locked（锁定）。
    不允许管理员锁定自己。
    """
    user = db.query(User).filter(User.id == user_id, User.enable_flag == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 防止管理员锁定自己
    if str(user.id) == str(admin.id) and body.status == UserStatus.LOCKED:
        raise HTTPException(status_code=400, detail="不能锁定自己的账户")

    user.status = body.status.value
    user.update_time = datetime.utcnow()
    db.commit()
    db.refresh(user)

    action = "锁定" if body.status == UserStatus.LOCKED else "解锁" if body.status == UserStatus.ACTIVE else "更新"
    return {
        "success": True,
        "data": _user_to_response(user),
        "message": f"用户已{action}",
    }
