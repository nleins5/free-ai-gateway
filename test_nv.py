import os
import requests

url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"
headers = {
    "Authorization": f"Bearer {os.getenv('NVIDIA_API_KEY', 'YOUR_NVIDIA_API_KEY')}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
payload = {
    "prompt": "A futuristic city",
    "seed": 42
}
try:
    response = requests.post(url, headers=headers, json=payload)
    print(response.status_code)
    print(response.text[:200])
except Exception as e:
    print(e)
