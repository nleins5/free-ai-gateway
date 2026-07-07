"""
Web search utility — shared by chat.py unified endpoints.
Deduplicates the perform_web_search function that was previously copy-pasted.
"""
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


async def perform_web_search(query: str) -> List[Dict[str, Any]]:
    """
    Search the web using DuckDuckGo and return deduplicated results.
    Runs in a threadpool since ddgs is synchronous.
    """
    from starlette.concurrency import run_in_threadpool
    return await run_in_threadpool(_search_sync, query)


def _search_sync(q: str) -> List[Dict[str, Any]]:
    """Synchronous web search implementation."""
    results = []

    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            # 1. Primary search
            results.extend(list(ddgs.text(q, max_results=5)))

            # 2. Detect proper nouns (Vietnamese capitalized multi-word names) for deeper search
            proper_nouns = re.findall(r'\b[A-ZÀ-Ỹ][a-zà-ỹ]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]*)*\b', q)
            proper_nouns = [name for name in proper_nouns if len(name.split()) >= 2]

            if not proper_nouns:
                clean_q = re.sub(r'(anh|chị|ông|bà|là ai|ở đâu|thế nào|\?)', '', q, flags=re.IGNORECASE).strip()
                if clean_q:
                    proper_nouns = [clean_q]

            for name in proper_nouns:
                try:
                    results.extend(list(ddgs.text(f'"{name}" uef', max_results=3)))
                except Exception:
                    pass
                try:
                    results.extend(list(ddgs.text(f'"{name}"', max_results=3)))
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Web search failed: {e}")

    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for r in results:
        href = r.get("href")
        if href and href not in seen_urls:
            seen_urls.add(href)
            unique_results.append(r)

    return unique_results[:8]
