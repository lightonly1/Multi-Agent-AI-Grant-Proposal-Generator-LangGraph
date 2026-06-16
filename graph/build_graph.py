# graph/build_graph.py
#
# LangGraph StateGraph Assembly
# ------------------------------
# This is where we wire all the nodes and edges together
# into a compiled LangGraph graph.
#
# Think of this file as the "main circuit board" —
# it doesn't contain any logic itself, it just connects components.
#
# Author: Krit Prakash (M.Tech Capstone — Vignan Institute)

from langgraph.graph import StateGraph, END

from .state import ProposalState
from .nodes import (
    ingest_guidelines,
    draft_proposal,
    generate_budget,
    evaluate_proposal,
    refine_proposal,
    finalize_output
)
from .edges import should_refine


def build_proposal_graph():
    """
    Build and compile the proposal generation LangGraph.

    Graph structure:
      START
        → ingest_guidelines
        → draft_proposal
        → generate_budget
        → evaluate_proposal
        → [should_refine conditional edge]
             "refine"   → refine_proposal → evaluate_proposal  (loop)
             "finalize" → finalize_output
        → END

    Returns:
        Compiled LangGraph StateGraph ready for .invoke()
    """
    graph = StateGraph(ProposalState)

    # register all nodes
    graph.add_node("ingest_guidelines", ingest_guidelines)
    graph.add_node("draft_proposal",    draft_proposal)
    graph.add_node("generate_budget",   generate_budget)
    graph.add_node("evaluate_proposal", evaluate_proposal)
    graph.add_node("refine_proposal",   refine_proposal)
    graph.add_node("finalize_output",   finalize_output)

    # sequential edges (always execute in this order)
    graph.add_edge("ingest_guidelines", "draft_proposal")
    graph.add_edge("draft_proposal",    "generate_budget")
    graph.add_edge("generate_budget",   "evaluate_proposal")

    # conditional edge after evaluation — this is the feedback loop
    graph.add_conditional_edges(
        "evaluate_proposal",   # source node
        should_refine,         # routing function
        {
            "refine":   "refine_proposal",   # loop back for improvement
            "finalize": "finalize_output"    # done — write to DB and exit
        }
    )

    # after refinement, always re-evaluate
    graph.add_edge("refine_proposal",  "evaluate_proposal")

    # terminal edge
    graph.add_edge("finalize_output",  END)

    # set the starting node
    graph.set_entry_point("ingest_guidelines")

    # compile validates the graph (checks for orphan nodes, etc.)
    compiled_graph = graph.compile()
    return compiled_graph
