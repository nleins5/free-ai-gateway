# 🚀 Hệ Thống AI Miễn Phí với Auto-Routing & Load Balancing

## 📋 Mục lục

1. [Nguồn AI Models Miễn Phí](#nguồn-ai-models-miễn-phí)
2. [Routing & Load Balancing Tools](#routing--load-balancing-tools)
3. [Cách Kết Nối & Tự Động Xoay](#cách-kết-nối--tự-động-xoay)
4. [Implementation Examples](#implementation-examples)

---

## 🎯 Nguồn AI Models Miễn Phí

### 1️⃣ **Cloudflare Workers AI** ⭐⭐⭐⭐⭐

**Free Tier:** 10,000 Neurons/day (reset 00:00 UTC)

**Available Models:**

- **LLMs:** Llama 3/3.1/4, Mistral 7B, Qwen 1.5/2.5, Hermes 2 Pro, Starling 7B, DeepSeek-R1
- **Vision:** FLUX.2 [klein/dev], Leonardo Phoenix, Lucid Origin
- **Audio:** Whisper, MeloTTS, Aura TTS
- **Embeddings:** BGE, UAE-Large
- **Image Generation:** Stable Diffusion variants

**Endpoint:**

```bash
https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}
```

**Setup:**

```bash
# 1. Tạo Cloudflare account (free)
# 2. Get Account ID từ dashboard
# 3. Tạo API Token (Workers AI permissions)

# 4. Test call
curl https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3-8b-instruct \
  -H "Authorization: Bearer {api_token}" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

**Pricing sau free tier:** $0.011/1,000 Neurons

**Docs:** <https://developers.cloudflare.com/workers-ai/>

---

### 2️⃣ **GitHub Models** ⭐⭐⭐⭐⭐

**Free Tier:** Rate limits per model tier

**Available Models:**

- **Tier Low:** 15 req/min, 150 req/day (Llama 3.2, Phi-3)
- **Tier Medium:** 10 req/min, 50 req/day (GPT-4o, Mistral Large)
- **Tier High:** 10 req/min, 50 req/day (Claude Sonnet 4, GPT-4o, DeepSeek-R1, Grok 3)

**Models List:**

- AI21 Jamba 1.5 Large
- Cohere Command R/R+ 08-2024
- **DeepSeek-R1, DeepSeek-V3**
- **Grok 3, Grok 3 Mini**
- **Llama 4 Scout/Maverick**
- Meta Llama 3.1/3.2/3.3 (8B, 70B, 405B)
- Mistral Large, Codestral
- OpenAI GPT-4o, o1-mini
- Anthropic Claude Sonnet 4

**Endpoint:**

```bash
https://models.github.ai/inference
```

**Setup:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key="ghp_YOUR_GITHUB_PAT"  # GitHub Personal Access Token
)

response = client.chat.completions.create(
    model="openai/gpt-4o",  # hoặc "deepseek/deepseek-r1"
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Tạo GitHub PAT:**

1. GitHub Settings → Developer settings → Personal access tokens (Beta)
2. Generate new token với quyền `models:read` / `models`
3. Copy token

**Docs:** <https://docs.github.com/en/github-models>

---

### 3️⃣ **FreeTheAI** ⭐⭐⭐⭐

**Free Tier:** Rate limits per minute

**Available Models:**

- **Chat:** Kimi K2.6, DeepSeek-V3, Llama variants
- **Image:** Grok Imagine (xai/grok-imagine-image)
- **Video:** Grok Imagine Video (xai/grok-imagine-video)
- **Audio/TTS:** Grok TTS (multiple voices)

**Endpoint:**

```bash
https://api.freetheai.xyz/v1
```

**Setup:**

1. Join Discord: <https://discord.gg/freetheai>
2. Run `/signup` command
3. Copy API key

**Example:**

```bash
curl https://api.freetheai.xyz/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "wsf/kimi-k2.6",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

**Docs:** <https://github.com/vibheksoni/free-ai>

---

### 4️⃣ **Groq API** ⭐⭐⭐⭐

**Free Tier:** 14,400 requests/day, 30 req/min

**Models:**

- Llama 3.1/3.2/3.3 (8B, 70B, 405B)
- Gemma 2 (9B, 27B)
- Mixtral 8x7B
- DeepSeek-R1

**Endpoint:**

```bash
https://api.groq.com/openai/v1
```

**Docs:** <https://console.groq.com/>

---

### 5️⃣ **HuggingFace Inference API** ⭐⭐⭐

**Free Tier:** Rate limits vary by model

**Models:** 100,000+ models (<10GB auto-available)

**Endpoint:**

```bash
https://api-inference.huggingface.co/models/{model_name}
```

**Docs:** <https://huggingface.co/docs/api-inference/>

---

### 6️⃣ **OpenRouter** ⭐⭐⭐⭐

**Free Models:** 150+ free models across 20+ providers

**Endpoint:**

```bash
https://openrouter.ai/api/v1
```

**Free Models Include:**

- Google Gemini Flash (free)
- Meta Llama (free tiers)
- Mistral (free tiers)
- Qwen, DeepSeek variants

**Docs:** <https://openrouter.ai/docs>

---

### 7️⃣ **Cerebras Inference** ⭐⭐⭐⭐

**Free Tier:** Generous limits

**Models:**

- Llama 3.1 (8B, 70B)
- Llama 3.3 70B

**Đặc điểm:** Cực kỳ nhanh (2000+ tokens/sec)

**Docs:** <https://cerebras.ai/>

---

### 8️⃣ **Together AI** ⭐⭐⭐

**Free Credits:** $25 signup credit

**Models:** 50+ open-source models

**Docs:** <https://www.together.ai/>

---

## 🔄 Routing & Load Balancing Tools

### 1️⃣ **Bifrost** ⭐⭐⭐⭐⭐ (RECOMMENDED)

**GitHub:** <https://github.com/maximhq/bifrost>

**Features:**

- ⚡ **50x faster than LiteLLM** (11 µs overhead @ 5K RPS)
- 🔄 Automatic failover (<100ms)
- ⚖️ Load balancing across multiple API keys
- 💾 Semantic caching
- 🎯 Support 1000+ models
- 🆓 **Fully open-source, self-hosted**

**Setup:**

```bash
# NPM (quickest)
npx -y @maximhq/bifrost

# Docker
docker run -p 8080:8080 maximhq/bifrost

# Access web UI: http://localhost:8080
```

**Config Example (bifrost.yaml):**

```yaml
models:
  - name: gpt-4-auto
    providers:
      - provider: cloudflare
        model: "@cf/meta/llama-3-8b-instruct"
        api_key: ${CLOUDFLARE_API_TOKEN}
        account_id: ${CLOUDFLARE_ACCOUNT_ID}
        priority: 1

      - provider: github
        model: "gpt-4o"
        api_key: ${GITHUB_PAT}
        priority: 2

      - provider: openrouter
        model: "meta-llama/llama-3.1-70b-instruct:free"
        api_key: ${OPENROUTER_API_KEY}
        priority: 3

    fallback_strategy: priority # auto failover khi rate limit
    load_balancing: round-robin
```

**Usage:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="dummy"  # Bifrost handles auth internally
)

# Request tự động route qua Cloudflare → GitHub → OpenRouter
response = client.chat.completions.create(
    model="gpt-4-auto",
    messages=[{"role": "user", "content": "Hello"}]
)
```

---

### 2️⃣ **Olla** ⭐⭐⭐⭐

**GitHub:** <https://github.com/thushan/olla>

**Features:**

- 🎯 Priority-based routing
- 📌 Sticky sessions (KV-cache aware)
- 💊 Health monitoring + circuit breakers
- 🔁 Automatic retry with failover
- 🔧 Self-healing model discovery

**Setup:**

```bash
# Download binary
wget https://github.com/thushan/olla/releases/latest/download/olla-linux-amd64
chmod +x olla-linux-amd64

# Run
./olla-linux-amd64 --config olla.yaml
```

**Config (olla.yaml):**

```yaml
profiles:
  - name: free-llm-pool
    backends:
      - url: https://api.cloudflare.com/client/v4/accounts/{account}/ai/run
        priority: 1
        health_check: true

      - url: https://models.github.ai/inference
        priority: 2
        health_check: true

      - url: https://api.groq.com/openai/v1
        priority: 3
        health_check: true

    routing_strategy: priority_failover
    sticky_sessions: true
    retry_on_failure: true
```

---

### 3️⃣ **AxonHub** ⭐⭐⭐⭐

**GitHub:** <https://github.com/looplj/axonhub>

**Features:**

- 🔄 Auto failover <100ms
- 💰 Per-request cost tracking
- 🎯 Fine-grained access control
- 📊 End-to-end observability

**Setup:**

```bash
docker compose up -d
# Web UI: http://localhost:3000
```

---

### 4️⃣ **LiteLLM Proxy** ⭐⭐⭐⭐⭐ (Most Popular)

**GitHub:** <https://github.com/BerriAI/litellm>

**Features:**

- 🌐 Support 100+ LLM providers
- ⚖️ Load balancing
- 🔄 Fallbacks
- 💾 Caching
- 📊 Spend tracking

**Setup:**

```bash
pip install litellm[proxy]

# Config
cat > config.yaml << EOF
model_list:
  - model_name: gpt-4-free
    litellm_params:
      model: cloudflare/@cf/meta/llama-3-8b-instruct
      api_key: os.environ/CLOUDFLARE_API_TOKEN

  - model_name: gpt-4-free
    litellm_params:
      model: github/gpt-4o
      api_key: os.environ/GITHUB_PAT

  - model_name: gpt-4-free
    litellm_params:
      model: groq/llama-3.1-70b-versatile
      api_key: os.environ/GROQ_API_KEY

router_settings:
  routing_strategy: simple-shuffle
  num_retries: 3
  retry_after: 10
EOF

# Run
litellm --config config.yaml
```

---

### 5️⃣ **Portkey Gateway** ⭐⭐⭐⭐

**GitHub:** <https://github.com/Portkey-AI/gateway>

**Features:**

- 🚀 200+ LLMs support
- 🛡️ 50+ AI Guardrails
- ⚖️ Load balancing with weights
- 🔄 Automatic retries (5x max)
- ⏱️ Request timeouts

---

## 🎯 Cách Kết Nối & Tự Động Xoay

### Phương Án 1: Bifrost (SIMPLEST) ⭐ RECOMMENDED

**Architecture:**

```
Your App → Bifrost Gateway → [Cloudflare, GitHub, Groq, OpenRouter] → Auto-rotate
```

**Full Setup:**

```bash
# 1. Install Bifrost
npx -y @maximhq/bifrost

# 2. Create config
cat > bifrost.yaml << 'EOF'
providers:
  cloudflare:
    api_key: ${CLOUDFLARE_API_TOKEN}
    account_id: ${CLOUDFLARE_ACCOUNT_ID}

  github:
    api_key: ${GITHUB_PAT}

  groq:
    api_key: ${GROQ_API_KEY}

  openrouter:
    api_key: ${OPENROUTER_API_KEY}

models:
  # Free tier 1: Cloudflare primary
  - name: llama-3-free
    providers:
      - provider: cloudflare
        model: "@cf/meta/llama-3-8b-instruct"
        priority: 1
        rate_limit: 10000  # daily neurons

      - provider: groq
        model: "llama-3.1-8b-instant"
        priority: 2
        rate_limit: 14400  # daily requests

      - provider: openrouter
        model: "meta-llama/llama-3.1-8b-instruct:free"
        priority: 3

    fallback_strategy: priority
    load_balancing: weighted_round_robin
    retry: 3

  # Free tier 2: Advanced models
  - name: gpt-4o-free
    providers:
      - provider: github
        model: "gpt-4o"
        priority: 1
        rate_limit: 50  # daily

      - provider: openrouter
        model: "openai/gpt-4o-mini:free"
        priority: 2

    fallback_strategy: priority
    retry: 3

  # Free tier 3: Reasoning models
  - name: deepseek-r1-free
    providers:
      - provider: github
        model: "deepseek-r1"
        priority: 1

      - provider: openrouter
        model: "deepseek/deepseek-r1:free"
        priority: 2

caching:
  enabled: true
  semantic: true
  ttl: 3600

monitoring:
  enabled: true
  prometheus: true
EOF

# 3. Set environment variables
export CLOUDFLARE_API_TOKEN="your_token"
export CLOUDFLARE_ACCOUNT_ID="your_account_id"
export GITHUB_PAT="ghp_your_token"
export GROQ_API_KEY="your_key"
export OPENROUTER_API_KEY="your_key"

# 4. Run
npx -y @maximhq/bifrost --config bifrost.yaml
```

**Usage in your app:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="dummy"
)

# Auto-rotates across all providers
response = client.chat.completions.create(
    model="gpt-4o-free",  # Will try GitHub → OpenRouter on rate limit
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
```

**How Auto-Rotation Works:**

1. Request hits Bifrost
2. Routes to priority 1 provider (GitHub)
3. If rate limit → automatic failover to priority 2 (OpenRouter)
4. If all fail → retry 3 times with exponential backoff
5. Semantic cache checks before API calls

---

### Phương Án 2: LiteLLM (Most Features)

```bash
# Install
pip install litellm[proxy]

# Config
cat > config.yaml << 'EOF'
model_list:
  # Pool 1: Llama models
  - model_name: llama-pool
    litellm_params:
      model: cloudflare/@cf/meta/llama-3-8b-instruct
      api_key: os.environ/CLOUDFLARE_API_TOKEN
      api_base: https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run

  - model_name: llama-pool
    litellm_params:
      model: groq/llama-3.1-8b-instant
      api_key: os.environ/GROQ_API_KEY

  - model_name: llama-pool
    litellm_params:
      model: openrouter/meta-llama/llama-3.1-8b-instruct:free
      api_key: os.environ/OPENROUTER_API_KEY

  # Pool 2: Advanced models
  - model_name: gpt-4o-pool
    litellm_params:
      model: github/gpt-4o
      api_key: os.environ/GITHUB_PAT
      api_base: https://models.github.ai/inference

  - model_name: gpt-4o-pool
    litellm_params:
      model: openrouter/openai/gpt-4o-mini:free
      api_key: os.environ/OPENROUTER_API_KEY

router_settings:
  routing_strategy: simple-shuffle  # Round-robin
  num_retries: 3
  retry_after: 5
  cooldown_time: 60

  fallbacks:
    - llama-pool: ["gpt-4o-pool"]

  allowed_fails: 3
EOF

# Run
litellm --config config.yaml --port 8000
```

---

### Phương Án 3: Custom Script (Maximum Control)

```python
# free_ai_router.py
import os
import time
from openai import OpenAI
from typing import List, Dict

class FreeAIRouter:
    def __init__(self):
        self.providers = [
            {
                "name": "cloudflare",
                "client": OpenAI(
                    base_url=f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID')}/ai/run",
                    api_key=os.getenv("CLOUDFLARE_API_TOKEN")
                ),
                "models": {
                    "llama-3": "@cf/meta/llama-3-8b-instruct",
                    "mistral": "@cf/mistral/mistral-7b-instruct-v0.1"
                },
                "daily_limit": 10000,
                "current_usage": 0,
                "priority": 1
            },
            {
                "name": "github",
                "client": OpenAI(
                    base_url="https://models.github.ai/inference",
                    api_key=os.getenv("GITHUB_PAT")
                ),
                "models": {
                    "gpt-4o": "gpt-4o",
                    "claude": "claude-sonnet-4",
                    "deepseek": "deepseek-r1"
                },
                "daily_limit": 50,
                "current_usage": 0,
                "priority": 2
            },
            {
                "name": "groq",
                "client": OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=os.getenv("GROQ_API_KEY")
                ),
                "models": {
                    "llama-3": "llama-3.1-8b-instant",
                    "mixtral": "mixtral-8x7b-32768"
                },
                "daily_limit": 14400,
                "current_usage": 0,
                "priority": 3
            }
        ]

        self.current_provider_idx = 0

    def chat(self, model_type: str, messages: List[Dict], **kwargs) -> str:
        """Auto-rotate through providers on failure"""
        providers_tried = 0

        while providers_tried < len(self.providers):
            provider = self.providers[self.current_provider_idx]

            # Check rate limit
            if provider["current_usage"] >= provider["daily_limit"]:
                print(f"⚠️ {provider['name']} rate limit reached, switching...")
                self._rotate_provider()
                providers_tried += 1
                continue

            # Try request
            try:
                model_id = provider["models"].get(model_type)
                if not model_id:
                    self._rotate_provider()
                    providers_tried += 1
                    continue

                print(f"🔄 Using {provider['name']} ({model_id})")

                response = provider["client"].chat.completions.create(
                    model=model_id,
                    messages=messages,
                    **kwargs
                )

                provider["current_usage"] += 1
                return response.choices[0].message.content

            except Exception as e:
                print(f"❌ {provider['name']} failed: {e}")
                self._rotate_provider()
                providers_tried += 1
                time.sleep(1)  # Brief delay before retry

        raise Exception("All providers exhausted")

    def _rotate_provider(self):
        """Switch to next provider"""
        self.current_provider_idx = (self.current_provider_idx + 1) % len(self.providers)

    def reset_daily_limits(self):
        """Reset counters (call this daily via cron)"""
        for provider in self.providers:
            provider["current_usage"] = 0

# Usage
router = FreeAIRouter()

# Auto-rotates Cloudflare → GitHub → Groq on failures
response = router.chat(
    model_type="gpt-4o",
    messages=[{"role": "user", "content": "Explain machine learning"}],
    temperature=0.7,
    max_tokens=500
)

print(response)
```

**Chạy script:**

```bash
python free_ai_router.py
```

---

## 📊 So Sánh Các Phương Án

| Feature              | Bifrost            | LiteLLM       | Custom Script | Olla          |
| -------------------- | ------------------ | ------------- | ------------- | ------------- |
| **Setup Complexity** | ⭐⭐⭐⭐⭐ Easiest | ⭐⭐⭐ Medium | ⭐⭐ Complex  | ⭐⭐⭐ Medium |
| **Performance**      | 50x faster         | Baseline      | Fastest       | Very fast     |
| **Auto Failover**    | ✅ <100ms          | ✅            | ✅ (manual)   | ✅            |
| **Load Balancing**   | ✅ Advanced        | ✅            | ✅ (manual)   | ✅            |
| **Semantic Caching** | ✅                 | ✅            | ❌            | ❌            |
| **Web UI**           | ✅                 | ✅            | ❌            | ❌            |
| **Cost Tracking**    | ✅                 | ✅            | ✅ (manual)   | ❌            |
| **Monitoring**       | ✅ Prometheus      | ✅            | ❌            | ✅            |
| **Customization**    | ⭐⭐⭐             | ⭐⭐⭐⭐      | ⭐⭐⭐⭐⭐    | ⭐⭐⭐        |

**Recommendation:**

- **Production:** Bifrost (fastest + easiest)
- **Max Features:** LiteLLM
- **Full Control:** Custom Script
- **Local LLMs:** Olla

---

## 🎓 Advanced: Multi-Tier Strategy

Combine multiple free tiers for maximum availability:

```yaml
# bifrost-advanced.yaml
models:
  - name: smart-router
    tiers:
      # Tier 1: Fastest free models (Cloudflare, Groq)
      - providers:
          - cloudflare/@cf/meta/llama-3-8b-instruct
          - groq/llama-3.1-8b-instant
        priority: 1
        max_usage: 10000

      # Tier 2: Advanced free models (GitHub)
      - providers:
          - github/gpt-4o
          - github/claude-sonnet-4
        priority: 2
        max_usage: 50

      # Tier 3: Fallback (OpenRouter free tier)
      - providers:
          - openrouter/meta-llama/llama-3.1-70b-instruct:free
          - openrouter/google/gemini-flash-1.5:free
        priority: 3

    routing_logic: |
      if complexity(prompt) < 0.3:
        use tier_1  # Simple queries
      elif complexity(prompt) < 0.7:
        use tier_2  # Complex queries
      else:
        use tier_3  # Very complex
```

---

## 🔧 Debugging & Monitoring

### View Bifrost Logs

```bash
# Real-time monitoring
curl http://localhost:8080/metrics
```

### LiteLLM Dashboard

```bash
litellm --config config.yaml --debug
# Dashboard: http://localhost:4000
```

### Custom Script Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log every request
logger.info(f"Provider: {provider}, Model: {model}, Tokens: {tokens}")
```

---

## 🚀 Deployment Options

### Docker Compose (All-in-One)

```yaml
# docker-compose.yml
version: "3.8"

services:
  bifrost:
    image: maximhq/bifrost:latest
    ports:
      - "8080:8080"
    environment:
      - CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}
      - GITHUB_PAT=${GITHUB_PAT}
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./bifrost.yaml:/app/config.yaml

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Run:**

```bash
docker-compose up -d
```

---

## 📚 Tài Liệu Tham Khảo

### Official Docs

- Cloudflare Workers AI: <https://developers.cloudflare.com/workers-ai/>
- GitHub Models: <https://docs.github.com/en/github-models>
- Bifrost: <https://github.com/maximhq/bifrost>
- LiteLLM: <https://docs.litellm.ai/>
- Olla: <https://thushan.github.io/olla/>

### GitHub Repos

- Free AI Resources: <https://github.com/ShaikhWarsi/free-ai-tools>
- Free LLM APIs: <https://github.com/cheahjs/free-llm-api-resources>
- AI Router Tools: <https://github.com/topics/ai-router>

---

## ⚡ Quick Start (TL;DR)

```bash
# 1. Get API keys (5 phút)
# - Cloudflare: https://dash.cloudflare.com/
# - GitHub: https://github.com/settings/tokens
# - Groq: https://console.groq.com/

# 2. Install Bifrost (30 giây)
npx -y @maximhq/bifrost

# 3. Set env vars
export CLOUDFLARE_API_TOKEN="your_token"
export CLOUDFLARE_ACCOUNT_ID="your_id"
export GITHUB_PAT="ghp_token"
export GROQ_API_KEY="gsk_key"

# 4. Test (Bifrost auto-starts on port 8080)
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# ✅ Done! You now have auto-rotating free AI with failover
```

---

## 💡 Pro Tips

1. **Rate Limit Tracking:** Implement daily cron to reset counters
2. **Caching:** Use Redis for semantic caching (save 70% API calls)
3. **Monitoring:** Set up Prometheus + Grafana for usage insights
4. **Fallback Chain:** Always have 3+ providers configured
5. **Cost Optimization:** Route simple queries to free tiers, complex to premium

---

## 🧪 Implementation Examples

### 0) Kiến trúc gộp các nguồn free vào 1 route

Repo này đã gom các nguồn free/free-tier vào một gateway OpenAI-compatible duy nhất:

```text
App / UI / RAG / fine-tune profile
        |
        v
http://localhost:8000/v1/chat/completions
        |
        v
Router weighted + adaptive + cooldown
        |
        +--> Cloudflare AI Gateway / Workers AI
        +--> GitHub Models
        +--> Groq
        +--> OpenRouter free models
        +--> Gemini API
        +--> Hugging Face / Cerebras / SambaNova / FreeTheAI
        +--> Ollama local fallback
```

Client chỉ cần gọi 1 endpoint và 1 model ảo, ví dụ `smart-chat`. Gateway tự chọn provider còn hoạt động, tự bỏ qua provider thiếu API key, tự cooldown provider lỗi nhiều lần, và trả về provider thật trong `x-ai-provider` / `router.provider`.

Các luồng đã nối chung vào router:

- Chat thường: `/v1/chat/completions`
- Tạo ảnh: `/v1/images/generations`
- RAG: `/v1/rag/ingest`, `/v1/rag/search`, `/v1/rag/chat`
- Fine-tune profile giả lập: `/v1/fine_tune/chat`
- RAG + fine-tune profile: `/v1/rag/fine_tune/chat`
- Benchmark phân phối provider: `python benchmark_router.py ...`

Cloudflare có 2 cách dùng:

- Là một provider trong chain hiện tại qua `CLOUDFLARE_BASE_URL`.
- Là upstream hub nếu bạn cấu hình Cloudflare AI Gateway Dynamic Route/BYOK, rồi đặt `CLOUDFLARE_MODEL=dynamic/default` hoặc gọi alias `cf-dynamic`.

### 1) Chạy gateway local (repo này)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
set -a && source .env && set +a
python simple_ai_gateway.py
```

Mở sản phẩm web:

```bash
open http://localhost:8000/hub
```

Nếu không dùng lệnh `open`, vào trình duyệt và mở:

```text
http://localhost:8000/hub
```

Lưu ý khi sửa `.env`:

- Giữ biến số ở dạng số thuần, ví dụ `ADAPTIVE_LATENCY_ALPHA=0.3`.
- Không nối path vào biến số. Sai: `ADAPTIVE_LATENCY_ALPHA=0.3/Users/.../.venv`.
- Khi dùng `source .env`, các biến JSON phải được bọc bằng nháy đơn:
  `PROVIDER_WEIGHTS_JSON='{"cloudflare":4,"github":2}'`.
- `.env` chứa key thật nên để local; dùng `.env.example` làm template an toàn.
- `.cursor/settings.json` chỉ là cấu hình editor Cursor, không ảnh hưởng runtime gateway.

Config mặc định trong `.env.example` đã bật chain rộng:

```env
PROVIDER_CHAIN=cloudflare,github,groq,openrouter,gemini,huggingface,cerebras,sambanova,freetheai,ollama
ROUTING_MODE=weighted
ADAPTIVE_ROUTING=1
```

Bạn chỉ cần điền key provider nào có. Provider không có key sẽ tự bị bỏ qua.

### 2) Gọi model ảo `smart-chat` (auto xoay provider)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "smart-chat",
    "messages": [
      {"role":"user","content":"Tóm tắt sự khác nhau giữa RAG và fine-tuning"}
    ],
    "temperature": 0.3
  }'
```

Hoặc gọi alias Gemma:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-free",
    "messages": [
      {"role":"user","content":"Giải thích nhanh về vector database"}
    ]
  }'
```

### 3) Xem provider nào đã trả lời

Gateway trả thêm:

- Header: `x-ai-provider`, `x-ai-model`
- Body: `router.provider`, `router.model`

### 4) Xem alias models đang map

```bash
curl http://localhost:8000/router/models
```

### 5) Xem router health state + cooldown

```bash
curl http://localhost:8000/router/state
```

### 5.1) Export metrics kiểu Prometheus

```bash
curl http://localhost:8000/metrics
```

### 6) Gọi Gemma theo profile mạnh

```bash
# Cân bằng tốc độ/chất lượng
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-fast","messages":[{"role":"user","content":"Tóm tắt event-driven architecture"}]}'

# Chất lượng cao hơn (27B nếu provider hỗ trợ)
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-quality","messages":[{"role":"user","content":"Phân tích trade-off giữa Kafka và RabbitMQ"}]}'
```

### 7) Benchmark router phân phối traffic

```bash
python benchmark_router.py \
  --base-url http://localhost:8000 \
  --model smart-chat \
  --requests 60 \
  --concurrency 10
```

### 8) Các biến tuning quan trọng

- `ROUTING_MODE=weighted` để bật chia tải theo trọng số.
- `PROVIDER_WEIGHTS_JSON` để set baseline traffic share.
- `ADAPTIVE_ROUTING=1` để tự điều chỉnh weight theo error-rate + latency.
- `PROVIDER_FAILURE_THRESHOLD` + `PROVIDER_COOLDOWN_S` cho circuit breaker.

### 9) Dùng RAG ngay trong gateway

Ingest tài liệu:

```bash
curl http://localhost:8000/v1/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "id": "pricing-doc",
        "text": "Gói Pro hỗ trợ 100 request/phút. Gói Free hỗ trợ 20 request/phút.",
        "metadata": {"source":"internal-docs"}
      }
    ]
  }'
