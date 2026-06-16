"""Analysis node: synthesize raw findings into a structured analysis."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.graph import mock, prompts
from app.graph.llm import get_chat
from app.graph.state import (
    ResearchState,  # noqa: TC001 - used as a runtime-cheap annotation
)
from app.graph.util import format_findings
from app.logging_config import get_logger
from app.schemas.report import Analysis

logger = get_logger("app.graph.analysis")


async def analysis_node(state: ResearchState) -> dict:
    company = state["company_name"]
    objective = state["objective"]
    findings = state.get("findings", [])

    try:
        if settings.mock_mode:
            analysis = mock.mock_analysis(company, objective, findings)
        else:
            llm = get_chat().with_structured_output(Analysis)
            analysis = await llm.ainvoke(
                [
                    SystemMessage(content=prompts.ANALYSIS_SYSTEM),
                    HumanMessage(
                        content=prompts.ANALYSIS_USER.format(
                            company_name=company,
                            objective=objective,
                            findings=format_findings(findings),
                        ),
                    ),
                ],
            )
        return {"analysis": analysis.model_dump()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("analysis failed, using fallback", extra={"ctx_error": str(exc)})
        fallback = mock.mock_analysis(company, objective, findings)
        return {"analysis": fallback.model_dump(), "errors": [f"analysis error: {exc}"]}
