from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.dependencies import verify_admin
from app.config import settings, reload_config, COST_PER_1M
from app.database import get_db
from app.db_models import RequestLog, User

router = APIRouter()


@router.get("/stats", dependencies=[Depends(verify_admin)])
async def get_gateway_stats(request: Request, db: AsyncSession = Depends(get_db)):
    """Get runtime statistics for all providers (in-memory + DB aggregate)."""
    # In-memory real-time stats
    realtime = request.app.state.state_store.get_all_states()
    
    # DB aggregate stats
    db_stats = await db.execute(
        select(
            RequestLog.provider,
            func.count(RequestLog.id).label("total_requests"),
            func.coalesce(func.sum(RequestLog.tokens_in), 0).label("total_tokens_in"),
            func.coalesce(func.sum(RequestLog.tokens_out), 0).label("total_tokens_out"),
            func.coalesce(func.sum(RequestLog.cost_usd), 0.0).label("total_cost"),
            func.coalesce(func.avg(RequestLog.latency_ms), 0.0).label("avg_latency"),
        ).group_by(RequestLog.provider)
    )
    
    db_providers = {}
    for row in db_stats.all():
        db_providers[row.provider] = {
            "total_requests": row.total_requests,
            "total_tokens_in": int(row.total_tokens_in),
            "total_tokens_out": int(row.total_tokens_out),
            "total_cost_usd": round(float(row.total_cost), 6),
            "avg_latency_ms": round(float(row.avg_latency), 2),
        }
    
    # Total users count
    user_count = await db.execute(select(func.count(User.id)))
    total_users = user_count.scalar() or 0
    
    # Total requests and tokens all-time
    total_result = await db.execute(
        select(
            func.count(RequestLog.id).label("count"),
            func.coalesce(func.sum(RequestLog.tokens_in), 0).label("tokens_in"),
            func.coalesce(func.sum(RequestLog.tokens_out), 0).label("tokens_out"),
        )
    )
    total_data = total_result.first()
    total_requests = total_data.count if total_data else 0
    total_tokens_alltime = (int(total_data.tokens_in) + int(total_data.tokens_out)) if total_data else 0
    
    # Per-model breakdown
    model_stats = await db.execute(
        select(
            RequestLog.model,
            RequestLog.provider,
            func.count(RequestLog.id).label("requests"),
            func.coalesce(func.sum(RequestLog.tokens_in), 0).label("tokens_in"),
            func.coalesce(func.sum(RequestLog.tokens_out), 0).label("tokens_out"),
            func.coalesce(func.sum(RequestLog.cost_usd), 0.0).label("cost"),
            func.coalesce(func.avg(RequestLog.latency_ms), 0.0).label("avg_latency"),
        ).group_by(RequestLog.model, RequestLog.provider)
        .order_by(desc(func.count(RequestLog.id)))
    )
    model_breakdown = []
    for row in model_stats.all():
        model_breakdown.append({
            "model": row.model,
            "provider": row.provider,
            "requests": row.requests,
            "tokens_in": int(row.tokens_in),
            "tokens_out": int(row.tokens_out),
            "cost_usd": round(float(row.cost), 6),
            "avg_latency_ms": round(float(row.avg_latency), 2),
        })

    # Failover trace stats (how often each provider was a fallback)
    failover_stats = await db.execute(
        select(
            RequestLog.provider,
            RequestLog.status,
            func.count(RequestLog.id).label("count"),
        ).group_by(RequestLog.provider, RequestLog.status)
    )
    failover_breakdown = {}
    for row in failover_stats.all():
        if row.provider not in failover_breakdown:
            failover_breakdown[row.provider] = {"success": 0, "error": 0}
        if row.status == "success":
            failover_breakdown[row.provider]["success"] = row.count
        else:
            failover_breakdown[row.provider]["error"] += row.count

    realtime["db_stats"] = db_providers
    realtime["model_breakdown"] = model_breakdown
    realtime["failover_breakdown"] = failover_breakdown
    realtime["total_users"] = total_users
    realtime["total_requests_alltime"] = total_requests
    realtime["total_tokens_alltime"] = total_tokens_alltime
    realtime["budget_limit_usd"] = settings.budget_daily_limit_usd
    realtime["cost_rates"] = {k: {"input": v[0], "output": v[1]} for k, v in COST_PER_1M.items()}
    return realtime


