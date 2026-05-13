import os
from dataclasses import dataclass
from typing import Dict

@dataclass
class Provider:
    key: str
    name: str
    base_url: str
    api_key_env: str
    model_env: str
    default_model: str

PROVIDER_REGISTRY: Dict[str, Provider] = {
    "github": Provider(
        key="github",
        name="GitHub Models",
        base_url="https://models.github.ai/inference",
        api_key_env="GITHUB_TOKEN",
        model_env="GITHUB_MODEL",
        default_model="gpt-4o-mini",
    ),
    "openrouter": Provider(
        key="openrouter",
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        model_env="OPENROUTER_MODEL",
        default_model="openrouter/free",
    ),
    "cloudflare": Provider(
        key="cloudflare",
        name="Cloudflare AI Gateway",
        base_url=os.getenv("CLOUDFLARE_BASE_URL", ""),
        api_key_env="CLOUDFLARE_API_KEY",
        model_env="CLOUDFLARE_MODEL",
        default_model="@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    ),
    "groq": Provider(
        key="groq",
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        model_env="GROQ_MODEL",
        default_model="llama-3.3-70b-versatile",
    ),
    "gemini": Provider(
        key="gemini",
        name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key_env="GEMINI_API_KEY",
        model_env="GEMINI_MODEL",
        default_model="gemini-flash-latest",
    ),
    "cerebras": Provider(
        key="cerebras",
        name="Cerebras",
        base_url="https://api.cerebras.ai/v1",
        api_key_env="CEREBRAS_API_KEY",
        model_env="CEREBRAS_MODEL",
        default_model="llama-3.3-70b",
    ),
    "sambanova": Provider(
        key="sambanova",
        name="SambaNova",
        base_url="https://api.sambanova.ai/v1",
        api_key_env="SAMBANOVA_API_KEY",
        model_env="SAMBANOVA_MODEL",
        default_model="Llama-3.1-405B-Instruct",
    ),
    "freetheai": Provider(
        key="freetheai",
        name="FreeTheAI",
        base_url="https://api.freetheai.xyz/v1",
        api_key_env="FREETHEAI_API_KEY",
        model_env="FREETHEAI_MODEL",
        default_model="wsf/kimi-k2.6",
    ),
    "huggingface": Provider(
        key="huggingface",
        name="HuggingFace",
        base_url="https://api-inference.huggingface.co/v1/",
        api_key_env="HUGGINGFACE_API_KEY",
        model_env="HUGGINGFACE_MODEL",
        default_model="Qwen/Qwen2.5-72B-Instruct",
    ),
    "ollama": Provider(
        key="ollama",
        name="Ollama Local",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key_env="OLLAMA_API_KEY",
        model_env="OLLAMA_MODEL",
        default_model="llama3.1:8b",
    ),
    "together": Provider(
        key="together",
        name="Together AI",
        base_url="https://api.together.xyz/v1",
        api_key_env="TOGETHER_API_KEY",
        model_env="TOGETHER_MODEL",
        default_model="meta-llama/Llama-3-70b-chat-hf",
    ),
    "xai": Provider(
        key="xai",
        name="xAI (Grok)",
        base_url="https://api.x.ai/v1",
        api_key_env="XAI_API_KEY",
        model_env="XAI_MODEL",
        default_model="grok-2",
    ),
    "claude": Provider(
        key="claude",
        name="Anthropic (via Proxy)",
        base_url=os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1"),
        api_key_env="ANTHROPIC_API_KEY",
        model_env="CLAUDE_MODEL",
        default_model="claude-3-5-sonnet-20241022",
    ),
    "nvidia": Provider(
        key="nvidia",
        name="NVIDIA NIM",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env="NVIDIA_API_KEY",
        model_env="NVIDIA_MODEL",
        default_model="meta/llama-3.1-70b-instruct",
    ),
    "nvidia_33": Provider(
        key="nvidia_33",
        name="NVIDIA NIM (Llama 3.3)",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env="NVIDIA_API_KEY_33",
        model_env="NVIDIA_MODEL_33",
        default_model="meta/llama-3.3-70b-instruct",
    ),
    "nvidia_77": Provider(
        key="nvidia_77",
        name="NVIDIA NIM (Llama 70B)",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env="NVIDIA_API_KEY_77",
        model_env="NVIDIA_MODEL_77",
        default_model="meta/llama-3.1-70b-instruct",
    ),
    "nvidia_custom": Provider(
        key="nvidia_custom",
        name="NVIDIA NIM (Custom)",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env="NVIDIA_API_KEY_CUSTOM",
        model_env="NVIDIA_MODEL_CUSTOM",
        default_model="nvidia/llama-3.1-nemotron-70b-instruct",
    ),
}
