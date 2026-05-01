import asyncio
import base64
import json
import os
import random
import re
import time
import unicodedata
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

app = FastAPI(title="Free AI Gateway Router", version="2.0.0")


@dataclass
class Provider:
    key: str
    name: str
    base_url: str
    api_key_env: str
    model_env: str
    default_model: str


PROVIDER_REGISTRY: Dict[str, Provider] = {
    "github": Provider(
        key="github",
        name="GitHub Models",
        base_url="https://models.github.ai/inference",
        api_key_env="GITHUB_TOKEN",
        model_env="GITHUB_MODEL",
        default_model="gpt-4o",
    ),
    "openrouter": Provider(
        key="openrouter",
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        model_env="OPENROUTER_MODEL",
        default_model="openrouter/free",
    ),
    "cloudflare": Provider(
        key="cloudflare",
        name="Cloudflare AI Gateway",
        base_url=os.getenv("CLOUDFLARE_BASE_URL", ""),
        api_key_env="CLOUDFLARE_API_KEY",
        model_env="CLOUDFLARE_MODEL",
        default_model="@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    ),
    "groq": Provider(
        key="groq",
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        model_env="GROQ_MODEL",
        default_model="llama-3.3-70b-versatile",
    ),
    "gemini": Provider(
        key="gemini",
        name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key_env="GEMINI_API_KEY",
        model_env="GEMINI_MODEL",
        default_model="gemini-1.5-pro",
    ),
    "cerebras": Provider(
        key="cerebras",
        name="Cerebras",
        base_url="https://api.cerebras.ai/v1",
        api_key_env="CEREBRAS_API_KEY",
        model_env="CEREBRAS_MODEL",
        default_model="llama-3.3-70b",
    ),
    "sambanova": Provider(
        key="sambanova",
        name="SambaNova",
        base_url="https://api.sambanova.ai/v1",
        api_key_env="SAMBANOVA_API_KEY",
        model_env="SAMBANOVA_MODEL",
        default_model="Llama-3.1-405B-Instruct",
    ),
    "freetheai": Provider(
        key="freetheai",
        name="FreeTheAI",
        base_url="https://api.freetheai.xyz/v1",
        api_key_env="FREETHEAI_API_KEY",
        model_env="FREETHEAI_MODEL",
        default_model="wsf/kimi-k2.6",
    ),
    "huggingface": Provider(
        key="huggingface",
        name="HuggingFace",
        base_url="https://api-inference.huggingface.co/v1/",
        api_key_env="HUGGINGFACE_API_KEY",
        model_env="HUGGINGFACE_MODEL",
        default_model="Qwen/Qwen2.5-72B-Instruct",
    ),
    "ollama": Provider(
        key="ollama",
        name="Ollama Local",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key_env="OLLAMA_API_KEY",
        model_env="OLLAMA_MODEL",
        default_model="llama3.1:8b",
    ),
}

PROVIDER_CHAIN = [s.strip().lower() for s in os.getenv("PROVIDER_CHAIN", "github,cerebras,huggingface,sambanova,groq,gemini,cloudflare,openrouter,freetheai").split(",") if s.strip()]
ROUTING_MODE = os.getenv("ROUTING_MODE", "round_robin").strip().lower()

TASK_TIERS = {
    "general": ["github", "huggingface", "groq", "gemini", "cloudflare"],
    "code": ["github", "huggingface", "cerebras", "groq"],
    "vision": ["github", "gemini"],
    "image": ["cloudflare", "freetheai"],
    "gemma": ["groq", "openrouter", "huggingface"]
}
REQUEST_TIMEOUT_S = float(os.getenv("REQUEST_TIMEOUT_S", "30"))
IMAGE_MAX_WAIT_MS = max(int(os.getenv("IMAGE_MAX_WAIT_MS", "9500")), 1000)
MAX_RETRIES_PER_PROVIDER = max(int(os.getenv("MAX_RETRIES_PER_PROVIDER", "1")), 0)
PROVIDER_FAILURE_THRESHOLD = max(int(os.getenv("PROVIDER_FAILURE_THRESHOLD", "2")), 1)
PROVIDER_COOLDOWN_S = max(float(os.getenv("PROVIDER_COOLDOWN_S", "60")), 0.0)
ADAPTIVE_ROUTING = os.getenv("ADAPTIVE_ROUTING", "1").strip().lower() in {"1", "true", "yes", "on"}
ADAPTIVE_LATENCY_ALPHA = min(max(float(os.getenv("ADAPTIVE_LATENCY_ALPHA", "0.3")), 0.05), 0.95)
ADAPTIVE_ERROR_PENALTY = min(max(float(os.getenv("ADAPTIVE_ERROR_PENALTY", "0.5")), 0.05), 0.95)
RAG_STORE_PATH = os.getenv("RAG_STORE_PATH", ".rag_store.json")
RAG_TOP_K = max(int(os.getenv("RAG_TOP_K", "4")), 1)
RAG_MAX_CHUNK_CHARS = max(int(os.getenv("RAG_MAX_CHUNK_CHARS", "900")), 200)
RAG_CHUNK_OVERLAP_CHARS = max(int(os.getenv("RAG_CHUNK_OVERLAP_CHARS", "120")), 0)
APP_NAME = os.getenv("APP_NAME", "free-ai-gateway")

_rr_counter = 0
_provider_state: Dict[str, Dict[str, Any]] = {}


def _provider_api_key(provider: Provider) -> str:
    if provider.key == "ollama":
        return os.getenv(provider.api_key_env, "ollama")
    if provider.key == "github":
        return os.getenv(provider.api_key_env) or os.getenv("GITHUB_PAT", "")
    return os.getenv(provider.api_key_env, "")


def _normalize_provider_model(provider: Provider, model: str) -> str:
    if provider.key != "github" or "/" in model:
        return model
    github_aliases = {
        "gpt-4o": "openai/gpt-4o",
        "gpt-4o-mini": "openai/gpt-4o-mini",
        "deepseek-r1": "deepseek/deepseek-r1",
    }
    return github_aliases.get(model, model)


def _provider_model(provider: Provider) -> str:
    return _normalize_provider_model(provider, os.getenv(provider.model_env, provider.default_model))


def _provider_base(provider: Provider) -> str:
    if provider.key == "cloudflare":
        return os.getenv("CLOUDFLARE_BASE_URL", provider.base_url)
    if provider.key == "ollama":
        return os.getenv("OLLAMA_BASE_URL", provider.base_url)
    return provider.base_url


def _alias_map() -> Dict[str, Dict[str, str]]:
    raw = os.getenv("MODEL_ALIAS_JSON", "").strip()
    aliases: Dict[str, Dict[str, str]] = {}
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                for alias, provider_map in parsed.items():
                    if isinstance(alias, str) and isinstance(provider_map, dict):
                        normalized_map: Dict[str, str] = {}
                        for p_key, p_model in provider_map.items():
                            if isinstance(p_key, str) and isinstance(p_model, str):
                                normalized_map[p_key.strip().lower()] = p_model.strip()
                        if normalized_map:
                            aliases[alias.strip()] = normalized_map
        except Exception:
            pass

    # Add hardcoded defaults for zero-config experience (Updated for 2026)
    hardcoded_defaults = {
        "gemma": {
            "groq": "llama-3.1-8b-instant",  # Gemma fallback to Llama 8B
            "github": "gpt-4o-mini",
            "openrouter": "google/gemma-2-9b-it:free",
            "huggingface": "google/gemma-2-9b-it"
        },
        "deepseek": {
            "groq": "llama-3.3-70b-versatile", # DeepSeek fallback if missing
            "github": "gpt-4o",
            "cloudflare": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
            "huggingface": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
        },
        "llama": {
            "groq": "llama-3.3-70b-versatile",
            "github": "gpt-4o",
            "cerebras": "llama-3.3-70b",
            "sambanova": "Llama-3.3-70B-Instruct"
        },
        "general": {
            "github": "gpt-4o",
            "groq": "llama-3.3-70b-versatile",
            "gemini": "gemini-1.5-pro"
        },
        "code": {
            "github": "gpt-4o",
            "groq": "llama-3.3-70b-versatile",
            "cerebras": "llama-3.3-70b"
        }
    }
    for k, v in hardcoded_defaults.items():
        if k not in aliases:
            aliases[k] = v

    return aliases


def _provider_model_for_request(provider: Provider, model_override: Optional[str]) -> str:
    if not model_override:
        return _provider_model(provider)
    alias_map = _alias_map()
    provider_model_map = alias_map.get(model_override, {})
    if provider_model_map:
        mapped_model = provider_model_map.get(provider.key)
        if mapped_model:
            return _normalize_provider_model(provider, mapped_model)
    return _normalize_provider_model(provider, model_override)


def _provider_supports_model(provider: Provider, model_override: Optional[str]) -> bool:
    if not model_override:
        return True
    alias_map = _alias_map()
    provider_model_map = alias_map.get(model_override)
    if provider_model_map is None:
        return True
    return provider.key in provider_model_map


def _provider_weights() -> Dict[str, int]:
    raw = os.getenv("PROVIDER_WEIGHTS_JSON", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    weights: Dict[str, int] = {}
    for key, val in parsed.items():
        if not isinstance(key, str):
            continue
        if isinstance(val, int) and val > 0:
            weights[key.strip().lower()] = val
    return weights


def _ensure_provider_state(provider_key: str) -> Dict[str, Any]:
    state = _provider_state.get(provider_key)
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
        _provider_state[provider_key] = state
    return state


def _is_provider_on_cooldown(provider_key: str) -> bool:
    state = _ensure_provider_state(provider_key)
    return state["cooldown_until"] > time.time()


def _mark_provider_success(provider_key: str) -> None:
    state = _ensure_provider_state(provider_key)
    state["failures"] = 0
    state["consecutive_failures"] = 0
    state["successes"] += 1
    state["cooldown_until"] = 0.0
    state["last_error"] = ""
    state["last_attempt_at"] = time.time()
    state["inflight"] = max(0, int(state["inflight"]) - 1)


def _mark_provider_failure(provider_key: str, err: str) -> None:
    state = _ensure_provider_state(provider_key)
    state["failures"] += 1
    state["consecutive_failures"] += 1
    state["failures_total"] += 1
    state["last_error"] = err
    state["last_attempt_at"] = time.time()
    state["inflight"] = max(0, int(state["inflight"]) - 1)
    if state["consecutive_failures"] >= PROVIDER_FAILURE_THRESHOLD:
        state["cooldown_until"] = time.time() + PROVIDER_COOLDOWN_S
        state["consecutive_failures"] = 0


def _mark_provider_attempt(provider_key: str) -> None:
    state = _ensure_provider_state(provider_key)
    state["attempts"] += 1
    state["inflight"] += 1
    state["last_attempt_at"] = time.time()


def _record_provider_latency(provider_key: str, latency_ms: float) -> None:
    state = _ensure_provider_state(provider_key)
    state["last_latency_ms"] = latency_ms
    if state["latency_ewma_ms"] <= 0:
        state["latency_ewma_ms"] = latency_ms
    else:
        state["latency_ewma_ms"] = (
            ADAPTIVE_LATENCY_ALPHA * latency_ms
            + (1.0 - ADAPTIVE_LATENCY_ALPHA) * float(state["latency_ewma_ms"])
        )


def _effective_provider_weight(provider_key: str, base_weight: int) -> float:
    if not ADAPTIVE_ROUTING:
        return float(base_weight)
    state = _ensure_provider_state(provider_key)
    attempts = max(int(state["attempts"]), 1)
    failures = int(state["failures_total"])
    error_rate = failures / attempts
    error_multiplier = max(0.1, 1.0 - (error_rate * (1.0 + ADAPTIVE_ERROR_PENALTY)))

    ewma_latency = float(state["latency_ewma_ms"])
    if ewma_latency <= 0:
        latency_multiplier = 1.0
    else:
        latency_multiplier = max(0.2, min(2.0, 800.0 / ewma_latency))
    return max(0.1, float(base_weight) * error_multiplier * latency_multiplier)


def _active_providers() -> List[Provider]:
    providers: List[Provider] = []
    for key in PROVIDER_CHAIN:
        provider = PROVIDER_REGISTRY.get(key)
        if not provider:
            continue
        base = _provider_base(provider)
        api_key = _provider_api_key(provider)
        if not base:
            continue
        if provider.key != "ollama" and not api_key:
            continue
        providers.append(provider)
    return providers


def _provider_order(providers: List[Provider]) -> List[Provider]:
    global _rr_counter
    if not providers:
        return providers

    hot = [p for p in providers if not _is_provider_on_cooldown(p.key)]
    cold = [p for p in providers if _is_provider_on_cooldown(p.key)]
    active_order = hot if hot else providers

    if ROUTING_MODE == "weighted":
        weights = _provider_weights()
        pool = active_order[:]
        ordered: List[Provider] = []
        while pool:
            sample_weights = [_effective_provider_weight(p.key, weights.get(p.key, 1)) for p in pool]
            selected = random.choices(pool, weights=sample_weights, k=1)[0]
            ordered.append(selected)
            pool.remove(selected)
        return ordered + ([p for p in cold if p not in ordered] if hot else [])

    if ROUTING_MODE == "round_robin":
        start_idx = _rr_counter % len(active_order)
        _rr_counter += 1
        rr = active_order[start_idx:] + active_order[:start_idx]
        return rr + ([p for p in cold if p not in rr] if hot else [])

    return active_order + ([p for p in cold if p not in active_order] if hot else [])


def _client_for_provider(provider: Provider) -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=_provider_base(provider),
        api_key=_provider_api_key(provider),
        timeout=REQUEST_TIMEOUT_S,
    )


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code in (408, 409, 425, 429, 500, 502, 503, 504)
    return False


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False
    task: Optional[str] = Field("general", description="Task type: general, code, vision, image")


class ImageRequest(BaseModel):
    prompt: str = Field(..., min_length=2)


class RAGDocument(BaseModel):
    id: Optional[str] = None
    text: str = Field(..., min_length=5)
    metadata: Optional[Dict[str, Any]] = None


class RAGIngestRequest(BaseModel):
    documents: List[RAGDocument]


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k: Optional[int] = None


class RAGChatRequest(BaseModel):
    query: str = Field(..., min_length=2)
    model: Optional[str] = None
    top_k: Optional[int] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 800
    include_sources: Optional[bool] = True
    stream: Optional[bool] = False


class FineTuneChatRequest(BaseModel):
    prompt: str = Field(..., min_length=2)
    base_model: str = "llama-3.1-8b"
    tuning_id: str = Field(..., description="ID of the fine-tuned model or tuning session")
    temperature: Optional[float] = 0.5


class RAGFineTuneChatRequest(BaseModel):
    query: str = Field(..., min_length=2)
    tuning_id: str = Field(..., description="ID of the fine-tuned model or tuning session")
    base_model: str = "llama-3.1-8b"
    model: Optional[str] = None
    top_k: Optional[int] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 800
    include_sources: Optional[bool] = True


class UnifiedAIChatRequest(BaseModel):
    query: Optional[str] = Field(None, min_length=2)
    messages: Optional[List[Dict[str, Any]]] = None
    mode: str = Field("chat", description="chat, rag, fine_tune, or rag_fine_tune")
    model: Optional[str] = None
    task: str = "general"
    tuning_id: Optional[str] = None
    base_model: str = "llama-3.1-8b"
    top_k: Optional[int] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 800
    include_sources: Optional[bool] = True


class SimpleRAGStore:
    def __init__(self, path: str):
        self.path = path
        self.chunks: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            self.chunks = []
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.chunks = payload.get("chunks", []) if isinstance(payload, dict) else []
        except Exception:
            self.chunks = []

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"chunks": self.chunks}, f, ensure_ascii=False)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        normalized = re.sub(r"\s+", " ", text.lower()).strip()
        return re.findall(r"[a-z0-9_]+", normalized)

    @staticmethod
    def _chunk_text(text: str, size: int, overlap: int) -> List[str]:
        text = text.strip()
        if len(text) <= size:
            return [text]
        chunks: List[str] = []
        step = max(size - overlap, 1)
        start = 0
        while start < len(text):
            piece = text[start : start + size].strip()
            if piece:
                chunks.append(piece)
            start += step
        return chunks

    def ingest(self, docs: List[RAGDocument]) -> Dict[str, int]:
        added_chunks = 0
        for i, doc in enumerate(docs):
            doc_id = doc.id or f"doc-{int(time.time())}-{i}"
            metadata = doc.metadata or {}
            for idx, piece in enumerate(self._chunk_text(doc.text, RAG_MAX_CHUNK_CHARS, RAG_CHUNK_OVERLAP_CHARS)):
                tokens = self._tokenize(piece)
                if not tokens:
                    continue
                self.chunks.append(
                    {
                        "chunk_id": f"{doc_id}#chunk-{idx}",
                        "doc_id": doc_id,
                        "text": piece,
                        "tokens": tokens,
                        "metadata": metadata,
                    }
                )
                added_chunks += 1
        self._save()
        return {"documents": len(docs), "chunks": added_chunks}

    def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        q_tokens = self._tokenize(query)
        if not q_tokens or not self.chunks:
            return []
        q_set: Set[str] = set(q_tokens)
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for chunk in self.chunks:
            tokens = chunk.get("tokens", [])
            if not tokens:
                continue
            token_set = set(tokens)
            overlap = len(q_set.intersection(token_set))
            if overlap == 0:
                continue
            lexical = overlap / max(len(q_set), 1)
            density = overlap / max(len(token_set), 1)
            score = (0.7 * lexical) + (0.3 * density)
            scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "score": round(score, 4),
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "text": chunk["text"],
                "metadata": chunk.get("metadata", {}),
            }
            for score, chunk in scored[:top_k]
        ]


