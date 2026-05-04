import os
import json
import re
import time
import math
import aiofiles
from typing import Any, Dict, List, Set, Tuple
from fastapi import HTTPException
from app.models import RAGDocument
from app.config import RAG_MAX_CHUNK_CHARS, RAG_CHUNK_OVERLAP_CHARS, RAG_STORE_PATH

class SimpleRAGStore:
    def __init__(self, path: str):
        self.path = path
        self.chunks: List[Dict[str, Any]] = []
        self._doc_frequencies = {}
        self._avgdl = 0.0

    async def initialize(self):
        await self._load()
        self._recompute_stats()

    async def _load(self) -> None:
        if not os.path.exists(self.path):
            self.chunks = []
            return
        try:
            async with aiofiles.open(self.path, "r", encoding="utf-8") as f:
                content = await f.read()
                payload = json.loads(content)
            self.chunks = payload.get("chunks", []) if isinstance(payload, dict) else []
        except Exception:
            self.chunks = []

    async def _save(self) -> None:
        try:
            async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
                content = json.dumps({"chunks": self.chunks}, ensure_ascii=False)
                await f.write(content)
        except Exception as e:
            import logging
            logging.error(f"Failed to save RAG store: {e}")

    def _recompute_stats(self):
        self._doc_frequencies = {}
        total_len = 0
        for chunk in self.chunks:
            tokens = chunk.get("tokens", [])
            total_len += len(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self._doc_frequencies[t] = self._doc_frequencies.get(t, 0) + 1
        self._avgdl = total_len / max(len(self.chunks), 1)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        normalized = re.sub(r"\s+", " ", text.lower()).strip()
        return re.findall(r"[a-z0-9_]+", normalized)

    @staticmethod
    def _chunk_text(text: str, size: int, overlap: int) -> List[str]:
        text = text.strip()
        if len(text) <= size:
            return [text]
        chunks: List[str] = []
        step = max(size - overlap, 1)
        start = 0
        while start < len(text):
            piece = text[start : start + size].strip()
            if piece:
                chunks.append(piece)
            start += step
        return chunks

    async def ingest(self, docs: List[RAGDocument]) -> Dict[str, int]:
        added_chunks = 0
        for i, doc in enumerate(docs):
            doc_id = doc.doc_id or f"doc-{int(time.time())}-{i}"
            metadata = doc.metadata or {}
            for idx, piece in enumerate(self._chunk_text(doc.content, RAG_MAX_CHUNK_CHARS, RAG_CHUNK_OVERLAP_CHARS)):
                tokens = self._tokenize(piece)
                if not tokens:
                    continue
                self.chunks.append(
                    {
                        "chunk_id": f"{doc_id}#chunk-{idx}",
                        "doc_id": doc_id,
                        "text": piece,
                        "tokens": tokens,
                        "metadata": metadata,
                    }
                )
                added_chunks += 1
        if added_chunks > 0:
            self._recompute_stats()
            await self._save()
        return {"documents": len(docs), "chunks": added_chunks}

    def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        q_tokens = self._tokenize(query)
        if not q_tokens or not self.chunks:
            return []
            
        k1 = 1.5
        b = 0.75
        N = len(self.chunks)
        avgdl = self._avgdl or 1.0

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for chunk in self.chunks:
            tokens = chunk.get("tokens", [])
            if not tokens:
                continue
            
            score = 0.0
            doc_len = len(tokens)
            
            for q in set(q_tokens):
                tf = tokens.count(q)
                if tf == 0:
                    continue
                df = self._doc_frequencies.get(q, 0)
                idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
                term_score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
                score += term_score

            if score > 0:
                scored.append((score, chunk))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "score": round(score, 4),
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "text": chunk["text"],
                "content": chunk["text"],  # alias for downstream consumers
                "metadata": chunk.get("metadata", {}),
            }
            for score, chunk in scored[:top_k]
        ]


# ── Public Service Facade ─────────────────────────────────────────
# This class provides the stable interface that dependencies.py and
# the API layer import.  It delegates to SimpleRAGStore internally.

class RAGService:
    """Facade around SimpleRAGStore consumed by FastAPI dependency injection."""

    def __init__(self, store: SimpleRAGStore):
        self._store = store

    # --- Ingest ---
    async def ingest(self, docs: List[RAGDocument]) -> Dict[str, int]:
        """Index a batch of RAGDocument objects."""
        return await self._store.ingest(docs)

    # --- Search ---
    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Return ranked search hits.  Each hit contains 'content' and 'text'."""
        return self._store.search(query, top_k=top_k)

    # --- Context builder (used by unified chat) ---
    def get_context(self, query: str, top_k: int = 4) -> Tuple[str, List[Dict[str, Any]]]:
        """Return (context_string, sources) for prompt augmentation."""
        hits = self.search(query, top_k=top_k)
        if not hits:
            return "", []

        context_lines = []
        sources = []
        for hit in hits:
            source_id = hit["chunk_id"]
            context_lines.append(f"[{source_id}] {hit['text']}")
            sources.append(
                {
                    "chunk_id": hit["chunk_id"],
                    "doc_id": hit["doc_id"],
                    "score": hit["score"],
                    "metadata": hit.get("metadata", {}),
                }
            )
        return "\n\n".join(context_lines), sources

# Singletons removed, will be attached to app.state

