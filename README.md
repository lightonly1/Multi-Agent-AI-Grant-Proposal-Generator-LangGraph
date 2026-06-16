# AI Research Grant Proposal Generator & Evaluator

An enterprise-grade, privacy-focused Agentic AI System designed to automate the end-to-end generation, evaluation and iterative refinement of rigorous academic and scientific research grant proposals.

Developed as a flagship project within the HYSEA Project Drona 2.0 track, this architecture was successfully defended solo before a senior corporate executive evaluation panel from TCS and Tech Mahindra receiving direct leadership commendations for system design, robust data extraction and autonomous closed-loop execution.

---

## Problem Statement & Business Context

### The Challenge
The development of research grant proposals is often hindered by the complexity of aligning diverse funding agency guidelines with intricate technical content and strict budgetary constraints. Researchers frequently struggle with compliance, structural formatting and financial estimation, leading to high rejection rates.

### Industry Significance & Scoping
Securing research funding is a high-stakes, competitive necessity for both academic and industrial institutions. By standardizing the proposal drafting process and providing an objective, pre-submission scoring engine, this system:
* Minimizes compliance-driven human error.
* Drastically reduces manual preparation time.
* Increases the overall statistical probability of securing competitive grants across multiple deep-tech domains (e.g., Solar Energy, Material Science).

---

## System Architecture & Workflow

Unlike basic linear RAG pipelines or standard chatbots, this system leverages a Multi-Agent StateGraph Architecture powered by LangGraph. The workflow forms a closed feedback loop where the execution path is dynamically determined at runtime by an evaluation agent acting as an autonomous quality gate.


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



The `should_refine` conditional edge is the core indicator of Agentic AI behavior—the graph's execution path responds dynamically to output validation rules rather than following a static, hardcoded script.

### Component & Agent Breakdown

1. **Guideline Ingestion Agent (`guideline_agent.py`)**: Parses raw funding guideline PDFs using `PyPDFLoader`. Splits data text into 1000-character chunks with 150-character overlap, builds a localized FAISS vector index at `data/faiss_index/`, and extracts structured constraint profiles (required sections, eligibility criteria, scoring weights, budget limits) using GPT-4o ($temperature=0$).
2. **Proposal Drafting Agent (`proposal_agent.py`)**: Queries the local FAISS vector store to pull contextually relevant chunks ($top-5$). Generates all 6 comprehensive proposal sections in a single inference context block to ensure strong narrative coherence ($temperature=0.7$). On re-drafts, it automatically appends evaluation feedback to the prompt.
3. **Budget & Project Timeline Agent (`budget_agent.py`)**: Parses the generated methodology section to deduce resource needs, generates an itemized budget table with written category justifications, constructs a month-by-month milestone timeline, and programmatically checks totals against funding ceilings.
4. **Deterministic Evaluation Agent (`evaluation_agent.py`)**: Conducts an objective critique scoring 4 foundational pillars (Innovation, Feasibility, Budget Clarity, Impact) out of 25 points each ($temperature=0.1$). Returns clean, structured JSON containing exact numerical scores and granular weaknesses while verifying that the total score matches the sum of criteria.
5. **Feedback-Driven Refinement Agent (`refinement_agent.py`)**: Isolates criteria falling short of the target threshold (under 18/25), uses GPT-4o to synthesize weaknesses into an actionable refinement brief, and triggers an intelligent prompt-injected full proposal regeneration loop for document consistency.

---

## Data Engineering & Processing Pipeline

The ingestion engine converts highly unstructured, regulatory documents into clean, machine-actionable context windows:

* **Data Sources**: Real-world compliance and funding guideline documentation (PDF format) from premier national and international agencies like DST (Department of Science and Technology) and CSIR (Council of Scientific and Industrial Research).
* **Processing & Token Alignment**: Implemented Semantic Chunking and text extraction to split documents by thematic transitions rather than arbitrary character counts. This preserves regulatory context and keeps payload windows highly optimized.
* **Storage & Low-Latency Retrieval**: Utilized a FAISS-based vector database hosted locally for high-velocity retrieval of specific regulatory constraints, mandatory templates, and domain-specific clauses.

