"""
Follow-up chat grounded in a completed report.

Kept intentionally lightweight: the report is small and bounded, so it is passed
directly as grounding context rather than running a retrieval index. Answers are
constrained to the report to avoid the model inventing facts.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.config import settings
from app.graph import prompts
from app.graph.llm import get_chat

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def render_report_context(report: dict) -> str:
    """Flatten a stored report dict into readable grounding text."""

    def section(title: str, value) -> str:
        if not value:
            return f"## {title}\n(none)"
        if isinstance(value, list):
            if value and isinstance(value[0], dict):  # sources
                lines = [f"- {v.get('title', '')} ({v.get('url', '')})" for v in value]
            else:
                lines = [f"- {v}" for v in value]
            return f"## {title}\n" + "\n".join(lines)
        return f"## {title}\n{value}"

    return "\n\n".join(
        [
            section("Company Overview", report.get("company_overview")),
            section("Products & Services", report.get("products_and_services")),
            section("Target Customers", report.get("target_customers")),
            section("Business Signals", report.get("business_signals")),
            section("Risks & Challenges", report.get("risks_and_challenges")),
            section("Discovery Questions", report.get("discovery_questions")),
            section("Outreach Strategy", report.get("outreach_strategy")),
            section("Unknowns", report.get("unknowns")),
            section("Sources", report.get("sources")),
        ],
    )


def _mock_answer(report: dict, question: str) -> str:
    overview = report.get("company_overview", "the company")
    return (
        f"[mock answer] Based on the report: {overview} "
        f"Regarding '{question}', the briefing's relevant sections cover products, "
        f"customers, signals, and recommended discovery questions. Anything not "
        f"captured is listed under Unknowns."
    )


def _build_messages(
    context: str,
    history: list[dict],
    question: str,
) -> list[SystemMessage | AIMessage | HumanMessage]:
    messages: list[SystemMessage | AIMessage | HumanMessage] = [
        SystemMessage(content=prompts.CHAT_SYSTEM),
        SystemMessage(content=f"RESEARCH REPORT CONTEXT:\n{context}"),
    ]
    for turn in history:
        if turn.get("role") == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=question))
    return messages


async def astream_followup(
    report: dict,
    history: list[dict],
    question: str,
) -> AsyncIterator[str]:
    """
    Stream a follow-up answer token-by-token, grounded only in the report.

    Yields text deltas; concatenating every delta reproduces the full answer.
    Mock mode emits the canned answer in small slices so the streaming UX (and
    its tests) behave the same without an API key.
    """
    context = render_report_context(report)

    if settings.mock_mode:
        answer = _mock_answer(report, question)
        for i in range(0, len(answer), 4):
            await asyncio.sleep(0.01)
            yield answer[i : i + 4]
        return

    llm = get_chat(fast=True, temperature=0.3)
    async for chunk in llm.astream(_build_messages(context, history, question)):
        if text := chunk.text:
            yield text