```

Search context:

```bash
curl http://localhost:8000/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Gói Free giới hạn bao nhiêu request?", "top_k": 3}'
```

Chat với RAG + auto-routing:

```bash
curl http://localhost:8000/v1/rag/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query":"Gói nào phù hợp team nhỏ và giới hạn bao nhiêu?",
    "model":"gemma-quality",
    "top_k": 4
  }'
```

Endpoint sản phẩm gộp cho chat/RAG/fine-tune:

```bash
curl http://localhost:8000/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "chat",
    "model": "smart-chat",
    "query": "Giải thích cách gateway tự xoay provider"
  }'
```

Đổi `mode` thành `rag`, `fine_tune`, hoặc `rag_fine_tune` để dùng các luồng đã tích hợp.

Tạo ảnh ngay trong `/hub`: chọn mode `Image / Flux`, nhập prompt như:

```text
Một robot nhỏ đang điều phối nhiều model AI miễn phí, phong cách cinematic, chi tiết cao
```

API tạo ảnh trực tiếp:

```bash
curl http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A cinematic AI gateway routing free models, high detail"}'
```

Gọi Cloudflare dynamic route nếu bạn đã cấu hình AI Gateway Dynamic Route/BYOK:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cf-dynamic",
    "messages": [
      {"role":"user","content":"Route request này qua Cloudflare AI Gateway dynamic route"}
    ]
  }'
```

