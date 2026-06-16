# AI Research Grant Proposal Generator & Evaluator

An enterprise-grade, privacy-focused Agentic AI System designed to automate the end-to-end generation, evaluation, and iterative refinement of rigorous academic and scientific research grant proposals.

Developed as a flagship project within the HYSEA Project Drona 2.0 track, this architecture was successfully defended solo before a senior corporate executive evaluation panel from TCS and Tech Mahindra, receiving direct leadership commendations for system design, robust data extraction, and autonomous closed-loop execution.

---

## Problem Statement & Business Context

### The Challenge
The development of research grant proposals is often hindered by the complexity of aligning diverse funding agency guidelines with intricate technical content and strict budgetary constraints. Researchers frequently struggle with compliance, structural formatting, and financial estimation, leading to high rejection rates.

### Industry Significance & Scoping
Securing research funding is a high-stakes, competitive necessity for both academic and industrial institutions. By standardizing the proposal drafting process and providing an objective, pre-submission scoring engine, this system:
* Minimizes compliance-driven human error.
* Drastically reduces manual preparation time.
* Increases the overall statistical probability of securing competitive grants across multiple deep-tech domains (e.g., Solar Energy, Material Science).

---

## System Architecture & Workflow

Unlike basic linear RAG pipelines or standard chatbots, this system leverages a Multi-Agent StateGraph Architecture powered by LangGraph. The workflow forms a closed feedback loop where the execution path is dynamically determined at runtime by an evaluation agent acting as an autonomous quality gate.

```text
START
→ ingest_guidelines      (Runs once to index PDF rules via Local RAG)
→ draft_proposal         (Generates initial 6-section text)
→ generate_budget        (Derives financial line-items & milestone timeline)
→ evaluate_proposal      (Deterministic JSON scoring across 4 pillars)
→ [should_refine?]
     IF Score >= Threshold OR Max Iterations Reached → finalize_output → END
     IF Score < Threshold AND Iterations Remaining  → refine_proposal ──┐
          ▲                                                             │
          └─────────────────────────────────────────────────────────────┘
