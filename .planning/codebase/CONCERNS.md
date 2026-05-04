# Technical Concerns & Debt

## Architecture
- **Monolith**: `simple_ai_gateway.py` is too large (1800+ lines). Needs decomposition.
- **Global State**: Mutable globals will fail in multi-worker or distributed environments.
- **Coupling**: Backend is tightly coupled with the "Hub" UI (embedded HTML).

## Reliability
- **Sync I/O**: `providers.json` loading and `rag_store` saving are synchronous, potentially blocking the event loop.
- **Simplistic RAG**: Lexical search lacks semantic understanding.
- **Broad Exceptions**: Many `except Exception: pass` blocks hide potential failures.

## Security
- **Admin Secret**: Inconsistently applied across endpoints.
- **Sensitive Data**: API keys managed via `.env` but provider weights/config in `providers.json` could be sensitive.
- **Input Sanitization**: Minimal sanitization for prompts (mostly for image fallbacks).

## Performance
- **Image Proxy**: Sequential fetch with multiple attempts might block workers.
- **Large State**: Tracking state for 10+ providers in memory might grow.