rag_store = SimpleRAGStore(RAG_STORE_PATH)


def _rag_context_for_query(query: str, top_k: int) -> Tuple[str, List[Dict[str, Any]]]:
    hits = rag_store.search(query, top_k=top_k)
    if not hits:
        raise HTTPException(status_code=400, detail="RAG store is empty or no relevant context. Call /v1/rag/ingest first.")

    context_lines = []
    sources = []
    for hit in hits:
        source_id = hit["chunk_id"]
        context_lines.append(f"[{source_id}] {hit['text']}")
        sources.append(
            {
                "chunk_id": hit["chunk_id"],
                "doc_id": hit["doc_id"],
                "score": hit["score"],
                "metadata": hit.get("metadata", {}),
            }
        )
    return "\n\n".join(context_lines), sources


@app.get("/favicon.ico")
async def favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#0f172a"/>
<path d="M16 34c0-10 7-18 16-18s16 8 16 18" fill="none" stroke="#38bdf8" stroke-width="5" stroke-linecap="round"/>
<path d="M20 34h8l4 10 4-24 4 14h4" fill="none" stroke="#a78bfa" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="32" cy="48" r="4" fill="#34d399"/>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/image-fallback")
async def image_fallback(prompt: str = "Image generation temporarily unavailable"):
    safe_prompt = prompt[:140].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    seed = abs(hash(prompt)) % 9973
    c1 = f"#{(0x224466 + (seed * 31)) % 0xFFFFFF:06x}"
    c2 = f"#{(0x0f766e + (seed * 53)) % 0xFFFFFF:06x}"
    c3 = f"#{(0x7c3aed + (seed * 71)) % 0xFFFFFF:06x}"
    x1 = 120 + (seed % 240)
    y1 = 190 + (seed % 220)
    x2 = 720 - (seed % 210)
    y2 = 680 - (seed % 180)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
