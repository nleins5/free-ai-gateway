import os
import time
import random
import logging
from typing import Any, Dict, List, Optional, Tuple, AsyncGenerator
from fastapi import HTTPException
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, APIStatusError

from app.config import (
    settings, REQUEST_TIMEOUT_S, MAX_RETRIES_PER_PROVIDER,
    ROUTING_MODE, PROVIDER_FAILURE_THRESHOLD
)
from app.core.providers import PROVIDER_REGISTRY, Provider
from app.core.state import StateStore

logger = logging.getLogger(__name__)


class ProviderHealth:
    """Track health metrics for each provider."""
    def __init__(self):
        self.success_count: int = 0
        self.failure_count: int = 0
        self.total_latency_ms: float = 0.0
        self.request_count: int = 0
        self.last_error: Optional[str] = None
        self.last_success_time: float = 0.0
        self.consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        if self.request_count == 0:
            return 1.0
        return self.success_count / self.request_count

    @property
    def avg_latency_ms(self) -> float:
        if self.success_count == 0:
            return 0.0
        return self.total_latency_ms / self.success_count

    def record_success(self, latency_ms: float):
        self.success_count += 1
        self.request_count += 1
        self.total_latency_ms += latency_ms
        self.consecutive_failures = 0
        self.last_success_time = time.time()
        self.last_error = None

    def record_failure(self, error: str):
        self.failure_count += 1
        self.request_count += 1
        self.consecutive_failures += 1
        self.last_error = error

    def is_healthy(self) -> bool:
        """Check if provider is healthy enough to receive traffic."""
        if self.consecutive_failures >= PROVIDER_FAILURE_THRESHOLD:
            return False
        if self.request_count >= 10 and self.success_rate < 0.3:
            return False
        return True


