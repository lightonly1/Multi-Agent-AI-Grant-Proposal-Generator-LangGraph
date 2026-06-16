# agents/evaluation_agent.py

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class EvaluationAgent:

    def __init__(self):
        pass

    def score_proposal(self, proposal: dict):

        logger.info("Scoring proposal (FREE MODE)...")

        scores = {
            "innovation": {
                "score": 20,
                "reason": "The proposal introduces AI-based optimization in solar energy, which is relevant and moderately novel. However, it lacks comparison with recent state-of-the-art methods.",
                "strength": "Applies AI to a high-impact domain.",
                "weakness": "Needs stronger novelty justification."
            },
            "feasibility": {
                "score": 22,
                "reason": "The methodology is clearly structured with defined steps. The plan appears achievable within the given timeline.",
                "strength": "Well-defined methodology.",
                "weakness": "Could include more details on datasets."
            },
            "budget_clarity": {
                "score": 18,
                "reason": "Budget categories are present and reasonable. However, detailed justification for each item is missing.",
                "strength": "Budget is realistic.",
                "weakness": "Needs item-level justification."
            },
            "impact": {
                "score": 21,
                "reason": "The proposal targets solar energy optimization, which has strong real-world impact. However, outcomes are not clearly quantified.",
                "strength": "High societal relevance.",
                "weakness": "Impact needs measurable metrics."
            }
        }

        total_score = sum(v["score"] for v in scores.values())

        return {
            "criteria": scores,
            "total_score": total_score,
            "grade": "A" if total_score >= 90 else "B" if total_score >= 75 else "C",
            "overall_recommendation": "Good proposal with strong fundamentals. Improve novelty and justification for higher score.",
            "ready_to_submit": total_score >= 75
        }

    def run(
        self,
        proposal_draft: dict,
        budget_timeline: dict,
        guidelines_summary: dict,
        iteration: int = 1
    ):

        logger.info(f"=== EvaluationAgent: Starting (iteration {iteration}) ===")

        result = self.score_proposal(proposal_draft)

        result["iteration"] = iteration
        result["evaluated_at"] = datetime.now().isoformat()

        logger.info(f"Final Score: {result['total_score']}/100")

        logger.info("=== EvaluationAgent: Done ===")

        return {
            "eval_scores": result,
            "iteration": iteration + 1
        }