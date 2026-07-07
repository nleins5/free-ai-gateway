"""
Ollama-compatible endpoint — /api/generate & /api/chat & /api/tags

Drop-in replacement for any system calling an Ollama server.
Just change the base URL, zero other code changes needed.
Rate-limited to prevent abuse on public endpoints.
"""

from typing import Optional, List, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import json
import time

from app.dependencies import get_router_service
from app.services.router import RouterService
from app.core.providers import PROVIDER_REGISTRY
from app.core.rate_limit import rate_limiter

router = APIRouter()


async def _check_rate_limit(request: Request):
    """Dependency: enforce rate limiting by client IP."""
    client_ip = request.client.host if request.client else "unknown"
    allowed, info = rate_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({info['limit']}/min). Retry after {info['retry_after']}s.",
            headers={"Retry-After": str(info["retry_after"])},
        )


# ── Request models ─────────────────────────────────────────────

class OllamaGenerateRequest(BaseModel):
    model: str = "gemma4:latest"
    prompt: str
    system: Optional[str] = None
    stream: Optional[bool] = False
    options: Optional[Dict[str, Any]] = None


class OllamaChatMessage(BaseModel):
    role: str
    content: str


class OllamaChatRequest(BaseModel):
    model: str = "gemma4:latest"
    messages: List[OllamaChatMessage]
    stream: Optional[bool] = False
    options: Optional[Dict[str, Any]] = None


# ── Response helpers ───────────────────────────────────────────

def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _gen_resp(model: str, text: str, done: bool = True) -> dict:
    return {"model": model, "created_at": _ts(), "response": text, "done": done}


def _chat_resp(model: str, text: str, done: bool = True) -> dict:
    return {
        "model": model,
        "created_at": _ts(),
        "message": {"role": "assistant", "content": text},
        "done": done,
    }


# ── GET /api/tags ──────────────────────────────────────────────

@router.get("/tags")
async def list_models():
    models = [
        {
            "name": p.default_model,
            "model": p.default_model,
            "modified_at": "2025-01-01T00:00:00Z",
            "size": 0,
            "digest": k,
            "details": {"family": k, "parameter_size": "unknown"},
        }
        for k, p in PROVIDER_REGISTRY.items()
    ]
    return {"models": models}


# ── Shared stream helper ───────────────────────────────────────

async def _run_stream(router_svc, messages, temperature, max_tokens, fmt):
    """
    Consume gateway stream chunks and yield Ollama-format NDJSON.
    fmt: "generate" | "chat"
    """
    model_used = "gateway"
    async for chunk in router_svc.chat_stream_with_failover(
        messages=messages,
        task="general",
        user_tier="free",
        temperature=temperature,
        max_tokens=max_tokens,
    ):
        # Control dict — error / info / done signal
        if "error" in chunk:
            yield json.dumps({"error": chunk.get("message", "error")}) + "\n"
            return
        if "info" in chunk:
            continue

        # Token chunk: {"choices": [...], "provider": ..., "model": ...}
        choices = chunk.get("choices", [])
        if not choices:
            continue
        model_used = chunk.get("model", model_used)
        try:
            delta = choices[0].delta
            token = delta.content or ""
            finish = choices[0].finish_reason
        except Exception:
            continue

        if token:
            if fmt == "generate":
                yield json.dumps(_gen_resp(model_used, token, done=False)) + "\n"
            else:
                yield json.dumps(_chat_resp(model_used, token, done=False)) + "\n"

        if finish == "stop":
            if fmt == "generate":
                yield json.dumps(_gen_resp(model_used, "", done=True)) + "\n"
            else:
                yield json.dumps(_chat_resp(model_used, "", done=True)) + "\n"
            return


# ── POST /api/generate ─────────────────────────────────────────

@router.post("/generate", dependencies=[Depends(_check_rate_limit)])
async def ollama_generate(
    req: OllamaGenerateRequest,
    router_svc: RouterService = Depends(get_router_service),
):
    messages = []
    if req.system:
        messages.append({"role": "system", "content": req.system})
    messages.append({"role": "user", "content": req.prompt})

    opts = req.options or {}
    temperature = float(opts.get("temperature", 0.7))
    max_tokens = opts.get("num_predict") or opts.get("max_tokens") or None

    if req.stream:
        return StreamingResponse(
            _run_stream(router_svc, messages, temperature, max_tokens, "generate"),
            media_type="application/x-ndjson",
        )

    # Non-streaming — collect via fake stream
    full = ""
    model_used = req.model
    async for chunk in router_svc.chat_stream_with_failover(
        messages=messages,
        task="general",
        user_tier="free",
        temperature=temperature,
        max_tokens=max_tokens,
    ):
        if "error" in chunk:
            return {"error": chunk.get("message", "error"), "done": True}
        if "info" in chunk:
            continue
        choices = chunk.get("choices", [])
        if choices:
            model_used = chunk.get("model", model_used)
            try:
                token = choices[0].delta.content or ""
                full += token
            except Exception:
                pass

    return _gen_resp(model_used, full, done=True)


# ── POST /api/chat ─────────────────────────────────────────────

@router.post("/chat", dependencies=[Depends(_check_rate_limit)])
async def ollama_chat(
    req: OllamaChatRequest,
    router_svc: RouterService = Depends(get_router_service),
):
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    opts = req.options or {}
    temperature = float(opts.get("temperature", 0.7))
    max_tokens = opts.get("num_predict") or opts.get("max_tokens") or None

    if req.stream:
        return StreamingResponse(
            _run_stream(router_svc, messages, temperature, max_tokens, "chat"),
            media_type="application/x-ndjson",
        )

    full = ""
    model_used = req.model
    async for chunk in router_svc.chat_stream_with_failover(
        messages=messages,
        task="general",
        user_tier="free",
        temperature=temperature,
        max_tokens=max_tokens,
    ):
        if "error" in chunk:
            return {"error": chunk.get("message", "error"), "done": True}
        if "info" in chunk:
            continue
        choices = chunk.get("choices", [])
        if choices:
            model_used = chunk.get("model", model_used)
            try:
                token = choices[0].delta.content or ""
                full += token
            except Exception:
                pass

    return _chat_resp(model_used, full, done=True)