<defs>
  <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
    <stop offset="0%" stop-color="{c1}"/>
    <stop offset="100%" stop-color="{c2}"/>
  </linearGradient>
  <radialGradient id="r1" cx="30%" cy="20%" r="65%">
    <stop offset="0%" stop-color="{c3}" stop-opacity="0.58"/>
    <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
  </radialGradient>
</defs>
<rect width="1024" height="1024" fill="url(#g)"/>
<rect width="1024" height="1024" fill="url(#r1)"/>
<circle cx="{x1}" cy="{y1}" r="190" fill="#ffffff" fill-opacity="0.08"/>
<circle cx="{x2}" cy="{y2}" r="240" fill="#ffffff" fill-opacity="0.06"/>
<rect x="44" y="44" width="936" height="936" rx="24" fill="none" stroke="#38bdf8" stroke-opacity="0.4" stroke-width="4"/>
<text x="72" y="120" fill="#dbeafe" font-family="monospace" font-size="28">free-ai-gateway local instant render</text>
<text x="72" y="170" fill="#bfdbfe" font-family="monospace" font-size="22">Upstream free image API busy. This fallback is generated from your prompt.</text>
<foreignObject x="72" y="230" width="880" height="700">
  <div xmlns="http://www.w3.org/1999/xhtml" style="color:#e2e8f0;font-family:system-ui,Segoe UI,sans-serif;font-size:36px;line-height:1.35;white-space:pre-wrap;">{safe_prompt}</div>
</foreignObject>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml")


