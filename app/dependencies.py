from fastapi import Header, HTTPException, Request
from app.config import settings, GATEWAY_SECRET
from app.services.router import RouterService
from app.services.rag import RAGService
from app.services.images import ImageService, image_service

async def verify_admin(x_admin_key: str = Header(None, alias="X-Admin-Key")):
    if not settings.admin_key:
        # If no admin key set, allow access (development mode)
        return
    if x_admin_key != settings.admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")


async def verify_gateway(x_gateway_key: str = Header(None, alias="X-Gateway-Key")):
    """Verify the shared secret between Vercel frontend and Render backend.
    If GATEWAY_SECRET is not set, skip verification (dev mode).
    """
    if not GATEWAY_SECRET:
        return  # No secret configured → dev mode, allow all
    if x_gateway_key != GATEWAY_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


def get_router_service(request: Request) -> RouterService:
    return request.app.state.router_service

def get_rag_service(request: Request) -> RAGService:
    return request.app.state.rag_service

def get_image_service() -> ImageService:
    return image_service

