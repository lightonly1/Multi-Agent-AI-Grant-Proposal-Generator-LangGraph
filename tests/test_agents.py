# tests/test_agents.py
#
# Unit Tests for Agent Modules
# -----------------------------
# These tests check that each agent class behaves correctly.
# We mock the LLM and FAISS calls so tests run offline without
# burning API credits. Real integration tests would need a live key.
#
# Run with: python -m pytest tests/ -v
#
# Author: Krit Prakash (M.Tech Capstone — Vignan Institute)

import json
import pytest
import sys
import os

# add project root to path so imports work when running from project dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── shared mock fixtures ────────────────────────────────────────────────────

SAMPLE_TOPIC = "AI-assisted early detection of diabetic retinopathy"

SAMPLE_GUIDELINES = {
    "proposal_sections": [
        "Title", "Abstract", "Problem Statement",
        "Objectives", "Methodology", "Expected Impact"
    ],
    "eligibility_criteria": [
        "Must be affiliated with a recognised institution",
        "Principal Investigator must hold a PhD"
    ],
    "evaluation_rubric": {
        "innovation": 25,
        "feasibility": 25,
        "budget_clarity": 25,
        "impact": 25
    },
    "max_budget": "50000",
    "duration_months": 18,
    "funding_agency": "DST-SERB",
    "submission_deadline": "December 31, 2025",
    "special_requirements": []
}

SAMPLE_PROPOSAL = {
    "Title": "AI-Driven Diabetic Retinopathy Detection Using Fundus Image Analysis",
    "Abstract": (
        "Diabetic retinopathy (DR) is a leading cause of preventable blindness globally. "
        "This proposal presents an AI-based system using deep convolutional neural networks "
        "to detect early-stage DR from fundus photographs with high accuracy. "
        "The system will be validated on public and clinical datasets and deployed "
        "as a mobile-accessible screening tool for rural healthcare settings."
    ),
    "Problem Statement": (
        "Over 77 million Indians suffer from diabetes, yet fewer than 30% receive regular "
        "retinal screening. Manual grading by ophthalmologists is expensive and unavailable "
        "in rural areas. Early detection prevents 90% of vision loss cases."
    ),
    "Objectives": (
        "1. Develop a multi-class CNN model for DR grading (no DR, mild, moderate, severe, PDR)\n"
        "2. Achieve AUC > 0.95 on the APTOS and EyePACS benchmark datasets\n"
        "3. Build a lightweight mobile-compatible inference pipeline\n"
        "4. Deploy and validate in 3 rural PHCs in Telangana\n"
        "5. Publish findings in a peer-reviewed journal"
    ),
    "Methodology": (
        "Phase 1 (Months 1-4): Dataset curation — combine APTOS 2019, EyePACS, and local "
        "clinical data (n>5000 images). Pre-process using CLAHE and circular cropping.\n"
        "Phase 2 (Months 5-10): Model development using EfficientNet-B4 with transfer learning. "
        "Ensemble with ResNet-50 for improved generalization. Explainability via Grad-CAM.\n"
        "Phase 3 (Months 11-15): Mobile deployment using TensorFlow Lite. Integration with "
        "ABHA health ID API.\n"
        "Phase 4 (Months 16-18): Clinical validation, impact assessment, dissemination."
    ),
    "Expected Impact": (
        "The system will enable primary healthcare workers to screen for DR without specialist "
        "presence, potentially screening 50,000+ patients annually across Telangana. "
        "Scientific impact: two journal papers, one conference presentation. "
        "Economic impact: estimated ₹2.1 Cr savings in avoidable blindness treatment costs."
    )
}

