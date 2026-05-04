from fastapi import APIRouter, Depends
from app.models import RAGDocument, RAGIngestRequest, RAGSearchRequest, RAGChatRequest
from app.dependencies import get_rag_service, get_router_service
from app.services.rag import RAGService
from app.services.router import RouterService

router = APIRouter()

@router.post("/ingest")
async def ingest_documents(
    req: RAGIngestRequest,
    rag_svc: RAGService = Depends(get_rag_service)
):
    """Index documents for RAG."""
    result = rag_svc.ingest(req.documents)
    return {"status": "success", **result}

@router.post("/search")
async def search_documents(
    req: RAGSearchRequest,
    rag_svc: RAGService = Depends(get_rag_service)
):
    """Search for relevant documents."""
    results = rag_svc.search(req.query, top_k=req.top_k)
    return {"results": results}

@router.post("/chat")
async def rag_chat(
    req: RAGChatRequest,
    rag_svc: RAGService = Depends(get_rag_service),
    router_svc: RouterService = Depends(get_router_service)
):
    """Perform a chat completion augmented with RAG context."""
    # 1. Search for context
    context_docs = rag_svc.search(req.query, top_k=req.top_k)
    context_str = "\n\n".join([d["content"] for d in context_docs])
    
    # 2. Build messages
    messages = [
        {"role": "system", "content": f"{req.system_prompt}\n\nContext:\n{context_str}"},
        {"role": "user", "content": req.query}
    ]
    
    # 3. Call router
    response, meta = await router_svc.chat_with_failover(
        messages=messages,
        model_override=req.model,
        task="general"
    )
    
    return {
        "answer": response.choices[0].message.content,
        "context_used": context_docs,
        "metadata": meta
    }
