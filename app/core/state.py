import time
import datetime
from typing import Any, Dict, List, Tuple
from app.config import (
    PROVIDER_FAILURE_THRESHOLD, PROVIDER_COOLDOWN_S, ADAPTIVE_ROUTING,
    ADAPTIVE_LATENCY_ALPHA, ADAPTIVE_ERROR_PENALTY, COST_PER_1M
)

class StateStore:
    def __init__(self):
        self.provider_state: Dict[str, Dict[str, Any]] = {}
        self.daily_usage: Dict[str, Dict[str, Any]] = {}
        self.daily_usage_date: str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        self.rr_counter: int = 0
        self.user_usage: Dict[str, int] = {}

    def _ensure_daily_reset(self) -> None:
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        if today != self.daily_usage_date:
            self.daily_usage.clear()
            self.daily_usage_date = today

    def ensure_provider_state(self, provider_key: str) -> Dict[str, Any]:
        state = self.provider_state.get(provider_key)
        if state is None:
            state = {
                "failures": 0,
                "successes": 0,
                "attempts": 0,
                "consecutive_failures": 0,
                "failures_total": 0,
                "cooldown_until": 0.0,
                "last_error": "",
                "last_attempt_at": 0.0,
                "last_latency_ms": 0.0,
                "latency_ewma_ms": 0.0,
                "inflight": 0,
            }
            self.provider_state[provider_key] = state
        return state

    def is_on_cooldown(self, provider_key: str) -> bool:
        state = self.ensure_provider_state(provider_key)
        return state["cooldown_until"] > time.time()

    def mark_success(self, provider_key: str) -> None:
        state = self.ensure_provider_state(provider_key)
        state["failures"] = 0
        state["consecutive_failures"] = 0
        state["successes"] += 1
        state["cooldown_until"] = 0.0
        state["last_error"] = ""
        state["last_attempt_at"] = time.time()
        state["inflight"] = max(0, int(state["inflight"]) - 1)

    def mark_failure(self, provider_key: str, err: str) -> None:
        state = self.ensure_provider_state(provider_key)
        state["failures"] += 1
        state["consecutive_failures"] += 1
        state["failures_total"] += 1
        state["last_error"] = err
        state["last_attempt_at"] = time.time()
        state["inflight"] = max(0, int(state["inflight"]) - 1)
        if state["consecutive_failures"] >= PROVIDER_FAILURE_THRESHOLD:
            state["cooldown_until"] = time.time() + PROVIDER_COOLDOWN_S
            state["consecutive_failures"] = 0

    def mark_cooldown(self, provider_key: str, cooldown_s: float = None) -> None:
        """Manually put a provider on cooldown for a specified or default duration."""
        state = self.ensure_provider_state(provider_key)
        duration = cooldown_s if cooldown_s is not None else PROVIDER_COOLDOWN_S
        state["cooldown_until"] = time.time() + duration
        state["consecutive_failures"] = 0

    def mark_attempt(self, provider_key: str) -> None:
        state = self.ensure_provider_state(provider_key)
        state["attempts"] += 1
        state["inflight"] += 1
        state["last_attempt_at"] = time.time()

    def record_latency(self, provider_key: str, latency_ms: float) -> None:
        state = self.ensure_provider_state(provider_key)
        state["last_latency_ms"] = latency_ms
        if state["latency_ewma_ms"] <= 0:
            state["latency_ewma_ms"] = latency_ms
        else:
            state["latency_ewma_ms"] = (
                ADAPTIVE_LATENCY_ALPHA * latency_ms
                + (1.0 - ADAPTIVE_LATENCY_ALPHA) * float(state["latency_ewma_ms"])
            )

    def get_effective_weight(self, provider_key: str, base_weight: int) -> float:
        if not ADAPTIVE_ROUTING:
            return float(base_weight)
        state = self.ensure_provider_state(provider_key)
        attempts = max(int(state["attempts"]), 1)
        failures = int(state["failures_total"])
        error_rate = failures / attempts
        error_multiplier = max(0.1, 1.0 - (error_rate * (1.0 + ADAPTIVE_ERROR_PENALTY)))

        ewma_latency = float(state["latency_ewma_ms"])
        if ewma_latency <= 0:
            latency_multiplier = 1.0
        else:
            # Dampened latency bonus — use sqrt to flatten the curve.
            # Fast providers still get a boost but won't monopolize traffic.
            # Cap at 1.5x (was 2.0x) so a 200ms provider only gets 1.5x, not 4x.
            raw = 600.0 / ewma_latency
            latency_multiplier = max(0.4, min(1.5, raw ** 0.5))

        # Penalize providers with many inflight requests (load spreading)
        inflight = int(state.get("inflight", 0))
        inflight_penalty = max(0.5, 1.0 - (inflight * 0.15))

        return max(0.1, float(base_weight) * error_multiplier * latency_multiplier * inflight_penalty)

    def record_usage(self, provider_key: str, tokens_in: int = 0, tokens_out: int = 0) -> None:
        self._ensure_daily_reset()
        if provider_key not in self.daily_usage:
            self.daily_usage[provider_key] = {
                "requests": 0, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0
            }
        
        rates = COST_PER_1M.get(provider_key, (0.0, 0.0))
        cost_usd = (tokens_in * rates[0] + tokens_out * rates[1]) / 1_000_000
        
        u = self.daily_usage[provider_key]
        u["requests"] += 1
        u["tokens_in"] += tokens_in
        u["tokens_out"] += tokens_out
        u["cost_usd"] += cost_usd

    def get_total_cost(self) -> float:
        self._ensure_daily_reset()
        return sum(u.get("cost_usd", 0.0) for u in self.daily_usage.values())

    def increment_rr(self) -> int:
        res = self.rr_counter
        self.rr_counter += 1
        return res

    def get_user_prompts(self, user_id: str) -> int:
        if not user_id:
            return 0
        self._ensure_user_reset()
        return self.user_usage.get(user_id, 0)

    def increment_user_prompt(self, user_id: str) -> None:
        if not user_id:
            return
        self._ensure_user_reset()
        self.user_usage[user_id] = self.get_user_prompts(user_id) + 1

    def _ensure_user_reset(self) -> None:
        """Reset user prompt counters daily so free-tier limits reset at midnight UTC."""
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        if not hasattr(self, '_user_usage_date') or today != self._user_usage_date:
            self.user_usage.clear()
            self._user_usage_date = today

    # ── Telemetry methods used by admin API ──────────────────────

    def get_all_states(self) -> Dict[str, Any]:
        """Return a snapshot of all provider states + daily usage."""
        self._ensure_daily_reset()
        return {
            "providers": {
                k: {**v, "on_cooldown": self.is_on_cooldown(k)}
                for k, v in self.provider_state.items()
            },
            "daily_usage": dict(self.daily_usage),
            "daily_usage_date": self.daily_usage_date,
            "total_cost_usd": round(self.get_total_cost(), 6),
        }