SAMPLE_BUDGET = {
    "budget_items": [
        {
            "category": "Personnel",
            "item": "Junior Research Fellow (JRF) — 18 months",
            "quantity": 1,
            "unit_cost_usd": 14400,
            "cost_usd": 14400,
            "justification": "Core ML research and dataset curation"
        },
        {
            "category": "Equipment",
            "item": "GPU Workstation (NVIDIA RTX 4090)",
            "quantity": 1,
            "unit_cost_usd": 3500,
            "cost_usd": 3500,
            "justification": "Model training — existing institute hardware insufficient"
        },
        {
            "category": "Travel",
            "item": "Conference travel — 2 international conferences",
            "quantity": 2,
            "unit_cost_usd": 1800,
            "cost_usd": 3600,
            "justification": "Dissemination of results at top AI/medical imaging venues"
        },
        {
            "category": "Consumables",
            "item": "Cloud compute credits (AWS/GCP) for training runs",
            "quantity": 1,
            "unit_cost_usd": 2000,
            "cost_usd": 2000,
            "justification": "Large-scale hyperparameter sweep on cloud"
        },
        {
            "category": "Overheads",
            "item": "Institutional overhead (20%)",
            "quantity": 1,
            "unit_cost_usd": 4700,
            "cost_usd": 4700,
            "justification": "Standard 20% institutional overhead"
        }
    ],
    "timeline_milestones": [
        {"month": 2,  "milestone": "Dataset collection complete", "deliverable": "Annotated dataset (5000+ images)", "responsible": "PI + JRF"},
        {"month": 6,  "milestone": "Baseline model trained",      "deliverable": "Model with AUC > 0.90",            "responsible": "JRF"},
        {"month": 10, "milestone": "Ensemble model finalized",    "deliverable": "Technical report + code repo",    "responsible": "PI + JRF"},
        {"month": 14, "milestone": "Mobile app deployed",         "deliverable": "APK + deployment report",         "responsible": "JRF"},
        {"month": 18, "milestone": "Clinical validation complete","deliverable": "Journal paper submission",         "responsible": "PI"}
    ],
    "total_cost_usd": 28200,
    "budget_by_category": {
        "Personnel": 14400,
        "Equipment": 3500,
        "Travel": 3600,
        "Consumables": 2000,
        "Overheads": 4700
    },
    "within_limit": True
}

SAMPLE_EVAL_SCORES = {
    "innovation": {
        "score": 20,
        "reason": (
            "The proposal introduces Grad-CAM explainability for fundus image classification "
            "in a rural deployment context — a meaningful contribution beyond baseline CNN "
            "screening tools. The backbone (EfficientNet-B4) is well-established, but the "
            "domain adaptation combination is not widely published for this use case. "
            "Scored 20/25 — solid novelty with a gap in comparative positioning."
        ),
        "strength": "Strong use of explainability via Grad-CAM is novel for rural deployment context.",
        "weakness": "The CNN approach is well-established; the novelty of the ensemble architecture should be better justified."
    },
    "feasibility": {
        "score": 22,
        "reason": (
            "The four-phase plan maps concretely onto the 18-month timeline. Team composition "
            "is appropriate and the MoU with Hyderabad hospitals removes data-access risk. "
            "IRB approval for PHC clinical validation is not scheduled — this takes 6-8 weeks "
            "in Indian academic settings and could compress Phase 4. "
            "Scored 22/25 — well-planned with one material scheduling gap."
        ),
        "strength": "Clear phase-wise methodology with concrete milestones and realistic timeline.",
        "weakness": "Dataset access from local PHCs needs IRB approval — not mentioned in methodology."
    },
    "budget_clarity": {
        "score": 19,
        "reason": (
            "Personnel items are justified with durations and roles. Equipment includes "
            "quantities and model references. Cloud compute ($2,000) is the weakest item — "
            "at AWS p3.2xlarge rates this is plausible but offers no buffer for failed runs. "
            "An AWS calculator screenshot would strengthen this. "
            "Scored 19/25 — good overall with one underspecified item."
        ),
        "strength": "Personnel and equipment costs are well-justified with specific quantities.",
        "weakness": "Consumables (cloud credits) need more breakdown — $2000 seems low for large-scale training."
    },
    "impact": {
        "score": 21,
        "reason": (
            "The impact section names specific beneficiaries, quantifies reach (50,000 patients/year), "
            "and estimates cost savings in INR — unusually concrete for a grant proposal. "
            "International scalability is mentioned in the abstract but has no corresponding plan "
            "in the Expected Impact section. "
            "Scored 21/25 — strong domestic impact case, unsubstantiated international dimension."
        ),
        "strength": "Specific quantitative impact claims (50,000 patients/year, cost savings) are compelling.",
        "weakness": "International scalability beyond Telangana is mentioned but not substantiated."
    },
    "total_score": 82,
    "grade": "A",
    "overall_recommendation": (
        "A strong proposal with clear methodology and measurable impact. "
        "Address the IRB approval gap and provide more detail on cloud compute justification."
    ),
    "ready_to_submit": True,
    "iteration": 1,
    "evaluated_at": "2025-10-15T10:30:00"
}


# ─── GuidelineIngestionAgent tests ───────────────────────────────────────────

