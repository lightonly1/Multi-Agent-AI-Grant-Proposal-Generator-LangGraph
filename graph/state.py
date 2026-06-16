# graph/state.py
#
# LangGraph State Schema
# ----------------------
# This TypedDict defines the shape of the state object that gets
# passed between all nodes in the LangGraph StateGraph.
#
# v2 change: added iteration_history — a list that accumulates a
# lightweight snapshot after every evaluation pass.  This lets the
# Streamlit UI show before/after score comparisons without hitting
# the database, and enables the score-delta chart to update in real
# time as each iteration completes.
#
# Author: Krit Prakash (M.Tech Capstone — Vignan Institute)

from typing import TypedDict, Optional, List


class IterationSnapshot(TypedDict):
    """
    Lightweight record of one evaluation pass.
    Appended to ProposalState["iteration_history"] after each evaluation.

    Fields:
      iteration:        0-based index of this pass
      total_score:      100-point total
      criterion_scores: {innovation, feasibility, budget_clarity, impact} → int
      weaknesses:       {criterion → weakness string} for failing criteria
      proposal_title:   first line of Title section (for diff display)
      version_tag:      "initial" | "v2" | "v3" etc.
    """
    iteration:        int
    total_score:      int
    criterion_scores: dict   # e.g. {"innovation": 18, "feasibility": 21, ...}
    weaknesses:       dict   # failing criteria → weakness text
    proposal_title:   str
    version_tag:      str


class ProposalState(TypedDict):
    """
    The single shared state object for the entire pipeline.

    Lifecycle of each field:
      topic, pdf_path       → set once before graph starts, never change
      guidelines_summary    → written by ingest_guidelines
      faiss_index_path      → written by ingest_guidelines
      proposal_draft        → written by draft_proposal, overwritten by refine_proposal
      budget_timeline       → written by generate_budget
      eval_scores           → written/overwritten by evaluate_proposal each round
      iteration             → starts at 0, incremented by evaluate_proposal
      iteration_history     → list of IterationSnapshot, grows by one each eval pass
      max_iterations        → set once, never changes
      score_threshold       → set once, never changes
      refinement_brief      → written by refine_proposal (for UI display)
      run_id                → written by evaluate_proposal (first pass) → SQLite FK
    """
    # inputs — set once at pipeline start
    topic:             str
    pdf_path:          str
    max_iterations:    int
    score_threshold:   int

    # set by ingest_guidelines
    guidelines_summary: Optional[dict]
    faiss_index_path:   Optional[str]

    # set by draft_proposal, updated by refine_proposal
    proposal_draft:    Optional[dict]

    # set by generate_budget
    budget_timeline:   Optional[dict]

    # set/updated by evaluate_proposal
    eval_scores:          Optional[dict]
    iteration:            int
    iteration_history:    List[dict]   # list of IterationSnapshot dicts

    # set by refine_proposal (optional, for Streamlit display)
    refinement_brief:  Optional[str]

    # set by finalize_output
    run_id:            Optional[int]