### 10) Dùng fine-tune profile

Endpoint này không train model thật; nó dùng `tuning_id` như một expert profile/system prompt rồi vẫn auto-route qua provider đang cấu hình.

```bash
curl http://localhost:8000/v1/fine_tune/chat \
  -H "Content-Type: application/json" \
  -d '{
    "tuning_id": "support-v1",
    "base_model": "llama-3.1-8b",
    "prompt": "Viết câu trả lời ngắn cho khách hỏi về giới hạn gói Free",
    "temperature": 0.4
  }'
```

### 11) Dùng RAG + fine-tune profile cùng lúc

Luồng này retrieve context từ store trước, sau đó trả lời bằng fine-tune profile.

```bash
curl http://localhost:8000/v1/rag/fine_tune/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Khách team nhỏ nên dùng gói nào?",
    "tuning_id": "support-v1",
    "base_model": "llama-3.1-8b",
    "model": "gemma-quality",
    "top_k": 4,
    "include_sources": true
  }'
```

---

### 12) Production Gateway với LiteLLM + Auto-Fallback

Khi cần gateway production-grade, dùng LiteLLM làm proxy trung gian. Toàn bộ app chỉ gọi **1 endpoint duy nhất**, LiteLLM tự xử lý routing + fallback nội bộ.

