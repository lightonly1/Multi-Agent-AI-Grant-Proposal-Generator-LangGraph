# agents/budget_agent.py

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class BudgetTimelineAgent:

    def __init__(self):
        pass

    def generate_budget_and_timeline(
        self,
        topic: str,
        methodology: str,
        objectives: str,
        max_budget: str,
        duration_months: int
    ):

        logger.info("Generating budget and timeline (FREE MODE)...")

        budget_items = [
            {
                "category": "Personnel",
                "item": "Research Associate",
                "quantity": 1,
                "unit_cost_usd": 12000,
                "cost_usd": 12000,
                "justification": "Handles AI model development"
            },
            {
                "category": "Equipment",
                "item": "Computing system",
                "quantity": 1,
                "unit_cost_usd": 5000,
                "cost_usd": 5000,
                "justification": "Required for model training"
            },
            {
                "category": "Software",
                "item": "Tools and licenses",
                "quantity": 1,
                "unit_cost_usd": 2000,
                "cost_usd": 2000,
                "justification": "Required for development"
            }
        ]

        total_cost = sum(item["cost_usd"] for item in budget_items)

        timeline = [
            {"month": 1, "milestone": "Literature Review"},
            {"month": 3, "milestone": "Data Collection"},
            {"month": 6, "milestone": "Model Development"},
            {"month": 9, "milestone": "Testing"},
            {"month": duration_months, "milestone": "Final Submission"}
        ]

        return {
            "budget_items": budget_items,
            "total_cost_usd": total_cost,
            "timeline_milestones": timeline,
            "within_limit": True
        }

    def run(
        self,
        topic: str,
        proposal_draft: dict,
        guidelines_summary: dict
    ):

        logger.info("=== BudgetTimelineAgent: Starting ===")

        methodology = proposal_draft.get("Methodology", "")
        objectives = proposal_draft.get("Objectives", "")
        max_budget = guidelines_summary.get("max_budget")
        duration = guidelines_summary.get("duration_months", 12)

        budget_data = self.generate_budget_and_timeline(
            topic,
            methodology,
            objectives,
            max_budget,
            duration
        )

        logger.info("=== BudgetTimelineAgent: Done ===")

        return {"budget_timeline": budget_data}