@router.get("/logs", dependencies=[Depends(verify_admin)])
async def get_request_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Paginated request logs from database."""
    query = select(RequestLog).order_by(desc(RequestLog.created_at))
    
    if provider:
        query = query.where(RequestLog.provider == provider)
    
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Total count
    count_query = select(func.count(RequestLog.id))
    if provider:
        count_query = count_query.where(RequestLog.provider == provider)
    total = (await db.execute(count_query)).scalar() or 0
    
    return {
        "logs": [
            {
                "id": log.id,
                "provider": log.provider,
                "model": log.model,
                "tokens_in": log.tokens_in,
                "tokens_out": log.tokens_out,
                "latency_ms": round(log.latency_ms, 2),
                "cost_usd": round(log.cost_usd, 6),
                "task_type": log.task_type,
                "status": log.status,
                "error_msg": log.error_msg,
                "created_at": str(log.created_at),
                "user_id": log.user_id,
            }
            for log in logs
        ],
        "page": page,
        "per_page": per_page,
        "total": total,
    }


@router.get("/users", dependencies=[Depends(verify_admin)])
async def list_users(
    db: AsyncSession = Depends(get_db),
):
    """List all registered users with usage stats and billing data."""
    result = await db.execute(
        select(
            User.id,
            User.username,
            User.role,
            User.is_active,
            User.created_at,
            func.count(RequestLog.id).label("request_count"),
            func.coalesce(func.sum(RequestLog.tokens_in), 0).label("tokens_in"),
            func.coalesce(func.sum(RequestLog.tokens_out), 0).label("tokens_out"),
            func.coalesce(func.sum(RequestLog.cost_usd), 0.0).label("total_cost"),
            func.max(RequestLog.created_at).label("last_active"),
        )
        .outerjoin(RequestLog, RequestLog.user_id == User.id)
        .group_by(User.id, User.username, User.role, User.is_active, User.created_at)
        .order_by(desc(User.created_at))
    )
    
    users = []
    for row in result.all():
        users.append({
            "id": row.id,
            "username": row.username,
            "role": row.role,
            "is_active": row.is_active,
            "created_at": str(row.created_at),
            "last_active": str(row.last_active) if row.last_active else None,
            "request_count": row.request_count,
            "tokens_in": int(row.tokens_in),
            "tokens_out": int(row.tokens_out),
            "total_cost_usd": round(float(row.total_cost), 6),
        })
    
    return {"users": users}


@router.get("/providers", dependencies=[Depends(verify_admin)])
async def get_gateway_providers():
    """Get configured provider status and info."""
    providers_list = []
    
    all_provider_keys = set(settings.provider_chain)
    for p_list in settings.task_tiers.values():
        all_provider_keys.update(p_list)
        
    for p_key in all_provider_keys:
        tasks = [tier for tier, t_list in settings.task_tiers.items() if p_key in t_list]
        providers_list.append({
            "name": p_key.capitalize(),
            "key": p_key,
            "active": True,
            "in_chain": p_key in settings.provider_chain,
            "tasks": tasks
        })
        
    return {
        "providers": providers_list,
        "chain_order": settings.provider_chain
    }


@router.post("/reload", dependencies=[Depends(verify_admin)])
async def reload_providers_config():
    """Trigger a hot-reload of providers.json configuration."""
    await reload_config()
    return {
        "status": "success",
        "message": "Configuration reloaded from providers.json",
        "active_chain": settings.provider_chain,
        "task_tiers": list(settings.task_tiers.keys()),
    }


@router.get("/config", dependencies=[Depends(verify_admin)])
async def get_current_config():
    """View current active configuration (sensitive)."""
    return {
        "routing_mode": settings.routing_mode,
        "provider_chain": settings.provider_chain,
        "task_tiers": settings.task_tiers,
        "cooldown_period": settings.provider_cooldown_s,
        "budget_limit": settings.budget_daily_limit_usd,
        "weights": settings.dynamic_weights,
    }