class TestGuidelineIngestionAgent:
    """Tests for the PDF ingestion and guidelines extraction agent."""

    def test_import(self):
        """Agent class should import without error."""
        from agents.guideline_agent import GuidelineIngestionAgent
        agent = GuidelineIngestionAgent.__new__(GuidelineIngestionAgent)
        assert agent is not None

    def test_extract_guidelines_fallback_on_bad_json(self, monkeypatch):
        """
        If the LLM returns malformed JSON, the agent should
        gracefully return default guidelines rather than crashing.
        """
        from agents.guideline_agent import GuidelineIngestionAgent
        from unittest.mock import MagicMock

        agent = GuidelineIngestionAgent.__new__(GuidelineIngestionAgent)

        # mock the LLM chain to return garbage
        mock_chain = MagicMock()
        mock_chain.run.return_value = "this is not json at all {broken"

        # mock the LLMChain constructor
        monkeypatch.setattr(
            "agents.guideline_agent.LLMChain",
            lambda **kwargs: mock_chain
        )
        # also mock the LLM and embeddings so __init__ doesn't fail
        agent.llm = MagicMock()
        agent.embeddings = MagicMock()
        agent.text_splitter = MagicMock()

        # create fake page objects
        fake_page = MagicMock()
        fake_page.page_content = "Some guideline text about research funding."
        fake_pages = [fake_page] * 3

        result = agent.extract_guidelines_structure(fake_pages)

        # should return defaults, not raise
        assert "proposal_sections" in result
        assert "evaluation_rubric" in result
        assert isinstance(result["evaluation_rubric"], dict)

    def test_extract_guidelines_parses_valid_json(self, monkeypatch):
        """Agent should parse and return valid JSON from LLM correctly."""
        from agents.guideline_agent import GuidelineIngestionAgent
        from unittest.mock import MagicMock

        agent = GuidelineIngestionAgent.__new__(GuidelineIngestionAgent)
        agent.llm = MagicMock()
        agent.embeddings = MagicMock()

        mock_chain = MagicMock()
        mock_chain.run.return_value = json.dumps(SAMPLE_GUIDELINES)
        monkeypatch.setattr("agents.guideline_agent.LLMChain", lambda **kwargs: mock_chain)

        fake_page = MagicMock()
        fake_page.page_content = "Sample funding guidelines"

        result = agent.extract_guidelines_structure([fake_page] * 2)

        assert result["funding_agency"] == "DST-SERB"
        assert result["duration_months"] == 18
        assert len(result["proposal_sections"]) == 6


# ─── ProposalDraftingAgent tests ─────────────────────────────────────────────

class TestProposalDraftingAgent:
    """Tests for the RAG-based proposal drafting agent."""

    def test_build_feedback_section_empty_when_no_scores(self):
        """With no eval_scores, feedback section should be empty string."""
        from agents.proposal_agent import ProposalDraftingAgent
        agent = ProposalDraftingAgent.__new__(ProposalDraftingAgent)

        result = agent.build_feedback_section(None)
        assert result == ""

    def test_build_feedback_section_flags_low_scores(self):
        """Criteria scoring below threshold should appear in feedback."""
        from agents.proposal_agent import ProposalDraftingAgent
        agent = ProposalDraftingAgent.__new__(ProposalDraftingAgent)

        low_scores = {
            "innovation":     {"score": 10, "weakness": "Not novel enough"},
            "feasibility":    {"score": 20, "weakness": "Looks fine"},
            "budget_clarity": {"score": 8,  "weakness": "Missing justifications"},
            "impact":         {"score": 19, "weakness": "OK"}
        }

        result = agent.build_feedback_section(low_scores)

        # should mention the two failing criteria
        assert "INNOVATION" in result
        assert "BUDGET_CLARITY" in result
        # should NOT mention passing criteria
        assert "FEASIBILITY" not in result

    def test_build_feedback_section_empty_when_all_pass(self):
        """When all criteria pass threshold, feedback should be empty."""
        from agents.proposal_agent import ProposalDraftingAgent
        agent = ProposalDraftingAgent.__new__(ProposalDraftingAgent)

        passing_scores = {
            "innovation":     {"score": 22, "weakness": "Minor gap"},
            "feasibility":    {"score": 21, "weakness": "Minor gap"},
            "budget_clarity": {"score": 20, "weakness": "Minor gap"},
            "impact":         {"score": 23, "weakness": "Minor gap"}
        }

        result = agent.build_feedback_section(passing_scores)
        assert result == ""

    def test_generate_sections_fallback_on_bad_json(self, monkeypatch):
        """If LLM returns bad JSON for proposal, use emergency fallback."""
        from agents.proposal_agent import ProposalDraftingAgent
        from unittest.mock import MagicMock

        agent = ProposalDraftingAgent.__new__(ProposalDraftingAgent)
        agent.llm = MagicMock()
        agent.embeddings = MagicMock()

        mock_chain = MagicMock()
        mock_chain.run.return_value = "```not valid json here```"
        monkeypatch.setattr("agents.proposal_agent.LLMChain", lambda **kwargs: mock_chain)

        result = agent.generate_all_sections(
            topic=SAMPLE_TOPIC,
            context="sample context",
            guidelines=SAMPLE_GUIDELINES
        )

        # fallback should return all required sections
        assert "Title" in result
        assert "Abstract" in result
        assert "Methodology" in result


