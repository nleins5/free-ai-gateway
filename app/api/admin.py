from fastapi import APIRouter, Depends
from app.dependencies import verify_admin
from app.core.state import state_store
from app.config import settings, reload_config

router = APIRouter()

@router.get("/stats", dependencies=[Depends(verify_admin)])
async def get_gateway_stats():
    """Get runtime statistics for all providers."""
    return state_store.get_all_states()

@router.post("/reload", dependencies=[Depends(verify_admin)])
async def reload_providers_config():
    """Trigger a hot-reload of providers.json configuration."""
    reload_config()
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
