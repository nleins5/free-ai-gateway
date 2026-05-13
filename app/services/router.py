import os
import time
import random
import logging
import httpx
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException
from openai import AsyncOpenAI

from app.config import (
    settings, REQUEST_TIMEOUT_S, MAX_RETRIES_PER_PROVIDER, 
    ROUTING_MODE
)
from app.core.providers import PROVIDER_REGISTRY, Provider
from app.core.state import StateStore

logger = logging.getLogger(__name__)

class RouterService:
    def __init__(self, state_store: StateStore):
        self._clients: Dict[str, AsyncOpenAI] = {}
        self.state_store = state_store

    def get_client(self, provider: Provider) -> AsyncOpenAI:
        if provider.key not in self._clients:
            api_key = self._get_api_key(provider)
            base_url = self._get_base_url(provider)
            self._clients[provider.key] = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=REQUEST_TIMEOUT_S
            )
        return self._clients[provider.key]

    def _get_api_key(self, provider: Provider) -> str:
        if provider.key == "ollama":
            return os.getenv(provider.api_key_env, "ollama")
        if provider.key == "github":
            return os.getenv(provider.api_key_env) or os.getenv("GITHUB_PAT") or "not_provided"
        return os.getenv(provider.api_key_env) or "not_provided"

    def _get_base_url(self, provider: Provider) -> str:
        if provider.key == "cloudflare":
            return os.getenv("CLOUDFLARE_BASE_URL", provider.base_url)
        if provider.key == "ollama":
            return os.getenv("OLLAMA_BASE_URL", provider.base_url)
        return provider.base_url

    def _get_provider_model(self, provider: Provider, model_override: Optional[str] = None) -> str:
        model = model_override or os.getenv(provider.model_env, provider.default_model)
        # Normalize for GitHub
        if provider.key == "github" and "/" not in model:
            github_aliases = {
                "gpt-4o": "gpt-4o",
                "gpt-4o-mini": "gpt-4o-mini",
                "deepseek-r1": "DeepSeek-R1",
            }
            model = github_aliases.get(model, model)
        return model

    def _is_retryable(self, exc: Exception) -> bool:
        # Standard OpenAI retry logic
        from openai import APIConnectionError, APITimeoutError, APIStatusError
        if isinstance(exc, (APIConnectionError, APITimeoutError)):
            return True
        if isinstance(exc, APIStatusError) and exc.status_code in [429, 500, 502, 503, 504]:
            return True
        return False

    def _get_ordered_providers(self, active_keys: List[str]) -> List[Provider]:
        available = []
        for key in active_keys:
            p = PROVIDER_REGISTRY.get(key)
            if p and not self.state_store.is_on_cooldown(key):
                available.append(p)
        
        if not available:
            return []

        if ROUTING_MODE == "weighted":
            # Weighted random shuffle — distributes traffic proportionally
            # instead of always picking the highest-weight provider.
            # E.g. Groq(3) vs NVIDIA(2) → Groq gets ~60%, NVIDIA ~40% as primary.
            scored = []
            for p in available:
                base_w = settings.dynamic_weights.get(p.key, 100)
                eff_w = self.state_store.get_effective_weight(p.key, base_w)
                scored.append((eff_w, p))
            
            # Weighted shuffle: pick providers one by one based on their weight
            shuffled = []
            remaining = list(scored)
            while remaining:
                total = sum(w for w, _ in remaining)
                if total <= 0:
                    # Fallback: append rest in original order
                    shuffled.extend([p for _, p in remaining])
                    break
                r = random.random() * total
                cumulative = 0.0
                for i, (w, p) in enumerate(remaining):
                    cumulative += w
                    if cumulative >= r:
                        shuffled.append(p)
                        remaining.pop(i)
                        break
            
            logger.info(f"Weighted shuffle order: {[p.key for p in shuffled]}")
            return shuffled
        elif ROUTING_MODE == "round_robin":
            idx = self.state_store.increment_rr() % len(available)
            return available[idx:] + available[:idx]
        else:
            # Default sequence
            return available

    async def chat_with_failover(
        self,
        messages: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        model_override: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = None,
        task: Optional[str] = "general",
    ) -> Tuple[Any, Dict[str, Any]]:
        
        if task == "omniverse":
            sys_msg = {
                "role": "system",
                "content": "You are an expert NVIDIA Omniverse and OpenUSD developer. Your task is to generate OpenUSD Python code, answer Omniverse knowledge questions, and assist with 3D scene creation using Omniverse Kit. Always provide clean, functional Python code when requested."
            }
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] += "\n" + sys_msg["content"]
            else:
                messages.insert(0, sys_msg)

        if self.state_store.get_total_cost() >= settings.budget_daily_limit_usd > 0:
            raise HTTPException(
                status_code=429,
                detail=f"Daily budget limit of ${settings.budget_daily_limit_usd:.2f} exceeded."
            )

        # Track user prompt count and enforce free tier limit
        if user_id:
            prompt_count = self.state_store.get_user_prompts(user_id)
            if prompt_count >= 10:
                raise HTTPException(
                    status_code=402,
                    detail="Bạn đã sử dụng hết 10 lượt miễn phí. Vui lòng đăng nhập để tiếp tục."
                )
            self.state_store.increment_user_prompt(user_id)
            logger.info(f"User {user_id[:8]}... prompt #{prompt_count + 1}/10, task={task}")

        # Resolve task tier → provider chain
        # Keep user's chosen task mode (chat/code/research/general) intact
        resolved_task = task or "general"
        chain = settings.task_tiers.get(resolved_task, None)
        if chain is None:
            # Unknown task tier → fallback to "general" tier, then full chain
            chain = settings.task_tiers.get("general", settings.provider_chain)
            logger.warning(f"Unknown task tier '{resolved_task}', falling back to general")
        
        providers = self._get_ordered_providers(chain)
        
        if not providers:
            # Fallback to entire registry if everything is on cooldown or invalid
            logger.warning("All providers in chain on cooldown, falling back to full registry")
            providers = [p for p in PROVIDER_REGISTRY.values() if not self.state_store.is_on_cooldown(p.key)]
            if not providers:
                raise HTTPException(status_code=502, detail="All providers are currently on cooldown or inactive.")

        errors = []
        for provider in providers:
            client = self.get_client(provider)
            model = self._get_provider_model(provider, model_override)
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens

            last_error = None
            for attempt in range(MAX_RETRIES_PER_PROVIDER + 1):
                self.state_store.mark_attempt(provider.key)
                start_time = time.perf_counter()
                try:
                    response = await client.chat.completions.create(**payload)  # type: ignore
                    latency = (time.perf_counter() - start_time) * 1000.0
                    self.state_store.record_latency(provider.key, latency)
                    self.state_store.mark_success(provider.key)
                    
                    # Usage tracking
                    usage = getattr(response, "usage", None)
                    t_in = getattr(usage, "prompt_tokens", 0) if usage else 0
                    t_out = getattr(usage, "completion_tokens", 0) if usage else 0
                    self.state_store.record_usage(provider.key, t_in, t_out)
                    
                    meta = {
                        "provider": provider.key,
                        "provider_name": provider.name,
                        "model": model,
                        "latency_ms": round(latency, 2),
                        "failover_trace": errors
                    }
                    return response, meta
                except Exception as exc:
                    latency = (time.perf_counter() - start_time) * 1000.0
                    self.state_store.record_latency(provider.key, latency)
                    last_error = exc
                    logger.warning(f"Provider {provider.key} attempt {attempt+1} failed: {exc}")
                    if not self._is_retryable(exc):
                        break
            
            if last_error:
                self.state_store.mark_failure(provider.key, str(last_error))
                errors.append({"provider": provider.key, "error": str(last_error)})

        # Build a human-readable error summary
        error_summary = "; ".join([f"{e['provider']}: {str(e['error'])[:80]}" for e in errors[:5]])
        logger.error(f"All {len(errors)} providers failed for task={resolved_task}. Errors: {error_summary}")
        raise HTTPException(
            status_code=502,
            detail=f"All upstream providers failed. Tried {len(errors)} providers. Last errors: {error_summary}",
        )
# router_service removed, initialized in app.main
