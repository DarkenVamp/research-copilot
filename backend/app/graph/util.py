"""Small pure helpers shared across nodes."""

from __future__ import annotations


def format_findings(findings: list[dict], per_result_chars: int = 600) -> str:
    """Render accumulated findings into a compact text block for prompting."""
    if not findings:
        return "(no findings gathered)"
    blocks: list[str] = []
    for item in findings:
        query = item.get("query", "")
        blocks.append(f"### Query: {query}")
        for r in item.get("results", []):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            content = (r.get("content", "") or "")[:per_result_chars]
            blocks.append(f"- {title} ({url})\n  {content}")
    return "\n".join(blocks)


def dedupe_sources(sources: list[dict]) -> list[dict]:
    """Deduplicate sources by URL, preserving first-seen order."""
    seen: set[str] = set()
    out: list[dict] = []
    for s in sources:
        url = s.get("url", "")
        if not url or url in seen:
            continue
        seen.add(url)
        out.append({"title": s.get("title", "") or url, "url": url})
    return out
