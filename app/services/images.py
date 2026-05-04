import os
import re
import random
import urllib.parse
import httpx
from typing import Optional, Dict, Any
from app.config import settings

# Regex for cleaning prompts
_IMAGE_COMMAND_RE = re.compile(r"^\s*(/image|draw|generate|create|imagine)\s*", re.I)

def prepare_image_prompt(prompt: str) -> str:
    clean_prompt = re.sub(r"\s+", " ", prompt).strip()
    subject = _IMAGE_COMMAND_RE.sub("", clean_prompt).strip(" ,.-:")
    subject = subject or clean_prompt

    # For modern models like FLUX, passing the prompt as-is works best.
    # We add a mild enhancement for very short prompts.
    word_count = len(re.findall(r"\w+", subject))
    if word_count <= 4:
        compiled = f"{subject}, high quality, detailed, visually appealing"
    else:
        compiled = subject

    return compiled[:900]

class ImageService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def generate_image(self, prompt: str) -> Dict[str, Any]:
        clean_prompt = re.sub(r"\s+", " ", prompt).strip()
        compiled_prompt = prepare_image_prompt(clean_prompt)
        
        try:
            # Try NVIDIA
            nv_image = await self._image_from_nvidia(compiled_prompt)
            if nv_image:
                return nv_image

            # Try Cloudflare
            cf_image = await self._image_from_cloudflare(compiled_prompt)
            if cf_image:
                return cf_image
            
            # Try HuggingFace
            hf_image = await self._image_from_huggingface(compiled_prompt)
            if hf_image:
                return hf_image
        except Exception:
            pass

        # Fallback to Pollinations
        encoded_prompt = urllib.parse.quote(compiled_prompt)
        seed = random.randint(1, 999999)
        source_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux"
        
        return {
            "provider": "pollinations",
            "original_prompt": clean_prompt,
            "translated_prompt": compiled_prompt,
            "data": [{"url": source_url}],
        }

    async def _image_from_nvidia(self, prompt: str) -> Optional[Dict[str, Any]]:
        nv_token = os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY_CUSTOM")
        if not nv_token:
            return None

        url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"
        seed = random.randint(1, 999999)
        payload = {
            "text_prompts": [{"text": prompt}],
            "seed": seed,
            "steps": 25
        }
        
        try:
            response = await self.http_client.post(
                url,
                headers={
                    "Authorization": f"Bearer {nv_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                if "artifacts" in data and len(data["artifacts"]) > 0:
                    img_b64 = data["artifacts"][0]["base64"]
                    return {
                        "provider": "NVIDIA (FLUX.1-dev VIP)",
                        "data": [{"url": f"data:image/jpeg;base64,{img_b64}"}]
                    }
        except Exception:
            pass
        return None

    async def _image_from_cloudflare(self, prompt: str) -> Optional[Dict[str, Any]]:
        cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        cf_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if not cf_account or not cf_token:
            return None

        url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        try:
            response = await self.http_client.post(
                url,
                headers={"Authorization": f"Bearer {cf_token}"},
                json={"prompt": prompt}
            )
            if response.status_code == 200:
                import base64
                img_b64 = base64.b64encode(response.content).decode("utf-8")
                return {
                    "provider": "cloudflare",
                    "data": [{"url": f"data:image/png;base64,{img_b64}"}]
                }
        except Exception:
            pass
        return None

    async def _image_from_huggingface(self, prompt: str) -> Optional[Dict[str, Any]]:
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token:
            return None
        
        model_id = "black-forest-labs/FLUX.1-schnell"
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        try:
            response = await self.http_client.post(
                url,
                headers={"Authorization": f"Bearer {hf_token}"},
                json={"inputs": prompt}
            )
            if response.status_code == 200:
                import base64
                img_b64 = base64.b64encode(response.content).decode("utf-8")
                return {
                    "provider": "huggingface",
                    "data": [{"url": f"data:image/png;base64,{img_b64}"}]
                }
        except Exception:
            pass
        return None

image_service = ImageService()
