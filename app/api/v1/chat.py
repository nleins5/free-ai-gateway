from typing import Optional, AsyncGenerator
from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import re
import json as json_lib

from app.models import ChatRequest, UnifiedAIChatRequest
from app.dependencies import get_router_service, get_rag_service, get_db_optional
from app.services.router import RouterService
from app.services.rag import RAGService
from app.services.search import perform_web_search
from app.database import get_db
from app.db_models import RequestLog, ChatMessage, Conversation, User
from app.core.prompts import get_task_system_prompt
from sqlalchemy import select

router = APIRouter()


async def _resolve_user(api_key: Optional[str], db: Optional[AsyncSession]):
    if not api_key or not db:
        return None
    try:
        result = await db.execute(select(User).where(User.api_key == api_key, User.is_active))
        return result.scalar_one_or_none()
    except Exception:
        return None


async def _log_request(db: Optional[AsyncSession], user_id, provider, model, tokens_in, tokens_out, latency_ms, cost_usd, task, failover_trace=None, status="success", error_msg=None):
    if not db:
        return  # DB unavailable — skip logging silently
    import json
    log = RequestLog(
        user_id=user_id,
        provider=provider,
        model=model,
        failover_trace=json.dumps(failover_trace) if failover_trace else None,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        task_type=task or "general",
        status=status,
        error_msg=error_msg,
    )
    db.add(log)


