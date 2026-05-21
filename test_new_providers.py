import os
import requests
from dotenv import load_dotenv

# Load keys from the Desktop env file since they are updated there
load_dotenv("/Users/lananh/Desktop/free-ai-gateway/.env")

providers = [
    {
        "name": "Chutes AI",
        "url": "https://api.chutes.ai/v1/chat/completions",
        "key": os.getenv("CHUTES_API_KEY"),
        "model": "deepseek-ai/DeepSeek-R1",
    },
    {
        "name": "Novita AI",
        "url": "https://api.novita.ai/v3/openai/chat/completions",
        "key": os.getenv("NOVITA_API_KEY"),
        "model": "meta-llama/llama-3.3-70b-instruct",
    },
    {
        "name": "DeepInfra",
        "url": "https://api.deepinfra.com/v1/openai/chat/completions",
        "key": os.getenv("DEEPINFRA_API_KEY"),
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    },
    {
        "name": "Doubleword AI",
        "url": "https://api.doubleword.ai/v1/chat/completions",
        "key": os.getenv("DOUBLEWORD_API_KEY"),
        "model": os.getenv("DOUBLEWORD_MODEL", "moonshotai/Kimi-K2.6"),
    },
    {
        "name": "9Router",
        "url": "http://localhost:20128/v1/chat/completions",
        "key": os.getenv("NINEROUTER_API_KEY", "any-key"),
        "model": os.getenv("NINEROUTER_MODEL", "claude-3-5-sonnet-20241022"),
    }
]

print("=== TESTING NEW PROVIDERS ===")
for provider in providers:
    if not provider["key"]:
        print(f"\n[{provider['name']}] SKIPPED: No API Key found.")
        continue
        
    print(f"\nTesting {provider['name']}...")
    headers = {
        "Authorization": f"Bearer {provider['key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": provider["model"],
        "messages": [{"role": "user", "content": "Reply with 'Hello'"}],
        "max_tokens": 150
    }
    
    try:
        response = requests.post(provider["url"], headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            print(f"[{provider['name']}] SUCCESS: {reply}")
        else:
            print(f"[{provider['name']}] FAILED: HTTP {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[{provider['name']}] ERROR: {str(e)}")
print("\n=== TEST COMPLETE ===")