**File cấu hình `/etc/litellm/config.yaml`:**

```yaml
router:
  model_list:
    - name: openrouter
      model: openrouter/llama-3-70b
      api_base: https://openrouter.ai/api/v1
      api_key: OPENROUTER_KEY
      weight: 4 # Ưu tiên cao nhất
      timeout: 10
    - name: groq
      model: groq/llama3-8b
      api_base: https://api.groq.com/openai/v1
      api_key: GROQ_KEY
      weight: 3
      timeout: 10
    - name: xai
      model: grok-4.1-fast
      api_base: https://api.x.ai/v1
      api_key: XAI_KEY
      weight: 1
      cost_per_1k_tokens: 0.0002 # để tracking

litellm_settings:
  retries: 2
  retry_policy: exponential
  fallbacks:
    - openrouter
    - groq
    - xai
  track_costs: true
  log_requests: true
```

**Router logic (LiteLLM tự xử lý):**

1. Gửi request đến **openrouter** (weight cao nhất).
2. Nếu lỗi 429 (rate limit) hoặc 5xx → tự động chuyển sang **groq**.
3. Nếu groq cũng lỗi → rớt xuống **xai** (Grok 4.1 Fast).
4. Ghi log chi tiết: chi phí, số tokens, thời gian phản hồi.

