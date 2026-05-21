import os
import json
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import aiofiles

load_dotenv()

# --- CONSTANTS ---
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "changeme")
GATEWAY_SECRET = os.getenv("GATEWAY_SECRET", "")  # Shared secret for Vercel↔Render auth
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
PROVIDERS_JSON_PATH = os.getenv("PROVIDERS_JSON_PATH", "providers.json")
REQUEST_TIMEOUT_S = float(os.getenv("REQUEST_TIMEOUT_S", "15"))
IMAGE_MAX_WAIT_MS = max(int(os.getenv("IMAGE_MAX_WAIT_MS", "9500")), 1000)
MAX_RETRIES_PER_PROVIDER = max(int(os.getenv("MAX_RETRIES_PER_PROVIDER", "1")), 0)
PROVIDER_FAILURE_THRESHOLD = max(int(os.getenv("PROVIDER_FAILURE_THRESHOLD", "2")), 1)
PROVIDER_COOLDOWN_S = max(float(os.getenv("PROVIDER_COOLDOWN_S", "60")), 0.0)
ADAPTIVE_ROUTING = os.getenv("ADAPTIVE_ROUTING", "1").strip().lower() in {"1", "true", "yes", "on"}
ADAPTIVE_LATENCY_ALPHA = min(max(float(os.getenv("ADAPTIVE_LATENCY_ALPHA", "0.3")), 0.05), 0.95)
ADAPTIVE_ERROR_PENALTY = min(max(float(os.getenv("ADAPTIVE_ERROR_PENALTY", "0.5")), 0.05), 0.95)
RAG_STORE_PATH = os.getenv("RAG_STORE_PATH", ".rag_store.json")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/nexus_gateway")
RAG_TOP_K = max(int(os.getenv("RAG_TOP_K", "4")), 1)
RAG_MAX_CHUNK_CHARS = max(int(os.getenv("RAG_MAX_CHUNK_CHARS", "900")), 200)
RAG_CHUNK_OVERLAP_CHARS = max(int(os.getenv("RAG_CHUNK_OVERLAP_CHARS", "120")), 0)
APP_NAME = os.getenv("APP_NAME", "free-ai-gateway")
ROUTING_MODE = os.getenv("ROUTING_MODE", "weighted").strip().lower()

# Cost per 1M tokens (input, output)
COST_PER_1M: Dict[str, Tuple[float, float]] = {
    # Core providers
    "groq": (0.05, 0.10),
    "gemini": (0.075, 0.30),
    "github": (0.0, 0.0),
    "cerebras": (0.0, 0.0),
    "sambanova": (0.10, 0.10),
    "cloudflare": (0.0, 0.0),
    "openrouter": (0.0, 0.0),
    "huggingface": (0.0, 0.0),
    "freetheai": (0.0, 0.0),
    "ollama": (0.0, 0.0),
    "together": (0.0, 0.0),
    "xai": (0.0, 0.0),
    "claude": (0.0, 0.0),
    "nvidia": (0.0, 0.0),
    "nvidia_33": (0.0, 0.0),
    "nvidia_77": (0.0, 0.0),
    "nvidia_custom": (0.0, 0.0),
    # New free providers
    "deepseek": (0.0, 0.0),
    "perplexity": (0.0, 0.0),
    "mistral": (0.0, 0.0),
    "vertex": (0.0, 0.0),
    "cohere": (0.0, 0.0),
    "ai21": (0.0, 0.0),
    "anthropic": (0.0, 0.0),
    "openai": (0.0, 0.0),
    "zeroone": (0.0, 0.0),
    "alibaba": (0.0, 0.0),
    "moonshot": (0.0, 0.0),
    "stepfun": (0.0, 0.0),
    "zhipu": (0.0, 0.0),
    "baichuan": (0.0, 0.0),
    "grok": (0.0, 0.0),
    "qwen": (0.0, 0.0),
    "hunyuan": (0.0, 0.0),
    "jina": (0.0, 0.0),
    "yi": (0.0, 0.0),
    "fireworks": (0.0, 0.0),
    "nebius": (0.0, 0.0),
    "scalr": (0.0, 0.0),
    "deepinfra": (0.0, 0.0),
    "novita": (0.0, 0.0),
    "chutes": (0.0, 0.0),
    "ninerouter": (0.0, 0.0),
    "doubleword": (0.0, 0.0),
}

