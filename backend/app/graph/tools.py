"""
Research tools: Tavily web search + plain web fetch.

Both degrade gracefully: when no Tavily key is configured they return
deterministic mock results so the whole workflow runs offline.
"""

from __future__ import annotations

import os
import re

import httpx
from langchain_tavily import TavilySearch

from app.config import settings
from app.logging_config import get_logger

logger = get_logger("app.graph.tools")

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _mock_search(query: str) -> list[dict]:
    return [
        {
            "title": f"Overview relevant to: {query}",
            "url": f"https://example.com/search?q={query.replace(' ', '+')}",
            "content": (
                f"[mock result] Summary of publicly available information about "
                f"'{query}'. Includes products, market positioning, and recent "
                f"business activity. Replace with real data by setting TAVILY_API_KEY."
            ),
        },
        {
            "title": f"News & signals: {query}",
            "url": f"https://news.example.com/{query.replace(' ', '-').lower()}",
            "content": (
                f"[mock result] Recent signals related to '{query}': hiring, "
                f"funding rounds, partnerships, and product launches."
            ),
        },
    ]


async def web_search(query: str) -> list[dict]:
    """Return a list of {title, url, content} for a query."""
    if not settings.use_real_search:
        return _mock_search(query)

    # langchain-tavily reads the key from the environment.
    os.environ.setdefault("TAVILY_API_KEY", settings.tavily_api_key)

    tool = TavilySearch(max_results=settings.tavily_max_results)
    raw = await tool.ainvoke({"query": query})
    results = raw.get("results", []) if isinstance(raw, dict) else raw
    out: list[dict] = []
    for r in results or []:
        if isinstance(r, dict):
            out.append(
                {
                    "title": r.get("title", "") or "Untitled",
                    "url": r.get("url", ""),
                    "content": r.get("content", "") or "",
                },
            )
    return out


async def fetch_url(url: str | None) -> str:
    """Fetch a page and return cleaned, truncated text. Best-effort."""
    if not url:
        return ""
    if not settings.use_real_search:
        return f"[mock fetch] Homepage content for {url}."
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ResearchCopilot/0.1"})
            resp.raise_for_status()
            text = _TAG_RE.sub(" ", resp.text)
            text = _WS_RE.sub(" ", text).strip()
            return text[:4000]
    except Exception as exc:  # noqa: BLE001 - degrade gracefully
        logger.warning("fetch_url failed", extra={"ctx_url": url, "ctx_error": str(exc)})
        return ""
