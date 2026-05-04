from fastapi import APIRouter, Depends
from app.models import ImageRequest
from app.dependencies import get_image_service
from app.services.images import ImageService

router = APIRouter()

@router.post("/generations")
async def generate_image(
    req: ImageRequest,
    image_svc: ImageService = Depends(get_image_service)
):
    """Generate images using available providers with fallback."""
    return await image_svc.generate_image(req.prompt)