# ─── BudgetTimelineAgent tests ────────────────────────────────────────────────

class TestBudgetTimelineAgent:
    """Tests for the budget generation agent."""

    def test_compute_totals_correct(self):
        """compute_totals should correctly sum budget items."""
        from agents.budget_agent import BudgetTimelineAgent
        agent = BudgetTimelineAgent.__new__(BudgetTimelineAgent)

        test_budget = {
            "budget_items": [
                {"category": "Personnel", "cost_usd": 10000},
                {"category": "Equipment", "cost_usd": 5000},
                {"category": "Travel",    "cost_usd": 2500}
            ]
        }

        result = agent.compute_totals(test_budget)

        assert result["total_cost_usd"] == 17500
        assert result["budget_by_category"]["Personnel"] == 10000
        assert result["budget_by_category"]["Equipment"] == 5000

    def test_validate_budget_within_limit(self):
        """Budget within limit should set within_limit=True."""
        from agents.budget_agent import BudgetTimelineAgent
        agent = BudgetTimelineAgent.__new__(BudgetTimelineAgent)

        budget = {"total_cost_usd": 30000}
        result = agent.validate_budget(budget, "50000")
        assert result["within_limit"] is True

    def test_validate_budget_exceeds_limit(self):
        """Budget over limit should set within_limit=False."""
        from agents.budget_agent import BudgetTimelineAgent
        agent = BudgetTimelineAgent.__new__(BudgetTimelineAgent)

        budget = {"total_cost_usd": 75000}
        result = agent.validate_budget(budget, "$50,000")
        assert result["within_limit"] is False

    def test_validate_budget_no_limit_stays_true(self):
        """When no limit is specified, within_limit should default to True."""
        from agents.budget_agent import BudgetTimelineAgent
        agent = BudgetTimelineAgent.__new__(BudgetTimelineAgent)

        budget = {"total_cost_usd": 999999}
        result = agent.validate_budget(budget, None)
        assert result["within_limit"] is True


# ─── EvaluationAgent tests ────────────────────────────────────────────────────

