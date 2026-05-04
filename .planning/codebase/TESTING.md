# Testing Strategy

## Current State
- **Automated Tests**: NONE.
- **Manual Verification**: Performed via the `/hub` or `/chat` UIs.
- **Validation**: Pydantic models provide basic request schema validation.

## Recommended Next Steps
1. **Unit Tests**: For routing logic and cost estimation.
2. **Integration Tests**: For provider failover and RAG ingestion.
3. **Mocking**: Use `httpx` mocking for external AI providers.