# --- GIAO DIỆN WEB ---
@app.get("/", response_class=HTMLResponse)
async def index():
    providers = _active_providers()
    chain_view = " -> ".join([p.name for p in providers]) if providers else "No provider configured"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ultimate AI Gateway</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="/favicon.ico">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
            body {{ background: #0f172a; color: white; font-family: 'Inter', sans-serif; }}
            .chat-box {{ height: 60vh; overflow-y: auto; scroll-behavior: smooth; }}
            .img-result {{ max-width: 100%; border-radius: 20px; margin-top: 12px; border: 4px solid #1e293b; transition: all 0.3s; }}
            .img-result:hover {{ border-color: #3b82f6; transform: scale(1.01); }}
            .user-msg {{ background: #2563eb; border-radius: 20px 20px 0 20px; }}
            .ai-msg {{ background: #1e293b; border-radius: 20px 20px 20px 0; }}
            @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
            .loading-dots {{ animation: pulse 1s infinite; }}
        </style>
    </head>
    <body class="flex flex-col items-center justify-center min-h-screen p-2 sm:p-4">
        <div class="w-full max-w-3xl bg-slate-800 rounded-[2.5rem] shadow-2xl p-4 sm:p-8 border border-slate-700">
            <div class="flex justify-between items-center mb-8">
                <div>
                    <h1 class="text-3xl font-black text-white">🚀 Personal AI</h1>
                    <p class="text-slate-400 text-xs mt-1">Routing: <span class="text-blue-400 font-bold uppercase">{ROUTING_MODE}</span></p>
                    <p class="text-slate-400 text-xs">Providers: <span class="text-emerald-400 font-bold">{chain_view}</span></p>
                </div>
                <button onclick="window.location.reload()" class="bg-slate-700 hover:bg-slate-600 p-2 px-4 rounded-full text-xs font-bold transition">Reset Chat</button>
            </div>
            
            <div id="chat" class="chat-box mb-6 space-y-4 p-4 bg-slate-900/80 rounded-[2rem] border border-slate-700/50 shadow-inner">
                <div class="text-slate-500 text-center py-10 text-sm">Gõ "Vẽ..." để tạo ảnh hoặc đặt câu hỏi bất kỳ.</div>
            </div>

            <div class="relative flex gap-3">
                <input id="userInput" type="text" placeholder="Nhập tin nhắn..." 
                    class="flex-1 bg-slate-900 border-2 border-slate-700 rounded-2xl px-6 py-4 focus:border-blue-500 outline-none transition-all text-lg shadow-inner">
                <button id="sendBtn" onclick="send()" class="bg-blue-600 hover:bg-blue-500 px-8 rounded-2xl font-black transition-all shadow-lg active:scale-95">Gửi</button>
            </div>
        </div>

        <script>
            const chat = document.getElementById('chat');
            const input = document.getElementById('userInput');
            const btn = document.getElementById('sendBtn');
            let messages = [];

            async function send() {{
                const text = input.value.trim();
                if (!text) return;

                appendMsg('user', text);
                input.value = '';
                
                const isImageRequest = /^(vẽ|draw|tạo ảnh|image|picture)/i.test(text);
                const loadingMsg = appendMsg('assistant', '<span class="loading-dots">Đang xử lý...</span>');
                btn.disabled = true;

                try {{
                    if (isImageRequest) {{
                        const res = await fetch('/v1/images/generations', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ prompt: text }})
                        }});
                        const data = await res.json();
                        if (!res.ok) throw new Error(data.detail || 'Image generation failed');
                        const imageUrl = data.data[0].url;
                        const translated = data.translated_prompt || text;
                        loadingMsg.innerHTML = `
                            <div class="text-xs text-slate-400 mb-2 italic">Dịch: ${{translated}}</div>
                            <img src="${{imageUrl}}" class="img-result" alt="AI Image" 
                                 onload="this.parentElement.classList.remove('loading-dots')"
                                 onerror="this.src='https://dummyimage.com/1024x1024/1e293b/ffffff&text=Lỗi+load+ảnh+hãy+thử+lại'">
                        `;
                    }} else {{
                        messages.push({{role: 'user', content: text}});
                        const res = await fetch('/v1/chat/completions', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ messages: messages }})
                        }});
                        const data = await res.json();
                        if (!res.ok) throw new Error(data.detail || 'Chat failed');
                        const reply = data.choices[0].message.content;
                        loadingMsg.innerHTML = reply;
                        messages.push({{role: 'assistant', content: reply}});
                    }}
                }} catch (e) {{
                    loadingMsg.innerHTML = "Lỗi: " + e.message;
                }}
                
                btn.disabled = false;
                chat.scrollTop = chat.scrollHeight;
            }}

            function appendMsg(role, text) {{
                const div = document.createElement('div');
                div.className = role === 'user' ? 'flex justify-end' : 'flex justify-start';
                div.innerHTML = `<div class="max-w-[85%] px-6 py-3 shadow-xl ${{role === 'user' ? 'user-msg text-white' : 'ai-msg text-slate-100'}}">${{text}}</div>`;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
                return div.querySelector('div');
            }}

            input.addEventListener('keypress', (e) => {{ if(e.key === 'Enter') send(); }});
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/hub", response_class=HTMLResponse)
async def unified_hub():
    providers = _active_providers()
    chain_view = " -> ".join([p.key for p in providers]) if providers else "No provider configured"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Free AI Gateway Hub</title>
        <link rel="icon" href="/favicon.ico">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #090f1c;
                --bg-soft: #0d1628;
                --panel: rgba(14, 22, 38, 0.9);
                --panel-border: rgba(148, 163, 184, 0.22);
                --text: #e7edf9;
                --muted: #8da2c7;
                --accent: #1d9bf0;
                --accent-2: #0ea5e9;
                --success: #10b981;
            }}
            body {{
                background:
                    radial-gradient(900px 460px at 8% -12%, rgba(29, 155, 240, 0.18), transparent 60%),
                    radial-gradient(700px 420px at 92% 0%, rgba(16, 185, 129, 0.14), transparent 62%),
                    var(--bg);
                color: var(--text);
                font-family: "Manrope", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}
            .panel {{
                background: linear-gradient(180deg, rgba(16, 25, 44, 0.86) 0%, rgba(11, 18, 34, 0.9) 100%);
                border: 1px solid var(--panel-border);
                box-shadow: 0 12px 40px rgba(2, 6, 23, 0.42), inset 0 1px 0 rgba(255,255,255,0.04);
            }}
            .mono {{ font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
            .msg-user {{ background: linear-gradient(135deg, #0f6ec7, #1d9bf0); color: #fff; border-radius: 14px 14px 2px 14px; }}
            .msg-ai {{ background: #0f172a; border: 1px solid rgba(148, 163, 184, 0.22); border-radius: 14px 14px 14px 2px; }}
            .mode {{
                background: #0f172a;
                border: 1px solid rgba(148, 163, 184, 0.26);
                transition: transform .16s ease, border-color .2s ease, background-color .2s ease;
            }}
            .mode:hover {{ border-color: rgba(29, 155, 240, 0.64); transform: translateY(-1px); }}
            .mode.active {{
                background: linear-gradient(135deg, #1d9bf0, #0ea5e9);
                border-color: rgba(125, 211, 252, 0.8);
                color: #fff;
                box-shadow: 0 10px 20px rgba(14, 165, 233, 0.24);
            }}
            .chat-scroll {{ min-height: 360px; max-height: calc(100vh - 260px); }}
            select, input, textarea {{
                background: #0b1222;
                border-color: rgba(148, 163, 184, 0.28);
                color: var(--text);
            }}
            select:focus, input:focus, textarea:focus {{
                outline: none;
                border-color: rgba(56, 189, 248, 0.85);
                box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.18);
            }}
        </style>
    </head>
    <body class="min-h-screen">
        <main class="mx-auto max-w-7xl p-4 lg:p-6 grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-4">
            <aside class="panel rounded-xl p-4 space-y-4 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:overflow-y-auto">
                <div>
                    <h1 class="text-2xl font-extrabold tracking-tight">Free AI Gateway</h1>
                    <p class="text-xs mt-1" style="color: var(--muted)">One route. Many free/free-tier providers. Auto failover.</p>
                </div>

                <div class="text-xs rounded-lg p-3 border border-slate-800" style="background: rgba(2, 6, 23, 0.52)">
                    <div class="uppercase tracking-wide mb-1" style="color: var(--muted)">Routing</div>
                    <div class="mono text-sky-300 font-semibold">{ROUTING_MODE}</div>
                    <div class="mono mt-1 break-words text-slate-400">{chain_view}</div>
                </div>

                <label class="block text-xs font-bold text-slate-300">Model alias</label>
                <select id="model" class="w-full border rounded-lg px-3 py-2.5 text-sm">
                    <option value="smart-chat">smart-chat</option>
                    <option value="cf-dynamic">cf-dynamic</option>
                    <option value="fast-free">fast-free</option>
                    <option value="reasoning-free">reasoning-free</option>
                    <option value="gemma-free">gemma-free</option>
                    <option value="gemma-quality">gemma-quality</option>
                </select>

                <div class="grid grid-cols-2 gap-2">
                    <button class="mode active rounded-lg px-3 py-2 text-xs font-bold" data-mode="chat">Chat</button>
                    <button class="mode rounded-lg px-3 py-2 text-xs font-bold" data-mode="rag">RAG</button>
                    <button class="mode rounded-lg px-3 py-2 text-xs font-bold" data-mode="fine_tune">Fine profile</button>
                    <button class="mode rounded-lg px-3 py-2 text-xs font-bold" data-mode="rag_fine_tune">RAG + Fine</button>
                    <button class="mode rounded-lg px-3 py-2 text-xs font-bold col-span-2" data-mode="image">Image / Flux</button>
                </div>

                <div class="space-y-2">
                    <label class="block text-xs font-bold text-slate-300">Tuning ID</label>
                    <input id="tuningId" value="support-v1" class="w-full border rounded-lg px-3 py-2.5 text-sm">
                </div>

                <div class="space-y-2">
                    <label class="block text-xs font-bold text-slate-300">Ingest RAG document <span class="text-slate-500 font-normal">(không phải ô chat)</span></label>
                    <input id="docId" value="manual-doc" class="w-full border rounded-lg px-3 py-2.5 text-sm">
                    <textarea id="ragText" rows="4" class="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Dán tài liệu dài tối thiểu 5 ký tự, ví dụ pricing, FAQ, policy..."></textarea>
                    <button onclick="ingestRag()" class="w-full bg-emerald-600 hover:bg-emerald-500 rounded-lg px-3 py-2 text-sm font-bold">Ingest to RAG</button>
                    <div id="ragStatus" class="text-xs" style="color: var(--muted)"></div>
                </div>

                <button onclick="loadState()" class="w-full bg-slate-800 hover:bg-slate-700 rounded-lg px-3 py-2 text-sm font-bold">Refresh router state</button>
                <pre id="state" class="text-[11px] bg-slate-950 rounded-lg p-3 overflow-auto max-h-40 border border-slate-800"></pre>
            </aside>

            <section id="chatPanel" class="panel rounded-xl p-4 flex flex-col h-[calc(100vh-2rem)] lg:h-[calc(100vh-3rem)]">
                <div class="flex items-center justify-between gap-3 border-b border-slate-800 pb-3">
                    <div>
                    <h2 class="text-xl font-extrabold tracking-tight">Unified Chat</h2>
                    <p id="modeLabel" class="text-xs" style="color: var(--muted)">Mode: chat</p>
                </div>
                    <a href="/docs" class="text-xs text-sky-300 hover:text-sky-200">API docs</a>
                </div>

                <div id="chat" class="chat-scroll flex-1 overflow-y-auto py-4 space-y-3">
                    <div class="msg-ai max-w-[86%] px-4 py-3 text-sm text-slate-300">
                        Nhập câu hỏi hoặc prompt tạo ảnh ở ô dưới cùng rồi bấm Send. Nếu muốn RAG, ingest tài liệu ở panel trái trước.
                    </div>
                </div>

                <div class="border-t border-slate-800 pt-3">
                    <textarea id="prompt" rows="3" class="w-full border rounded-xl px-4 py-3 text-sm" placeholder="CHAT Ở ĐÂY: nhập câu hỏi hoặc prompt tạo ảnh rồi bấm Send. Enter để gửi, Shift+Enter xuống dòng."></textarea>
                    <div class="mt-2 flex justify-between gap-2">
                        <button onclick="clearChat()" class="bg-slate-800 hover:bg-slate-700 rounded-lg px-4 py-2 text-sm font-bold">Clear</button>
                        <button onclick="sendUnified()" class="bg-indigo-600 hover:bg-indigo-500 rounded-lg px-5 py-2 text-sm font-black">Send</button>
                    </div>
                </div>
            </section>
        </main>

        <script>
            let currentMode = 'chat';
            const chat = document.getElementById('chat');
            const promptEl = document.getElementById('prompt');

            document.querySelectorAll('.mode').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    currentMode = btn.dataset.mode;
                    document.querySelectorAll('.mode').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    document.getElementById('modeLabel').innerText = 'Mode: ' + currentMode;
                    document.getElementById('chatPanel').scrollIntoView({{behavior: 'smooth', block: 'nearest'}});
                    promptEl.focus();
                }});
            }});

            function addMessage(role, html) {{
                const row = document.createElement('div');
                row.className = role === 'user' ? 'flex justify-end' : 'flex justify-start';
                row.innerHTML = `<div class="${{role === 'user' ? 'msg-user' : 'msg-ai'}} max-w-[86%] px-4 py-3 text-sm whitespace-pre-wrap">${{html}}</div>`;
                chat.appendChild(row);
                chat.scrollTop = chat.scrollHeight;
                return row.querySelector('div');
            }}

            function addImageMessage(imageUrl, translatedPrompt, originalPrompt = '') {{
                const row = document.createElement('div');
                row.className = 'flex justify-start';
                const fallback = '/image-fallback?prompt=' + encodeURIComponent(translatedPrompt || 'Image generation temporarily unavailable');
                const imgId = 'img_' + Date.now().toString(36);
                row.innerHTML = `
                    <div class="msg-ai max-w-[86%] px-4 py-3 text-sm">
                        ${{originalPrompt ? `<div class="text-xs text-slate-500 mb-1">Original: ${{originalPrompt}}</div>` : ''}}
                        ${{translatedPrompt ? `<div class="text-xs text-slate-400 mb-2">Sent to model: ${{translatedPrompt}}</div>` : ''}}
                        <img id="${{imgId}}" src="${{imageUrl}}" alt="AI generated image" class="max-w-full rounded-xl border border-slate-700 bg-slate-950" onerror="this.onerror=null; this.src='${{fallback}}';">
                    </div>
                `;
                chat.appendChild(row);
                chat.scrollTop = chat.scrollHeight;
                const img = document.getElementById(imgId);
                if (img) {{
                    const timeout = setTimeout(() => {{
                        if (!img.complete || img.naturalWidth === 0) img.src = fallback;
                    }}, {IMAGE_MAX_WAIT_MS});
                    img.addEventListener('load', () => clearTimeout(timeout), {{ once: true }});
                    img.addEventListener('error', () => clearTimeout(timeout), {{ once: true }});
                }}
            }}

            function showLocalImageFallback(promptText) {{
                addImageMessage('/image-fallback?prompt=' + encodeURIComponent(promptText), promptText + ' (local fallback)');
            }}

            function clearChat() {{
                chat.innerHTML = '';
            }}

            async function ingestRag() {{
                const text = document.getElementById('ragText').value.trim();
                const id = document.getElementById('docId').value.trim() || 'manual-doc';
                const status = document.getElementById('ragStatus');
                if (text.length < 5) {{
                    status.innerText = 'Tài liệu RAG cần tối thiểu 5 ký tự. Câu hỏi thì nhập ở ô chat bên phải.';
                    return;
                }}
                status.innerText = 'Ingesting...';
                const res = await fetch('/v1/rag/ingest', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{documents: [{{id, text, metadata: {{source: 'hub'}}}}]}})
                }});
                const data = await res.json();
                status.innerText = res.ok ? `OK: ${{data.ingested_chunks}} chunks, total ${{data.total_chunks}}` : 'Không ingest được: ' + friendlyError(data.detail || data);
                if (res.ok) promptEl.focus();
            }}

            async function sendUnified() {{
                const query = promptEl.value.trim();
                if (!query) return;
                addMessage('user', query);
                promptEl.value = '';
                const pending = addMessage('ai', currentMode === 'image' ? 'Generating image with Flux...' : 'Routing...');
                try {{
                    if (currentMode === 'image') {{
                        const controller = new AbortController();
                        const timer = setTimeout(() => controller.abort(), {IMAGE_MAX_WAIT_MS});
                        const res = await fetch('/v1/images/generations', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{prompt: query}}),
                            signal: controller.signal
                        }});
                        clearTimeout(timer);
                        const data = await res.json();
                        if (!res.ok) throw new Error(JSON.stringify(data.detail || data));
                        pending.remove();
                        const promptLabel = `${{data.translated_prompt || data.warning || query}} [provider: ${{data.provider || 'unknown'}}]`;
                        addImageMessage(data.data?.[0]?.url, promptLabel, data.original_prompt || query);
                        return;
                    }}
                    const res = await fetch('/v1/ai/chat', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            query,
                            mode: currentMode,
                            model: document.getElementById('model').value,
                            tuning_id: document.getElementById('tuningId').value,
                            top_k: 4,
                            include_sources: true
                        }})
                    }});
                    const data = await res.json();
                    if (!res.ok) throw new Error(JSON.stringify(data.detail || data));
                    const reply = data.reply || data.choices?.[0]?.message?.content || JSON.stringify(data);
                    const provider = data.router ? `\\n\\n[provider: ${{data.router.provider}}, model: ${{data.router.model}}]` : '';
                    const sources = data.sources ? `\\n[sources: ${{data.sources.map(s => s.chunk_id).join(', ')}}]` : '';
                    pending.innerText = reply + provider + sources;
                }} catch (e) {{
                    if (currentMode === 'image') {{
                        pending.remove();
                        showLocalImageFallback(query);
                    }} else {{
                        pending.innerText = 'ERROR: ' + e.message;
                    }}
                }}
            }}

            function friendlyError(detail) {{
                const raw = typeof detail === 'string' ? detail : JSON.stringify(detail);
                if (raw.includes('at least 5 characters')) return 'nội dung quá ngắn, cần tối thiểu 5 ký tự.';
                if (raw.includes('No providers configured')) return 'chưa có provider active. Kiểm tra API key hoặc Ollama.';
                return raw;
            }}

            async function loadState() {{
                const box = document.getElementById('state');
                const res = await fetch('/router/state');
                box.innerText = JSON.stringify(await res.json(), null, 2);
            }}

            promptEl.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    sendUnified();
                }}
            }});
            loadState();
            promptEl.focus();
        </script>
    </body>
    </html>
    """
    return html_content

# --- PROXY ẢNH (Vượt rào cản trình duyệt) ---
@app.get("/proxy-image")
async def proxy_image(url: str):
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
            # Giả lập browser để không bị chặn
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            resp = None
            for attempt in range(3):
                resp = await client.get(url, headers=headers, follow_redirects=True)
                if resp.status_code != 429:
                    break
                await asyncio.sleep(0.7 * (attempt + 1))
            if resp is None:
                raise HTTPException(status_code=502, detail="Không thể tải ảnh từ nguồn")
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Không thể tải ảnh từ nguồn")
            content_type = resp.headers.get("content-type", "image/jpeg")
            if not content_type.startswith("image/"):
                raise HTTPException(status_code=502, detail="Nguồn trả dữ liệu không phải ảnh. Hãy thử prompt khác.")
            return Response(content=resp.content, media_type=content_type)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ảnh đang render chậm. Hãy thử lại hoặc rút ngắn prompt.")

# --- ENDPOINT TẠO ẢNH ---
async def _chat_with_failover(
    messages: List[Dict[str, Any]],
    model_override: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    task: str = "general",
) -> Tuple[Any, Dict[str, Any]]:
    # Filter chain by task if applicable
    chain = TASK_TIERS.get(task, PROVIDER_CHAIN)
    active = [p for p in _active_providers() if p.key in chain]
    if not active:
        active = _active_providers()
        
    providers = _provider_order(active)
    if not providers:
        raise HTTPException(status_code=400, detail="No providers configured. Set API keys in environment variables.")

    errors: List[Dict[str, str]] = []
    for provider in providers:
        if not _provider_supports_model(provider, model_override):
            continue
        client = _client_for_provider(provider)
        model = _provider_model_for_request(provider, model_override)
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p

        last_error: Optional[Exception] = None
        for _attempt in range(MAX_RETRIES_PER_PROVIDER + 1):
            _mark_provider_attempt(provider.key)
            started_at = time.perf_counter()
            try:
                response = await client.chat.completions.create(**payload)
                _record_provider_latency(provider.key, (time.perf_counter() - started_at) * 1000.0)
                _mark_provider_success(provider.key)
                meta = {"provider": provider.key, "provider_name": provider.name, "model": model}
                return response, meta
            except Exception as exc:  # noqa: BLE001
                _record_provider_latency(provider.key, (time.perf_counter() - started_at) * 1000.0)
                last_error = exc
                if not _is_retryable(exc):
                    break

        if last_error is not None:
            _mark_provider_failure(provider.key, str(last_error))
            errors.append({"provider": provider.key, "error": str(last_error)})

    raise HTTPException(
        status_code=502,
        detail={"message": "All providers failed", "errors": errors},
    )


_IMAGE_COMMAND_RE = re.compile(
    r"^\s*(vẽ|ve|draw|tạo ảnh|tao anh|tạo hình|tao hinh|gen ảnh|gen anh|generate image|image|picture|ảnh|anh)\s*[:,-]?\s*",
    re.IGNORECASE,
)

_VI_IMAGE_PHRASE_MAP: List[Tuple[str, str]] = [
    ("mat troi moc", "sunrise"),
    ("mat troi lan", "sunset"),
    ("mat troi", "the sun"),
    ("mat trang tron", "a full moon"),
    ("mat trang ram", "a full moon"),
    ("mat trang khuyet", "a crescent moon"),
    ("mat trang", "the moon"),
    ("anh trang", "moonlight"),
    ("trang ram", "full moon"),
    ("trang khuyet", "crescent moon"),
    ("tren bau troi dem", "in the night sky"),
    ("tren bau troi", "in the sky"),
    ("bau troi dem", "night sky"),
    ("tren bien", "over the ocean"),
    ("tren nui", "over the mountain"),
    ("tren troi", "in the sky"),
    ("trong rung", "in a forest"),
    ("giua rung", "in the middle of a forest"),
    ("ben bo bien", "by the seaside"),
    ("binh minh", "sunrise"),
    ("hoang hon", "sunset"),
    ("bau troi", "sky"),
    ("dam may", "clouds"),
    ("may trang", "white clouds"),
    ("bien", "ocean"),
    ("bai bien", "beach"),
    ("ban dem", "night"),
    ("dem", "night"),
    ("ngoi sao", "stars"),
    ("ngon nui", "mountain"),
    ("nui", "mountain"),
    ("rung", "forest"),
    ("dong co", "grass field"),
    ("canh dong", "field"),
    ("song", "river"),
    ("ho nuoc", "lake"),
    ("thanh pho", "city"),
    ("toa nha", "building"),
    ("duong pho", "street"),
    ("xe hoi", "car"),
    ("o to", "car"),
    ("may bay", "airplane"),
    ("tau vu tru", "spaceship"),
    ("phi hanh gia", "astronaut"),
    ("robot", "robot"),
    ("con meo", "cat"),
    ("meo", "cat"),
    ("con cho", "dog"),
    ("cho", "dog"),
    ("chim", "bird"),
    ("ca", "fish"),
    ("hoa sen", "lotus flower"),
    ("hoa hong", "rose"),
    ("hoa", "flower"),
    ("chan dung", "portrait"),
    ("co gai", "woman"),
    ("chang trai", "man"),
    ("nguoi", "person"),
    ("em be", "child"),
    ("viet nam", "Vietnam"),
    ("sai gon", "Saigon"),
    ("ha noi", "Hanoi"),
    ("de thuong", "cute"),
    ("dep", "beautiful"),
    ("sieu thuc", "surreal"),
    ("dien anh", "cinematic"),
    ("tuong lai", "futuristic"),
    ("toi gian", "minimal"),
    ("mau sac", "colorful"),
    ("anh sang", "light"),
    ("vang", "golden"),
    ("do", "red"),
    ("xanh duong", "blue"),
    ("xanh la", "green"),
    ("trang", "white"),
    ("den", "black"),
]


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").replace("đ", "d").replace("Đ", "D")


def _translate_vi_image_terms(prompt: str) -> str:
    translated = _strip_accents(prompt).lower()
    translated = re.sub(r"[^a-z0-9\s,.-]", " ", translated)
    translated = re.sub(r"\s+", " ", translated).strip()
    if not translated:
        return prompt

    for vi_phrase, en_phrase in sorted(_VI_IMAGE_PHRASE_MAP, key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(rf"\b{re.escape(vi_phrase)}\b", en_phrase, translated)

    translated = re.sub(r"\s+", " ", translated).strip(" ,.-")
    return translated or prompt


def _prepare_image_prompt(prompt: str) -> str:
    clean_prompt = re.sub(r"\s+", " ", prompt).strip()
    subject = _IMAGE_COMMAND_RE.sub("", clean_prompt).strip(" ,.-:")
    subject = subject or clean_prompt
    translated_subject = _translate_vi_image_terms(subject)

    word_count = len(re.findall(r"\w+", translated_subject))
    if word_count <= 4:
        compiled = (
            f"A clear high-quality image of {translated_subject}, centered main subject, "
            "simple clean background, visually faithful to the prompt, no text, no watermark, "
            "no unrelated objects."
        )
    else:
        compiled = (
            f"{translated_subject}. Make the main subject obvious and visually faithful to the prompt. "
            "No text, no watermark, no unrelated objects."
        )

    return compiled[:900]


async def _image_from_cloudflare(prompt: str) -> Optional[Dict[str, str]]:
    api_key = os.getenv("CLOUDFLARE_API_KEY", "").strip()
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    model = os.getenv("CLOUDFLARE_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell").strip()
    if not api_key or not account_id:
        return None

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"prompt": prompt}
    timeout_s = min(REQUEST_TIMEOUT_S, 9.0)
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return None

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("image/"):
            encoded = base64.b64encode(response.content).decode("ascii")
            return {
                "provider": "cloudflare",
                "url": f"data:{content_type};base64,{encoded}",
                "prompt": prompt,
            }

        try:
            body = response.json()
        except ValueError:
            return None
        result = body.get("result", {}) if isinstance(body, dict) else {}
        if isinstance(result, str) and result:
            return {
                "provider": "cloudflare",
                "url": f"data:image/png;base64,{result}",
                "prompt": prompt,
            }
        image_b64 = result.get("image") if isinstance(result, dict) else None
        if isinstance(image_b64, str) and image_b64:
            return {
                "provider": "cloudflare",
                "url": f"data:image/png;base64,{image_b64}",
                "prompt": prompt,
            }
    return None


async def _image_from_huggingface(prompt: str) -> Optional[Dict[str, str]]:
    api_key = os.getenv("HUGGINGFACE_API_KEY", "").strip()
    model = os.getenv("HUGGINGFACE_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell").strip()
    if not api_key or not model:
        return None

    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"inputs": prompt}
    timeout_s = min(REQUEST_TIMEOUT_S, 9.0)
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return None
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            return None
        encoded = base64.b64encode(response.content).decode("ascii")
        return {
            "provider": "huggingface",
            "url": f"data:{content_type};base64,{encoded}",
            "prompt": prompt,
        }


@app.post("/v1/images/generations")
async def generate_image(req: ImageRequest):
    clean_prompt = re.sub(r"\s+", " ", req.prompt).strip()
    compiled_prompt = _prepare_image_prompt(clean_prompt)
    try:
        cloudflare_image = await _image_from_cloudflare(compiled_prompt)
        if cloudflare_image is not None:
            return {
                "provider": cloudflare_image["provider"],
                "original_prompt": clean_prompt,
                "translated_prompt": cloudflare_image["prompt"],
                "data": [{"url": cloudflare_image["url"]}],
            }

        hf_image = await _image_from_huggingface(compiled_prompt)
        if hf_image is not None:
            return {
                "provider": hf_image["provider"],
                "original_prompt": clean_prompt,
                "translated_prompt": hf_image["prompt"],
                "data": [{"url": hf_image["url"]}],
            }
    except Exception:  # noqa: BLE001
        pass

    # Last fallback: public free endpoint (flaky but no key required)
    encoded_prompt = urllib.parse.quote(compiled_prompt)
    seed = random.randint(1, 999999)
    source_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=640&height=640&seed={seed}&model=flux"
    return {
        "provider": "pollinations",
        "original_prompt": clean_prompt,
        "translated_prompt": compiled_prompt,
        "data": [{"url": source_url}],
    }

@app.post("/v1/chat/completions")
async def proxy_chat_completions(req: ChatRequest):
    try:
        response, meta = await _chat_with_failover(
            messages=req.messages,
            model_override=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            top_p=None,
            task=req.task
        )
        payload = response.model_dump()
        payload["router"] = meta
        return JSONResponse(content=payload, headers={"x-ai-provider": meta["provider"], "x-ai-model": meta["model"]})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/ai/chat")
async def unified_ai_chat(req: UnifiedAIChatRequest):
    mode = req.mode.strip().lower()
    allowed_modes = {"chat", "rag", "fine_tune", "rag_fine_tune"}
    if mode not in allowed_modes:
        raise HTTPException(status_code=400, detail=f"Unsupported mode. Use one of: {', '.join(sorted(allowed_modes))}")

    query = (req.query or "").strip()
    if not query and req.messages:
        for message in reversed(req.messages):
            if message.get("role") == "user" and isinstance(message.get("content"), str):
                query = message["content"].strip()
                break
    if not query and mode != "chat":
        raise HTTPException(status_code=400, detail="query is required for RAG and fine-tune modes.")

    messages = req.messages or ([{"role": "user", "content": query}] if query else [])
    if not messages:
        raise HTTPException(status_code=400, detail="Provide either query or messages.")

    sources: List[Dict[str, Any]] = []
    rag_meta: Optional[Dict[str, Any]] = None
    fine_tune_meta: Optional[Dict[str, str]] = None

    if mode == "chat":
        final_messages = messages
    elif mode == "fine_tune":
        if not req.tuning_id:
            raise HTTPException(status_code=400, detail="tuning_id is required for fine_tune mode.")
        fine_tune_meta = {"tuning_id": req.tuning_id, "base_model": req.base_model}
        system_prompt = f"Fine-tuned expert profile (ID: {req.tuning_id}). Base: {req.base_model}."
        final_messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]
    else:
        top_k = req.top_k or RAG_TOP_K
        context, sources = _rag_context_for_query(query, top_k=top_k)
        rag_meta = {"top_k": top_k, "store_path": RAG_STORE_PATH}
        if mode == "rag_fine_tune":
            if not req.tuning_id:
                raise HTTPException(status_code=400, detail="tuning_id is required for rag_fine_tune mode.")
            fine_tune_meta = {"tuning_id": req.tuning_id, "base_model": req.base_model}
            system_prompt = (
                f"Fine-tuned expert profile (ID: {req.tuning_id}). Base: {req.base_model}. "
                "You are also a retrieval-augmented assistant. Answer using the provided context. "
                "If context is insufficient, clearly say what is missing. Cite source chunk ids in brackets."
            )
        else:
            system_prompt = (
                "You are a retrieval-augmented assistant. Answer using the provided context. "
                "If context is insufficient, clearly say what is missing. Cite source chunk ids in brackets."
            )
        user_prompt = (
            "Context:\n"
            + context
            + f"\n\nQuestion: {query}\n\n"
            + "Answer in Vietnamese unless user asks otherwise."
        )
        final_messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    response, meta = await _chat_with_failover(
        messages=final_messages,
        model_override=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        top_p=None,
        task=req.task,
    )
    payload = response.model_dump()
    payload["mode"] = mode
    payload["reply"] = response.choices[0].message.content
    payload["router"] = meta
    if rag_meta is not None:
        payload["rag"] = rag_meta
        if req.include_sources:
            payload["sources"] = sources
    if fine_tune_meta is not None:
        payload["fine_tune"] = fine_tune_meta
    return JSONResponse(content=payload, headers={"x-ai-provider": meta["provider"], "x-ai-model": meta["model"]})


@app.post("/v1/rag/ingest")
async def rag_ingest(req: RAGIngestRequest):
    result = rag_store.ingest(req.documents)
    return {
        "status": "ok",
        "store_path": RAG_STORE_PATH,
        "ingested_documents": result["documents"],
        "ingested_chunks": result["chunks"],
        "total_chunks": len(rag_store.chunks),
    }


@app.post("/v1/rag/search")
async def rag_search(req: RAGSearchRequest):
    top_k = req.top_k or RAG_TOP_K
    hits = rag_store.search(req.query, top_k=top_k)
    return {
        "query": req.query,
        "top_k": top_k,
        "hits": hits,
    }


@app.post("/v1/rag/chat")
async def rag_chat(req: RAGChatRequest):
    top_k = req.top_k or RAG_TOP_K
    hits = rag_store.search(req.query, top_k=top_k)
    if not hits:
        raise HTTPException(status_code=400, detail="RAG store is empty or no relevant context. Call /v1/rag/ingest first.")

    context_lines = []
    sources = []
    for hit in hits:
        source_id = hit["chunk_id"]
        context_lines.append(f"[{source_id}] {hit['text']}")
        sources.append(
            {
                "chunk_id": hit["chunk_id"],
                "doc_id": hit["doc_id"],
                "score": hit["score"],
                "metadata": hit.get("metadata", {}),
            }
        )

    system_prompt = (
        "You are a retrieval-augmented assistant. Answer using the provided context. "
        "If context is insufficient, clearly say what is missing. Cite source chunk ids in brackets."
    )
    user_prompt = (
        "Context:\n"
        + "\n\n".join(context_lines)
        + f"\n\nQuestion: {req.query}\n\n"
        + "Answer in Vietnamese unless user asks otherwise."
    )
    response, meta = await _chat_with_failover(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        model_override=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        top_p=None,
        task="general"
    )
    payload = response.model_dump()
    payload["router"] = meta
    if req.include_sources:
        payload["sources"] = sources
    payload["rag"] = {"top_k": top_k, "store_path": RAG_STORE_PATH}
    return JSONResponse(content=payload, headers={"x-ai-provider": meta["provider"], "x-ai-model": meta["model"]})


@app.get("/cinematic", response_class=HTMLResponse)
async def cinematic_ui():
    """Trang giao diện Hub AI Đa nhiệm cho Doanh nghiệp."""
    providers = _active_providers()
    chain_view = " -> ".join([p.name for p in providers]) if providers else "No provider configured"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enterprise AI Hub | Multi-Task Gateway</title>
        <link rel="icon" href="/favicon.ico">
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Playfair+Display:ital,wght@1,900&family=JetBrains+Mono&display=swap" rel="stylesheet">
        <style>
            :root {{ --primary: #0D0D12; --accent: #7B61FF; --background: #FAF8F5; }}
            body {{ background-color: var(--primary); color: white; font-family: 'Inter', sans-serif; overflow: hidden; }}
            .glass {{ background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 2rem; }}
            .module-card {{ transition: all 0.4s ease; cursor: pointer; border: 1px solid rgba(255, 255, 255, 0.05); }}
            .module-card:hover {{ background: rgba(123, 97, 255, 0.1); border-color: var(--accent); transform: translateY(-5px); }}
            .module-card.active {{ background: var(--accent); color: white; }}
            .chat-area {{ height: 60vh; scrollbar-width: none; }}
            .status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 10px #10b981; }}
        </style>
    </head>
    <body class="flex h-screen">
        <!-- Sidebar Modules -->
        <aside class="w-80 border-r border-white/5 p-8 flex flex-col gap-6">
            <div class="flex items-center gap-3 mb-8">
                <div class="status-dot"></div>
                <span class="font-black text-xs tracking-widest uppercase">Enterprise AI Hub</span>
            </div>
            
            <div id="task-general" class="module-card active p-6 glass">
                <h3 class="font-bold text-sm mb-1">Standard Chat</h3>
                <p class="text-[10px] opacity-50">Llama 3.3 / GPT-4o Mini</p>
            </div>
            <div id="task-code" class="module-card p-6 glass">
                <h3 class="font-bold text-sm mb-1">Dev Ops & Code</h3>
                <p class="text-[10px] opacity-50">DeepSeek R1 / Qwen 2.5</p>
            </div>
            <div id="task-vision" class="module-card p-6 glass">
                <h3 class="font-bold text-sm mb-1">Vision & OCR</h3>
                <p class="text-[10px] opacity-50">Image Analysis Protocol</p>
            </div>
            <div id="task-image" class="module-card p-6 glass">
                <h3 class="font-bold text-sm mb-1">Creative Engine</h3>
                <p class="text-[10px] opacity-50">Flux / SDXL Generation</p>
            </div>
            <div id="task-gemma" class="module-card p-6 glass border-emerald-500/30">
                <h3 class="font-bold text-sm mb-1 text-emerald-400">Gemma Explorer</h3>
                <p class="text-[10px] opacity-50">Google Gemma 2 Protocol</p>
            </div>
            
            <div class="mt-auto p-6 glass bg-white/5">
                <span class="block text-[10px] font-bold opacity-30 uppercase mb-2">Protocol Status</span>
                <span class="text-[10px] text-emerald-400 font-mono uppercase">{ROUTING_MODE} Mode Active</span>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 p-12 flex flex-col">
            <header class="flex justify-between items-center mb-12">
                <div>
                    <h1 class="text-4xl font-black tracking-tighter" id="title-display">Standard Chat</h1>
                    <p class="text-white/40 text-sm mt-2" id="desc-display">General purpose intelligence for daily tasks.</p>
                </div>
                <div class="flex gap-4">
                    <button class="px-6 py-2 rounded-full border border-white/10 text-[10px] font-bold uppercase tracking-widest">Settings</button>
                    <button class="px-6 py-2 rounded-full bg-[#7B61FF] text-white text-[10px] font-black uppercase tracking-widest">API Docs</button>
                </div>
            </header>

            <div class="flex-1 glass p-8 flex flex-col relative overflow-hidden">
                <div id="chat-box" class="chat-area overflow-y-auto space-y-6 font-mono text-[13px] mb-8 pr-4">
                    <div class="p-4 bg-white/5 rounded-xl border border-white/5 italic text-white/40">
                        System initialized. Gateway routing to {chain_view.split(' -> ')[0]}...
                    </div>
                </div>

                <div class="relative mt-auto">
                    <input id="userInput" type="text" placeholder="Type your request or drop code here..." 
                        class="w-full bg-black/40 border border-white/10 rounded-2xl px-8 py-5 outline-none focus:border-[#7B61FF] transition-all font-mono text-white">
                    <button id="executeBtn" class="absolute right-3 top-1/2 -translate-y-1/2 bg-[#7B61FF] text-white px-8 py-3 rounded-xl font-bold text-xs hover:scale-105 transition active:scale-95">EXECUTE</button>
                </div>
            </div>
        </main>

        <script>
            let currentTask = "general";
            const chatBox = document.getElementById("chat-box");
            const input = document.getElementById("userInput");
            const executeBtn = document.getElementById("executeBtn");
            
            const taskInfo = {{
                general: {{ title: "Standard Chat", desc: "General purpose intelligence for daily tasks." }},
                code: {{ title: "Dev Ops & Code", desc: "Advanced reasoning for debugging and architecture." }},
                vision: {{ title: "Vision & OCR", desc: "Analyze images, read documents, and identify objects." }},
                image: {{ title: "Creative Engine", desc: "Generate high-fidelity visual assets from text." }},
                gemma: {{ title: "Gemma Explorer", desc: "Experience Google's lightweight yet powerful Gemma 2 model." }}
            }};

            function addLog(text, type = "user") {{
                const div = document.createElement("div");
                const inner = document.createElement("div");
                if (type === "status") {{
                    div.className = "text-[#7B61FF] text-[10px] font-bold uppercase tracking-widest py-2 border-y border-white/5";
                    div.innerText = ">> " + text;
                }} else if (type === "user") {{
                    div.className = "flex flex-col items-end w-full mb-4";
                    inner.className = "bg-white/10 p-4 rounded-2xl rounded-tr-none max-w-[80%] break-words";
                    inner.textContent = text;
                }} else {{
                    div.className = "flex flex-col items-start w-full mb-4";
                    inner.className = "bg-[#7B61FF]/20 border border-[#7B61FF]/30 p-4 rounded-2xl rounded-tl-none max-w-[80%] break-words";
                    inner.textContent = text;
                }}
                div.appendChild(inner);
                chatBox.appendChild(div);
                chatBox.scrollTop = chatBox.scrollHeight;
                return inner;
            }}

            function setTask(task) {{
                currentTask = task;
                document.querySelectorAll(".module-card").forEach(c => c.classList.remove("active"));
                const card = document.getElementById("task-" + task);
                if (card) card.classList.add("active");
                document.getElementById("title-display").innerText = taskInfo[task].title;
                document.getElementById("desc-display").innerText = taskInfo[task].desc;
                addLog(`System recalibrated to task: ${{task.toUpperCase()}}`, "status");
            }}

            async function execute() {{
                const text = input.value.trim();
                if (!text) return;

                console.log("Executing:", text);
                addLog(text, "user");
                input.value = "";
                
                const responseLog = addLog("Processing...", "ai");
                
                try {{
                    const res = await fetch("/v1/chat/completions", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ 
                            messages: [{{ role: "user", content: text }}],
                            model: currentTask === "gemma" ? "gemma" : undefined,
                            task: currentTask 
                        }})
                    }});
                    
                    if (!res.ok) throw new Error("Gateway Error " + res.status);

                    const data = await res.json();
                    responseLog.innerText = data.choices[0].message.content;
                }} catch (e) {{
                    responseLog.innerText = "ERROR: " + e.message;
                    responseLog.style.color = "#ff4444";
                }}
            }}

            // Attach listeners
            if (executeBtn) executeBtn.addEventListener("click", execute);
            if (input) input.addEventListener("keydown", (e) => {{ 
                if(e.key === "Enter" && !e.shiftKey) {{ 
                    e.preventDefault(); 
                    execute(); 
                }} 
            }});
            
            Object.keys(taskInfo).forEach(task => {{
                const el = document.getElementById("task-" + task);
                if (el) el.addEventListener("click", () => setTask(task));
            }});

            console.log("Dashboard Initialized");
        </script>
    </body>
    </html>
    """
    return html_content


