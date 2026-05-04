from fastapi import Header, HTTPException, Request
from app.config import settings
from app.services.router import RouterService
from app.services.rag import RAGService
from app.services.images import ImageService, image_service

async def verify_admin(x_admin_key: str = Header(None, alias="X-Admin-Key")):
    if not settings.admin_key:
        # If no admin key set, allow access (development mode)
        return
    if x_admin_key != settings.admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")

def get_router_service(request: Request) -> RouterService:
    return request.app.state.router_service

def get_rag_service(request: Request) -> RAGService:
    return request.app.state.rag_service

def get_image_service() -> ImageService:
    return image_service