---

## Enterprise Design Choices & Trade-offs

* **Local Data Sovereignty (Ollama vs. OpenAI)**: For deployments managing sensitive institutional data, proprietary research, or pre-patent intellectual property, the system seamlessly supports an isolated local inference layer via Ollama / Mistral. This guarantees zero data leakage beyond organizational firewalls.
* **Mitigating Hallucinations**: Financial and budget generation are notorious areas for LLM hallucination. This architecture mitigates mathematical discrepancies through targeted prompt engineering, structured JSON schemas, and iterative validation loops within the `budget_agent` node.
* **State Persistence & Observability**: Powered by a lightweight SQLite relational tracking store (`data/proposals.db`). Every iteration run, discrete agent evaluation score, and prompt mutation is fully preserved, allowing developers to trace the agent's historical correction path.

---

## Model Performance & Validation Metrics

The framework's adaptability was heavily stress-tested and validated using diverse, real-world regulatory scenarios. Score variations accurately reflect the model's ability to distinguish between the unique, rigorous specificities of different funding bodies:

### Evaluation Case Studies

| Funding Body / Program | Target Domain | Iterations to Converge | Final Validated Score |
| --- | --- | --- | --- |
| **DST (Department of Science & Technology)** | Solar Energy Infrastructure | 2 | **81 / 100** |
| **CSIR (Council of Scientific & Industrial Research)** | Advanced Composite Materials | 1 | **87 / 100** |

---

## Repository Structure


grant_proposal_ai/
│
├── agents/                     # Isolated agentic computational nodes
│   ├── guideline_agent.py      # PDF ingestion + FAISS vector indexing
│   ├── proposal_agent.py       # Context-aware RAG-based generation
│   ├── budget_agent.py         # Resource estimation & budget derivation
│   ├── evaluation_agent.py     # Deterministic evaluation & JSON scoring
│   └── refinement_agent.py     # Critique synthesis & feedback engineering
│
├── graph/                      # LangGraph StateGraph engine wiring
│   ├── state.py                # Thread-safe shared state schema (TypedDict)
│   ├── nodes.py                # LangGraph operational execution adapters
│   ├── edges.py                # Conditional routing logic & control flows
│   └── build_graph.py          # StateGraph structural assembly & compilation
│
├── db/                         # Persistence layer
│   └── storage.py              # SQLite schema for deterministic audit trailing
│
├── utils/                      # Production utility extensions
│   └── exporters.py            # Stream-based .docx and .txt compilation
│
├── tests/                      # Enterprise testing suite
│   └── test_agents.py          # Offline unit tests using mock interfaces
│
├── app.py                      # Interactive Streamlit Web Interface
├── run_graph.py                # Production CLI Execution Driver
├── requirements.txt            # Explicit dependency pinning
├── .env.example                # Sanitized environment file template
└── README.md                   # Technical portfolio documentation



---

## Technology Stack Matrix

| Component | Library | Purpose |
| --- | --- | --- |
| LLM Framework | `langchain-openai` / `ollama` | Local Mistral or Cloud GPT-4o for agent tasks |
| Agent Orchestration | `langgraph` | StateGraph architecture with conditional routing |
| PDF Ingestion Engine | `pypdf` (`langchain-community`) | Extraction and parsing of raw guideline data |
| Local Vector Cache | `faiss-cpu` | High-velocity context retrieval without cloud dependencies |
| Visualization UI | `streamlit` | Front-end demonstration and parameter tuning dashboard |
| Audit Persistence | `sqlite3` (stdlib) | Persistent local relational storage of workflow runs |
| Document Compiler | `python-docx` | Generates stream-based downloadable `.docx` files |
| Testing Infrastructure | `pytest` | Validates isolated agent node logic offline |

---

## Quickstart & Setup Instructions

### 1. Environment Activation & Dependencies


