"""
Drives a LangGraph run for a session.

Streams node-level updates from ``graph.astream(stream_mode="updates")``, persists
each as a ``WorkflowEvent``, and republishes them to SSE subscribers. Because the
graph is compiled with a Postgres checkpointer keyed by ``thread_id=session_id``,
an interrupted run can be resumed by calling :func:`run_workflow` with
``resume=True`` (passing ``None`` as graph input continues from the last
checkpoint).
"""

from __future__ import annotations

from app.db import repository as repo
from app.db.database import SessionLocal
from app.db.models import STATUS_COMPLETED, STATUS_FAILED, STATUS_RUNNING
from app.graph.state import NODE_REPORT
from app.logging_config import get_logger
from app.services.engine import engine
from app.services.pubsub import pubsub

logger = get_logger("app.services.workflow_runner")


def _summarize(node: str, update: dict) -> tuple[str, dict | None]:
    """Produce a compact (message, data) pair for a node's state update."""
    if node == "planner":
        plan = update.get("plan") or {}
        return (
            "Drafted research plan",
            {
                "focus_areas": plan.get("focus_areas", []),
                "search_queries": plan.get("search_queries", []),
            },
        )
    if node == "research":
        return (
            "Gathered evidence",
            {
                "new_findings": len(update.get("findings", []) or []),
                "new_sources": len(update.get("sources", []) or []),
            },
        )
    if node == "analysis":
        analysis = update.get("analysis") or {}
        return (
            "Synthesized findings",
            {
                "products": len(analysis.get("products_and_services", []) or []),
                "signals": len(analysis.get("business_signals", []) or []),
                "unknowns": len(analysis.get("unknowns", []) or []),
            },
        )
    if node == "quality_check":
        q = update.get("quality") or {}
        verdict = "passed" if q.get("passed") else "needs more research"
        return (
            f"Quality check: {verdict} (score {q.get('score')})",
            {
                "score": q.get("score"),
                "passed": q.get("passed"),
                "issues": q.get("issues", []),
                "gaps_to_research": q.get("gaps_to_research", []),
            },
        )
    if node == "report":
        return ("Generated final report", {"ready": True})
    return ("", None)


async def run_workflow(session_id: str, *, resume: bool = False) -> None:
    """Execute (or resume) the research workflow for a session."""
    config = {"configurable": {"thread_id": session_id}}

    async with SessionLocal() as db:
        session = await repo.get_session(db, session_id)
        if session is None:
            logger.warning(
                "run requested for missing session", extra={"ctx_session": session_id},
            )
            return

        graph_input = (
            None
            if resume
            else {
                "session_id": session_id,
                "company_name": session.company_name,
                "website": session.website,
                "objective": session.objective,
                "findings": [],
                "sources": [],
                "errors": [],
                "retries": 0,
            }
        )

        await repo.update_session_status(db, session_id, STATUS_RUNNING)
        await pubsub.publish(session_id, {"type": "started", "status": STATUS_RUNNING})

        final_report: dict | None = None
        try:
            async for chunk in engine.graph.astream(
                graph_input,
                config,
                stream_mode="updates",
            ):
                for node, update in chunk.items():
                    if not isinstance(update, dict):
                        continue
                    message, data = _summarize(node, update)
                    event = await repo.add_event(
                        db,
                        session_id,
                        node=node,
                        status="completed",
                        message=message,
                        data=data,
                    )
                    await pubsub.publish(
                        session_id,
                        {
                            "type": "node",
                            "id": event.id,
                            "node": node,
                            "status": "completed",
                            "message": message,
                            "data": data,
                        },
                    )
                    if node == NODE_REPORT and update.get("report"):
                        final_report = update["report"]

            if final_report is not None:
                await repo.upsert_report(db, session_id, final_report)
            await repo.update_session_status(db, session_id, STATUS_COMPLETED)
            await pubsub.publish(
                session_id, {"type": "done", "status": STATUS_COMPLETED},
            )
            logger.info("workflow completed", extra={"ctx_session": session_id})

        except Exception as exc:
            logger.exception("workflow failed", extra={"ctx_session": session_id})
            await repo.update_session_status(
                db, session_id, STATUS_FAILED, error=str(exc),
            )
            await repo.add_event(
                db,
                session_id,
                node="workflow",
                status="failed",
                message=str(exc),
            )
            await pubsub.publish(
                session_id,
                {"type": "error", "status": STATUS_FAILED, "message": str(exc)},
            )
