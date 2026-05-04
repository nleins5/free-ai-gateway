from fastapi import APIRouter, Depends
from app.models import ImageRequest
from app.dependencies import get_image_service, get_router_service
from app.services.images import ImageService
from app.services.router import RouterService

router = APIRouter()

@router.post("/generations")
async def generate_image(
    req: ImageRequest,
    image_svc: ImageService = Depends(get_image_service),
    router_svc: RouterService = Depends(get_router_service)
):
    """Generate images using available providers with fallback."""
    # Translate and enhance prompt using LLM if necessary
    translation_prompt = [
        {
            "role": "system", 
            "content": "You are a prompt translator. Translate the user's image description into a descriptive English prompt for an AI image generator. If it is already in English, just return the original English text. Do not add conversational filler, output ONLY the translated English prompt."
        },
        {"role": "user", "content": req.prompt}
    ]
    
    try:
        response, _ = await router_svc.chat_with_failover(
            messages=translation_prompt,
            model_override=None,
            temperature=0.3,
            task="general"
        )
        enhanced_prompt = response.choices[0].message.content.strip()
    except Exception:
        # Fallback to original prompt if translation fails
        enhanced_prompt = req.prompt

    return await image_svc.generate_image(enhanced_prompt)
