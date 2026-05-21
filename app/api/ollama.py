"""
Ollama-compatible endpoint — /api/generate & /api/chat

Allows any system that calls Ollama to drop in this gateway URL
with zero code changes. Just replace the base URL.

Supported formats:
  POST /api/generate  {"model":"gemma4:latest","prompt":"..."}
  POST /api/chat      {"model":"gemma4:latest","messages":[...]}
  GET  /api/tags      → list available models
"""

from typing import Optional, List, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import json
import time

from app.dependencies import get_router_service
from app.services.router import RouterService
from app.core.providers import PROVIDER_REGISTRY

router = APIRouter()


# ── Request models ─────────────────────────────────────────────────────────

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


# ── Helpers ────────────────────────────────────────────────────────────────

def _ollama_response(model: str, content: str, done: bool = True) -> dict:
    return {
        "model": model,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "response": content,
        "done": done,
        "done_reason": "stop" if done else None,
        "context": [],
        "total_duration": 0,
        "eval_count": len(content.split()),
    }


def _ollama_chat_response(model: str, content: str, done: bool = True) -> dict:
    return {
        "model": model,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "message": {"role": "assistant", "content": content},
        "done": done,
        "done_reason": "stop" if done else None,
    }


# ── GET /api/tags — list models ────────────────────────────────────────────

@router.get("/tags")
async def list_models():
    """Ollama-compatible model list."""
    models = []
    for key, provider in PROVIDER_REGISTRY.items():
        models.append({
            "name": provider.default_model,
            "model": provider.default_model,
            "modified_at": "2025-01-01T00:00:00Z",
            "size": 0,
            "digest": key,
            "details": {
                "family": key,
                "parameter_size": "unknown",
                "quantization_level": "unknown",
            }
        })
    return {"models": models}


# ── POST /api/generate — Ollama generate format ────────────────────────────

@router.post("/generate")
async def ollama_generate(
    req: OllamaGenerateRequest,
    router_svc: RouterService = Depends(get_router_service),
):
    """
    Drop-in replacement for Ollama /api/generate.
    Routes through the gateway's failover system.
    """
    messages = []
    if req.system:
        messages.append({"role": "system", "content": req.system})
    messages.append({"role": "user", "content": req.prompt})

    options = req.options or {}
    temperature = options.get("temperature", 0.7)
    max_tokens = options.get("num_predict", options.get("max_tokens", None))

    if req.stream:
        async def event_stream() -> AsyncGenerator[str, None]:
            full = ""
            try:
                async for chunk in router_svc.chat_stream_with_failover(
                    messages=messages,
                    model_override=req.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    user_tier="free",
                ):
                    if "error" in chunk:
                        yield json.dumps({"error": chunk.get("message", "")}) + "\n"
                        return
                    if "info" in chunk:
                        continue
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = getattr(choices[0], "delta", None)
                        token = getattr(delta, "content", None) if delta else None
                        finish = getattr(choices[0], "finish_reason", None)
                        if token:
                            full += token
                            yield json.dumps(_ollama_response(req.model, token, done=False)) + "\n"
                        if finish == "stop":
                            yield json.dumps(_ollama_response(req.model, "", done=True)) + "\n"
                            return
            except Exception as e:
                yield json.dumps({"error": str(e)}) + "\n"

        return StreamingResponse(event_stream(), media_type="application/x-ndjson")

    # Non-streaming
    response, meta = await router_svc.chat_with_failover(
        messages=messages,
        model_override=req.model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content or ""
    return _ollama_response(req.model, content)


# ── POST /api/chat — Ollama chat format ────────────────────────────────────

@router.post("/chat")
async def ollama_chat(
    req: OllamaChatRequest,
    router_svc: RouterService = Depends(get_router_service),
):
    """
    Drop-in replacement for Ollama /api/chat.
    Routes through the gateway's failover system.
    """
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    options = req.options or {}
    temperature = options.get("temperature", 0.7)
    max_tokens = options.get("num_predict", options.get("max_tokens", None))

    if req.stream:
        async def event_stream() -> AsyncGenerator[str, None]:
            try:
                async for chunk in router_svc.chat_stream_with_failover(
                    messages=messages,
                    model_override=req.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    user_tier="free",
                ):
                    if "error" in chunk:
                        yield json.dumps({"error": chunk.get("message", "")}) + "\n"
                        return
                    if "info" in chunk:
                        continue
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = getattr(choices[0], "delta", None)
                        token = getattr(delta, "content", None) if delta else None
                        finish = getattr(choices[0], "finish_reason", None)
                        if token:
                            yield json.dumps(_ollama_chat_response(req.model, token, done=False)) + "\n"
                        if finish == "stop":
                            yield json.dumps(_ollama_chat_response(req.model, "", done=True)) + "\n"
                            return
            except Exception as e:
                yield json.dumps({"error": str(e)}) + "\n"

        return StreamingResponse(event_stream(), media_type="application/x-ndjson")

    # Non-streaming
    response, meta = await router_svc.chat_with_failover(
        messages=messages,
        model_override=req.model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content or ""
    return _ollama_chat_response(req.model, content)
