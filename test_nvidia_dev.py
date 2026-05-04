import asyncio
import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

async def test_nvidia():
    nv_token = os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY_CUSTOM")
    url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"
    payload = {
        "text_prompts": [{"text": "A clear high-quality image of labubu, centered main subject, simple clean background"}],
        "seed": 12345,
        "steps": 25
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {nv_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30.0
        )
        if response.status_code == 200:
            data = response.json()
            print("Finish Reason:", data["artifacts"][0].get("finishReason"))
            # Let's save it to a file to verify if it is an actual image or a blank image
            import base64
            with open("test_labubu.jpg", "wb") as f:
                f.write(base64.b64decode(data["artifacts"][0]["base64"]))
            print("Saved image to test_labubu.jpg")

asyncio.run(test_nvidia())
