from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatRequest, UnifiedAIChatRequest
from app.dependencies import get_router_service, get_rag_service
from app.services.router import RouterService
from app.services.rag import RAGService
from app.database import get_db
from app.db_models import RequestLog, ChatMessage, Conversation, User
from sqlalchemy import select

router = APIRouter()


async def _resolve_user(api_key: Optional[str], db: AsyncSession):
    if not api_key:
        return None
    result = await db.execute(select(User).where(User.api_key == api_key, User.is_active == True))
    return result.scalar_one_or_none()


async def _log_request(db: AsyncSession, user_id, provider, model, tokens_in, tokens_out, latency_ms, cost_usd, task, status="success", error_msg=None):
    log = RequestLog(
        user_id=user_id,
        provider=provider,
        model=model,
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
    db: AsyncSession = Depends(get_db),
    x_api_key: str = Header(None, alias="X-API-Key"),
    x_conversation_id: str = Header(None, alias="X-Conversation-Id"),
):
    """
    High-level unified chat endpoint.
    Handles RAG integration and task-based routing.
    """
    user = await _resolve_user(x_api_key, db)
    messages = []
    
    # 1. Handle RAG if requested
    if req.use_rag:
        context_docs = rag_svc.search(req.query, top_k=4)
        if context_docs:
            context_str = "\n\n".join([d["content"] for d in context_docs])
            system_prompt = req.system_prompt or "You are a helpful assistant. Use the following context to answer the user's question."
            messages.append({"role": "system", "content": f"{system_prompt}\n\nContext:\n{context_str}"})
    elif req.system_prompt:
        messages.append({"role": "system", "content": req.system_prompt})

    messages.append({"role": "user", "content": req.query})

    # 2. Call router with task-based failover
    response, meta = await router_svc.chat_with_failover(
        messages=messages,
        user_id=req.user_id,
        model_override=req.model_override,
        task=req.task
    )

    answer = response.choices[0].message.content
    usage = response.usage

    # 3. Log to database
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
    )

    # 4. Save to conversation if provided
    if x_conversation_id:
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
            db.add(ChatMessage(
                conversation_id=conv.id,
                role="assistant",
                content=answer,
                provider=meta["provider"],
                model=meta["model"],
            ))

    return {
        "answer": answer,
        "metadata": meta,
        "usage": usage.model_dump() if usage else None
    }