class TestEvaluationAgent:
    """
    Tests for the transparent-reasoning evaluation agent.

    Covers:
      - flatten_proposal_to_text (unchanged)
      - format_budget_for_eval (unchanged)
      - score_proposal: reason field present, arithmetic correction
      - score_proposal: fallback_scores triggered on bad JSON
      - score_label: human-readable performance labels
      - format_as_report: report contains all required sections
      - reason fields in fallback scores
    """

    def test_flatten_proposal_includes_all_sections(self):
        """flatten_proposal_to_text should label every section clearly."""
        from agents.evaluation_agent import EvaluationAgent
        agent = EvaluationAgent.__new__(EvaluationAgent)

        result = agent.flatten_proposal_to_text(SAMPLE_PROPOSAL)

        for section in ["TITLE", "ABSTRACT", "PROBLEM STATEMENT",
                        "OBJECTIVES", "METHODOLOGY", "EXPECTED IMPACT"]:
            assert section in result

    def test_format_budget_for_eval_shows_total(self):
        """Budget summary should include total cost and category names."""
        from agents.evaluation_agent import EvaluationAgent
        agent = EvaluationAgent.__new__(EvaluationAgent)

        result = agent.format_budget_for_eval(SAMPLE_BUDGET)

        assert "$28,200" in result
        assert "Personnel" in result

    def test_score_label_correct_bands(self):
        """score_label() should return the right performance label for each band."""
        from agents.evaluation_agent import score_label

        assert score_label(25, 25) == "Excellent (25/25)"
        assert score_label(22, 25) == "Excellent (22/25)"  # 88% >= 84%
        assert score_label(20, 25) == "Strong (20/25)"     # 80% >= 72%
        assert score_label(15, 25) == "Adequate (15/25)"   # 60% >= 56%
        assert score_label(10, 25) == "Weak (10/25)"       # 40% >= 36%
        assert score_label(5,  25) == "Poor (5/25)"        # 20% < 36%
        assert score_label(0,  25) == "Poor (0/25)"

    def test_score_label_includes_fraction(self):
        """score_label should always include the raw score/max in output."""
        from agents.evaluation_agent import score_label
        result = score_label(18, 25)
        assert "18/25" in result

    def test_reason_field_present_after_scoring(self, monkeypatch):
        """
        score_proposal must include a non-empty 'reason' field for every
        criterion when the LLM returns valid JSON.
        """
        from agents.evaluation_agent import EvaluationAgent
        from unittest.mock import MagicMock

        agent = EvaluationAgent.__new__(EvaluationAgent)
        agent.llm = MagicMock()

        valid_scores_with_reasons = {
            "innovation": {
                "score": 20,
                "reason": "The proposal introduces MMD-based domain adaptation, which is novel in this context. However the ensemble ablation is missing. Scored 20/25 because novelty is present but not fully justified.",
                "strength": "Novel domain adaptation approach.",
                "weakness": "Missing ablation study for ensemble choice."
            },
            "feasibility": {
                "score": 21,
                "reason": "Phase-wise plan is detailed and MoU with hospitals is secured. IRB timeline not accounted for — this could delay Phase 4 by 6-8 weeks. Scored 21/25.",
                "strength": "MoU with hospital partner is a strong credibility signal.",
                "weakness": "IRB approval timeline is not budgeted into the schedule."
            },
            "budget_clarity": {
                "score": 19,
                "reason": "Personnel and equipment are well-justified with quantities. Cloud compute budget of $2,400 for 200 GPU-hours is tight at current AWS rates. Scored 19/25.",
                "strength": "Every personnel line item has a clear justification.",
                "weakness": "Cloud compute estimate needs a vendor quote to substantiate."
            },
            "impact": {
                "score": 22,
                "reason": "Claims are specific: 50,000 patients/year and Rs 2.1 Cr savings over 5 years. Ayushman Bharat integration is named explicitly. International scale is aspirational. Scored 22/25.",
                "strength": "Quantified impact claims with a named policy integration pathway.",
                "weakness": "International replication plan is mentioned but not detailed."
            },
            "total_score": 82,
            "grade": "A",
            "overall_recommendation": "Strong proposal. Address IRB scheduling and cloud compute justification.",
            "ready_to_submit": True
        }

        mock_chain = MagicMock()
        mock_chain.run.return_value = json.dumps(valid_scores_with_reasons)
        monkeypatch.setattr("agents.evaluation_agent.LLMChain", lambda **kwargs: mock_chain)

        result = agent.score_proposal(
            proposal_text="test proposal text",
            budget_summary="test budget summary",
            guidelines=SAMPLE_GUIDELINES,
            iteration=1
        )

        # every criterion must have a non-empty reason
        for criterion in ["innovation", "feasibility", "budget_clarity", "impact"]:
            assert criterion in result
            assert isinstance(result[criterion], dict)
            assert "reason" in result[criterion], f"reason missing for {criterion}"
            assert len(result[criterion]["reason"]) > 20, f"reason too short for {criterion}"

    def test_reason_synthesised_when_missing_from_llm(self, monkeypatch):
        """
        If the LLM omits the 'reason' field, score_proposal should
        synthesise one from strength + weakness rather than leaving it empty.
        """
        from agents.evaluation_agent import EvaluationAgent
        from unittest.mock import MagicMock

        agent = EvaluationAgent.__new__(EvaluationAgent)
        agent.llm = MagicMock()

        # LLM output without 'reason' fields (old format)
        scores_no_reason = {
            "innovation":     {"score": 18, "strength": "Novel approach.", "weakness": "Needs ablation."},
            "feasibility":    {"score": 20, "strength": "Clear phases.", "weakness": "IRB gap."},
            "budget_clarity": {"score": 17, "strength": "Items justified.", "weakness": "Cloud undercosted."},
            "impact":         {"score": 21, "strength": "Quantified claims.", "weakness": "Scale unproven."},
            "total_score": 76,
            "grade": "B",
            "overall_recommendation": "Good proposal overall.",
            "ready_to_submit": True
        }

        mock_chain = MagicMock()
        mock_chain.run.return_value = json.dumps(scores_no_reason)
        monkeypatch.setattr("agents.evaluation_agent.LLMChain", lambda **kwargs: mock_chain)

        result = agent.score_proposal(
            proposal_text="test", budget_summary="test",
            guidelines=SAMPLE_GUIDELINES, iteration=1
        )

        # agent should have synthesised a reason for every criterion
        for criterion in ["innovation", "feasibility", "budget_clarity", "impact"]:
            reason = result[criterion].get("reason", "")
            assert len(reason) > 0, f"synthesised reason missing for {criterion}"

    def test_fallback_scores_include_reason(self):
        """
        _fallback_scores() — used when LLM returns unparseable JSON —
        must include a 'reason' field for every criterion.
        """
        from agents.evaluation_agent import EvaluationAgent
        agent = EvaluationAgent.__new__(EvaluationAgent)

        fallback = agent._fallback_scores()

        for criterion in ["innovation", "feasibility", "budget_clarity", "impact"]:
            assert "reason" in fallback[criterion], f"fallback reason missing for {criterion}"
            assert len(fallback[criterion]["reason"]) > 10

    def test_fallback_scores_low_total(self):
        """_fallback_scores should return a low total so refinement triggers."""
        from agents.evaluation_agent import EvaluationAgent
        agent = EvaluationAgent.__new__(EvaluationAgent)

        fallback = agent._fallback_scores()
        assert fallback["total_score"] < 75
        assert fallback["ready_to_submit"] is False

    def test_score_correction_when_llm_arithmetic_wrong(self, monkeypatch):
        """
        If LLM reports wrong total_score, it must be corrected to
        the actual sum of the four criterion scores.
        """
        from agents.evaluation_agent import EvaluationAgent
        from unittest.mock import MagicMock

        agent = EvaluationAgent.__new__(EvaluationAgent)
        agent.llm = MagicMock()

        wrong_scores = {
            "innovation":     {"score": 18, "reason": "Good.", "strength": "Good", "weakness": "Gap"},
            "feasibility":    {"score": 18, "reason": "Good.", "strength": "Good", "weakness": "Gap"},
            "budget_clarity": {"score": 18, "reason": "Good.", "strength": "Good", "weakness": "Gap"},
            "impact":         {"score": 18, "reason": "Good.", "strength": "Good", "weakness": "Gap"},
            "total_score": 80,   # wrong — actual sum is 72
            "grade": "B",
            "overall_recommendation": "Good proposal.",
            "ready_to_submit": False
        }

        mock_chain = MagicMock()
        mock_chain.run.return_value = json.dumps(wrong_scores)
        monkeypatch.setattr("agents.evaluation_agent.LLMChain", lambda **kwargs: mock_chain)

        result = agent.score_proposal(
            proposal_text="test", budget_summary="test",
            guidelines=SAMPLE_GUIDELINES, iteration=1
        )

        assert result["total_score"] == 72

    def test_format_as_report_contains_all_criteria(self):
        """
        format_as_report() should produce a text report that includes
        every criterion name, its score, and the reason text.
        """
        from agents.evaluation_agent import EvaluationAgent
        agent = EvaluationAgent.__new__(EvaluationAgent)

        scores_with_reasons = {
            "innovation": {
                "score": 21,
                "reason": "The proposal introduces domain adaptation via MMD. The ensemble lacks ablation. Scored 21/25 — strong novelty with minor gap.",
                "strength": "Novel MMD adaptation approach.",
                "weakness": "Ensemble ablation missing."
            },
            "feasibility": {
                "score": 22,
                "reason": "Four-phase plan is well-structured and MoU is secured. IRB not scheduled. Scored 22/25.",
                "strength": "MoU with hospital confirms data access.",
                "weakness": "IRB timeline not in schedule."
            },
            "budget_clarity": {
                "score": 20,
                "reason": "Personnel and equipment justified. Cloud compute may be undercosted. Scored 20/25.",
                "strength": "Quantities and rates provided for all items.",
                "weakness": "Cloud estimate needs vendor quote."
            },
            "impact": {
                "score": 22,
                "reason": "Specific quantified claims. Ayushman Bharat pathway named. Scale unproven outside India. Scored 22/25.",
                "strength": "Quantified patient reach and cost savings.",
                "weakness": "International plan not detailed."
            },
            "total_score": 85,
            "grade": "A",
            "overall_recommendation": "Strong proposal. Fix IRB and cloud budget.",
            "ready_to_submit": True,
            "evaluated_at": "2025-01-15T10:30:00"
        }

        report = agent.format_as_report(scores_with_reasons, "AI cancer detection")

        # header elements
        assert "GRANT PROPOSAL EVALUATION REPORT" in report
        assert "AI cancer detection" in report

        # all four criteria present with scores
        assert "Innovation" in report
        assert "21/25" in report
        assert "Feasibility" in report
        assert "22/25" in report
        assert "Budget Clarity" in report
        assert "20/25" in report
        assert "Impact" in report
        assert "22/25" in report

        # reason text present for each criterion
        assert "Why this score" in report
        assert "domain adaptation" in report.lower()
        assert "IRB" in report

        # summary section
        assert "85 / 100" in report
        assert "Grade: A" in report
        assert "READY TO SUBMIT" in report

    def test_format_as_report_without_topic(self):
        """format_as_report should work gracefully with no topic argument."""
        from agents.evaluation_agent import EvaluationAgent
        agent = EvaluationAgent.__new__(EvaluationAgent)

        minimal_scores = {
            "innovation":     {"score": 15, "reason": "Some novelty.", "strength": "OK", "weakness": "Weak"},
            "feasibility":    {"score": 15, "reason": "Feasible.", "strength": "OK", "weakness": "Gap"},
            "budget_clarity": {"score": 15, "reason": "Adequate.", "strength": "OK", "weakness": "Thin"},
            "impact":         {"score": 15, "reason": "Some impact.", "strength": "OK", "weakness": "Vague"},
            "total_score": 60, "grade": "C",
            "overall_recommendation": "Needs significant work.",
            "ready_to_submit": False
        }

        # should not raise even without a topic
        report = agent.format_as_report(minimal_scores)
        assert "GRANT PROPOSAL EVALUATION REPORT" in report
        assert "60 / 100" in report
        assert "Grade: C" in report

    def test_rubric_bands_imported_correctly(self):
        """RUBRIC_BANDS should have all 4 criteria with 5 bands each."""
        from agents.evaluation_agent import RUBRIC_BANDS

        assert set(RUBRIC_BANDS.keys()) == {"innovation", "feasibility",
                                             "budget_clarity", "impact"}
        for criterion, info in RUBRIC_BANDS.items():
            assert "max" in info
            assert "bands" in info
            assert len(info["bands"]) == 5, f"{criterion} should have 5 bands"
            assert info["max"] == 25

    def test_format_bands_string_output(self):
        """_format_bands() should return a non-empty string for every criterion."""
        from agents.evaluation_agent import _format_bands

        for criterion in ["innovation", "feasibility", "budget_clarity", "impact"]:
            result = _format_bands(criterion)
            assert isinstance(result, str)
            assert len(result) > 50
            assert ":" in result  # should have score ranges like "21-25: ..."


