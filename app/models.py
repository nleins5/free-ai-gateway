from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    extra_body: Optional[Dict[str, Any]] = None

class ImageRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"

class RAGDocument(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    doc_id: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)

class RAGIngestRequest(BaseModel):
    documents: List[RAGDocument]

class RAGSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4

class RAGChatRequest(BaseModel):
    query: str
    model: Optional[str] = None
    system_prompt: Optional[str] = "You are a helpful assistant with access to context information. Answer the question based solely on the provided context."
    top_k: Optional[int] = 4
    stream: Optional[bool] = False

class FineTuneChatRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.1

class RAGFineTuneChatRequest(BaseModel):
    query: str
    model: Optional[str] = None
    system_prompt: Optional[str] = "You are a professional assistant. Answer accurately based on the provided context."
    top_k: Optional[int] = 4
    stream: Optional[bool] = False

class UnifiedAIChatRequest(BaseModel):
    query: str
    task: Optional[str] = "general" # "general", "code", "vision", "image", "gemma"
    model_override: Optional[str] = None
    stream: Optional[bool] = False
    system_prompt: Optional[str] = None
    use_rag: Optional[bool] = False