@app.post("/v1/fine_tune/chat")
async def fine_tune_chat(req: FineTuneChatRequest):
    system_prompt = f"Fine-tuned expert (ID: {req.tuning_id}). Base: {req.base_model}."
    response, meta = await _chat_with_failover(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": req.prompt}],
        model_override=None,
        temperature=req.temperature,
    )
    return {"status": "success", "reply": response.choices[0].message.content, "router": meta}


@app.post("/v1/rag/fine_tune/chat")
async def rag_fine_tune_chat(req: RAGFineTuneChatRequest):
    top_k = req.top_k or RAG_TOP_K
    hits = rag_store.search(req.query, top_k=top_k)
    if not hits:
        raise HTTPException(status_code=400, detail="RAG store is empty or no relevant context. Call /v1/rag/ingest first.")

    context_lines = []
    sources = []
    for hit in hits:
        source_id = hit["chunk_id"]
        context_lines.append(f"[{source_id}] {hit['text']}")
        sources.append(
            {
                "chunk_id": hit["chunk_id"],
                "doc_id": hit["doc_id"],
                "score": hit["score"],
                "metadata": hit.get("metadata", {}),
            }
        )

    system_prompt = (
        f"Fine-tuned expert profile (ID: {req.tuning_id}). Base: {req.base_model}. "
        "You are also a retrieval-augmented assistant. Answer using the provided context. "
        "If context is insufficient, clearly say what is missing. Cite source chunk ids in brackets."
    )
    user_prompt = (
        "Context:\n"
        + "\n\n".join(context_lines)
        + f"\n\nQuestion: {req.query}\n\n"
        + "Answer in Vietnamese unless user asks otherwise."
    )
    response, meta = await _chat_with_failover(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        model_override=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        top_p=None,
        task="general",
    )
    payload = response.model_dump()
    payload["router"] = meta
    if req.include_sources:
        payload["sources"] = sources
    payload["rag"] = {"top_k": top_k, "store_path": RAG_STORE_PATH}
    payload["fine_tune"] = {"tuning_id": req.tuning_id, "base_model": req.base_model}
    return JSONResponse(content=payload, headers={"x-ai-provider": meta["provider"], "x-ai-model": meta["model"]})