# --- DYNAMIC STATE ---
# These are loaded from providers.json and updated via reload_config()
_DEFAULT_CHAIN = [s.strip().lower() for s in os.getenv("PROVIDER_CHAIN", "groq,gemini,github,cerebras,huggingface,sambanova,cloudflare,openrouter,deepseek,mistral,zhipu,deepinfra,novita,chutes").split(",") if s.strip()]
_DEFAULT_TASK_TIERS = {
    "general": ["groq", "gemini", "cloudflare", "github", "openrouter", "huggingface", "deepinfra"],
    "chat": ["groq", "gemini", "cloudflare", "github", "openrouter", "huggingface", "deepinfra"],
    "research": ["groq", "gemini", "openrouter", "deepinfra", "novita", "cloudflare"],
    "code": ["groq", "gemini", "openrouter", "deepinfra", "novita", "cloudflare", "github"],
    "vision": ["github", "gemini"],
    "image": ["cloudflare", "huggingface"],
    "gemma": ["groq", "openrouter", "huggingface"],
    "omniverse": ["deepinfra", "novita", "groq", "gemini", "openrouter", "cloudflare", "github"],
    "interview": ["cloudflare", "openrouter", "groq", "deepinfra"],
    "english": ["cloudflare", "openrouter", "groq", "deepinfra"],
    "fast": ["groq", "cloudflare", "openrouter", "cerebras"],
    "cheap": ["cloudflare", "openrouter", "huggingface"],
    "smart": ["deepinfra", "novita", "openrouter", "groq", "gemini"]
}

# ── Tier-based provider chains (for guest 3-prompt funnel) ──────────────────
# VIP: prompt 1 — Best available models, highest quality
TIER_VIP_CHAIN = [s.strip() for s in os.getenv("TIER_VIP_CHAIN", "deepinfra,novita,groq,gemini,github").split(",") if s.strip()]
# STANDARD: prompt 2 — Good quality, reliable
TIER_STANDARD_CHAIN = [s.strip() for s in os.getenv("TIER_STANDARD_CHAIN", "groq,gemini,cloudflare,github").split(",") if s.strip()]
# FREE: prompt 3+ (logged in free users) — Always-on free providers
TIER_FREE_CHAIN = [s.strip() for s in os.getenv("TIER_FREE_CHAIN", "cloudflare,openrouter,huggingface,groq").split(",") if s.strip()]

class Settings:
    """Mutable runtime settings — reloaded from providers.json on demand."""

    def __init__(self):
        self.provider_chain: List[str] = list(_DEFAULT_CHAIN)
        self.task_tiers: Dict[str, List[str]] = dict(_DEFAULT_TASK_TIERS)
        self.dynamic_weights: Dict[str, int] = {}
        self.budget_daily_limit_usd: float = 0.0

    # ── Attribute accessors used by admin.py ──────────────────────
    @property
    def routing_mode(self) -> str:
        return ROUTING_MODE

    @property
    def admin_key(self) -> str:
        return ADMIN_SECRET

    @property
    def provider_cooldown_s(self) -> float:
        return PROVIDER_COOLDOWN_S

    @property
    def groq_api_key(self) -> str | None:
        return os.getenv("GROQ_API_KEY")

    @property
    def nvidia_api_key(self) -> str | None:
        return os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY_CUSTOM")

    @property
    def nvidia_api_key_33(self) -> str | None:
        return os.getenv("NVIDIA_API_KEY_33")

    @property
    def nvidia_api_key_77(self) -> str | None:
        return os.getenv("NVIDIA_API_KEY_77")

settings = Settings()

def reload_config_sync():
    """Synchronous fallback to load settings from providers.json on startup."""
    path = PROVIDERS_JSON_PATH
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        _apply_config(cfg)
    except Exception:
        pass

async def reload_config():
    """Reload settings from providers.json if it exists."""
    path = PROVIDERS_JSON_PATH
    if not os.path.isfile(path):
        return
    try:
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
            cfg = json.loads(content)
        _apply_config(cfg)
    except Exception:
        pass

def _apply_config(cfg):
    if not isinstance(cfg, dict):
        return

    if "provider_chain" in cfg and isinstance(cfg["provider_chain"], list):
        settings.provider_chain = [s.strip().lower() for s in cfg["provider_chain"] if isinstance(s, str) and s.strip()]
    
    if "task_tiers" in cfg and isinstance(cfg["task_tiers"], dict):
        settings.task_tiers.clear()
        settings.task_tiers.update(cfg["task_tiers"])
    
    if "provider_weights" in cfg and isinstance(cfg["provider_weights"], dict):
        settings.dynamic_weights.clear()
        for k, v in cfg["provider_weights"].items():
            if isinstance(k, str) and isinstance(v, (int, float)) and v > 0:
                settings.dynamic_weights[k.strip().lower()] = int(v)
    
    budget = cfg.get("budget", {})
    if isinstance(budget, dict):
        settings.budget_daily_limit_usd = float(budget.get("daily_limit_usd", 0))

# Load on startup
reload_config_sync()
