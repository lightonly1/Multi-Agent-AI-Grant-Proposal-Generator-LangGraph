# agents/refinement_agent.py
#
# Refinement Agent
# ----------------
# This is the agent that closes the feedback loop.
# It receives the evaluation scores + weaknesses and decides
# how to improve the proposal — then triggers a full regeneration.
#
# Design decision: Full regeneration vs patching
# -----------------------------------------------
# Earlier approach: patch individual weak sections in place.
# Problem: section-level patching creates inconsistency — the
# "fixed" sections use different terminology and don't flow naturally
# from the surrounding unchanged sections.
#
# Current approach: full regeneration with targeted feedback.
# The ProposalDraftingAgent already supports this — when eval_scores
# are present in its run() call, it adds a feedback section to the
# prompt that instructs the LLM to address specific weaknesses.
# This gives a coherent proposal while still being feedback-driven.
#
# What this agent adds:
# - Analyzes which criteria failed and why
# - Builds a structured refinement brief
# - Decides whether to also regenerate the budget
# - Calls ProposalDraftingAgent with enriched feedback context
#
# Author: Krit Prakash (M.Tech Capstone — Vignan Institute)

import os
import json
import logging

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# import our own agent — refinement delegates actual writing to ProposalDraftingAgent
from .proposal_agent import ProposalDraftingAgent

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# thresholds — scores below these values trigger targeted feedback
CRITERION_THRESHOLD = 18   # out of 25 — below 72% = needs work
CRITICAL_THRESHOLD  = 12   # below 48% = severe problem, needs major rework


class RefinementAgent:
    """
    Agent 5: Analyzes evaluation results and drives proposal improvement.

    Workflow:
      1. Identify which criteria scored below threshold
      2. Categorize failures as mild (needs polish) vs critical (needs rework)
      3. Generate a refinement brief — a structured set of instructions
         specific to the failing areas
      4. Pass this brief to ProposalDraftingAgent for full regeneration
      5. Optionally flag budget issues separately

    Why an LLM for the refinement brief?
      We could just pass the raw weakness strings directly to the drafting agent.
      But using an LLM to first synthesize the weaknesses into actionable
      instructions produces better rewrites — it transforms
      "Novelty is unclear" into "Add a paragraph explicitly comparing your
      approach to [X] and [Y] from the literature".
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=os.environ.get("OPENAI_API_KEY")
        )
        # refinement delegates actual writing to the proposal agent
        self.proposal_agent = ProposalDraftingAgent()

    def analyze_scores(self, eval_scores: dict) -> dict:
        """
        Look at the scores and categorize what needs work.

        Args:
            eval_scores: Full evaluation output from EvaluationAgent

        Returns:
            Analysis dict with:
              - failing_criteria: list of criteria below threshold
              - critical_criteria: list of severely failing criteria
              - passing_criteria: list of criteria that are fine
              - overall_gap: how many points below target
        """
        criteria = ["innovation", "feasibility", "budget_clarity", "impact"]
        failing  = []
        critical = []
        passing  = []

        for criterion in criteria:
            data = eval_scores.get(criterion, {})
            score = data.get("score", 0) if isinstance(data, dict) else 0

            if score < CRITICAL_THRESHOLD:
                critical.append({
                    "criterion": criterion,
                    "score": score,
                    "weakness": data.get("weakness", "No feedback available"),
                    "strength": data.get("strength", "")
                })
            elif score < CRITERION_THRESHOLD:
                failing.append({
                    "criterion": criterion,
                    "score": score,
                    "weakness": data.get("weakness", "No feedback available"),
                    "strength": data.get("strength", "")
                })
            else:
                passing.append(criterion)

        total_score    = eval_scores.get("total_score", 0)
        target_score   = 75
        overall_gap    = max(0, target_score - total_score)

        analysis = {
            "failing_criteria":  failing,
            "critical_criteria": critical,
            "passing_criteria":  passing,
            "all_weak_criteria": critical + failing,   # combined for convenience
            "total_score":       total_score,
            "target_score":      target_score,
            "overall_gap":       overall_gap,
            "needs_major_rework": len(critical) > 0,
            "all_criteria_pass":  len(failing) == 0 and len(critical) == 0
        }

        logger.info(
            f"Score analysis: total={total_score}/100, "
            f"critical failures={len(critical)}, "
            f"mild failures={len(failing)}, "
            f"passing={len(passing)}"
        )

        return analysis

    def generate_refinement_brief(
        self,
        analysis: dict,
        topic: str,
        current_proposal: dict
    ) -> str:
        """
        Use an LLM to convert raw score analysis into a structured,
        actionable refinement brief.

        This brief is more useful than raw weakness strings because
        it's framed as positive instructions ("add X", "strengthen Y")
        rather than criticisms ("X is missing").

        Args:
            analysis: Output from analyze_scores()
            topic: Research topic
            current_proposal: Current proposal draft

        Returns:
            Refinement brief as a formatted string
        """
        weak_items = analysis.get("all_weak_criteria", [])

        if not weak_items:
            logger.info("All criteria passing — no refinement brief needed")
            return ""

        # format the weak items for the prompt
        weak_summary = "\n".join([
            f"- {item['criterion'].upper()} (score: {item['score']}/25): {item['weakness']}"
            for item in weak_items
        ])

        # get the abstract to give the LLM context about the current proposal
        current_abstract = current_proposal.get("Abstract", "")[:500]

        brief_prompt = PromptTemplate(
            input_variables=["topic", "weak_summary", "abstract", "major_rework"],
            template="""
