"""Planner node: turn the objective into a focused research plan."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.graph import mock, prompts
from app.graph.llm import get_chat
from app.graph.state import ResearchState
from app.logging_config import get_logger
from app.schemas.report import ResearchPlan

logger = get_logger("app.graph.planner")


async def planner_node(state: ResearchState) -> dict:
    company = state["company_name"]
    website = state.get("website")
    objective = state["objective"]

    try:
        if settings.mock_mode:
            plan = mock.mock_plan(company, website, objective)
        else:
            llm = get_chat().with_structured_output(ResearchPlan)
            plan = await llm.ainvoke(
                [
                    SystemMessage(content=prompts.PLANNER_SYSTEM),
                    HumanMessage(
                        content=prompts.PLANNER_USER.format(
                            company_name=company,
                            website=website or "(not provided)",
                            objective=objective,
                        )
                    ),
                ]
            )
        return {"plan": plan.model_dump()}
    except Exception as exc:  # noqa: BLE001 - degrade with a minimal plan
        logger.warning("planner failed, using fallback", extra={"ctx_error": str(exc)})
        fallback = mock.mock_plan(company, website, objective)
        return {
            "plan": fallback.model_dump(),
            "errors": [f"planner error: {exc}"],
        }