# ─── RefinementAgent tests ────────────────────────────────────────────────────

class TestRefinementAgent:
    """Tests for the feedback analysis and proposal refinement agent."""

    def test_analyze_scores_correctly_categorizes(self):
        """
        Scores below CRITERION_THRESHOLD should go to failing,
        below CRITICAL_THRESHOLD to critical, above to passing.
        """
        from agents.refinement_agent import RefinementAgent, CRITERION_THRESHOLD, CRITICAL_THRESHOLD
        agent = RefinementAgent.__new__(RefinementAgent)

        scores = {
            "innovation":     {"score": 8,  "weakness": "Very weak"},   # critical
            "feasibility":    {"score": 15, "weakness": "Needs work"},  # failing
            "budget_clarity": {"score": 21, "weakness": "Minor"},       # passing
            "impact":         {"score": 20, "weakness": "Fine"},        # passing
            "total_score": 64
        }

        result = agent.analyze_scores(scores)

        assert len(result["critical_criteria"]) == 1
        assert result["critical_criteria"][0]["criterion"] == "innovation"

        assert len(result["failing_criteria"]) == 1
        assert result["failing_criteria"][0]["criterion"] == "feasibility"

        assert "budget_clarity" in result["passing_criteria"]
        assert "impact" in result["passing_criteria"]

        assert result["needs_major_rework"] is True

    def test_analyze_scores_all_pass(self):
        """When all criteria pass threshold, all_criteria_pass should be True."""
        from agents.refinement_agent import RefinementAgent
        agent = RefinementAgent.__new__(RefinementAgent)

        result = agent.analyze_scores(SAMPLE_EVAL_SCORES)

        # SAMPLE_EVAL_SCORES has all scores >= 19 — all should pass threshold of 18
        assert result["all_criteria_pass"] is True
        assert len(result["all_weak_criteria"]) == 0

    def test_should_regenerate_budget_when_budget_fails(self):
        """should_regenerate_budget should return True when budget_clarity failed."""
        from agents.refinement_agent import RefinementAgent
        agent = RefinementAgent.__new__(RefinementAgent)

        analysis_with_budget_fail = {
            "all_weak_criteria": [
                {"criterion": "innovation",     "score": 10},
                {"criterion": "budget_clarity", "score": 8}
            ]
        }

        assert agent.should_regenerate_budget(analysis_with_budget_fail) is True

    def test_should_not_regenerate_budget_when_budget_passes(self):
        """should_regenerate_budget should return False when budget_clarity passed."""
        from agents.refinement_agent import RefinementAgent
        agent = RefinementAgent.__new__(RefinementAgent)

        analysis_no_budget_fail = {
            "all_weak_criteria": [
                {"criterion": "innovation", "score": 10}
            ]
        }

        assert agent.should_regenerate_budget(analysis_no_budget_fail) is False