You are a research grant writing coach helping a researcher improve their proposal.
Based on the evaluation feedback below, write a clear, actionable refinement brief.

RESEARCH TOPIC: {topic}

CURRENT PROPOSAL ABSTRACT (for context):
{abstract}

EVALUATION WEAKNESSES TO ADDRESS:
{weak_summary}

SEVERITY: {'Major rework needed — multiple critical failures' if major_rework else 'Polish needed — minor improvements required'}

Write a refinement brief as a numbered list of specific, actionable instructions.
Each instruction should tell the researcher EXACTLY what to add, change, or expand.
Be concrete — name specific sections, suggest specific content additions.

Format:
REFINEMENT BRIEF — Iteration Improvement Instructions:
1. [Section to improve]: [Specific action to take]
2. [Section to improve]: [Specific action to take]
...

Keep the brief to 6-8 instructions maximum. Focus on the highest-impact changes.
"""
        )

        chain = LLMChain(llm=self.llm, prompt=brief_prompt)

        logger.info("Generating refinement brief...")
        brief = chain.run(
            topic=topic,
            weak_summary=weak_summary,
            abstract=current_abstract,
            major_rework=str(analysis.get("needs_major_rework", False))
        )

        return brief.strip()

    def should_regenerate_budget(self, analysis: dict) -> bool:
        """
        Decide if the budget also needs to be regenerated.
        We only regenerate budget if budget_clarity specifically failed,
        since budget generation is expensive (extra LLM call).

        Args:
            analysis: Output from analyze_scores()

        Returns:
            True if budget should also be regenerated
        """
        weak_criteria = [
            item["criterion"]
            for item in analysis.get("all_weak_criteria", [])
        ]
        return "budget_clarity" in weak_criteria

    def run(
        self,
        topic: str,
        proposal_draft: dict,
        budget_timeline: dict,
        eval_scores: dict,
        guidelines_summary: dict,
        faiss_index_path: str
    ) -> dict:
        """
        Main entry point. Called by LangGraph as the refine_proposal node.

        This agent:
          1. Analyzes which criteria failed
          2. Generates a refinement brief
          3. Calls ProposalDraftingAgent for full regeneration
          4. Returns the new proposal (budget is kept unless budget_clarity failed)

        Args:
            topic: Research topic
            proposal_draft: Current proposal from ProposalDraftingAgent
            budget_timeline: Current budget from BudgetTimelineAgent
            eval_scores: Evaluation from EvaluationAgent
            guidelines_summary: Extracted guidelines from Agent 1
            faiss_index_path: Path to FAISS index

        Returns:
            Dict with 'proposal_draft' (new version) and optionally
            'refinement_brief' (for display in UI)
        """
        logger.info("=== RefinementAgent: Starting ===")

        # Step 1: Analyze what failed
        analysis = self.analyze_scores(eval_scores)

        if analysis["all_criteria_pass"]:
            logger.info("All criteria already passing — no refinement needed")
            return {
                "proposal_draft": proposal_draft,
                "refinement_brief": "No refinement needed — all criteria passed."
            }

        # Step 2: Generate structured refinement brief
        refinement_brief = self.generate_refinement_brief(
            analysis=analysis,
            topic=topic,
            current_proposal=proposal_draft
        )

        logger.info(f"Refinement brief:\n{refinement_brief}")

        # Step 3: Enrich eval_scores with the brief so ProposalDraftingAgent
        # gets both the raw weakness descriptions AND the synthesized brief
        enriched_scores = dict(eval_scores)  # copy so we don't mutate original
        enriched_scores["refinement_brief"] = refinement_brief
        enriched_scores["analysis_summary"] = {
            "failing": [item["criterion"] for item in analysis["failing_criteria"]],
            "critical": [item["criterion"] for item in analysis["critical_criteria"]],
            "gap_to_target": analysis["overall_gap"]
        }

        # Step 4: Full regeneration via ProposalDraftingAgent
        # The proposal agent checks for eval_scores in its prompt builder
        logger.info("Triggering full proposal regeneration with feedback...")
        redraft_result = self.proposal_agent.run(
            topic=topic,
            faiss_index_path=faiss_index_path,
            guidelines_summary=guidelines_summary,
            eval_scores=enriched_scores
        )

        new_proposal = redraft_result.get("proposal_draft", proposal_draft)

        # Step 5: Log improvement context
        logger.info(
            f"Refinement complete. Addressed {len(analysis['all_weak_criteria'])} "
            f"weak criteria: "
            f"{[item['criterion'] for item in analysis['all_weak_criteria']]}"
        )

        logger.info("=== RefinementAgent: Done ===")

        return {
            "proposal_draft":    new_proposal,
            "refinement_brief":  refinement_brief,
            "refinement_analysis": analysis
        }
