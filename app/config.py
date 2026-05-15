import os
import json
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import aiofiles

load_dotenv()

# --- CONSTANTS ---
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "changeme")
PROVIDERS_JSON_PATH = os.getenv("PROVIDERS_JSON_PATH", "providers.json")
REQUEST_TIMEOUT_S = float(os.getenv("REQUEST_TIMEOUT_S", "8"))
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
ROUTING_MODE = os.getenv("ROUTING_MODE", "round_robin").strip().lower()

# Cost per 1M tokens (input, output)
COST_PER_1M: Dict[str, Tuple[float, float]] = {
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
    "chutes": (0.0, 0.0),
    "novita": (0.0, 0.0),
    "deepinfra": (0.0, 0.0),
}

# --- DYNAMIC STATE ---
# These are loaded from providers.json and updated via reload_config()
_DEFAULT_CHAIN = [s.strip().lower() for s in os.getenv("PROVIDER_CHAIN", "github,cerebras,huggingface,sambanova,groq,gemini,cloudflare,openrouter,chutes,novita,deepinfra,freetheai").split(",") if s.strip()]
_DEFAULT_TASK_TIERS = {
    "general": ["groq", "gemini", "github", "deepinfra", "chutes", "huggingface", "cloudflare", "novita", "nvidia", "nvidia_77", "nvidia_custom", "cerebras", "sambanova", "openrouter", "together", "xai"],
    "chat": ["groq", "gemini", "github", "deepinfra", "chutes", "huggingface", "cloudflare", "novita", "nvidia", "nvidia_77", "nvidia_custom", "cerebras", "sambanova", "openrouter", "together", "xai"],
    "research": ["github", "gemini", "deepinfra", "chutes", "claude", "xai", "nvidia", "nvidia_77", "nvidia_custom", "novita", "groq", "huggingface", "cerebras", "sambanova", "openrouter", "together"],
    "code": ["github", "deepinfra", "chutes", "huggingface", "cerebras", "groq", "nvidia", "nvidia_77", "nvidia_custom", "novita", "gemini", "sambanova", "openrouter", "together", "xai"],
    "vision": ["github", "gemini", "deepinfra", "nvidia", "nvidia_77", "groq"],
    "image": ["cloudflare", "huggingface", "freetheai"],
    "gemma": ["groq", "openrouter", "huggingface", "deepinfra", "novita", "cerebras", "sambanova", "together"],
    "omniverse": ["nvidia", "nvidia_77", "nvidia_custom", "groq", "deepinfra", "gemini", "github", "chutes", "novita", "huggingface", "cerebras", "openrouter", "together", "xai"],
    "reasoning": ["groq", "deepinfra", "chutes", "nvidia", "nvidia_77", "nvidia_custom", "gemini", "github", "novita", "huggingface", "cerebras", "sambanova", "openrouter", "together", "xai"],
}

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
