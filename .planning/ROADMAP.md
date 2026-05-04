# Roadmap: Aether Gateway Refactor

## Phase 1: Foundation (Completed)
- [x] Create `app/` directory structure and `__init__.py` files
- [x] Implement `app/models.py` (Pydantic schemas)
- [x] Implement `app/config.py` (Env/Settings)
- [x] Implement `app/core/providers.py` (Provider Registry)
- [x] Verification: Config loads correctly and providers are mapped.

## Phase 2: Service Extraction
- [ ] `app/services/rag.py`: Extract RAG logic
- [ ] `app/services/router.py`: Extract Failover & Routing engine
- [ ] `app/services/images.py`: Extract Image generation
- [ ] `app/core/state.py`: Implement centralized StateStore
- [ ] Verification: Services are unit-testable and isolated from FastAPI.

## Phase 3: API & App Assembly
- [ ] `app/api/v1/chat.py`: OpenAI-compatible endpoints
- [ ] `app/api/v1/images.py`: Image endpoints
- [ ] `app/api/v1/rag.py`: RAG management endpoints
- [ ] `app/api/admin.py`: Admin/Hot-reload endpoints
- [ ] `app/main.py`: Main FastAPI app initialization
- [ ] Verification: Full gateway functionality restored through modular routing.

## Phase 4: Polish & Security
- [ ] Implement unified `verify_admin` dependency
- [ ] Add basic integration tests
- [ ] Clean up/Deprecate `simple_ai_gateway.py`
- [ ] Verification: Production readiness check.
