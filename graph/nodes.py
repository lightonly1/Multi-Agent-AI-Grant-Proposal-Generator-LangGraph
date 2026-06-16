# graph/nodes.py

from llm_local import generate_with_llm
import logging
import re

from agents.guideline_agent import GuidelineIngestionAgent
from agents.proposal_agent import ProposalDraftingAgent
from agents.budget_agent import BudgetTimelineAgent
from agents.refinement_agent import RefinementAgent
from db.storage import (
    initialize_database,
    create_run,
    save_proposal,
    save_evaluation,
    save_budget,
    finalize_run
)

from .state import ProposalState

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def ingest_guidelines(state: ProposalState) -> dict:
    logger.info(">>> Node: ingest_guidelines")

    agent = GuidelineIngestionAgent()
    result = agent.run(pdf_path=state["pdf_path"])

    return {
        "guidelines_summary": result["guidelines_summary"],
        "faiss_index_path": result["faiss_index_path"]
    }


def draft_proposal(state: ProposalState) -> dict:
    logger.info(">>> Node: draft_proposal")

    agent = ProposalDraftingAgent()
    result = agent.run(
        topic=state["topic"],
        faiss_index_path=state["faiss_index_path"],
        guidelines_summary=state["guidelines_summary"],
        eval_scores=None
    )

    base_proposal = result["proposal_draft"]

    prompt = f"""
    Improve and rewrite the following research proposal in a professional and structured manner.

    Topic: {state['topic']}

    Proposal:
    {base_proposal}
    """

    enhanced = generate_with_llm(prompt)

    proposal_dict = {
        "Title": state["topic"],
        "Abstract": enhanced,
        "Objectives": enhanced,
        "Methodology": enhanced,
        "Impact": enhanced
    }

    return {"proposal_draft": proposal_dict}


def generate_budget(state: ProposalState) -> dict:
    logger.info(">>> Node: generate_budget")

    agent = BudgetTimelineAgent()
    result = agent.run(
        topic=state["topic"],
        proposal_draft=state["proposal_draft"],
        guidelines_summary=state["guidelines_summary"]
    )

    return {"budget_timeline": result["budget_timeline"]}


def evaluate_proposal(state: ProposalState) -> dict:
    logger.info(f">>> Node: evaluate_proposal (iteration {state['iteration']})")

    initialize_database()

    run_id = state.get("run_id")
    if run_id is None:
        run_id = create_run(
            topic=state["topic"],
            pdf_path=state["pdf_path"]
        )

    proposal_text = str(state["proposal_draft"])

    prompt = f"""
    You are a strict evaluator.

    Evaluate the proposal based on:
    Innovation (0-25)
    Feasibility (0-25)
    Budget (0-25)
    Impact (0-25)

    Output format:
    Innovation: <score>/25
    Feasibility: <score>/25
    Budget: <score>/25
    Impact: <score>/25
    Total: <score>/100

    Also include:
    Strengths
    Weaknesses
    Suggestions

    Proposal:
    {proposal_text}
    """

    llm_output = generate_with_llm(prompt)

    def extract(label, max_val):
        match = re.search(rf"{label}.*?(\d+)", llm_output, re.IGNORECASE)
        if match:
            return min(int(match.group(1)), max_val)
        return int(max_val * 0.6)

    innovation = extract("Innovation", 25)
    feasibility = extract("Feasibility", 25)
    budget = extract("Budget", 25)
    impact = extract("Impact", 25)

    total_score = innovation + feasibility + budget + impact
    new_iteration = state["iteration"] + 1

    eval_scores = {
        "innovation": {"score": innovation},
        "feasibility": {"score": feasibility},
        "budget_clarity": {"score": budget},
        "impact": {"score": impact},
        "total_score": total_score
    }

    snapshot = {
        "iteration": state["iteration"],
        "total_score": total_score,
        "criterion_scores": {
            "innovation": innovation,
            "feasibility": feasibility,
            "budget_clarity": budget,
            "impact": impact
        },
        "weaknesses": {"llm_feedback": llm_output},
        "proposal_title": "Generated Proposal",
        "version_tag": "initial" if state["iteration"] == 0 else f"v{new_iteration}"
    }

    history = list(state.get("iteration_history") or [])
    history.append(snapshot)

    proposal_id = save_proposal(
        run_id=run_id,
        iteration=state["iteration"],
        proposal_draft=state["proposal_draft"],
        version_tag=snapshot["version_tag"]
    )

    save_evaluation(
        run_id=run_id,
        proposal_id=proposal_id,
        iteration=state["iteration"],
        eval_scores=eval_scores
    )

    save_budget(
        run_id=run_id,
        proposal_id=proposal_id,
        budget_timeline=state["budget_timeline"]
    )

    logger.info(f"Dynamic Score: {total_score}/100")

    return {
        "eval_scores": eval_scores,
        "iteration": new_iteration,
        "iteration_history": history,
        "run_id": run_id,
        "llm_feedback": llm_output
    }


def refine_proposal(state: ProposalState) -> dict:
    logger.info(f">>> Node: refine_proposal (after iteration {state['iteration'] - 1})")

    agent = RefinementAgent()
    result = agent.run(
        topic=state["topic"],
        proposal_draft=state["proposal_draft"],
        budget_timeline=state["budget_timeline"],
        eval_scores=state["eval_scores"],
        guidelines_summary=state["guidelines_summary"],
        faiss_index_path=state["faiss_index_path"]
    )

    return {
        "proposal_draft": result["proposal_draft"],
        "refinement_brief": "Refined based on evaluation"
    }


def finalize_output(state: ProposalState) -> dict:
    logger.info(">>> Node: finalize_output")

    run_id = state.get("run_id")
    score = state["eval_scores"].get("total_score", 0)
    iteration = state.get("iteration", 0)

    if run_id:
        finalize_run(
            run_id=run_id,
            final_score=score,
            total_iterations=iteration
        )

    return {
        "topic": state.get("topic"),
        "pdf_path": state.get("pdf_path"),
        "max_iterations": state.get("max_iterations"),
        "score_threshold": state.get("score_threshold"),
        "guidelines_summary": state.get("guidelines_summary"),
        "faiss_index_path": state.get("faiss_index_path"),
        "proposal_draft": state.get("proposal_draft"),
        "budget_timeline": state.get("budget_timeline"),
        "eval_scores": state.get("eval_scores"),
        "iteration": state.get("iteration"),
        "iteration_history": state.get("iteration_history"),
        "refinement_brief": state.get("refinement_brief"),
        "run_id": state.get("run_id")
    }