@router.post("/completions")
async def chat_completions(
    req: ChatRequest,
    router_svc: RouterService = Depends(get_router_service),
    db: AsyncSession = Depends(get_db),
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """OpenAI-compatible chat completions endpoint."""
    user = await _resolve_user(x_api_key, db)

    response, meta = await router_svc.chat_with_failover(
        messages=[m.model_dump() for m in req.messages],
        user_id=req.user_id,
        model_override=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens
    )
    
    # Extract usage
    usage = getattr(response, "usage", None)
    t_in = getattr(usage, "prompt_tokens", 0) if usage else 0
    t_out = getattr(usage, "completion_tokens", 0) if usage else 0
    
    # Log to database
    from app.config import COST_PER_1M
    rates = COST_PER_1M.get(meta["provider"], (0.0, 0.0))
    cost = (t_in * rates[0] + t_out * rates[1]) / 1_000_000
    
    await _log_request(
        db, user_id=user.id if user else None,
        provider=meta["provider"], model=meta["model"],
        tokens_in=t_in, tokens_out=t_out,
        latency_ms=meta["latency_ms"], cost_usd=cost,
        task="general",
        failover_trace=meta.get("failover_trace"),
    )

    # Wrap response with gateway metadata
    res_dict = response.model_dump()
    res_dict["x_gateway"] = meta
    return res_dict


@router.post("/unified")
async def unified_chat(
    req: UnifiedAIChatRequest,
    router_svc: RouterService = Depends(get_router_service),
    rag_svc: RAGService = Depends(get_rag_service),
    db: Optional[AsyncSession] = Depends(get_db_optional),
    x_api_key: str = Header(None, alias="X-API-Key"),
    x_conversation_id: str = Header(None, alias="X-Conversation-Id"),
):
    """
    High-level unified chat endpoint.
    Handles RAG integration and task-based routing.
    Gracefully degrades when DB is unavailable.
    """
    user = await _resolve_user(x_api_key, db)
    
    # Auto-register guest users from frontend if they don't exist
    if not user and req.user_id and db:
        result = await db.execute(select(User).where(User.id == req.user_id))
        user = result.scalar_one_or_none()
        if not user:
            try:
                user = User(
                    id=req.user_id,
                    username=f"guest_{req.user_id}",
                    api_key=f"sk_guest_{req.user_id}",
                    role="guest"
                )
                db.add(user)
                await db.flush()
            except Exception:
                await db.rollback()
                # Race condition: another request created this user already
                result = await db.execute(select(User).where(User.id == req.user_id))
                user = result.scalar_one_or_none()
    messages = []
    
    # 1. Handle Web Search (Research Mode) if requested
    if req.use_rag:
        search_results = await perform_web_search(req.query)
        if search_results:
            context_str = ""
            for idx, res in enumerate(search_results):
                context_str += f"[{idx+1}] {res.get('title')}\nURL: {res.get('href')}\nSnippet: {res.get('body')}\n\n"
            
            system_prompt = req.system_prompt or "You are a helpful research assistant. Use the following web search results to answer the user's question accurately. Always cite your sources using the [Number] format in your response."
            messages.append({"role": "system", "content": f"{system_prompt}\n\n--- Web Search Results ---\n{context_str}"})
        else:
            system_prompt = req.system_prompt or "You are a helpful assistant."
            messages.append({"role": "system", "content": system_prompt})
    else:
        system_prompt = req.system_prompt or get_task_system_prompt(req.task)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

    # Append conversation history from request
    if req.history:
        for msg in req.history:
            messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": req.query})

    # 2. Call router with task-based failover
    response, meta = await router_svc.chat_with_failover(
        messages=messages,
        user_id=req.user_id,
        model_override=req.model_override,
        task=req.task
    )

    raw_answer = response.choices[0].message.content or ""
    # Strip DeepSeek-R1 <think>...</think> reasoning blocks
    answer = re.sub(r'<think>[\s\S]*?</think>\s*', '', raw_answer).strip() or raw_answer
    usage = response.usage

    # 3. Log to database (skip if DB unavailable)
    t_in = getattr(usage, "prompt_tokens", 0) if usage else 0
    t_out = getattr(usage, "completion_tokens", 0) if usage else 0
    from app.config import COST_PER_1M
    rates = COST_PER_1M.get(meta["provider"], (0.0, 0.0))
    cost = (t_in * rates[0] + t_out * rates[1]) / 1_000_000

    await _log_request(
        db, user_id=user.id if user else None,
        provider=meta["provider"], model=meta["model"],
        tokens_in=t_in, tokens_out=t_out,
        latency_ms=meta["latency_ms"], cost_usd=cost,
        task=req.task or "general",
        failover_trace=meta.get("failover_trace"),
    )

    # 4. Save to conversation if provided (skip if DB unavailable)
    if x_conversation_id and db:
        try:
            conv_result = await db.execute(
                select(Conversation).where(Conversation.id == x_conversation_id)
            )
            conv = conv_result.scalar_one_or_none()
            if conv:
                # Save user message
                db.add(ChatMessage(
                    conversation_id=conv.id,
                    role="user",
                    content=req.query,
                ))
                # Save assistant response
                import json
                db.add(ChatMessage(
                    conversation_id=conv.id,
                    role="assistant",
                    content=answer,
                    provider=meta["provider"],
                    model=meta["model"],
                    failover_trace=json.dumps(meta.get("failover_trace")) if meta.get("failover_trace") else None
                ))
        except Exception:
            pass  # DB issue — don't crash the response

    return {
        "answer": answer,
        "metadata": meta,
        "usage": usage.model_dump() if usage else None
    }


@router.post("/unified/stream")
async def unified_chat_stream(
    req: UnifiedAIChatRequest,
    router_svc: RouterService = Depends(get_router_service),
    rag_svc: RAGService = Depends(get_rag_service),
    db: Optional[AsyncSession] = Depends(get_db_optional),
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """
    SSE streaming version of unified_chat.
    Streams tokens to the client in real-time — no waiting for full response.
    """
    # Build messages (same logic as unified_chat)
    messages = []

    if req.use_rag:
        search_results = await perform_web_search(req.query)
        if search_results:
            context_str = ""
            for idx, res in enumerate(search_results):
                context_str += f"[{idx+1}] {res.get('title')}\nURL: {res.get('href')}\nSnippet: {res.get('body')}\n\n"
            system_prompt = req.system_prompt or "You are a helpful research assistant. Use the following web search results to answer the user's question accurately. Always cite your sources using the [Number] format in your response."
            messages.append({"role": "system", "content": f"{system_prompt}\n\n--- Web Search Results ---\n{context_str}"})
        else:
            system_prompt = req.system_prompt or "You are a helpful assistant."
            messages.append({"role": "system", "content": system_prompt})
    else:
        system_prompt = req.system_prompt or get_task_system_prompt(req.task)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

    if req.history:
        for msg in req.history:
            messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": req.query})

    async def event_stream() -> AsyncGenerator[str, None]:
        import time as _time
        start_ts = _time.time()
        final_provider = ''
        final_model = ''
        try:
            async for chunk in router_svc.chat_stream_with_failover(
                messages=messages,
                user_id=req.user_id,
                model_override=req.model_override,
                task=req.task,
                user_tier=req.user_tier or "guest",
                guest_prompt_count=req.guest_prompt_count or 0,
            ):
                # Error from router
                if "error" in chunk:
                    yield f"data: {json_lib.dumps({'error': chunk['error'], 'message': chunk.get('message', '')})}\n\n"
                    return

                # Failover info notification
                if "info" in chunk:
                    yield f"data: {json_lib.dumps({'info': chunk['info'], 'message': chunk.get('message', '')})}\n\n"
                    continue

                # Token chunk
                choices = chunk.get("choices", [])
                if choices:
                    delta = getattr(choices[0], "delta", None)
                    content = getattr(delta, "content", None) if delta else None
                    finish_reason = getattr(choices[0], "finish_reason", None)
                    if chunk.get('provider'): final_provider = chunk['provider']
                    if chunk.get('model'): final_model = chunk['model']

                    if content:
                        yield f"data: {json_lib.dumps({'token': content, 'provider': final_provider})}\n\n"
                    if finish_reason == "stop":
                        latency_ms = (_time.time() - start_ts) * 1000
                        # Log to DB using a SEPARATE session (the request's session may be closed)
                        try:
                            from app.database import AsyncSessionLocal
                            from app.config import COST_PER_1M
                            async with AsyncSessionLocal() as log_db:
                                log = RequestLog(
                                    user_id=req.user_id,
                                    provider=final_provider or 'unknown',
                                    model=final_model or 'unknown',
                                    latency_ms=latency_ms,
                                    cost_usd=0.0,
                                    task_type=req.task or 'general',
                                    status='success',
                                )
                                log_db.add(log)
                                await log_db.commit()
                        except Exception:
                            pass  # Don't crash the stream for a logging failure
                        yield f"data: {json_lib.dumps({'done': True, 'provider': final_provider, 'model': final_model})}\n\n"
                        return

        except Exception as exc:
            import logging
            logging.error(f"Stream error: {exc}")
            yield f"data: {json_lib.dumps({'error': 'StreamError', 'message': str(exc)[:200]})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
