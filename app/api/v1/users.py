import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.db_models import User, RequestLog

router = APIRouter()


class UserRegister(BaseModel):
    username: str


class UserLogin(BaseModel):
    api_key: str


def _generate_api_key() -> str:
    """Generate a secure random API key."""
    return f"nxk_{secrets.token_urlsafe(32)}"


@router.post("/register")
async def register_user(
    body: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user. Returns a unique API key."""
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    api_key = _generate_api_key()
    user = User(
        username=body.username,
        api_key=api_key,
        role="user",
    )
    db.add(user)
    await db.flush()

    return {
        "id": user.id,
        "username": user.username,
        "api_key": api_key,
        "role": user.role,
        "message": "Save your API key — it won't be shown again.",
    }


@router.post("/login")
async def login_user(
    body: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Validate an API key and return user info."""
    result = await db.execute(
        select(User).where(User.api_key == body.api_key, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.get("/me")
async def get_current_user(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    """Get current user info + usage stats."""
    result = await db.execute(
        select(User).where(User.api_key == x_api_key, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Get usage stats
    stats_result = await db.execute(
        select(
            func.count(RequestLog.id).label("total_requests"),
            func.coalesce(func.sum(RequestLog.tokens_in), 0).label("total_tokens_in"),
            func.coalesce(func.sum(RequestLog.tokens_out), 0).label("total_tokens_out"),
            func.coalesce(func.sum(RequestLog.cost_usd), 0.0).label("total_cost"),
        ).where(RequestLog.user_id == user.id)
    )
    stats = stats_result.one()

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "created_at": str(user.created_at),
        "usage": {
            "total_requests": stats.total_requests,
            "total_tokens_in": int(stats.total_tokens_in),
            "total_tokens_out": int(stats.total_tokens_out),
            "total_cost_usd": round(float(stats.total_cost), 6),
        },
    }
