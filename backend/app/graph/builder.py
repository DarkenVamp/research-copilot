"""
Assemble the compiled LangGraph workflow.

    START → planner → research → analysis → quality_check ─┐
                          ▲                                 │ (conditional)
                          └──────────── gaps ───────────────┤
                                                            ▼
                                                         report → END

The checkpointer is injected so the same graph definition works with a real
Postgres saver (production / app runtime) or an in-memory saver (tests).
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    analysis_node,
    planner_node,
    quality_node,
    report_node,
    research_node,
)
from app.graph.router import route_after_quality
from app.graph.state import (
    NODE_ANALYSIS,
    NODE_PLANNER,
    NODE_QUALITY,
    NODE_REPORT,
    NODE_RESEARCH,
    ResearchState,
)


def build_graph(checkpointer):
    graph = StateGraph(ResearchState)

    graph.add_node(NODE_PLANNER, planner_node)
    graph.add_node(NODE_RESEARCH, research_node)
    graph.add_node(NODE_ANALYSIS, analysis_node)
    graph.add_node(NODE_QUALITY, quality_node)
    graph.add_node(NODE_REPORT, report_node)

    graph.add_edge(START, NODE_PLANNER)
    graph.add_edge(NODE_PLANNER, NODE_RESEARCH)
    graph.add_edge(NODE_RESEARCH, NODE_ANALYSIS)
    graph.add_edge(NODE_ANALYSIS, NODE_QUALITY)
    graph.add_conditional_edges(
        NODE_QUALITY,
        route_after_quality,
        {NODE_RESEARCH: NODE_RESEARCH, NODE_REPORT: NODE_REPORT},
    )
    graph.add_edge(NODE_REPORT, END)

    return graph.compile(checkpointer=checkpointer)
