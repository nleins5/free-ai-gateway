import os
import re
import random
import urllib.parse
import httpx
from typing import Optional, Dict, Any
from app.config import settings

# Regex for cleaning prompts
_IMAGE_COMMAND_RE = re.compile(r"^\s*(/image|draw|generate|create|imagine)\s*", re.I)

_VI_IMAGE_PHRASE_MAP = [
    ("con ho", "a tiger"),
    ("con meo", "a cat"),
    ("phong canh", "landscape"),
    ("rung", "forest"),
    ("nui", "mountain"),
    ("bien", "ocean"),
    ("thanh pho", "city"),
    ("tuong lai", "futuristic"),
    ("cyberpunk", "cyberpunk"),
    ("chan thuc", "realistic"),
    ("sac net", "sharp"),
    ("dep", "beautiful"),
]

def _strip_accents(s: str) -> str:
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

def _translate_vi_image_terms(prompt: str) -> str:
    translated = _strip_accents(prompt).lower()
    translated = re.sub(r"[^a-z0-9\s,.-]", " ", translated)
    translated = re.sub(r"\s+", " ", translated).strip()
    if not translated:
        return prompt

    for vi_phrase, en_phrase in sorted(_VI_IMAGE_PHRASE_MAP, key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(rf"\b{re.escape(vi_phrase)}\b", en_phrase, translated)

    translated = re.sub(r"\s+", " ", translated).strip(" ,.-")
    return translated or prompt

def prepare_image_prompt(prompt: str) -> str:
    clean_prompt = re.sub(r"\s+", " ", prompt).strip()
    subject = _IMAGE_COMMAND_RE.sub("", clean_prompt).strip(" ,.-:")
    subject = subject or clean_prompt
    translated_subject = _translate_vi_image_terms(subject)

    word_count = len(re.findall(r"\w+", translated_subject))
    if word_count <= 4:
        compiled = (
            f"A clear high-quality image of {translated_subject}, centered main subject, "
            "simple clean background, visually faithful to the prompt, no text, no watermark, "
            "no unrelated objects."
        )
    else:
        compiled = (
            f"{translated_subject}. Make the main subject obvious and visually faithful to the prompt. "
            "No text, no watermark, no unrelated objects."
        )

    return compiled[:900]

class ImageService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def generate_image(self, prompt: str) -> Dict[str, Any]:
        clean_prompt = re.sub(r"\s+", " ", prompt).strip()
        compiled_prompt = prepare_image_prompt(clean_prompt)
        
        try:
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
