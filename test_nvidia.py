import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_nvidia():
    nv_token = os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY_CUSTOM")
    
    urls_to_test = [
        "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-1.1-pro",
        "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-pro",
        "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"
    ]
    
    payload = {
        "text_prompts": [{"text": "A simple sun"}],
        "seed": 12345,
        "steps": 4
    }
    
    async with httpx.AsyncClient() as client:
        for url in urls_to_test:
            print(f"Testing {url}")
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {nv_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            print(response.status_code)
            print(response.text[:200])

asyncio.run(test_nvidia())
