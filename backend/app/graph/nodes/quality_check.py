"""
Quality-check node: LLM-as-judge that drives the conditional retry loop.

The pass/fail decision is enforced against the configured threshold rather than
trusting the model's own boolean, so routing is deterministic and tunable.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.graph import mock, prompts
from app.graph.llm import get_chat
from app.graph.state import (
    ResearchState,  # noqa: TC001 - used as a runtime-cheap annotation
)
from app.logging_config import get_logger
from app.schemas.report import QualityAssessment

logger = get_logger("app.graph.quality")


async def quality_node(state: ResearchState) -> dict:
    objective = state["objective"]
    analysis = state.get("analysis") or {}
    retries = state.get("retries", 0)

    try:
        if settings.mock_mode:
            qa = mock.mock_quality(
                retries,
                settings.quality_threshold,
            )
        else:
            llm = get_chat(fast=True).with_structured_output(QualityAssessment)
            qa = await llm.ainvoke(
                [
                    SystemMessage(content=prompts.QUALITY_SYSTEM),
                    HumanMessage(
                        content=prompts.QUALITY_USER.format(
                            objective=objective,
                            analysis=json.dumps(analysis, indent=2),
                        ),
                    ),
                ],
            )
            # Enforce the threshold ourselves for deterministic routing.
            qa.passed = qa.score >= settings.quality_threshold
        return {"quality": qa.model_dump()}
    except Exception as exc:  # noqa: BLE001 - on judge failure, pass through to report
        logger.warning(
            "quality check failed, passing through",
            extra={"error": str(exc)},
        )
        passthrough = QualityAssessment(score=settings.quality_threshold, passed=True)
        return {
            "quality": passthrough.model_dump(),
            "errors": [f"quality error: {exc}"],
        }