@app.get("/health")
async def health():
    providers = _active_providers()
    return {
        "status": "ok",
        "app": APP_NAME,
        "routing_mode": ROUTING_MODE,
        "adaptive_routing": ADAPTIVE_ROUTING,
        "rag_store_path": RAG_STORE_PATH,
        "rag_total_chunks": len(rag_store.chunks),
        "provider_failure_threshold": PROVIDER_FAILURE_THRESHOLD,
        "provider_cooldown_s": PROVIDER_COOLDOWN_S,
        "providers": [
            {
                "key": p.key,
                "name": p.name,
                "base_url": _provider_base(p),
                "model": _provider_model(p),
            }
            for p in providers
        ],
    }


@app.get("/providers")
async def providers():
    active_provider_keys = {p.key for p in _active_providers()}
    configured = []
    for key, p in PROVIDER_REGISTRY.items():
        configured.append(
            {
                "key": key,
                "name": p.name,
                "enabled": key in active_provider_keys,
                "base_url": _provider_base(p),
                "model": _provider_model(p),
                "api_key_env": p.api_key_env,
            }
        )
    return {
        "routing_chain": PROVIDER_CHAIN,
        "routing_mode": ROUTING_MODE,
        "adaptive_routing": ADAPTIVE_ROUTING,
        "model_aliases": _alias_map(),
        "providers": configured,
    }


