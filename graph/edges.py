# graph/edges.py
#
# LangGraph Conditional Edge Functions
# -------------------------------------
# These functions are called by LangGraph AFTER a node completes
# to decide which node to run next.
#
# This is the agentic routing mechanism — the graph's path is
# not fixed, it depends on the current state values.
#
# Author: Krit Prakash (M.Tech Capstone — Vignan Institute)

import logging
from .state import ProposalState

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def should_refine(state: ProposalState) -> str:
    """
    Conditional edge function called after evaluate_proposal.
    LangGraph uses the return value to pick the next node.

    Decision logic:
      1. If score >= threshold → go to finalize_output
      2. If iteration >= max_iterations → go to finalize_output (don't loop forever)
      3. Otherwise → go to refine_proposal

    Args:
        state: Current ProposalState

    Returns:
        "refine"   → routes to refine_proposal node
        "finalize" → routes to finalize_output node
    """
    total_score   = state["eval_scores"].get("total_score", 0) if state.get("eval_scores") else 0
    iteration     = state.get("iteration", 0)
    max_iter      = state.get("max_iterations", 3)
    threshold     = state.get("score_threshold", 75)

    logger.info(
        f"Routing check: score={total_score}/{threshold}, "
        f"iteration={iteration}/{max_iter}"
    )

    # passed quality bar
    if total_score >= threshold:
        logger.info("→ Score passed threshold. Routing to finalize.")
        return "finalize"

    # hit iteration cap — stop even if score is still low
    if iteration >= max_iter:
        logger.info(
            f"→ Max iterations ({max_iter}) reached. "
            f"Routing to finalize with best available draft."
        )
        return "finalize"

    # still room to improve
    logger.info(
        f"→ Score {total_score} below threshold {threshold}. "
        f"Routing to refine ({max_iter - iteration} iterations remaining)."
    )
    return "refine"
