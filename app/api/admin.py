from fastapi import APIRouter, Depends, Request
from app.dependencies import verify_admin
from app.config import settings, reload_config

router = APIRouter()

@router.get("/stats", dependencies=[Depends(verify_admin)])
async def get_gateway_stats(request: Request):
    """Get runtime statistics for all providers."""
    return request.app.state.state_store.get_all_states()

@router.get("/providers", dependencies=[Depends(verify_admin)])
async def get_gateway_providers():
    """Get configured provider status and info."""
    providers_list = []
    
    # Identify unique providers from task tiers and provider chain
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