@app.get("/router/models")
async def router_models():
    return {"model_aliases": _alias_map()}


@app.get("/router/state")
async def router_state():
    now = time.time()
    snapshot: Dict[str, Dict[str, Any]] = {}
    for key, state in _provider_state.items():
        remaining = max(0.0, float(state.get("cooldown_until", 0.0)) - now)
        snapshot[key] = {
            "attempts": int(state.get("attempts", 0)),
            "successes": int(state.get("successes", 0)),
            "failures_total": int(state.get("failures_total", 0)),
            "error_rate": round(
                (float(state.get("failures_total", 0)) / max(float(state.get("attempts", 1)), 1.0)),
                4,
            ),
            "last_latency_ms": round(float(state.get("last_latency_ms", 0.0)), 2),
            "latency_ewma_ms": round(float(state.get("latency_ewma_ms", 0.0)), 2),
            "cooldown_remaining_s": round(remaining, 2),
            "last_error": state.get("last_error", ""),
            "last_attempt_at": state.get("last_attempt_at", 0.0),
            "effective_weight": round(_effective_provider_weight(key, _provider_weights().get(key, 1)), 3),
        }
    return {
        "routing_mode": ROUTING_MODE,
        "adaptive_routing": ADAPTIVE_ROUTING,
        "weights": _provider_weights(),
        "state": snapshot,
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    lines: List[str] = [
        "# HELP ai_gateway_provider_attempts_total Total attempts per provider",
        "# TYPE ai_gateway_provider_attempts_total counter",
        "# HELP ai_gateway_provider_success_total Total successes per provider",
        "# TYPE ai_gateway_provider_success_total counter",
        "# HELP ai_gateway_provider_failures_total Total failures per provider",
        "# TYPE ai_gateway_provider_failures_total counter",
        "# HELP ai_gateway_provider_latency_ewma_ms EWMA latency milliseconds per provider",
        "# TYPE ai_gateway_provider_latency_ewma_ms gauge",
        "# HELP ai_gateway_provider_cooldown_remaining_seconds Remaining cooldown in seconds",
        "# TYPE ai_gateway_provider_cooldown_remaining_seconds gauge",
    ]
    now = time.time()
    base_weights = _provider_weights()
    for key in PROVIDER_REGISTRY:
        state = _ensure_provider_state(key)
        cooldown_remaining = max(0.0, float(state.get("cooldown_until", 0.0)) - now)
        lines.append(f'ai_gateway_provider_attempts_total{{provider="{key}"}} {int(state.get("attempts", 0))}')
        lines.append(f'ai_gateway_provider_success_total{{provider="{key}"}} {int(state.get("successes", 0))}')
        lines.append(f'ai_gateway_provider_failures_total{{provider="{key}"}} {int(state.get("failures_total", 0))}')
        lines.append(f'ai_gateway_provider_latency_ewma_ms{{provider="{key}"}} {float(state.get("latency_ewma_ms", 0.0)):.4f}')
        lines.append(
            f'ai_gateway_provider_cooldown_remaining_seconds{{provider="{key}"}} {cooldown_remaining:.4f}'
        )
        lines.append(
            f'ai_gateway_provider_effective_weight{{provider="{key}"}} '
            f'{_effective_provider_weight(key, base_weights.get(key, 1)):.4f}'
        )
    return "\n".join(lines) + "\n"

if __name__ == "__main__":
    uvicorn.run("simple_ai_gateway:app", host="0.0.0.0", port=8000, reload=True)