git clone [https://github.com/lightonly1/Multi-Agent-AI-Grant-Proposal-Generator-LangGraph.git](https://github.com/lightonly1/Multi-Agent-AI-Grant-Proposal-Generator-LangGraph.git)
cd Multi-Agent-AI-Grant-Proposal-Generator-LangGraph
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt


### 2. Configure Environment Injections

Instantiate your environment file from the secure deployment template:

cp .env.example .env
# Edit .env and append your secure API configurations:
# OPENAI_API_KEY=sk-proj-...


### 3. Execution via Production CLI Driver

Run the end-to-end multi-agent pipeline natively inside your terminal:


python run_graph.py \
  --topic "AI-assisted early detection of diabetic retinopathy" \
  --pdf path/to/guidelines.pdf \
  --max-iter 3 \
  --threshold 75


### 4. Interactive Graphical Web Dashboard

Launch the web-based visualization interface built with Streamlit:


streamlit run app.py


### 5. Deterministic Offline Testing

Run the offline pytest suite to validate structural agent node performance without using live API tokens:


python -m pytest tests/ -v

---

## Database Schema Mapping

The SQLite persistence layer matches real-world auditable tracking patterns across operations (`data/proposals.db`):


runs         (id, topic, pdf_path, started_at, finished_at, final_score, total_iterations, status)
proposals    (id, run_id, iteration, version_tag, title, abstract, ..., full_draft_json)
evaluations  (id, run_id, proposal_id, iteration, innovation_score, ..., total_score, grade)
budgets      (id, run_id, proposal_id, total_cost_usd, within_limit, full_budget_json)


---

## Sample Production Execution Logs


=============================================================================
  PIPELINE COMPLETE
=============================================================================
  Final score:  82/100  (Grade: A)
  Iterations:   2
  Budget total: $28,200 USD
=============================================================================

── EVALUATION SCORES ──
  Innovation           20/25  | weakness: Ensemble novelty not justified...
  Feasibility          22/25  | weakness: IRB approval not mentioned...
  Budget Clarity       19/25  | weakness: Cloud credits need breakdown...
  Impact               21/25  | weakness: International scale unsubstantiated...

---

## Limitations & Advanced Future Development

* **API Overhead and Cost Optimization**: Deep pipeline loops run ~8–12 context requests per setup, averaging $0.10–$0.25 per execution on cloud endpoints. Developers are advised to maintain `--max-iter 1` settings during localized debugging phases.
* **Asynchronous Execution Graphs**: Currently, budget generation waits for the baseline draft to finish. Future iterations can run independent tasks in parallel using LangGraph's native asynchronous execution engine (`graph.ainvoke()`).
* **Human-in-the-Loop Interruption**: For production deployment, integrating human review points between evaluation and refinement stages ensures domain-expert oversight. This can be achieved natively using LangGraph's `interrupt_before` compiled parameter.
* **Multimodal OCR Processing**: The current pipeline functions optimally on text-dense guideline vectors. Incorporating standalone engine layouts (e.g., `pytesseract` or specialized vision processing) will extend coverage to scanned physical documents or imagery.
* **Localization Engineering**: Financial estimation blocks generate baseline tracking values in USD. Future modular features will implement contextual text matching to auto-detect native currency models (e.g., INR) based on parsed agency rules.

---

## References & Frameworks

1. LangGraph Engine Docs — https://langchain-ai.github.io/langgraph/
2. Context-Aware Retrieval (RAG) — LangChain Ecosystem
3. FAISS: High-Performance Similarity Vectors — Johnson et al., 2019
4. ReAct Logic: Synergizing Reasoning and Action in LLMs — Yao et al., 2022
5. DST-SERB Grant Guidelines — https://serb.gov.in/page/english/core_research_grant

---

## Author Profile

* **Developer:** Krit Prakash
* **Designation:** Applied AI/ML Engineer (NPTEL National Domain Scholar)
* **Education:** M.Tech, Indian Institute of Technology (ISM) Dhanbad
* **Core Focus:** Advanced LLM Orchestration, Real-time Backend System Engineering & Scalable Data Pipelines
