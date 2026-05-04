from fastapi import APIRouter, Depends
from app.models import ChatRequest, UnifiedAIChatRequest
from app.dependencies import get_router_service, get_rag_service
from app.services.router import RouterService
from app.services.rag import RAGService

router = APIRouter()

@router.post("/completions")
async def chat_completions(
    req: ChatRequest,
    router_svc: RouterService = Depends(get_router_service)
):
    """OpenAI-compatible chat completions endpoint."""
    response, meta = await router_svc.chat_with_failover(
        messages=[m.model_dump() for m in req.messages],
        user_id=req.user_id,
        model_override=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens
    )
    
    # Wrap response with gateway metadata
    res_dict = response.model_dump()
    res_dict["x_gateway"] = meta
    return res_dict

@router.post("/unified")
async def unified_chat(
    req: UnifiedAIChatRequest,
    router_svc: RouterService = Depends(get_router_service),
    rag_svc: RAGService = Depends(get_rag_service)
):
    """
    High-level unified chat endpoint.
    Handles RAG integration and task-based routing.
    """
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

    return {
        "answer": response.choices[0].message.content,
        "metadata": meta,
        "usage": response.usage.model_dump() if response.usage else None
    }