---

### 13) App production gọi Gateway

Toàn bộ ứng dụng chỉ cần gọi 1 endpoint chuẩn OpenAI:

```bash
POST https://llm-gateway.mycompany.com/v1/chat/completions

{
  "model": "auto",
  "messages": [
    {"role": "user", "content": "Tóm tắt file báo cáo này giúp tôi"}
  ]
}
```

LiteLLM tự route nội bộ theo weight + fallback. Khi thêm provider mới (Fireworks, Together…), chỉ sửa `config.yaml` rồi reload container — **không đụng mã nguồn app**.

---

### 14) Tracking cost & request với Langfuse (self-host miễn phí)

**Cài Langfuse (Docker):**

```bash
docker run -d -p 3000:3000 langfuse/langfuse
```

**Thêm vào `config.yaml`:**

```yaml
integrations:
  langfuse:
    api_key: LANGFUSE_KEY
    endpoint: http://localhost:3000/api
```

**Mỗi request qua Gateway đều được log:**

- Tổng token / request
- Cost theo `cost_per_1k_tokens`
- Model sử dụng (để audit hoặc tối ưu router)

**Dashboard realtime hiển thị:**

- 💰 Tổng chi phí theo ngày
- 🔄 Tỉ lệ fallback (bao nhiêu request gặp lỗi 429)
- ⚖️ Load mỗi provider
- 📈 Token throughput (TPM, RPM)

---

### 15) Mở rộng: thêm provider

Chỉ cần thêm 1 block mới vào `model_list`, set weight:

```yaml
- name: together
  model: together/llama-70b
  api_base: https://api.together.xyz/v1
  api_key: TOGETHER_KEY
  weight: 2
```

Reload container → provider mới lập tức tham gia vào pool routing.

---

### 16) Tách task theo loại (tag-based routing)

LiteLLM hỗ trợ route theo `tag` trong metadata, giúp mapping task → model tối ưu:

| Tag    | Route đến          | Lý do                                                |
| ------ | ------------------ | ---------------------------------------------------- |
| `EASY` | Groq / OpenRouter  | Chat đơn giản, classify, rewrite — nhanh và rẻ       |
| `HARD` | xAI / Claude / GPT | Code, reasoning, phân tích phức tạp — cần chất lượng |

```bash
curl https://llm-gateway.mycompany.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Giải thích kiến trúc microservices"}],
    "metadata": {"tag": "HARD"}
  }'
```
