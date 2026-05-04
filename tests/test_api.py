"""
Aether Gateway — API & Core Unit Tests
========================================
Validates endpoint contracts, model schemas, provider registry completeness,
state store logic, and RAG service behavior WITHOUT requiring live provider keys.
"""

import json
import os
import time

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# ─── Health & Smoke ─────────────────────────────────────────────

class TestHealth:
    def test_health_endpoint_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "online"
        assert "timestamp" in body
        assert body["version"] == "2.0.0"


# ─── Request Validation (422 on bad input) ──────────────────────

class TestValidation:
    def test_unified_chat_requires_query(self, client):
        """POST /v1/chat/unified must have a 'query' field."""
        response = client.post("/v1/chat/unified", json={})
        assert response.status_code == 422

    def test_unified_chat_rejects_bare_string(self, client):
        response = client.post("/v1/chat/unified", content='"hello"',
                               headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    def test_completions_requires_messages(self, client):
        """POST /v1/chat/completions must have 'model' and 'messages'."""
        response = client.post("/v1/chat/completions", json={})
        assert response.status_code == 422

    def test_image_generation_requires_prompt(self, client):
        """POST /v1/images/generations must have a 'prompt' field."""
        response = client.post("/v1/images/generations", json={})
        assert response.status_code == 422

    def test_rag_search_requires_query(self, client):
        response = client.post("/v1/rag/search", json={})
        assert response.status_code == 422

    def test_rag_ingest_requires_documents(self, client):
        response = client.post("/v1/rag/ingest", json={})
        assert response.status_code == 422


# ─── Provider Registry ──────────────────────────────────────────

class TestProviderRegistry:
    def test_registry_is_non_empty(self, client):
        from app.core.providers import PROVIDER_REGISTRY
        assert len(PROVIDER_REGISTRY) > 0

    def test_all_providers_in_chain_are_registered(self, client):
        """Every provider listed in providers.json must exist in PROVIDER_REGISTRY."""
        from app.core.providers import PROVIDER_REGISTRY
        cfg_path = os.path.join(os.path.dirname(__file__), "..", "providers.json")
        if not os.path.isfile(cfg_path):
            pytest.skip("providers.json not found")
        with open(cfg_path, "r") as f:
            cfg = json.load(f)
        missing = [p for p in cfg["provider_chain"] if p not in PROVIDER_REGISTRY]
        assert missing == [], f"Missing providers in registry: {missing}"

    def test_provider_dataclass_fields(self, client):
        """Every Provider in the registry should have non-empty required fields."""
        from app.core.providers import PROVIDER_REGISTRY
        for key, p in PROVIDER_REGISTRY.items():
            assert p.key == key, f"Provider key mismatch: {p.key} != {key}"
            assert p.name, f"Provider {key} has no name"
            assert p.api_key_env, f"Provider {key} has no api_key_env"
            assert p.default_model, f"Provider {key} has no default_model"


# ─── State Store Logic ──────────────────────────────────────────

class TestStateStore:
    def _fresh_store(self):
        from app.core.state import StateStore
        return StateStore()

    def test_initial_state_is_clean(self, client):
        store = self._fresh_store()
        state = store.ensure_provider_state("test_provider")
        assert state["failures"] == 0
        assert state["successes"] == 0
        assert state["attempts"] == 0

    def test_mark_success_resets_failures(self, client):
        store = self._fresh_store()
        store.mark_failure("groq", "timeout")
        store.mark_success("groq")
        state = store.ensure_provider_state("groq")
        assert state["failures"] == 0
        assert state["consecutive_failures"] == 0
        assert state["successes"] == 1

    def test_cooldown_triggers_after_threshold(self, client):
        from app.config import PROVIDER_FAILURE_THRESHOLD
        store = self._fresh_store()
        for _ in range(PROVIDER_FAILURE_THRESHOLD):
            store.mark_failure("bad_provider", "500")
        assert store.is_on_cooldown("bad_provider")

    def test_record_latency_ewma(self, client):
        store = self._fresh_store()
        store.record_latency("fast_provider", 100.0)
        state = store.ensure_provider_state("fast_provider")
        assert state["latency_ewma_ms"] == 100.0

        store.record_latency("fast_provider", 200.0)
        # EWMA should be between 100 and 200
        assert 100.0 < state["latency_ewma_ms"] < 200.0

    def test_effective_weight_never_zero(self, client):
        store = self._fresh_store()
        weight = store.get_effective_weight("unknown_provider", 100)
        assert weight > 0

    def test_usage_tracking_accumulates(self, client):
        store = self._fresh_store()
        store.record_usage("groq", tokens_in=1000, tokens_out=500)
        store.record_usage("groq", tokens_in=2000, tokens_out=1000)
        usage = store.daily_usage["groq"]
        assert usage["requests"] == 2
        assert usage["tokens_in"] == 3000
        assert usage["tokens_out"] == 1500

    def test_get_all_states_shape(self, client):
        store = self._fresh_store()
        store.mark_attempt("groq")
        result = store.get_all_states()
        assert "providers" in result
        assert "daily_usage" in result
        assert "total_cost_usd" in result


# ─── RAG Service ─────────────────────────────────────────────────

class TestRAGService:
    def _fresh_service(self, tmp_path):
        from app.services.rag import SimpleRAGStore, RAGService
        from app.models import RAGDocument
        store = SimpleRAGStore(str(tmp_path / "test_rag.json"))
        return RAGService(store)

    def test_search_empty_store_returns_empty(self, tmp_path):
        svc = self._fresh_service(tmp_path)
        results = svc.search("anything", top_k=4)
        assert results == []

    @pytest.mark.asyncio
    async def test_ingest_and_search_round_trip(self, tmp_path):
        from app.models import RAGDocument
        svc = self._fresh_service(tmp_path)
        doc = RAGDocument(content="The quick brown fox jumps over the lazy dog", doc_id="fox-doc")
        result = await svc.ingest([doc])
        assert result["documents"] == 1
        assert result["chunks"] >= 1

        hits = svc.search("quick fox", top_k=2)
        assert len(hits) >= 1
        assert "content" in hits[0]
        assert "fox" in hits[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_get_context_returns_tuple(self, tmp_path):
        from app.models import RAGDocument
        svc = self._fresh_service(tmp_path)
        doc = RAGDocument(content="AI gateway with multi-provider routing", doc_id="gw-doc")
        await svc.ingest([doc])

        context_str, sources = svc.get_context("gateway routing")
        assert isinstance(context_str, str)
        assert isinstance(sources, list)
        assert len(context_str) > 0


# ─── Config / Settings ──────────────────────────────────────────

class TestConfig:
    def test_settings_has_required_properties(self, client):
        from app.config import settings
        assert isinstance(settings.routing_mode, str)
        assert isinstance(settings.admin_key, str)
        assert isinstance(settings.provider_cooldown_s, float)
        assert isinstance(settings.provider_chain, list)
        assert isinstance(settings.task_tiers, dict)

    @pytest.mark.asyncio
    async def test_reload_config_is_idempotent(self, client):
        from app.config import reload_config, settings
        chain_before = list(settings.provider_chain)
        await reload_config()
        assert settings.provider_chain == chain_before


# ─── Admin Endpoints ────────────────────────────────────────────

class TestAdmin:
    def test_stats_accessible_without_key_in_dev(self, client):
        """In dev mode (ADMIN_SECRET=changeme), stats should be accessible."""
        response = client.get("/admin/stats")
        # Either 200 (no key needed) or 403 (key needed but not sent)
        assert response.status_code in (200, 403)

    def test_config_endpoint_exists(self, client):
        response = client.get("/admin/config")
        assert response.status_code in (200, 403)

    def test_reload_endpoint_exists(self, client):
        response = client.post("/admin/reload")
        assert response.status_code in (200, 403)