# ─── SQLite storage tests ─────────────────────────────────────────────────────

class TestStorage:
    """Tests for the SQLite storage layer."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Provide a temporary DB path for each test."""
        return str(tmp_path / "test_proposals.db")

    def test_initialize_creates_tables(self, temp_db):
        """initialize_database should create all required tables."""
        import sqlite3
        from db.storage import initialize_database
        initialize_database(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "runs"        in tables
        assert "proposals"   in tables
        assert "evaluations" in tables
        assert "budgets"     in tables

    def test_create_run_returns_id(self, temp_db):
        """create_run should return a positive integer run ID."""
        from db.storage import initialize_database, create_run
        initialize_database(temp_db)

        run_id = create_run("Test topic", "test.pdf", temp_db)
        assert isinstance(run_id, int)
        assert run_id > 0

    def test_save_and_retrieve_proposal(self, temp_db):
        """Saved proposal should be retrievable with correct content."""
        from db.storage import initialize_database, create_run, save_proposal, get_run_history
        initialize_database(temp_db)

        run_id = create_run(SAMPLE_TOPIC, "test.pdf", temp_db)
        proposal_id = save_proposal(
            run_id=run_id,
            iteration=0,
            proposal_draft=SAMPLE_PROPOSAL,
            db_path=temp_db
        )

        assert proposal_id > 0

        history = get_run_history(run_id, temp_db)
        assert len(history["proposals"]) == 1
        assert history["proposals"][0]["title"] == SAMPLE_PROPOSAL["Title"]

    def test_save_evaluation(self, temp_db):
        """Saved evaluation scores should persist in DB."""
        from db.storage import initialize_database, create_run, save_proposal, save_evaluation
        initialize_database(temp_db)

        run_id      = create_run(SAMPLE_TOPIC, "test.pdf", temp_db)
        proposal_id = save_proposal(run_id, 0, SAMPLE_PROPOSAL, db_path=temp_db)
        eval_id     = save_evaluation(run_id, proposal_id, 0, SAMPLE_EVAL_SCORES, temp_db)

        assert eval_id > 0

    def test_finalize_run_updates_status(self, temp_db):
        """finalize_run should update status to 'completed'."""
        import sqlite3
        from db.storage import initialize_database, create_run, finalize_run
        initialize_database(temp_db)

        run_id = create_run(SAMPLE_TOPIC, "test.pdf", temp_db)
        finalize_run(run_id, final_score=82, total_iterations=2, db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT status, final_score FROM runs WHERE id = ?", (run_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == "completed"
        assert row[1] == 82

    def test_get_all_runs_returns_list(self, temp_db):
        """get_all_runs should return a list of dicts."""
        from db.storage import initialize_database, create_run, get_all_runs
        initialize_database(temp_db)

        create_run("Topic 1", "a.pdf", temp_db)
        create_run("Topic 2", "b.pdf", temp_db)

        runs = get_all_runs(temp_db)
        assert len(runs) == 2
        assert all(isinstance(r, dict) for r in runs)


# ─── LangGraph edge tests ─────────────────────────────────────────────────────

class TestLangGraphEdges:
    """Tests for the conditional routing logic."""

    def _make_state(self, score, iteration, max_iter=3, threshold=75):
        """Helper to create a minimal state dict for edge testing."""
        return {
            "eval_scores":    {"total_score": score},
            "iteration":      iteration,
            "max_iterations": max_iter,
            "score_threshold": threshold
        }

    def test_routes_to_finalize_when_score_passes(self):
        """Score at or above threshold should route to finalize."""
        from graph.edges import should_refine

        state = self._make_state(score=75, iteration=1)
        assert should_refine(state) == "finalize"

        state = self._make_state(score=90, iteration=1)
        assert should_refine(state) == "finalize"

    def test_routes_to_refine_when_score_low(self):
        """Score below threshold with iterations remaining should route to refine."""
        from graph.edges import should_refine

        state = self._make_state(score=60, iteration=1, max_iter=3)
        assert should_refine(state) == "refine"

    def test_routes_to_finalize_at_max_iterations(self):
        """When max iterations reached, always route to finalize even if score is low."""
        from graph.edges import should_refine

        state = self._make_state(score=40, iteration=3, max_iter=3)
        assert should_refine(state) == "finalize"

    def test_routes_to_refine_below_threshold_with_room(self):
        """With iterations remaining and low score, should still refine."""
        from graph.edges import should_refine

        state = self._make_state(score=55, iteration=1, max_iter=5, threshold=80)
        assert should_refine(state) == "refine"


# ─── run all tests ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # allows running directly: python tests/test_agents.py
    pytest.main([__file__, "-v", "--tb=short"])
