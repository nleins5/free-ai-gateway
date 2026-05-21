import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_nvidia():
    nv_token = os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY_CUSTOM")
    if not nv_token:
        print("No NVIDIA API key found")
        return
    
    url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"
    payload = {
        "text_prompts": [{"text": "a futuristic 3D rendered sphere, high quality, sci-fi metallic, raytraced"}],
        "seed": 42,
        "steps": 25
    }
    
    headers = {
        "Authorization": f"Bearer {nv_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("Testing NVIDIA Image Generation (FLUX)...")
            response = await client.post(url, headers=headers, json=payload)
            print(f"NVIDIA HTTP Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("NVIDIA Success! Keys in response:", data.keys())
                if "artifacts" in data:
                    print("Artifacts count:", len(data["artifacts"]))
            else:
                print(f"NVIDIA Error body: {response.text}")
        except Exception as e:
            print(f"NVIDIA Exception: {e}")

async def test_huggingface():
    hf_token = os.getenv("HUGGINGFACE_API_KEY")
    if not hf_token:
        print("No HF token found")
        return
    
    model_id = os.getenv("HUGGINGFACE_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("\nTesting HuggingFace Image Generation...")
            response = await client.post(url, headers=headers, json={"inputs": "a futuristic 3D rendered sphere, high quality"})
            print(f"HF HTTP Status: {response.status_code}")
            if response.status_code == 200:
                print("HF Success! Content length:", len(response.content))
            else:
                print(f"HF Error body: {response.text}")
        except Exception as e:
            print(f"HF Exception: {e}")

async def main():
    await test_nvidia()
    await test_huggingface()

if __name__ == "__main__":
    asyncio.run(main())
