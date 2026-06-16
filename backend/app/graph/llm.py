"""LLM factory.

Centralises model selection so nodes never construct a client directly. Two
tiers are exposed: the main model for synthesis-heavy nodes and a cheaper/faster
model for routing and the quality judge.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import settings


def get_chat(*, fast: bool = False, temperature: float = 0.2) -> ChatOpenAI:
    """Return a configured ChatOpenAI client.

    Only called when ``settings.mock_mode`` is False — mock mode bypasses the LLM
    entirely (see app.graph.mock), so no API key is required to run the graph.
    """
    model = settings.openai_fast_model if fast else settings.openai_model
    return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        temperature=temperature,
        timeout=60,
        max_retries=2,
    )