class RouterService:
    def __init__(self, state_store: StateStore):
        self._clients: Dict[str, AsyncOpenAI] = {}
        self._health: Dict[str, ProviderHealth] = {}
        self.state_store = state_store

    def get_health(self, provider_key: str) -> ProviderHealth:
        if provider_key not in self._health:
            self._health[provider_key] = ProviderHealth()
        return self._health[provider_key]

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
        if provider.key == "freetheai":
            # FreeTheAI doesn't require API key
            return os.getenv(provider.api_key_env) or "free"
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
        if isinstance(exc, (APIConnectionError, APITimeoutError)):
            return True
        if isinstance(exc, APIStatusError):
            # Auth, billing, and permission errors → fail fast, never retry
            if exc.status_code in [401, 402, 403, 404]:
                return False
            # Rate limit and server errors → retryable
            if exc.status_code in [429, 500, 502, 503, 504]:
                return True
            if exc.status_code >= 500:
                return True
        return False

    def _classify_error(self, exc: Exception) -> str:
        """Classify error for better logging and cooldown decisions."""
        if isinstance(exc, APITimeoutError):
            return "timeout"
        if isinstance(exc, APIConnectionError):
            return "connection"
        if isinstance(exc, APIStatusError):
            if exc.status_code in [401, 403]:
                return "auth"
            if exc.status_code == 402:
                return "billing"
            if exc.status_code == 404:
                return "model_not_found"
            if exc.status_code == 429:
                return "rate_limit"
            if exc.status_code >= 500:
                return "server_error"
        return "unknown"

    def _has_api_key(self, provider: Provider) -> bool:
        """Check if a provider has a valid API key configured."""
        if provider.key in ("ollama", "freetheai"):
            return True  # These don't require real keys
        key = os.getenv(provider.api_key_env)
        if not key or key == "not_provided":
            return False
        # Detect obvious placeholder keys
        placeholder_prefixes = ("PASTE_", "REPLACE_", "YOUR_", "invalid_", "changeme")
        if key.startswith(placeholder_prefixes):
            return False
        return True

    def _calculate_provider_score(self, provider: Provider) -> float:
        """Calculate health-adjusted score for provider selection."""
        health = self.get_health(provider.key)
        base_weight = settings.dynamic_weights.get(provider.key, 100)

        # Health multiplier (0.1 to 1.0)
        health_mult = health.success_rate if health.request_count >= 5 else 1.0

        # Latency penalty (faster = higher score)
        avg_latency = health.avg_latency_ms
        latency_penalty = 1.0 / (1.0 + avg_latency / 1000.0) if avg_latency > 0 else 1.0

        # Consecutive failure penalty
        failure_penalty = max(0.1, 1.0 - (health.consecutive_failures * 0.2))

        return base_weight * health_mult * latency_penalty * failure_penalty

    def _get_ordered_providers(self, active_keys: List[str], task: str = "general") -> List[Provider]:
        available = []
        skipped_no_key = []
        skipped_unhealthy = []
        for key in active_keys:
            p = PROVIDER_REGISTRY.get(key)
            if not p:
                continue
            # Skip providers without valid API keys entirely
            if not self._has_api_key(p):
                skipped_no_key.append(key)
                continue
            if self.get_health(key).is_healthy() and not self.state_store.is_on_cooldown(key):
                available.append(p)
            else:
                skipped_unhealthy.append(key)

        if skipped_no_key:
            logger.debug(f"Skipped (no API key): {skipped_no_key}")

        if not available:
            logger.warning(f"No healthy providers available (unhealthy: {skipped_unhealthy}), relaxing constraints")
            # Relax constraints: try all providers with valid keys, even if unhealthy
            for key in active_keys:
                p = PROVIDER_REGISTRY.get(key)
                if p and self._has_api_key(p):
                    available.append(p)

            if not available:
                return []

        if ROUTING_MODE == "weighted":
            # Score-based selection with some randomness for load distribution
            scored = [(self._calculate_provider_score(p), p) for p in available]
            scored.sort(key=lambda x: x[0], reverse=True)

            # Top 3 candidates, then random shuffle among them for load balancing
            top_n = min(3, len(scored))
            top_providers = [(s, p) for s, p in scored[:top_n]]
            rest_providers = scored[top_n:]

            random.shuffle(top_providers)
            ordered = [p for _, p in top_providers] + [p for _, p in rest_providers]

            logger.info(f"Provider order (task={task}): {[p.key for p in ordered]}")
            return ordered

        elif ROUTING_MODE == "round_robin":
            idx = self.state_store.increment_rr() % len(available)
            return available[idx:] + available[:idx]

        elif ROUTING_MODE == "health_first":
            # Sort by health score, highest first
            scored = [(self._calculate_provider_score(p), p) for p in available]
            scored.sort(key=lambda x: x[0], reverse=True)
            return [p for _, p in scored]

        else:
            # Default: respect provider_chain order
            chain = settings.task_tiers.get(task, settings.provider_chain)
            ordered = []
            for key in chain:
                for p in available:
                    if p.key == key:
                        ordered.append(p)
                        break
            return ordered

    async def chat_with_failover(
        self,
        messages: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        model_override: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = None,
        task: Optional[str] = "general",
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Main chat method with intelligent failover across multiple providers.

        Features:
        - Health-aware provider selection
        - Automatic failover on failure
        - Usage tracking per user
        - Budget enforcement
        - Task-based provider routing
        """
        # Special system prompts for specific tasks
        if task == "omniverse":
            sys_msg = {
                "role": "system",
                "content": "You are an expert NVIDIA Omniverse and OpenUSD developer. Your task is to generate OpenUSD Python code, answer Omniverse knowledge questions, and assist with 3D scene creation using Omniverse Kit. Always provide clean, functional Python code when requested."
            }
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] += "\n" + sys_msg["content"]
            else:
                messages.insert(0, sys_msg)

        # Budget check
        if self.state_store.get_total_cost() >= settings.budget_daily_limit_usd > 0:
            raise HTTPException(
                status_code=429,
                detail=f"Daily budget limit of ${settings.budget_daily_limit_usd:.2f} exceeded."
            )

        # User prompt tracking (free tier: 10 prompts/day)
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
        resolved_task = task or "general"
        chain = settings.task_tiers.get(resolved_task, settings.provider_chain)

        providers = self._get_ordered_providers(chain, resolved_task)

        if not providers:
            logger.warning("All providers on cooldown or unhealthy, falling back to full registry")
            providers = [p for p in PROVIDER_REGISTRY.values()
                        if self.get_health(p.key).is_healthy()]
            if not providers:
                raise HTTPException(
                    status_code=503,
                    detail="All providers are currently unavailable. Please try again later."
                )

        errors = []
        start_time = time.time()

        for idx, provider in enumerate(providers):
            health = self.get_health(provider.key)
            client = self.get_client(provider)
            model = self._get_provider_model(provider, model_override)

            # Log provider attempt
            attempt_info = f"Attempt {idx+1}/{len(providers)}: {provider.key} ({model})"
            logger.info(attempt_info)

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
                request_start = time.perf_counter()

                try:
                    response = await client.chat.completions.create(**payload)
                    latency = (time.perf_counter() - request_start) * 1000.0
                    total_latency = (time.time() - start_time) * 1000.0

                    # Record success
                    health.record_success(latency)
                    self.state_store.record_latency(provider.key, latency)
                    self.state_store.mark_success(provider.key)

                    # Usage tracking
                    usage = getattr(response, "usage", None)
                    t_in = getattr(usage, "prompt_tokens", 0) if usage else 0
                    t_out = getattr(usage, "completion_tokens", 0) if usage else 0
                    self.state_store.record_usage(provider.key, t_in, t_out)

                    # Build metadata
                    meta = {
                        "provider": provider.key,
                        "provider_name": provider.name,
                        "model": model,
                        "latency_ms": round(latency, 2),
                        "total_latency_ms": round(total_latency, 2),
                        "failover_trace": errors,
                        "attempt_number": idx + 1,
                        "total_providers_tried": len(providers),
                    }

                    logger.info(f"Success: {provider.key} in {latency:.0f}ms (total: {total_latency:.0f}ms)")
                    return response, meta

                except Exception as exc:
                    latency = (time.perf_counter() - request_start) * 1000.0
                    error_type = self._classify_error(exc)
                    health.record_failure(str(exc))
                    self.state_store.mark_failure(provider.key, str(exc)[:200])
                    last_error = exc

                    logger.warning(
                        f"Provider {provider.key} attempt {attempt+1} failed [{error_type}]: "
                        f"{type(exc).__name__}: {str(exc)[:100]}"
                    )

                    # Auth/billing errors → immediate cooldown, skip retries
                    if error_type in ("auth", "billing", "model_not_found"):
                        logger.info(f"Provider {provider.key} has {error_type} error, skipping retries")
                        break

                    if not self._is_retryable(exc):
                        break

            # Provider failed after all retries
            if last_error:
                error_type = self._classify_error(last_error)
                error_info = {
                    "provider": provider.key,
                    "error": str(last_error)[:200],
                    "status_code": getattr(last_error, "status_code", None),
                    "error_type": error_type,
                }
                errors.append(error_info)

                # Auth/billing errors → longer cooldown to avoid hammering
                if error_type in ("auth", "billing", "model_not_found"):
                    self.state_store.mark_cooldown(provider.key, cooldown_s=300.0)
                    logger.warning(f"Provider {provider.key} [{error_type}]: cooldown 5min")
                elif health.consecutive_failures >= PROVIDER_FAILURE_THRESHOLD:
                    self.state_store.mark_cooldown(provider.key)
                    logger.warning(f"Provider {provider.key} marked for cooldown")

        # All providers failed
        error_summary = "; ".join([f"{e['provider']}: {e['error'][:80]}" for e in errors[:5]])
        total_time = (time.time() - start_time) * 1000.0
        logger.error(
            f"All {len(errors)} providers failed in {total_time:.0f}ms. "
            f"Errors: {error_summary}"
        )

        raise HTTPException(
            status_code=503,
            detail=f"All AI providers are currently unavailable. "
                   f"Please try again in a moment. (Tried: {len(errors)} providers)",
        )

    async def chat_stream_with_failover(
        self,
        messages: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        model_override: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = None,
        task: Optional[str] = "general",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming version of chat_with_failover.

        Yields SSE-formatted events for real-time response streaming.
        Includes failover notification when switching providers.
        """
        # Special system prompts for specific tasks
        if task == "omniverse":
            sys_msg = {
                "role": "system",
                "content": "You are an expert NVIDIA Omniverse and OpenUSD developer. Your task is to generate OpenUSD Python code, answer Omniverse knowledge questions, and assist with 3D scene creation using Omniverse Kit. Always provide clean, functional Python code when requested."
            }
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] += "\n" + sys_msg["content"]
            else:
                messages.insert(0, sys_msg)

        # Budget check
        if self.state_store.get_total_cost() >= settings.budget_daily_limit_usd > 0:
            yield {
                "error": "BudgetExceeded",
                "message": f"Daily budget limit of ${settings.budget_daily_limit_usd:.2f} exceeded."
            }
            return

        # User prompt tracking
        if user_id:
            prompt_count = self.state_store.get_user_prompts(user_id)
            if prompt_count >= 10:
                yield {
                    "error": "FreeLimitReached",
                    "message": "Bạn đã sử dụng hết 10 lượt miễn phí. Vui lòng đăng nhập để tiếp tục."
                }
                return
            self.state_store.increment_user_prompt(user_id)

        # Resolve task tier → provider chain
        resolved_task = task or "general"
        chain = settings.task_tiers.get(resolved_task, settings.provider_chain)

        providers = self._get_ordered_providers(chain, resolved_task)

        if not providers:
            providers = [p for p in PROVIDER_REGISTRY.values()
                        if self.get_health(p.key).is_healthy()]
            if not providers:
                yield {
                    "error": "ServiceUnavailable",
                    "message": "All providers are currently unavailable."
                }
                return

        errors = []

        for idx, provider in enumerate(providers):
            health = self.get_health(provider.key)
            client = self.get_client(provider)
            model = self._get_provider_model(provider, model_override)

            # Notify about provider selection (for streaming UI display)
            if idx > 0:
                yield {
                    "info": "Failover",
                    "message": f"Switching to {provider.name} due to previous provider errors...",
                    "provider": provider.key,
                }

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens

            last_error = None
            for attempt in range(MAX_RETRIES_PER_PROVIDER + 1):
                self.state_store.mark_attempt(provider.key)

                try:
                    stream = await client.chat.completions.create(**payload)
                    health.record_success(0)  # Mark as responsive
                    self.state_store.mark_success(provider.key)

                    # Stream the response
                    async for chunk in stream:
                        usage = getattr(chunk, "usage", None)
                        if usage:
                            t_in = getattr(usage, "prompt_tokens", 0)
                            t_out = getattr(usage, "completion_tokens", 0)
                            self.state_store.record_usage(provider.key, t_in, t_out)

                        yield {
                            "choices": chunk.choices,
                            "provider": provider.key,
                            "model": model,
                        }

                    # Success - break out of retry loop
                    return

                except Exception as exc:
                    last_error = exc
                    error_type = self._classify_error(exc)
                    logger.warning(
                        f"Provider {provider.key} stream attempt {attempt+1} failed [{error_type}]: "
                        f"{type(exc).__name__}: {str(exc)[:100]}"
                    )

                    if error_type in ("auth", "billing", "model_not_found"):
                        break
                    if not self._is_retryable(exc):
                        break

            if last_error:
                error_type = self._classify_error(last_error)
                health.record_failure(str(last_error))
                self.state_store.mark_failure(provider.key, str(last_error)[:200])
                errors.append({"provider": provider.key, "error": str(last_error)[:200], "error_type": error_type})

                if error_type in ("auth", "billing", "model_not_found"):
                    self.state_store.mark_cooldown(provider.key, cooldown_s=300.0)
                elif health.consecutive_failures >= PROVIDER_FAILURE_THRESHOLD:
                    self.state_store.mark_cooldown(provider.key)

        # All providers failed
        yield {
            "error": "ServiceUnavailable",
            "message": f"All providers failed. Last error: {errors[-1]['error'] if errors else 'Unknown error'}",
        }

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current status of all providers for admin dashboard."""
        status = {}
        for key, provider in PROVIDER_REGISTRY.items():
            health = self.get_health(key)
            status[key] = {
                "key": key,
                "name": provider.name,
                "healthy": health.is_healthy(),
                "success_rate": round(health.success_rate, 3),
                "avg_latency_ms": round(health.avg_latency_ms, 2),
                "consecutive_failures": health.consecutive_failures,
                "total_requests": health.request_count,
                "last_error": health.last_error[:100] if health.last_error else None,
                "on_cooldown": self.state_store.is_on_cooldown(key),
            }
        return status

    def reset_provider_health(self, provider_key: str):
        """Manually reset health tracking for a provider."""
        if provider_key in self._health:
            self._health[provider_key] = ProviderHealth()
            logger.info(f"Reset health for provider: {provider_key}")