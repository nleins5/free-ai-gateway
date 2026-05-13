from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel

from app.database import get_db
from app.db_models import Conversation, ChatMessage, User

router = APIRouter()


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ConversationUpdate(BaseModel):
    title: str


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    provider: Optional[str] = None
    model: Optional[str] = None
    created_at: str


async def _get_user_from_key(api_key: str, db: AsyncSession) -> Optional[User]:
    if not api_key:
        return None
    result = await db.execute(select(User).where(User.api_key == api_key, User.is_active == True))
    return result.scalar_one_or_none()


@router.post("")
async def create_conversation(
    body: ConversationCreate,
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    user = await _get_user_from_key(x_api_key, db) if x_api_key else None

    conv = Conversation(
        title=body.title,
        user_id=user.id if user else None,
    )
    db.add(conv)
    await db.flush()
    return {"id": conv.id, "title": conv.title, "created_at": str(conv.created_at)}


@router.get("")
async def list_conversations(
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    """List conversations for the authenticated user."""
    user = await _get_user_from_key(x_api_key, db) if x_api_key else None
    user_id = user.id if user else None

    query = select(Conversation).order_by(Conversation.updated_at.desc())
    if user_id:
        query = query.where(Conversation.user_id == user_id)
    else:
        query = query.where(Conversation.user_id.is_(None))
    query = query.limit(50)

    result = await db.execute(query)
    convs = result.scalars().all()

    out = []
    for c in convs:
        msg_count_result = await db.execute(
            select(ChatMessage.id).where(ChatMessage.conversation_id == c.id)
        )
        count = len(msg_count_result.all())
        out.append({
            "id": c.id,
            "title": c.title,
            "created_at": str(c.created_at),
            "updated_at": str(c.updated_at),
            "message_count": count,
        })
    return {"conversations": out}


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a conversation."""
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msgs_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
    )
    msgs = msgs_result.scalars().all()

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": str(conv.created_at),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "provider": m.provider,
                "model": m.model,
                "created_at": str(m.created_at),
            }
            for m in msgs
        ],
    }


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    body: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update conversation title."""
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.title = body.title
    return {"id": conv.id, "title": conv.title}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.execute(delete(ChatMessage).where(ChatMessage.conversation_id == conversation_id))
    await db.execute(delete(Conversation).where(Conversation.id == conversation_id))
    return {"status": "deleted", "id": conversation_id}
